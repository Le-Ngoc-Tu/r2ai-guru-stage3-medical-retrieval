# Phương pháp đánh giá và Giải phẫu độ đo Macro F2

Tài liệu phân tích toán học chỉ số macro F2 trên hai cấp độ Document và Chunk, hệ quả của trọng số Recall gấp 4 lần Precision, và chiến lược xác định ngưỡng cắt (cutoff threshold) tối ưu điểm số.

---

## 1. Công thức đánh giá hai cấp độ [ĐÃ CẬP NHẬT 29/09/2026 theo trang Phương pháp đánh giá chính thức của BTC]

Hiệu suất hệ thống được tính riêng biệt ở hai cấp độ, và **hai cấp độ dùng hai công thức Precision/Recall KHÁC NHAU** — đây là điểm cần lưu ý kỹ vì không phải cùng một công thức set-based áp cho cả hai:

### 1.1. Cấp độ tài liệu (Document-level) — set-based trên `doc_id`

Với mỗi truy vấn $q$, gọi $D$ là tập `doc_id` được truy hồi và $G$ là tập `doc_id` liên quan theo nhãn tham chiếu:

$$Precision(q) = \frac{|D \cap G|}{|D|} \qquad Recall(q) = \frac{|D \cap G|}{|G|}$$

### 1.2. Cấp độ đoạn nội dung (Chunk-level) — content overlap trên `chunk_text`, KHÔNG phải set-based trên `chunk_id`

Gọi $C$ là tập `chunk_text` được truy hồi (nội dung text thật do đội thi tự chunking và nộp — xem [01-THONG-TIN-CUOC-THI.md](01-THONG-TIN-CUOC-THI.md) mục 6) và $I$ là tập các phần thông tin cần thiết trong những tài liệu liên quan, do BTC xác định trước cho mỗi câu hỏi.

Một `chunk_text` được tính là **relevant** nếu chứa nội dung tương ứng hoặc overlap đủ với ít nhất một phần tử của $I$:

$$Precision(q) = \frac{\text{Số chunk relevant}}{\text{Tổng số chunk được truy hồi } (|C|)} \qquad Recall(q) = \frac{\text{Số phần tử của } I \text{ được bao phủ}}{|I|}$$

Khác biệt cốt lõi so với Document-level: mẫu số của Recall là **số phần thông tin cần thiết** ($|I|$), không phải số chunk gold — một phần thông tin có thể được bao phủ bởi chunk dài hơn hoặc chunk ngắn overlap đúng phần lõi, miễn nội dung khớp/overlap đủ. Độ dài mỗi `chunk_text` khuyến nghị **không quá ~1.024 tokens**.

**[ĐÍNH CHÍNH 14/10/2026, từ trang Phương pháp đánh giá chính thức 3.3]** Recall chunk-level là $\dfrac{	ext{số chunk tham chiếu đã được tìm thấy}}{	ext{tổng số chunk tham chiếu}}$ (mẫu số là số **chunk tham chiếu** của BTC, không phải số "phần thông tin cần thiết" như mô tả ở trên); Precision là số chunk nộp được tính đúng chia tổng chunk nộp. Chunk nộp chỉ được đối chiếu với chunk tham chiếu cùng truy vấn và cùng `doc_id`.

**[CẬP NHẬT 12/10/2026, luật khớp chunk chính thức của BTC]** Chunk nộp `c` khớp chunk tham chiếu `g` khi: cùng truy vấn và cùng `doc_id`; cả hai được chuẩn hóa NFKC, giải mã HTML entity, chữ thường, gộp khoảng trắng; rồi $\text{overlap}(c,g) = \frac{LCS_{tokens}(c,g)}{|g|} \geq 0{,}40$ (LCS giữ thứ tự token nhưng không bắt buộc liên tiếp; mẫu số là độ dài chunk tham chiếu). Cách tách token để tính LCS (đặc biệt tiếng Trung) tài liệu chấm không nêu - CHƯA RÕ. **Hệ quả**: ngưỡng 0,6 theo tỷ lệ token chung (bag-of-words) đang đặt mặc định trong `eval_f2.py` là con số tự đoán, KHÔNG phải luật BTC; đã thay bằng LCS ≥ 0,40 trong `eval_f2.py` (14/10/2026, Giai đoạn 5; chữ Hán tách từng chữ vì slide không nêu cách tách).

Điểm $F_2$ cho mỗi truy vấn $q$ được tính theo công thức (giống nhau cho cả hai cấp độ, chỉ khác cách tính Precision/Recall đầu vào):

$$F_2(q) = \frac{5 \times Precision(q) \times Recall(q)}{4 \times Precision(q) + Recall(q)}$$

Chỉ số cuối cùng trên toàn bộ tập kiểm thử là trung bình cộng (Macro-Average) của tất cả các câu hỏi:

$$Macro\text{-}F_2 = \frac{1}{|Q|} \sum_{q \in Q} F_2(q)$$

Nếu một truy vấn không trả về phần tử nào ($|D| = 0$ hoặc $|C| = 0$), $Precision(q) = 0$, $Recall(q) = 0$ và $F_2(q) = 0$.

---

## 2. Giải phẫu toán học: Recall được coi trọng gấp 4 lần

Công thức tổng quát $F_\beta$ được định nghĩa:

$$F_\beta = (1 + \beta^2) \frac{P \times R}{\beta^2 P + R}$$

