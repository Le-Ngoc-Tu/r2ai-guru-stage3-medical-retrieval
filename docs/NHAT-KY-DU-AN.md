# AGENTS.md — hướng dẫn cho agent làm việc trong repo này

Cập nhật **03/10/2026**. Đọc file này trước khi làm bất cứ việc gì trong repo.

Mục đích: ép buộc thực thi **tuần tự theo giai đoạn**, không nhảy cóc, không phân mảnh công việc ra
nhiều agent/subagent chạy song song — vì mỗi agent/subagent không chia sẻ context đầy đủ với nhau,
dễ dẫn tới quyết định mâu thuẫn, trùng công, hoặc mất dấu lý do một quyết định kỹ thuật đã được chốt.
Dự án này chạy xuyên nhiều phiên làm việc (crawl một mình có thể mất hàng ngày), nên tính liên tục
của NGỮ CẢNH quan trọng hơn tốc độ của việc chạy song song.

---

## 0. Nguyên tắc làm việc chung (chắt lọc từ CLAUDE.md global, áp dụng cụ thể cho repo này)

File này **không lặp lại toàn bộ** `~/.claude/CLAUDE.md` (đã tự nạp mỗi phiên) — chỉ nêu phần đã
chứng minh LÀ TRỌNG YẾU cho chính repo này, để ai đọc một mình file này (không có session cũ) vẫn
đủ ngữ cảnh làm đúng.

1. **Phân loại trước khi hỏi (Classify Before Asking).** Một sự thật đo được (tốc độ crawl thật,
   license một thư viện, nội dung một file) — tự Read/Bash kiểm chứng, KHÔNG hỏi user. Chỉ hỏi khi
   chạm quyết định mà chỉ user/BTC quyết được (ví dụ: chấp nhận license non-commercial của một model
   hay không — đã hỏi và được xác nhận 29/09; chiến lược ưu tiên crawl toàn bộ vs theo mẫu — đã hỏi
   01/10). Đã áp dụng xuyên suốt: verify license qua `pip show` thay vì nhớ, verify domain qua truy
   vấn `links_corpus.parquet` thật thay vì suy đoán.
2. **Grounding tuyệt đối.** Không suy đoán về file/dữ liệu chưa đọc. Mọi số liệu ghi trong các tài
   liệu `phan-tich/stage3/*.md` phải trace được về một lần đo/đọc file thật — nếu không đo được, ghi
   rõ "CHƯA ĐO" (như mục 3 dưới đây đang làm với tốc độ crawl phần Trung Quốc), không bịa số.
3. **Khớp công sức với độ lớn việc.** Sửa 1 dòng số liệu trong 1 doc → làm ngay. Việc chạm 2-4 file
   (ví dụ cập nhật README+AGENTS+1 doc) → nêu ngắn rồi làm. Việc đổi kiến trúc/chạm ≥5 file → tóm tắt
   kế hoạch, chờ xác nhận trước khi làm (đã dùng cho các lần cập nhật thể lệ lớn ngày 28-29/09).
4. **Subtract before you add.** Trước khi thêm nội dung mới vào một doc, dọn luôn phần đã lỗi thời
   liên quan trong CÙNG lần sửa đó (đã làm: bỏ nhánh "Tiếng Anh/PubMed" khỏi README khi cập nhật Bước
   3, không để tài liệu vừa đúng vừa sai cùng tồn tại).
5. **Diff tối thiểu.** Khi sửa một doc đã có, chỉ đổi đúng đoạn cần đổi — không format lại toàn file,
   không đổi thứ tự mục khi không yêu cầu.
6. **Verification-Driven, không fabricate.** Không ghi "đã xong"/đưa số liệu khi chưa thực sự đo
   (file `docs/readme-banner-prompt.md` chủ động để trống nội dung thật vì chưa có kết quả leaderboard
   — xem mục đó để thấy ví dụ áp dụng).
7. **An toàn — repo này KHÔNG có git, mọi xóa/ghi đè coi như vĩnh viễn.** Trước khi xóa hoặc sửa đè
   bất kỳ file trong `data/` (đặc biệt `crawl_cache.sqlite3` khi crawler đang chạy), phải dừng tiến
   trình an toàn trước, không sửa file khi có process khác đang viết vào nó.
8. **Ngôn ngữ:** trả lời/viết tài liệu bằng tiếng Việt có dấu đầy đủ; thuật ngữ kỹ thuật (tên model,
   tên thư viện, tên field JSON) giữ nguyên tiếng Anh; code comment trong `.py` tiếng Việt có dấu.

---

## 1. Luật thực thi tuần tự (BẮT BUỘC, không thương lượng)

1. **Chỉ làm việc trong ĐÚNG MỘT giai đoạn tại một thời điểm** (xem bảng giai đoạn ở mục 2). Không
   bắt đầu code/thiết kế cho giai đoạn N+1 khi giai đoạn N chưa đạt tiêu chí hoàn thành.
2. **Không spawn nhiều agent chạy song song** (Agent tool, Task, Workflow, fork) cho công việc của
   dự án này, trừ khi user yêu cầu tường minh trong đúng câu lệnh đó. Tự làm trực tiếp tuần tự
   (Read/Grep/Glob/Bash/Edit) — một luồng xử lý duy nhất giữ được toàn bộ bối cảnh đã tích lũy.
3. **Mỗi giai đoạn phải có tiêu chí hoàn thành đo được** trước khi coi là xong (Verification-Driven,
   không phải "nhìn có vẻ ổn"). Tiêu chí ghi rõ trong bảng mục 2.
4. Khi hoàn thành một giai đoạn: cập nhật cột "Trạng thái" trong bảng mục 2 ngay trong phiên đó,
   trước khi chuyển sang giai đoạn kế — không để trạng thái file này trôi khỏi thực tế.
5. Nếu phát hiện thông tin mới làm invalidate một quyết định đã chốt ở giai đoạn trước (ví dụ: thể
   lệ đổi, dữ liệu thật khác giả định) — SỬA NGAY tài liệu liên quan trong `phan-tich/stage3/`, dẫn
   nguồn xác nhận, rồi mới tiếp tục. Không để tài liệu cũ và thực tế mới mâu thuẫn nhau.
6a. **Ghi số liệu cụ thể khi đóng mỗi giai đoạn liên quan dữ liệu** (crawl, chunk, index, mock dev
   set...) — không chấp nhận ghi mơ hồ "đã xong". Phải kèm: tổng số đơn vị dữ liệu nguồn, số đã xử
   lý thành công, số bị loại trừ + LÝ DO CỤ THỂ, tỷ lệ %. Lý do: ở Stage 2, việc không dùng hết dữ liệu công khai BTC cấp mà không giải trình được tỷ lệ/
   nguyên nhân — minh bạch số liệu sử dụng dữ liệu là tiêu chí thực tế bị soi tại demo, không phải
   chi tiết kỹ thuật nội bộ có thể bỏ qua. Mục 3 dưới đây là ví dụ áp dụng cho Giai đoạn 1.
6. **Ngoại lệ DUY NHẤT đã dùng (01/10/2026): `eval_f2.py` viết sớm ở Giai đoạn 1** dù thuộc bảng
   Giai đoạn 5 — lý do: hàm thuần toán học (công thức đã khóa ở doc 02, xác nhận chính thức từ BTC),
   **không đưa ra bất kỳ giả định nào về dữ liệu thật chưa kiểm chứng**, tự test được bằng các ví dụ
   có sẵn kết quả biết trước trong doc 02 (không cần crawl/chunk/index thật). Đây KHÔNG phải tiền lệ
   chung — chỉ áp dụng khi file mới hoàn toàn độc lập dữ liệu thật như trường hợp này. Mọi module khác
   (`medical_chunker.py`, `tantivy_indexer.py`, `validate_submission.py`...) vẫn phải đợi đúng giai
   đoạn vì chúng CẦN giả định về đặc điểm dữ liệu thật mà ta chưa kiểm chứng xong.

---

## 2. Các giai đoạn (Phase Gate) — trạng thái cập nhật 01/10/2026

| # | Giai đoạn | Tiêu chí hoàn thành | Trạng thái |
|---|---|---|---|
| 0 | Chuẩn bị hạ tầng (`.venv`, dependencies) | `httpx`/`trafilatura`/`polars` import được trong venv | **XONG** |
| 1 | Crawl toàn bộ `links_corpus.parquet` (`url_crawler.py`) | `SELECT COUNT(*) FROM pages WHERE status='pending'` = 0 trong `data/crawl_cache.sqlite3` | **XONG 09/10/2026 16:24** — `pending=0`, `retry=0`; số liệu đóng ở đầu mục 3 |
| 2 | Nghiên cứu/EDA dữ liệu đã crawl | Có báo cáo phân bố ngôn ngữ thật, độ dài, tỷ lệ nội dung y khoa vs nhiễu, trùng lặp | **XONG báo cáo 09/10/2026** — [doc 14](phan-tich/14-BAO-CAO-EDA-GIAI-DOAN-2.md); phát hiện lỗi mã hóa ~503k trang done (14,46%); đã tải lại `wujue.com` (53.341 trang, 100% thành công), còn ~450k trang `cnkang.com` hỏng, user chọn không tải lại. **Đã đóng 09/10/2026 23:31** |
| 3 | Chunking (`medical_chunker.py`) | Chạy thử trên mẫu, chunk có metadata đầy đủ, áp dụng Contextual Retrieval (doc 11 mục 3) | **XONG 10/10/2026** — `src/stage3/medical_chunker.py`; chunk theo ngân sách token BGE-M3 (tối đa 420 token/chunk, overlap 60), `text` là chuỗi con nguyên văn của thân bài (có `char_start/char_end`), Contextual Retrieval tĩnh ở `embed_text`. Số liệu mục 3b. Chưa chunk toàn corpus (chạy ở pipeline Giai đoạn 4) |
| 4 | Lập chỉ mục Sparse + Dense (`tantivy_indexer.py`, BGE-M3, Binary Quantization) | Index chạy được truy vấn thử, RAM trong ngân sách 16GB (doc 11 mục 4) | **XONG 14/10/2026** — BM25 + embed + binary + RRF đã chạy truy vấn thử; số liệu ở mục 3c |
| 5 | Reranking + Dynamic Thresholding | `eval_f2.py` đo được $F_{2,doc}$ và $F_{2,chunk}$ tách tầng trên mock dev set | **XONG 14/10/2026** — `eval_f2.py` theo luật LCS >= 0,40; baseline, reranker (có tiêu đề), khử chunk lặp và ngưỡng động đã đo trên 743 cặp (số liệu mục 3c). Truy vấn tiếng Trung/CARE KHÔNG đo được trên dev hiện tại (không có nhãn tiếng Trung), chuyển sang A/B trên leaderboard ở Giai đoạn 7-8 |
| 6 | Mock dev set từ dữ liệu mở (ViHealthQA/webMedQA/cMedQA2 — doc 13) | ≥300 cặp câu hỏi-chunk đã gán nhãn, dùng để calibrate ngưỡng cắt | **XONG 14/10/2026** (làm TRƯỚC giai đoạn 5, user đồng ý đảo thứ tự) — 743 cặp tiếng Việt, chưa có phần tiếng Trung; số liệu và hạn chế ở mục 3c |
| 7 | Nộp bài baseline đầu tiên (BM25 thuần, `validate_submission.py`) | 1 bài nộp hợp lệ format trên leaderboard Public Test | **XONG, ĐÃ NỘP 14/10/2026, ĐƯỢC CHẤM** — điểm rất thấp (FINAL 0,0253 / 0,0237) vì trả quá ít doc (3) so với ~71 doc tham chiếu mỗi câu; đang sửa bằng quét K lớn (mục 3c, 14/10) |
| 8 | Lặp cải tiến dựa trên leaderboard thật, có mentor đồng hành | Điểm F2 macro tăng có ghi nhận nguyên nhân mỗi lần đổi; dự Mentor 2 (~12/10) và Mentor 3 (~22/10) | **ĐANG LÀM, ĐÃ PHẲNG** — bản Public chốt: bài 5781, FINAL 0,2312 (16/10); tổng kết và kế hoạch ở mục 3d |
| 9 | Working Notes Paper + chuẩn bị **Demo Day** | Nộp paper trước 11/11/2026; có bản trình bày sẵn sàng cho sự kiện Demo Day/Chung kết cùng ngày (xác nhận Kick-off 01/10 — không chỉ "công bố kết quả" suông) | CHƯA BẮT ĐẦU |

---

## 3. Trạng thái Giai đoạn 1 (Crawl) — ĐÃ XONG 09/10/2026 16:24 (các mục bên dưới là nhật ký lịch sử)

### [09/10/2026, 16:24] ĐÓNG GIAI ĐOẠN 1 — số liệu cuối (quy tắc 6a)

Log ghi `no more pending/retry rows - crawl complete`; crawler tự thoát, không còn process, không còn
file `-wal`/`-shm`. Số liệu đếm từ `data/crawl_cache.sqlite3` (bảng `pages`):

| Trạng thái | Số dòng | % của 4.394.718 |
|---|---|---|
| **done** (đã crawl + trích xuất, dùng được) | **3.487.922** | **79,37%** |
| banned_cooldown (loại trừ — xem lý do dưới) | 875.487 | 19,92% |
| needs_js_render (chưa crawl, cần trình duyệt) | 28.710 | 0,65% |
| failed (lỗi vĩnh viễn sau retry) | 2.599 | 0,06% |
| pending / retry | 0 / 0 | 0% |
| **Tổng** | **4.394.718** | 100% (khớp `links_corpus.parquet`) |

**Lý do loại trừ `banned_cooldown` (875.487 dòng) — user quyết định 09/10 KHÔNG retry, bỏ qua hẳn:**
domain bị WAF chặn IP (403/429) hoặc không kết nối được, bị circuit breaker hoặc thao tác tay chuyển
sang `banned_cooldown`. Đã định danh được: `www.120ask.com` 175.540 dòng pending/retry còn lại (không
vào được từ 08/10 08:24, CHƯA xác định sập hay chặn IP máy này), `zysjonline.com` ~243.347,
`ask.39.net` 197.862, `nhathuoclongchau.com.vn` + `pmc-ecm-healthblog.beta.pharmacity.io` 84.931,
`suckhoecongdongonline.vn` 59.284, `bingli.iiyi.com` 24.970, `article.iiyi.com` 5.623, `baodanang.vn` +
`baohaiphong.vn` 30.786, `youmed.vn` 4.294, `thaythuocvietnam.vn` 1.717, `qihuangzhishu.com`,
`medlatec.vn`... (con số từng domain lấy từ các mục nhật ký bên dưới). **Cộng các domain trên không ra
đủ 875.487**: phần còn lại (~262.927 dòng theo đối soát 02/10) **CHƯA gán được domain — CHƯA ĐO**.

`needs_js_render` (28.710): **[GHI CHÚ HOÃN, user quyết 09/10]** chưa chạy pass `crawl4ai` ngay; để dành
làm ở cuối cuộc thi (khi các giai đoạn chính đã ổn) vì có thể giúp tăng thêm một ít điểm. Khi làm: cài
`crawl4ai` + Chromium, chạy riêng cho 28.710 dòng này (doc 09), ghi lại số dòng thu được. `failed` (2.599):
lỗi vĩnh viễn (404/410, v.v.), chưa phân loại theo mã lỗi — CHƯA ĐO.

**Phát hiện 09/10 (đối chiếu README dataset, chưa giải thích được):** `data/ViBioMIR/README.md` ghi
"Tổng số liên kết 4.420.561, khoảng ID 1-4.420.561", nhưng `links_corpus.parquet` thực tế có **4.394.718
dòng, `id` từ 583 đến 4.420.561** (không trùng lặp) — thiếu 25.843 `id` so với số README công bố. Mẫu số
của báo cáo này là số dòng parquet thật (4.394.718). Nguyên nhân chênh (BTC loại bớt link sách? bản
parquet khác README?) **CHƯA xác định**; user quyết định (09/10) KHÔNG hỏi BTC (số README chỉ là ước chừng) — dùng 4.394.718 làm mẫu số.

**[ĐÍNH CHÍNH 09/10, từ EDA Giai đoạn 2 — doc 14]** Con số `done` 3.487.922 ở trên là số trang crawl
thành công về mặt HTTP/trích xuất, **KHÔNG đảm bảo nội dung đúng**: ước lượng ~503.000 trang (14,46% done)
chứa ký tự `U+FFFD` thay chữ Hán do lỗi giải mã (`resp.text` ở `url_crawler.py` dòng 228 với trang GBK
không có charset trong header) — chủ yếu `www.cnkang.com` (~449k) và `www.wujue.com` (~53k). Số trang done
**dùng được** ước lượng ~2.977.000 (85,54% done; 67,7% corpus). Đã kiểm chứng nguyên nhân bằng 3 request thật.

**[XỬ LÝ 09/10, 23:31] Đã tải lại `www.wujue.com` (user chọn phương án a, chạy trước Giai đoạn 3):** sửa
`url_crawler.py` (hàm `_decode_response`: đọc `<meta charset>` khi header thiếu charset, GB2312/GBK giải mã
bằng gb18030), đặt lại 53.341 dòng `wujue.com` từ `done` về `pending`, crawl lại với tốc độ đo được 12,1/s.
Kết quả: 53.341/53.341 thành công (100%), `pending=0`, `done` trở lại 3.487.922. Kiểm tra mẫu 3.000 dòng
wujue: 0 trang còn `U+FFFD`, 3.000/3.000 có chữ Hán (ước lượng từ mẫu, không đọc đủ 53k dòng). Còn hỏng:
`www.cnkang.com` ~449.000 trang (user chọn KHÔNG tải lại, phương án a) cộng vài nghìn trang lẻ ở domain khác →
tổng hỏng ước lượng ~450.000; done **dùng được** ước lượng ~3.038.000 (87,1% done; 69,1% corpus).
Log crawl Giai đoạn 1 lưu ở `data/crawl_log_giai_doan1.txt`.

