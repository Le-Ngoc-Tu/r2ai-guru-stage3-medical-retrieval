# Working Notes — Truy hồi tài liệu y khoa đa ngôn ngữ (R2AI GURU Stage 3, Nhiệm vụ chung R2AI2026)

**Tác giả:** Lê Ngọc Tú (tài khoản leaderboard: `lengoctu`), thi đấu cá nhân
**Nhiệm vụ:** với một câu hỏi y khoa tiếng Việt, trả về các tài liệu (`relevant_docs`) và các đoạn văn (`relevant_chunks`) liên quan trong kho `ViBioMIR` gồm 4.394.718 URL tiếng Việt và tiếng Trung.
**Mã nguồn, số liệu, nhật ký thực nghiệm:** `github.com/Le-Ngoc-Tu/r2ai-guru-stage3-medical-retrieval` (thư mục `src/stage3`, `results/leaderboard_history.csv`, `docs/NHAT-KY-DU-AN.md`).

> Trạng thái bản thảo: số liệu Public đến ngày 19/10/2026. Các chỗ đánh dấu **[ĐIỀN SAU]** (điểm Private, tên đội trên hệ thống) chỉ điền khi có kết quả thật; không có chỗ nào được ước lượng thay cho số đo.

---

## Tóm tắt

Chúng tôi trình bày một hệ thống truy hồi lai chạy trọn vẹn trên **một máy cá nhân** (RTX 3050 6 GB, RAM 16 GB, ổ HDD, không cloud GPU, không API đóng): crawl bất đồng bộ 4.394.718 URL, chia chunk theo ngân sách token, lập chỉ mục BM25 (Tantivy) và dense BGE-M3 (nhị phân 1.024 bit kèm rescoring fp16), hợp nhất bằng RRF, rerank bằng BGE-reranker-v2-m3 có ghép thêm điểm Qwen3-Reranker-0.6B, chọn tài liệu theo **ngưỡng điểm rerank** và nộp **cửa sổ chunk dài ≤ 900 token**.

Kết quả trên Public Test (600 câu được chấm) theo luật chấm chunk ban đầu: **FINAL 0,2483** (Docs F2 0,2906; Chunks F2 0,2060), tăng từ 0,0253 của bài nộp đầu tiên; mỗi bước tăng đều có nguyên nhân đo được (mục 6). Ngày 23/10 Ban Tổ chức siết luật khớp chunk (mục 1); nộp lại đúng cùng file cho **FINAL 0,2384** (Docs F2 giữ nguyên 0,2906; Chunks F2 0,1862). Điểm Private: **[ĐIỀN SAU]**.

Đóng góp chính không nằm ở một mô hình mới mà ở **kỷ luật đo và các phát hiện về bài toán**:

1. Mỗi câu hỏi có trung bình **71 tài liệu tham chiếu**, không phải "vài tài liệu" như giả định ban đầu; sửa giả định này nâng điểm từ 0,025 lên 0,147 chỉ bằng cách trả đủ nhiều tài liệu.
2. Một bộ dev tự dựng (743 cặp) cho kết luận **ngược** với leaderboard thật về reranker; chúng tôi ghi lại cách phát hiện và bỏ nó khỏi việc chọn cấu hình.
3. Nộp **cửa sổ ghép chunk liền kề** thay vì chunk riêng lẻ tăng Chunks Precision 3,3 lần ở cùng cách xếp hạng, do luật khớp chia cho độ dài chunk tham chiếu.
4. Chọn tài liệu theo **điểm rerank** tốt hơn cắt theo K cố định; điểm rerank dự báo độ đúng mạnh hơn thứ hạng.
5. Phân tích chunk trượt cho thấy **77,2%** cửa sổ nộp thuộc tài liệu không có chunk nhãn nào, còn khi tài liệu đã đúng thì **82,4%** cửa sổ trúng: nút thắt là chọn đúng tài liệu (Precision), không phải chọn đoạn.

Báo cáo ghi đầy đủ các hướng đã đo và bác bỏ (mục 7) và những điều **chưa đo** (mục 9), vì một kết quả âm đo cẩn thận có giá trị hơn một con số đẹp không giải thích được.

---

## 1. Bài toán, dữ liệu và luật chấm

**Kho tri thức.** `links_corpus.parquet` do Ban Tổ chức cung cấp: 4.394.718 dòng (`id` từ 583 đến 4.420.561, không trùng; README dataset ghi 4.420.561 liên kết, chênh 25.843 `id` chưa giải thích được), 97 domain y tế, chỉ tiếng Việt và tiếng Trung (không có domain tiếng Anh, đã xác minh bằng quét toàn bộ domain). Đội thi tự crawl, làm sạch, chia chunk và lập chỉ mục.

**Câu hỏi.** `query.parquet`: 1.200 câu y khoa tiếng Việt; Public Test chấm 600 câu (593 câu có nhãn trong file chi tiết của bộ chấm).

**Bài nộp.** Một `submission.json` trong `submission.zip` (≤ 100 MB). Mỗi câu gồm `relevant_docs` (danh sách `id` nguyên có trong `links_corpus`) và `relevant_chunks` (danh sách `{"doc_id", "chunk_text"}`, văn bản thật của đoạn, ≤ 1.024 token, thuộc một tài liệu đã liệt kê).

**Điểm.** Hai phép F2 độc lập (Recall quan trọng gấp 4 lần Precision), `FINAL = (Docs F2 + Chunks F2) / 2`. Một chunk nộp được tính đúng khi thuộc đúng tài liệu và LCS token ≥ 0,40 so với độ dài một chunk tham chiếu (sau NFKC, HTML entity, chữ thường, chuẩn hóa khoảng trắng). `eval_f2.py` cài đặt đúng luật này và có bộ tự kiểm tra bằng các ví dụ có đáp án biết trước. **Cập nhật 23/10:** Ban Tổ chức bổ sung điều kiện thứ hai, chunk chỉ khớp khi đồng thời LCS/độ dài chunk đáp án ≥ 0,40 **và** LCS/độ dài chunk dự đoán ≥ 0,40, nhằm chặn chunk dự đoán quá dài; `eval_f2.py` chưa được cập nhật theo điều kiện này.

