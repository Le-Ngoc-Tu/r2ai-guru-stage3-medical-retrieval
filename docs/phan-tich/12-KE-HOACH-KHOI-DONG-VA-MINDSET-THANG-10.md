# Kế hoạch Khởi động và Mindset Thực thi Tháng 10/2026

Tài liệu chốt trạng thái toàn bộ giai đoạn nghiên cứu (18/09 – 29/09/2026) và chuẩn bị mindset thực thi. **[CẬP NHẬT 01/10/2026]**: Public Test đã mở, dữ liệu thật đã về, crawl đang chạy. Trạng thái tuần tự theo giai đoạn (Phase Gate) nay được theo dõi tập trung tại **[AGENTS.md](../NHAT-KY-DU-AN.md)** (gốc repo) — đọc file đó trước để biết đang ở giai đoạn nào, tài liệu này giữ vai trò digest nghiên cứu + mindset, không lặp lại bảng trạng thái.

---

## 1. Hiện trạng đã xác minh trên máy thật — lịch sử 29/09 → 01/10/2026

**[ĐÃ XONG — không còn đúng ở bản 29/09]** Môi trường `.venv` lúc đó trống hoàn toàn; đến 01/10 đã cài xong `httpx`, `trafilatura`, `polars`, `orjson` và `url_crawler.py` đã chạy thật (xem [AGENTS.md](../NHAT-KY-DU-AN.md) mục 3 để biết số liệu crawl mới nhất). PyTorch/sentence-transformers/tantivy vẫn CHƯA cài — chỉ cần khi vào Giai đoạn 3-4 (chunking/indexing), không cần cho crawl.

Ghi chú lịch sử (giữ lại để hiểu bối cảnh quyết định): tại 29/09/2026, `.venv` hoàn toàn trống, code chỉ có `mock_data.py` và `pubmed_client.py`, và 6 module (`url_crawler.py`, `medical_chunker.py`, `tantivy_indexer.py`, `eval_f2.py`, `validate_submission.py`, `pipeline_orchestrator.py`) đều chưa viết. Tới 01/10 đã viết và chạy thật `url_crawler.py`; 5 module còn lại vẫn chưa viết — đúng theo luật tuần tự ở AGENTS.md (chưa cần viết `medical_chunker.py` khi Giai đoạn 1 crawl chưa xong).

---

## 2. Tóm tắt nghiên cứu đã chốt (digest nhanh, không cần đọc lại 11 file)

| Doc | Chốt gì |
| :--- | :--- |
| 01 | Thể lệ chính thức: model ≤15B/model, public trước 01/08/2026, không cần license thương mại; **`relevant_chunks` phải là `chunk_text` thật**, không phải `chunk_id`; deadline 31/10 Public, 04/11 Private. |
| 02 | Công thức F2 macro: Document-level set-based trên `doc_id`; Chunk-level theo content-overlap trên `chunk_text` (Precision = chunk relevant/tổng trả về, Recall = số phần thông tin cần thiết được phủ/tổng số phần thông tin cần thiết). |
| 03 | 6 bài học Stage 2 chuyển hóa sang Stage 3 + chốt danh mục công nghệ (trafilatura/crawl4ai, Tantivy, BGE-M3, BGE-reranker-v2-m3). |
| 04 | Kiến trúc 3 giai đoạn: Query Expansion → Hybrid Retrieval (Sparse+Dense+RRF) → Two-tier Reranking & Chunk Pinpointing. |
| 05 | Lộ trình 4 giai đoạn theo mốc thời gian thật của BTC. |
| 06 | Đặc tả JSONL gốc (lưu ý: một phần đã lỗi thời do BTC đổi thể lệ 26/09 — không còn nhận KB cắt sẵn). |
| 07 | Bi-Encoder vs Cross-Encoder, VRAM budget reranker trên 6GB, 5 hướng nghiên cứu áp dụng. |
| 08 | BTC chuyển toàn bộ Data Engineering cho đội thi tự làm; xác nhận chính thức cách chấm `chunk_text`. |
| 09 | Crawl4AI hợp lệ thể lệ, dùng làm fallback cho trang SPA. |
| 10 | Kiến trúc 5 giai đoạn tách rời, danh mục model theo VRAM budget 6GB. |
| 11 | Rà soát kỹ thuật 2026: binary/scalar quantization cho vector index (giải bài toán RAM 30-100M chunk), Contextual Retrieval nâng cấp chunking, ứng viên Qwen3-Embedding/Reranker cần tự đo trước khi đổi baseline. |

---

## 3. Checklist — trạng thái 01/10/2026 (đã chạy thật, không còn là dự kiến)

1. ~~Dựng `.venv`~~ — **XONG** (httpx/trafilatura/polars), PyTorch/tantivy để dành cho Giai đoạn 3-4.
2. **Vẫn còn thiếu**: `faiss-cpu` chưa thêm vào `requirements.txt` — cần trước khi vào Giai đoạn 4 (Binary/Scalar Quantization, doc 11 mục 4). Chưa gấp vì crawl (Giai đoạn 1) chưa xong.
3. `eval_f2.py` — **CHƯA VIẾT**, đúng theo luật tuần tự ở [AGENTS.md](../NHAT-KY-DU-AN.md) (chưa cần đo gì khi chưa có chunk nào tồn tại). Sẽ viết ở Giai đoạn 5, không viết trước.
4. `validate_submission.py`, `medical_chunker.py`, `tantivy_indexer.py`, `pipeline_orchestrator.py` — **CHƯA VIẾT**, đều thuộc Giai đoạn 3 trở đi, chủ động KHÔNG viết trước khi Giai đoạn 1 (crawl) hoàn tất, để tránh code dựa trên giả định về dữ liệu chưa kiểm chứng (ví dụ format chunk có thể cần điều chỉnh sau khi thấy rõ đặc điểm nội dung thật — xem quan sát chất lượng ở AGENTS.md mục 3).
5. ~~Viết `url_crawler.py`~~ — **ĐANG CHẠY THẬT**, không phải thử nghiệm trên mock_data nữa.

