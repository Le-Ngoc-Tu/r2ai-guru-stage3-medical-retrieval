# Mindset kỹ thuật: Kế thừa và Chuyển hóa 6 Bài học từ Stage 2

Tài liệu chuyển 6 bài học từ Stage 2 và các phân tích trong [phan-tich/](../../src/stage3/) sang bài toán y khoa đa ngôn ngữ của Stage 3.

---

## 1. Đo tách tầng trước khi tối ưu bất cứ thứ gì

### Thực tế Stage 2
- Hệ thống AISOLO đạt độ trúng tài liệu 0.898 nhưng chọn đúng bảng chỉ đạt 0.421.
- Trong số bảng bỏ sót, **92.4% nằm ngay trong tài liệu đã lấy đúng**.
- Sai lầm: Suốt quá trình chỉ loay hoay sửa hàm reranker ở tầng bảng mà không nhận ra thiếu đặc trưng đầu vào.

### Chuyển hóa sang Stage 3
- Bài toán Stage 3 được BTC tách sẵn thành 2 cấp độ rõ rệt:
  - Cấp Document (`relevant_docs`)
  - Cấp Chunk (`relevant_chunks`)
- **Quy tắc ngày đầu:** Xây dựng bộ script đánh giá độc lập trên proxy dev set cho 2 tầng:
  - $Recall_{doc}$: Hệ thống có tìm ra đúng bài báo/tài liệu y khoa gốc không?
  - $Recall_{chunk|doc}$: Trong các tài liệu đã lấy đúng, hệ thống chọn đúng chunk lõi bệnh lý hay chọn lệch?
- Nếu $Recall_{doc} > 0.90$ mà $F_{2, chunk} < 0.50$, nguyên nhân nằm ở khâu chunk pinpointing, tuyệt đối không thay đổi mô hình retrieval ở tầng doc.

---

## 2. Lỗi có hình dạng — Hãy đi tìm hình dạng đó

### Thực tế Stage 2
- 33.7% khối bỏ sót chỉ cách khối hệ thống chọn dưới 50 dòng, có ca lệch đúng 4 dòng.
- Đây là lỗi "bốc nhầm khối bên cạnh trong cùng khu vực", do làm phẳng bảng làm mất tiêu đề cột.

### Chuyển hóa sang Stage 3
- Văn bản y khoa luôn tuân theo cấu trúc lâm sàng:
  `Tiêu đề bệnh -> Định nghĩa -> Triệu chứng -> Nguyên nhân -> Chẩn đoán -> Điều trị/Thuốc -> Phòng ngừa`.
- Khi hệ thống chọn sai chunk, bắt buộc đo:
  $$\Delta_{index} = |chunk\_index_{pred} - chunk\_index_{gold}|$$
- Nếu $\Delta_{index} \le 2$: Đây là lỗi "trượt cửa sổ" (window slip). Hệ thống vào đúng tài liệu, nhưng vì câu hỏi y khoa lặp lại các từ khóa giống nhau giữa đoạn "Triệu chứng" và đoạn "Điều trị", mô hình embedding bị nhầm lẫn.
- Cách chữa: Không đổi embedding, mà bổ sung semantic tag hoặc tiêu đề phân đoạn cho mỗi chunk.

---

## 3. Giữ ngữ cảnh khi dựng kho — Đừng làm phẳng

### Thực tế Stage 2
- AISOLO làm phẳng toàn bộ bảng, mất sạch ngữ cảnh bao quanh, dẫn đến mất 45% recall.

### Chuyển hóa sang Stage 3
- BTC cung cấp dữ liệu dưới dạng các chunk độc lập: `{chunk_id, doc_id, chunk_index, text}`.
- Nếu chỉ đem từng chunk đi embed một cách rời rạc, các chunk ở giữa sẽ mất hoàn toàn tiêu đề bệnh/tiêu đề tài liệu nằm ở `chunk_index = 0`.
- **Kiến trúc dựng kho:**
  - Tái lập cấu trúc tài liệu theo `doc_id`.
  - Lưu trữ kèm: Tiêu đề tài liệu (trích từ `chunk_index = 0`), nội dung chunk trước đó (`chunk_index - 1`), và nội dung chunk kế tiếp (`chunk_index + 1`).
  - Khi tính toán embedding và rerank, bổ sung ngữ cảnh bao quanh (context window expansion) để chunk giữ trọn ý nghĩa y sinh học.

---

## 4. Chọn một chiến lược theo công thức chấm và đi tới cùng