**Quy mô nhãn đo được.** Từ file chi tiết của bộ chấm cho bài nộp đầu tiên (593 câu có nhãn): trung bình **71,0 tài liệu tham chiếu mỗi câu** (trung vị 60, P10 = 12, P90 = 145, tối đa 190) và 74,7 chunk tham chiếu (trung vị 64, tối đa 200), tức ≈ 1,05 chunk mỗi tài liệu. Phát hiện này quyết định toàn bộ thiết kế sau đó (mục 5.1).

---

## 2. Hệ thống

Toàn bộ mã nguồn là tự viết (xem `THIRD-PARTY-NOTICES.md`); chỉ dùng thư viện và mô hình công khai.

### 2.1 Crawl

`url_crawler.py`: asyncio + `httpx`, trích nội dung bằng `trafilatura`, checkpoint SQLite (dừng và chạy lại an toàn). Hai cơ chế quan trọng rút ra từ thực tế:

- **Cột `bucket = id % 997`** để xoay vòng lấy lô theo nhiều domain. Nguyên nhân gốc của các lần tụt tốc độ là domain nằm thành khối `id` liên tục lớn hơn kích thước lô lấy (30.000), nên một lô chỉ chứa một domain và bị giới hạn bởi số kết nối mỗi domain. Sau khi sửa, tốc độ ổn định 5,1–5,2 trang/giây.
- **Circuit breaker theo domain:** domain có tỷ lệ lỗi 403/429/timeout vượt ngưỡng bị tạm cô lập (`banned_cooldown`) thay vì làm kẹt các worker. Ban đầu việc phát hiện làm thủ công; breaker tự động đã cô lập nhiều domain (ví dụ `zysjonline.com`, `ask.39.net`).
- **Lỗi mã hóa:** trang GBK không khai báo charset trong header bị giải mã sai thành `U+FFFD`. Đã sửa (`_decode_response` đọc `<meta charset>`, GB2312/GBK giải mã bằng gb18030) và tải lại 53.341 trang `wujue.com` (100% thành công). Phần `cnkang.com` (~449.000 trang) **không** tải lại; xem mục 3.

### 2.2 Chunk

`medical_chunker.py`, `chunk_corpus.py`: chia theo **ngân sách token BGE-M3**, tối đa 420 token mỗi chunk, overlap 60. Lý do: tỷ lệ token/ký tự đo trên 2.718 trang mẫu là 0,636 (tiếng Trung, trung vị) so với 0,279 (tiếng Việt), nên ngưỡng theo ký tự sẽ vượt 512 token với tiếng Trung. `text` luôn là chuỗi con nguyên văn của thân bài (có `char_start/char_end`); kiểm thử trên 3.000 trang cho 0 chunk có `text` không phải chuỗi con nguyên văn, điều bắt buộc vì luật cấm "tạo chunk thay thế ID". Contextual Retrieval tĩnh: `embed_text` ghép tiêu đề tài liệu và mục vào văn bản embed/chấm điểm, còn `text` nộp vẫn nguyên văn.

### 2.3 Truy hồi lai

- **BM25** (`tantivy_indexer.py`): Tantivy trên đĩa; chuỗi chữ Hán tách **bigram chồng lấp**, phần còn lại tách theo ký tự chữ-số chữ thường; truy vấn dùng đúng hàm tách từ này.
- **Dense** (`embed_corpus.py`, `dense_index.py`): `BAAI/bge-m3` fp16, vector 1.024 chiều; lập chỉ mục **nhị phân** (dấu từng chiều, FAISS `IndexBinaryFlat`, ≈ 1 GB) rồi **rescoring top-200** bằng vector fp16 gốc đọc mmap (15 GB trên đĩa). RAM tiến trình truy hồi ≈ 4 GB, VRAM đỉnh BGE-M3 ≈ 1,3 GB.
- **Hợp nhất** (`hybrid_search.py`): Reciprocal Rank Fusion k = 60, độ sâu 300 hoặc 600 chunk mỗi nguồn.

Độ trễ truy hồi nóng trung vị 256 ms/câu (BM25 58 ms + dense 178 ms) trên 20 câu mẫu; lần đầu nguội trên HDD 2,6 s.

### 2.4 Rerank

`rerank_deep.py`: **BGE-reranker-v2-m3** (fp16) chấm lại các chunk của RRF; văn bản chấm là `embed_text` (có tiêu đề + mục). Có guard RAM / nhiệt độ GPU / VRAM (tạm dừng khi RAM trống < 3,5 GB, GPU ≥ 80°C hoặc VRAM trống < 1,5 GB; file `STOP_RERANK` để dừng êm) để máy vẫn dùng làm việc được. Pool rerank đã thử: top-150, 300, 600 chunk.

### 2.5 Ghép Qwen3-Reranker-0.6B

`rerank_qwen.py`: với **100 tài liệu đầu** của mỗi câu (theo điểm BGE), chấm thêm đúng một chunk mỗi tài liệu (chunk điểm BGE cao nhất, cũng là chunk neo của cửa sổ nộp) bằng `Qwen/Qwen3-Reranker-0.6B`. Điểm là `logit("yes") − logit("no")` ở vị trí cuối của prompt chuẩn của mô hình (system "Judge whether the Document meets the requirements…", `<Instruct>/<Query>/<Document>`), đệm trái, tài liệu cắt 480 token, batch 8, chỉ tính logits vị trí cuối (`logits_to_keep=1`).

Ghép trong `make_submission.py --qwen FILE WEIGHT`: với mỗi câu, z-score riêng của điểm BGE và điểm Qwen trên 100 tài liệu, trộn với trọng số Qwen 0,5, rồi **quy ngược về thang BGE** (`mean_b + std_b · blend`) để các ngưỡng đã chọn trên thang BGE vẫn dùng được. Các chunk khác của cùng tài liệu bị chặn trên bởi điểm neo; tài liệu ngoài top 100 giữ nguyên điểm BGE.

### 2.6 Chọn tài liệu và cửa sổ

`make_submission.py --dynamic DOC_MIN DOC_CAP WINDOW_BUDGET WINDOW_CAP`:

