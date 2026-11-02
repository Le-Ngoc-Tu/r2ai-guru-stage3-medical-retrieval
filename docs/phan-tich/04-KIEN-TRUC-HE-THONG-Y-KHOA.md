# Kiến trúc Hệ thống: Truy hồi Y khoa Đa ngôn ngữ Quy mô lớn

Tài liệu thiết kế chi tiết kiến trúc hệ thống truy hồi thông tin y sinh 2 tầng (Document và Chunk) đáp ứng bài toán hàng chục triệu chunk đa ngôn ngữ (Tiếng Việt, Tiếng Anh, Tiếng Trung).

---

## 1. Bốn thách thức kỹ thuật cốt lõi

1. Thách thức quy mô (Scale):
   Kho dữ liệu hàng chục triệu chunk (ước tính 10–30 triệu bản ghi). Nếu sử dụng dense vector 1024 chiều (float16), chỉ riêng bộ nhớ chứa vector đã mất 20–60 GB RAM. Không thể quét toàn bộ dense vector brute-force trên máy cá nhân.

2. Thách thức xuyên ngôn ngữ (Cross-lingual Gap):
   Truy vấn 100% bằng tiếng Việt nhưng kho tri thức nằm chủ yếu ở tiếng Anh và tiếng Trung. So khớp từ khóa thuần túy (keyword match) sẽ hoàn toàn bất lực khi tìm tài liệu tiếng Anh hoặc tiếng Trung.

3. Thách thức ngữ nghĩa y sinh (Biomedical Semantics):
   Từ ngữ y học có tính đa dạng cao: tên thuốc quốc tế (INN), biệt dược, mã ICD, tên khoa học bệnh, và mô tả triệu chứng dân gian bằng tiếng Việt.

4. Không có tập Train/Dev chính thức:
   Ban Tổ chức không cung cấp dữ liệu mẫu có nhãn để calibrate mô hình. Đội thi phải tự dựng dữ liệu kiểm thử nội bộ (Synthetic Dev Set).

---

## 2. Kiến trúc tổng thể 3 giai đoạn (Pipeline Architecture)

Hệ thống được thiết kế theo mô hình phân lớp để tối ưu giữa tốc độ lọc và độ chính xác ngữ nghĩa:

```
[Truy vấn tiếng Việt]
       |
       v
+-------------------------------------------------------------+
| Giai đoạn 1: Xử lý truy vấn & Mở rộng đa ngôn ngữ            |
| - Chuẩn hóa thuật ngữ y khoa (MeSH / UMLS)                   |
| - Phát âm / Định danh thực thể (Bệnh, Triệu chứng, Thuốc)    |
| - Sinh truy vấn song ngữ Anh - Trung qua open model          |
+-------------------------------------------------------------+
       |
       v
+-------------------------------------------------------------+
| Giai đoạn 2: Truy hồi ứng viên quy mô lớn (Hàng chục triệu)  |
| - Sparse Search (Tantivy / BM25 đa ngôn ngữ): Lọc thô disk   |
| - Dense Multi-lingual Embedding (BGE-M3 / Multi-E5)          |
| - Reciprocal Rank Fusion (RRF) -> Top 200 docs / 500 chunks |
+-------------------------------------------------------------+
       |
       v
+-------------------------------------------------------------+
| Giai đoạn 3: Xếp hạng 2 tầng & Định vị Chunk (Pinpointing)   |
| - Tầng 1: Gộp điểm tài liệu (Document Score Aggregation)     |
| - Tầng 2: Cross-Encoder Reranker kèm context window (+-1)    |
| - Dynamic Thresholding: Chọn relevant_docs & relevant_chunks |
+-------------------------------------------------------------+
       |
       v
[File JSON -> Nén ZIP nộp Leaderboard]
```

---

## 3. Chi tiết từng thành phần kỹ thuật

### 3.1. Giai đoạn 1: Xử lý truy vấn & Mở rộng đa ngôn ngữ (Query Expansion)
- Thư viện tách từ tiếng Việt chuyên ngành: Kết hợp underthesea hoặc pyvi.
- Tra cứu thuật ngữ y học: Xây dựng từ điển mapping thuật ngữ y khoa Việt - Anh - Trung dựa trên MeSH (Medical Subject Headings) và UMLS sẵn có.
- Sinh truy vấn đa ngôn ngữ: Sử dụng LLM mã nguồn mở nhẹ (ví dụ Qwen2.5-7B-Instruct chạy 4-bit) để trích xuất ý định lâm sàng và dịch/mở rộng truy vấn sang tiếng Anh và tiếng Trung chuyên ngành.