### Thực tế Stage 2
- AISOLO trả 5.58 bảng/câu nhưng Precision chỉ 0.430 vì thêm vào nhầm bảng không liên quan -> Thất bại.

### Chuyển hóa sang Stage 3
- Công thức chấm là Macro $F_2$, trong đó Recall được tính gấp 4 lần Precision.
- Chiến lược rõ ràng:
  - Tầng 1 (Document Filter): Chọn RỘNG (Lấy Top 50–100 doc ứng viên để đo phủ Recall tối đa).
  - Tầng 2 (Chunk Pinpointing): Chọn CHÍNH XÁC (Chỉ chọn 1–4 chunk có độ tương thích cao nhất trong các doc ứng viên bằng Dynamic Thresholding).
- Ghi sổ nguyên tắc: Không ghi nhận kết luận mơ hồ kiểu "tăng K làm giảm F2", mà phải ghi rõ: "Thuật toán X với tham số Y trên tập test Z làm giảm chỉ số nào".

---

## 5. Phân nhóm truy vấn y khoa và xử lý riêng biệt

### Thực tế Stage 2
- Đội giải Nhất chia 1.012 câu thành 7 nhóm (tỷ số, so sánh kỳ, lọc điều kiện...) và viết solver riêng cho từng nhóm.
- AISOLO dùng một đường ống chung cho mọi loại câu hỏi.

### Chuyển hóa sang Stage 3
- Tập câu hỏi y khoa tiếng Việt có sự phân hóa rất mạnh về chủ đích lâm sàng:
  1. Nhóm Triệu chứng & Chẩn đoán (Symptoms / Diagnostic criteria).
  2. Nhóm Điều trị & Dược lý (Treatment / Drug dosage / Pharmacology).
  3. Nhóm Nguyên nhân & Cơ chế bệnh sinh (Etiology / Pathogenesis).
  4. Nhóm Phòng ngừa & Y tế công cộng (Prevention / Public health).
  5. Nhóm Can thiệp ngoại khoa & Cấp cứu (Surgery / Emergency).
- Hướng xử lý: Sử dụng phân loại intent nhẹ ở đầu vào. Nếu câu hỏi thuộc nhóm "Điều trị", tăng trọng số từ khóa tên thuốc và bộ lọc loại bỏ các chunk thuần túy mô tả lịch sử phát hiện bệnh.

---

## 6. Ràng buộc thật là gì — Phá bỏ giới hạn 6 GB VRAM

### Thực tế Stage 2
- Quy chế Stage 2 đặt trần mô hình tối đa 14 tỷ tham số (14B).
- Máy cá nhân có card RTX 3050 6 GB VRAM.

### Chuyển hóa sang Stage 3
- **Quy tắc bất biến từ người dùng: 100% CHẠY TRÊN PHẦN CỨNG CÁ NHÂN (RTX 3050 6GB VRAM, RAM 16GB, Ổ đĩa E trống 124GB). Không dùng Cloud GPU trả phí.**
- **Kiến trúc chia nhỏ 5 giai đoạn tuần tự (Stage-wise Decoupled Pipeline):**
  Để không bao giờ bị OOM trên 6GB VRAM và 16GB RAM, hệ thống được phân tách thành 5 script độc lập chạy nối tiếp, giải phóng bộ nhớ triệt để sau mỗi bước:
  1. Giai đoạn 1 (Crawl & Ingest): `httpx` + `trafilatura` + Europe PMC API (0 GB VRAM, RAM < 500MB).
  2. Giai đoạn 2 (Chunking & Inverted Index): Cắt chunk Markdown + lập chỉ mục `Tantivy` trên ổ E (0 GB VRAM, xử lý streaming).
  3. Giai đoạn 3 (Query Expansion): Tra từ điển MeSH/UMLS hoặc `Qwen2.5-1.5B` 4-bit (~1.1 GB VRAM).
  4. Giai đoạn 4 (Candidate Retrieval): Chỉ nạp duy nhất `BAAI/bge-m3` fp16 (~2.2 GB VRAM) lọc ra Top 50 candidates, xuất file JSON rồi giải phóng GPU.
  5. Giai đoạn 5 (Two-Tier Rerank & Output): Chỉ nạp duy nhất `BAAI/bge-reranker-v2-m3` với `batch_size=16` (~4.0 GB VRAM) chấm điểm Top 50, dynamic thresholding xuất file nộp.
- Khâu nộp bài là file JSON nên toàn bộ chu trình hoàn toàn khả thi và ổn định 100% trên máy cá nhân.

---

