"""Kiểm tra bài nộp theo các lưu ý bắt buộc của thể lệ (01-THONG-TIN-CUOC-THI.md mục 6).

Chạy:
    python validate_submission.py ../../data/submission/submission_A.zip
"""

import glob
import json
import sys
import zipfile
from pathlib import Path

import polars as pl
from transformers import AutoTokenizer

import tantivy_indexer as ti

MAX_ZIP_BYTES = 100 * 1024 * 1024
MAX_CHUNK_TOKENS = 1024


def validate(zip_path: Path) -> list[str]:
    errors = []
    if zip_path.stat().st_size > MAX_ZIP_BYTES:
        errors.append(f"zip {zip_path.stat().st_size / 1e6:.1f} MB vượt 100 MB")
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        if len(names) != 1 or not names[0].endswith(".json") or "/" in names[0]:
            return errors + [f"zip phải có đúng 1 file .json ở gốc, hiện có {names}"]
        data = json.loads(archive.read(names[0]))

    query_ids = set(pl.read_parquet(ti.ROOT / "data" / "ViBioMIR" / "query.parquet")["id"].to_list())
    corpus_ids = set(pl.read_parquet(ti.ROOT / "data" / "ViBioMIR" / "links_corpus.parquet", columns=["id"])["id"].to_list())
    corpus_ids |= set(pl.read_parquet(ti.ROOT / "data" / "ViBioMIR_new" / "links_corpus_vi_en_zh.parquet", columns=["id"])["id"].to_list())
    if not isinstance(data, list):
        return errors + ["JSON gốc phải là list"]
    seen = [item.get("id") for item in data]
    if len(seen) != len(set(seen)):
        errors.append("có id trùng lặp")
    if set(seen) != query_ids:
        errors.append(f"id không khớp query.parquet: thiếu {len(query_ids - set(seen))}, thừa {len(set(seen) - query_ids)}")
    tokenizer = AutoTokenizer.from_pretrained(glob.glob(str(ti.ROOT / "data" / "hf_cache" / "models--BAAI--bge-m3" / "snapshots" / "*"))[0])
    empty_docs = empty_chunks = 0
    for item in data:
        qid = item.get("id")
        if not isinstance(qid, int) or isinstance(qid, bool):
            errors.append(f"id={qid!r} không phải số nguyên")
        missing = [f for f in ("relevant_docs", "relevant_chunks") if not isinstance(item.get(f), list)]
        if missing:
            errors.append(f"id={qid}: thiếu hoặc sai kiểu {missing}")
            continue
        docs, chunks = item["relevant_docs"], item["relevant_chunks"]
        empty_docs += not docs
        empty_chunks += not chunks
        if not all(isinstance(c, dict) and set(c) == {"doc_id", "chunk_text"} for c in chunks):
            errors.append(f"id={qid}: mỗi chunk phải là object có đúng 2 khóa doc_id và chunk_text")
            continue
        pairs = [(c["doc_id"], c["chunk_text"]) for c in chunks]
        if len(pairs) != len(set(pairs)):
            errors.append(f"id={qid}: chunk trùng lặp")
        if len(docs) != len(set(docs)):
            errors.append(f"id={qid}: doc_id trùng lặp")
        if any(not isinstance(d, int) or d not in corpus_ids for d in docs):
            errors.append(f"id={qid}: doc_id không phải số nguyên có trong links_corpus")
        if any(c["doc_id"] not in docs for c in chunks):
            errors.append(f"id={qid}: chunk có doc_id không nằm trong relevant_docs")
        if any(not isinstance(c["chunk_text"], str) or not c["chunk_text"].strip() for c in chunks):
            errors.append(f"id={qid}: chunk_text rỗng hoặc sai kiểu")
        elif any(len(tokenizer(c["chunk_text"], add_special_tokens=False)["input_ids"]) > MAX_CHUNK_TOKENS for c in chunks):
            errors.append(f"id={qid}: có chunk_text dài hơn {MAX_CHUNK_TOKENS} token")
    print(f"{len(data)} câu, {empty_docs} câu rỗng relevant_docs, {empty_chunks} câu rỗng relevant_chunks")
    return errors


if __name__ == "__main__":
    problems = validate(Path(sys.argv[1]))
    for problem in problems[:20]:
        print("LỖI:", problem)
    print("HỢP LỆ" if not problems else f"KHÔNG HỢP LỆ ({len(problems)} lỗi)")
    sys.exit(1 if problems else 0)
