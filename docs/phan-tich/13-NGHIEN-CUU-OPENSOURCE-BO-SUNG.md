# Nghiên cứu Open-source Bổ sung: Đối chiếu 4 Quyền Tự chủ BTC với Corpus Thật

Tài liệu rà soát xem trong 4 điểm BTC trao quyền tự chủ cho đội thi (mô hình embedding, chiến lược lập chỉ mục, cơ chế reranking, dữ liệu mở bổ trợ) còn điểm nào chưa được nghiên cứu phù hợp với corpus THẬT đã xác nhận (chỉ Việt + Trung, ~4,39 triệu tài liệu, 63%+ là các site hỏi-đáp y tế Trung Quốc — xem [12-KE-HOACH-KHOI-DONG-VA-MINDSET-THANG-10.md](12-KE-HOACH-KHOI-DONG-VA-MINDSET-THANG-10.md)).

---

## 1. Mô hình embedding: xác nhận lựa chọn hiện tại vẫn là "mặc định phổ biến nhất" 2026

Tra cứu xác nhận: **đa số hệ thống RAG production 2026 vẫn mặc định dùng `BGE-M3` + `BGE-reranker-v2`** — không phải lựa chọn lỗi thời. BGE-M3 (MIT license, 100+ ngôn ngữ, hỗ trợ đồng thời dense/sparse/multi-vector trong 1 model) tiếp tục là "workhorse" tiêu chuẩn, trong khi `Qwen3-Embedding-8B` dẫn đầu thuần về điểm benchmark MTEB nhưng không phải lựa chọn mặc định phổ biến nhất. => **Giữ nguyên quyết định ở doc 03/10, không cần đổi baseline.**

**Phát hiện mới đáng giá — ứng viên chuyên biệt tiếng Trung y tế**: `CMedTEB` (Chinese Medical Text Embedding Benchmark) đi kèm model `CARE` (Chinese medical Asymmetric REtriever) — kiến trúc bất đối xứng (query encoder nhẹ + document encoder mạnh), đạt SOTA trên benchmark y tế tiếng Trung, mã nguồn + model đã mở. Vì **63%+ corpus là nội dung hỏi-đáp y tế tiếng Trung** (120ask.com, 39.net, cnkang.com, familydoctor.com.cn), CARE là ứng viên đáng thử nghiệm A/B cùng BGE-M3 trên riêng phần corpus tiếng Trung — **CẦN THỰC NGHIỆM đo trên mock dev set tiếng Trung** trước khi quyết định, không thay baseline khi chưa đo.

---

## 2. Dữ liệu mở bổ trợ hợp pháp: đã xác định đúng theo NGÔN NGỮ corpus thật

BTC cho phép dùng "các tập dữ liệu mở khác về y học... để huấn luyện/đánh giá bổ trợ" ([01-THONG-TIN-CUOC-THI.md](01-THONG-TIN-CUOC-THI.md) mục 4). Doc 04 trước đây liệt kê PubMedQA/MedMCQA/BioASQ — toàn bộ tiếng Anh, **không khớp corpus thật (không có tiếng Anh)**. Đã sửa tại doc 04 mục 4, thay bằng:

