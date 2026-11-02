# Thông tin cuộc thi R2AI GURU STAGE 3

Tài liệu tổng hợp toàn bộ thể lệ, đặc tả bài toán, quy định kỹ thuật và quy trình nộp bài của cuộc thi R2AI GURU STAGE 3 — Nhiệm vụ chung R2AI2026: Truy hồi tài liệu y khoa đa ngôn ngữ.

---

## 1. Bối cảnh bài toán

Tri thức y sinh hiện nay được phân bố không đồng đều giữa các ngôn ngữ. Trong khi tiếng Anh và tiếng Trung sở hữu kho tài nguyên y sinh đồ sộ về cả chiều sâu lẫn độ bao phủ chuyên môn, nguồn dữ liệu tiếng Việt còn tương đối hạn chế. Sự chênh lệch này tạo ra một "khoảng cách thông tin y tế" đáng kể, gây khó khăn cho người dùng tiếng Việt trong việc tiếp cận bằng chứng y học được công bố bằng các ngôn ngữ khác.

Cuộc thi hướng tới việc xây dựng hệ thống AI có khả năng truy hồi thông tin trên một cơ sở tri thức y sinh đa ngôn ngữ quy mô hàng chục triệu tài liệu (tích hợp từ nguồn tiếng Việt, tiếng Anh và tiếng Trung). Với mỗi truy vấn bằng tiếng Việt, hệ thống phải xác định được các nội dung liên quan mà không phụ thuộc vào ngôn ngữ gốc của tài liệu.

Kết quả được đánh giá đồng thời ở hai mức độ:
- Mức độ tài liệu (Document-level): Xác định đúng tập tài liệu gốc chứa thông tin.
- Mức độ đoạn nội dung (Chunk-level): Định vị chính xác phần đoạn nội dung thực sự chứa lời lâm sàng cần thiết để trả lời câu hỏi.

### Hình thức hóa nhiệm vụ [ĐÃ CẬP NHẬT 29/09/2026 cho khớp thể lệ hiện hành]

Cho tập truy vấn $Q = \{q_1, q_2, \dots, q_n\}$ bằng tiếng Việt và các nguồn dữ liệu y sinh đa ngôn ngữ do Ban Tổ chức cung cấp hoặc chỉ định (danh sách URL Vi/Zh, phạm vi PubMed cho En — xem mục 5). **Đội thi tự thiết kế toàn bộ quy trình xây dựng cơ sở tri thức $K$**: thu thập dữ liệu, tiền xử lý, phân đoạn (chunking), lập chỉ mục và truy xuất — không còn nhận kho chunk đã cắt sẵn từ BTC.

Với mỗi truy vấn $q_i$, hệ thống thực hiện truy hồi trên $K$ và trả về hai danh sách:
- Danh sách các `doc_id` tương ứng với những tài liệu liên quan (mã tài liệu nguồn: URL hoặc PMID).
- Danh sách các `chunk_text` — nội dung text thật của các đoạn do chính hệ thống tự chunking sinh ra — tương ứng với những đoạn nội dung liên quan (xem định dạng chi tiết ở mục 6).

Một truy vấn có thể có nhiều kết quả phù hợp, thuộc một hoặc nhiều ngôn ngữ trong cùng cơ sở tri thức.

---

## 2. Mục tiêu cần đạt của hệ thống

1. Truy hồi chính xác ở cấp tài liệu (Document Retrieval):
   Xác định đúng tập tài liệu trong kho dữ liệu hàng chục triệu tài liệu. Hệ thống phải tìm kiếm theo ngữ nghĩa xuyên ngôn ngữ (Cross-lingual Semantic Search: Tiếng Việt sang Tiếng Anh và Tiếng Trung) thay vì chỉ so khớp từ khóa bề mặt.

2. Truy hồi chính xác ở cấp đoạn nội dung (Chunk Retrieval):
   Xác định đúng các chunk thực sự chứa lời lâm sàng cần thiết để trả lời truy vấn. Không được suy diễn rằng mọi chunk của một tài liệu liên quan đều liên quan.

3. Hiểu truy vấn y khoa bằng tiếng Việt:
   Hiểu ngôn ngữ tự nhiên tiếng Việt về các thuật ngữ, khái niệm y khoa và thực hành lâm sàng. Xử lý được truy vấn phức hợp chứa nhiều thông tin, yếu tố bệnh lý khác nhau trong cùng một câu hỏi.

---

## 3. Các mốc thời gian quan trọng