- **Tài liệu:** lấy tài liệu có điểm rerank ≥ `DOC_MIN` (bản chốt −1,5), tối đa 400 tài liệu mỗi câu, mỗi câu luôn có ≥ 10 tài liệu. Bản chốt trung bình 167,9 tài liệu mỗi câu.
- **Chunk:** mỗi tài liệu được chọn nhận một **cửa sổ** = chunk neo ghép các chunk liền kề cùng tài liệu (nguyên văn, bỏ phần overlap) tới ≤ 900 token (đếm thật bằng tokenizer BGE-M3, chừa biên vì bộ chấm đếm lệch tối đa ~30 token so với tokenizer này). Ngân sách 110.000 cửa sổ toàn bộ 1.200 câu (≈ 92 cửa sổ mỗi câu), giới hạn bởi trần 100 MB của zip (bản chốt 96,6 MB).
- `validate_submission.py` kiểm tra schema, id, trùng lặp, chunk thuộc tài liệu đã liệt kê, ≤ 1.024 token và ≤ 100 MB trước mỗi lần nộp.

---

## 3. Sử dụng dữ liệu: dùng bao nhiêu, bỏ bao nhiêu

Số liệu đo trực tiếp từ `crawl_cache.sqlite3` và các shard chunk (không phải ước lượng):

| Hạng mục | Số lượng | Tỷ lệ |
| :--- | ---: | ---: |
| URL trong `links_corpus.parquet` | 4.394.718 | 100% |
| Trang crawl thành công (`done`) | 3.487.922 | 79,37% |
| Trang được chunk | 3.033.854 | 69,03% của corpus (86,98% của `done`) |
| **Chunk được lập chỉ mục (BM25 + dense)** | **7.607.882** | tiếng Trung 76,5%, tiếng Việt 23,5% |
| Loại: bị WAF chặn (`banned_cooldown`) | 875.487 | 19,92% |
| Loại: cần render JavaScript (`needs_js_render`) | 28.710 | 0,65% |
| Loại: lỗi vĩnh viễn (`failed`) | 2.599 | 0,06% |
| Loại: lỗi giải mã ký tự (≥ 10 ký tự `U+FFFD`, chủ yếu `cnkang.com`) | 454.068 | 10,33% |
| **Phần corpus chưa vào chỉ mục** | **1.360.864** | **30,97%** |

Chi tiết lý do loại trừ:

- **`banned_cooldown` (875.487):** domain bị WAF chặn IP hoặc không kết nối được, bị circuit breaker hoặc thao tác tay chuyển trạng thái. Đã định danh: `www.120ask.com` (175.540 dòng chưa crawl; không vào được từ 08/10, chưa xác định sập hay chặn IP), `zysjonline.com` (~243.347), `ask.39.net` (197.862), `nhathuoclongchau.com.vn` và `pmc-ecm-healthblog.beta.pharmacity.io` (84.931), `suckhoecongdongonline.vn` (59.284), `bingli.iiyi.com` (24.970), `article.iiyi.com` (5.623), `baodanang.vn` và `baohaiphong.vn` (30.786), `youmed.vn` (4.294), `thaythuocvietnam.vn` (1.717) và vài domain nhỏ. Cộng các domain này **không đủ** 875.487; phần còn lại (~262.927 dòng theo đối soát 02/10) **chưa gán được domain**. Quyết định (09/10): không retry các domain này.
- **Lỗi mã hóa (454.068):** trang GBK giải mã sai. Đã sửa và tải lại `wujue.com`; `cnkang.com` (~449.000 trang) không tải lại vì chi phí lớn và kỳ vọng thấp (bằng chứng gián tiếp ở mục 6.7 cho thấy nhãn chủ yếu ở tài liệu tiếng Việt).
- **`needs_js_render` (28.710):** chưa chạy `crawl4ai`; để dành nếu còn thời gian.

**Chưa đo:** tỷ lệ tài liệu tham chiếu nằm trong 30,97% chưa vào chỉ mục (không có danh sách tài liệu nhãn đầy đủ). Đây là một chặn trên chưa lượng hóa của Recall.

**Dữ liệu ngoài.** Chỉ dùng một nguồn ngoài, và chỉ để **dựng bộ dev thăm dò, không dùng để huấn luyện**: `tarudesu/ViHealthQA` (10.015 cặp hỏi-đáp, giữ 743 cặp có đáp án gần nguyên văn trong corpus). Bộ này sau đó bị bỏ khỏi việc chọn cấu hình (mục 5.2). Không dùng dữ liệu ngoài nào khác; không có bước huấn luyện hay tinh chỉnh mô hình nào trong hệ thống.

---

## 4. Thiết lập thực nghiệm và thước đo

- **Phép đo chính:** điểm Public (600 câu) do bộ chấm trả về sau mỗi lần nộp. Đây là phép đo duy nhất không thiên lệch; mọi quyết định cuối đều dựa vào đó.
- **Sai số:** với 600 câu, chênh dưới ≈ 0,003 FINAL giữa hai bài sát nhau được coi là nhiễu. Chúng tôi chủ động ghi mức này khi báo cáo từng so sánh.
- **Phân tích offline:** dùng file chi tiết (`details.jsonl`) của từng bài nộp mà bộ chấm trả về, cho biết từng tài liệu và từng cửa sổ trúng hay trượt. Chỉ dùng để **chọn cấu hình và chẩn đoán**, không dùng để huấn luyện bất kỳ mô hình nào. Thước đo offline: AUC trung bình theo câu, tính trên các tài liệu đã nộp, với nhãn là cửa sổ trúng/trượt của bài nộp tương ứng; khoảng tin cậy bằng bootstrap theo câu. Mọi phân tích offline chỉ nói về các tài liệu **đã được nộp**, nên không đo được tài liệu bị bỏ sót.
- **Quy tắc nộp:** mỗi bản đổi đúng **một** yếu tố so với bản trước để đọc được nguyên nhân; không nộp thí nghiệm ít thông tin (hạn mức 10 bài/ngày).

---

## 5. Các phát hiện

### 5.1 Bài toán nhiều tài liệu: sửa giả định nền

