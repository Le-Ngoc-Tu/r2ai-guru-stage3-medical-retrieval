# Third-Party Notices

R2AI Stage 3 sử dụng các thư viện mã nguồn mở qua `pip` (giấy phép đi kèm trong `.venv/Lib/site-packages/<package>/`, không phân phối lại trong repo này), dùng các mô hình AI mã nguồn mở đã công bố trọng số công khai (không sao chép mã nguồn, chỉ gọi qua `sentence-transformers`/`transformers`), và dùng một bộ dữ liệu do Ban Tổ chức cung cấp theo giấy phép riêng.

**Tính đến 01/10/2026, repo này KHÔNG sao chép/phái sinh trực tiếp mã nguồn của bên thứ ba vào bất kỳ file `.py` nào** — toàn bộ các file trong `src/stage3/` là code tự viết. Mục này tồn tại để minh bạch giấy phép của những gì được **gọi/sử dụng** (không phải "sao chép"), và sẽ được bổ sung đoạn code gốc + giấy phép đầy đủ nếu sau này có dòng nào được sao chép/phái sinh trực tiếp từ nguồn khác (theo đúng yêu cầu của giấy phép loại MIT/Apache/BSD khi phái sinh).

---

## Thư viện Python (`requirements.txt`, đã xác minh qua `pip show` trên venv thật — không suy đoán)

| Thư viện | Giấy phép | Dùng để làm gì |
| :--- | :--- | :--- |
| [httpx](https://github.com/encode/httpx) | BSD-3-Clause | Async HTTP client cho `url_crawler.py` |
| [trafilatura](https://github.com/adbar/trafilatura) | Apache-2.0 | Bóc tách nội dung chính từ HTML |
| [lxml_html_clean](https://github.com/fedora-python/lxml_html_clean) | BSD-3-Clause | Dependency bắt buộc của trafilatura (HTML sanitize) |
| [polars](https://github.com/pola-rs/polars) | MIT | Đọc `links_corpus.parquet`/`query.parquet`, xử lý dữ liệu streaming |
| [orjson](https://github.com/ijl/orjson) | MPL-2.0 và (Apache-2.0 hoặc MIT) — tùy chọn theo người dùng | Parse/serialize JSON hiệu năng cao |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | BSD-3-Clause | Nạp biến môi trường từ `.env` |
| [psutil](https://github.com/giampaolo/psutil) | BSD-3-Clause | Theo dõi RAM/CPU khi chạy pipeline |
| [Tantivy](https://github.com/quickwit-oss/tantivy) (+ binding Python) | MIT | Inverted index BM25 (dự kiến dùng ở Giai đoạn 4) |
| [faiss-cpu](https://github.com/facebookresearch/faiss) | MIT (đọc từ METADATA 1.15.1) | Chỉ mục nhị phân `IndexBinaryFlat` cho dense retrieval |
| [transformers](https://github.com/huggingface/transformers) | Apache-2.0 (5.19.0) | Chạy BGE-M3 và BGE-reranker-v2-m3 |
| [tokenizers](https://github.com/huggingface/tokenizers) | Apache-2.0 (0.23.3) | Đếm token BGE-M3 khi cắt chunk và kiểm tra bài nộp |
| [huggingface_hub](https://github.com/huggingface/huggingface_hub) | Apache-2.0 (2.2.0) | Tải model về cache cục bộ |
| [PyTorch](https://github.com/pytorch/pytorch) | BSD-3-Clause và các giấy phép đi kèm (2.14.1+cu126) | Suy luận trên GPU |
| [NumPy](https://github.com/numpy/numpy) | BSD-3-Clause và các giấy phép đi kèm (2.4.6) | Xử lý vector |
| [crawl4ai](https://github.com/unclecode/crawl4ai) | Apache-2.0 | Fallback crawl trang SPA/JS-rendered (dự kiến, chưa cài — xem [09-DANH-GIA-CONG-CU-CRAWL4AI.md](docs/phan-tich/09-DANH-GIA-CONG-CU-CRAWL4AI.md)) |

---

## Mô hình AI mã nguồn mở (trọng số công khai, gọi qua Hugging Face — không sao chép mã nguồn)

| Model | Giấy phép | Dùng để làm gì |
| :--- | :--- | :--- |
| [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3) | MIT | Dense embedding đa ngôn ngữ (Giai đoạn 4) |
| [BAAI/bge-reranker-v2-m3](https://huggingface.co/BAAI/bge-reranker-v2-m3) | MIT | Cross-Encoder reranker (Giai đoạn 5) |
| [Qwen/Qwen3-Reranker-0.6B](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B) | Apache-2.0 (đọc từ model card) | Dùng trong bài nộp cuối: ghép điểm với BGE-reranker-v2-m3 cho 100 doc đầu mỗi câu |

*(Danh sách sẽ cập nhật nếu đổi/thêm model theo kết quả thực nghiệm — xem [11-NGHIEN-CUU-KY-THUAT-MOI-NHAT-2026.md](docs/phan-tich/11-NGHIEN-CUU-KY-THUAT-MOI-NHAT-2026.md). Mọi model dùng phải thỏa ràng buộc thể lệ ở [AGENTS.md](docs/NHAT-KY-DU-AN.md) mục 4: open-weight, ≤15B tham số, công bố trước 01/08/2026.)*

---

## Dữ liệu (không phải mã nguồn, nhưng có giấy phép riêng cần ghi công)

| Nguồn | Giấy phép | Ghi chú |
| :--- | :--- | :--- |
| [ViBioMIR dataset (MedKB — AI Guru/TiniX)](https://medkb.tinix.ai/) | CC BY-NC 4.0 | `links_corpus.parquet` + `query.parquet` — phi thương mại, yêu cầu ghi công (xem bibtex ở README mục 5) |
| Nội dung crawl từ các site y tế trong `links_corpus.parquet` | Bản quyền của từng trang nguồn | Chỉ dùng cho mục đích nghiên cứu/dự thi, không phân phối lại nội dung thô |

---

## Nguyên tắc cập nhật file này

Mỗi khi thêm một thư viện/model mới vào `requirements.txt` hoặc pipeline: thêm ngay một dòng vào bảng tương ứng ở trên, xác minh giấy phép qua `pip show <package>` (không suy đoán từ tên hoặc trí nhớ — license có thể đổi giữa các version). Nếu có dòng code nào được sao chép/phái sinh trực tiếp từ một nguồn khác (không chỉ import làm dependency), thêm một mục riêng theo đúng format của Stage 2 (`E:\r2ai_guru\THIRD-PARTY-NOTICES.md`): trích dẫn nguyên văn giấy phép gốc đầy đủ, không chỉ ghi tên giấy phép.

---

## Công cụ dựng video giới thiệu (`promo/`, không thuộc pipeline truy hồi)

| Thành phần | Giấy phép | Dùng để làm gì |
| :--- | :--- | :--- |
| [HyperFrames](https://hyperframes.heygen.com) (`hyperframes` trên npm, 0.8.163) | Apache-2.0 (đọc từ `npm view`) | Kết xuất HTML thành video/GIF cho showreel và banner |
| [GSAP](https://gsap.com) (3.14.2, nạp từ CDN khi dựng) | "Standard 'no charge' license" (đọc từ `npm view gsap license`; xem https://gsap.com/standard-license) | Thư viện hoạt họa trong `promo/*/index.html` |
| League Gothic, JetBrains Mono, Noto Sans JP | Font mã nguồn mở (do trình dựng nhúng tự động); giấy phép từng font xem tại Google Fonts | Phông chữ của showreel và banner |
