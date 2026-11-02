# Tổng quan và Kiến trúc R2AI Stage 3

Thư mục này lưu trữ toàn bộ tài liệu phân tích, đặc tả thể lệ, kiến trúc kỹ thuật và kế hoạch hành động cho cuộc thi R2AI GURU STAGE 3 (Nhiệm vụ: Truy hồi tài liệu y khoa đa ngôn ngữ). Toàn bộ tài liệu được kế thừa trực tiếp từ các bài học thực chiến của Stage 2 và hệ thống script đánh giá trong [phan-tich/](../../src/stage3/).

---

## Cấu trúc tài liệu

1. [01-THONG-TIN-CUOC-THI.md](01-THONG-TIN-CUOC-THI.md)
   Đặc tả thể lệ, bối cảnh bài toán khoảng cách thông tin y tế, quy chế PLM mã nguồn mở, định dạng file nộp JSON/ZIP, các mốc thời gian quan trọng và quy định working notes paper.

2. [02-DANH-GIA-VA-CONG-THUC-F2.md](02-DANH-GIA-VA-CONG-THUC-F2.md)
   Giải phẫu toán học công thức macro F2 ở 2 cấp độ: Document và Chunk. Phân tích lý do Recall được coi trọng gấp 4 lần Precision, nguy cơ sụp bẫy khi đoán chunk bừa và chiến lược dynamic thresholding.

3. [03-MINDSET-KE-THUA-STAGE2.md](03-MINDSET-KE-THUA-STAGE2.md)
   Chuyển hóa 6 bài học xương tủy từ Stage 2 sang Stage 3 và **Mục 7: Chốt toàn bộ danh mục công nghệ, thư viện và mô hình sẽ dùng** (trafilatura, crawl4ai, Europe PMC, Tantivy, BGE-M3, BGE-Reranker-v2-m3).

4. [04-KIEN-TRUC-HE-THONG-Y-KHOA.md](04-KIEN-TRUC-HE-THONG-Y-KHOA.md)
   Thiết kế hệ thống truy hồi 2 tầng cho quy mô hàng chục triệu chunk đa ngôn ngữ (Tiếng Việt, Tiếng Anh, Tiếng Trung): lọc thô Sparse (Tantivy/BM25) -> Dense Multilingual Embedding (BGE-M3) -> Two-tier Reranking & Chunk Pinpointing.

5. [05-KE-HOACH-HANH-DONG.md](05-KE-HOACH-HANH-DONG.md)
   Lộ trình thực thi 4 giai đoạn: chuẩn bị trước 01/10/2026, chiến lược nộp 10 bài/ngày ở Public Test (31/10/2026), chiến lược chọn lọc 5 bài ở Private Test (04/11/2026) và hoàn thiện báo cáo giải pháp.

6. [06-QUY-CACH-VA-XU-LY-DU-LIEU.md](06-QUY-CACH-VA-XU-LY-DU-LIEU.md)
   Đặc tả cấu trúc JSONL của Test Set và Kho tri thức đa ngôn ngữ, quy ước định danh `doc_id` / `chunk_id`, kỹ thuật đọc dữ liệu streaming và lập chỉ mục Tantivy trên đĩa.


8. [08-THAY-DOI-THE-LE-DATA-PIPELINE.md](08-THAY-DOI-THE-LE-DATA-PIPELINE.md)
   Giải mã bước ngoặt thể lệ mới nhất (26/09/2026): BTC không cấp chunk sẵn mà yêu cầu tự crawl URL Vi/Zh và tìm kiếm PubMed En qua API; kiến trúc data engineering end-to-end.

9. mock_data.py
   Script tạo bộ dữ liệu mẫu giả lập chuẩn đặc tả Ban Tổ chức (câu hỏi y khoa và các chunk Vi/En/Zh) lưu tại mock_data/.

10. pubmed_client.py
    Module tìm kiếm và thu thập bài báo y sinh PubMed qua Europe PMC REST API, tự động phân đoạn text thành chunk chuẩn format Stage 3.

11. [09-DANH-GIA-CONG-CU-CRAWL4AI.md](09-DANH-GIA-CONG-CU-CRAWL4AI.md)
    Đánh giá chuyên sâu công cụ `unclecode/crawl4ai`: Tính hợp lệ thể lệ, 4 ưu điểm xuất sắc cho RAG Markdown, giới hạn overhead Chromium trên máy 6GB và kiến trúc thu thập lai 2 tầng (httpx + crawl4ai).

12. [10-CHIEN-LUOC-HARDWARE-LOCAL-6GB.md](10-CHIEN-LUOC-HARDWARE-LOCAL-6GB.md)
    Kiến trúc tối ưu 100% trên phần cứng cá nhân (RTX 3050 6GB VRAM, RAM 16GB, Ổ đĩa E): Chia nhỏ thành 5 giai đoạn độc lập không bao giờ gây OOM, danh mục mô hình phù hợp nhất (BGE-M3, BGE-Reranker-v2-m3, Qwen2.5-1.5B).

13. [11-NGHIEN-CUU-KY-THUAT-MOI-NHAT-2026.md](11-NGHIEN-CUU-KY-THUAT-MOI-NHAT-2026.md)
    Rà soát kỹ thuật retrieval/embedding/reranking mới nhất (Qwen3-Embedding/Reranker, Contextual Retrieval, Binary/Scalar Quantization cho vector index quy mô 10-100 triệu chunk), đối chiếu VRAM/RAM thực tế trên RTX 3050 6GB và đề xuất thực nghiệm trước khi đổi baseline.

14. [12-KE-HOACH-KHOI-DONG-VA-MINDSET-THANG-10.md](12-KE-HOACH-KHOI-DONG-VA-MINDSET-THANG-10.md)
    Chốt trạng thái máy thật (venv trống, code còn thiếu module nào), digest nhanh toàn bộ nghiên cứu 01-11, checklist việc phải làm trước 01/10, và mindset thực thi khi bắt đầu Public Test.

15. [13-NGHIEN-CUU-OPENSOURCE-BO-SUNG.md](13-NGHIEN-CUU-OPENSOURCE-BO-SUNG.md)
    Đối chiếu 4 quyền tự chủ BTC (model, index, rerank, dữ liệu mở) với corpus thật (chỉ Việt-Trung): xác nhận BGE-M3+reranker-v2 vẫn là mặc định phổ biến 2026, tìm ra CARE/CMedTEB cho tiếng Trung y tế, và phát hiện `webMedQA` có thể trùng nguồn trực tiếp với domain `120ask.com` (~21% corpus).

---

## Ba nguyên tắc bất biến khi thực thi Stage 3

1. Không suy diễn rằng mọi chunk của tài liệu liên quan đều liên quan: Document đúng không đồng nghĩa với việc nhét toàn bộ chunk vào bài nộp; phải định vị chính xác phần nội dung chứa lời lâm sàng cần thiết.
2. 100% thực thi trên phần cứng cá nhân (Local-Only): Chia nhỏ pipeline thành 5 giai đoạn tuần tự độc lập, tuyệt đối không nạp 2 model cùng lúc vào VRAM, giải phóng bộ nhớ triệt để sau mỗi bước.
3. Dùng đo tách tầng trước khi tối ưu bất cứ thứ gì: Theo dõi độc lập chỉ số ở tầng Document và tầng Chunk trên proxy dev set ngay từ ngày đầu tiên.