### 3.2. Giai đoạn 2: Bộ lọc ứng viên Sparse + Dense quy mô lớn
- Công cụ chỉ mục Sparse: **Tantivy** (thư viện search engine bằng Rust, tốc độ vượt trội Lucene, chạy trực tiếp trên đĩa cứng, không tốn VRAM GPU).
  - Hỗ trợ tokenizer chuyên biệt: tiếng Việt (whitespace/ngram), tiếng Trung (jieba), tiếng Anh (stemming).
- Mô hình Dense Embedding xuyên ngôn ngữ: **BAAI/bge-m3** (hỗ trợ đồng thời Tiếng Việt, Tiếng Anh, Tiếng Trung, độ dài ngữ cảnh 8192 tokens, hỗ trợ cả dense lẫn sparse lexical weights).
- Fusion: Kết hợp điểm số BM25 và Vector Cosine qua công thức RRF (Reciprocal Rank Fusion):
  $$RRF\_Score(d) = \sum_{m \in \{BM25, Dense\}} \frac{1}{60 + Rank_m(d)}$$
  Thu hẹp không gian tìm kiếm từ 10+ triệu chunk xuống Top 200 tài liệu và Top 500 chunk ứng viên.

### 3.3. Giai đoạn 3: Two-tier Reranking & Chunk Pinpointing
- Giữ nguyên tắc Stage 2: Không suy diễn mọi chunk đều liên quan.
- Tính điểm tài liệu (Document Level):
  $$Score_{doc}(D) = \max_{c \in D}(Score_{chunk}(c)) + \alpha \cdot \frac{1}{|D_{cand}|} \sum_{c \in D_{cand}} Score_{chunk}(c)$$
- Định vị chunk (Chunk Level):
  - Lấy các chunk thuộc Top tài liệu hàng đầu.
  - Đưa vào Cross-Encoder Reranker mạnh (ví dụ `BAAI/bge-reranker-v2-m3`).
  - **Đặc biệt quan trọng (Bài học 3 Stage 2):** Khi đưa chunk vào reranker, nối kèm nội dung của `chunk_index - 1` và `chunk_index + 1` làm context, giúp reranker không bị "trượt cửa sổ" khi chunk chỉ chứa một nửa câu điều trị.
- Bộ lọc Dynamic Thresholding:
  - Lấy toàn bộ chunk có điểm rerank thỏa mãn cả 2 điều kiện: điểm vượt ngưỡng cơ sở và không chênh quá biên độ so với chunk đứng đầu.

---

## 4. Xây dựng tập đánh giá nội bộ (Synthetic Dev Set)

Do Ban Tổ chức không cung cấp tập train/dev, việc đánh giá chặt chẽ trước ngày nộp là yếu tố quyết định.

**[ĐÃ CẬP NHẬT 01/10/2026]** Dữ liệu thật (`data/ViBioMIR/links_corpus.parquet`) xác nhận corpus **chỉ có tiếng Việt và tiếng Trung, KHÔNG có tiếng Anh** (xem phân tích domain trong [12-KE-HOACH-KHOI-DONG-VA-MINDSET-THANG-10.md](12-KE-HOACH-KHOI-DONG-VA-MINDSET-THANG-10.md)). Danh sách dữ liệu mẫu PubMedQA/MedMCQA/BioASQ (tiếng Anh) dưới đây **không còn phù hợp** — thay bằng các tập dữ liệu y tế mở tiếng Việt/Trung đã xác minh qua nghiên cứu [13-NGHIEN-CUU-OPENSOURCE-BO-SUNG.md](13-NGHIEN-CUU-OPENSOURCE-BO-SUNG.md):

1. Nguồn dữ liệu mẫu (đã sửa theo đúng ngôn ngữ corpus thật):
   - Tiếng Việt: `tarudesu/ViHealthQA` (10.015 cặp câu hỏi-đáp y tế từ các trang sức khỏe tiếng Việt).
   - Tiếng Trung: `webMedQA` (63.284 câu hỏi, nguồn 120Ask + Baidu Doctor — **120Ask trùng trực tiếp với domain `www.120ask.com` chiếm ~21% corpus**), `cMedQA2` (108.000 câu hỏi), hoặc `FreedomIntelligence/Huatuo26M-Lite` (bản rút gọn của Huatuo-26M, nguồn gồm 39Health-KG tương ứng domain `39.net` trong corpus).
2. Xây dựng 300–500 cặp câu hỏi - tài liệu - chunk chuẩn bằng phương pháp bán tự động (LLM tạo câu hỏi từ chunk y khoa, sau đó chuyên gia/người kiểm thử kiểm tra lại).
3. Chạy script tính F2 macro tách tầng (tương tự như `phan-tich/ba_ben.py`) để tune các siêu tham số ngưỡng cắt trước khi chấm điểm thật trên leaderboard.
