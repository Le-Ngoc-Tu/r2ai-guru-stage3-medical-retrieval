"""Dựng mock dev set từ ViHealthQA, nhãn gắn vào chunk thật của corpus.

ViHealthQA có cột `link` nhưng URL không trùng URL trong links_corpus, nên không có nhãn trực
tiếp. Thay vào đó, coi câu trả lời là "phần thông tin cần thiết": tìm trong chỉ mục BM25 các
chunk chứa gần nguyên văn câu trả lời (LCS token / độ dài câu trả lời >= GOLD_OVERLAP) và lấy
đó làm nhãn dương. Chỉ giữ các cặp có ít nhất một chunk đạt ngưỡng (nhãn chắc chắn).

Hạn chế đã biết: (1) chỉ gồm câu hỏi mà đáp án nằm gần nguyên văn trong corpus; (2) ứng viên
nhãn lấy từ BM25 của chính câu trả lời (không phải câu hỏi) nên thiên nhẹ về từ vựng; (3) chỉ
tiếng Việt, không đo được đáp án tiếng Trung cho câu hỏi tiếng Việt.

Chạy:
    python build_mock_dev.py
"""

import json
import re
import time
import unicodedata
from collections import defaultdict
from pathlib import Path

import numpy as np
import polars as pl

import tantivy_indexer as ti

ROOT = ti.ROOT
DENSE_DIR = ROOT / "data" / "dense_index"
OUT_DIR = ROOT / "data" / "mock_dev"
CANDIDATE_DEPTH = 30
LCS_CANDIDATES = 3
GOLD_OVERLAP = 0.6
QUERY_CHARS = 400


def tokens(text: str) -> list[str]:
    return re.findall(r"\w+", unicodedata.normalize("NFKC", text).lower())


def lcs_length(first: list[str], second: list[str]) -> int:
    previous = [0] * (len(second) + 1)
    for token in first:
        current = [0]
        for j, other in enumerate(second):
            current.append(previous[j] + 1 if token == other else max(previous[j + 1], current[j]))
        previous = current
    return previous[-1]


def main() -> None:
    pairs = pl.concat([
        pl.read_csv(OUT_DIR / "vihealthqa" / f"{split}.csv").with_columns(pl.lit(split).alias("split"))
        for split in ("train", "val", "test")
    ])
    doc_ids = np.load(DENSE_DIR / "row_doc_id.npy")
    chunk_indexes = np.load(DENSE_DIR / "row_chunk_index.npy")
    offsets = np.load(DENSE_DIR / "shard_offsets.npy")
    names = [p.stem for p in sorted(ti.CHUNK_DIR.glob("shard_*.parquet"))]
    keys = doc_ids.astype(np.int64) << 12 | chunk_indexes
    key_order = np.argsort(keys)
    sorted_keys = keys[key_order]

    index = ti.open_index(ROOT / "data" / "tantivy_index")
    index.reload()
    searcher = index.searcher()

    started = time.time()
    candidates: list[list[int]] = []
    for n, answer in enumerate(pairs["answer"].to_list()):
        query = index.parse_query_lenient(ti.to_index_text(answer[:QUERY_CHARS]), ["body"])[0]
        rows = []
        for _, address in searcher.search(query, CANDIDATE_DEPTH).hits:
            doc = searcher.doc(address)
            key = (doc["doc_id"][0] << 12) | doc["chunk_index"][0]
            rows.append(int(key_order[np.searchsorted(sorted_keys, key)]))
        candidates.append(rows)
        if n % 1000 == 0:
            print(f"BM25 {n}/{pairs.height}, {time.time() - started:.0f}s", flush=True)

    wanted: dict[int, set[int]] = defaultdict(set)
    for rows in candidates:
        for row in rows:
            shard = int(np.searchsorted(offsets, row, side="right") - 1)
            wanted[shard].add(row - int(offsets[shard]))
    chunk_tokens: dict[int, list[str]] = {}
    for done, (shard, local_rows) in enumerate(sorted(wanted.items())):
        texts = pl.read_parquet(ti.CHUNK_DIR / f"{names[shard]}.parquet", columns=["text"])["text"]
        for local in local_rows:
            chunk_tokens[int(offsets[shard]) + local] = tokens(texts[local])
        if done % 20 == 0:
            print(f"đọc text shard {done}/{len(wanted)}, {time.time() - started:.0f}s", flush=True)

    kept = 0
    with open(OUT_DIR / "dev_set.jsonl", "w", encoding="utf-8") as out:
        for pair, rows in zip(pairs.iter_rows(named=True), candidates):
            gold = set(tokens(pair["answer"]))
            if not gold:
                continue
            answer_tokens = tokens(pair["answer"])
            ranked = sorted(rows, key=lambda r: -len(gold & set(chunk_tokens[r])))[:LCS_CANDIDATES]
            matches = []
            for row in ranked:
                overlap = lcs_length(answer_tokens, chunk_tokens[row]) / len(answer_tokens)
                if overlap >= GOLD_OVERLAP:
                    matches.append({"doc_id": int(doc_ids[row]), "chunk_index": int(chunk_indexes[row]),
                                    "overlap": round(overlap, 3)})
            if matches:
                kept += 1
                out.write(json.dumps({
                    "id": pair["id"], "split": pair["split"], "query": pair["question"],
                    "answer": pair["answer"], "gold_chunks": matches,
                    "gold_docs": sorted({m["doc_id"] for m in matches}),
                }, ensure_ascii=False) + "\n")
    print(f"XONG: giữ {kept}/{pairs.height} cặp (ngưỡng LCS {GOLD_OVERLAP}), {time.time() - started:.0f}s", flush=True)


if __name__ == "__main__":
    main()
