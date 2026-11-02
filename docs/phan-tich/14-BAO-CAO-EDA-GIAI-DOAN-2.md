# Báo cáo EDA Giai đoạn 2 — dữ liệu đã crawl (09/10/2026)

Mọi số liệu dưới đây trace được về một lần đo; phần là **ước lượng từ mẫu** được ghi rõ, phần chưa đo ghi **CHƯA ĐO**.

## 1. Phương pháp và những điều đã thử bỏ

- **Tổng số liệu chính xác** lấy từ `links_corpus.parquet` (4.394.718 dòng, 97 domain) và đếm SQLite lúc đóng Giai đoạn 1 (done 3.487.922; banned_cooldown 875.487; needs_js_render 28.710; failed 2.599).
- **Quét toàn bảng `pages` để đếm theo domain/status đã thử 2 lần và bỏ**: DB 17,6GB trên HDD, đọc rơi xuống ~0,6MB/s (đọc ngẫu nhiên) dù chỉ chọn cột `domain`,`status`. Lý do cấu trúc chưa kiểm chứng riêng (nghi các leaf page bị tách rời sau khi UPDATE cột `bucket`/markdown). Đã chuyển sang **mẫu phân tầng**.
- **Mẫu**: 31.374 id (97 domain; tối thiểu 50 id/domain, còn lại tỷ lệ theo corpus; seed 0) chọn từ parquet rồi đọc theo id từ DB trong 348 giây. Lưu tại `data/eda_sample.parquet` (cột id, domain, status, http_status, title, content_length, markdown) để mọi phân tích sau không phải đụng lại DB.
- **Kiểm chứng bộ ước lượng** (trọng số = N_domain / k_domain): ước lượng từ mẫu so với số đếm thật — done -0,2%; banned_cooldown +0,7%; needs_js_render +3,5%; failed +26,7% (chỉ 2.599 dòng nên phương sai lớn, không dùng cho failed). Với các nhóm lớn bộ ước lượng đủ tin cậy.
- **Bước băm toàn corpus để đo trùng lặp chính xác (bước D) đã bỏ** theo quyết định của user; trùng lặp chỉ đo trên mẫu.

## 2. Phát hiện chính: lỗi mã hóa làm hỏng ~14,5% trang `done`

Một phần trang tiếng Trung lưu trong DB chứa ký tự thay thế `U+FFFD` (hiện `��`) thay cho chữ Hán — mất thông tin vĩnh viễn, không khôi phục được từ DB.

- **Ước lượng**: ~503.000 trang (14,46% trang done), tập trung ở **`www.cnkang.com` ~449.000** (46,6% số trang done của domain trong mẫu; theo id: nhóm ~1.650.000-1.999.999 và ~3.400.000-3.5xx.xxx hầu như hỏng 100%, các nhóm id khác 0%) và **`www.wujue.com` ~53.000 (100% hỏng)**; còn lẻ ở `health.people.com.cn` (32% mẫu), `qy.familydoctor.com.cn` (100%, ~40 trang) và vài trang khác.
- **Nguyên nhân (đã kiểm chứng trực tiếp 3 request ngày 09/10)**: server trả `Content-Type: text/html` **không kèm charset**, charset chỉ nằm trong `<meta ... charset=gb2312>`. `url_crawler.py` dòng 228 gọi `resp.text` (httpx mặc định UTF-8 khi header thiếu charset) nên giải mã sai. Trên `wujue.com` và một URL `cnkang.com` bị hỏng: giải mã UTF-8 cho 2.264 / 1.327 ký tự `U+FFFD` và gần 0 chữ Hán; giải mã `gb18030` cho **0 `U+FFFD`** và 1.802 / 910 chữ Hán. Tức là tải lại với giải mã đúng sẽ sửa được.
- **Hệ quả cho phân loại ngôn ngữ**: các trang hỏng bị bộ phân loại Unicode xếp nhầm là "tiếng Việt" (vì chỉ còn chữ Latin trong khung YAML). Báo cáo bên dưới đã tách riêng nhóm này.
- **Đã xử lý một phần (09/10, 23:31)**: sửa `url_crawler.py` (hàm `_decode_response`) và tải lại `www.wujue.com`: 53.341/53.341 dòng thành công (tốc độ đo 12,1/s). Mẫu 3.000 dòng sau tải lại: 0 trang còn `U+FFFD`, 3.000/3.000 có chữ Hán, độ dài trung vị 846 ký tự (ước lượng từ mẫu). **`www.cnkang.com` (~449.000 trang) KHÔNG tải lại** theo quyết định của user. Sau xử lý: trang hỏng còn ~450.000, trang done dùng được ước lượng ~3.038.000 (87,1% done; 69,1% corpus). Các con số ở mục 3 bên dưới là số TRƯỚC khi tải lại `wujue.com`.

## 3. Phân bố trên trang `done` (ước lượng toàn corpus từ mẫu, 3.480.431 trang ước lượng)

| Nhóm | Số trang ước lượng | % |
|---|---|---|
| Tiếng Trung (tỷ lệ chữ Hán > 50%) | ~2.483.000 | 71,34% |
| **Lỗi mã hóa (>=10 ký tự U+FFFD)** | ~503.000 | 14,46% |
| Tiếng Việt (tỷ lệ chữ Hán < 5%) | ~491.000 | 14,11% |
| Hỗn hợp | ~3.000 | 0,09% |