Lưu ý khi dùng dữ liệu ở Giai đoạn 2+: các domain bị loại là không đồng đều (nhiều domain Trung Quốc lớn
như 120ask/ask.39.net/zysjonline thiếu một phần), nên phân bố ngôn ngữ/nguồn của tập `done` lệch so với
corpus gốc — Giai đoạn 2 (EDA) phải đo lệch này, không giả định đại diện.

---

### 3b. Số liệu đóng Giai đoạn 3 (10/10/2026, đo trên mẫu — KHÔNG phải chunk toàn corpus)

- **Tỷ lệ token/ký tự (tokenizer BGE-M3, 2.718 trang mẫu)**: tiếng Trung trung vị 0,636 (P95 0,838); tiếng Việt trung vị 0,279 (P95 0,312). Vì vậy 800-1200 ký tự (doc 08) vượt 512 token với tiếng Trung → dùng ngân sách token.
- **Kiểm thử 3.000 trang `done` ngẫu nhiên**: 6.507 chunk; 463 trang (15,4%) bị bỏ qua (lỗi mã hóa `U+FFFD` hoặc không có thân bài; mẫu lấy trước khi tải lại `wujue.com` nên cao hơn thực tế hiện tại). 0 chunk có `text` không phải chuỗi con nguyên văn; token thật của `text` trung vị 361, tối đa 423; của `embed_text` tối đa 500; 0 chunk vượt 512. Chunk dưới 50 token: 0,7%. Tốc độ ~1.300 trang/giây (1 luồng).
- **Ước lượng toàn corpus (có trọng số theo domain, 8.000 trang)**: 2,50 chunk/trang → khoảng **7,58 triệu chunk**, khoảng **2,44 tỷ token** trên ~3,038 triệu trang dùng được. Đây là ước lượng; tổng chunk thật CHƯA ĐO.
- **Hệ quả cho Giai đoạn 4**: số chunk (~7,6 triệu, không phải 30-100 triệu như doc 11 giả định) → vector binary 1024-bit ~1GB, float16 ~15,5GB. Thời gian embed 2,44 tỷ token bằng BGE-M3 trên RTX 3050 6GB **CHƯA ĐO** (cần đo thông lượng thật trước khi cam kết lập chỉ mục toàn corpus).
- **Chưa đo**: độ lớn lợi ích Contextual Retrieval (cần mock dev set, Giai đoạn 6); 36% trang có heading, 45,3% chunk có `section`.

---

### 3c. Giai đoạn 4 - môi trường và thông lượng BGE-M3 đã đo (10/10/2026)

- **Môi trường (trong `.venv`, Python 3.11)**: `torch 2.14.1+cu126` (GPU nhận, VRAM trống 5.158/6.143 MB; ~1 GB đang bị tiến trình khác dùng), `transformers 5.19.0`, `tantivy`, `faiss-cpu 1.15.1`, `numpy 2.4.6`, `tokenizers`, `huggingface_hub`. Model `BAAI/bge-m3` (pytorch_model.bin 2.165 MB) ở `data/hf_cache`. Cache pip ở `data/pip_cache`, thư mục tạm `data/tmp` (có thể xóa khi không cần).
- **Thông lượng BGE-M3 fp16, 2.000 chunk thật (trung bình 341 token, tổng 682.136 token), max_length 512, sắp xếp theo độ dài**: batch 8 → 49,9 chunk/s (17.023 token/s, VRAM đỉnh 1.181 MB); batch 16 → 50,6 chunk/s (17.242 token/s, VRAM đỉnh 1.269 MB); **batch 32 → 11,2 chunk/s (chậm gấp 4,5 lần, nguyên nhân CHƯA xác định - không dùng)**. Nạp model 1,7s, model chiếm 1.083 MB VRAM.
- **Suy ra (ước lượng, chưa chạy thật)**: 7,58 triệu chunk ÷ 50 chunk/s ≈ 151.600 s ≈ **42 giờ GPU liên tục** (chưa tính đọc DB trên HDD và ghi vector). VRAM không phải nút thắt (đỉnh ~1,3 GB); thời gian mới là ràng buộc.

- **[10/10/2026, 16:28] CHUNK TOÀN CORPUS XONG (Giai đoạn 4, việc 1/3; quy tắc 6a)**: `chunk_corpus.py` chạy 2 worker ưu tiên thấp (lần chạy cuối 25.633s ≈ 7,1 giờ), 222/222 shard ở `data/chunks/shard_*.parquet` (2,26 GB, zstd), 0 file `.tmp`, đã dọn sạch process.

| Mục | Số liệu đo | % |
|---|---|---|
| Trang `done` đầu vào | 3.487.922 | 100% |
| Trang bị loại: lỗi mã hóa (>=10 ký tự `U+FFFD`) | 454.068 | 13,02% |
| Trang bị loại: không có thân bài | 0 | 0% |
| **Trang được chunk** | **3.033.854** | **86,98% của done; 69,03% của 4.394.718** |
| **Chunk** | **7.607.882** (ước lượng trước đó 7,58 triệu, lệch +0,4%) | |
| Token chunk (trung bình 322,57; tối đa 420) | ~2,454 tỷ | |
| Chunk tiếng Trung / tiếng Việt | 5.816.327 (76,5%) / 1.791.555 (23,5%) | |
| Trang tiếng Trung / tiếng Việt có chunk | 2.359.412 / 674.442 | |
| Chunk dưới 50 token | 66.595 | 0,88% |

Ước lượng EDA trước đó (~450.000 trang hỏng) khớp số đo thật 454.068. Sau cộng gộp các lần loại trừ, phần corpus KHÔNG vào được chỉ mục: 875.487 (banned_cooldown) + 28.710 (needs_js_render) + 2.599 (failed) + 454.068 (lỗi mã hóa, chủ yếu `cnkang.com`) = 1.360.864 trang = **30,97%** của 4.394.718.

- **[10/10/2026, 17:38] CHỈ MỤC TANTIVY BM25 XONG (Giai đoạn 4, việc 2/3)**: `src/stage3/tantivy_indexer.py` → `data/tantivy_index` (2,70 GB, 19 segment). Chạy 2 luồng ưu tiên thấp, **950 giây** cho toàn bộ. `num_docs` = **7.607.882** = đúng số chunk (100%, 0 chunk thiếu hoặc thừa). Không còn process nào sau khi xong.
  - Tokenizer: chuỗi chữ Hán → bigram chồng lấp; còn lại tách theo ký tự chữ-số + chữ thường (`to_index_text`, truy vấn phải dùng đúng hàm này). Trường `body` = tiêu đề + mục + text (index_option `freq`). Index chỉ lưu `doc_id`, `chunk_index`; text lấy lại từ `data/chunks`.
  - Kiểm tra bằng 20 câu hỏi thật từ `query.parquet` (seed 0): 0 câu không có kết quả; độ trễ trung vị 45 ms, P95 109 ms, tối đa 135 ms (mẫu nhỏ, bộ đệm HDD lạnh).
  - **Phát hiện quan trọng**: cả 200 kết quả top-10 của 20 câu hỏi đều là chunk **tiếng Việt** (0 chunk tiếng Trung), dù 76,5% chunk là tiếng Trung. Câu hỏi toàn tiếng Việt nên BM25 thuần không chạm tới phần tiếng Trung. Phần tài liệu đúng nằm ở tiếng Trung chiếm bao nhiêu CHƯA ĐO (cần mock dev set, Giai đoạn 6). Hướng giải quyết: dense BGE-M3 xuyên ngôn ngữ (việc 3/3) và/hoặc dịch truy vấn sang tiếng Trung rồi BM25 bigram.

- **[10/10 22:00 - 11/10 08:58] EMBED DENSE BGE-M3 (Giai đoạn 4, việc 3/3) - ĐANG DỞ, TẠM DỪNG THEO YÊU CẦU USER**: `src/stage3/embed_corpus.py` → `data/embeddings/shard_*.npy` (fp16, N x 1024, đúng thứ tự dòng parquet). Batch 16, ưu tiên thấp, tự tạm dừng khi GPU >= 82°C hoặc RAM trống < 2,5 GB. Đã xong **129/222 shard = 3.705.939 / 7.607.882 chunk (48,71%)** (đêm 1: 36 shard, 1.409.672 chunk, 11,05 giờ, 35,4 chunk/s; đêm 2 (nâng ngưỡng bảo vệ lên RAM trống >= 3,5GB, GPU < 80°C): 93 shard, 2.296.267 chunk, ~14,5 giờ thực, khoảng 44 chunk/s; mỗi shard 29-48 chunk/s vì guard dừng khi GPU nóng). Còn 93 shard = 3.901.943 chunk; ước lượng còn ~25 giờ nếu giữ ~44 chunk/s (ước lượng, chưa đo). Lưu ý: log in "tong 70507s" không khớp giờ đồng hồ thực (~52.000s), chưa rõ nguyên nhân - số chunk/s ở trên tính theo giờ thực. Kiểm chứng shard 0: 46.574 vector khớp đúng 46.574 dòng, 0 NaN, cosine với embed từng chunk min 0,99992 / TB 0,999998. Dừng đêm 2 lúc 07:50 bằng STOP (dừng êm, 0 file `.tmp`, không còn process). **Chạy lại**: xóa `data/embeddings/STOP` rồi chạy `embed_corpus.py`; tự bỏ qua shard đã xong. Chưa làm: lượng tử hóa binary (faiss), RRF với BM25.

- **[14/10/2026] EMBED DENSE BGE-M3 XONG (Giai đoạn 4, việc 3/3; quy tắc 6a)**: log ghi `XONG`, 222/222 shard `data/embeddings/shard_*.npy` (fp16, N x 1024, tổng 15 GB), tiến trình đã thoát, 0 file `.tmp`, không có STOP. Đối soát bằng đọc lại từng shard: **7.607.882 vector = 7.607.882 chunk (100%)**, 0 shard sai shape/dtype. Chunk bị loại khỏi embed: 0. Thông lượng thực vài ngày cuối 28-32 chunk/s (GPU ~62-63°C, guard không còn dừng). Tổng thời gian chạy cộng dồn các đêm/ngày CHƯA ĐO chính xác (log "tong ...s" không khớp giờ đồng hồ, xem mục trên). Chưa làm: lượng tử hóa binary (faiss), RRF với BM25.

- **[14/10/2026] ĐÓNG GIAI ĐOẠN 4 - binary quantization + RRF (quy tắc 6a)**: `src/stage3/dense_index.py build` → `data/dense_index/` (1,0 GB): `faiss.IndexBinaryFlat` 1024 bit (dấu từng chiều), **7.607.882 vector = 7.607.882 chunk (100%, 0 loại trừ)**, dựng 156 giây; kèm ánh xạ hàng → (doc_id, chunk_index) và vector fp16 gốc (`data/embeddings`, 15 GB, đọc mmap) để rescoring top-200. `src/stage3/hybrid_search.py test` (BM25 Tantivy + dense + RRF k=60, độ sâu 100/100) chạy trên 20 câu hỏi thật của `query.parquet` (seed 0): độ trễ nóng trung vị 256 ms/câu (BM25 58 ms, dense 178 ms; lần đầu nguội trên HDD 2,6 s), RAM tiến trình 3,9 GB (đỉnh 4,1 GB, gồm encoder BGE-M3 và chỉ mục), trong ngân sách 16 GB. Recall@10 của binary + rescoring so với duyệt chính xác toàn bộ fp16: **1,000 trên 3 câu** (mẫu quá nhỏ, chưa kết luận chắc). Tỷ lệ chunk tiếng Trung trong top-10: BM25 0%, dense 7%, RRF 1% (trong khi 76,5% chunk là tiếng Trung): truy vấn tiếng Việt vẫn gần như chỉ ra chunk tiếng Việt; phần đáp án đúng nằm ở tiếng Trung bao nhiêu **CHƯA ĐO** (cần mock dev set, Giai đoạn 6). Chưa có chất lượng truy hồi (F2/Recall) vì chưa có nhãn. Không còn process nền.

- **[14/10/2026] ĐÓNG GIAI ĐOẠN 6 - MOCK DEV SET (quy tắc 6a)**: `src/stage3/build_mock_dev.py` → `data/mock_dev/dev_set.jsonl`. Nguồn: ViHealthQA (`tarudesu/ViHealthQA`, tải về `data/mock_dev/vihealthqa/`), 10.015 cặp hỏi-đáp. **Không có nhãn trực tiếp**: cột `link` chỉ chung 2 domain với corpus (vinmec, vnexpress) nhưng 0/10.015 URL khớp `links_corpus` (dạng URL khác, vnexpress trỏ trang tổng hợp). Cách gán nhãn: BM25 (Tantivy, độ sâu 30) bằng 400 ký tự đầu câu trả lời, lấy 3 chunk trùng từ nhiều nhất, tính LCS token / độ dài đáp án (NFKC, chữ thường), giữ chunk đạt >= 0,60 làm nhãn dương. Thăm dò 100 cặp trước đó: chỉ 44% đạt >= 0,4, 11% đạt >= 0,6, 3% đạt >= 0,8, nên 0,4 chủ yếu là trùng từ vựng chung, không dùng làm nhãn. **Kết quả: giữ 743/10.015 cặp (7,42%)** (train 507 / val 83 / test 153), 872 doc nhãn duy nhất, 1,38 chunk nhãn và 1,37 doc nhãn mỗi câu (536 câu đúng 1 doc); domain nhãn: vinmec 376, medlatec 111, suckhoedoisong 97, tiemchunglongchau 54, suckhoecongdongonline 40, thanhnien 36, hellobacsi 31 doc. Loại 9.272 cặp (92,58%) vì đáp án không nằm gần nguyên văn trong corpus (lý do: corpus không chứa trang nguồn gốc của ViHealthQA, hoặc trang thuộc phần banned_cooldown/lỗi mã hóa; tỷ lệ từng nguyên nhân CHƯA ĐO). **Hạn chế đã biết**: (1) toàn bộ nhãn là chunk tiếng Việt nên bộ này KHÔNG đo được trường hợp đáp án tiếng Trung cho câu hỏi tiếng Việt, đúng điểm đáng lo của Giai đoạn 4; (2) ứng viên nhãn lấy từ BM25 của câu trả lời nên thiên về từ vựng; (3) phân bố domain lệch Vinmec, khác 1.200 câu thật chưa biết nguồn; (4) webMedQA/cMedQA2 CHƯA dùng, chưa có mock tiếng Trung. Chưa đo chất lượng truy hồi trên bộ này (việc của Giai đoạn 5).

- **[14/10/2026] GIAI ĐOẠN 5 - ĐO TRÊN MOCK DEV SET (quy tắc 6a; 743 câu: train 488 / val+test 255 sau lọc; mẫu nhỏ, chỉ tiếng Việt)**: (1) `eval_f2.py` sửa sang luật chính thức NFKC + HTML entity + chữ thường + LCS token / |đoạn tham chiếu| >= 0,40, chữ Hán tách từng chữ (giả định, tài liệu chấm không nêu); self-test cũ vẫn PASS. (2) Baseline `eval_retrieval.py` (relevant = đúng doc nhãn và LCS với đáp án >= 0,40), top-k chunk, RRF k=60 độ sâu 50: BM25 DocRecall@10 0,376 / @50 0,450; dense 0,412 / 0,477; **RRF 0,407 / 0,502**; F2 cố định doc top-3 / chunk top-5: BM25 0,210 / 0,185; dense 0,238 / 0,197; RRF 0,241 / 0,196. Trần của mọi phương pháp ở top-50 chỉ ~0,50: nửa số câu không có chunk nhãn trong 50 ứng viên. (3) Reranker BGE-reranker-v2-m3 (fp16, chỉ `text`, top-30 của RRF, 573 giây cho 743 câu) cho **ChunkHit@1/3/5/10 = 0,225/0,285/0,320/0,377, KÉM RRF (0,272/0,323/0,346/0,398)**; top-1 rerank tiếng Trung chỉ 1,6% (không phải thiên lệch ngôn ngữ). Chẩn đoán trên 46 câu RRF top-1 đúng mà rerank sai: reranker chọn câu hỏi-đáp khác cùng chủ đề, hợp lý nhưng KHÔNG có nhãn; nhãn dev chỉ gồm chunk gần nguyên văn đáp án ViHealthQA nên phạt oan, đo sát từ vựng đáp án. Vì vậy KHÔNG kết luận reranker vô dụng, chỉ kết luận mock dev set không phân xử được. (4) Ngưỡng động `tune_threshold.py` (lưới T_min, Delta, K_max, K_doc, chọn trên train): T_min=-2, Delta=2, K_max=5, K_doc=5 cho F2 doc / chunk = 0,276 / 0,273 (train), **0,206 / 0,207 (val+test)**; top-1 cố định trên val+test: 0,198 / 0,204. Chênh train-held lớn, ngưỡng này chưa đáng tin để dùng làm cuối. Chưa làm: gộp chunk cùng tài liệu và khử chunk lặp do overlap (khuyến nghị của mentor), thử rerank có `doc_title`, thử CARE/dịch truy vấn sang tiếng Trung. Điểm leaderboard thật là phép đo duy nhất không thiên lệch nhãn: nên dùng Giai đoạn 7 để A/B RRF thuần vs RRF + rerank.

