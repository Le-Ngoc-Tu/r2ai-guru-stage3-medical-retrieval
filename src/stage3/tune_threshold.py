"""Chỉnh ngưỡng cắt động (T_min, Delta, K_max, K_doc) trên điểm rerank của mock dev set.

Tìm tham số trên split train, báo cáo trên val + test (không dùng để chọn tham số).
Mỗi câu có một đoạn thông tin cần thiết (đáp án): F2 chunk dùng P = relevant/trả về,
R = 1 nếu có chunk relevant; F2 doc theo tập doc_id.

Chạy:
    python tune_threshold.py
"""

import argparse
import itertools
import json

import numpy as np

import eval_f2
import hybrid_search as hs
import tantivy_indexer as ti

DEV_DIR = ti.ROOT / "data" / "mock_dev"
T_MIN_GRID = [-np.inf, -6, -4, -2, 0, 1, 2, 3]
DELTA_GRID = [1, 2, 3, 4, 6, 8, np.inf]
K_MAX_GRID = [3, 5, 8]
K_DOC_GRID = [2, 3, 5]


def cut(keys, scores, t_min, delta, k_max, k_doc):
    order = np.argsort(-np.asarray(scores))
    top = scores[order[0]]
    kept, docs = [], []
    for i in order:
        if len(kept) == k_max or scores[i] < t_min or scores[i] < top - delta:
            break
        doc = keys[i][0]
        if doc not in docs:
            if len(docs) == k_doc:
                continue
            docs.append(doc)
        kept.append(int(i))
    return kept, docs


def dedup_mask(keys, scores, spans, texts):
    """Giữ chunk điểm cao nhất; bỏ chunk chồng lấn >= 50% ký tự trong cùng tài liệu hoặc trùng nội dung."""
    kept_spans: dict[int, list[tuple[int, int]]] = {}
    seen_text = set()
    mask = np.zeros(len(keys), dtype=bool)
    for i in np.argsort(-scores):
        doc = keys[i][0]
        start, end = spans[keys[i]]
        normalized = " ".join(eval_f2._tokenize(texts[keys[i]]))
        overlaps = any(min(end, e) - max(start, b) >= 0.5 * min(end - start, e - b) for b, e in kept_spans.get(doc, []))
        if overlaps or normalized in seen_text:
            continue
        mask[i] = True
        kept_spans.setdefault(doc, []).append((start, end))
        seen_text.add(normalized)
    return mask


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores", default="rerank_scores.jsonl")
    parser.add_argument("--dedup", action="store_true")
    args = parser.parse_args()
    dev = {}
    for line in open(DEV_DIR / "dev_set.jsonl", encoding="utf-8"):
        item = json.loads(line)
        dev[item["id"]] = item
    scored = [json.loads(l) for l in open(DEV_DIR / args.scores, encoding="utf-8")]
    searcher = hs.HybridSearcher()
    fields = searcher.chunk_fields(sorted({tuple(k) for s in scored for k in s["keys"]}), ["text", "char_start", "char_end"])
    texts = {k: row[0] for k, row in fields.items()}
    spans = {k: (row[1], row[2]) for k, row in fields.items()}

    rows = []
    for s in scored:
        item = dev[s["id"]]
        keys = [tuple(k) for k in s["keys"]]
        gold_docs = set(item["gold_docs"])
        flags = [k[0] in gold_docs and eval_f2.is_chunk_relevant(texts[k], item["answer"]) for k in keys]
        scores = np.array(s["scores"])
        if args.dedup:
            mask = dedup_mask(keys, scores, spans, texts)
            keys, scores, flags = [k for k, m in zip(keys, mask) if m], scores[mask], [f for f, m in zip(flags, mask) if m]
        rows.append({"split": item["split"], "keys": keys, "scores": scores, "flags": flags, "gold_docs": gold_docs})

    def evaluate(subset, params):
        doc_f2, chunk_f2 = [], []
        for r in subset:
            kept, docs = cut(r["keys"], r["scores"], *params)
            doc_f2.append(eval_f2.document_level_scores(docs, list(r["gold_docs"]))["f2"])
            hits = [r["flags"][i] for i in kept]
            chunk_f2.append(eval_f2.f2_score(sum(hits) / len(hits), float(any(hits))) if hits else 0.0)
        return float(np.mean(doc_f2)), float(np.mean(chunk_f2))

    train = [r for r in rows if r["split"] == "train"]
    held = [r for r in rows if r["split"] != "train"]
    best = max(itertools.product(T_MIN_GRID, DELTA_GRID, K_MAX_GRID, K_DOC_GRID),
               key=lambda p: sum(evaluate(train, p)))
    print(f"Điểm: {args.scores}, khử lặp: {args.dedup}")
    print(f"Tham số tốt nhất trên train ({len(train)} câu): T_min={best[0]}, Delta={best[1]}, K_max={best[2]}, K_doc={best[3]}")
    for name, subset in (("train", train), ("val+test", held)):
        doc, chunk = evaluate(subset, best)
        print(f"  {name:9s} n={len(subset)}: F2 doc {doc:.3f}, F2 chunk {chunk:.3f}")
    for k in (1, 3, 5):
        doc, chunk = evaluate(held, (-np.inf, np.inf, k, k))
        print(f"  Top-{k} cố định (val+test): F2 doc {doc:.3f}, F2 chunk {chunk:.3f}")
    ceiling = np.mean([any(r["flags"]) for r in rows])
    print(f"Trần rerank top-30 (có chunk relevant trong 30 ứng viên): {ceiling:.3f}")
    for k in (1, 3, 5, 10):
        print(f"  ChunkHit@{k} sau rerank: {np.mean([any(np.array(r['flags'])[np.argsort(-r['scores'])[:k]]) for r in rows]):.3f}")


if __name__ == "__main__":
    main()