Thiết kế ban đầu kế thừa từ Stage 2 ("trả vài tài liệu, ít mà đúng": 3 tài liệu, 5 chunk) cho **FINAL 0,0253** (bài A) và 0,0237 (bài B có rerank + ngưỡng động chọn trên dev). Phân tích file chi tiết cho thấy mỗi câu có ~71 tài liệu tham chiếu, nên trả 3 tài liệu thì Recall tối đa chỉ ~4%. Quét K trên leaderboard: K = 10 → 0,0572; K = 30 → 0,0996; K = 100 → 0,1467 (mỗi tài liệu một chunk). Bài học: kiểm tra phân bố nhãn thật trước khi chọn bậc độ lớn của đầu ra.

### 5.2 Bộ dev tự dựng làm lệch kết luận

Bộ dev 743 cặp từ ViHealthQA có trung bình ~1,4 tài liệu nhãn mỗi câu (so với 71 ở dữ liệu thật). Trên bộ này, reranker không tiêu đề cho ChunkHit@1 = 0,225 so với RRF 0,272 (kém), nên chúng tôi từng kết luận reranker không giúp. Điểm leaderboard thật cho kết luận ngược: ở cùng cách chọn doc, rerank nâng Chunks F2 từ 0,1495 lên 0,1748 (precision +18%, recall +17%). Chẩn đoán trên bộ dev: reranker chọn câu hỏi-đáp khác cùng chủ đề, hợp lý nhưng không có nhãn; nhãn dev chỉ gồm chunk gần nguyên văn đáp án ViHealthQA nên phạt oan. Bài học: với nhãn thưa và lệch, **không chọn K hay reranker bằng dev tự dựng**; chúng tôi bỏ nó khỏi mọi quyết định sau ngày 14/10. Bản rerank có tiêu đề trên dev cho ChunkHit@1 = 0,272 (bằng RRF), cho thấy tiêu đề quan trọng, nhưng chênh nằm trong sai số của mẫu 743 câu.

### 5.3 Cửa sổ dài

Giả thuyết: luật khớp chia LCS cho độ dài chunk **tham chiếu**, nên nộp đoạn dài chỉ làm tăng overlap mà không đổi precision. Thử nghiệm: cùng cách xếp hạng, thay "mỗi tài liệu một chunk ≈ 350 token" bằng "cửa sổ ghép chunk liền kề ≤ 900 token". Kết quả: Chunks Precision **0,064 → 0,208** (3,3 lần), Chunks F2 0,0801 → 0,1159, FINAL 0,1467 → 0,1700. Phân tích cửa sổ trúng của bài sau: overlap trung bình 0,77 (phân vị 10/25/50/75/90 = 0,50/0,61/0,74/0,99/1,00), 40,7% đạt ≥ 0,9. Cỡ cửa sổ không phải đòn bẩy tiếp: cửa sổ 980 token (101.000 cửa sổ) cho Chunks F2 0,1897 so với 0,1927 ở 900 token (precision mỗi cửa sổ +5,4% nhưng số cửa sổ −8%).

### 5.4 Rerank: có ích khi có tiêu đề, và khi pool đủ sâu

- Rerank pool 150 chunk (bài 5628): FINAL 0,2006; Docs F2 **không đổi** (0,2265) đúng như dự đoán, vì pool chỉ ~110 tài liệu nhỏ hơn K nên tập tài liệu gần như không đổi (giao 0,95 với RRF); chỉ Chunks F2 tăng.
- Dự đoán trước của chúng tôi ("rerank sẽ đổi tập tài liệu khi cắt K") **sai** ở bước này vì lý do pool; đã sửa bằng cách rerank pool 300 chunk (≈ 230 tài liệu). Kết quả: ở K = 150, Docs F2 **0,2491** so với 0,2241 của RRF cùng K (+0,025); tập tài liệu đổi 27% (giao 0,73 với RRF top-150).
- Pool 600 chunk: thêm Docs F2 +0,0007 ở ≈ 140 tài liệu và +0,0072 ở ≈ 167 tài liệu; lợi ích nhỏ.

### 5.5 Điểm rerank dự báo độ đúng; chọn tài liệu theo ngưỡng

Từ file chi tiết của bài K = 130 (57.000 cửa sổ): tỷ lệ cửa sổ trúng theo điểm rerank là dưới −4: 1,3%; [−4, −2): 4,6%; [−2, 0): 9,8%; [0, 2): 19,4%; [2, 4): 28,3%; từ 4 trở lên: 37,1%. Trong cùng nhóm hạng, điểm cao trúng gấp 2–3 lần điểm thấp (hạng 30–60: 22,6% so với 9,1%). Vì vậy chọn tài liệu theo **ngưỡng điểm** thay vì K cố định: Docs F2 0,2513 (K = 130) → 0,2601 (ngưỡng −3) → 0,2626 (−2,5); đường cong ngưỡng phẳng quanh −2,5 đến −2. Với pool 600, ngưỡng −1,5 cho 0,2698 (167 tài liệu), −2,5 cho 0,2688 (223 tài liệu: Recall 0,428 nhưng Precision giảm 0,030), tức đỉnh quanh 170–190 tài liệu.

### 5.6 Nút thắt: Precision chọn tài liệu

Trên 593 câu có nhãn của bài 5781 (52.665 cửa sổ):

- **77,2%** cửa sổ (40.664) thuộc tài liệu không có chunk nhãn nào;
- 22,8% (12.001) thuộc tài liệu có nhãn, trong đó **82,4%** trúng;
- chỉ **4,0%** (2.107) là đúng tài liệu mà trượt đoạn;
- chunk nhãn tìm được: 10.151 / 44.819 (22,6%); cửa sổ trung bình 665 token.

Kết luận: chọn đoạn trong tài liệu đúng đã tốt; muốn nâng điểm chunk phải nâng Precision chọn tài liệu. Docs Recall 0,38 cao hơn nhiều Precision 0,16 ở bản chốt.

### 5.7 Ngôn ngữ của nhãn