- **[14/10/2026] GIAI ĐOẠN 5 - BỔ SUNG, ĐÓNG (quy tắc 6a; cùng 743 câu: train 488 / val+test 255)**: (1) **Rerank có tiêu đề** (`rerank_dev.py --with-title`: văn bản chấm = `build_embed_text(doc_title, section, text)`, 573 giây/743 câu) đảo kết quả: ChunkHit@1/3/5/10 = **0,272/0,322/0,353/0,393** (chỉ `text`: 0,225/0,285/0,320/0,377; RRF thuần: 0,272/0,323/0,346/0,398). Tức rerank có tiêu đề bằng RRF ở @1, nhỉnh hơn ở @5 (+0,007), kém nhẹ ở @10 (-0,005), chênh nằm trong sai số của mẫu 743 câu. (2) **Ngưỡng động với điểm có tiêu đề**: tốt nhất trên train T_min=-inf, Delta=1, K_max=8, K_doc=5 (K_max=8 vượt trần 5 đã đặt, do lưới thử 3/5/8); F2 doc / chunk = 0,316 / 0,317 (train), **0,256 / 0,257 (val+test)**; top-1 cố định val+test 0,234 / 0,239; top-3 0,206 / 0,203; top-5 0,191 / 0,180. Tốt hơn hẳn bản không tiêu đề (0,206 / 0,207). Ngưỡng cắt này chọn trên train 488 câu, chênh train-held 0,06, chưa đáng tin tuyệt đối. (3) **Khử chunk lặp** (bỏ chunk chồng >= 50% ký tự cùng tài liệu hoặc trùng nội dung chuẩn hóa): ChunkHit@5 0,353 -> 0,354, F2 không đổi: trong top-30 gần như không có chunk lặp, KHÔNG đáng làm phức tạp thêm trên dev này (tỷ lệ lặp trên toàn corpus CHƯA ĐO). (4) **Truy vấn tiếng Trung (dịch hoặc CARE)**: KHÔNG đo được trước leaderboard, vì mọi nhãn dev là tiếng Việt, không có cặp câu hỏi tiếng Việt - đáp án tiếng Trung nào để chấm; để A/B bằng điểm leaderboard thật ở Giai đoạn 7-8. Quy trình đề xuất nộp: A = RRF thuần, B = RRF + rerank có tiêu đề + ngưỡng động.

- **[14/10/2026] GIAI ĐOẠN 7 - TẠO BÀI NỘP (quy tắc 6a; CHƯA có điểm leaderboard, không suy đoán điểm)**: `make_submission.py` chạy 1.200/1.200 câu của `query.parquet` (truy hồi RRF độ sâu 50, rerank top-30 với BGE-reranker-v2-m3 có tiêu đề, cache ở `data/submission/candidates.jsonl` và `rerank_scores.jsonl`) rồi xuất 2 bài. **Bài A** = RRF thuần, tối đa 3 doc và 5 chunk thuộc các doc đó: TB 3,00 doc và 4,20 chunk mỗi câu, zip 2,59 MB. **Bài B** = rerank + ngưỡng động (T_min=-inf, Delta=1, K_max=8, K_doc=5, chọn trên mock dev set): TB 2,91 doc và 3,41 chunk mỗi câu, zip 2,08 MB (xa trần 100 MB). `validate_submission.py` (zip đúng 1 file `submission.json` ở gốc; đủ 1.200 id khớp `query.parquet`, không trùng; `relevant_docs` là số nguyên có trong `links_corpus`; không trùng doc/chunk; hai trường luôn có; chunk không rỗng và <= 1.024 token theo tokenizer BGE-M3) báo HỢP LỆ cả hai; 0 câu rỗng ở cả hai trường. `relevant_chunks` là `text` nguyên văn trong `data/chunks`, chunk của bài B luôn thuộc doc đã liệt kê; bài A chỉ lấy chunk thuộc doc đã liệt kê. Lưu ý: 7 chunk trong bài B và 2 trong bài A là phần đầu trang hỏi-đáp tiếng Trung có 87-91% khoảng trắng (330-411 token, hợp lệ nhưng chủ yếu là metadata), tỷ lệ chunk dạng này trong corpus CHƯA ĐO. Quy trình A/B: nộp cả hai, so điểm Docs F2 và Chunks F2 của leaderboard; ghi điểm thật vào đây khi có.

- **[14/10/2026] SỬA LỖI ĐỊNH DẠNG BÀI NỘP (đính chính doc 01)**: cả hai bài nộp đầu tiên bị evaluator Codabench báo lỗi `Query 1 chunk 0 must be an object` vì `relevant_chunks` là chuỗi trần. Schema đúng (trang Phương pháp đánh giá + ví dụ BTC do user dán): mỗi chunk là object `{"doc_id": ..., "chunk_text": "..."}`. Nguyên nhân sai của ta: doc 01 mục 6 ghi ví dụ chuỗi trần, ta không có nguồn chính thức cho schema object và `validate_submission.py` kiểm tra theo chính ví dụ sai đó nên không bắt được. Đã sửa `make_submission.py` và `validate_submission.py` (kiểm tra object đúng 2 khóa, `doc_id` của chunk nằm trong `relevant_docs`), tạo lại 2 bài (A 2,62 MB, B 2,11 MB), cả hai HỢP LỆ theo validator đã sửa. Chưa biết evaluator thật có đòi thêm gì (ví dụ kiểu chuỗi của `doc_id`) hay không; cần nộp lại để xác nhận. Doc 02 mục 1.2 cũng đã đính chính định nghĩa Recall chunk-level (mẫu số là chunk tham chiếu).

- **[14/10/2026] KẾT QUẢ CHẤM THẬT ĐẦU TIÊN VÀ PHÁT HIỆN LÀM SAI GIẢ ĐỊNH NỀN (rất quan trọng)**: bộ chấm Codabench chạy 600 câu (593 câu có nhãn). Điểm: **bài A (RRF, 3 doc / 4,19 chunk mỗi câu)**: FINAL 0,0253 = trung bình của DOCS_F2 0,0354 và CHUNKS_F2 0,0153; DOCS P/R 0,3839 / 0,0305; CHUNKS P/R 0,1288 / 0,0142. **Bài B (rerank + ngưỡng động, 2,88 doc / 3,40 chunk)**: FINAL 0,0237; DOCS_F2 0,0326, CHUNKS_F2 0,0149; DOCS P/R 0,4417 / 0,0277; CHUNKS P/R 0,1919 / 0,0130. Mốc BTC BM25: DOCS_F2 0,5587, CHUNKS_F2 0,1941, FINAL 0,3764. **Phát hiện từ `details.jsonl` của bộ chấm: mỗi câu có trung bình 71,0 doc tham chiếu (trung vị 60, P10 12, P90 145, tối đa 190) và 74,7 chunk tham chiếu (trung vị 64, tối đa 200), tức khoảng 1 chunk tham chiếu mỗi doc.** Vì vậy trả 3 doc thì Recall tối đa ~4%; giả định K_doc=3 / K_max=5 (lấy từ Stage 2, "ít mà đúng") sai hoàn toàn ở Stage 3, và mock dev set (mỗi câu chỉ ~1,4 doc nhãn) đã đánh lừa ta. Số liệu phụ: 71,2% câu (A) có ít nhất 1 trong 3 doc đúng (doc đúng TB 1,14/câu); chunk: 40,3% câu có >=1 chunk khớp luật LCS 0,40; `unknown_doc` (chunk thuộc doc không có chunk tham chiếu) 1.468 trên khoảng 2.514 chunk nộp (A). Trong các chunk thuộc doc đúng, khoảng 30% khớp một chunk tham chiếu. Rerank (B) làm Chunk precision tăng (0,129 -> 0,192) nhưng recall chung không đổi vì số lượng quá nhỏ; chưa kết luận gì về rerank trước khi trả đủ nhiều doc. **Việc đang làm**: truy hồi sâu RRF top-300 mỗi nguồn (`make_submission.py`), xuất các biến thể K doc x 1 chunk/doc (10, 30, 100) để quét K trên leaderboard (hạn mức 10 bài/ngày, hôm nay đã dùng 4 gồm 2 bài lỗi định dạng). Mock dev set hiện không còn dùng để chọn K; cần dựng dev set lớn nhãn (hàng chục doc/câu) hoặc dùng chính leaderboard.

- **[14/10/2026] ĐƯỜNG CONG K TRÊN LEADERBOARD THẬT (RRF doc xếp theo lần xuất hiện đầu, mỗi doc 1 chunk; 600 câu chấm)**: K=10 → FINAL 0,0572; K=30 → 0,0996; **K=100 → 0,1467** (DOCS_F2 0,2133, P 0,1659, R 0,2840; CHUNKS_F2 0,0801, P 0,0638, R 0,1074). Điểm còn tăng ở K=100. **Thí nghiệm kế tiếp**: bỏ dense, chỉ BM25 Tantivy xếp doc theo chunk cao nhất (`make_submission.py --source bm25`): bm25_K40x1 (23,9 MB) và bm25_K100x1 (60,1 MB), đã qua validator, đang chờ user nộp (hôm nay đã dùng 7/10 lượt).

- **[14/10/2026] KẾT QUẢ BM25 THUẦN (Tantivy chunk, xếp doc theo chunk cao nhất, mỗi doc 1 chunk) - BÁC BỎ GIẢ THUYẾT "BỎ DENSE"**: bm25_K40x1 → FINAL 0,0624 (DOCS_F2 0,0934, P 0,1273, R 0,1034; CHUNKS_F2 0,0314, P 0,0432, R 0,0367); bm25_K100x1 → FINAL **0,0786** (DOCS_F2 0,1178, P 0,0892, R 0,1598; CHUNKS_F2 0,0395, P 0,0302, R 0,0565). So với RRF cùng K=100 (FINAL 0,1467, DOCS P 0,166, R 0,284): BM25 thuần chỉ bằng ~54% điểm, precision doc thấp hơn gần một nửa. Vậy dense ĐANG GIÚP, không gây hại; giả thuyết trước đó ("nhãn gần với BM25 nên dense làm lệch") bị bác bỏ cho BM25 CỦA TA. Ưu tiên kế tiếp: lấy `details.jsonl` của các bài đã chấm (cho biết doc nào đúng theo từng rank) để đánh giá offline các cách xếp hạng trong phạm vi doc đã có nhãn, thay vì tốn lượt nộp.

- **[14/10/2026] PHÂN TÍCH `details.jsonl` (RRF K100 và BM25 K100, 600 câu) VÀ GIẢ THUYẾT "CHUNK THAM CHIẾU DÀI HƠN CHUNK CỦA TA"**: tỷ lệ chunk khớp theo nhóm rank (RRF): 1-10 0,127; 11-20 0,079; 21-30 0,071; ... 91-100 0,038; BM25 thấp hơn RRF khoảng 2 lần ở mọi nhóm (1-10 0,065; 91-100 0,017). Doc đúng TB 16,4/100 (RRF) và 8,8/100 (BM25); chunk khớp TB 6,31 và 2,98 trên 100. Tỷ lệ chunk khớp / doc đúng chỉ 0,385 (RRF): ngay cả khi đúng doc, chunk của ta chỉ khớp một chunk tham chiếu 38% số lần. Overlap của chunk khớp TB 0,66, median 0,60 (ngưỡng 0,40), nhiều chunk chỉ vừa qua ngưỡng. `token_count` BTC báo lệch vài token so với `n_tokens` của ta (TB -2, tối đa 31), tức tokenizer gần giống BGE-M3 nhưng không giống hệt. Domain chunk khớp trải đều (suckhoedoisong 9,0%, thanhnien 10,7%, vinmec 6,0%, 120ask.com tiếng Trung 6,8% trong những chunk RRF trả về), nên dense có tìm đúng cả doc tiếng Trung. **Giả thuyết (CHƯA kiểm chứng)**: chunk tham chiếu dài hơn chunk ~350 token của ta; vì overlap = LCS/|g| (mẫu số là chunk tham chiếu), nộp đoạn dài hơn (tới <=1.024 token, mức khuyến nghị) chỉ làm tăng overlap mà không đổi precision. **Thí nghiệm kế tiếp** (`make_submission.py 150x30x900`): `relevant_docs` = 150 doc xếp đầu của RRF (tách biệt với chunk vì hai cấp chấm độc lập), `relevant_chunks` = 30 doc đầu, mỗi doc là cửa sổ ghép chunk neo với chunk liền kề cùng tài liệu tới <=900 token (đếm thật bằng tokenizer BGE-M3, chừa biên cho lệch tokenizer), file `submission_rrf_150x30x900.zip` (33,4 MB, HỢP LỆ). So với K100x1 (CHUNKS_F2 0,0801, DOCS_F2 0,2133) ta sẽ thấy riêng ảnh hưởng của cửa sổ dài lên chunk và ảnh hưởng của K=150 lên doc. Hôm nay đã dùng 9/10 lượt, còn đúng 1 lượt cho bài này.

- **[14/10/2026] KẾT QUẢ GIẢ THUYẾT CỬA SỔ DÀI (rrf_150x30x900, bài 5591, 600 câu): FINAL 0,1700** (K100x1: 0,1467). DOCS_F2 0,2241 (P 0,1374, R 0,3368; K100: 0,2133, P 0,166, R 0,284); **CHUNKS_F2 0,1159 (P 0,2081, R 0,1189; K100x1: 0,0801, P 0,0638, R 0,1074)**. Giả thuyết ĐƯỢC XÁC NHẬN: nộp cửa sổ dài (<=900 token, ghép chunk liền kề) làm Chunks Precision tăng 3,3 lần (0,064 -> 0,208) với cùng cách xếp hạng. Recall chunk chỉ tăng nhẹ vì mới nộp 30 chunk/câu; 30 cửa sổ trúng TB 6,2 mà tìm được TB 8,9 chunk tham chiếu (tính theo Recall 0,1189 x 74,7), tức một cửa sổ khớp trung bình ~1,4 chunk tham chiếu: chunk tham chiếu NHỎ HƠN cửa sổ 900 token (suy luận, chưa có dữ liệu kích thước chunk tham chiếu). Doc 100 -> 150: Recall +0,053 (~+3,8 doc đúng trên 50 doc thêm, precision biên ~7,5%); F2 tối ưu khi precision biên ~ F2/5 ≈ 4,5%, nên K còn nên tăng nữa (ước lượng, chưa đo).

- **[14/10/2026] BÀI 5597 (rrf_300x60x900; 300 doc cap, TB ~230 doc thực tế, 60 cửa sổ <=900 token/câu; 600 câu): FINAL 0,1880** (5591: 0,1700). DOCS_F2 0,2265 (P 0,1144, R 0,3920; 5591: 0,2241, P 0,1374, R 0,3368): doc gần như đứng yên khi tăng K 150 -> ~230 (precision biên của 80 doc thêm ~ (0,392-0,3368) x 71 / 80 = 4,9%, sát mức F2/5 ≈ 4,5%): K~230 đã gần tối ưu cho cách xếp hạng hiện tại. **CHUNKS_F2 0,1495 (P 0,1659, R 0,1717; 5591: 0,1159, P 0,2081, R 0,1189)**. Phân tích `details.jsonl` của 5597: cửa sổ trung bình 680 token (median 722, max 934); tỷ lệ cửa sổ khớp theo rank 1-10 0,278 / 11-20 0,185 / 21-30 0,154 / 31-40 0,140 / 41-50 0,122 / 51-60 0,105, tức tất cả vượt xa ngưỡng biên (~F2/5 ≈ 3%), nên thêm cửa sổ vẫn có lợi nhưng bị trần zip 100 MB (60 cửa sổ = 63,2 MB). Overlap của cửa sổ khớp: TB 0,77, phân vị 10/25/50/75/90 = 0,50/0,61/0,74/0,99/1,00; 40,7% >= 0,9 (chunk tham chiếu nằm gọn trong cửa sổ), 24,0% trong [0,4; 0,6). Mỗi cửa sổ khớp tìm được TB 1,02 chunk tham chiếu và số chunk tham chiếu / doc tham chiếu = 1,05 (ĐÍNH CHÍNH: ước lượng "~1,4 chunk/cửa sổ" ở mục trước là sai, chunk tham chiếu không nhỏ hơn nhiều). Đòn bẩy còn lại lớn nhất: CHẤT LƯỢNG XẾP HẠNG (DOCS P chỉ 0,114 ở ~230 doc). Thí nghiệm kế: xếp doc theo TỔNG đóng góp RRF của mọi chunk (`300x60x900xsum`) thay vì lần xuất hiện đầu; sau đó rerank sâu (BGE-reranker-v2-m3 có tiêu đề trên top-150 chunk, ~180k cặp/90 phút GPU) để A/B trên leaderboard vì mock dev set không đáng tin để chọn.

- **[15/10/2026] RERANK SÂU XONG VÀ ĐÍNH CHÍNH DỰ ĐOÁN VỀ TẬP DOC**: `rerank_deep.py` chấm xong 1.200/1.200 câu (top-150 chunk của RRF, BGE-reranker-v2-m3 có tiêu đề, 6.037 giây, `data/submission/rerank_d150.jsonl`); script chờ tự xuất bài bị hệ thống dừng 2 lần vì thiếu RAM (không phải lỗi code), sau đó chạy tay `make_submission.py --source rerank 150x60x900 230x60x900`. Hai bài `submission_rerank_150x60x900.zip` (60,0 MB, TB 150 doc) và `submission_rerank_230x60x900.zip` (60,4 MB, TB 217 doc) đều HỢP LỆ. **DỰ ĐOÁN SAI của ta**: tôi đã nói rerank sẽ đổi được tập doc khi cắt K, nhưng pool rerank chỉ là top-150 CHUNK (~110 doc), nhỏ hơn K nên mọi K >= ~110 đều lấy nguyên tập doc của pool cộng phần đuôi RRF: giao tập doc của rerank150 với RRF K150 là 1,00, của rerank230 với RRF là 0,95. Vậy rerank KHÔNG cải thiện DOCS_F2 (ước tính bằng RRF cùng K: 0,2241 ở K150, 0,2265 ở ~230); nó chỉ đổi 35% trong 60 doc đầu (giao top-60 với RRF 0,65) nên chỉ đo được ảnh hưởng lên CHUNKS_F2. Muốn rerank ảnh hưởng tập doc phải rerank pool lớn hơn (top-300 chunk, ~230 doc) rồi cắt K nhỏ hơn: chưa làm, ~180.000 cặp nữa ~100 phút GPU. Khuyến nghị nộp `rerank_230x60x900` (giữ tập doc ngang bài 5597) thay cho `rerank_150x60x900`.

