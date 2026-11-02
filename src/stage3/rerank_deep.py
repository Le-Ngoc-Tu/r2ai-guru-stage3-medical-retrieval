"""Rerank sâu cho 1.200 câu thật: chấm điểm các chunk xếp hạng START..END của RRF bằng BGE-reranker-v2-m3 (có tiêu đề).

Kết quả: data/submission/rerank_r{START}_{END}.jsonl, mỗi dòng {"id", "keys", "scores"} (logit thô).
Có cache từng phần: chạy lại sẽ bỏ qua các câu đã xong, và bỏ qua chunk đã có điểm trong mọi file rerank_r*.jsonl khác.
Máy này còn là máy làm việc: ưu tiên thấp, tự tạm dừng khi RAM trống thấp, GPU nóng hoặc VRAM trống thấp,
và dừng êm khi có file data/submission/STOP_RERANK.

Chạy:
    python rerank_deep.py 150 300
    python rerank_deep.py 0 600 --candidates candidates_rrf600_d600.jsonl
"""

import argparse
import ctypes
import glob
import json
import time

import polars as pl
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

import embed_corpus
import hybrid_search as hs
import make_submission as ms
import medical_chunker as mc
import rerank_dev
import tantivy_indexer as ti

OUT_DIR = ti.ROOT / "data" / "submission"
MIN_FREE_VRAM_GB = 1.5
BELOW_NORMAL_PRIORITY = 0x00004000


def wait_until_ok(guard: embed_corpus.Guard) -> None:
    """Chờ tới khi RAM, nhiệt độ GPU và VRAM trống đều đạt ngưỡng (ngưỡng RAM/nhiệt lấy từ embed_corpus)."""
    guard.wait_until_ok()
    warned = False
    while torch.cuda.mem_get_info()[0] / 2**30 < MIN_FREE_VRAM_GB:
        if not warned:
            print(f"TAM DUNG: VRAM trong {torch.cuda.mem_get_info()[0] / 2**30:.1f}GB", flush=True)
            warned = True
        time.sleep(20)
    if warned:
        guard.wait_until_ok()


def already_scored(exclude_path) -> dict[int, set[tuple[int, int]]]:
    scored: dict[int, set[tuple[int, int]]] = {}
    for path in OUT_DIR.glob("rerank_r*.jsonl"):
        if path == exclude_path:
            continue
        for line in open(path, encoding="utf-8"):
            row = json.loads(line)
            scored.setdefault(row["id"], set()).update(tuple(k) for k in row["keys"])
    return scored


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("start", type=int)
    parser.add_argument("end", type=int)
    parser.add_argument("--candidates", default="candidates_rrf_d300.jsonl")
    parser.add_argument("--new-corpus", action="store_true", help="bỏ chunk của doc ngoài corpus mới trước khi rerank")
    args = parser.parse_args()
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), BELOW_NORMAL_PRIORITY)
    queries = dict(zip(*(pl.read_parquet(ti.ROOT / "data" / "ViBioMIR" / "query.parquet")[c].to_list() for c in ("id", "query"))))
    candidates = [json.loads(line) for line in open(OUT_DIR / args.candidates, encoding="utf-8")]
    if args.new_corpus:
        ms.restrict_corpus(candidates)
    path = OUT_DIR / f"rerank_r{args.start}_{args.end}.jsonl"
    scored = already_scored(path)
    done = {json.loads(line)["id"] for line in open(path, encoding="utf-8")} if path.exists() else set()
    todo = [c for c in candidates if c["id"] not in done]
    stop_file = OUT_DIR / "STOP_RERANK"

    searcher = hs.HybridSearcher()
    snapshot = glob.glob(str(ti.ROOT / "data" / "hf_cache" / "models--BAAI--bge-reranker-v2-m3" / "snapshots" / "*"))[0]
    tokenizer = AutoTokenizer.from_pretrained(snapshot)
    model = AutoModelForSequenceClassification.from_pretrained(snapshot, dtype=torch.float16).cuda().eval()
    guard = embed_corpus.Guard()
    print(f"con {len(todo)} cau; RAM trong {embed_corpus.free_ram_gb():.1f}GB", flush=True)

    started = time.time()
    with open(path, "a", encoding="utf-8") as out:
        for start in range(0, len(todo), 50):
            if stop_file.exists():
                print("co file STOP_RERANK - dung em", flush=True)
                return
            batch = todo[start:start + 50]
            ranked_by_query = {c["id"]: [tuple(k) for k in c["ranking"][args.start:args.end] if tuple(k) not in scored.get(c["id"], ())] for c in batch}
            keys = sorted({k for ranked in ranked_by_query.values() for k in ranked})
            fields = searcher.chunk_fields(keys, ["doc_title", "section", "text"])
            for c in batch:
                ranked = ranked_by_query[c["id"]]
                pairs = [(queries[c["id"]], mc.build_embed_text(*fields[k])) for k in ranked]
                while True:
                    wait_until_ok(guard)
                    try:
                        scores = rerank_dev.score_pairs(tokenizer, model, pairs)
                        break
                    except torch.cuda.OutOfMemoryError:
                        torch.cuda.empty_cache()
                        print("OOM VRAM - doi 30s roi thu lai", flush=True)
                        time.sleep(30)
                out.write(json.dumps({"id": c["id"], "keys": [list(k) for k in ranked], "scores": scores}) + "\n")
            out.flush()
            print(f"rerank {start + len(batch)}/{len(todo)}, {time.time() - started:.0f}s, GPU {guard.temp}C, RAM trong {embed_corpus.free_ram_gb():.1f}GB", flush=True)
    print("XONG", flush=True)


if __name__ == "__main__":
    main()
