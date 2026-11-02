"""Chunk toàn bộ trang `done` trong crawl_cache.sqlite3 thành các shard parquet.

Mỗi shard = một khoảng id liên tiếp (SHARD_SIZE id), ghi nguyên tử (.tmp rồi đổi tên)
nên dừng/chạy lại an toàn: shard đã có sẽ bị bỏ qua. Đọc DB bằng nhiều process vì
HDD chỉ đạt ~140 dòng/s với 1 luồng, ~200 dòng/s với 4 luồng (đo 10/10/2026).

Chạy:
    python chunk_corpus.py              # toàn bộ
    python chunk_corpus.py --max-shards 2   # thử
"""

import argparse
import json
import sqlite3
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
import medical_chunker as mc  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB_URI = f"file:{(ROOT / 'data' / 'crawl_cache.sqlite3').as_posix()}?mode=ro"
OUT_DIR = ROOT / "data" / "chunks"
MAX_ID = 4_420_561
SHARD_SIZE = 20_000
WORKERS = 4

SCHEMA = {
    "doc_id": pl.Int64, "chunk_id": pl.String, "chunk_index": pl.Int32, "doc_title": pl.String,
    "section": pl.String, "language": pl.String, "text": pl.String,
    "char_start": pl.Int32, "char_end": pl.Int32, "n_tokens": pl.Int32,
}

_tokenizer = None
_conn = None


def _init_worker() -> None:
    global _tokenizer, _conn
    _tokenizer = mc.load_tokenizer()
    _conn = sqlite3.connect(DB_URI, uri=True, timeout=600)
    _conn.execute("PRAGMA cache_size=-50000")


def process_shard(lo: int) -> dict:
    hi = lo + SHARD_SIZE
    path = OUT_DIR / f"shard_{lo:08d}.parquet"
    stats = {"lo": lo, "pages_done": 0, "pages_fffd": 0, "pages_no_body": 0, "chunks": 0, "tokens": 0, "skipped": False}
    if path.exists():
        stats["skipped"] = True
        return stats
    started = time.time()
    rows = []
    for page_id, markdown in _conn.execute(
        "SELECT id, markdown FROM pages WHERE id >= ? AND id < ? AND status = 'done' ORDER BY id", (lo, hi)
    ):
        stats["pages_done"] += 1
        if markdown.count("�") >= mc.FFFD_LIMIT:
            stats["pages_fffd"] += 1
            continue
        chunks = mc.chunk_page(page_id, markdown, _tokenizer)
        if not chunks:
            stats["pages_no_body"] += 1
            continue
        for c in chunks:
            rows.append((c.doc_id, c.chunk_id, c.chunk_index, c.doc_title, c.section, c.language,
                         c.text, c.char_start, c.char_end, c.n_tokens))
            stats["tokens"] += c.n_tokens
    stats["chunks"] = len(rows)
    frame = pl.DataFrame(rows, schema=SCHEMA, orient="row")
    tmp = path.with_suffix(".tmp")
    frame.write_parquet(tmp, compression="zstd")
    tmp.replace(path)
    stats["seconds"] = round(time.time() - started, 1)
    return stats


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-shards", type=int, default=None)
    parser.add_argument("--workers", type=int, default=WORKERS)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    starts = list(range(0, MAX_ID + 1, SHARD_SIZE))
    if args.max_shards:
        starts = [s for s in starts if s >= 600_000][: args.max_shards]
    stats_path = OUT_DIR / "stats.jsonl"
    done_count = 0
    t0 = time.time()
    with Pool(args.workers, initializer=_init_worker) as pool, stats_path.open("a", encoding="utf-8") as log:
        for stats in pool.imap_unordered(process_shard, starts):
            done_count += 1
            if not stats["skipped"]:
                log.write(json.dumps(stats) + "\n")
                log.flush()
            print(f"[{done_count}/{len(starts)}] shard {stats['lo']}: pages={stats['pages_done']} "
                  f"fffd={stats['pages_fffd']} chunks={stats['chunks']} {stats.get('seconds', 0)}s "
                  f"(tong {time.time() - t0:.0f}s)", flush=True)
    print("XONG", flush=True)


if __name__ == "__main__":
    main()
