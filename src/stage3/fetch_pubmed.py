"""Lấy tiêu đề + tóm tắt cho 240.000 URL PubMed của corpus mới (18/10/2026) qua NCBI E-utilities (efetch).

Nội dung thuộc đúng các PMID trong URL do Ban Tổ chức cung cấp; không dùng nguồn ngoài corpus.
Giới hạn không có API key: 3 request/giây. Kết quả lưu SQLite, chạy lại bỏ qua phần đã có.

Chạy:
    python fetch_pubmed.py              # toàn bộ
    python fetch_pubmed.py --limit 400  # thử nhỏ
"""

import argparse
import re
import sqlite3
import time
import xml.etree.ElementTree as ET

import httpx
import polars as pl

import url_crawler as uc

NEW_CORPUS = uc.ROOT / "data" / "ViBioMIR_new" / "links_corpus_vi_en_zh.parquet"
DB_PATH = uc.ROOT / "data" / "pubmed_cache.sqlite3"
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
BATCH = 200
MIN_INTERVAL = 0.4


def text_of(node) -> str:
    return "".join(node.itertext()).strip() if node is not None else ""


def parse_articles(xml: str) -> dict[int, tuple[str, str, str, str]]:
    root = ET.fromstring(xml)
    records = {}
    for article in root.iter("PubmedArticle"):
        pmid = int(text_of(article.find("./MedlineCitation/PMID")))
        title = text_of(article.find(".//ArticleTitle"))
        parts = []
        for part in article.findall(".//Abstract/AbstractText"):
            label = part.get("Label")
            body = text_of(part)
            if body:
                parts.append(f"{label}: {body}" if label else body)
        journal = text_of(article.find(".//Journal/Title"))
        year = text_of(article.find(".//JournalIssue/PubDate/Year")) or text_of(article.find(".//JournalIssue/PubDate/MedlineDate"))
        records[pmid] = (title, "\n\n".join(parts), journal, year)
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    corpus = pl.read_parquet(NEW_CORPUS).filter(pl.col("url").str.contains("pubmed.ncbi.nlm.nih.gov"))
    pairs = [(i, int(re.search(r"/(\d+)/?$", u).group(1))) for i, u in corpus.iter_rows()]
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.execute("CREATE TABLE IF NOT EXISTS pubmed (id INTEGER PRIMARY KEY, pmid INTEGER, title TEXT, abstract TEXT, journal TEXT, year TEXT, status TEXT)")
    done = {r[0] for r in conn.execute("SELECT id FROM pubmed")}
    todo = [p for p in pairs if p[0] not in done]
    if args.limit:
        todo = todo[: args.limit]
    print(f"còn {len(todo)}/{len(pairs)} PMID", flush=True)
    client = httpx.Client(timeout=60, headers={"User-Agent": "r2ai-stage3-research/1.0"})
    started, last = time.time(), 0.0
    for n in range(0, len(todo), BATCH):
        batch = todo[n:n + BATCH]
        for attempt in range(6):
            wait = MIN_INTERVAL - (time.time() - last)
            if wait > 0:
                time.sleep(wait)
            last = time.time()
            try:
                resp = client.post(EFETCH, data={"db": "pubmed", "id": ",".join(str(p) for _, p in batch), "retmode": "xml", "tool": "r2ai_stage3"})
                if resp.status_code == 200:
                    records = parse_articles(resp.text)
                    break
                print(f"HTTP {resp.status_code}, thử lại", flush=True)
            except Exception as exc:
                print(f"{type(exc).__name__}, thử lại", flush=True)
            time.sleep(5 * (attempt + 1))
        else:
            raise RuntimeError("efetch thất bại liên tục")
        conn.execute("BEGIN")
        conn.executemany(
            "INSERT OR REPLACE INTO pubmed VALUES (?,?,?,?,?,?,?)",
            [(i, p, *(records[p] if p in records else ("", "", "", "")), "done" if p in records else "no_record") for i, p in batch],
        )
        conn.execute("COMMIT")
        if (n // BATCH) % 20 == 0:
            print(f"{n + len(batch)}/{len(todo)} {time.time() - started:.0f}s", flush=True)
    print("XONG", flush=True)


if __name__ == "__main__":
    main()
