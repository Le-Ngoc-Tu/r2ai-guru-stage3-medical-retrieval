"""Lập chỉ mục BM25 (Tantivy) cho các chunk trong data/chunks/shard_*.parquet.

Tiếng Trung không có dấu cách giữa các từ nên tokenizer mặc định sẽ gom cả câu thành
một token. `to_index_text` biến mỗi chuỗi chữ Hán thành bigram chồng lấp (cách
Lucene CJKAnalyzer dùng); phần còn lại (tiếng Việt, số, chữ Latin) tách theo ký tự
chữ-số và chuyển chữ thường. Phía truy vấn phải dùng đúng hàm này.

Index chỉ lưu doc_id + chunk_index (không lưu text); text lấy lại từ parquet theo shard.
Resume: checkpoint ghi sau mỗi lần commit; khi chạy lại, xóa mọi tài liệu thuộc shard
chưa có trong checkpoint rồi lập lại, nên không bị trùng nếu bị ngắt giữa chừng.

Chạy:
    python tantivy_indexer.py --index-dir ../../data/tantivy_index
    python tantivy_indexer.py --index-dir <thư mục thử> --max-shards 3
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

import polars as pl
import tantivy

ROOT = Path(__file__).resolve().parents[2]
CHUNK_DIR = ROOT / "data" / "chunks"
TOKENIZER_NAME = "cjk_vi"
SHARD_SIZE = 20_000
COMMIT_EVERY_SHARDS = 4
HEAP_BYTES = 600_000_000

_HAN_RUN = re.compile(r"[一-鿿]+")


def _bigrams(match: re.Match) -> str:
    run = match.group()
    if len(run) == 1:
        return f" {run} "
    return " " + " ".join(run[i:i + 2] for i in range(len(run) - 1)) + " "


def to_index_text(text: str) -> str:
    return _HAN_RUN.sub(_bigrams, text)


def build_schema() -> tantivy.Schema:
    builder = tantivy.SchemaBuilder()
    builder.add_text_field("body", stored=False, tokenizer_name=TOKENIZER_NAME, index_option="freq")
    builder.add_integer_field("doc_id", stored=True, indexed=True, fast=True)
    builder.add_integer_field("chunk_index", stored=True, indexed=False, fast=True)
    builder.add_integer_field("shard", stored=False, indexed=True)
    return builder.build()


def register_analyzer(index: tantivy.Index) -> None:
    analyzer = (
        tantivy.TextAnalyzerBuilder(tantivy.Tokenizer.simple())
        .filter(tantivy.Filter.remove_long(40))
        .filter(tantivy.Filter.lowercase())
        .build()
    )
    index.register_tokenizer(TOKENIZER_NAME, analyzer)


def open_index(index_dir: Path) -> tantivy.Index:
    index_dir.mkdir(parents=True, exist_ok=True)
    index = tantivy.Index(build_schema(), path=str(index_dir))
    register_analyzer(index)
    return index


def index_shard(writer: tantivy.IndexWriter, path: Path, shard: int) -> int:
    frame = pl.read_parquet(path, columns=["doc_id", "chunk_index", "doc_title", "section", "text"])
    for doc_id, chunk_index, title, section, text in frame.iter_rows():
        body = to_index_text(f"{title}\n{section}\n{text}")
        writer.add_document(tantivy.Document(body=body, doc_id=doc_id, chunk_index=chunk_index, shard=shard))
    return frame.height


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index-dir", type=Path, required=True)
    parser.add_argument("--max-shards", type=int, default=None)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()

    index = open_index(args.index_dir)
    writer = index.writer(HEAP_BYTES, args.threads)
    checkpoint_path = args.index_dir / "_checkpoint.json"
    done = set(json.loads(checkpoint_path.read_text())["done"]) if checkpoint_path.exists() else set()

    shard_files = sorted(CHUNK_DIR.glob("shard_*.parquet"))
    pending = [(int(p.stem.split("_")[1]), p) for p in shard_files if int(p.stem.split("_")[1]) not in done]
    if args.max_shards:
        pending = pending[: args.max_shards]
    for shard, _ in pending:
        writer.delete_documents("shard", shard)
    writer.commit()

    started = time.time()
    total_chunks = 0
    since_commit: list[int] = []
    for position, (shard, path) in enumerate(pending, 1):
        total_chunks += index_shard(writer, path, shard)
        since_commit.append(shard)
        if len(since_commit) >= COMMIT_EVERY_SHARDS or position == len(pending):
            writer.commit()
            done.update(since_commit)
            checkpoint_path.write_text(json.dumps({"done": sorted(done)}))
            since_commit = []
            print(f"[{position}/{len(pending)}] shard {shard} chunks={total_chunks} "
                  f"{time.time() - started:.0f}s", flush=True)
    writer.wait_merging_threads()
    print("XONG", flush=True)


if __name__ == "__main__":
    sys.exit(main())
