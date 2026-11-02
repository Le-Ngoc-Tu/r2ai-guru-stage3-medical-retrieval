# Thay đổi Thể lệ Data Pipeline (Cập nhật 26/09/2026)

Tài liệu phân tích bước ngoặt chiến lược từ thông báo mới nhất của Ban Tổ chức cuộc thi trên `https://leaderboard.aiguru.com.vn/competitions/15/`: **BTC không cung cấp kho chunk sẵn nữa, mà chuyển giao toàn bộ quy trình Data Engineering (Crawl, PubMed API, Preprocessing, Chunking) cho các đội thi tự thực hiện.**

---

## 1. Nội dung thay đổi từ Ban Tổ chức

| Thành phần dữ liệu | Thể lệ cũ | Thể lệ mới (Chính thức) |
| :--- | :--- | :--- |
| **Tiếng Việt & Tiếng Trung** | Cung cấp sẵn file hàng chục triệu chunk đã cắt sẵn | **Chỉ cung cấp danh sách URL**. Đội thi phải tự crawl nội dung, tiền xử lý, làm sạch HTML và tự phân đoạn (chunking). |
| **Tiếng Anh** | Cung cấp sẵn tập chunk tiếng Anh | **Không cung cấp bất kỳ danh sách tài liệu nào**. Giới hạn phạm vi ở cơ sở dữ liệu PubMed (~36 triệu bài). Đội thi chủ động tìm kiếm bài phù hợp qua API (NCBI Entrez, Europe PMC, PubTator) rồi tự thu thập và chunking. |
| **Phạm vi đánh giá** | Thuần túy mô hình Retrieval & Rerank | **Đánh giá toàn diện cả năng lực Data Engineering**: Từ thu thập -> làm sạch -> chunking -> corpus indexing -> retrieval. |

---

## 2. Giải mã chiến lược kỹ thuật mới (Technical Blueprint)

Sự thay đổi này biến cuộc thi từ "tìm kiếm trên kho đóng" thành **"Open-domain Search & Data Processing"**. Các đội mạnh về mô hình nhưng yếu về Data Engineering sẽ bị tắc nghẽn ngay từ khâu crawl và xử lý dữ liệu.

```
[Danh sách URL Việt/Trung từ BTC]       [Tập câu hỏi truy vấn Test Set (Vi)]
                |                                       |
                v                                       v
    +-----------------------+              +--------------------------+
    | Async URL Crawler     |              | Cross-lingual Expansion  |
    | (httpx + trafilatura) |              | Việt -> MeSH / English   |
    +-----------------------+              +--------------------------+
                |                                       |
                |                                       v
                |                          +--------------------------+
                |                          | PubMed Search API        |
                |                          | (Europe PMC / Entrez)    |
                |                          +--------------------------+
                |                                       |
                |                                       v
                |                          +--------------------------+
                |                          | Fetch PubMed Abstracts   |
                |                          | & PMC Fulltexts          |
                |                          +--------------------------+
                |                                       |
                +-------------------+-------------------+
                                    |
                                    v
                    +-------------------------------+
                    | Text Cleaning & Normalization |
                    | (Bỏ boilerplate, menu, quảng  |
                    |  cáo, giữ nguyên tiêu đề)     |
                    +-------------------------------+
                                    |
                                    v
                    +-------------------------------+
                    | Context-Preserving Chunking   |
                    | (Giữ doc_id, chunk_index,     |
                    |  title, chunk_index +-1)      |
                    +-------------------------------+
                                    |
                                    v
                    +-------------------------------+
                    | Dynamic Corpus & Indexing     |
                    | (Tantivy BM25 + BGE-M3 Embed) |
                    +-------------------------------+
                                    |
                                    v
                    +-------------------------------+
                    | Two-tier Retrieval & Rerank   |
                    | -> Xuất JSON nộp Leaderboard  |
                    +-------------------------------+
```

---

## 3. Chiến lược xử lý cho từng nhánh dữ liệu

### 3.1. Nhánh Tiếng Việt & Tiếng Trung: Async URL Crawler & Content Extractor
- Danh sách URL do BTC cấp có thể lên tới hàng chục ngàn hoặc hàng trăm ngàn liên kết.
- Không dùng requests tuần tự; phải dùng **`httpx` asynchronous + `asyncio`** kèm cơ chế rate limiting, retry backoff (3 lần) và timeout an toàn (10–15 giây/request).
- Bóc tách văn bản sạch (Main Content Extraction):
  - Không parse HTML bằng regex hay BeautifulSoup thủ công để tránh dính menu, footer, sidebar.
  - Sử dụng **`trafilatura`** (thư viện mã nguồn mở tối ưu nhất hiện nay cho việc tách bài viết, hỗ trợ cả tiếng Việt lẫn tiếng Trung, loại bỏ 99% nội dung rác).
- Tiếng Trung đặc thù: Cần kiểm tra và ép encoding UTF-8 chuẩn xác, loại bỏ ký tự lỗi.

