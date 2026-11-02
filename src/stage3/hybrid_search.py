"""Truy vấn lai: BM25 (Tantivy) + dense BGE-M3 (binary + rescoring) hợp nhất bằng RRF.

Chạy kiểm thử trên câu hỏi thật:
    python hybrid_search.py test --n 20
"""

import argparse
import ctypes
import re
import time
from collections import defaultdict

import numpy as np
import polars as pl
import tantivy
import torch

import dense_index
import embed_corpus
import tantivy_indexer as ti

RRF_K = 60
BM25_DEPTH = 100
DENSE_DEPTH = 100
_HAN = re.compile(r"[一-鿿]")


class _MemoryCounters(ctypes.Structure):
    _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]


def rss_gb(peak: bool = False) -> float:
    counters = _MemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    kernel32, psapi = ctypes.WinDLL("kernel32"), ctypes.WinDLL("psapi")
    kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(_MemoryCounters), ctypes.c_ulong]
    psapi.GetProcessMemoryInfo(kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb)
    return (counters.PeakWorkingSetSize if peak else counters.WorkingSetSize) / 1024 ** 3


def rrf(rankings: list[list[tuple[int, int]]], top_k: int) -> list[tuple[tuple[int, int], float]]:
    """Reciprocal Rank Fusion: điểm = tổng 1/(RRF_K + hạng) qua các danh sách xếp hạng."""
    fused: dict[tuple[int, int], float] = defaultdict(float)
    for ranking in rankings:
        for rank, key in enumerate(ranking, start=1):
            fused[key] += 1.0 / (RRF_K + rank)
    return sorted(fused.items(), key=lambda item: -item[1])[:top_k]


class QueryEncoder:
    def __init__(self) -> None:
        self.tokenizer, self.model = embed_corpus.load_model()

    @torch.inference_mode()
    def encode(self, queries: list[str]) -> np.ndarray:
        batch = self.tokenizer(queries, padding=True, truncation=True, max_length=512, return_tensors="pt").to("cuda")
        cls = self.model(**batch).last_hidden_state[:, 0]
        return torch.nn.functional.normalize(cls.float(), dim=-1).cpu().numpy()


class HybridSearcher:
    def __init__(self) -> None:
        self.dense = dense_index.DenseIndex()
        index = ti.open_index(ti.ROOT / "data" / "tantivy_index")
        index.reload()
        self.index = index
        self.searcher = index.searcher()
        keys = self.dense.doc_id.astype(np.int64) << 12 | self.dense.chunk_index
        if self.dense.chunk_index.max() >= 4096:
            raise ValueError("chunk_index vượt 4095, không đóng gói được khóa")
        self.key_order = np.argsort(keys)
        self.sorted_keys = keys[self.key_order]

    def bm25(self, query: str, top_k: int) -> list[tuple[int, int]]:
        parsed = self.index.parse_query_lenient(ti.to_index_text(query), ["body"])[0]
        hits = self.searcher.search(parsed, top_k).hits
        return [(self.searcher.doc(address)["doc_id"][0], self.searcher.doc(address)["chunk_index"][0]) for _, address in hits]

    def dense_search(self, query_vector: np.ndarray, top_k: int) -> list[tuple[int, int]]:
        return [(doc, chunk) for doc, chunk, _ in self.dense.search(query_vector, top_k, candidates=max(200, 2 * top_k))]

    def search(self, query: str, query_vector: np.ndarray, top_k: int = 10):
        bm25_ranking = self.bm25(query, BM25_DEPTH)
        dense_ranking = self.dense_search(query_vector, DENSE_DEPTH)
        return rrf([bm25_ranking, dense_ranking], top_k), bm25_ranking, dense_ranking

    def chunk_row(self, doc_id: int, chunk_index: int) -> int:
        position = np.searchsorted(self.sorted_keys, (doc_id << 12) | chunk_index)
        return int(self.key_order[position])

    def chunk_text(self, doc_id: int, chunk_index: int) -> str:
        row = self.chunk_row(doc_id, chunk_index)
        shard = int(np.searchsorted(self.dense.offsets, row, side="right") - 1)
        path = dense_index.CHUNK_DIR / f"{self.dense.names[shard]}.parquet"
        offset = row - int(self.dense.offsets[shard])
        return pl.scan_parquet(path).slice(offset, 1).select("text").collect().item()

    def chunk_fields(self, keys: list[tuple[int, int]], columns: list[str]) -> dict[tuple[int, int], tuple]:
        """Đọc các cột của nhiều chunk, mỗi shard parquet chỉ đọc một lần."""
        by_shard: dict[int, list[tuple[tuple[int, int], int]]] = defaultdict(list)
        for key in keys:
            row = self.chunk_row(*key)
            shard = int(np.searchsorted(self.dense.offsets, row, side="right") - 1)
            by_shard[shard].append((key, row - int(self.dense.offsets[shard])))
        fields = {}
        for shard, items in by_shard.items():
            frame = pl.read_parquet(dense_index.CHUNK_DIR / f"{self.dense.names[shard]}.parquet", columns=columns)
            for key, local in items:
                fields[key] = frame.row(local)
        return fields

    def chunk_texts(self, keys: list[tuple[int, int]]) -> dict[tuple[int, int], str]:
        return {key: row[0] for key, row in self.chunk_fields(keys, ["text"]).items()}


