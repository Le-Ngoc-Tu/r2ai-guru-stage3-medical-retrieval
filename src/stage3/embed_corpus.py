"""Embed dense BGE-M3 (fp16, CLS, chuẩn hóa) cho mọi chunk trong data/chunks/shard_*.parquet.

Mỗi shard -> data/embeddings/shard_XXXXXXXX.npy (float16, N x 1024, đúng thứ tự dòng của
parquet tương ứng). Ghi nguyên tử (.tmp rồi đổi tên) nên dừng/chạy lại an toàn, shard
đã có sẽ bị bỏ qua. Thiết kế cho máy yếu (RTX 3050 6GB, RAM 16GB dùng chung):
  - ưu tiên tiến trình thấp, ít luồng CPU, batch 16 (batch 32 chậm gấp 4,5 lần, đã đo);
  - tạm dừng khi RAM trống dưới MIN_FREE_GB hoặc GPU từ MAX_TEMP độ trở lên;
  - tạo file data/embeddings/STOP để dừng êm sau shard hiện tại.

Chạy:
    python embed_corpus.py
    python embed_corpus.py --max-shards 1
"""

import argparse
import ctypes
import glob
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import polars as pl
import torch
from transformers import AutoModel, AutoTokenizer

sys.path.insert(0, str(Path(__file__).resolve().parent))
import medical_chunker as mc  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CHUNK_DIR = ROOT / "data" / "chunks"
OUT_DIR = ROOT / "data" / "embeddings"
BATCH_SIZE = 16
MAX_LENGTH = 512
MIN_FREE_GB = float(os.environ.get("R2AI_MIN_FREE_GB", "3.5"))
MAX_TEMP = 80
CPU_THREADS = 2
BELOW_NORMAL_PRIORITY = 0x00004000


class _MemoryStatus(ctypes.Structure):
    _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong),
                ("total_phys", ctypes.c_ulonglong), ("avail_phys", ctypes.c_ulonglong),
                ("total_page", ctypes.c_ulonglong), ("avail_page", ctypes.c_ulonglong),
                ("total_virtual", ctypes.c_ulonglong), ("avail_virtual", ctypes.c_ulonglong),
                ("avail_extended", ctypes.c_ulonglong)]


def free_ram_gb() -> float:
    status = _MemoryStatus()
    status.length = ctypes.sizeof(status)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
    return status.avail_phys / 2**30


def gpu_temp() -> int:
    out = subprocess.run(["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
                         capture_output=True, text=True, timeout=20)
    return int(out.stdout.strip().splitlines()[0])


class Guard:
    """Chặn khi máy quá tải; kiểm tra nhiệt độ tối đa 30 giây một lần."""

    def __init__(self) -> None:
        self.last_temp_check = 0.0
        self.temp = 0

    def wait_until_ok(self) -> None:
        warned = False
        while True:
            now = time.time()
            if now - self.last_temp_check > 30:
                self.temp = gpu_temp()
                self.last_temp_check = now
            ram = free_ram_gb()
            if ram >= MIN_FREE_GB and self.temp < MAX_TEMP:
                return
            if not warned:
                print(f"TAM DUNG: RAM trong {ram:.1f}GB, GPU {self.temp}C", flush=True)
                warned = True
            time.sleep(20)
            self.last_temp_check = 0.0


def load_model():
    path = glob.glob(str(ROOT / "data" / "hf_cache" / "models--BAAI--bge-m3" / "snapshots" / "*"))[0]
    tokenizer = AutoTokenizer.from_pretrained(path)
    model = AutoModel.from_pretrained(path, dtype=torch.float16).cuda().eval()
    return tokenizer, model


@torch.inference_mode()
def embed_shard(path: Path, tokenizer, model, guard: Guard) -> np.ndarray:
    frame = pl.read_parquet(path, columns=["doc_title", "section", "text", "n_tokens"])
    texts = [mc.build_embed_text(t, s, x) for t, s, x in zip(frame["doc_title"], frame["section"], frame["text"])]
    order = np.argsort(frame["n_tokens"].to_numpy(), kind="stable")
    out = np.empty((len(texts), 1024), dtype=np.float16)
    for i in range(0, len(texts), BATCH_SIZE):
        guard.wait_until_ok()
        idx = order[i:i + BATCH_SIZE]
        batch = tokenizer([texts[j] for j in idx], padding=True, truncation=True,
                          max_length=MAX_LENGTH, return_tensors="pt").to("cuda")
        cls = model(**batch).last_hidden_state[:, 0]
        out[idx] = torch.nn.functional.normalize(cls.float(), dim=-1).half().cpu().numpy()
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-shards", type=int, default=None)
    args = parser.parse_args()

    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), BELOW_NORMAL_PRIORITY)
    torch.set_num_threads(CPU_THREADS)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stop_file = OUT_DIR / "STOP"

    pending = [p for p in sorted(CHUNK_DIR.glob("shard_*.parquet")) if not (OUT_DIR / f"{p.stem}.npy").exists()]
    if args.max_shards:
        pending = pending[: args.max_shards]
    print(f"con {len(pending)} shard can embed; RAM trong {free_ram_gb():.1f}GB", flush=True)
    if not pending:
        print("XONG", flush=True)
        return

    guard = Guard()
    guard.wait_until_ok()
    tokenizer, model = load_model()
    t0 = time.time()
    total = 0
    with (OUT_DIR / "stats.jsonl").open("a", encoding="utf-8") as log:
        for position, path in enumerate(pending, 1):
            if stop_file.exists():
                print("co file STOP - dung em", flush=True)
                return
            started = time.time()
            vectors = embed_shard(path, tokenizer, model, guard)
            target = OUT_DIR / f"{path.stem}.npy"
            tmp = target.with_suffix(".tmp")
            with tmp.open("wb") as handle:
                np.save(handle, vectors)
            tmp.replace(target)
            seconds = time.time() - started
            total += len(vectors)
            log.write(json.dumps({"shard": path.stem, "chunks": len(vectors), "seconds": round(seconds, 1)}) + "\n")
            log.flush()
            rate = len(vectors) / seconds if seconds else 0
            print(f"[{position}/{len(pending)}] {path.stem}: {len(vectors)} chunk {seconds:.0f}s "
                  f"{rate:.1f} chunk/s | GPU {guard.temp}C RAM trong {free_ram_gb():.1f}GB | "
                  f"tong {total} chunk {time.time() - t0:.0f}s", flush=True)
    print("XONG", flush=True)


if __name__ == "__main__":
    main()
