# Chiến lược Tối ưu 100% trên Phần cứng Cá nhân (Local RTX 3050 6GB VRAM)

Tài liệu thiết kế kiến trúc pipeline chia nhỏ thành các giai đoạn tuần tự (Stage-wise Decoupled Pipeline), đảm bảo toàn bộ hệ thống từ crawl, index, embedding đến reranking chạy hoàn toàn trên máy cá nhân: **GPU NVIDIA GeForce RTX 3050 6GB VRAM, RAM 16GB, Ổ đĩa E (124 GB trống)** mà không bao giờ bị tràn bộ nhớ (OOM) hoặc cần đến Cloud GPU.

---

## 1. Phân tích hiện trạng phần cứng thực tế

Kết quả đo lường trực tiếp trên hệ thống ngày 26/09/2026:
- **GPU:** NVIDIA GeForce RTX 3050 (6.144 MB VRAM, Driver 591.86, CUDA 13.1).
  - VRAM rảnh thực tế khi chạy chế độ coding/terminal: **~3.700 – 4.500 MB**.
- **RAM hệ thống:** 15.86 GB (RAM khả dụng khi mở trình duyệt khoảng 3.7 – 6.0 GB).
- **Ổ đĩa lưu trữ E:** Còn trống **124.5 GB** (đủ sức chứa hàng trăm triệu record index Tantivy và Parquet).
- **Điểm cần khắc phục ngay:** PyTorch hiện tại trong môi trường là bản CPU-only (`2.13.0+cpu`). Cần cài đặt lại PyTorch CUDA (cu124 hoặc cu121) để kích hoạt 6GB VRAM cho GPU.

---

## 2. Nguyên tắc sống còn: Chia nhỏ pipeline thành 5 giai đoạn độc lập (Stage-wise Decoupled Execution)

Tuyệt đối **KHÔNG nạp 2 model cùng lúc vào VRAM** (Bài học xương máu Stage 2: khi có service chiếm 3.3 GB VRAM làm hệ thống chậm gấp 8 lần và crash).

Mỗi giai đoạn được tách thành một script Python độc lập, chạy xong sẽ giải phóng 100% bộ nhớ ra file trung gian trên ổ đĩa E:

```
[Giai đoạn 1: Crawl & Ingest] (0 GB VRAM - Pure Async CPU/Disk)
  - Chạy: url_crawler.py + pubmed_client.py
  - Output: E:/r2ai_stage3/data/raw_corpus.parquet (hoặc SQLite)
      |
      v
[Giai đoạn 2: Chunking & Sparse Indexing] (0 GB VRAM - Disk-based)
  - Chạy: markdown_chunker.py + tantivy_indexer.py
  - Output: E:/r2ai_stage3/data/tantivy_index/ (Zero VRAM, đọc trên NVMe SSD)
      |
      v
[Giai đoạn 3: Query Translation & Expansion] (1.1 GB VRAM hoặc Pure Dictionary)
  - Dùng từ điển MeSH/UMLS offline hoặc Qwen2.5-1.5B (GGUF Q4_K_M ~1.1 GB VRAM)
  - Output: E:/r2ai_stage3/data/expanded_queries.json
      |
      v
[Giai đoạn 4: Candidate Retrieval - Lọc thô Top 50] (2.2 GB VRAM)
  - Nạp Duy nhất Bi-Encoder: BAAI/bge-m3 (fp16, chiếm ~2.2 GB VRAM)
  - Kết hợp Tantivy BM25 + BGE-M3 Dense/Sparse qua RRF
  - Output: E:/r2ai_stage3/data/candidate_pool.json (Top 50 candidates/câu)
  - GIẢI PHÓNG BGE-M3 khỏi VRAM (torch.cuda.empty_cache())
      |
      v
[Giai đoạn 5: Two-Tier Reranking & Dynamic Cutoff] (4.0 GB VRAM)
  - Nạp Duy nhất Cross-Encoder: BAAI/bge-reranker-v2-m3 (batch_size=16)
  - Rerank kèm context window (+-1 chunk)
  - Dynamic Margin Cutoff -> Xuất E:/r2ai_stage3/submission/submission.json
  - Đóng gói ZIP tự động theo quy chuẩn
```

---

## 3. Danh mục mô hình mã nguồn mở tối ưu nhất cho RTX 3050 6GB

Tất cả các mô hình dưới đây đều là mã nguồn mở 100%, được công bố trước ngày 01/08/2026 (xem cập nhật mốc mới nhất tại [01-THONG-TIN-CUOC-THI.md](01-THONG-TIN-CUOC-THI.md)), không phải API đóng và đã được benchmark an toàn trên 6 GB VRAM:

### 3.1. Mô hình Dense Embedding (Chọn 1 trong 2)
1. **`BAAI/bge-m3` (Khuyến nghị số 1):**
   - Kích thước: 567M tham số (~2.2 GB VRAM ở chế độ fp16).
   - Đặc điểm: Chuẩn của AI Guru; hỗ trợ đồng thời Tiếng Việt, Tiếng Anh, Tiếng Trung; context 8.192 tokens.
   - Lưu ý trên 6GB VRAM: Đặt `batch_size = 16` hoặc `32`, bật `torch.cuda.amp.autocast(dtype=torch.float16)`.
2. **`intfloat/multilingual-e5-base` (Phương án dự phòng siêu nhẹ):**
   - Kích thước: 278M tham số (~1.1 GB VRAM).
   - Tốc độ: Nhanh gấp 2.5 lần BGE-M3, chiếm cực ít bộ nhớ.

### 3.2. Mô hình Cross-Encoder Reranker (Chọn 1 trong 2)
1. **`BAAI/bge-reranker-v2-m3` (Khuyến nghị số 1):**
   - Backbone: XLM-RoBERTa-large (560M tham số).
   - Chi phí bộ nhớ: 1.5 GB model weights + 2.5 GB attention (khi `batch_size = 16`, `sequence_length = 1024–1536`).
   - Tổng VRAM đỉnh: **~4.0 – 4.5 GB** (hoàn toàn nằm trong hạn mức 6GB của RTX 3050).
2. **`cross-encoder/ms-marco-MiniLM-L-6-v2` hoặc `bge-reranker-base` (Dự phòng siêu tốc):**
   - Kích thước: ~1.1 GB VRAM, thời gian rerank chỉ 0.3s/query.

### 3.3. Mô hình Query Expansion / Medical Translation (Nếu không dùng từ điển)
- **`Qwen/Qwen2.5-1.5B-Instruct` (hoặc bản lượng tử hóa Q4_K_M GGUF):**
  - Chỉ chiếm **1.1 GB VRAM** chạy qua `llama-cpp-python`.
  - Khả năng dịch thuật y khoa Việt - Anh - Trung rất mạnh, vượt trội các model cũ.

---

## 4. Ba kỹ thuật lập trình chống tràn RAM (16 GB) và VRAM (6 GB)

1. **Kỹ thuật xử lý bằng Generator (Zero RAM Bloat):**
   - Không dùng `data = [json.loads(line) for line in open('file.jsonl')]`.
   - Dùng generator `for line in open(...)` hoặc thư viện **`polars`** đọc streaming theo lô 10.000 bản ghi.

2. **Giải phóng bộ nhớ chủ động giữa các bước (Explicit GC):**
   ```python
   import gc, torch
   def release_gpu():
       gc.collect()
       if torch.cuda.is_available():
           torch.cuda.empty_cache()
           torch.cuda.ipc_collect()
   ```

3. **Giảm kích thước sequence_length khi rerank trên Local:**
   - Thay vì để mặc định 2.048 token, cắt gọn xuống **1.024 hoặc 1.280 tokens** (đủ chứa query + 1 chunk y khoa 400 token + context xung quanh).
   - Giảm $L$ từ 2048 xuống 1024 làm giảm bộ nhớ attention xuống **4 lần** ($L^2$), giúp VRAM hạ từ 4.0 GB xuống còn dưới 1.5 GB!

---

## 5. Danh sách thư viện mã nguồn mở cần dùng

| Tác vụ | Thư viện / Công cụ | Ưu điểm vượt trội trên máy cá nhân |
| :--- | :--- | :--- |
| Crawl nhanh | `httpx` + `trafilatura` | Async, ~100 pages/s, 0 VRAM, RAM < 300MB |
| Crawl JS/SPA | `crawl4ai` | Playwright, Memory-Adaptive Dispatcher tự bóp luồng tránh OOM |
| Search PubMed | Europe PMC REST API | Miễn phí, không cần API key, trả JSON trực tiếp |
| Storage & Table | `polars` / `duckdb` | Đọc file lớn nhanh gấp 10 lần pandas, không tốn RAM |
| Search Engine | `tantivy` (Python binding) | Rust engine, chạy trên NVMe SSD ổ E, 0 GB VRAM |
| Embedding & Rerank | `sentence-transformers` | fp16, hỗ trợ BGE-M3 và BGE-Reranker-v2-m3 |
| Lượng tử hóa LLM | `llama-cpp-python` (nếu dùng Qwen 1.5B/7B) | Chạy model 4-bit cực nhẹ, tiết kiệm 70% VRAM |
