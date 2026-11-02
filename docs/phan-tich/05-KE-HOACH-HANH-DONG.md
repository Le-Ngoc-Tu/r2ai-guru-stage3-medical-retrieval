# Kế hoạch Hành động: Lộ trình Chuẩn bị và Thực thi Stage 3

Lộ trình hành động từng bước theo thời gian từ ngày hiện tại (18/09/2026) đến khi công bố kết quả chung cuộc (11/11/2026).

> Xem [12-KE-HOACH-KHOI-DONG-VA-MINDSET-THANG-10.md](12-KE-HOACH-KHOI-DONG-VA-MINDSET-THANG-10.md) để biết trạng thái thực tế đã kiểm tra (29/09/2026) của Giai đoạn 0 dưới đây và checklist cụ thể cần hoàn thành trước 01/10.

---

## 1. Các giai đoạn thực thi theo mốc thời gian

```
[18/09 - 30/09/2026] Chuẩn bị hạ tầng, mock dev set & script F2 tách tầng
        |
        v
[01/10 - 31/10/2026] Public Test: Nhận KB + Test, dựng chỉ mục, tối ưu 10 bài/ngày
        |
        v
[01/11 - 04/11/2026] Private Test: Chạy trên tập kiểm thử cuối, chọn lọc 5 bài nộp
        |
        v
[05/11 - 11/11/2026] Viết Working Notes Paper & bảo vệ kết quả
```

---

## 2. Giai đoạn 0: Chuẩn bị trước khi mở đề (18/09 - 30/09/2026)

Mục tiêu: Dựng sẵn toàn bộ bộ khung phần mềm, script đánh giá và hạ tầng để khi Ban Tổ chức mở dữ liệu ngày 01/10/2026 là bắt tay vào lập chỉ mục ngay lập tức.

1. Xây dựng bộ script đánh giá Macro F2 hai tầng (`eval_f2.py`):
   - Cài đặt đúng công thức tính Precision, Recall và F2 cho Document và Chunk.
   - Hỗ trợ đo tách tầng: tỷ lệ tìm đúng tài liệu, tỷ lệ chọn đúng chunk trong tài liệu đã đúng, độ lệch index của chunk.
2. Xây dựng module đóng gói và kiểm tra bài nộp (`validate_submission.py`):
   - Kiểm tra cấu trúc JSON: danh sách đối tượng chứa đủ 3 trường `id`, `relevant_docs`, `relevant_chunks`.
   - Kiểm tra không có mã trùng lặp trong danh sách, tự động đóng gói 1 file JSON duy nhất vào file ZIP.
3. Chuẩn bị kho từ điển y khoa đa ngôn ngữ (MeSH / UMLS):
   - Thu thập bộ từ điển Anh - Việt - Trung cho các thực thể bệnh lý, triệu chứng, hoạt chất thuốc phổ biến.
4. Thiết lập công cụ lập chỉ mục quy mô lớn (Tantivy):
   - Viết sẵn script nạp file JSONL hàng chục triệu chunk vào Tantivy index trên ổ cứng, hỗ trợ tokenizer tiếng Việt, tiếng Trung và tiếng Anh.
5. Tạo bộ dữ liệu kiểm thử giả lập (Mock Dev Set):
   - Trích 500 đoạn y văn mẫu đa ngôn ngữ kèm 100 câu hỏi giả lập để kiểm tra toàn bộ luồng code từ đầu đến cuối.

---

## 3. Giai đoạn 1: Public Test Phase (01/10 - 31/10/2026)

Mục tiêu: Lập chỉ mục toàn bộ kho dữ liệu thật, thực hiện các đợt nộp bài hàng ngày (tối đa 10 bài/ngày) để tìm ra cấu hình ngưỡng tối ưu nhất.

1. Ngày 01/10 - 03/10:
   - Tải kho tài liệu KB và tập test công khai.
   - Kiểm tra cấu trúc thực tế của KB (kích thước file, độ dài chunk trung bình, phân bố ngôn ngữ Vi/En/Zh).
   - Chạy lập chỉ mục Sparse bằng Tantivy trên đĩa SSD (mục tiêu hoàn thành trong vòng 4–8 giờ).
2. Ngày 04/10 - 10/10:
   - Dùng baseline Sparse BM25 đa ngôn ngữ để nộp bài đầu tiên lên leaderboard, kiểm tra độ tương thích 100% của format.
   - Tính toán dense embedding cho các chunk ứng viên bằng BGE-M3 trên GPU cloud (Kaggle/RunPod).
3. Ngày 11/10 - 25/10:
   - Tích hợp Two-tier Reranker (Document Aggregation -> Chunk Reranking kèm context window).
   - Thực nghiệm căn chỉnh các siêu tham số ngưỡng cắt (Dynamic Margin Thresholding) dựa trên điểm leaderboard và mock dev set.
4. Ngày 26/10 - 31/10:
   - Đóng băng pipeline ổn định nhất (Freeze Candidate Pipeline).
   - Chọn lọc 2 hướng tiếp cận tốt nhất: 1 hướng tối ưu độ sâu Recall và 1 hướng cân bằng Precision cao.

---

## 4. Giai đoạn 2: Private Test Phase (01/11 - 04/11/2026)

Mục tiêu: Xử lý tập Private Test và lựa chọn cẩn trọng tối đa 5 bài nộp quyết định thứ hạng chung cuộc.

1. Ngày 01/11:
   - Nhận tập câu hỏi Private Test từ Ban Tổ chức.
   - Kiểm tra phân bố câu hỏi (số lượng câu, độ dài câu hỏi, từ khóa mới).
2. Ngày 02/11 - 03/11:
   - Chạy pipeline đã đóng băng để sinh kết quả.
   - Thực hiện semantic audit trên các câu lệch lớn để đảm bảo không có lỗi định dạng hay lỗi mã chunk không tồn tại.
   - Nộp các bài dự đoán theo chiến lược đã định sẵn:
     - Bài 1: Baseline an toàn (Cân bằng P-R tốt nhất ở Public Test).
     - Bài 2: Chiến lược tăng cường Recall (Độ rộng chunk cao hơn 15% có chọn lọc).
     - Bài 3: Chiến lược Ensemble (Kết hợp đồng thuận từ nhiều mô hình rerank).
     - Bài 4 & 5: Các biến thể dự phòng tinh chỉnh trên tập private.

---

## 5. Giai đoạn 3: Working Notes Paper (05/11 - 11/11/2026)

Mục tiêu: Hoàn thiện bài báo khoa học mô tả giải pháp để được công nhận kết quả chính thức.

1. Cấu trúc bài báo theo quy chuẩn:
   - Abstract & Introduction: Đặt vấn đề khoảng cách thông tin y tế.
   - Proposed Architecture: Sơ đồ 3 giai đoạn (Query Expansion -> Hybrid Retrieval -> Two-tier Reranking).
   - Experimental Setup: Mô tả các mô hình mã nguồn mở đã dùng (BGE-M3, Tantivy, BGE-Reranker, Qwen2.5), cách trích xuất ngữ cảnh $\pm 1$.
   - Results & Discussion: Bảng kết quả Public Test, phân tích ảnh hưởng của chỉ số F2 và lỗi trượt cửa sổ chunk.
   - Conclusion: Tổng kết bài học và hướng phát triển.
2. Hoàn tất và nộp bài trước hạn chót ngày 11/11/2026.