**[CẬP NHẬT 01/10/2026 — recap Kick-off chính thức]** BTC đóng khung lại các mốc theo "Vòng" thay vì chỉ Public/Private Phase như thông báo trước đó. Hai cách gọi mô tả CÙNG một khung thời gian, không mâu thuẫn — giữ cả hai để không mất chi tiết nào:

| Mốc thời gian | Sự kiện (theo Kick-off) | Ghi chú / đối chiếu thông báo cũ |
| :--- | :--- | :--- |
| **01/10/2026** | Kick-off Stage 3 | Phát hành tập kiểm thử công khai, mở leaderboard |
| **31/10/2026** | Kết thúc **Vòng 1** | = hạn chót nộp bài Public Test (thông báo cũ) |
| **01–10/11/2026** | **Vòng 2: Mentoring & tối ưu sản phẩm** | Bao gồm giai đoạn Private Test — hạn chót nộp hệ thống Private Test vẫn là **04/11/2026** (tối đa 5 bài nộp tổng cộng, thông báo cũ chưa thấy bị thay đổi) |
| **11/11/2026** | **Demo Day / Chung kết Stage 3** | Không chỉ "công bố kết quả" như thông báo cũ ghi — xác nhận có **sự kiện trình bày trực tiếp (Demo Day)**, xét duyệt cùng working notes paper |

**Lịch Mentor** (BTC gửi chi tiết trước ≥24 giờ qua email/kênh chính thức):
- Mentor 2: dự kiến **12/10/2026**.
- Mentor 3: dự kiến **22/10/2026**.
- Mentor 4: có thể bổ sung tùy nhu cầu thực tế trong quá trình thi.

*Lưu ý: Tất cả các hạn chót đều tính vào 23:59 theo giờ Việt Nam (UTC+07:00).*

---

## 4. Quy chế kỹ thuật và mô hình ngôn ngữ (PLMs)

### Quy định về mô hình (LLM / PLM)
- **[XÁC NHẬN CHÍNH THỨC 29/09/2026 — trang Điều khoản Tham gia]**: "Người tham gia có thể sử dụng các mô hình ngôn ngữ huấn luyện trước và các LLM có dữ liệu huấn luyện và/hoặc mô hình được công khai (ví dụ: Hugging Face hoặc các trang tương tự), nhưng không được sử dụng các LLM có mô hình đóng (ví dụ: GPT-4o, Gemini, ...). Ngoài ra, người tham gia chỉ được sử dụng các mô hình được phát hành trước ngày 1 tháng 8 năm 2026 (giờ Việt Nam) có kích thước nhỏ hơn hoặc bằng 15B."
  - Đây là quy định chính thức, không còn là "châm chước" như suy đoán ở bản cập nhật trước: **trần cứng ≤ 15B tham số**, áp dụng cho từng model riêng lẻ trong pipeline (không tính tổng cả pipeline), và mốc phát hành phải trước **01/08/2026**.
  - **Điều kiện duy nhất về giấy phép mở là "được công khai"** (open weight, có trên Hugging Face hoặc kho tương tự) — BTC KHÔNG yêu cầu license phải cho phép mục đích thương mại. Model có license non-commercial (ví dụ CC-BY-NC như `jina-reranker-v2-base-multilingual`) vẫn hợp lệ, miễn trọng số công khai và không phải LLM đóng qua API thương mại.
  - => Không được dùng Qwen2.5-32B/70B hay bất kỳ model đơn lẻ nào > 15B tham số.
- **CẤM tuyệt đối**: Không được sử dụng các LLM mô hình đóng qua API thương mại (ví dụ GPT-4o, Gemini, Claude...).
- Yêu cầu tái lập: Phải ghi rõ nguồn gốc, tên checkpoint và phương thức lấy mô hình vào bài báo mô tả phương pháp.

### Quy định về dữ liệu ngoài
- Được phép sử dụng dữ liệu ngoài (dữ liệu y sinh mở, ontology, từ điển MeSH, UMLS...).
- Phải trích dẫn rõ ràng và cung cấp đầy đủ nguồn gốc dữ liệu để Ban Tổ chức xác minh.

### Bản báo cáo giải pháp (Working Notes Paper)
- Kết quả chung cuộc chỉ được công nhận chính thức khi đội thi nộp bài báo working notes paper mô tả đầy đủ, chi tiết các phương pháp đã thực thi.

---

## 5. Quy cách dữ liệu đầu vào (Cập nhật quan trọng 26/09/2026, đối chiếu dữ liệu thật 01/10/2026)