### 3.2. Nhánh Tiếng Anh: Query-driven Focused PubMed Retrieval
- PubMed có hơn 36 triệu bài báo y sinh. **Không thể và không cần thiết phải crawl toàn bộ PubMed về máy.**
- Chiến lược tối ưu là **Query-driven Focused Retrieval**:
  1. Với mỗi câu hỏi tiếng Việt trong tập Test, trích xuất thực thể y sinh (tên bệnh, thuốc, triệu chứng) và dịch sang thuật ngữ MeSH / tiếng Anh qua model mã nguồn mở (Qwen2.5) hoặc từ điển UMLS.
  2. Gọi API tìm kiếm để lấy Top 50–100 PMIDs (PubMed IDs) phù hợp nhất:
     - **Europe PMC REST API**: Khuyến nghị sử dụng vì tốc độ phản hồi nhanh hơn Entrez, trả về JSON trực tiếp và có sẵn trình trích xuất cả abstract lẫn open-access full-text.
     - **NCBI Entrez E-utilities** (`esearch` + `efetch`): Cung cấp kèm API Key để tăng hạn mức lên 10 requests/giây.
     - **PubTator**: Hiển thị thêm các thực thể bệnh lý đã được gán nhãn sẵn.
  3. Tải Abstract (và Fulltext nếu có) của các bài viết tìm được, tạo thành tập tài liệu ứng viên tiếng Anh cho truy vấn.

### 3.3. Chiến lược Chunking (Do đội thi tự thiết kế)
Khi BTC trao quyền tự chunking cho đội thi, chúng ta cần áp dụng ngay **Bài học số 3 từ Stage 2 (Giữ ngữ cảnh, đừng làm phẳng)**:
- Độ dài chunk lý tưởng: 256–512 tokens (hoặc 800–1200 ký tự), có độ gối đầu (overlap 100–150 ký tự).
- Lưu trữ bắt buộc các trường metadata kèm theo mỗi chunk:
  - `doc_id`: Mã tài liệu (hoặc URL gốc / PMID).
  - `chunk_id`: `{doc_id}_c{chunk_index:03d}`.
  - `chunk_index`: Vị trí thứ tự trong tài liệu.
  - `doc_title`: Tiêu đề bài viết gốc (để đưa vào cross-encoder context).
  - `language`: `vi`, `zh`, hoặc `en`.

---

## 4. Những câu hỏi kỹ thuật cần làm rõ vào ngày 01/10/2026

1. **Quy ước định danh `doc_id` và `chunk_id` trong file nộp:**
   - Trong file kết quả: `{"id": "q_0001", "relevant_docs": [...], "relevant_chunks": [...]}`.
   - Khi đội thi tự chunking, liệu Ban Tổ chức có cấp sẵn `doc_id` tương ứng với từng URL và từng PMID không? Hay đội thi tự đặt tên `doc_id` theo URL/PMID?
   - Danh sách `relevant_chunks` sẽ được chấm như thế nào nếu mỗi đội thi phân đoạn độ dài chunk khác nhau? (Liệu BTC chấm độ trùng lặp nội dung văn bản, hay BTC có một tập chunk chuẩn ẩn danh để đối chiếu?).

   > **[XÁC NHẬN CHÍNH THỨC 29/09/2026 — trang Phương pháp đánh giá của BTC]** Câu hỏi này đã được giải quyết dứt điểm, không còn là suy đoán: độ đo Document-level giữ nguyên set-based trên `doc_id`, còn độ đo Chunk-level vận hành trực tiếp trên **`chunk_text`** (nội dung text thật do đội thi tự chunking và nộp), KHÔNG đối chiếu với một tập chunk chuẩn ẩn danh cố định. Với mỗi câu hỏi, BTC đã xác định trước tài liệu gốc và tập các phần thông tin cần thiết ($I$); một chunk nộp được tính relevant nếu nội dung khớp/overlap đủ với ít nhất một phần tử của $I$. Precision = số chunk relevant / tổng chunk trả về; Recall = số phần tử của $I$ được bao phủ / $|I|$. Công thức đầy đủ xem [02-DANH-GIA-VA-CONG-THUC-F2.md](02-DANH-GIA-VA-CONG-THUC-F2.md) mục 1.2. **Khuyến nghị của BTC: mỗi chunk không nên dài quá ~1.024 tokens.** Mục tiêu chunking hiện tại của hệ thống (300–500 / 256–512 tokens, xem mục 3.3) đã nằm sâu mức trần này nên không cần điều chỉnh chiến lược chunking.
   > Hệ quả trực tiếp cho định dạng bài nộp: trường `relevant_chunks` trong file JSON PHẢI chứa `chunk_text` thật, không phải `chunk_id` tham chiếu — [01-THONG-TIN-CUOC-THI.md](01-THONG-TIN-CUOC-THI.md) mục 6 đã được cập nhật theo xác nhận này.
2. **Quy mô danh sách URL:**
   - Có tổng cộng bao nhiêu URL tiếng Việt và tiếng Trung? (Hàng ngàn hay hàng triệu?).
   - Có URL nào yêu cầu đăng nhập hoặc JavaScript rendering (SPA) không?

---

## 5. Các module cần lập trình sẵn sàng trước ngày 01/10/2026

1. `url_crawler.py`: Async crawler đọc danh sách URL, parse text bằng `trafilatura`, lưu kết quả vào sqlite/parquet.
2. `pubmed_client.py`: Client truy vấn Europe PMC / NCBI Entrez, nhận truy vấn y khoa và tải abstract/fulltext về theo PMID.
3. `medical_chunker.py`: Engine phân đoạn văn bản giữ ngữ cảnh và metadata phục vụ ranking.
4. `pipeline_orchestrator.py`: Kết nối từ khâu nạp URL/PubMed đến chỉ mục Tantivy và Reranking.
