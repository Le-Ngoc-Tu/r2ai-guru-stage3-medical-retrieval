"""Chấm thêm điểm Qwen3-Reranker-0.6B cho chunk xếp đầu của mỗi doc trong top-N doc theo điểm BGE-reranker.

Mỗi doc chỉ chấm đúng một chunk: chunk có điểm BGE cao nhất của doc (chính là chunk neo cửa sổ nộp).
Kết quả: data/submission/<out>, mỗi dòng {"id", "keys", "bge", "qwen"} (qwen = logit(yes) - logit(no)).
Có cache từng câu (chạy lại bỏ qua câu đã xong), guard RAM/GPU/VRAM, ưu tiên thấp, dừng êm khi có file STOP_RERANK.

Chạy:
    python rerank_qwen.py qwen_check.jsonl --first 100 --docs 100     # kiểm tra nhỏ
    python rerank_qwen.py qwen_top100.jsonl --docs 100                # toàn bộ 1.200 câu
"""

import argparse
import ctypes
import glob
import json
import time

import numpy as np
import polars as pl
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

import embed_corpus
import hybrid_search as hs
import make_submission as ms
import medical_chunker as mc
import rerank_deep
import tantivy_indexer as ti

OUT_DIR = ti.ROOT / "data" / "submission"
BATCH_SIZE = 8
MAX_DOC_TOKENS = 480
BELOW_NORMAL_PRIORITY = 0x00004000
INSTRUCTION = "Given a Vietnamese medical question, judge whether the document passage contains information that answers or is directly relevant to the question"
PREFIX = '<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the Instruct provided. Note that the answer can only be "yes" or "no".<|im_end|>\n<|im_start|>user\n'
SUFFIX = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"


@torch.inference_mode()
def score_pairs(tokenizer, model, yes_id: int, no_id: int, pairs: list[tuple[str, str]]) -> list[float]:
    prefix_ids = tokenizer(PREFIX, add_special_tokens=False)["input_ids"]
    suffix_ids = tokenizer(SUFFIX, add_special_tokens=False)["input_ids"]
    bodies = []
    for query, doc in pairs:
        doc_ids = tokenizer(doc, add_special_tokens=False, truncation=True, max_length=MAX_DOC_TOKENS)["input_ids"]
        head = tokenizer(f"<Instruct>: {INSTRUCTION}\n<Query>: {query}\n<Document>: ", add_special_tokens=False)["input_ids"]
        bodies.append(prefix_ids + head + doc_ids + suffix_ids)
    order = np.argsort([len(b) for b in bodies])
    scores = np.empty(len(pairs), dtype=np.float32)
    pad = tokenizer.pad_token_id
    for start in range(0, len(pairs), BATCH_SIZE):
        idx = order[start:start + BATCH_SIZE]
        width = max(len(bodies[i]) for i in idx)
        ids = torch.full((len(idx), width), pad, dtype=torch.long)
        mask = torch.zeros((len(idx), width), dtype=torch.long)
        for row, i in enumerate(idx):  # đệm bên trái để token cuối luôn là vị trí dự đoán
            ids[row, width - len(bodies[i]):] = torch.tensor(bodies[i])
            mask[row, width - len(bodies[i]):] = 1
        logits = model(input_ids=ids.cuda(), attention_mask=mask.cuda(), logits_to_keep=1).logits[:, -1, :].float()
        scores[idx] = (logits[:, yes_id] - logits[:, no_id]).cpu().numpy()
    return scores.tolist()