- **[15/10/2026] BÀI 5628 (rerank_230x60x900; TB 217 doc, 60 cửa sổ <=900 token chọn theo điểm rerank; 600 câu): FINAL 0,2006**. DOCS_F2 0,2265 (P 0,1163, R 0,3861), **bằng đúng bài 5597 như dự đoán** (tập doc giao 0,95 với RRF, nên DOCS_F2 không đổi). **CHUNKS_F2 0,1748 (P 0,1956, R 0,2006)** so với 5597 là 0,1495 (P 0,1659, R 0,1717): +0,0253 F2, Precision +18%, Recall +17%. Reranker CÓ ÍCH khi chọn doc nào nhận cửa sổ, KHẾT LUẬN trực tiếp từ điểm thật (khác dev set bị lệch nhãn, đã kết luận sai chiều ở mục 14/10). Hệ quả: rerank pool lớn hơn nên cải thiện cả DOCS (hiện pool rerank chỉ ~110 doc nên không đổi được tập doc). Điểm lịch sử: 0,0253 -> 0,1467 (K100) -> 0,1700 (cửa sổ dài) -> 0,1880 (60 cửa sổ) -> 0,2006 (rerank).

- **[15/10/2026] GHI CHÚ TRONG LÚC CHỜ RERANK SÂU #2 (trạng thái để phiên sau tiếp tục không cần hỏi lại)**: (1) **Đang chạy**: `python rerank_deep.py 150 300` (nền, log `data/rerank_deep2.log`, đầu ra `data/submission/rerank_r150_300.jsonl`, ghi dần theo lô 50 câu; kỳ vọng ~100 phút; chạy lại cùng lệnh sẽ bỏ qua câu đã xong; không có file STOP/guard RAM riêng, dựa vào việc ghi dần). Điểm rerank của đoạn 0-150 đã đổi tên thành `rerank_r0_150.jsonl`. (2) **Khi xong, việc kế tiếp**: chạy `python make_submission.py --source rerank 150x60x900 230x60x900` (tự ghép mọi `rerank_r*.jsonl`, nối đuôi RRF), chạy `validate_submission.py` cho cả hai, rồi đưa user nộp; so với bài 5628 (FINAL 0,2006, DOCS_F2 0,2265, CHUNKS_F2 0,1748) để biết rerank pool 300 chunk có làm DOCS_F2 tăng không. (3) **Việc nên làm sau đó (chưa làm)**: số cửa sổ chunk còn tăng được tới trần 100 MB (60 cửa sổ = ~60 MB, tỷ lệ khớp rank 51-60 vẫn 10,5% >> ngưỡng ~3%); ngưỡng điểm rerank động thay cho K cố định; cân nhắc rerank pool sâu hơn nữa (top-600 chunk ~7 giờ GPU) nếu Docs P vẫn thấp; thử thêm dense-only để biết nguồn nào mang nhãn. (4) **Hạn mức nộp**: 10 bài/ngày (ngày 14/10 đã dùng ~11 theo đếm của user gồm 2 bài lỗi định dạng), đừng nộp thí nghiệm ít thông tin; `submission_rrf_300x60x900xsum.zip` (xếp doc theo tổng RRF) đã tạo nhưng CHƯA nộp. (5) **Quy ước chạy nền trên máy này**: hệ thống tự dừng shell nền (script chờ) khi RAM thấp, đã xảy ra 2 lần; tiến trình Python chính không bị dừng; KHÔNG tự chạy lại shell nền sau khi bị dừng, báo user. Khi xuất bài nên chạy trực tiếp (foreground) và đóng bớt Chrome/Edge trước.

- **[15/10/2026] RERANK SÂU #2 XONG (đoạn xếp hạng 150-300, 1.200/1.200 câu, 5.490 giây, không lỗi) VÀ XUẤT 2 BÀI TỪ POOL 300 CHUNK**: `make_submission.py --source rerank 150x60x900 230x60x900` (chạy trực tiếp, RAM trống 8,5 GB) -> `submission_rerank_150x60x900.zip` (59,7 MB, TB 150 doc) và `submission_rerank_230x60x900.zip` (60,0 MB, TB 217 doc), cả hai HỢP LỆ. So với RRF (bài 5597): **tập doc của bản 150 chỉ giao 0,73 với RRF top-150** (27% doc khác nhau, lần đầu rerank đổi tập doc), bản 230 giao 0,95 với RRF toàn bộ, top-60 doc có cửa sổ giao 0,52 (bài 5628 giao 0,65). Chưa có điểm. So sánh cần làm khi có điểm: bản 150 so với DOCS_F2 của RRF cùng K150 (0,2241, bài 5591) cho biết rerank có cải thiện chất lượng tập doc không; CHUNKS_F2 so với bài 5628 (0,1748). Khuyến nghị nộp bản 150 trước (thông tin mới ở cấp doc), bản 230 sau nếu còn lượt.

- **[15/10/2026] KẾ HOẠCH NỘP CHO NGÀY MỚI (hạn mức 10 bài/ngày; user nói có thể được nộp > 100 MB, CHƯA xác nhận: doc 01 vẫn ghi trần 100 MB chốt 06/10, nên các bản > 100 MB chỉ nộp nếu trang nộp thật sự cho phép)**. Tất cả dùng pool rerank 300 chunk (`rerank_r0_150` + `rerank_r150_300`), mỗi bản đổi đúng MỘT yếu tố so với bản trước để đọc được nguyên nhân. Thứ tự nộp đề nghị: (1) `rerank_150x60x900` (đổi tập doc 27% so với RRF K150; so DOCS_F2 với 0,2241 và CHUNKS_F2 với 0,1748 của 5628); (2) `rerank_230x60x900` (tập doc ~ RRF, đo ảnh hưởng của pool 300 lên chunk); (3) `rerank_150x90x900` (~90 MB: chỉ tăng số doc có cửa sổ 60 -> 90, đo Recall chunk biên); (4) `rerank_150x45x900xm2` (~90 MB: cùng dung lượng với (3) nhưng 45 doc x 2 cửa sổ không chồng nhau, so (3) để biết thêm doc hay thêm cửa sổ cùng doc có lợi hơn); (5) `rerank_230x120x900` (~120 MB, CHỈ nếu nộp được > 100 MB). Các bản (3)-(5) đang được tạo bằng `make_submission.py --source rerank 150x90x900 150x45x900xm2 230x120x900` (log `data/make_submission_more.log`). Chưa triển khai: cắt doc theo ngưỡng điểm rerank (cần đưa điểm vào bước chọn).

- **[15/10/2026] KIỂM TRA BA BẢN XUẤT THÊM (`make_submission.py --source rerank 150x90x900 150x45x900xm2 230x120x900`, xong, không còn tiến trình nào của dự án chạy; GPU trống ngoài ~450 MB của ứng dụng khác)**: (1) `submission_rerank_150x90x900.zip` **89,7 MB, HỢP LỆ**, đúng 150 doc và 90 chunk mỗi câu: dùng được. (2) `submission_rerank_230x120x900.zip` **120,4 MB, đúng nội dung nhưng validator báo vượt 100 MB** (như dự kiến), TB 217 doc và 109-120 chunk mỗi câu: chỉ nộp nếu trang nộp thật sự nhận > 100 MB. (3) `submission_rerank_150x45x900xm2.zip` **48,0 MB, KHÔNG HỢP LỆ (1 lỗi: id=433 có chunk trùng) và KHÔNG đạt mục đích thiết kế**: chỉ có TB 48,0 chunk mỗi câu (45 đến 70), không phải ~90, vì trong pool 300 chunk mỗi doc hiếm khi có chunk thứ hai cách chunk neo >= 4 vị trí; nên bản này không so sánh công bằng được với `150x90x900`. **KHÔNG nộp bản này** (đính chính kế hoạch ở mục kế hoạch nộp bên trên, mục (4)). Sửa nếu cần: `write_zip` hiện không loại chunk trùng như `unique_chunks` ở phiên bản cũ. Thứ tự nộp còn lại: `rerank_150x60x900` -> `rerank_230x60x900` -> `rerank_150x90x900` -> (`rerank_230x120x900` nếu > 100 MB được nhận).

- **[15/10/2026] KẾT QUẢ 3 BÀI POOL RERANK 300 (600 câu chấm; cột: FINAL / DOCS_F2 / CHUNKS_F2 / DOCS P, R / CHUNKS P, R)**: bài 5673 `rerank_150x60x900`: 0,2135 / 0,2491 / 0,1779 / 0,1549, 0,3688 / 0,1989, 0,2043. Bài 5675 `rerank_230x60x900`: 0,2039 / 0,2298 / 0,1779 / 0,1181, 0,3912 / 0,1989, 0,2043. Bài 5674 `rerank_150x90x900`: **0,2227 (tốt nhất)** / 0,2491 / 0,1964 / 0,1549, 0,3688 / 0,1690, 0,2466. (1) **Rerank sâu cải thiện tập doc**: K150 DOCS_F2 0,2491 so với RRF cùng K 0,2241 (+0,025), precision 0,137 -> 0,155, recall 0,337 -> 0,369. (2) **K nên nhỏ hơn 230**: doc từ hạng 150 đến ~217 thêm recall 0,0224 x 71 = 1,6 doc đúng trên ~67 doc (~2,4%), thấp hơn ngưỡng biên F2/5 ~ 5%; DOCS_F2 giảm 0,2491 -> 0,2298. K tối ưu có thể dưới 150 (CHƯA đo). (3) **Thêm cửa sổ vẫn có lợi**: 60 -> 90 cửa sổ, CHUNKS_F2 0,1779 -> 0,1964; 30 cửa sổ thêm trúng ~3,3 trên 30 (~11%), vẫn xa ngưỡng ~3%. (4) CHUNKS_F2 của 5673 và 5675 bằng nhau vì top-60 doc có cửa sổ trùng nhau. Bài 5628 (rerank pool 150): 0,2006 -> 5675 chỉ +0,0033, pool 300 cho chunk gần như không thêm. `230x120x900` không nộp vì trần 100 MB chưa được nới.
- **[15/10/2026] KẾT QUẢ K=110/130 VỚI 95 CỬA SỔ (600 câu chấm; FINAL / DOCS_F2 / CHUNKS_F2 / DOCS P, R / CHUNKS P, R)**: bài 5684 `rerank_130x95x900`: **0,2245** / 0,2513 / 0,1978 / 0,1696, 0,3533 / 0,1648, 0,2519 (tốt nhất). Bài 5683 `rerank_110x95x900`: 0,2241 / 0,2504 / 0,1978 / 0,1865, 0,3356 / 0,1648, 0,2519. Cùng bài 5674 (K150, 90 cửa sổ): 0,2227 / 0,2491 / 0,1964. DOCS_F2 gần phẳng quanh 0,250 khi K từ 110 đến 150 (precision biên 110->130 ~6,3%, 130->150 ~5,5%, sát ngưỡng F2/5 ~5%): chỉnh K đã chạm trần, K~130 tối ưu nhẹ. Thêm 5 cửa sổ (90 -> 95): CHUNKS_F2 +0,0014 (~9% trúng trên 5 cửa sổ thêm), tăng rất ít vì zip đã sát 100 MB (99,2 MB). Hai bài 5683/5684 có CHUNKS bằng nhau vì cùng 95 cửa sổ trên cùng top doc.
- **[15/10/2026] CHỌN DOC/CỬA SỔ THEO ĐIỂM RERANK (`make_submission.py --source rerank --dynamic DOC_MIN DOC_CAP BUDGET WINDOW_CAP`; 600 câu chấm; FINAL / DOCS_F2 / CHUNKS_F2 / DOCS P, R / CHUNKS P, R)**. Cơ sở: phân tích `details_5684.jsonl` (600/600 câu khớp thứ tự cửa sổ với điểm rerank) cho tỷ lệ cửa sổ trúng theo điểm rerank: <-4: 1,3%; [-4,-2): 4,6%; [-2,0): 9,8%; [0,2): 19,4%; [2,4): 28,3%; >=4: 37,1%; trong cùng nhóm hạng, điểm cao trúng gấp 2-3 lần điểm thấp (hạng 30-60: 22,6% so với 9,1%), tương quan điểm trung bình top-30 với số doc đúng mỗi câu 0,64. Bài 5694 `dyn-3` (doc có điểm >= -3, TB 146,6 doc/câu, 110.000 cửa sổ phân theo điểm, ngưỡng cửa sổ -1,04): **0,2294** / 0,2601 / 0,1987 / 0,1591, 0,3646 / 0,1776, 0,2317 (tốt nhất). Bài 5695 `dyn-4` (điểm >= -4, TB 169,9 doc): 0,2257 / 0,2527 / 0,1987 / 0,1425, 0,3787 / 0,1776, 0,2317. So 5684 (K130 cố định): DOCS_F2 +0,0088 (dyn-3), CHUNKS_F2 +0,0009 (chỉ cắt cửa sổ theo điểm: precision tăng 0,165 -> 0,178, recall giảm 0,252 -> 0,232, F2 phẳng). Kết luận: cắt DOC theo điểm hơn K cố định, ngưỡng nghiêm hơn (-3) tốt hơn -4 (xu hướng tiếp theo: thử -2, -2,5); phân bổ cửa sổ theo điểm KHÔNG cải thiện chunk, trần chunk ~0,198 ở dung lượng 100 MB.
- **[15/10/2026] KẾT QUẢ NGƯỠNG DOC -2 VÀ -2,5 (600 câu chấm; FINAL / DOCS_F2 / CHUNKS_F2 / DOCS P, R)**: bài 5715 `dyn-2.5` (TB 133,6 doc/câu): **0,2306** / 0,2626 / 0,1987 / 0,1705, 0,3532 (tốt nhất). Bài 5713 `dyn-2` (119,9 doc): 0,2301 / 0,2616 / 0,1987 / 0,1842, 0,3374. Đường cong ngưỡng doc: -4 -> 0,2527; -3 -> 0,2601; -2,5 -> 0,2626; -2 -> 0,2616 (DOCS_F2). Phẳng quanh -2,5 đến -2 (chênh 0,001, trong sai số); đỉnh ~ -2,5. CHUNKS_F2 vẫn 0,1987 vì cùng 110.000 cửa sổ. Chỉnh ngưỡng doc đã chạm trần; muốn tăng nữa phải cải thiện chất lượng/độ phủ ứng viên (recall ứng viên), không phải cách cắt.
- **[16/10/2026] POOL RERANK 600 (`rerank_r0_600.jsonl`, 14.674 giây, guard RAM/GPU/VRAM hoạt động, 0 lỗi) VÀ KẾT QUẢ (600 câu chấm; FINAL / DOCS_F2 / CHUNKS_F2 / DOCS P, R / CHUNKS P, R)**: bài 5781 `dyn-1.5_400` (TB 167,3 doc, 110.000 cửa sổ): **0,2312** / **0,2698** / 0,1927 / 0,1635, 0,3751 / 0,1842, 0,2235. Bài 5780 `dyn-1_400` (139,9 doc): 0,2280 / 0,2633 / 0,1927 / 0,1838, 0,3419 / 0,1842, 0,2235. So 5715 (pool 300, 134 doc): 0,2306 / 0,2626 / 0,1987. (1) Pool sâu cho DOCS_F2 +0,0007 ở ~140 doc và +0,0072 ở ~167 doc: lợi ích nhỏ; precision biên 140 -> 167 doc ~ (0,3751-0,3419) x 71 / 27 = 8,7% còn trên ngưỡng ~5%, nên số doc nhiều hơn (bản `dyn-2.5_400`, 222,6 doc, CHƯA nộp) có thể còn thêm. (2) CHUNKS_F2 GIẢM 0,1987 -> 0,1927 (P 0,178 -> 0,184, R 0,232 -> 0,224): chọn cửa sổ theo điểm toàn cục trên pool sâu không tốt hơn; chunk phẳng ~0,19-0,20. (3) Tổng: tinh chỉnh K/ngưỡng/pool chỉ còn cho ~+0,005; cần thay đổi chất lượng xếp hạng để tiến thêm. (4) Phân tích `details_5684.jsonl` theo domain (57.000 cửa sổ, 9.282 trúng = 16,3%), **ĐÃ ĐÍNH CHÍNH 16/10**: bản đầu tính nhầm các domain tiếng Việt không đuôi `.vn` (vinmec.com, hellobacsi.com) vào nhóm không phải tiếng Việt nên con số "78,5% số trúng thuộc .vn" SAI. Phân loại lại theo 14 domain tiếng Trung đã định danh (120ask, cnkang, ask.39.net, baby.39.net, familydoctor.com.cn, zysjonline, a-hospital, zhongyibaodian, zydcd, wujue, youlai, iiyi x2, qihuangzhishu): cửa sổ tiếng Trung = 7.450 (13,1% bài nộp), trúng 539 (5,8% số trúng), tỷ lệ trúng 7,2%; cửa sổ tiếng Việt = 49.550 (86,9%), trúng 8.743 (94,2%), tỷ lệ trúng 17,6%. Nhãn nằm chủ yếu ở tài liệu tiếng Việt (suckhoedoisong 23,2%, thanhnien 19,9%, medlatec 18,0%). CHƯA THỬ truy vấn bằng tiếng Trung (dịch hoặc mở rộng) nên không kết luận về giá trị của hướng đó; đây chỉ là bằng chứng gián tiếp, phân loại theo domain.
- **[16/10/2026] BÀI 5786 `dyn-2.5_400` (pool 600, TB 222,6 doc, 110.000 cửa sổ): FINAL 0,2303 / DOCS_F2 0,2688 / CHUNKS_F2 0,1917 / DOCS P 0,1331, R 0,4282 / CHUNKS P 0,1857, R 0,2227.** So 5781 (167 doc): 0,2312 / 0,2698 / 0,1927. DOCS_F2 phẳng 0,2688-0,2698 khi số doc từ 167 lên 223 (recall +0,053 nhưng precision -0,030): đỉnh quanh 170-190 doc; chỉnh số doc/ngưỡng/pool đã hết dư địa, FINAL tốt nhất 0,2312 (bài 5781). Recall doc 0,428, nghẽn là PRECISION (0,13-0,16), tức là khả năng phân biệt doc đúng/sai, không phải độ phủ: pseudo-relevance feedback (tăng recall) vì vậy không còn là ưu tiên. Thử gộp điểm cấp doc (offline, `details_5684.jsonl`, AUC trung bình trong 95 doc nộp mỗi câu, 578 câu): max chunk 0,652; tổng sigmoid mọi chunk 0,663; max+0,3 log(số chunk) 0,658; chunk thứ hai 0,577; số chunk 0,562 — cách gộp chỉ thêm ~0,01 AUC, không đáng kể.
- **[16/10/2026] THỬ QWEN3-Reranker-0.6B (offline, 100 câu / 95 câu có nhãn, 9.500 cặp; AUC trung bình trên nhãn cửa sổ trúng/trượt của `details_5684`)**: BGE-reranker hiện tại 0,6584; Qwen3-Reranker-0.6B riêng 0,6570 (ngang BGE); ghép z-score BGE + Qwen 0,6784 (+0,020); ghép trọng số Qwen x2 0,6775. Tốc độ thật CHỈ 5,3 cặp/giây (1.794 giây cho 9.500 cặp; GPU dùng chung, ưu tiên thường, batch 8), nên rerank đủ 360.000 cặp ~ 19 giờ. Với ngưỡng đã đặt (cần >= +0,03 AUC mới chạy toàn bộ), KẾT LUẬN: KHÔNG chạy; bản 4B còn chậm hơn nhiều lần. Ngõ cụt đã đo: ghép thêm reranker chỉ thêm ~0,02 AUC ở giá >15 giờ GPU.
- **[16/10/2026] BÀI 5793 `dyn-1.5_400_101000_w980` (cửa sổ <=980 token, 101.000 cửa sổ, cùng tập doc với 5781): FINAL 0,2297 / DOCS_F2 0,2698 (bằng 5781 như kỳ vọng) / CHUNKS_F2 0,1897 / CHUNKS P 0,1942, R 0,2154.** So 5781 (cửa sổ 900, 110.000 cửa sổ): CHUNKS_F2 0,1927, P 0,1842, R 0,2235. Cửa sổ dài hơn nâng precision mỗi cửa sổ +5,4% tương đối (+9% kích thước) nhưng số cửa sổ giảm 8% làm recall giảm 3,6%: F2 chunk -0,003. Kích thước cửa sổ không phải đòn bẩy (hiệu ứng ngang nhau); giữ 900. Ước lượng thu nhỏ cửa sổ xuống ~700 cũng xấp xỉ hòa (không thử).
- **[16/10/2026] PHÂN TÍCH K THEO TỪNG CÂU (offline, `details_5780/5781/5786.jsonl`; ba mức doc lồng nhau 133/160/216 doc TB; DOCS_F2 tính lại khớp bảng: 0,2633/0,2698/0,2688 trên 593 câu)**: F2 cấp doc của một câu = 5r/(4G+k) (r doc đúng, k doc nộp, G doc tham chiếu). Chọn đúng mức tốt nhất cho TỪNG câu (oracle, 3 mức) cho DOCS_F2 0,2911 (+0,021 so 0,2698): phân bố mức tốt nhất 235/141/217 câu cho mức nhỏ/giữa/lớn. Quy tắc thực tế (chọn mức theo tỷ lệ k1/k3 hoặc k1, ngưỡng học trên một nửa số câu, đo trên nửa còn lại, 2-fold): DOCS_F2 0,2745 và 0,2766 so 0,2688 và 0,2708 của mức giữa cố định, tức chỉ +0,006 trên DOCS_F2 (khoảng +0,003 trên FINAL), trong sai số với 593 câu. Hình dạng quy tắc: câu có ít doc đạt điểm thì hạ ngưỡng (nộp nhiều doc hơn), câu có nhiều doc đạt điểm thì siết ngưỡng, tức hội tụ về số doc xấp xỉ cố định. Kết luận: cắt theo từng câu không phải đòn bẩy lớn; không triển khai trừ khi cần vài phần nghìn cuối.