76,5% chunk của kho là tiếng Trung, nhưng nhãn nằm chủ yếu ở tài liệu tiếng Việt. Trong 57.000 cửa sổ của một bài nộp, 14 domain tiếng Trung đã định danh chiếm 13,1% bài nộp nhưng chỉ 5,8% số cửa sổ trúng (tỷ lệ trúng 7,2% so với 17,6% ở domain tiếng Việt); 94,2% số cửa sổ trúng thuộc tài liệu tiếng Việt. **Đây là phân loại ngôn ngữ theo domain, không phải đo trực tiếp**, và chúng tôi **chưa thử** truy vấn bằng tiếng Trung (dịch hoặc mở rộng đa ngôn ngữ), nên không kết luận về giá trị của hướng đó. (Lưu ý đính chính: bản phân tích đầu tiên tính nhầm các domain tiếng Việt không có đuôi `.vn` vào nhóm khác nên nêu con số "78,5% số trúng thuộc `.vn`" sai; đã tính lại và loại bỏ con số đó.)

---

### 5.8 Corpus thay đổi giữa cuộc thi

Ngày 18/10/2026 Ban Tổ chức phát hành `links_corpus_vi_en_zh.parquet`: 1.220.598 URL (740.598 tiếng Việt, 240.000 tiếng Trung, 240.000 PubMed tiếng Anh), `query.parquet` không đổi. Đối chiếu với corpus cũ: 980.598 URL trùng đúng `id` và URL (toàn bộ tiếng Việt và một mẫu 240.000 tiếng Trung giữ lại), 240.000 PubMed là mới (`id` > 4.420.561). Từ file chi tiết của ba bài đã chấm: 100% cửa sổ trúng (9.894, 9.282, 9.885) thuộc tài liệu có trong corpus mới, trong khi ≈ 6,3% cửa sổ nộp (≈ 3.300) nằm ngoài và không cửa sổ nào trong số đó trúng (kỳ vọng ≈ 620 nếu nhãn rải theo corpus cũ). Mô phỏng offline trên bài 5781 dự đoán +0,006 FINAL; nộp thật (bài 6039, chỉ thêm bước bỏ tài liệu ngoài corpus mới) cho **+0,0085** (0,2342 → 0,2427), xác nhận giả thuyết trên leaderboard.

Hệ quả: chỉ mục của chúng tôi chỉ phủ **654.811 / 1.220.598 = 53,6%** tài liệu của corpus mới (đối chiếu `doc_id` trong 222 shard chunk). Phần thiếu: 240.000 PubMed (chưa crawl); ≈ 249.000 trang tiếng Việt (219.088 `banned_cooldown`, 28.710 cần render JavaScript, 1.468 lỗi), tức tiếng Việt phủ 66,4%; ≈ 76.500 trang tiếng Trung (trong đó 31.235 trang `cnkang.com` hỏng mã hóa). Kiểm tra truy cập ngày 18/10 (một URL mỗi domain) cho thấy phần lớn domain tiếng Việt từng bị coi là bị chặn nay trả HTTP 200. Mật độ trúng theo domain dao động 1,5–71 cửa sổ trúng trên 1.000 tài liệu đã lập chỉ mục, nên lợi ích thêm các trang này không suy được từ số tài liệu: chưa đo.

**Mở rộng độ phủ (19/10/2026).** Chúng tôi crawl lại 9 domain tiếng Việt từng bị coi là bị chặn (4 request đồng thời mỗi domain, User-Agent trình duyệt vì User-Agent định danh bị trả 403; `robots.txt` chỉ cấm trang tìm kiếm và giỏ hàng) và lấy thêm 117.353 trang (+3,4% số trang `done`; 330.955 chunk), cộng 239.699/240.000 bản ghi PubMed qua NCBI efetch (tiêu đề và tóm tắt, 314.284 chunk tiếng Anh). `nhathuoclongchau.com.vn` (79.598 trang) chặn theo dấu vân TLS ngay cả với User-Agent trình duyệt; chúng tôi **không** vượt cơ chế chặn này và loại domain khỏi phạm vi. Độ phủ chỉ mục trên corpus mới (đo lại bằng đối chiếu `doc_id` của mọi shard chunk với `links_corpus_vi_en_zh.parquet`) tăng từ 654.811 lên **772.164 / 980.598 = 78,7%** tài liệu không phải PubMed. Sau khi nối thêm vào BM25, chỉ mục dense (8.253.121 vector), truy hồi và rerank lại, hai bài được nộp để tách tác động từng phần (cùng tham số cắt với bài 6039):

| Bài | Nội dung | FINAL | Docs F2 (P / R) | Chunks F2 (P / R) |
| :---: | :--- | :---: | :---: | :---: |
| 6039 | chỉ mục cũ, lọc corpus mới | 0,2427 | 0,2820 (0,1800 / 0,3821) | 0,2033 (0,1986 / 0,2342) |
| 6106 | + 117.353 trang tiếng Việt, không PubMed | **0,2483** | **0,2906** (0,1791 / 0,4016) | **0,2060** (0,2028 / 0,2384) |
| 6107 | + cả PubMed | 0,2443 | 0,2860 (0,1752 / 0,4014) | 0,2026 (0,2015 / 0,2360) |

Trang tiếng Việt mới cho **+0,0056 FINAL** (chủ yếu ở tầng tài liệu: Recall +0,0195 với Precision gần như giữ nguyên). PubMed làm điểm **giảm 0,0040**: Recall tài liệu không đổi (0,4016 → 0,4014) trong khi Precision giảm, tức các tài liệu PubMed (2,25% số tài liệu nộp) hầu như không trúng nhãn nhưng chiếm chỗ. Đây là bằng chứng gián tiếp rằng nhãn không (hoặc gần như không) chứa PubMed; tập PMID lấy mẫu ngẫu nhiên toàn PubMed, nhiều bài rất cũ. Bản chốt dùng cấu hình 6106.

---

## 6. Hành trình điểm trên Public Test

