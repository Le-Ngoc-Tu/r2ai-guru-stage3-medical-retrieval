"""Chunk phần dữ liệu bổ sung của corpus mới (18/10/2026) thành shard riêng, nối vào chỉ mục hiện có.

  vi     : trang tiếng Việt crawl lại (status done, thuộc corpus mới, chưa có chunk) -> shard_90000000
  pubmed : tiêu đề + tóm tắt PubMed (pubmed_cache.sqlite3) -> shard_91000000 + k * 20000

Tên shard lớn hơn mọi shard cũ nên các bước sau (embed_corpus, tantivy_indexer, dense_index build) tự nhận ra shard mới.
Chạy:
    python chunk_extra.py vi
    python chunk_extra.py pubmed
"""

import argparse
import sqlite3
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chunk_corpus as cc  # noqa: E402
import medical_chunker as mc  # noqa: E402

NEW_CORPUS = cc.ROOT / "data" / "ViBioMIR_new" / "links_corpus_vi_en_zh.parquet"
PUBMED_DB = cc.ROOT / "data" / "pubmed_cache.sqlite3"
VI_SHARD = 90_000_000
PUBMED_SHARD = 91_000_000
PUBMED_DOCS_PER_SHARD = 20_000


def indexed_doc_ids() -> set[int]:
    shards = sorted(p for p in cc.OUT_DIR.glob("shard_*.parquet") if int(p.stem.split("_")[1]) < VI_SHARD)
    return {d for p in shards for d in pl.scan_parquet(p).select("doc_id").unique().collect()["doc_id"].to_list()}


def to_rows(chunks, language: str | None = None) -> list[tuple]:
    return [(c.doc_id, c.chunk_id, c.chunk_index, c.doc_title, c.section, language or c.language, c.text, c.char_start, c.char_end, c.n_tokens) for c in chunks]


def write_shard(rows: list[tuple], number: int) -> None:
    path = cc.OUT_DIR / f"shard_{number:08d}.parquet"
    tmp = path.with_suffix(".tmp")
    pl.DataFrame(rows, schema=cc.SCHEMA, orient="row").write_parquet(tmp, compression="zstd")
    tmp.replace(path)
    print(f"{path.name}: {len(rows)} chunk", flush=True)


def chunk_vi() -> None:
    new_ids = set(pl.read_parquet(NEW_CORPUS)["id"].to_list())
    have = indexed_doc_ids()
    tokenizer = mc.load_tokenizer()
    conn = sqlite3.connect(cc.DB_URI, uri=True, timeout=600)
    done_ids = [r[0] for r in conn.execute("SELECT id FROM pages WHERE status='done'") if r[0] in new_ids and r[0] not in have]
    print(f"{len(done_ids)} trang done thuộc corpus mới chưa có chunk", flush=True)
    rows, skipped = [], 0
    for start in range(0, len(done_ids), 2000):
        batch = done_ids[start:start + 2000]
        for page_id, markdown in conn.execute(f"SELECT id, markdown FROM pages WHERE id IN ({','.join('?' * len(batch))})", batch):
            chunks = mc.chunk_page(page_id, markdown, tokenizer)
            skipped += not chunks
            rows.extend(to_rows(chunks))
    print(f"bỏ qua {skipped} trang (lỗi mã hóa hoặc không có thân bài)", flush=True)
    write_shard(rows, VI_SHARD)


def chunk_pubmed() -> None:
    tokenizer = mc.load_tokenizer()
    conn = sqlite3.connect(PUBMED_DB)
    records = conn.execute("SELECT id, title, abstract FROM pubmed WHERE status='done' ORDER BY id").fetchall()
    for k in range(0, len(records), PUBMED_DOCS_PER_SHARD):
        rows = []
        for doc_id, title, abstract in records[k:k + PUBMED_DOCS_PER_SHARD]:
            title = " ".join(title.split())
            body = f"{title}\n\n{abstract}" if abstract else title
            if not body.strip():
                continue
            rows.extend(to_rows(mc.chunk_page(doc_id, f"---\ntitle: {title}\n---\n{body}", tokenizer), "en"))
        write_shard(rows, PUBMED_SHARD + k // PUBMED_DOCS_PER_SHARD * PUBMED_DOCS_PER_SHARD)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("what", choices=["vi", "pubmed"])
    {"vi": chunk_vi, "pubmed": chunk_pubmed}[parser.parse_args().what]()