## 7. Mindset thực chiến: Chốt danh mục công nghệ và mô hình sẽ dùng

Dựa trên 6 bài học Stage 2, đặc tả thể lệ mới nhất (26/09/2026), tài liệu đào tạo #17 của AI Guru và đánh giá công cụ Crawl4AI, hệ thống kỹ thuật sẽ được chốt như sau:

### 7.1. Thu thập & Xử lý dữ liệu (Data Ingestion)
- **Tiếng Việt & Tiếng Trung (URL Crawler):**
  - *Fast Path (80-90% trang):* `httpx` (async) + `trafilatura` (bóc tách nội dung chính sạch, tốc độ 80-120 trang/giây, không tốn VRAM).
  - *Smart Fallback (10-20% trang):* `crawl4ai` (Playwright-based, Memory-Adaptive Dispatcher để chống OOM, xử lý trang web động SPA/Next.js/React, xuất Markdown sạch).
- **Tiếng Anh (PubMed Search API):**
  - Sử dụng **Europe PMC REST API** làm công cụ chính (không cần API key, trả JSON trực tiếp, tốc độ cao) và `Bio.Entrez` (NCBI E-utilities) làm dự phòng.
  - Chiến lược Query-driven: chỉ truy vấn Top 50-100 bài báo ứng viên cho mỗi câu hỏi thay vì crawl cả PubMed.

### 7.2. Phân đoạn văn bản (Context-Preserving Chunking)
- Chọn bộ cắt Markdown Header-Aware Chunker dựa theo phân cấp `#`, `##`, `###` do `trafilatura` và `crawl4ai` sinh ra.
- Độ dài: 300–500 tokens, overlap 80–100 tokens.
- **Bắt buộc lưu kèm metadata:** `{doc_id, chunk_id, chunk_index, doc_title, language}` để không làm phẳng dữ liệu.

### 7.3. Truy hồi đa ngôn ngữ (Hybrid Multi-lingual Retrieval - Tầng 1)
- **Sparse Engine (trên đĩa SSD):** `Tantivy` (Rust-based inverted index BM25, ngốn 0 GB VRAM, hỗ trợ tokenizer Tiếng Việt `pyvi/underthesea`, Tiếng Trung `jieba`, Tiếng Anh `stemmer`).
- **Dense Embedding Model:** `BAAI/bge-m3` (baseline chuẩn của AI Guru, hỗ trợ Vi/En/Zh natively, context 8192 tokens).
- **Fusion:** `Reciprocal Rank Fusion (RRF)` kết hợp điểm số từ Tantivy BM25 + BGE-M3 Dense + BGE-M3 Sparse để chốt Top 50–100 doc/chunk ứng viên, giải quyết triệt để nguy cơ rớt 40% recall như tài liệu #17 chỉ ra.

### 7.4. Xếp hạng lại & Định vị (Two-Tier Reranking & Chunk Pinpointing - Tầng 2)
- **Mô hình Cross-Encoder:**
  - *Local (RTX 3050 6 GB):* `BAAI/bge-reranker-v2-m3` với `batch_size = 32` (an toàn tuyệt đối với trần 6GB VRAM theo tính toán attention).
  - *Cloud GPU (Kaggle T4 / RunPod):* Mở rộng sang `Qwen2.5-14B-Instruct` hoặc `BAAI/bge-reranker-large` (thể lệ Stage 3 quy định trần cứng ≤15B/model — xem xác nhận chính thức tại [01-THONG-TIN-CUOC-THI.md](01-THONG-TIN-CUOC-THI.md); KHÔNG dùng Qwen2.5-32B vì vượt trần).
- **Context Window Expansion:** Khi chấm điểm một chunk, ghép thêm nội dung của chunk lân cận ($\pm 1$) và tiêu đề bài viết để reranker không bị phân tác dụng do thiếu ngữ cảnh.
- **Dynamic Margin Cutoff:** Lọc danh sách nộp theo công thức $Score \ge \max(Scores) - \Delta_{margin}$ (với $\Delta_{margin}$ căn chỉnh trên dev set) thay vì dùng Top-K cố định, nhằm tối ưu hóa Macro $F_2$.

### 7.5. Công cụ đánh giá & Đóng gói nộp bài
- `eval_f2.py`: Đo tách tầng độc lập ($F_{2, doc}$ và $F_{2, chunk}$) trên mock dev set.
- `validate_submission.py`: Kiểm tra tự động schema JSON và đóng gói 1 file `.json` vào `.zip` chuẩn quy chế Ban Tổ chức.