| Bước | Bài | FINAL | Docs F2 | Chunks F2 | Thay đổi và nguyên nhân |
| :--- | :---: | :---: | :---: | :---: | :--- |
| Baseline (3 tài liệu, 5 chunk) | — | 0,0253 | 0,0354 | 0,0153 | giả định số lượng tài liệu sai |
| RRF, 100 tài liệu × 1 chunk | — | 0,1467 | 0,2133 | 0,0801 | trả nhiều tài liệu |
| 150 tài liệu, 30 cửa sổ ≤ 900 token | 5591 | 0,1700 | 0,2241 | 0,1159 | chunk dài tăng precision 3,3 lần |
| ~230 tài liệu, 60 cửa sổ | 5597 | 0,1880 | 0,2265 | 0,1495 | thêm cửa sổ |
| Rerank (pool 150), ~217 tài liệu, 60 cửa sổ | 5628 | 0,2006 | 0,2265 | 0,1748 | rerank chọn đúng cửa sổ |
| Rerank sâu (pool 300), 150 tài liệu, 90 cửa sổ | 5674 | 0,2227 | 0,2491 | 0,1964 | rerank đổi được tập tài liệu |
| Tài liệu theo ngưỡng điểm ≥ −2,5 | 5715 | 0,2306 | 0,2626 | 0,1987 | cắt theo điểm thay vì K |
| Pool 600, ngưỡng ≥ −1,5 | 5781 | 0,2312 | 0,2698 | 0,1927 | thêm ứng viên cho rerank |
| + Ghép Qwen3-Reranker-0.6B | 5886 | 0,2342 | 0,2735 | 0,1949 | thêm bộ chấm độc lập; cả hai tầng cùng tăng |
| + Lọc theo corpus mới | 6039 | 0,2427 | 0,2820 | 0,2033 | nhãn chỉ nằm trong corpus mới; bỏ doc ngoài đó |
| + 117.353 trang tiếng Việt crawl lại (bản chốt) | **6106** | **0,2483** | **0,2906** | **0,2060** | tăng độ phủ chỉ mục từ 53,6%; Recall doc +0,0195 |
| (+ PubMed, không dùng) | 6107 | 0,2443 | 0,2860 | 0,2026 | PubMed không thêm Recall, giảm Precision |

Toàn bộ 25 bài đã chấm nằm ở `results/leaderboard_history.csv` (cấu hình và điểm). Từ bước "ngưỡng điểm" trở đi mọi tinh chỉnh chỉ còn vài phần nghìn FINAL: hệ thống đã **phẳng** với cách làm hiện tại.

### 6.1 Bài ghép Qwen (bài 5886)

Kiểm tra offline trên 46 câu có nhãn (100 câu đầu theo `id`, 100 tài liệu mỗi câu): AUC trung bình theo câu của BGE 0,6154; Qwen riêng 0,6409; ghép z-score với trọng số Qwen 0,25 / 0,5 / 0,75 cho 0,6340 / **0,6519** / 0,6462. Mức tăng ở 0,5: +0,0365, bootstrap theo câu 95% CI [+0,0095; +0,0660], 28/46 câu cải thiện. Chấm đủ 1.200 câu × 100 tài liệu (120.000 cặp) mất 13.400 giây (8,9 cặp/giây). Kết quả leaderboard so với bài 5781 (cùng tham số cắt, chỉ khác Qwen): FINAL **+0,0030**, Docs F2 +0,0037 (P 0,1635 → 0,1648; R 0,3751 → 0,3818), Chunks F2 +0,0022 (P 0,1842 → 0,1899; R 0,2235 → 0,2260). Mức tăng **sát ngưỡng nhiễu** và nhỏ hơn dự đoán offline, nhưng cùng chiều ở cả hai tầng và ở cả precision lẫn recall; chúng tôi dùng bản này làm bản chốt nhưng không khẳng định đây là cải thiện chắc chắn.

Lịch sử: một thử nghiệm offline trước đó trên 100 câu với tốc độ 5,3 cặp/giây (do tính logits toàn bộ từ vựng) ước 15–19 giờ GPU và chúng tôi đã định bác bỏ hướng này; sau khi sửa bằng `logits_to_keep=1` tốc độ đạt 8,7–8,9 cặp/giây và chỉ chấm 100 tài liệu mỗi câu thì còn ≈ 3,7 giờ, nên hướng được làm lại và chạy. Đây là ví dụ một quyết định bác bỏ dựa trên chi phí đo sai.

---

## 7. Các hướng đã đo và bị bác bỏ

| Hướng | Kết quả đo | Kết luận |
| :--- | :--- | :--- |
| BM25 thuần thay RRF | 54% điểm của RRF ở K = 100 (FINAL 0,0786 so với 0,1467; Docs Precision 0,089 so với 0,166) | dense cần thiết |
| Cửa sổ 980 token thay 900 | Chunks F2 0,1927 → 0,1897 | hòa: precision mỗi cửa sổ +5,4% nhưng số cửa sổ −8% |
| Phân bổ cửa sổ theo điểm toàn cục | Chunks F2 0,1987 → 0,1927 trên pool sâu; phân bổ theo điểm không cải thiện chunk | không tốt hơn cố định theo hạng |
| Gộp điểm cấp tài liệu (tổng sigmoid mọi chunk, số chunk, chunk thứ hai…) | AUC 0,652 → 0,663 (offline, 578 câu) | không đáng làm |
| Tăng K lên ≈ 223 tài liệu | Docs F2 0,2688 < 0,2698 (167 tài liệu) | đỉnh ở ≈ 170–190 tài liệu |
| Cắt số tài liệu theo từng câu | oracle chọn tốt nhất trong 3 mức: +0,021 Docs F2; quy tắc thực tế (học ngưỡng trên một nửa số câu, đo trên nửa còn lại): chỉ +0,006 | trong sai số, không triển khai |
| Khử chunk lặp do overlap | ChunkHit@5 0,353 → 0,354 trên dev | trong top-30 gần như không có chunk lặp |
| Tinh chỉnh K, ngưỡng, pool thêm | ± 0,005 FINAL | đã phẳng |

Quy tắc công thức F2: với Precision và Recall cấp tài liệu, F2 của một câu = 5r / (4G + k) (r tài liệu đúng, k tài liệu nộp, G tài liệu tham chiếu); biên tối ưu để thêm tài liệu là precision biên ≈ F2/5, ≈ 5% ở mức điểm hiện tại. Quy tắc này được dùng để đọc xem việc thêm tài liệu/cửa sổ còn lợi hay không (ví dụ, tài liệu hạng 150 → 217 có precision biên ≈ 2,4% nên giảm điểm).