| Dataset | Ngôn ngữ | Quy mô | Nguồn gốc | Link |
| :--- | :--- | :---: | :--- | :--- |
| `tarudesu/ViHealthQA` | Việt | 10.015 cặp Q-A | Hỏi-đáp từ các trang sức khỏe tiếng Việt (văn phong rất giống `query.parquet` của BTC) | [Hugging Face](https://huggingface.co/datasets/tarudesu/ViHealthQA) |
| `webMedQA` | Trung | 63.284 câu hỏi | **120Ask + Baidu Doctor** | [GitHub](https://github.com/hejunqing/webMedQA) |
| `cMedQA2` | Trung | 108.000 câu hỏi, 203.569 câu trả lời | Forum hỏi-đáp y tế cộng đồng Trung Quốc | [Awesome-Medical-Dataset](https://github.com/openmedlab/Awesome-Medical-Dataset/blob/main/resources/cMedQA.md) |
| `FreedomIntelligence/Huatuo26M-Lite` | Trung | Rút gọn từ 26 triệu cặp Q-A | Tư vấn y tế trực tuyến + 39Health-KG + CPubMed-KG + Xywy-KG | [Hugging Face](https://huggingface.co/papers/2305.01526) |

---

## 3. Phát hiện quan trọng cần hành động: `webMedQA` có thể trùng trực tiếp nguồn với `120ask.com` trong corpus

`webMedQA` ghi rõ nguồn thu thập là **"120Ask"** — đây rất có thể chính là `www.120ask.com`, domain chiếm **918.479 URL (~21% tổng corpus)**. Nếu đúng, `webMedQA` có thể đã chứa sẵn **nội dung text đã làm sạch** của một phần lớn các trang `120ask.com` mà hệ thống đang phải tự crawl — một cơ hội tiết kiệm thời gian crawl đáng kể cho domain lớn thứ 2 của corpus.

**[ĐÃ KIỂM TRA 01/10/2026]** Đọc trang GitHub chính thức của `webMedQA`: dataset được đóng gói theo format "mỗi câu hỏi kèm 1 câu trả lời đúng + 4 câu trả lời nhiễu" (Train 50.610 / Dev 6.337 / Test 6.337 câu hỏi) — đây là format dataset **huấn luyện mô hình matching/ranking QA**, không phải bản lưu trữ nguyên trang web, nên **khả năng cao KHÔNG giữ lại URL gốc hoặc ID liên kết trực tiếp tới `120ask.com`** (README không công bố schema field cụ thể, cần tải file ZIP thật mới khẳng định chắc chắn 100%, nhưng định dạng "1 positive + 4 negative answers" là dấu hiệu rõ của dataset matching, không phải page-archive).

=> **Kết luận: không dùng làm shortcut bỏ qua crawl.** Vẫn hữu ích đúng theo mục đích ban đầu — làm nguồn xây mock dev set tiếng Trung (mục 2) — nhưng không nên kỳ vọng tiết kiệm được công crawl domain `120ask.com`. Tiếp tục để `url_crawler.py` tự crawl toàn bộ như kế hoạch.

---

## 4. Chiến lược lập chỉ mục & reranking: không có phát hiện mới cần đổi

Rà soát lại không tìm thấy kỹ thuật lập chỉ mục/reranking phổ biến mới nào vượt trội hơn những gì đã chốt ở doc 10/11 (Tantivy BM25 + BGE-M3 Dense + RRF fusion, BGE-reranker-v2-m3, Binary/Scalar Quantization cho vector index quy mô lớn). Giữ nguyên kiến trúc đã thiết kế.

---

## 5. Việc cần làm tiếp theo (song song với crawl)

1. Tải và kiểm tra schema `webMedQA` — xác minh khả năng trùng nguồn với `120ask.com` (mục 3).
2. Tải `tarudesu/ViHealthQA` làm nguồn chính xây mock dev set tiếng Việt.
3. Khi crawl đạt ngưỡng đủ dữ liệu tiếng Trung (sau khi vượt qua vùng `id` thấp toàn tiếng Việt), thử nghiệm CARE/CMedTEB A/B với BGE-M3 trên phần corpus tiếng Trung.

---

## 6. Nguồn tham khảo

- [CMedTEB & CARE: Benchmarking and Enabling Efficient Chinese Medical Embedding](https://arxiv.org/pdf/2604.10937)
- [Best Embedding Models for RAG in 2026 — xác nhận BGE-M3 là lựa chọn mặc định production](https://airbyte.com/agentic-data/best-embedding-models-rag)
- [tarudesu/ViHealthQA (Hugging Face)](https://huggingface.co/datasets/tarudesu/ViHealthQA)
- [webMedQA (GitHub)](https://github.com/hejunqing/webMedQA)
- [cMedQA2 (Awesome-Medical-Dataset)](https://github.com/openmedlab/Awesome-Medical-Dataset/blob/main/resources/cMedQA.md)
- [Huatuo-26M (GitHub)](https://github.com/FreedomIntelligence/Huatuo-26M)