Khi Ban Tổ chức chọn $\beta = 2$, trọng số của độ bao phủ (Recall) được nhân đôi trong trung bình điều hòa, dẫn đến việc Recall đóng góp vào hàm mục tiêu với trọng số gấp $\beta^2 = 4$ lần so với Precision.

### Bảng độ nhạy điểm số $F_2$

Giả sử một truy vấn có $|I| = 2$ phần thông tin cần thiết (mỗi phần được bao phủ đúng bởi 1 chunk relevant). Bảng dưới đây so sánh các kịch bản dự đoán khác nhau (áp dụng công thức Chunk-level ở mục 1.2):

| Kịch bản dự đoán | Chunk relevant | Tổng chunk trả về ($|C|$) | Precision | Recall | Điểm $F_2$ | Đánh giá |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| Chính xác tuyệt đối | 2 | 2 | 1.00 | 1.00 | **1.000** | Lý tưởng |
| Lấy dư + dư phòng nhẹ | 2 | 3 | 0.67 | 1.00 | **0.909** | Tối ưu thực tế |
| Lấy dư + dư thừa vừa | 2 | 5 | 0.40 | 1.00 | **0.769** | Chấp nhận được vì F2 thích Recall |
| Bỏ sót 1/2 (thiếu) | 1 | 1 | 1.00 | 0.50 | **0.556** | Precision 100% vẫn bị sụp đổ hụt Recall |
| Xả chunk bừa bãi | 2 | 20 | 0.10 | 1.00 | **0.357** | **Thảm họa** do Precision quá thấp |

---

## 3. Cảnh báo: Bài học sụp bẫy "Xả toàn bộ chunk"

Một sai lầm dễ mắc phải khi thấy $F_2$ ưu tiên Recall là: *"Sau khi tìm được doc_id đúng, cứ đưa toàn bộ chunk của doc đó vào danh sách relevant_chunks để ăn trọn Recall".*

Quy chế đã ghi rõ: *"Không suy diễn rằng mọi chunk của một tài liệu liên quan đều liên quan."*

Toán học chứng minh ngay sự sụp đổ của chiến lược này (áp dụng đúng công thức Chunk-level ở mục 1.2: Precision theo số chunk relevant / tổng chunk trả về, Recall theo số phần tử của $I$ được bao phủ):
- Giả sử 1 tài liệu y khoa có 25 chunk, nhưng chỉ có đúng 1 chunk chứa nội dung khớp/overlap với phần thông tin cần thiết ($|I| = 1$).
- Nếu hệ thống xả cả 25 chunk vào kết quả:
  Số chunk relevant $= 1$, $|C| = 25 \implies Precision = 1/25 = 0.04$, $Recall = 1/1 = 1.0$.
  $$F_2 = \frac{5 \times 0.04 \times 1.0}{4 \times 0.04 + 1.0} = \frac{0.20}{0.16 + 1.0} = \frac{0.20}{1.16} \approx \mathbf{0.172}$$
- Trong khi nếu hệ thống chỉ chọn 3 chunk có điểm rerank cao nhất (chứa chunk relevant đó):
  Số chunk relevant $= 1$, $|C| = 3 \implies Precision = 1/3 = 0.333$, $Recall = 1.0$.
  $$F_2 = \frac{5 \times 0.333 \times 1.0}{4 \times 0.333 + 1.0} = \frac{1.667}{1.333 + 1.0} = \frac{1.667}{2.333} \approx \mathbf{0.714}$$

Điểm số giảm từ **0.714 xuống 0.172** (giảm hơn 4 lần) nếu cố tình trả về dư thừa vô tội vạ.

---

## 4. Đối chiếu thực nghiệm Stage 2: Ba hướng đi về quy mô trả về


---

## 5. Chiến lược Dynamic Thresholding cho Stage 3

Không dùng Top-K cố định (ví dụ lúc nào cũng lấy đúng 3 chunks). Số lượng bằng chứng y học thay đổi tùy theo truy vấn: có câu chỉ cần 1 chunk định nghĩa, có câu cần 3–5 chunk tổng hợp nhiều triệu chứng và phác đồ.

Thuật toán cắt ngưỡng cần kết hợp 2 điều kiện:
1. Ngưỡng điểm tối thiểu (Absolute Score Threshold): Chỉ lấy các ứng viên có điểm rerank $\ge T_{min}$.
2. Khoảng cách điểm tương đối (Relative Margin Threshold): Chỉ lấy ứng viên nếu điểm của nó không chênh lệch quá $\Delta_{max}$ so với ứng viên hạng 1:
   $$Score(chunk_i) \ge \max(Scores) - \Delta_{margin}$$
3. Giới hạn an toàn: Đặt trần $K_{max} = 5$ chunk và $K_{doc} = 3$ doc cho mỗi truy vấn để chặn tụt Precision.

**[ĐÍNH CHÍNH 14/10/2026, từ kết quả chấm thật]** Trần $K_{max}=5$ / $K_{doc}=3$ ở trên SAI cho Stage 3. Bộ chấm cho thấy mỗi câu có trung bình ~71 doc (trung vị 60, tối đa 190) và ~75 chunk tham chiếu; trả 3 doc chỉ đạt Recall doc 0,03 và FINAL 0,0253 (mốc BM25 của BTC 0,3764). Số lượng cần trả phải tính từ đường cong F2 theo K trên điểm thật, không phải từ Stage 2. Xem AGENTS.md §3c (14/10/2026).