### 3d. TỔNG KẾT GIAI ĐOẠN 8 TẠI 16/10/2026 - BẢN PUBLIC FINAL, TÁI TẠO, KẾ HOẠCH TIẾP (đọc mục này đầu tiên khi mở phiên mới)

**[CẬP NHẬT 18/10/2026: bản Public chốt MỚI là bài 6039 (ghép Qwen + lọc theo corpus mới), FINAL 0,2427; xem mục J, L, M, N ở cuối phần này. Bài 5886 và 5781 dưới đây giữ làm dự phòng.]**

**A. Bản chốt cho Public: bài 5781 = `data/submission/submission_rerank_dyn-1.5_400_110000.zip`** (96,36 MB, sha256 `e91451ad2ad37a65043045614ae6b96522ab0cf969c84ab7aea5ceb696f03032`, tạo 15/10 22:45; TB 167,3 doc, 1.200 câu, 110.000 cửa sổ <=900 token). Điểm Public (600 câu chấm): **FINAL 0,2312**, DOCS_F2 0,2698 (P 0,1635, R 0,3751), CHUNKS_F2 0,1927 (P 0,1842, R 0,2235). Lý do chọn: FINAL cao nhất trong các bản; các bản sát điểm (5715 0,2306; 5786 0,2303; 5793 0,2297; 5780 0,2280) chênh <= 0,003, trong sai số; bản này chọn doc bằng NGƯỠNG ĐIỂM RERANK (-1,5) nên tổng quát hơn K cố định hay chỉnh theo từng câu, ít rủi ro lệch khi sang bộ câu Private. Điểm tăng lịch sử: 0,0253 -> 0,1467 (K100) -> 0,1700 (cửa sổ dài) -> 0,1880 (60 cửa sổ) -> 0,2006 (rerank) -> 0,2227 (rerank sâu 150 doc, 90 cửa sổ) -> 0,2306 (ngưỡng điểm) -> 0,2312 (pool 600).

**B. Tái tạo bản chốt từ đầu** (chạy trong `phan-tich/stage3`, venv của dự án; mỗi bước chạy nền một lệnh, đóng bớt Chrome/Edge, RAM trống >= 8 GB; hệ thống từng dừng lệnh nền khi RAM < ~6 GB): (1) chunk + embed + Tantivy + binary index (mục 3b/3c); (2) `python make_submission.py --source rrf` (cache `candidates_rrf_d300.jsonl`) và `--source rrf600` (cache `candidates_rrf600_d600.jsonl`); (3) `python rerank_deep.py 0 150`, `150 300` rồi `python rerank_deep.py 0 600 --candidates candidates_rrf600_d600.jsonl` (ra `rerank_r0_150`, `rerank_r150_300`, `rerank_r0_600`; tổng 26.201 giây ~ 7,3 giờ GPU đo thật (6.037 + 5.490 + 14.674 giây; đoạn cuối chậm hơn vì guard nhiệt 80°C), có guard RAM/GPU/VRAM và file `data/submission/STOP_RERANK`); (4) `python make_submission.py --source rerank --dynamic -1.5 400 110000 200` (mỗi câu luôn có >= 10 doc và >= 5 cửa sổ); (5) `python validate_submission.py data/submission/submission_rerank_dyn-1.5_400_110000.zip` phải báo HỢP LỆ. Tham số `--dynamic DOC_MIN DOC_CAP WINDOW_BUDGET WINDOW_CAP`: doc có điểm rerank (logit BGE-reranker-v2-m3, có tiêu đề) >= DOC_MIN, tối đa DOC_CAP doc; WINDOW_BUDGET cửa sổ điểm cao nhất toàn bộ các câu (mỗi câu tối đa WINDOW_CAP); cửa sổ = chunk neo ghép chunk liền kề cùng tài liệu tới 900 token.

**C. KHÔNG xóa các file này** (cần để tái tạo/so sánh): `data/submission/candidates_rrf_d300.jsonl`, `candidates_rrf600_d600.jsonl`, `rerank_r0_150.jsonl`, `rerank_r150_300.jsonl`, `rerank_r0_600.jsonl`, `data/chunks`, `data/embeddings` (15 GB), `data/dense_index`, `data/tantivy_index`, `data/hf_cache` (BGE-M3, BGE-reranker-v2-m3, Qwen3-Reranker-0.6B), mọi zip bài đã nộp. Có thể xóa khi cần chỗ: `data/pip_cache` (2,5 GB), `data/tmp`, các zip chưa nộp trong `data/submission` (đừng xóa `submission_rerank_dyn-1.5_400_110000.zip`), `data/crawl_cache.sqlite3` chỉ khi chắc không crawl lại (16 GB, là nguồn gốc dữ liệu).

**D. Kế hoạch Private (tối đa 5 bài, hạn 04/11/2026)**: bài nộp gồm cả 1.200 câu nên dùng lại đúng zip bản chốt. Lượt 1 = bản chốt (mục A). Các lượt sau chỉ dùng cho biến thể có lý do rõ ràng (ví dụ `dyn-2.5_400` nhiều doc hơn nếu Private cho thấy precision khác); giữ ít nhất 1 lượt dự phòng cho lỗi định dạng. Không chỉnh tham số theo điểm riêng của 600 câu Public ngoài những gì đã làm (các ngưỡng đều theo điểm rerank, tổng quát).

**E. Việc nghiên cứu TIẾP khi còn thời gian (chưa làm; kỳ vọng đo được ghi kèm, xếp theo giá trị ước tính)**: (1) ghép thêm reranker (Qwen3-Reranker-0.6B ghép BGE: AUC +0,020, 5,3 cặp/giây nên 15-19 giờ GPU cho toàn bộ; chỉ chấm top ~100 doc mỗi câu thì ~6 giờ); (2) cửa sổ thứ hai không chồng nhau cho top doc nhờ pool 600 (`xmN`; bản xm2 trên pool 300 hỏng vì chunk trùng và thiếu chunk, cần khử trùng trong `write_zip`); (3) cắt số doc theo từng câu (oracle 3 mức +0,021 DOCS_F2, quy tắc thực tế CV chỉ +0,006 ~ +0,003 FINAL); (4) viết lại/mở rộng truy vấn bằng LLM mở <=15B (câu hỏi kiểu bệnh nhân kể dài; CHƯA đo); (5) tăng độ phủ corpus: 30,97% corpus chưa vào chỉ mục (875.487 banned_cooldown, 454.068 lỗi mã hóa cnkang, 28.710 needs_js_render, 2.599 failed); tỷ lệ doc nhãn nằm trong phần thiếu CHƯA ĐO; (6) pseudo-relevance feedback (ưu tiên thấp vì recall doc đã 0,43, nghẽn là precision). ĐÃ BÁC BỎ bằng số đo: BM25 thuần, (dịch truy vấn sang tiếng Trung CHƯA THỬ, xem đính chính ở phần phân tích domain 16/10), tinh chỉnh K/ngưỡng/pool thêm, cỡ cửa sổ (900 so 980).

**F. Giai đoạn 9 (Working Notes Paper + Demo Day) - đầu việc**: hạn nộp paper và Demo Day đều 11/11/2026; kết quả chung cuộc chỉ được công nhận khi có paper mô tả đầy đủ phương pháp, nguồn gốc checkpoint model (doc 01 mục 4). Nội dung paper cần: mô tả hệ thống (crawl -> chunk -> BGE-M3 dense + BM25 Tantivy -> RRF -> BGE-reranker-v2-m3 -> chọn doc theo ngưỡng điểm -> cửa sổ 900 token), số liệu dùng dữ liệu theo từng giai đoạn (mục 3, 3b, 3c: 4.394.718 URL, 3.487.922 done, 3.033.854 trang chunk, 7.607.882 chunk; phần loại trừ và lý do), bảng ablation đường điểm leaderboard (mục 3c), các phát hiện then chốt (71 doc/câu tham chiếu; mock dev set gây lệch; cửa sổ dài; rerank sâu), mục kết quả âm (phần E "đã bác bỏ"), nguồn model (BAAI/bge-m3, BAAI/bge-reranker-v2-m3, Qwen3-Reranker-0.6B chỉ thử nghiệm, không dùng trong bài nộp), tài nguyên tính toán (RTX 3050 6GB; rerank 26.201 giây GPU đo thật; tổng thời gian embed 7,6 triệu chunk CHƯA đo chính xác, xem mục 3c). Lịch đề xuất: 17-24/10 nghiên cứu thêm nếu muốn (mục E); 25-31/10 chốt Public; 01-04/11 nộp Private; 05-10/11 viết paper + slide Demo Day.

**G. [16/10/2026] Phân tích chunk trượt (offline, `details_5781.jsonl`, 593 câu có nhãn, 52.665 cửa sổ)**: 77,2% cửa sổ thuộc doc không có chunk nhãn nào (`unknown_doc` 40.664); 22,8% (12.001) thuộc doc có nhãn, trong đó 82,4% trúng; chỉ 4,0% tổng cửa sổ (2.107) là đúng doc mà trượt đoạn. Chunk nhãn tìm được 10.151 / 44.819 (22,6%); cửa sổ trung bình 665 token. Kết luận: chọn đoạn trong doc đúng đã tốt, nâng điểm chunk phải nâng precision chọn doc. Giải thích hao hụt 79,37% -> 69,03%: loại 454.068 trang lỗi mã hóa (13,02% số done, chủ yếu cnkang). Quyết định: KHÔNG tải lại phần tiếng Trung lỗi mã hóa (bằng chứng domain gián tiếp, chi phí lớn); độ phủ chỉ thử domain tiếng Việt bị chặn (~180 nghìn trang, CHƯA đo lợi ích). Slide Demo Day đã cập nhật lên 15 slide kèm ghi chú người nói.

**H. [16/10/2026] KIỂM TRA GHÉP Qwen3-Reranker-0.6B + BGE (hướng 1; `rerank_qwen.py`, đầu ra `data/submission/qwen_check.jsonl`)**: chấm 100 doc đầu (chunk điểm BGE cao nhất của doc) cho 100 câu id nhỏ nhất; 46 câu có nhãn dùng được (nhãn = cửa sổ trúng/trượt của bài 5781, kiểm tra khớp doc_id 0 lệch). Tốc độ thật 8,7 cặp/giây (đã sửa lỗi tính logits toàn vị trí bằng `logits_to_keep=1`; trước đó 5,3 cặp/giây) nên toàn bộ 1.200 câu x 100 doc = 120.000 cặp ~ 3,8 giờ GPU (ước lượng từ tốc độ đo). AUC trung bình theo câu trong ~92 doc đã nộp: BGE 0,6154; Qwen riêng 0,6409; ghép z-score trọng số Qwen 0,25 / 0,5 / 0,75 = 0,6340 / **0,6519** / 0,6462. Mức tăng ghép 0,5 so với BGE: +0,0365, bootstrap theo câu 95% CI [+0,0095; +0,0660], 28/46 câu cải thiện. Mẫu nhỏ; CHƯA có điểm leaderboard.

**I. [17/10/2026] QWEN TOÀN BỘ XONG VÀ BÀI GHÉP (chưa có điểm leaderboard)**: `rerank_qwen.py qwen_top100.jsonl --docs 100` chấm 1.200 câu x 100 doc, đủ 1.200 dòng, 0 NaN, 13.400 giây (~3,7 giờ) ở 8,9 cặp/giây, không lỗi, không bị guard dừng. Bài ghép: `python make_submission.py --source rerank --qwen qwen_top100.jsonl 0.5 --dynamic -1.5 400 110000 200` -> `data/submission/submission_rerank_dyn-1.5_400_110000_qwen0.5.zip` (96,57 MB, sha256 `bd4becf407e970f6fe0bbc12588486cc8a97c1506b6fd203ec09a3b3c25eb563`, HỢP LỆ, 167,9 doc/câu so với 167,3 của bản chốt). So bản chốt 5781: Jaccard tập doc trung bình 0,913; Jaccard tập doc có cửa sổ 0,805. Cách ghép: z-score trong từng câu của BGE và Qwen trên 100 doc đầu, trọng số 0,5, quy về thang BGE (giữ ngưỡng -1,5), chỉ đổi điểm chunk neo; doc ngoài top 100 giữ điểm BGE. Đối chiếu khi có điểm: bản chốt 0,2312 / Docs 0,2698 / Chunks 0,1927.

**J. [17/10/2026] ĐIỂM LEADERBOARD BÀI GHÉP QWEN (bài 5886, `dyn-1.5_400_110000_qwen0.5`, 600 câu chấm)**: FINAL **0,2342** / DOCS_F2 0,2735 (P 0,1648, R 0,3818) / CHUNKS_F2 0,1949 (P 0,1899, R 0,2260). So bản chốt 5781 (0,2312 / 0,2698 / 0,1927; DOCS P 0,1635, R 0,3751; CHUNKS P 0,1842, R 0,2235): FINAL +0,0030, DOCS_F2 +0,0037, CHUNKS_F2 +0,0022; cả hai tầng cùng tăng, cả precision lẫn recall tăng. Cùng tham số cắt doc/cửa sổ nên chênh là do Qwen. Mức tăng sát ngưỡng nhiễu (~0,003) và nhỏ hơn dự đoán offline (+0,0365 AUC), nhưng đúng chiều ở cả hai tầng. Quyết định: dùng 5886 làm bản Public chốt mới (đồng thời là lượt Private số 1), 5781 giữ làm dự phòng.

**L. [18/10/2026] CORPUS MỚI TỪ BTC (`data/ViBioMIR_new/links_corpus_vi_en_zh.parquet`, clone `AIGuruTinix/ViBioMIR` commit 71be0e1; bản cũ `data/ViBioMIR` giữ nguyên, commit ca87a68 đã bị force-update trên remote)**: README mới ghi 1.220.598 liên kết = 740.598 tiếng Việt + 240.000 tiếng Anh (toàn `pubmed.ncbi.nlm.nih.gov`) + 240.000 tiếng Trung; `query.parquet` GIỐNG HỆT bản cũ (cmp byte). Đo: 1.220.598 id duy nhất (583 đến 7.466.161); **980.598 URL nằm trong corpus cũ với cùng id và cùng url (22,3% của 4.394.718, hay 27,8% theo số dòng), 240.000 là PubMed mới (id > 4.420.561)**. 94 domain. **Bằng chứng nhãn nằm trong corpus mới** (từ `details_5781/5684/5786`): 100% cửa sổ trúng (9.894 / 9.282 / 9.885) thuộc doc có trong corpus mới, trong khi 6,3% cửa sổ nộp (≈ 3.300) nằm ngoài corpus mới và 0 cửa sổ trong số đó trúng (kỳ vọng ≈ 620 nếu nhãn rải theo corpus cũ). Mô phỏng offline lọc bỏ doc/cửa sổ ngoài corpus mới trên bài 5781 (593 câu, mô phỏng tái hiện đúng 0,2698 / 0,1927 / 0,2312 trước lọc): DOCS_F2 0,2698 -> 0,2781, CHUNKS_F2 0,1927 -> 0,1961, FINAL 0,2312 -> 0,2371 (+0,006; TB doc 161,7 -> 149,2), CHƯA có điểm leaderboard. Giả định cần user xác nhận: bộ chấm Public/Private dùng corpus mới (suy từ bằng chứng trên, chưa có thông báo BTC trong tay). CHƯA đo: nhãn có chứa doc PubMed hay không (ta chưa có nội dung PubMed; 0 doc tiếng Anh trong chỉ mục); phần doc nhãn trong 980.598 mà ta chưa crawl được (banned_cooldown, lỗi mã hóa cnkang...).