Theo thông báo trên `https://leaderboard.aiguru.com.vn/competitions/15/`, **Ban Tổ chức SẼ KHÔNG cung cấp sẵn tập chunk đã xử lý** nhằm đánh giá toàn diện cả khả năng chuẩn bị dữ liệu của các đội thi:

1. **Dữ liệu thật đã nhận (`data/ViBioMIR/links_corpus.parquet`, phát hành đúng 01/10/2026):**
   - Ban Tổ chức cung cấp danh sách URL (`id`, `url`) của các nguồn bài viết y học. Các đội thi chủ động crawl, tiền xử lý, làm sạch HTML, tự phân đoạn (chunking) và xây dựng cơ sở tri thức.
   - **[ĐÃ XÁC MINH 01/10/2026 bằng cách quét toàn bộ 97 domain]**: corpus thật **chỉ gồm Tiếng Việt và Tiếng Trung — KHÔNG có bất kỳ domain Tiếng Anh nào** (không PubMed, không NCBI). Nhánh "Dữ liệu Tiếng Anh qua PubMed API" mô tả ở bản trước đã **lỗi thời đối với Public Test hiện hành** — xem [AGENTS.md](../NHAT-KY-DU-AN.md) mục 3 để biết chi tiết phân bố domain thật.
   - Recap Kick-off 01/10/2026 vẫn mô tả bài toán tổng quát là "corpus có thể nằm trong tiếng Việt, tiếng Anh hoặc tiếng Trung" — đây là khung bài toán chung của Nhiệm vụ R2AI2026, không mâu thuẫn với việc **tập dữ liệu cụ thể của Public Test vòng này** chỉ chứa Vi+Zh (có thể các vòng/tập test khác sau này bổ sung tiếng Anh — cần theo dõi, không giả định cố định).
2. **Quy mô — [CHỐT 01/10/2026] lấy đúng theo dataset đã clone, không cố quy đổi theo số nêu ở Kick-off:**
   - Nguồn chân lý (source of truth) duy nhất: `links_corpus.parquet` đã clone về, đo trực tiếp có **4.394.718 dòng** — đây là con số dùng cho mọi tính toán quy mô/ETA/RAM budget trong toàn bộ dự án.
   - Kick-off có nhắc thêm "hơn 1 triệu bản ghi" (không khớp số dòng thật) — quyết định của dự án: **không cố gắng quy đổi hay suy đoán ý nghĩa con số đó**, không ảnh hưởng gì tới chiến lược vì BTC đã xác nhận riêng (mục 6) toàn bộ `id` trong `links_corpus.parquet` là không gian nhãn hợp lệ duy nhất. Không cần hỏi lại BTC về điểm này nữa.
3. **Tập câu hỏi truy vấn (Test Set, `data/ViBioMIR/query.parquet`):**
   - Phát hành đúng 01/10/2026, **1.200 câu hỏi** y học bằng tiếng Việt, mỗi dòng `{"id": <integer>, "query": <string>}`.
   - Không cung cấp bất kỳ tập train hoặc dev set nào.

Chi tiết phân tích kỹ thuật và kiến trúc crawler xem tại: [08-THAY-DOI-THE-LE-DATA-PIPELINE.md](08-THAY-DOI-THE-LE-DATA-PIPELINE.md).

---

## 6. Định dạng bài nộp và quy trình Dashboard

- Trang nộp bài: `http://leaderboard.aiguru.com.vn/` (mục My Submissions).
- Định dạng file: File JSON được đóng gói trong một file `.zip`.
- **Quy tắc đóng gói file zip:** File zip chỉ chứa DUY NHẤT một file `.json` ở gốc thư mục, không được nằm bên trong thư mục con.
- Hạn mức lượt nộp:
  - Public Phase: Tối đa **10 bài/ngày** cho mỗi đội.
  - Private Phase: Tối đa **5 bài tổng cộng** cho toàn bộ giai đoạn.
  - **[GHI CHÚ 01/10/2026] Ngân sách thử nghiệm tối đa Vòng 1**: từ 01/10 đến 31/10 (đủ 31 ngày) × 10 bài/ngày = **310 lượt nộp tối đa** nếu dùng hết mỗi ngày. Đây là trần lý thuyết — không cần nộp đủ 10 bài/ngày, chỉ nộp khi có thay đổi thật sự đáng đo (đúng tinh thần "đo trước, tối ưu sau" ở mindset Stage 2), nhưng biết trần này để không tự giới hạn bản thân quá sớm khi cần thử nhiều biến thể gần cuối Vòng 1.