Trên 2.977.000 trang done **không lỗi mã hóa** (85,54%):
- **Độ dài** (ký tự): P25/P50/P75/P95/P99 = 952 / 1.395 / 2.339 / 5.793 / 8.726. Dưới 500 ký tự: 3,71%; dưới 1.000 ký tự: 28,64%. So với câu hỏi (trung vị 81, P95 364 ký tự): không trang nào ngắn hơn câu hỏi trung vị; các trang ngắn nhất tập trung ở `zydcd.com` (trung vị 490), `qihuangzhishu.com` (343), `zhongyibaodian.net` (22% dưới 500).
- **Tỷ lệ nội dung y khoa — ƯỚC LƯỢNG RẤT THÔ**: 92,0% trang có >=3 lần xuất hiện của 22 từ khóa y khoa (10 từ Việt + 12 từ Hán, danh sách trong script phân tích). Hạn chế: từ khóa thô (ví dụ "病", "药", "đau", "bệnh" xuất hiện cả trong tin tức), không phân biệt tài liệu tham khảo lâm sàng với tin sức khỏe, chưa kiểm chứng bằng đọc thủ công. Domain nhiều trang ít từ khóa nhất: `suckhoecongdongonline.vn` (~62.000 trang), `suckhoedoisong.vn` (~19.000), `a-hospital.com` (~19.000), `zhongyibaodian.net` (~19.000), `thanhnien.vn` (~15.000).
- **Trang rác/placeholder** (lộ ra khi xem nhóm trùng lặp): trang chủ `thaythuocvietnam.vn` (13 bản trùng trong mẫu), trang "Content not available" của `vinmec.com`, trang "Xin lỗi, trang không tồn tại" của `39.net` (cũng bị lỗi mã hóa), trang đăng nhập `test.pmphai.com` ("Insert title here"). Tỷ lệ toàn corpus **CHƯA ĐO** (mẫu quá nhỏ).

## 4. Trùng lặp (chỉ trên mẫu — ước lượng thấp)

Trong 24.963 trang done của mẫu: 27 nhóm trùng nội dung (41 dòng dư, ~0,16%), 162 title trùng (426 dòng dư, ~1,7%). Mẫu chỉ chiếm ~0,7% số trang done nên **tỷ lệ trùng toàn corpus CHƯA ĐO**; trùng nội dung chủ yếu là trang placeholder nêu trên, trùng title ở trang trùng lặp theo chủ đề (không hẳn là tài liệu trùng).

## 5. Độ lệch của tập `done` so với corpus gốc

- **Domain bị loại hoàn toàn** (0% done): `zysjonline.com` (243.347), `nhathuoclongchau.com.vn` (79.598), `bingli.iiyi.com` (24.990), `article.iiyi.com` (5.641), `baohaiphong.vn`, `baonghean.vn`, `baodanang.vn`, `hanoimoi.vn`, `pmc-ecm-healthblog.beta.pharmacity.io`; `laodong.vn` và `baotayninh.vn` hầu hết là `needs_js_render` (91% và 100% trong mẫu).
- **Domain bị loại một phần** (tỷ lệ done trong mẫu): `ask.39.net` 40,9% (59,1% banned), `120ask.com` 80,4%, `suckhoecongdongonline.vn` 61,2%, `qihuangzhishu.com` 60,9%, `giadinhonline.vn` 34,2%, `baocantho.com.vn` 65,9%, `thaythuocvietnam.vn` 38%, `youmed.vn` 28%, `dantri.com.vn` 6%.
- Hệ quả: tập done thiên về tiếng Trung (71%) và một số domain lớn (`cnkang.com` ~27,6% số trang done); tỷ lệ done theo domain trong mẫu chỉ là ước lượng.

## 6. Tập câu hỏi công khai (`query.parquet`)

1.200 câu, `id` 1-1.200, không trùng, 100% có dấu tiếng Việt, 0 câu có chữ Hán. Độ dài ký tự min/trung vị/TB/P95/max = 18/81/129,5/364/1.243; số từ trung vị 18, TB 29,9 (khớp README dataset). Câu hỏi đều tiếng Việt trong khi ~71-85% trang done tiếng Trung (kể cả trang bị lỗi mã hóa) → bài toán bắt buộc là truy hồi **xuyên ngôn ngữ Việt → Trung** (ảnh hưởng chọn model embedding ở Giai đoạn 4).

## 7. Mẫu số corpus

README dataset ghi 4.420.561 liên kết, id 1-4.420.561; `links_corpus.parquet` thực tế 4.394.718 dòng, id 583-4.420.561 (thiếu 25.843 id). Nguyên nhân CHƯA xác định; user quyết định không hỏi BTC (09/10).

## 8. Điều chưa đo

Tỷ lệ trùng lặp/placeholder toàn corpus; tỷ lệ y khoa thật (cần gán nhãn thủ công một mẫu nhỏ); phân loại 262.927 dòng banned chưa gán domain (đã không còn ý nghĩa vì banned bỏ qua); nguyên nhân tách rời leaf page làm quét tuần tự chậm.
