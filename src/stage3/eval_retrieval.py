"""Đo baseline truy hồi (BM25, dense, RRF) trên mock dev set.

Một chunk được tính relevant với câu hỏi khi thuộc doc nhãn VÀ LCS token(chunk, đáp án) /
|đáp án| >= 0,40 (luật khớp chunk chính thức, xem eval_f2.py). Mỗi câu có một đoạn thông tin
cần thiết (đáp án), nên Recall chunk-level của một câu là 1 nếu có ít nhất một chunk relevant.

Chạy:
    python eval_retrieval.py
"""

import json
import time

import numpy as np

import eval_f2
import hybrid_search as hs
import tantivy_indexer as ti

DEV_SET = ti.ROOT / "data" / "mock_dev" / "dev_set.jsonl"
CANDIDATES = ti.ROOT / "data" / "mock_dev" / "candidates.jsonl"
DEPTH = 50
CUTOFFS = (1, 3, 5, 10, 20, 50)
FIXED_DOCS, FIXED_CHUNKS = 3, 5


def first_docs(ranking: list[tuple[int, int]], k: int) -> list[int]:
    docs: list[int] = []
    for doc_id, _ in ranking:
        if doc_id not in docs:
            docs.append(doc_id)
        if len(docs) == k:
            break
    return docs


def main() -> None:
    dev = [json.loads(line) for line in open(DEV_SET, encoding="utf-8")]
    encoder = hs.QueryEncoder()
    vectors = np.concatenate([encoder.encode([d["query"] for d in dev[i:i + 32]]) for i in range(0, len(dev), 32)])
    del encoder
    searcher = hs.HybridSearcher()

    started = time.time()
    rankings = []
    for item, vector in zip(dev, vectors):
        bm25 = searcher.bm25(item["query"], DEPTH)
        dense = searcher.dense_search(vector, DEPTH)
        fused = [key for key, _ in hs.rrf([bm25, dense], DEPTH)]
        rankings.append({"bm25": bm25, "dense": dense, "rrf": fused})
    print(f"Truy hồi {len(dev)} câu: {time.time() - started:.0f}s", flush=True)

    wanted = {key for r in rankings for ranking in r.values() for key in ranking[:max(CUTOFFS)]}
    texts = searcher.chunk_texts(sorted(wanted))
    print(f"Đã đọc text {len(texts)} chunk, {time.time() - started:.0f}s", flush=True)

    with open(CANDIDATES, "w", encoding="utf-8") as out:
        for item, r in zip(dev, rankings):
            out.write(json.dumps({"id": item["id"], **{name: [list(k) for k in ranking] for name, ranking in r.items()}}) + "\n")

    for name in ("bm25", "dense", "rrf"):
        doc_recall = {k: [] for k in CUTOFFS}
        chunk_hit = {k: [] for k in CUTOFFS}
        doc_f2, chunk_f2 = [], []
        for item, r in zip(dev, rankings):
            gold_docs = set(item["gold_docs"])
            ranking = r[name]
            flags = [doc in gold_docs and eval_f2.is_chunk_relevant(texts[(doc, idx)], item["answer"]) for doc, idx in ranking[:max(CUTOFFS)]]
            for k in CUTOFFS:
                doc_recall[k].append(len(set(first_docs(ranking, k)) & gold_docs) / len(gold_docs))
                chunk_hit[k].append(float(any(flags[:k])))
            docs = first_docs(ranking, FIXED_DOCS)
            doc_f2.append(eval_f2.document_level_scores(docs, list(gold_docs))["f2"])
            top = flags[:FIXED_CHUNKS]
            chunk_f2.append(eval_f2.f2_score(sum(top) / len(top), float(any(top))))
        print(f"\n[{name}] n={len(dev)}")
        print("  DocRecall@k : " + "  ".join(f"@{k}={np.mean(doc_recall[k]):.3f}" for k in CUTOFFS))
        print("  ChunkHit@k  : " + "  ".join(f"@{k}={np.mean(chunk_hit[k]):.3f}" for k in CUTOFFS))
        print(f"  F2 cố định: doc top-{FIXED_DOCS} = {np.mean(doc_f2):.3f}, chunk top-{FIXED_CHUNKS} = {np.mean(chunk_f2):.3f}")


if __name__ == "__main__":
    main()