- Schema file JSON (ví dụ minh họa cấu trúc, xem xác nhận chính thức về nội dung trường `relevant_chunks` ngay dưới đây). **[SỬA 01/10/2026]** Ví dụ `id`/`relevant_docs` trước đây ghi kiểu chuỗi (`"q_0001"`, `"d_12345678"`) là minh họa từ thông báo cũ — dữ liệu thật (`query.parquet`, `links_corpus.parquet`) xác nhận cả hai đều là **số nguyên**:
```json
[
  {
    "id": 1,
    "relevant_docs": [12345678, 23456789],
    "relevant_chunks": [
      {"doc_id": 12345678, "chunk_text": "<chunk_text 1>"},
      {"doc_id": 23456789, "chunk_text": "<chunk_text 2>"}
    ]
  }
]
```

**[ĐÍNH CHÍNH 14/10/2026 - từ lỗi chấm thật của evaluator và trang Phương pháp đánh giá trên Codabench]** Mỗi phần tử của `relevant_chunks` PHẢI là **object `{"doc_id": ..., "chunk_text": "..."}`**, không phải chuỗi trần. Hai bài nộp đầu tiên (chuỗi trần) bị evaluator báo `Query 1 chunk 0 must be an object`. Ví dụ của BTC dùng chuỗi giữ chỗ (`"doc_id1"`); ta giữ `doc_id` là số nguyên như `links_corpus.parquet` và sẽ ghi lại tại đây nếu evaluator đòi kiểu khác.

### [XÁC NHẬN CHÍNH THỨC 29/09/2026 — trang Phương pháp đánh giá] `relevant_chunks` chứa `chunk_text`, không phải `chunk_id` tham chiếu
Vì từ 26/09/2026 BTC không còn cấp kho chunk đã cắt sẵn (xem [08-THAY-DOI-THE-LE-DATA-PIPELINE.md](08-THAY-DOI-THE-LE-DATA-PIPELINE.md)), trang Phương pháp đánh giá chính thức của BTC xác nhận rõ độ đo cấp Chunk vận hành trên **`chunk_text`** do đội thi tự chunking và nộp lên, không phải một `chunk_id` đối chiếu với tập chunk chuẩn ẩn danh:
- Gọi **C** là tập `chunk_text` được truy hồi và **I** là tập các phần thông tin cần thiết trong những tài liệu liên quan (do BTC xác định trước).
- Một `chunk_text` được tính là **relevant** nếu chứa nội dung tương ứng hoặc overlap đủ với ít nhất một phần thông tin cần thiết trong **I**.
- $Precision = \dfrac{\text{Số chunk relevant}}{\text{Tổng số chunk được truy hồi}}$, $Recall = \dfrac{\text{Số phần thông tin cần thiết được bao phủ}}{\text{Tổng số phần thông tin cần thiết}}$.
- Độ dài mỗi `chunk_text` được khuyến nghị **không quá khoảng 1.024 tokens** (khớp với khuyến nghị đã ghi nhận trước đó tại doc 08).

**Điều này thay thế hoàn toàn quy định cũ "không nộp chunk tự tạo hoặc văn bản thô" — quy định đó thuộc bản thể lệ trước ngày 26/09/2026, khi BTC còn cấp sẵn kho chunk có `chunk_id` chính thức.** Ở thể lệ hiện hành, `relevant_chunks` PHẢI là nội dung text thật của chunk do hệ thống tự chunking sinh ra.