def top_docs(rows: list[dict], n_docs: int) -> dict[int, list[tuple[tuple[int, int], float]]]:
    """Mỗi câu: n_docs doc đầu theo điểm BGE, kèm chunk điểm cao nhất của doc."""
    result = {}
    for r in rows:
        seen, docs = set(), []
        for key, score in zip(r["ranking"], r["scores"]):
            if key[0] not in seen:
                seen.add(key[0])
                docs.append((tuple(key), score))
                if len(docs) == n_docs:
                    break
        result[r["id"]] = docs
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("out")
    parser.add_argument("--docs", type=int, default=100)
    parser.add_argument("--first", type=int, default=0, help="chỉ chấm N câu có id nhỏ nhất (0 = tất cả)")
    parser.add_argument("--reuse", help="file kết quả cũ: cặp (câu, chunk) đã có điểm Qwen thì dùng lại, chỉ chấm phần còn thiếu")
    parser.add_argument("--new-corpus", action="store_true", help="chỉ xét doc có trong corpus mới")
    args = parser.parse_args()
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), BELOW_NORMAL_PRIORITY)
    queries = dict(zip(*(pl.read_parquet(ti.ROOT / "data" / "ViBioMIR" / "query.parquet")[c].to_list() for c in ("id", "query"))))
    rows = ms.rerank_ranking()
    if args.new_corpus:
        ms.restrict_corpus(rows)
    per_query = top_docs(rows, args.docs)
    reused = {}
    if args.reuse:
        for line in open(OUT_DIR / args.reuse, encoding="utf-8"):
            r = json.loads(line)
            reused.update({(r["id"], tuple(k)): q for k, q in zip(r["keys"], r["qwen"])})
    ids = sorted(per_query)[:args.first] if args.first else sorted(per_query)
    path = OUT_DIR / args.out
    done = {json.loads(line)["id"] for line in open(path, encoding="utf-8")} if path.exists() else set()
    todo = [i for i in ids if i not in done]
    stop_file = OUT_DIR / "STOP_RERANK"

    searcher = hs.HybridSearcher()
    snapshot = glob.glob(str(ti.ROOT / "data" / "hf_cache" / "models--Qwen--Qwen3-Reranker-0.6B" / "snapshots" / "*"))[0]
    tokenizer = AutoTokenizer.from_pretrained(snapshot, padding_side="left")
    model = AutoModelForCausalLM.from_pretrained(snapshot, dtype=torch.float16).cuda().eval()
    yes_id, no_id = tokenizer.convert_tokens_to_ids("yes"), tokenizer.convert_tokens_to_ids("no")
    guard = embed_corpus.Guard()
    print(f"con {len(todo)} cau, {args.docs} doc/cau; RAM trong {embed_corpus.free_ram_gb():.1f}GB", flush=True)

    started = time.time()
    with open(path, "a", encoding="utf-8") as out:
        for n, qid in enumerate(todo, 1):
            if stop_file.exists():
                print("co file STOP_RERANK - dung em", flush=True)
                return
            docs = per_query[qid]
            missing = [k for k, _ in docs if (qid, k) not in reused]
            fields = searcher.chunk_fields(missing, ["doc_title", "section", "text"])
            pairs = [(queries[qid], mc.build_embed_text(*fields[k])) for k in missing]
            while True:
                rerank_deep.wait_until_ok(guard)
                try:
                    fresh = score_pairs(tokenizer, model, yes_id, no_id, pairs) if pairs else []
                    break
                except torch.cuda.OutOfMemoryError:
                    torch.cuda.empty_cache()
                    print("OOM VRAM - doi 30s roi thu lai", flush=True)
                    time.sleep(30)
            fresh_iter = iter(fresh)
            scores = [reused[(qid, k)] if (qid, k) in reused else next(fresh_iter) for k, _ in docs]
            out.write(json.dumps({"id": qid, "keys": [list(k) for k, _ in docs], "bge": [s for _, s in docs], "qwen": scores}) + "\n")
            out.flush()
            if n % 5 == 0:
                print(f"qwen {n}/{len(todo)}, {time.time() - started:.0f}s, {n * len(docs) / (time.time() - started):.1f} cap/s, GPU {guard.temp}C, RAM trong {embed_corpus.free_ram_gb():.1f}GB", flush=True)
    print("XONG", flush=True)


if __name__ == "__main__":
    main()