---

## 8. Tài nguyên tính toán và tái lập

**Phần cứng:** một máy Windows 11, RTX 3050 6 GB, RAM 16 GB, ổ HDD (cả dữ liệu lẫn code trên cùng một ổ vật lý). Không dùng cloud GPU, không gọi API LLM đóng.

**Phần mềm (đã xác minh trên venv):** Python 3.11, PyTorch 2.14.1+cu126, transformers 5.19.0, tokenizers 0.23.3, faiss-cpu 1.15.1, Tantivy, polars, httpx, trafilatura, numpy 2.4.6.

**Thời gian đo thật:**

| Bước | Thời gian |
| :--- | :--- |
| Crawl toàn bộ | từ 01/10 đến 09/10/2026 16:24, nhiều lần dừng/chạy lại (cúp điện, sự cố WAF, sự cố chặn event loop); tốc độ ổn định 5–7 trang/giây |
| Chunk toàn corpus (2 worker) | 25.633 giây (≈ 7,1 giờ), 222 shard, 2,26 GB |
| Chỉ mục BM25 (2 luồng) | 950 giây, 2,70 GB |
| Embed BGE-M3 7.607.882 chunk | nhiều ngày GPU (28–50 chunk/giây tùy giai đoạn, guard nhiệt độ/RAM); **tổng thời gian chính xác chưa đo** vì nhật ký bộ đếm không khớp giờ đồng hồ |
| Chỉ mục nhị phân | 156 giây (≈ 2,6 phút), 1,0 GB |
| Rerank BGE-reranker-v2-m3 (3 đoạn) | 6.037 + 5.490 + 14.674 = 26.201 giây (≈ 7,3 giờ) |
| Qwen3-Reranker-0.6B (120.000 cặp) | 13.400 giây (≈ 3,7 giờ) |

**Các lệnh tái tạo bản chốt** (trong `src/stage3`, venv của dự án; chạy nền từng lệnh, RAM trống ≥ 8 GB):

```
python url_crawler.py                               # crawl
python chunk_corpus.py                              # chunk -> data/chunks
python tantivy_indexer.py --index-dir ../../data/tantivy_index
python embed_corpus.py                              # BGE-M3 dense
python dense_index.py build                         # chỉ mục nhị phân
python make_submission.py --source rrf              # RRF sâu 300
python make_submission.py --source rrf600           # RRF sâu 600
python rerank_deep.py 0 150
python rerank_deep.py 150 300
python rerank_deep.py 0 600 --candidates candidates_rrf600_d600.jsonl
python rerank_qwen.py qwen_top100.jsonl --docs 100
python make_submission.py --source rerank --qwen qwen_top100.jsonl 0.5 --new-corpus --dynamic -1.5 400 110000 200
python validate_submission.py ../../data/submission/submission_rerank_dyn-1.5_400_110000_qwen0.5_newcorpus.zip
```

Bài chốt: `submission_rerank_dyn-1.5_400_110000_qwen0.5.zip`, 96,57 MB, sha256 `bd4becf407e970f6fe0bbc12588486cc8a97c1506b6fd203ec09a3b3c25eb563`, validator báo hợp lệ (1.200 câu, 0 câu rỗng ở cả hai trường). Bản chốt hiện tại là bài 6039 (`..._qwen0.5_newcorpus.zip`, 99,50 MB, sha256 `33b735387767ac5149c4f0930f41644176a4494c27bbc88541f4602cbd4e7647`, tạo bằng cách thêm `--new-corpus`); dưới đây là bản ghép Qwen không lọc (bài 5886) và bản dự phòng (bài 5781, 96,36 MB, sha256 `e91451ad2ad37a65043045614ae6b96522ab0cf969c84ab7aea5ceb696f03032`) không có Qwen.

**Tính xác định:** các điểm số và xếp hạng chỉ phụ thuộc vào mô hình, tokenizer, tham số cắt đã nêu và dữ liệu crawl. Dữ liệu crawl **không thể tái lập chính xác** vì nội dung các trang nguồn thay đổi và một số domain chặn IP; chúng tôi lưu `crawl_cache.sqlite3` (16 GB) làm nguồn gốc. Hiệu năng trên Linux hay GPU khác **chưa thử**.

---

## 9. Hạn chế và điều chưa đo

- **Luật chấm chunk đổi ngày 23/10 và bản nộp chưa được tối ưu lại cho luật mới.** Nộp lại đúng file bài 6106: Docs không đổi (F2 0,2906, P 0,1791, R 0,4016), Chunks F2 0,2060 → 0,1862 (P 0,2028 → 0,1817, R 0,2384 → 0,2151), FINAL 0,2483 → 0,2384. Precision và Recall chunk cùng giảm ≈ 10% khi số cửa sổ nộp không đổi; chúng tôi **suy luận** (chưa kiểm chứng) rằng khoảng 10% cửa sổ ≤ 900 token trước đó khớp nay trượt điều kiện LCS/độ dài chunk dự đoán. Thiết kế cửa sổ dài (mục 5.3) được chọn cho luật cũ; cửa sổ ngắn hơn có thể tốt hơn dưới luật mới nhưng **chưa được thử** vì giới hạn tài nguyên máy cá nhân, nên bản nộp cuối vẫn là cấu hình bài 6106.
- **Điểm Public chỉ từ 600 câu**, và các ngưỡng (K, điểm rerank, trọng số Qwen 0,5) được chọn trên chính những câu này; sai số giữa các bài sát nhau (± 0,003) nằm trong nhiễu. Mức tăng của Qwen (+0,003) nằm sát ngưỡng đó. Điểm Private: **[ĐIỀN SAU]**.
- **Độ phủ corpus:** 30,97% URL chưa vào chỉ mục; tỷ lệ tài liệu tham chiếu nằm trong phần đó **chưa đo**. Tải lại phần tiếng Trung lỗi mã hóa (`cnkang.com`) không làm; ước lượng lợi ích tối đa nếu thêm dữ liệu chỉ là phỏng đoán (≤ +0,01–0,02 FINAL), **chưa kiểm chứng**.
- **Độ phủ corpus mới chỉ 53,6%** (mục 5.8): PubMed chưa crawl, ≈ 249.000 trang tiếng Việt và ≈ 76.500 trang tiếng Trung chưa vào chỉ mục; chưa biết nhãn có chứa PubMed hay không. Điểm Public tăng khi bỏ doc ngoài corpus mới cho thấy đây là hướng còn dư địa nhưng lợi ích chưa đo.
- **Truy vấn tiếng Trung chưa thử** (dịch hoặc mở rộng đa ngôn ngữ); mọi nhãn dev tự dựng là tiếng Việt nên không đo được; bằng chứng duy nhất là gián tiếp (mục 5.7).
- **Viết lại truy vấn** bằng mô hình mở nhỏ (câu hỏi bệnh nhân dài, kể chuyện) chưa thử.
- **Precision chọn tài liệu** là nút thắt (Precision 0,16 so với Recall 0,38); các tinh chỉnh cắt tài liệu đã hết dư địa, chỉ chất lượng xếp hạng mới thay đổi được kết quả.
- Phân tích offline chỉ bao quát các tài liệu **đã nộp**; không đo được tài liệu nhãn bị bỏ sót hoàn toàn.
- Trang cần render JavaScript (28.710) chưa được crawl.
- Bộ chấm đếm token lệch ≈ ± 30 token so với tokenizer BGE-M3; mọi cửa sổ chừa biên dưới 1.024 token.
- Một số chunk (ví dụ 7 trong bài B đầu tiên) là phần đầu trang hỏi-đáp tiếng Trung có 87–91% khoảng trắng; tỷ lệ chunk dạng này trong corpus **chưa đo**.