---

## 4. Mindset thực thi khi bắt đầu tháng 10

### 4.1. Đo trước, tối ưu sau (bài học số 1 Stage 2)
Ngày đầu tiên có data thật (01/10), việc đầu tiên KHÔNG PHẢI là chạy full pipeline để nộp bài — mà là chạy `eval_f2.py` trên một mẫu nhỏ để biết đang đứng ở đâu, tách rõ $F_{2,doc}$ và $F_{2,chunk}$. Không đoán mù thứ đang hỏng ở tầng nào.

### 4.2. Đừng tự thêm ràng buộc không có (bài học số 6 Stage 2)
Ranh giới thật là **6GB VRAM và 16GB RAM của máy cá nhân**, không phải "phải dùng model nhỏ nhất có thể". Trong ngân sách đó, ưu tiên chất lượng retrieval trước, không tự siết xuống model nhẹ hơn cần thiết chỉ vì cảm giác "an toàn".

### 4.3. Phân loại trước khi hỏi (Classify Before Asking)
Câu hỏi "model A hay B tốt hơn cho domain y khoa" là sự thật đo được — tự chạy `eval_f2.py` trên mock dev set để trả lời, không hỏi lại người dùng những gì có thể tự thực nghiệm. Chỉ hỏi khi chạm ranh giới quyết định của BTC (ví dụ license, quy định thể lệ chưa rõ) như đã làm ở doc 08 mục 4 phần 2 (quy mô danh sách URL, doc_id có được BTC cấp sẵn hay không) — hai câu này vẫn còn mở, cần hỏi BTC ngay khi có kênh giải đáp ngày 01/10.

### 4.4. Đơn giản trước (Simplicity First)
Baseline đầu tiên nộp lên leaderboard nên là **Sparse BM25 thuần túy qua Tantivy** (đã chốt ở doc 05 mục 3, ngày 04-10/10) — không chờ đến khi có đủ Hybrid Retrieval + Reranking mới nộp bài đầu tiên. Biết điểm baseline sớm để có cơ sở so sánh mọi cải tiến sau đó.

### 4.5. Ghi ngõ cụt đúng phạm vi (bài học số 4 Stage 2)
Nếu một hướng thử nghiệm không cải thiện điểm, ghi rõ **phạm vi hẹp nhất mà phép đo bác bỏ** (ví dụ "tăng top_k từ 50 lên 100 ở Tầng 1 không cải thiện $F_{2,chunk}$ trên mock dev set 500 câu"), không tổng quát hóa thành "mở rộng candidate pool không có tác dụng".

### 4.6. Verification-Driven Development
Không báo "xong" khi code chạy không lỗi — phải có bằng chứng thực nghiệm cụ thể (log điểm F2, benchmark VRAM thật, kết quả `validate_submission.py` pass) trước khi coi một bước là hoàn thành.

---

## 5. Rủi ro / điều chưa chốt

1. ~~Quy mô danh sách URL~~ — **ĐÃ RÕ**: chính xác 4.394.718 URL trong `links_corpus.parquet`, chỉ Việt + Trung.
2. ~~`doc_id` cấp sẵn hay tự đặt~~ — **ĐÃ RÕ**: `doc_id` = trường `id` số nguyên có sẵn trong `links_corpus.parquet`, không tự đặt tên.
3. Checkpoint fine-tune y khoa (MedEmbed / claim "MMed-Embed") — vẫn **CHƯA XÁC MINH**, cần tự tải và đo trước khi dùng. Đã tìm thêm ứng viên tiếng Trung chuyên biệt (`CARE`/`CMedTEB`) — xem [13-NGHIEN-CUU-OPENSOURCE-BO-SUNG.md](13-NGHIEN-CUU-OPENSOURCE-BO-SUNG.md).
4. **Rủi ro mới (01/10)**: tốc độ crawl hiện tại (~4,3 req/s, đo trên phần site Việt Nam) cho ETA ~11,8 ngày nếu giữ nguyên suốt — chiếm ~40% ngân sách 30 ngày Public Test. Tốc độ thật trên 63%+ corpus còn lại (domain Trung Quốc) CHƯA được đo dưới tải sustained. Theo dõi sát ở [AGENTS.md](../NHAT-KY-DU-AN.md) mục 3.

---

## 6. Liên kết

- **Trạng thái giai đoạn + luật thực thi tuần tự (nguồn chính thức, cập nhật liên tục)**: [AGENTS.md](../NHAT-KY-DU-AN.md)
- Lộ trình gốc theo mốc thời gian: [05-KE-HOACH-HANH-DONG.md](05-KE-HOACH-HANH-DONG.md)
- Thể lệ và schema bài nộp chính thức: [01-THONG-TIN-CUOC-THI.md](01-THONG-TIN-CUOC-THI.md)
- Kỹ thuật mới cần thực nghiệm: [11-NGHIEN-CUU-KY-THUAT-MOI-NHAT-2026.md](11-NGHIEN-CUU-KY-THUAT-MOI-NHAT-2026.md)