**M. [18/10/2026] BÀI LỌC CORPUS MỚI (chưa có điểm leaderboard)**: `make_submission.py` có cờ `--new-corpus` (hàm `restrict_corpus`, lọc sau khi ghép Qwen: bỏ chunk của doc ngoài `ViBioMIR_new`, 58.700/720.000 chunk = 8,2%). Lệnh: `python make_submission.py --source rerank --qwen qwen_top100.jsonl 0.5 --new-corpus --dynamic -1.5 400 110000 200` -> `data/submission/submission_rerank_dyn-1.5_400_110000_qwen0.5_newcorpus.zip` (99,50 MB, sha256 `33b735387767ac5149c4f0930f41644176a4494c27bbc88541f4602cbd4e7647`, validator HỢP LỆ, 1.200 câu, 155,7 doc/câu, ngưỡng cửa sổ -0,36). Sát trần 100 MB (validator dùng 100*1024*1024 byte). Đối chiếu khi có điểm: 5886 = 0,2342 / 0,2735 / 0,1949; mô phỏng offline cho bản 5781 lọc: +0,006 FINAL.

**N. [18/10/2026] KẾT QUẢ BÀI LỌC CORPUS MỚI (bài 6039, `dyn-1.5_400_110000_qwen0.5_newcorpus`, 600 câu chấm)**: FINAL **0,2427** / DOCS_F2 0,2820 (P 0,1800, R 0,3821) / CHUNKS_F2 0,2033 (P 0,1986, R 0,2342). So 5886 (0,2342 / 0,2735 / 0,1949): FINAL +0,0085, DOCS_F2 +0,0085, CHUNKS_F2 +0,0084; vượt mô phỏng (+0,006) và vượt ngưỡng nhiễu: GIẢ THUYẾT "nhãn nằm trong corpus mới" ĐƯỢC XÁC NHẬN trên leaderboard. Bản chốt Public mới = 6039; 5886 và 5781 là dự phòng. **ĐỘ PHỦ CỦA CHỈ MỤC TRÊN CORPUS MỚI (đo 18/10; doc_id trong 222 shard chunk đối chiếu `links_corpus_vi_en_zh.parquet`)**: chỉ **654.811 / 1.220.598 = 53,6%** doc của corpus mới có trong chỉ mục. Phần thiếu 565.787 doc: PubMed 240.000 (chưa crawl, 0 chunk tiếng Anh); tiếng Việt ≈ 249.280 (phân loại domain gần đúng; coverage tiếng Việt 492.811/742.091 = 66,4%): `banned_cooldown` 219.088 (nhathuoclongchau.com.vn 79.598, suckhoecongdongonline.vn 59.282, baohaiphong.vn 16.286, baonghean.vn 15.941, baodanang.vn 14.500, giadinhonline.vn 12.405, pmc-ecm-healthblog 5.333, youmed.vn 4.287, laodong.vn 3.770, baocantho.com.vn 2.892, dantri.com.vn 1.761, thaythuocvietnam.vn 1.716, hanoimoi.vn 1.283), `needs_js_render` 28.710 (laodong.vn 27.512, baotayninh.vn 1.198), `failed` 1.468; tiếng Trung thiếu ≈ 76.507 trong 238.507 (cnkang.com 31.235 trang `done` hỏng mã hóa, banned: ask.39.net 19.065, 120ask 18.810, zysjonline 6.590). Corpus mới giữ 100% domain tiếng Việt của corpus cũ (kept = 1,0) nhưng chỉ 2,7-10,7% mỗi domain tiếng Trung lớn (zh được lấy mẫu 240.000). **Thử truy cập 18/10 (curl, UA trình duyệt, 1 URL mỗi domain)**: HTTP 200 với thaythuocvietnam, nhathuoclongchau, suckhoecongdongonline, baohaiphong, hanoimoi, baodanang, dantri, youmed, baotayninh, baonghean, baocantho, cnkang, ask.39.net; 403 với pmc-ecm-healthblog, zysjonline, giadinhonline; laodong.vn trả 177 byte (vỏ JS, cần render); 120ask timeout. Tức ≈ 199.000 trang tiếng Việt từng bị coi là bị chặn nay có vẻ truy cập được (chưa kiểm tra bằng crawl thật, mẫu 1 URL mỗi domain). **Mật độ trúng theo domain** (bài 5781, chỉ các doc đã nộp): hit rate cửa sổ 12-28% khá đều giữa các domain; số trúng trên 1.000 doc đã lập chỉ mục dao động 1,5-71 (medlatec 71, tamanhhospital 58, youmed 42, vinmec 41, tiemchunglongchau 38, suckhoedoisong 29, suckhoecongdongonline 3,4), nên KHÔNG thể giả định nhãn trải đều theo số doc. Ước lượng kỳ vọng thêm ≈ 200.000 trang tiếng Việt: từ +0,01 đến +0,05 FINAL (khoảng rộng, KHÔNG đo được trước khi crawl). Quyết định 09/10 "không retry banned_cooldown" cần user xác nhận lại vì tỷ trọng thay đổi (các domain này nay ≈ 18% corpus mới thay vì ~4% corpus cũ). Chưa làm gì ngoài đo (không crawl, không đổi chỉ mục).


---

### (Nhật ký lịch sử) cập nhật 02/10/2026, 09:45

### [02/10/2026] SỬA TRIỆT ĐỂ: thêm cột `bucket` để phá vỡ khối domain liên tục

**Nguyên nhân gốc thật sự của mọi lần giảm tốc độ trong 2 ngày qua** (không phải domain bị chặn như
nghi ngờ ban đầu mỗi lần): `links_corpus.parquet` có domain nằm thành **khối `id` liên tục lớn hơn cả
`FETCH_POOL_SIZE` (30.000)** — ví dụ `suckhoecongdongonline.vn` có hàng chục ngàn `id` liền kề. Khi
`fetch_pool()` lấy 30.000 dòng `pending` có `id` thấp nhất rồi mới xáo trộn, **toàn bộ lô có thể chỉ
chứa đúng 1 domain** — xáo trộn thứ tự không giúp được gì vì không có domain nào khác để trộn vào. Bị
giới hạn cứng bởi `PER_DOMAIN_CONCURRENCY=6` dù `GLOBAL_CONCURRENCY=150` cho phép nhiều hơn.

**Giải pháp đã triển khai**: thêm cột `bucket = id % 997` (gán 1 lần lúc seed, migrate 1 lần cho dữ
liệu cũ mất 405s), index `(status, bucket)`. `fetch_pool()` xoay vòng qua từng giá trị bucket thay vì
luôn lấy theo `id` tăng dần. Vì các `id` liên tiếp của CÙNG một domain rơi vào gần như đủ các giá trị
bucket khác nhau (tính chất số học của phép modulo trên dãy liên tiếp), mỗi lần lấy 1 bucket sẽ tự
nhiên có hàng chục domain khác nhau — đã xác minh thực tế: bucket mẫu có tới 10 domain khác nhau với
tỷ lệ đúng theo tỷ trọng tổng thể. Kết quả đo được ngay: tốc độ ổn định ~5-6/s ngay từ giây đầu (so
với bị kẹt ở 1,0/s trước đó), và circuit breaker đã **tự động phát hiện và cô lập `zysjonline.com`
(243.328 dòng) hoàn toàn tự động** trong lần test đầu tiên — đúng như thiết kế.

**Không cần sửa gì thêm ở tầng này nữa** trừ khi phát hiện bằng chứng thực nghiệm mới — đây là sửa
cấu trúc, không phải vá tạm.

> **Có watcher nền tự kiểm tra mỗi 10 phút, log tại `data/crawl_watch.log`, tự thoát và ghi dòng
> `CRAWL_HOAN_TAT` khi `pending=0 và retry=0`.** Nếu mở phiên làm việc mới và thấy watcher không còn
> chạy (process bash tương ứng đã mất, ví dụ do tắt máy), chỉ cần đọc `data/crawl_watch.log` để biết
> trạng thái gần nhất, không cần dựng lại watcher trừ khi crawl thật sự chưa xong.

- Tổng corpus: **4.394.718 URL** (`data/ViBioMIR/links_corpus.parquet`), chỉ Việt + Trung, KHÔNG
  có tiếng Anh (xem doc 12 mục kiểm tra domain).
- Đã xử lý: ~20.500 request, **~16.650 done, 0 failed, ~5.800 retry**.
- Tốc độ quan sát được: **~4.3 req/s** (ổn định) — nhưng đây là tốc độ đo trên phần `id` thấp, do
  chính corpus có cấu trúc đặc biệt: site Việt Nam chiếm phần lớn `id` thấp (584–~750.000), 4 domain
  Trung Quốc lớn nhất (63%+ corpus) có `id` bắt đầu từ ~750K–1,4M. **Tốc độ thực trên phần Trung Quốc
  CHƯA ĐƯỢC ĐO dưới tải sustained** — có thể nhanh hơn (ít domain hơn, mỗi request isolated test
  nhanh 0,4–7s) hoặc chậm hơn hiện tại, chưa có dữ liệu thật để khẳng định.
- **ETA [CẬP NHẬT 02/10/2026 09:50, SAU KHI SỬA LỖI BUCKET — đáng tin cậy hơn hẳn các ước tính trước]:
  ~8,4 ngày, dự kiến xong khoảng 10/10/2026.** Dựa trên tốc độ **ổn định thật sự 5,1-5,2/s** đo liên
  tục qua 1.900 request sau khi sửa lỗi phân bố domain (mục ngay trên) — khác các ước tính ETA trước
  đó (7,1 ngày, 11,8 ngày...) vốn dựa trên tốc độ KHÔNG ổn định do lỗi domain-clustering chưa được sửa
  gốc. Ước tính lần này đáng tin hơn vì tốc độ không còn phụ thuộc may rủi domain nào đang ở đầu hàng
  đợi — nhưng vẫn giữ nguyên lưu ý cũ: toàn bộ số liệu đo trên vùng `id` đã đi qua, phần tương lai của
  corpus (đặc biệt 63%+ domain Trung Quốc) có thể cho tốc độ khác do bucket mới giúp đều hơn nhưng
  chưa loại trừ khả năng xuất hiện domain lớn mới bị chặn (circuit breaker sẽ tự xử lý nếu có).
- Log: `data/crawl_log.txt` (append-only, cập nhật mỗi 100 request). Checkpoint: `data/crawl_cache.sqlite3`
  (resumable — dừng/mở lại session nào cũng tiếp tục đúng từ chỗ dừng qua `status IN ('pending','retry')`).

### [01/10/2026, 13:40] Phát hiện + xử lý: 2 domain bị chặn IP, không phải lọc User-Agent

`baodanang.vn` và `baohaiphong.vn` bị HTTP 403 liên tục (103→5.906 và 3.042 lần trong vài giờ). Test
trực tiếp `robots.txt` (file vô hại) bằng User-Agent Chrome thật — **vẫn 403**, server trả về
`openresty` với trang lỗi có padding chống "Chrome friendly error page" ⇒ đây là **chặn ở tầng WAF
theo IP**, không phải lọc theo User-Agent (đổi UA giả trình duyệt sẽ KHÔNG giải quyết được — đã xác
minh bằng thực nghiệm, không suy đoán). Nghiên cứu xác nhận: sau 2026, rotate UA/IP một mình không
còn đủ qua anti-bot hiện đại; mức an toàn thường dùng là 1-2 req/s có delay ngẫu nhiên 2-5s, site
khắt khe hơn cần 1 request/10-15s.

**Đã xử lý**: chuyển 30.786 dòng của 2 domain này sang status `banned_cooldown` (không nằm trong
`WHERE status IN ('pending','retry')` mà `url_crawler.py` dùng) để crawler chính không tiếp tục lãng
phí worker retry vô vọng trong lúc đang bị ban — **retry liên tục trong lúc bị ban chỉ kéo dài thời
gian ban, không giúp gì**. Hiệu quả đo được ngay: tốc độ tổng từ **4,3/s → 7,1/s (+65%)**.

**Kế hoạch sau cooldown thật (không phải bây giờ)**: chạy một script retry riêng, CHỈ cho 2 domain
này, với concurrency=1 và delay 10-15s/request (không phải `PER_DOMAIN_CONCURRENCY=6` như mặc định),
sau khi đã nghỉ vài giờ thật (ban IP thường cần thời gian thực để hết hạn, không phải thuật toán nào
"vượt qua" ngay được). Impact nếu mất hoàn toàn 2 domain này: ~30.786/4.394.718 ≈ 0,7% corpus — nhỏ,
không chặn tiến độ Giai đoạn 1.

---

### [02/10/2026, 07:55] Phát hiện lặp lại lần 3: thêm 2 domain bị chặn qua đêm

`nhathuoclongchau.com.vn` (79.598 URL — gần như toàn bộ domain, lỗi `http_429`) và
`pmc-ecm-healthblog.beta.pharmacity.io` (5.333 URL, lỗi `http_403`) bị chặn trong lúc không giám
sát. Xác nhận bằng request đơn lẻ thật lúc 07:55 — `nhathuoclongchau.com.vn` vẫn trả `429` ngay cả
khi chỉ gửi 1 request duy nhất, không phải do tải nặng tại thời điểm kiểm tra. Đã sideline 84.931
dòng sang `banned_cooldown`.

**Nhận định sau 3 lần phát hiện tương tự (2 domain lần 1, 3 domain lần 2, 2 domain lần 3 — tổng 7
domain, 134.163 dòng `banned_cooldown`):** đây là **mẫu hình lặp lại có hệ thống**, không phải sự cố
đơn lẻ — một số domain trong 97 domain của corpus có WAF nhạy với tải từ 1 IP, và crawler hiện tại
phát hiện bằng cách phản ứng (quan sát retry dồn ứ rồi mới xử lý) thay vì chủ động. **Cải tiến nên
cân nhắc ở lần sửa `url_crawler.py` tiếp theo** (chưa làm ngay vì phải dừng crawler đang chạy):
circuit-breaker tự động — nếu 1 domain có tỷ lệ lỗi 403/429 vượt ngưỡng (ví dụ >50% trong 50 request
gần nhất), tự động tạm dừng domain đó một khoảng thời gian thay vì đợi người phát hiện thủ công.

---

### [02/10/2026, chiều] Kiểm tra sức khỏe các domain Trung Quốc lớn — circuit breaker đã tự động xử lý 2 domain mới

4 domain Trung Quốc lớn nhất chiếm **~60,7% tổng corpus**: `www.cnkang.com` (963.438 dòng, 21,9%),
`www.120ask.com` (918.479, 20,9%), `www.familydoctor.com.cn` (447.453, 10,2%), `ask.39.net`
(337.375, 7,7%). Tổng cộng 12 domain Trung Quốc xác định được (gồm `zysjonline.com`,
`www.a-hospital.com`, `zhongyibaodian.net`, `www.zydcd.com`, `www.wujue.com`, `www.youlai.cn`,
`baby.39.net`, `bingli.iiyi.com`, `article.iiyi.com`) chiếm **~78,6% tổng corpus (3.456.882 dòng)**
— tỷ trọng Trung Quốc thực tế cao hơn con số "63%+" ghi trước đó (số đó chỉ tính riêng 4 domain lớn
nhất, không phải toàn bộ Trung Quốc).

**Đo trực tiếp domain lớn nhất (`cnkang.com`, 963.438 dòng) bằng truy vấn range theo `id`** (đo
được 6,2s, tránh được truy vấn domain-index gây tranh chấp disk I/O nặng với crawler đang chạy —
2 lần thử domain-equality GROUP BY trước đó đều timeout >60-120s do cần random lookup table cho
hàng trăm nghìn dòng cùng lúc crawler đang viết liên tục): **51.984 done, 911.220 pending, 232
retry, chỉ 2 failed** — tỷ lệ lỗi ~0,004%, KHÔNG bị circuit breaker can thiệp, đang crawl bình
thường. Không có bằng chứng domain lớn nhất gặp vấn đề.

**Nhưng CÓ 2 domain Trung Quốc bị circuit breaker tự động sideline trong lần chạy hiện tại** (xác
nhận qua grep `data/crawl_log.txt`, không cần truy vấn DB): `bingli.iiyi.com` (24.970 dòng) và
`article.iiyi.com` (5.623 dòng) — cả hai thuộc hệ thống iiyi.com (diễn đàn y khoa Trung Quốc).
Cộng thêm `suckhoecongdongonline.vn` (59.284 dòng, Việt Nam) cũng bị sideline cùng lần chạy này.
Đây là **đúng thiết kế circuit breaker đang hoạt động** (xem mục ngay trên về bucket fix), không
phải lỗi crawl.