### Các lưu ý kỹ thuật bắt buộc về bài nộp
1. Dự phòng trường rỗng: Nếu không dự đoán được kết quả ở cấp nào, bắt buộc phải nộp trường tương ứng với danh sách rỗng `[]`. Thiếu một trong hai trường sẽ bị coi là bài nộp không hợp lệ.
2. Tính duy nhất: Các `doc_id` và `chunk_text` không được trùng lặp trong cùng một danh sách kết quả của một câu hỏi.
3. Tính tồn tại của mã: `doc_id` phải tồn tại thực tế trong nguồn dữ liệu do Ban Tổ chức chỉ định (URL/PMID); `chunk_text` là nội dung tự sinh nên không cần đối chiếu tồn tại, nhưng phải trích thật từ tài liệu nguồn (không bịa nội dung).
4. Giới hạn độ dài: Mỗi `chunk_text` khuyến nghị không quá ~1.024 tokens.
5. **[XÁC NHẬN KICK-OFF 01/10/2026] Không giới hạn số lượng `relevant_docs`/`relevant_chunks` mỗi câu hỏi** — nhưng BTC lưu ý cần cân nhắc **kích thước file bài nộp và thời gian xử lý**. **[CHỐT 06/10/2026]** Giới hạn cụ thể: **`submission.zip` tối đa 100MB**. (Hệ thống này vẫn tự đặt giới hạn mềm $K_{max}=5$ chunk / $K_{doc}=3$ doc — xem [02-DANH-GIA-VA-CONG-THUC-F2.md](02-DANH-GIA-VA-CONG-THUC-F2.md) mục 5 — đây là LỰA CHỌN CHIẾN LƯỢC của ta để tối ưu Precision/F2, không phải giới hạn do BTC áp đặt; giới hạn 100MB là ràng buộc cứng của BTC, cần kiểm tra lại dung lượng `submission.json` ở Giai đoạn 7 trước khi nộp.)
6. **[XÁC NHẬN KICK-OFF 01/10/2026] Relevant Chunk phải thuộc đúng Document tương ứng** và chứa nội dung thật sự liên quan cần đánh giá — mỗi `chunk_text` nộp lên phải trích xuất thật từ một tài liệu cụ thể trong `links_corpus.parquet`, và tài liệu đó nên có mặt trong `relevant_docs` của cùng câu hỏi để nhất quán giữa hai cấp (dù schema JSON hiện tại không ép buộc kỹ thuật mối liên kết này, BTC có thể đối sánh ở hậu kỳ).
7. **[XÁC NHẬN KICK-OFF 01/10/2026] Quy tắc chống gian lận** (BTC nêu rõ tại Kick-off): cấm hardcode đáp án, cấm sao chép code của đội khác, cấm **"tạo chunk thay thế ID"** (tức bịa `chunk_text` không trích thật từ tài liệu gốc để giả làm chunk hợp lệ), cấm sử dụng dữ liệu trái phép ngoài phạm vi corpus/URL chính thức BTC cung cấp.
8. Tiêu chí đối sánh nội dung (content matching) khi chấm `chunk_text` và một số chi tiết đánh giá khác **sẽ tiếp tục được BTC cập nhật trên leaderboard** — cần theo dõi định kỳ, không coi đặc tả hiện tại là bản cuối cùng.

---

## 7. Điều khoản chung và điều kiện tham gia [XÁC NHẬN CHÍNH THỨC 29/09/2026]

### Điều khoản chung
- BTC có toàn quyền chấm dứt, sửa đổi hoặc tạm ngưng cuộc thi theo quyết định riêng.
- Khi nộp bài, đội thi đồng ý cho BTC công bố công khai điểm số tại hội thảo và kỷ yếu liên quan; BTC có quyền quyết định cuối cùng về chỉ số và giá trị điểm số.
- Tham gia cuộc thi đồng nghĩa đã chấp nhận Điều khoản Tham gia và Thỏa thuận Sử dụng Dữ liệu của Nhiệm vụ chung R2AI2026 (được gửi qua email đăng ký).
- Đội thi phải tự đảm bảo tuân thủ luật pháp hiện hành, không xâm phạm bản quyền/sở hữu trí tuệ/bằng sáng chế của bên khác trong phần mềm phát triển, không vi phạm luật kiểm soát xuất khẩu hoặc quyền riêng tư/bảo vệ dữ liệu.
- Giải thưởng phụ thuộc vào việc BTC xác minh tư cách hợp lệ và sự tuân thủ thể lệ của bài nộp thắng giải.
- **Người tham gia trao cho BTC quyền sử dụng bài nộp thắng giải cùng mã nguồn và dữ liệu tạo ra bài nộp đó cho bất kỳ mục đích nào, không cần phê duyệt thêm.**

### Điều kiện tham gia
- Mỗi người tham gia phải tạo một tài khoản để nộp bài; **chỉ cho phép một tài khoản cho mỗi người dùng**.
- Cuộc thi công khai nhưng BTC có thể từ chối cho tham gia theo cân nhắc riêng, và có quyền loại thí sinh nếu có cơ sở hợp lý tin rằng thí sinh gian lận, lừa dối hoặc chơi không công bằng.

### Đội thi
- Được phép lập đội; **mỗi người không được tham gia nhiều hơn một đội**, mỗi thành viên là một cá nhân riêng biệt vận hành tài khoản riêng.
- **Chỉ một tài khoản cho mỗi đội** được phê duyệt để nộp kết quả.

---

## 8. Thông tin Ban Tổ chức

- Đơn vị tổ chức: AI Guru – Công ty Cổ phần Tập đoàn Dagoras Group.
- Địa chỉ: Tầng 8, số 80 Duy Tân, Cầu Giấy, Hà Nội.

---