def is_chinese(text: str) -> bool:
    return len(_HAN.findall(text)) > len(text) * 0.1


def exact_dense_top(searcher: HybridSearcher, query_vector: np.ndarray, top_k: int) -> set[tuple[int, int]]:
    """Duyệt toàn bộ vector fp16 để lấy top-k chính xác, dùng đối chiếu recall của binary + rescoring."""
    best_scores, best_rows = np.full(top_k, -2.0), np.zeros(top_k, dtype=np.int64)
    for shard, vectors in enumerate(searcher.dense.vectors):
        scores = np.asarray(vectors, dtype=np.float32) @ query_vector
        local = np.argpartition(-scores, top_k)[:top_k]
        pool_scores = np.concatenate([best_scores, scores[local]])
        pool_rows = np.concatenate([best_rows, local + searcher.dense.offsets[shard]])
        keep = np.argsort(-pool_scores)[:top_k]
        best_scores, best_rows = pool_scores[keep], pool_rows[keep]
    return {(int(searcher.dense.doc_id[r]), int(searcher.dense.chunk_index[r])) for r in best_rows}


def run_test(n: int, exact_n: int) -> None:
    queries = pl.read_parquet(ti.ROOT / "data" / "ViBioMIR" / "query.parquet").sample(n, seed=0)["query"].to_list()
    rss_before = rss_gb()
    encoder = QueryEncoder()
    searcher = HybridSearcher()
    vectors = encoder.encode(queries)
    print(f"RSS sau khi nạp encoder + chỉ mục: {rss_gb():.2f} GB (trước {rss_before:.2f})")

    shares = {"bm25": [], "dense": [], "rrf": []}
    latencies, recalls, bm25_times, dense_times = [], [], [], []
    for i, (query, vector) in enumerate(zip(queries, vectors)):
        started = time.time()
        bm25_ranking = searcher.bm25(query, BM25_DEPTH)
        bm25_times.append(time.time() - started)
        mid = time.time()
        dense_ranking = searcher.dense_search(vector, DENSE_DEPTH)
        dense_times.append(time.time() - mid)
        fused = rrf([bm25_ranking, dense_ranking], 10)
        latencies.append(time.time() - started)
        for name, keys in (("bm25", bm25_ranking[:10]), ("dense", dense_ranking[:10]), ("rrf", [k for k, _ in fused])):
            shares[name].append(np.mean([is_chinese(searcher.chunk_text(*key)) for key in keys]))
        if i < exact_n:
            exact = exact_dense_top(searcher, vector, 10)
            recalls.append(len(exact & set(dense_ranking[:10])) / 10)
    print(f"Độ trễ mỗi câu (BM25 + dense + RRF, không tính encode): trung vị {np.median(latencies) * 1000:.0f} ms, "
          f"P95 {np.percentile(latencies, 95) * 1000:.0f} ms, tối đa {max(latencies) * 1000:.0f} ms")
    print(f"Trung vị riêng: BM25 {np.median(bm25_times) * 1000:.0f} ms, dense {np.median(dense_times) * 1000:.0f} ms")
    for name, values in shares.items():
        print(f"Tỷ lệ chunk tiếng Trung trong top-10 {name}: {np.mean(values):.1%}")
    if recalls:
        print(f"Recall@10 của binary + rescoring so với duyệt chính xác fp16 ({len(recalls)} câu): {np.mean(recalls):.3f}")
    print(f"RSS hiện tại {rss_gb():.2f} GB, đỉnh {rss_gb(peak=True):.2f} GB")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["test"])
    parser.add_argument("--n", type=int, default=20)
    parser.add_argument("--exact-n", type=int, default=5)
    args = parser.parse_args()
    run_test(args.n, args.exact_n)