Tổng domain Trung Quốc đã xác nhận bị `banned_cooldown`: `zysjonline.com` (243.347) +
`bingli.iiyi.com` (24.970) + `article.iiyi.com` (5.623) = **273.940 dòng ≈ 6,2% tổng corpus**.
Tổng `banned_cooldown` toàn hệ thống hiện tại: **486.967 dòng** — lớn hơn tổng các domain đã liệt
kê cụ thể trong tài liệu này cho tới nay (134.163 ghi lúc 02/10 07:55 + 89.877 của 3 domain mới =
224.040), còn **262.927 dòng CHƯA xác định rõ thuộc domain nào** — khả năng cao là log của các lần
circuit breaker trước đã bị mất do `crawl_log.txt` không giữ lịch sử xuyên các lần restart khác
nhau trong ngày (phát hiện mới: file log KHÔNG phải append-only xuyên mọi lần restart như ghi nhận
trước đây — mỗi lần restart có thể tạo log mới, cần sửa lại giả định này). **CHƯA xác định được
toàn bộ — ghi rõ CHƯA ĐO thay vì suy đoán**, sẽ đối soát đầy đủ bằng domain-count index-only (nhanh,
đã dùng ở trên) khi có cơ hội ít tranh chấp I/O hơn, không chạy thêm domain-equality GROUP BY nặng
khi crawler đang hoạt động để tránh làm chậm tiến độ crawl thật.

---

### [05/10/2026, 08:44] Phát hiện mới: `ask.39.net` (1 trong 4 domain TQ lớn nhất) bị circuit breaker ban