---

## 10. Mô hình, giấy phép và tuân thủ

| Mô hình | Checkpoint / cách lấy | Giấy phép | Tham số | Vai trò |
| :--- | :--- | :--- | :--- | :--- |
| BGE-M3 | `BAAI/bge-m3`, tải bằng `huggingface_hub` về `data/hf_cache` | MIT | < 1B | embedding dense đa ngôn ngữ; tokenizer đếm token |
| BGE-reranker-v2-m3 | `BAAI/bge-reranker-v2-m3`, tải bằng `huggingface_hub` | MIT | < 1B | cross-encoder rerank |
| Qwen3-Reranker-0.6B | `Qwen/Qwen3-Reranker-0.6B`, tải bằng `huggingface_hub` | Apache-2.0 | 0,6B (theo tên) | bộ chấm bổ sung ghép với BGE |

Cả ba mô hình đều là trọng số công khai trên Hugging Face, ≤ 15B tham số, công bố trước 01/08/2026; **không dùng LLM đóng nào**. Không có bước huấn luyện hay tinh chỉnh; mô hình dùng nguyên checkpoint công khai. Danh sách thư viện kèm giấy phép đã xác minh bằng `pip show`: `THIRD-PARTY-NOTICES.md`.

**Dữ liệu và quy tắc cuộc thi.** Mọi chunk nộp là văn bản nguyên văn trích từ tài liệu crawl (kiểm tra bằng `validate_submission.py` và kiểm thử chunker); không bịa chunk thay thế ID; `doc_id` luôn là `id` trong `links_corpus.parquet`; không hardcode đáp án; không sao chép mã đội khác. Dữ liệu ngoài duy nhất là ViHealthQA, chỉ dùng thăm dò (mục 3). Tập dữ liệu `ViBioMIR` giữ nguyên giấy phép CC BY-NC 4.0 của tác giả và không nằm trong repo; nội dung crawl thuộc bản quyền các trang nguồn và không được phân phối lại.

---

## Phụ lục A. Nhật ký quyết định đáng chú ý

1. **01/10:** chọn crawl toàn bộ corpus thay vì theo mẫu; chọn không dùng LangChain để chạy gọn trong 6 GB VRAM.
2. **02/10:** thêm cột `bucket` phá khối domain liên tục; circuit breaker tự cô lập domain bị chặn.
3. **09/10:** đóng crawl; không retry `banned_cooldown`; tải lại `wujue.com`, không tải lại `cnkang.com`.
4. **10/10:** chunk theo ngân sách token (đo tỷ lệ token/ký tự trước khi chọn).
5. **14/10:** hai bài nộp đầu bị bộ chấm báo lỗi định dạng (`relevant_chunks` phải là object `{doc_id, chunk_text}`, không phải chuỗi trần); nguyên nhân do tài liệu nội bộ ghi ví dụ sai và validator kiểm tra theo chính ví dụ sai; đã sửa cả hai. Cùng ngày phát hiện giả định "vài tài liệu" sai (mục 5.1).
6. **15/10:** rerank sâu; dự đoán sai về tập tài liệu của pool 150, sửa bằng pool 300 (mục 5.4); chọn tài liệu theo ngưỡng điểm.
7. **16/10:** pool 600; đóng bản chốt 5781; phân tích chunk trượt; thử Qwen offline (sau đó sửa tốc độ).
8. **17/10:** chấm Qwen cho 1.200 câu, bài 5886 đạt 0,2342; chốt làm bản Public và lượt Private số 1.
9. **18–22/10:** lọc theo corpus mới (6039, 0,2427); crawl lại 117.353 trang tiếng Việt (6106, 0,2483); thêm PubMed làm điểm giảm (6107, 0,2443) nên bỏ; không crawl `nhathuoclongchau.com.vn` (WAF theo dấu vân TLS) và không làm thêm trang Pharmacity sau thông báo 22/10 (lợi ích ước lượng ≈ +0,0003, trong nhiễu).
10. **23/10:** Ban Tổ chức siết luật khớp chunk; nộp lại 6106 cho 0,2384. Chúng tôi chọn giữ nguyên cấu hình 6106 cho Private thay vì thử cửa sổ ngắn hơn, vì máy cá nhân không đáp ứng nhiều giờ chạy lại.

## Phụ lục B. Tóm tắt các bài nộp chính

Xem bảng ở mục 6 và `results/leaderboard_history.csv`. Phụ lục này sẽ bổ sung điểm Private và danh sách lượt nộp Private (tối đa 5 bài, hạn 04/11/2026) khi có kết quả: **[ĐIỀN SAU]**.
