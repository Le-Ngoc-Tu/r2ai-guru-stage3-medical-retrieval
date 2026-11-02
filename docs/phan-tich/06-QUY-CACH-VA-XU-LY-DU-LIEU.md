# Quy cách và Chiến lược Xử lý Dữ liệu Stage 3

> **[ĐÃ LỖI THỜI — chỉ giữ để tham khảo lịch sử]** Toàn bộ mục 1 dưới đây mô tả đặc tả TRƯỚC ngày 26/09/2026, khi BTC còn dự kiến cấp sẵn kho chunk với `chunk_id`/`doc_id` kiểu chuỗi (`"d_12345678"`). Thực tế đã xác nhận: BTC không cấp kho chunk sẵn, `doc_id` là **số nguyên** trùng `id` trong `links_corpus.parquet`, và bài nộp dùng `chunk_text` chứ không phải `chunk_id` tham chiếu. Xem đặc tả CHÍNH THỨC hiện hành tại [01-THONG-TIN-CUOC-THI.md](01-THONG-TIN-CUOC-THI.md) mục 6 và [08-THAY-DOI-THE-LE-DATA-PIPELINE.md](08-THAY-DOI-THE-LE-DATA-PIPELINE.md).

Tài liệu phân tích đặc tả kỹ thuật dữ liệu chính thức từ Ban Tổ chức và đề xuất phương án xử lý dữ liệu quy mô lớn (Big Data Ingestion Pipeline) cho kho tài liệu hàng chục triệu bản ghi.

---

## 1. Đặc tả chi tiết cấu trúc dữ liệu gốc

### 1.1. Tập câu hỏi truy vấn (Test Set)
- Định dạng file: JSON Lines (`.jsonl`).
- Mỗi dòng là một JSON object độc lập đại diện cho một truy vấn y học:
```json
{
  "id": "q_0001",
  "query": "Cần làm gì đối với tình trạng tắc nghẽn đường tiết niệu do sỏi thận?"
}
```
- Trường `id`: Chuỗi định danh duy nhất của câu hỏi (khóa chính dùng cho bài nộp).
- Trường `query`: Câu hỏi lâm sàng hoặc thuật ngữ y tế hoàn toàn bằng tiếng Việt.

### 1.2. Kho tài liệu y khoa đa ngôn ngữ (Knowledge Base)
- Định dạng: Tập hợp các chunk văn bản y học (tiếng Việt, tiếng Anh, tiếng Trung).
- Cấu trúc mỗi bản ghi:
```json
{
  "chunk_id": "d_12345678_c000",
  "doc_id": "d_12345678",
  "chunk_index": 0,
  "text": "This document discusses urinary tract obstruction caused by kidney stones."
}
```
- Trường `chunk_id`: Mã chunk duy nhất toàn cục.
- Trường `doc_id`: Mã tài liệu gốc mà chunk thuộc về.
- Trường `chunk_index`: Số nguyên $\ge 0$, chỉ vị trí thứ tự của chunk trong tài liệu gốc.
- Trường `text`: Đoạn nội dung văn bản ở ngôn ngữ gốc (Việt, Anh, hoặc Trung).

---

## 2. Phân tích kỹ thuật quan trọng từ đặc tả

1. Phím tắt quy ước định danh:
   Ví dụ của BTC cho thấy format: `d_12345678_c000` = `{doc_id}_c{chunk_index:03d}`.
   Quan hệ 1-N giữa tài liệu và chunk thể hiện rõ ở cả trường `doc_id` lẫn cấu trúc mã `chunk_id`.

2. Khả năng tái lập cấu trúc tài liệu (Document Reconstruction):
   Nhờ trường `chunk_index`, hệ thống có thể xếp lại toàn bộ các chunk theo đúng thứ tự ban đầu để tạo ra bản văn hoàn chỉnh của một tài liệu hoặc lấy ngữ cảnh lân cận (`chunk_index \pm 1`) mà không cần crawl lại nguồn gốc.

3. Cảnh báo quy mô dữ liệu:
   BTC nêu: *"quy mô hàng chục triệu tài liệu, đã được phân đoạn sẵn thành các chunk"*.
   Nếu có 10–20 triệu tài liệu, mỗi tài liệu trung bình 3–5 chunk, tổng số chunk có thể lên tới **30–100 triệu chunk**.
   Tuyệt đối không đọc toàn bộ file vào bộ nhớ RAM (cấm dùng `json.load()` trực tiếp trên toàn bộ file).

4. Quy tắc phân đoạn (Chunking Rules):
   BTC sẽ công bố quy tắc phân đoạn cùng với dữ liệu (độ dài token, có overlap hay không). Thông tin này sẽ giúp tính toán độ dài của context window khi rerank.

---

## 3. Chiến lược kỹ thuật xử lý dữ liệu (Data Pipeline)

### 3.1. Đọc dữ liệu dạng dòng chảy (Streaming / Chunked Reading)
- Sử dụng trình đọc từng dòng (`streaming jsonl`) hoặc engine đọc hiệu năng cao bằng Rust/Python như `polars` hoặc `orjson`.
- Xử lý phân đoạn theo batch 50.000 – 100.000 bản ghi mỗi lần để đẩy vào bộ index Tantivy.

### 3.2. Lập chỉ mục 2 tầng trên đĩa (Zero GPU Memory)
- Sử dụng **Tantivy** để tạo chỉ mục ngược (inverted index) trực tiếp trên đĩa SSD:
  - Chỉ mục trường `text` với bộ phân tích đa ngôn ngữ (multilingual analyzer).
  - Lưu trữ kèm các trường metadata nhanh: `doc_id` (kiểu facet hoặc string nhanh), `chunk_index` (kiểu integer), `chunk_id` (kiểu string khóa chính).
- Tra cứu Sparse BM25 theo cả 2 chế độ:
  - Tra cứu cấp Chunk: tìm trực tiếp `chunk_id` phù hợp nhất.
  - Tra cứu cấp Doc: gộp điểm các chunk theo `doc_id` để lấy danh sách tài liệu ứng viên.

### 3.3. Xây dựng bộ dữ liệu kiểm thử nội bộ (Mock Dev Set)
Do BTC không cung cấp tập train/dev, cần xây dựng bộ mock data theo đúng schema để chạy kiểm thử hệ thống từ trước ngày 01/10/2026.