Sau khi resume crawler từ sự cố cúp điện 6h30 sáng 05/10 (resume sạch, `seeded 0 new pending rows`,
không mất dữ liệu nhờ WAL — xem lịch sử dừng/resume ở cuối mục này), circuit breaker tự động phát
hiện và sideline thêm 3 domain mới (xác nhận qua grep `crawl_log.txt`): **`ask.39.net`** (337.375
dòng, 7,7% tổng corpus — một trong 4 domain Trung Quốc lớn nhất, trước đó ghi nhận "không bị can
thiệp" ở mục ngay trên — nay đã đổi, sideline 197.862 dòng còn lại), `youmed.vn` (4.294),
`thaythuocvietnam.vn` (1.717). Tổng `banned_cooldown` toàn hệ thống nhảy từ 487.001 → **690.864**
(+203.863). **CHƯA xác định nguyên nhân cụ thể** (có thể do tải tích lũy từ nhiều ngày trước, hoặc
site siết chặt WAF gần đây) — cần theo dõi thêm, không suy đoán. Đây vẫn là circuit breaker hoạt
động đúng thiết kế (tự phát hiện, tự cô lập), không phải lỗi crawl.

**Lịch sử dừng/resume do mất điện theo kế hoạch**: dừng an toàn lúc 06:21 (39,69% done, taskkill
PID 5544), resume lúc 07:51 sau khi có điện lại (`seeded 0 new pending rows` — xác nhận checkpoint
SQLite WAL hoàn toàn không mất dữ liệu qua lần cúp điện này). Dừng lần 2 lúc 08:44 theo yêu cầu
người dùng để reset máy (taskkill PID 20848, done=1.747.326=39,76% tại thời điểm dừng).

---

### [05/10/2026, 09:51-10:08] Sự cố "crawler bị treo" + mất điện lần 2 — xác định nguyên nhân gốc: file DB 9,25GB trên ổ HDD, không phải lỗi code

**Hiện tượng**: sau khi resume crawler lúc 08:49, log dừng ở `processed=67` rất lâu, CPU crawler gần
0% (đo 2 lần cách nhau 5s, chỉ tăng 0,09s CPU — xác nhận THỰC SỰ không hoạt động, không phải chỉ
chậm), mọi truy vấn SQLite từ bên ngoài (kể cả sau khi `taskkill` crawler) đều timeout 30-40s.

**Nguyên nhân gốc (đo được, không suy đoán)**: `crawl_cache.sqlite3-wal` phình tới **73,97MB** (do
2 lần dừng/resume liên tiếp qua cúp điện + reset máy chưa kịp checkpoint đầy đủ). Mở connection mới
buộc SQLite phải merge toàn bộ WAL vào file chính **9,25GB** — trên ổ cứng xác nhận là **HDD thường
(ST1000VX013-3CV10C), không phải SSD** (xem câu hỏi "ổ D là HDD mà nhỉ" — cả D: và E: cùng nằm trên
1 ổ HDD vật lý duy nhất, SSD duy nhất là C: gần đầy). Đo trực tiếp: merge WAL 73,97MB mất **92 giây**.
Sau khi xoá sạch, test lại cho thấy **merge chỉ 6,6MB WAL vào đúng cùng file 9,25GB này vẫn mất
60+ giây** — xác nhận bản chất vấn đề là **kích thước file 9,25GB trên HDD vốn đã chậm cho mọi lần
mở connection đầu tiên** (cold-open), không riêng gì do WAL lớn. Baseline đo được sau khi WAL đã
sạch (0 byte): **mở + query status mất 17,5s** — đây là mức "bình thường" phải chấp nhận trên HDD
này với file cỡ này, KHÔNG phải dấu hiệu treo.

**Biện pháp phòng ngừa đã áp dụng (03/10-05/10, lặp lại mỗi lần dừng crawler từ nay)**:
1. Sau khi `taskkill` dừng crawler, **luôn chủ động chạy `PRAGMA wal_checkpoint(TRUNCATE)`** một lần
   trước khi coi là "đã dừng xong" — giữ WAL ở 0 byte để lần resume sau không phải merge backlog lớn.
2. Khi chẩn đoán "crawler có vẻ treo": **luôn tăng timeout lên tối thiểu 60-120s** trước khi kết
   luận treo thật — baseline cold-open trên HDD này là 15-90s tùy kích thước WAL tại thời điểm đó,
   KHÔNG dùng timeout 20-30s như các lần đo nhanh trước đây (sẽ luôn báo sai là "treo"/"timeout").
3. Đo CPU usage thực tế (2 lần Get-Process cách nhau vài giây) để phân biệt "treo thật" (CPU ~0%)
   với "đang xử lý I/O chậm" (CPU cũng có thể gần 0% vì I/O-bound — cần kết hợp với kiểm tra WAL size
   và thời gian chờ hợp lý trước khi taskkill, tránh giết oan một crawler chỉ đang chậm).
4. **Cân nhắc khi sửa `url_crawler.py` ở lần tiếp theo** (chưa làm ngay, crawler đang chạy ổn):
   thêm `conn.execute('PRAGMA wal_autocheckpoint = 1000')` (giảm từ default 1000 pages xuống nhỏ hơn
   nếu cần) hoặc checkpoint định kỳ trong `save_results()` để WAL không bao giờ phình lớn giữa các
   lần chạy — giảm rủi ro lặp lại sự cố này ở mỗi lần mất điện/reset tiếp theo (tần suất cao trong
   môi trường hiện tại: đã xảy ra 2 lần cúp điện liên tiếp trong cùng 1 buổi sáng 05/10).

**Lịch sử lần cúp điện thứ 2 (05/10, ~10:00)**: phát hiện ngay khi user báo — kiểm tra thấy crawler
đã tự dừng (không còn process), WAL lần này chỉ 6,6MB (nhỏ hơn nhiều vì đã chủ động checkpoint ở sự
cố lần 1 bên trên). Đã chủ động chạy `PRAGMA wal_checkpoint(TRUNCATE)` dọn sạch trước khi user yêu
cầu khởi động lại — xác nhận baseline cold-open giảm xuống 17,5s, done=1.748.220=39,78% (không mất
dữ liệu qua lần mất điện này).

---

### [06/10/2026, 17:10-17:58] Crawler tự dừng lặng lẽ, KHÔNG rõ nguyên nhân — khác các sự cố trước

Phát hiện lúc kiểm tra định kỳ 17:58: crawler không còn process (đã dừng từ ~17:10, cách ~48 phút),
**không có traceback/lỗi nào trong `crawl_log.txt`** — dòng cuối vẫn là 1 dòng progress bình thường
rồi im bặt, không giống 2 sự cố trước (không phải cúp điện do user báo, không phải WAL/HDD treo —
DB mở lại chỉ mất 0,6s, hoàn toàn khỏe). Dữ liệu không mất (done=2.369.345 tại thời điểm dừng).
**CHƯA xác định được nguyên nhân cụ thể** (có thể: terminal/shell chạy `nohup` bị đóng do thứ gì đó
ngoài phiên làm việc, Windows Update/sleep, hoặc giới hạn tài nguyên hệ thống) — ghi rõ CHƯA ĐO,
không suy đoán. Đã restart bình thường (`seeded 0 new pending rows`, resume đúng từ checkpoint).
**Theo dõi tiếp**: nếu lặp lại nhiều lần không do user tác động, cần điều tra sâu hơn (ví dụ thêm
log exception handler toàn cục trong `url_crawler.py`, hoặc kiểm tra Windows Event Viewer) ở lần
sửa code tiếp theo.

---

### [06/10/2026, 20:06-21:03] ĐÃ XÁC ĐỊNH NGUYÊN NHÂN GỐC: `sideline_domain()` chặn event loop ~50 phút trên HDD (KHÔNG phải memory leak, KHÔNG phải crash)

**Đính chính nhận định trước đó (20:02, "nghi memory leak") — đã bị bác bỏ bằng đo đạc.** Hiện tượng
"crawler chết/tự dừng" ở 17:10 và 20:06 thực chất là **crawler bị CHẶN** (process vẫn sống, bộ nhớ
chỉ trông bất thường do tôi lúc đó quan sát nhầm các process pytest/bench của project khác trên máy).

**Bằng chứng đo được (20:57-21:03)**:
- Log `crawl_log.txt` ngừng ghi từ 20:06:56 (mtime), CPU crawler ~0 (0,06s/5s), nhưng I/O vẫn chạy
  (ghi ~0,7MB/s) và `-wal` tăng đều (55,6→56,4MB trong 1 phút), hàng chục socket `CLOSE_WAIT`.
- Domain vừa vượt ngưỡng breaker lúc đó: `qihuangzhishu.com` (23.637 dòng, 9 `ReadTimeout` lúc
  20:06:39). Breaker gọi `sideline_domain()` = một `UPDATE ... WHERE domain=? AND status IN
  ('pending','retry')` **đồng bộ chạy thẳng trên event loop** (`url_crawler.py` ~dòng 295-306) →
  mọi worker đứng im chờ.
- Chạy đúng câu UPDATE đó riêng (crawler đã dừng, `PRAGMA cache_size=-400000`): **9.083 dòng chỉ
  18,4s**. Trong crawler (cache mặc định ~2MB, cạnh tranh I/O trên HDD) nó đã chạy >50 phút chưa
  xong → chênh lệch ~160 lần.
- Lưu ý: breaker đếm **mọi kết quả khác `done`** (kể cả `empty_extraction`, retry) là thất bại.

**Đã sửa (1 dòng, `connect_db()`)**: thêm `PRAGMA cache_size=-400000` (400MB page cache) — đúng cấu
hình đã đo cho ra 18,4s. Sau sửa, bộ nhớ crawler tăng ~+400MB so với trước là **bình thường/có chủ ý**.
**Sự cố 17:10 (domain nào, khi nào) CHƯA ĐO được trực tiếp** nhưng triệu chứng giống hệt (log im,
không traceback) nên khả năng cao cùng cơ chế; ghi rõ là suy luận, chưa kiểm chứng.

**Còn rủi ro**: `sideline_domain()` vẫn đồng bộ — domain rất lớn trip breaker (ví dụ `cnkang.com`
~900k dòng) vẫn có thể chặn crawler lâu hơn dù đã có cache lớn. Nếu thấy log im >5 phút: kiểm tra
mtime log + CPU ~0 + `-wal` tăng ⇒ đó là sideline, ĐỪNG kill ngay; chờ hoặc dừng rồi sideline thủ
công bằng script như trên (BEGIN/UPDATE/COMMIT với cache lớn). Hướng sửa gọn nếu lặp lại: chạy
`sideline_domain` qua `loop.run_in_executor` hoặc chia batch theo `id` để không chặn event loop.

---

### [08/10/2026, 08:24-17:30] `www.120ask.com` không kết nối được -> crawler bò ~1/s, đã sideline 175.540 dòng

**Hiện tượng**: từ 08:24 các request tới `www.120ask.com` (IP `219.239.89.30-32`) kẹt ở `SynSent`,
`curl` trực tiếp tới domain và tới IP đều timeout 8s (đo 12 lần từ 08:26 đến 13:22), trong khi
`cnkang.com`/`familydoctor.com.cn`/`google.com`/ping 8.8.8.8 bình thường. Crawler không treo
(log vẫn ghi, `-wal` đứng yên, RAM bình thường) nhưng tụt từ 5,7/s xuống ~1 done/s trong ~5 giờ
(done chỉ +~1.000-2.000 mỗi 30 phút thay vì ~22.000/giờ). **CHƯA xác định 120ask sập hay chặn IP
máy này** (không có cách phân biệt từ phía ta).

**Xử lý (user đồng ý)**: dừng crawler an toàn, chuyển pending/retry của `www.120ask.com` sang
`banned_cooldown` bằng script riêng (BEGIN/UPDATE/COMMIT, `cache_size=-400000`): **175.540 dòng,
mất 4.307s (~72 phút)** trên HDD. Phần lớn 120ask (918.479 dòng) đã `done` từ trước nên số dòng
sideline thấp hơn nhiều so với ước tính ban đầu 600k. Lần chạy script đầu bị hệ thống dừng giữa chừng
vì máy thiếu RAM (chưa kịp ghi gì, DB nguyên vẹn); lần 2 bỏ bước đếm `GROUP BY domain` (chậm trên
HDD) nên chạy được. Tổng `banned_cooldown` sau xử lý: **875.487**.

**Sau restart (khởi động nguội, ~16:30)**: tốc độ hồi phục dần 1,5/s (16:51) -> 4,1/s (17:14) ->
4,6/s (17:36) -> ~4,9/s (18:08), nghi do cache HDD nguội (chưa kiểm chứng trực tiếp). Trạng thái 18:08:
done=3.082.128 (70,13%), pending=405.681, retry=174, failed=2.538, needs_js_render=28.710.

**Việc còn lại**: thử lại 120ask khi nó hồi phục (concurrency 1, delay 10-15s, như kế hoạch cho các
domain `banned_cooldown`); nếu vẫn không vào được thì ghi số dòng 120ask bị loại + lý do vào báo cáo
đóng Giai đoạn 1 (quy tắc 6a).

---

### Quan sát chất lượng dữ liệu đã crawl (nguyên tắc LIMA — chất lượng quan trọng hơn số lượng)

Lấy mẫu ngẫu nhiên nội dung đã crawl: `trafilatura` trích xuất sạch (có frontmatter title/author/date/
description), **không có extraction rỗng** trong mẫu kiểm tra (min 301 ký tự, median 3.220, chỉ 3/16.126
dòng dưới 500 ký tự), **không có title null**. Về mặt kỹ thuật crawl, chất lượng TỐT.

Nhưng có một quan sát đáng lưu ý về **bản chất nội dung**: nhiều trang từ các báo điện tử địa phương
(`baoangiang.com.vn`, `baocantho.com.vn`...) là **tin tức nhân văn/sự kiện y tế** (ví dụ "giành giật sự
sống cho bé trai bị bỏng") hơn là **tài liệu tham khảo y khoa** (phác đồ, tiêu chuẩn chẩn đoán, thông
tin thuốc). Điều này không phải lỗi crawl — đây là đặc điểm THẬT của một phần corpus. Hệ quả: không
phải domain nào cũng có mật độ thông tin y khoa cao như nhau; cần lưu ý khi tới Giai đoạn 2 (EDA) để
đánh giá đúng tỷ lệ nội dung "tham khảo lâm sàng" vs "tin tức sức khỏe" theo từng domain, chứ không
giả định đồng nhất. Chưa cần hành động ở Giai đoạn 1 (crawl vẫn phải lấy đủ vì BTC coi toàn bộ
`links_corpus.parquet` là không gian nhãn hợp lệ — xem doc 01 mục 6).

---

## 4. Ràng buộc tuyệt đối (vi phạm là hỏng bài thi — xem [01-THONG-TIN-CUOC-THI.md](phan-tich/01-THONG-TIN-CUOC-THI.md))

- Model phải **open-weight, ≤15B tham số/model riêng lẻ, phát hành trước 01/08/2026**. Không cần
  license cho phép thương mại — chỉ cần công khai, không phải LLM đóng qua API thương mại.
- `relevant_chunks` trong file nộp phải là **`chunk_text` thật** (nội dung text), không phải `chunk_id`
  tham chiếu — thể lệ cũ (cấm nộp văn bản thô) đã hết hiệu lực từ 26/09/2026.
- `doc_id` phải là **số nguyên trùng với `id` trong `links_corpus.parquet`** — tài liệu ngoài danh
  sách này không được tính là nhãn dương, dù nội dung có liên quan thật.
- File zip nộp lên: **DUY NHẤT 1 file `.json` ở gốc zip, không trong thư mục con.** BTC **KHÔNG quy
  định tên file cụ thể** trong văn bản thể lệ. **[CHỐT 01/10/2026] Quy ước tên cố định của repo này
  để nhất quán giữa mọi lần nộp: `submission.json` đóng gói thành `submission.zip`** — đây là lựa
  chọn riêng của dự án (được phép vì không vi phạm cấu trúc bắt buộc), không phải tên BTC yêu cầu.
  Trước khi nộp thật (Giai đoạn 7), vẫn phải tự kiểm tra trang upload thật trên leaderboard phòng
  trường hợp form web có ràng buộc riêng không ghi trong văn bản thể lệ.
- **[CHỐT 06/10/2026] `submission.zip` tối đa 100MB** — ràng buộc cứng cần kiểm tra trước khi nộp ở
  Giai đoạn 7 (xem [01-THONG-TIN-CUOC-THI.md](phan-tich/01-THONG-TIN-CUOC-THI.md)
  mục "Các lưu ý kỹ thuật bắt buộc về bài nộp" điểm 5). Ảnh hưởng tới quyết định $K_{max}=5$/$K_{doc}=3$
  đã chọn — cần verify thực nghiệm ở Giai đoạn 7 rằng tổng dung lượng JSON với số lượng câu hỏi thật
  + độ dài chunk trung bình không vượt mốc này, không suy đoán.
- Deadline: Vòng 1 kết thúc 31/10/2026, Vòng 2 (Mentoring & tối ưu, gồm Private Test hạn 04/11) tới
  10/11/2026, **Demo Day/Chung kết 11/11/2026**.
- Hạn mức nộp bài: Public tối đa 10 bài/ngày (01-31/10 = **310 lượt tối đa cả Vòng 1**, không cần
  dùng hết — chỉ nộp khi có thay đổi đáng đo); Private tối đa **5 bài tổng cộng** cho cả giai đoạn.
- **[XÁC NHẬN KICK-OFF 01/10/2026] Quy tắc chống gian lận**: cấm hardcode đáp án, cấm sao chép code
  đội khác, cấm **"tạo chunk thay thế ID"** (bịa `chunk_text` không trích thật từ tài liệu gốc để giả
  làm chunk hợp lệ — đây là rủi ro thật nếu `medical_chunker.py` sau này có lỗi làm hỏng text gốc),
  cấm dùng dữ liệu ngoài phạm vi corpus/URL chính thức BTC cung cấp.
- **[XÁC NHẬN KICK-OFF 01/10/2026]** Không giới hạn số lượng `relevant_docs`/`relevant_chunks` mỗi
  câu hỏi (BTC chỉ lưu ý kích thước file & thời gian xử lý) — các giới hạn $K_{max}=5$/$K_{doc}=3$
  trong thiết kế hệ thống này là lựa chọn chiến lược riêng để tối ưu Precision, không phải luật BTC.
  Relevant Chunk phải thuộc đúng Document tương ứng (trích thật từ 1 tài liệu cụ thể, nên đồng bộ với
  `relevant_docs` cùng câu) — xem [01-THONG-TIN-CUOC-THI.md](phan-tich/01-THONG-TIN-CUOC-THI.md) mục 6.

---

## 5. Chạy như thế nào

```bash
# Luôn dùng venv của project, không dùng Python global
E:/r2ai_stage3/.venv/Scripts/python.exe

# Crawl (resumable — chạy lại là tiếp tục, không crawl lại cái đã done)
cd phan-tich/stage3
PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf-8 ../../.venv/Scripts/python.exe -u url_crawler.py

# Kiểm tra tiến độ crawl bất kỳ lúc nào (không cần dừng crawl)
../../.venv/Scripts/python.exe -c "
import sqlite3
conn = sqlite3.connect('../../data/crawl_cache.sqlite3')
print(dict(conn.execute('SELECT status, COUNT(*) FROM pages GROUP BY status').fetchall()))
"
```

---

## 6. Skills khả dụng theo từng giai đoạn (nghiên cứu 03/10/2026, dùng `npx skills find`)

Đã tra cứu thực tế qua skill `find-skills` (`npx skills find <query>`). **[CẬP NHẬT 03/10/2026]
Đã cài sẵn cục bộ vào project** (không phải global) tại `.agents/skills/` (symlink vào
`.claude/skills/`) theo yêu cầu người dùng chuẩn bị trước — nhưng **vẫn giữ nguyên luật phase-gate:
chỉ ĐỌC/DÙNG đúng skill của giai đoạn đang làm, không đọc trước nội dung skill của giai đoạn tương
lai chỉ vì đã có sẵn file**. Danh sách đã cài: `async-python-patterns`, `python-resilience`,
`embedding-strategies`, `hybrid-search-implementation`, `vector-index-tuning`,
`similarity-search-patterns`, `python-testing-patterns`, `python-error-handling`. Xác minh:
`npx skills list` (project scope) liệt kê đủ 8/8, không có skill nào global bị đụng tới.

Kết quả tra cứu **grounded**, không suy đoán:

- **Không có skill nào chuyên biệt cho y khoa đa ngôn ngữ Việt-Trung** (đã thử các truy vấn "medical
  NLP clinical text", "multilingual NLP Vietnamese Chinese" — chỉ ra kết quả nhiễu không liên quan).
  Không có gì để bổ sung ở khía cạnh này — dựa hoàn toàn vào nghiên cứu nội bộ (doc 13, mock dev set
  từ ViHealthQA/webMedQA/cMedQA2).
- **Giai đoạn 1 (Crawl, đang chạy)**: `async-python-patterns` và `python-resilience` khớp đúng kiến
  trúc đã tự xây (asyncio Queue+worker, circuit breaker, retry/backoff) — nhưng **KHÔNG áp dụng
  giờ** dù đã có sẵn file: `url_crawler.py` đã chạy ổn định, đã verify thực nghiệm (bucket fix,
  circuit breaker tự động hoạt động đúng — xem mục 3), không có lý do kỹ thuật cụ thể để đổi. Chỉ
  cân nhắc nếu sau này phát hiện vấn đề mới mà 2 skill này có giải pháp đã kiểm chứng rộng rãi
  (python-resilience: 10K+ installs).
- **Giai đoạn 3 (Chunking) — CHƯA BẮT ĐẦU**: `embedding-strategies` ("Select and optimize embedding
  models... chunking strategies... for specific domains") khớp trực tiếp việc cần làm (chunk
  300-500 token, Contextual Retrieval theo doc 11 mục 3). Đã cài sẵn — chỉ Đọc/áp dụng khi Giai
  đoạn 2 (EDA) xong.
- **Giai đoạn 4 (Index Sparse+Dense) — CHƯA BẮT ĐẦU**: 3 skill khớp đúng kiến trúc đã chốt (Tantivy
  BM25 + BGE-M3 dense + RRF + Binary Quantization, doc 10-11):
  - `hybrid-search-implementation` — "Combine vector and keyword search... when neither approach
    alone provides sufficient recall."
  - `vector-index-tuning` — "tuning HNSW parameters, selecting quantization strategies" — trực
    tiếp liên quan Binary Quantization đã chọn cho RAM budget 16GB.
  - `similarity-search-patterns` — pattern truy vấn vector hiệu quả.
  - Đã cài sẵn — chỉ Đọc/áp dụng khi tới Giai đoạn 4.
- **Giai đoạn 7 (`validate_submission.py`) — CHƯA BẮT ĐẦU**: `python-testing-patterns` và
  `python-error-handling` phù hợp cho việc validate format file nộp tại ranh giới hệ thống
  (boundary validation theo mục 0 nguyên tắc 3 — "chỉ validate ở ranh giới"). Đã cài sẵn.

**Nguyên tắc áp dụng**: dù đã cài sẵn cả 8 skill, KHÔNG đọc/áp dụng skill nào cho tới khi đúng giai
đoạn tương ứng bắt đầu (đúng luật mục 1 điểm 1 — không code/thiết kế cho giai đoạn N+1 khi giai
đoạn N chưa xong; "đã cài sẵn file" không phải lý do để bắt đầu sớm). Khi tới giai đoạn đó, đối
chiếu nội dung skill với kiến trúc đã chốt trong doc 10-11 — chỉ dùng phần khớp, không để skill áp
đặt abstraction/pattern khác với quyết định đã chốt (ví dụ: không đổi sang LangChain dù
`langchain-ai/langchain-skills@langchain-rag` có 16,2K installs — kiến trúc hiện tại cố ý tránh
framework nặng để chạy gọn trong 6GB VRAM, xem doc 10).

---

## 7. Kỷ luật đo (sẽ bổ sung khi có thực nghiệm thật)

*Chưa có mục nào — dự án mới ở Giai đoạn 1. Khi chạy `eval_f2.py` lần đầu trên mock dev set (Giai
đoạn 5-6), ghi lại đây: cách chia tập đo, ngưỡng nhận/loại một thay đổi, và giới hạn độ tin cậy của
proxy gold set (tương tự cách E:\r2ai_guru\AGENTS.md đã làm cho
Stage 2) — không fabricate số liệu chưa đo được.*

---

## 8. Ngõ cụt — đã đo, đừng thử lại

*Chưa có mục nào. Mỗi khi một hướng kỹ thuật bị thực nghiệm bác bỏ (không phải suy đoán), ghi vào
đây kèm số liệu đo được, theo đúng format bảng ở E:\r2ai_guru\AGENTS.md
mục 6.*

**O. [18/10/2026] MỞ RỘNG ĐỘ PHỦ CORPUS MỚI - TRẠNG THÁI ĐANG CHẠY (user duyệt 1a + PubMed sau đó; không push repo công khai cho tới khi có kết quả)**: (1) **Crawl lại tiếng Việt** `phan-tich/stage3/recrawl_vi.py --per-domain 4 --domains suckhoecongdongonline.vn baohaiphong.vn baonghean.vn baodanang.vn youmed.vn baocantho.com.vn dantri.com.vn thaythuocvietnam.vn hanoimoi.vn` (log `data/recrawl_vi.log`, ~10 trang/giây, tỷ lệ thành công gần 100%; đặt lại 198.905 dòng pending rồi sideline 79.598 nhathuoclongchau). Phát hiện: UA trung thực `R2AIStage3Crawler` bị 403 ở nhathuoclongchau, baohaiphong, hanoimoi, baodanang, baonghean, youmed; UA trình duyệt thường qua được (đã đọc robots.txt: chỉ cấm trang tìm kiếm/giỏ hàng, không cấm bài viết); riêng nhathuoclongchau (79.598 trang) vẫn 403 với httpx dù UA trình duyệt (chặn theo dấu vân TLS) nên KHÔNG crawl, không vượt WAF. Bỏ qua: nhathuoclongchau, giadinhonline (403), pmc-ecm-healthblog (403), laodong (cần render JS), zysjonline (403), 120ask (timeout). (2) **PubMed**: `fetch_pubmed.py` lấy tiêu đề + tóm tắt 239.699/240.000 PMID qua NCBI efetch (301 không còn bản ghi; 239.574 có tóm tắt, TB 1.328 ký tự; 3.351 giây; `data/pubmed_cache.sqlite3`); `chunk_extra.py pubmed` -> 12 shard `data/chunks/shard_91000000..91220000` (≈ 316.000 chunk, language `en`); embed BGE-M3 đang chạy (`data/embed_extra1.log`, 40 chunk/s). PMID lấy mẫu ngẫu nhiên toàn PubMed (nhiều bài 1976), nên nhiều khả năng là nhiễu; CHƯA biết nhãn có PubMed không. (3) **Các bước còn lại** (shard mới đặt tên lớn hơn mọi shard cũ nên tự nối vào chỉ mục): chờ crawl xong -> `python chunk_extra.py vi` (-> shard_90000000) -> `python embed_corpus.py` -> `python tantivy_indexer.py --index-dir ../../data/tantivy_index` (chỉ lập shard mới) -> `python dense_index.py build` (dựng lại ~3 phút) -> truy hồi lại 1.200 câu (cache mới, không ghi đè `candidates_rrf*`) -> `rerank_deep.py` với START/END mới (tự bỏ qua chunk đã có điểm) -> chấm Qwen cho doc mới vào top 100 -> `make_submission.py ... --new-corpus`.

**O (cập nhật 18/10 23:45)**: crawl lại xong (`pending=0`; tổng `done` 3.487.922 -> 3.605.275, +117.353 trang; `failed` 1.277 -> 1.514); WAL đã checkpoint. `chunk_extra.py vi` -> `shard_90000000` = 330.955 chunk từ 117.353 trang (bỏ 31.258 trang lỗi mã hóa/không thân bài, chủ yếu 31.235 trang `cnkang.com`). PubMed: 12 shard embed xong (314.284 chunk, 30-40 chunk/s). BM25: `tantivy_indexer.py` thêm 13 shard, tổng 645.239 chunk mới (29-31 giây mỗi shard). **Lỗi vận hành đã gặp**: lần embed đầu của `shard_90000000` đứng im ~70 phút từ 22:21 vì guard RAM (`MIN_FREE_GB = 3.5` trong khi máy chỉ còn ~2,8 GB trống do tiến trình embed chiếm 4,3 GB cho shard 331k chunk); guard chỉ in một dòng "TAM DUNG" mỗi lần chờ nên log trông như chưa có gì xảy ra. Đã sửa: `embed_corpus.py` đọc ngưỡng từ biến môi trường `R2AI_MIN_FREE_GB`; chạy lại với `R2AI_MIN_FREE_GB=1.5` (mất ~20 phút tiến độ). Việc kế tiếp sau khi embed xong: `dense_index.py build`; `make_submission.py --source rrf600v2` (cache `candidates_rrf600v2_d600.jsonl`); `rerank_deep.py 0 601 --candidates candidates_rrf600v2_d600.jsonl --new-corpus`; `rerank_qwen.py qwen_top100_v2.jsonl --docs 100 --reuse qwen_top100.jsonl --new-corpus`; `make_submission.py --source rerank --qwen qwen_top100_v2.jsonl 0.5 --new-corpus --dynamic -1.5 400 110000 200`.

**P. [19/10/2026] HAI BÀI NỘP TRÊN CHỈ MỤC MỞ RỘNG (chưa có điểm leaderboard)**: chuỗi đã chạy: embed shard_90000000 (330.955 chunk; 13.054 giây, 25,4 chunk/s; phải khởi động lại 1 lần vì guard RAM, và dùng thu gọn working set `EmptyWorkingSet` cho tiến trình embed khi máy chỉ còn <1,5 GB trống do mysqld 2,3 GB + nhiều tiến trình khác; shard 331k chunk quá lớn, lần sau nên tách shard 20k chunk) -> `dense_index.py build` (8.253.121 vector = 7.607.882 + 314.284 PubMed + 330.955 tiếng Việt mới, 169 giây) -> `make_submission.py --source rrf600v2` (truy hồi lại 1.200 câu, ~1,5 giờ, `candidates_rrf600v2_d600.jsonl`; top-600 mới có 2,4% chunk PubMed, 6,5% chunk tiếng Việt mới, 7,0% ngoài corpus mới) -> `rerank_deep.py 0 601 --candidates candidates_rrf600v2_d600.jsonl --new-corpus` (chỉ chấm cặp chưa có điểm: 65.351 cặp, 2.660 giây, `rerank_r0_601.jsonl`) -> `rerank_qwen.py qwen_top100_v2.jsonl --docs 100 --reuse qwen_top100.jsonl --new-corpus` (chấm bổ sung, ~48 cặp/giây). `validate_submission.py` nay chấp nhận id của cả hai corpus (bản cũ báo lỗi cho doc PubMed). **File bài 6039 đã nộp được giữ ở `submission_6039_qwen0.5_newcorpus.zip`** (đổi tên trước khi tạo bản mới vì cùng tên mặc định). **Bài A** `submission_rerank_dyn-1.5_400_110000_qwen0.5_newcorpus.zip`: 99,22 MB, sha256 `6cd07e4c6d7ad60ae26c2d65e337cdc63fd0fe526d2404feae44d725f6033de6`, HỢP LỆ, 169,9 doc/câu; so 6039 Jaccard doc 0,883, cửa sổ 0,814; trong doc nộp có 2,25% PubMed và 6,49% tiếng Việt mới. **Bài B** `..._newcorpus_nopubmed.zip` (cờ `--no-pubmed`): 99,71 MB, sha256 `8b8a54d12fec232ee7ec3eac12f1ae12086f16c4a784e0def75529eb71cd18ef`, HỢP LỆ, 166,1 doc/câu. Cách đọc điểm khi có: 6039 = 0,2427 / 0,2820 / 0,2033; B - 6039 = tác động của 117.353 trang tiếng Việt mới; A - B = tác động của PubMed. Đã nộp ngày 19/10, kết quả ở mục Q.

**P (đổi tên 19/10)**: hai bài nộp được đổi tên cho đủ giới hạn 64 ký tự của trang nộp: bài B -> `data/submission/sub_B_nopubmed_newcorpus_qwen.zip` (sha256 `8b8a54d1...18ef`), bài A -> `data/submission/sub_A_pubmed_newcorpus_qwen.zip` (sha256 `6cd07e4c...3de6`); nội dung không đổi. Thư mục `submission_rerank_dyn-1.5_400_110000_qwen0.5_newcorpus[_nopubmed]/` chứa `submission.json` tương ứng vẫn giữ tên cũ.

**Q. [19/10/2026] KẾT QUẢ HAI BÀI MỞ RỘNG ĐỘ PHỦ (600 câu chấm; FINAL / DOCS_F2 (P, R) / CHUNKS_F2 (P, R))**: bài 6106 = B `sub_B_nopubmed_newcorpus_qwen.zip` (+117.353 trang tiếng Việt, không PubMed): **0,2483** / 0,2906 (0,1791, 0,4016) / 0,2060 (0,2028, 0,2384). Bài 6107 = A `sub_A_pubmed_newcorpus_qwen.zip` (thêm PubMed): 0,2443 / 0,2860 (0,1752, 0,4014) / 0,2026 (0,2015, 0,2360). So 6039 (0,2427 / 0,2820 / 0,2033): B +0,0056 FINAL (Docs F2 +0,0086, Recall doc +0,0195, Precision doc gần như giữ; Chunks F2 +0,0027). A - B = -0,0040 FINAL: Recall doc không đổi (0,4016 -> 0,4014) và Precision giảm, tức doc PubMed (2,25% số doc nộp) gần như không trúng nhãn; nhãn không (hoặc gần như không) chứa PubMed. Quyết định: **bản chốt Public/Private lượt 1 = bài 6106 (B)**; 6039 và 5886 là dự phòng; PubMed bỏ hẳn (shard_91* vẫn nằm trong chỉ mục, lọc bằng `--no-pubmed`; mọi bài nộp mới PHẢI dùng `--new-corpus --no-pubmed`). Độ phủ chỉ mục trên corpus mới, đo lại 19/10 bằng đối chiếu doc_id của mọi shard chunk: 772.164 / 980.598 = 78,7% doc không phải PubMed (trước crawl lại 654.811 = 66,8%); 63,3% nếu tính cả 240.000 PubMed vào mẫu số. Phần tiếng Việt còn thiếu ≈ 130.000 trang: nhathuoclongchau 79.598 (WAF TLS, quyết định KHÔNG vượt), laodong 27.512 + baotayninh 1.198 (cần render JS), giadinhonline 12.405 (403), pmc-ecm-healthblog 5.333 (403). Ngoại suy thô theo trang (+0,0056 / 117k trang) cho khoảng +0,005 nếu mật độ nhãn tương đương, nhưng mật độ theo domain biến động 1,5-71 hit/1k doc (xem N) nên không đáng tin.
