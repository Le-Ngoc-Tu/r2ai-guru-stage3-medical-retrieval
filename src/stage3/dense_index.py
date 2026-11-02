"""Chỉ mục dense BGE-M3: binary quantization (faiss) + rescoring bằng vector float16.

Mỗi vector 1024 chiều fp16 được lượng tử hóa thành 1024 bit (dấu từng chiều, 128 byte);
faiss.IndexBinaryFlat quét khoảng cách Hamming chính xác trên toàn bộ chunk, rồi các ứng
viên được chấm lại bằng tích vô hướng với vector fp16 gốc (đọc mmap từ data/embeddings).

Thứ tự hàng toàn cục = thứ tự shard (sắp theo tên) nối nhau, khớp thứ tự dòng parquet.

Chạy dựng chỉ mục:
    python dense_index.py build
"""

import argparse
import time
from pathlib import Path

import faiss
import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[2]
CHUNK_DIR = ROOT / "data" / "chunks"
EMB_DIR = ROOT / "data" / "embeddings"
INDEX_DIR = ROOT / "data" / "dense_index"
DIM = 1024


def shard_names() -> list[str]:
    return [p.stem for p in sorted(CHUNK_DIR.glob("shard_*.parquet"))]


def binarize(vectors: np.ndarray) -> np.ndarray:
    return np.packbits(vectors > 0, axis=1)


def build() -> None:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    index = faiss.IndexBinaryFlat(DIM)
    doc_ids, chunk_indexes, offsets = [], [], [0]
    started = time.time()
    for name in shard_names():
        vectors = np.load(EMB_DIR / f"{name}.npy")
        meta = pl.read_parquet(CHUNK_DIR / f"{name}.parquet", columns=["doc_id", "chunk_index"])
        if vectors.shape != (meta.height, DIM):
            raise ValueError(f"{name}: vector {vectors.shape} không khớp {meta.height} chunk")
        index.add(binarize(vectors))
        doc_ids.append(meta["doc_id"].to_numpy())
        chunk_indexes.append(meta["chunk_index"].to_numpy())
        offsets.append(offsets[-1] + meta.height)
        print(f"{name}: tổng {offsets[-1]} hàng, {time.time() - started:.0f}s", flush=True)
    faiss.write_index_binary(index, str(INDEX_DIR / "binary.faiss"))
    np.save(INDEX_DIR / "row_doc_id.npy", np.concatenate(doc_ids))
    np.save(INDEX_DIR / "row_chunk_index.npy", np.concatenate(chunk_indexes))
    np.save(INDEX_DIR / "shard_offsets.npy", np.array(offsets, dtype=np.int64))
    print(f"XONG: {index.ntotal} vector, {time.time() - started:.0f}s", flush=True)


class DenseIndex:
    def __init__(self) -> None:
        self.index = faiss.read_index_binary(str(INDEX_DIR / "binary.faiss"))
        self.doc_id = np.load(INDEX_DIR / "row_doc_id.npy")
        self.chunk_index = np.load(INDEX_DIR / "row_chunk_index.npy")
        self.offsets = np.load(INDEX_DIR / "shard_offsets.npy")
        self.names = shard_names()
        self.vectors = [np.load(EMB_DIR / f"{name}.npy", mmap_mode="r") for name in self.names]

    def row_vectors(self, rows: np.ndarray) -> np.ndarray:
        shard_of = np.searchsorted(self.offsets, rows, side="right") - 1
        out = np.empty((len(rows), DIM), dtype=np.float32)
        for i, (row, shard) in enumerate(zip(rows, shard_of)):
            out[i] = self.vectors[shard][row - self.offsets[shard]]
        return out

    def search(self, query_vector: np.ndarray, top_k: int, candidates: int = 200) -> list[tuple[int, int, float]]:
        """Trả về [(doc_id, chunk_index, điểm cosine)] đã rescoring, giảm dần theo điểm."""
        query = query_vector.astype(np.float32)[None, :]
        _, rows = self.index.search(binarize(query), candidates)
        rows = rows[0][rows[0] >= 0]
        scores = self.row_vectors(rows) @ query[0]
        order = np.argsort(-scores)[:top_k]
        return [(int(self.doc_id[rows[i]]), int(self.chunk_index[rows[i]]), float(scores[i])) for i in order]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["build"])
    parser.parse_args()
    build()
