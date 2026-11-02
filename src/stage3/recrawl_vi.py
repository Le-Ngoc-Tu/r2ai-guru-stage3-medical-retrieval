"""Crawl lại các trang tiếng Việt thuộc corpus mới (18/10/2026) mà trước đây bị loại (banned_cooldown/failed).

Dùng lại url_crawler (cùng bảng pages, cùng bộ trích trafilatura) nhưng chậm hơn và lịch sự hơn: ít kết nối mỗi domain.
Chạy:
    python recrawl_vi.py                 # đặt lại trạng thái pending cho các domain đích rồi crawl
    python recrawl_vi.py --limit 300     # thử nhỏ
"""

import argparse
import asyncio
import re

import polars as pl

import url_crawler as uc

NEW_CORPUS = uc.ROOT / "data" / "ViBioMIR_new" / "links_corpus_vi_en_zh.parquet"
TARGET_DOMAINS = [
    "nhathuoclongchau.com.vn", "suckhoecongdongonline.vn", "baohaiphong.vn", "baonghean.vn", "baodanang.vn",
    "youmed.vn", "baocantho.com.vn", "dantri.com.vn", "thaythuocvietnam.vn", "hanoimoi.vn",
]
RESETTABLE = ("banned_cooldown", "failed", "retry")
BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def reset_targets(domains: list[str]) -> int:
    ids = [i for i, url in pl.read_parquet(NEW_CORPUS).iter_rows() if re.sub(r"^https?://", "", url).split("/")[0].lower() in domains]
    conn = uc.connect_db()
    conn.execute("BEGIN")
    marks = ",".join("?" * len(RESETTABLE))
    n = 0
    for start in range(0, len(ids), 5000):
        batch = ids[start:start + 5000]
        n += conn.execute(
            f"UPDATE pages SET status='pending', attempts=0, error=NULL WHERE status IN ({marks}) AND id IN ({','.join('?' * len(batch))})",
            (*RESETTABLE, *batch),
        ).rowcount
    conn.execute("COMMIT")
    conn.close()
    return n


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--per-domain", type=int, default=3)
    parser.add_argument("--global-concurrency", type=int, default=40)
    parser.add_argument("--domains", nargs="*", default=TARGET_DOMAINS)
    args = parser.parse_args()
    print(f"đặt lại pending: {reset_targets(args.domains)} dòng", flush=True)
    uc.USER_AGENT = BROWSER_UA
    uc.PER_DOMAIN_CONCURRENCY = args.per_domain
    uc.GLOBAL_CONCURRENCY = args.global_concurrency
    asyncio.run(uc.run(args.limit))


if __name__ == "__main__":
    main()
