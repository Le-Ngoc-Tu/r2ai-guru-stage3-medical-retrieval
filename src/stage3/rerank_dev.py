"""Chấm điểm BGE-reranker-v2-m3 cho top RRF của mock dev set, lưu logit thô để chỉnh ngưỡng sau.

Chạy:
    python rerank_dev.py
"""

import argparse
import glob
import json
import time

import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

import hybrid_search as hs
import medical_chunker as mc
import tantivy_indexer as ti

DEV_DIR = ti.ROOT / "data" / "mock_dev"
RERANK_DEPTH = 30
BATCH_SIZE = 16
MAX_LENGTH = 512


@torch.inference_mode()
def score_pairs(tokenizer, model, pairs: list[tuple[str, str]]) -> list[float]:
    order = np.argsort([len(text) for _, text in pairs])
    scores = np.empty(len(pairs), dtype=np.float32)
    for start in range(0, len(pairs), BATCH_SIZE):
        idx = order[start:start + BATCH_SIZE]
        batch = tokenizer([pairs[i][0] for i in idx], [pairs[i][1] for i in idx], padding=True, truncation=True,
                          max_length=MAX_LENGTH, return_tensors="pt").to("cuda")
        scores[idx] = model(**batch).logits[:, 0].float().cpu().numpy()
    return scores.tolist()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-title", action="store_true", help="ghép doc_title + section vào văn bản chấm (giống embed_text)")
    with_title = parser.parse_args().with_title
    dev = {json.loads(l)["id"]: json.loads(l) for l in open(DEV_DIR / "dev_set.jsonl", encoding="utf-8")}
    candidates = [json.loads(l) for l in open(DEV_DIR / "candidates.jsonl", encoding="utf-8")]
    searcher = hs.HybridSearcher()
    keys = sorted({tuple(k) for c in candidates for k in c["rrf"][:RERANK_DEPTH]})
    fields = searcher.chunk_fields(keys, ["doc_title", "section", "text"])
    texts = {k: mc.build_embed_text(*row) if with_title else row[2] for k, row in fields.items()}
    path = glob.glob(str(ti.ROOT / "data" / "hf_cache" / "models--BAAI--bge-reranker-v2-m3" / "snapshots" / "*"))[0]
    tokenizer = AutoTokenizer.from_pretrained(path)
    model = AutoModelForSequenceClassification.from_pretrained(path, dtype=torch.float16).cuda().eval()

    started = time.time()
    with open(DEV_DIR / ("rerank_scores_title.jsonl" if with_title else "rerank_scores.jsonl"), "w", encoding="utf-8") as out:
        for n, c in enumerate(candidates):
            ranking = [tuple(k) for k in c["rrf"][:RERANK_DEPTH]]
            scores = score_pairs(tokenizer, model, [(dev[c["id"]]["query"], texts[k]) for k in ranking])
            out.write(json.dumps({"id": c["id"], "keys": [list(k) for k in ranking], "scores": scores}) + "\n")
            if n % 50 == 0:
                print(f"{n}/{len(candidates)}, {time.time() - started:.0f}s", flush=True)
    print(f"XONG {time.time() - started:.0f}s", flush=True)


if __name__ == "__main__":
    main()
