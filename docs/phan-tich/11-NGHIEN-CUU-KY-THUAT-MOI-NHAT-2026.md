# Nghiên cứu Kỹ thuật Mới nhất (2026) và Lựa chọn Phù hợp Phần cứng RTX 3050 6GB

Tài liệu tổng hợp kết quả tra cứu các kỹ thuật retrieval/embedding/reranking mới nhất hiện nay (WebSearch, không suy đoán từ trí nhớ huấn luyện), đối chiếu với ràng buộc phần cứng thực tế (RTX 3050 6GB VRAM, RAM 16GB, không Cloud GPU) và ràng buộc thể lệ (model ≤15B tham số/model riêng lẻ, mã nguồn mở, công bố trước 01/08/2026 — xem [01-THONG-TIN-CUOC-THI.md](01-THONG-TIN-CUOC-THI.md)).

Nguyên tắc chọn lọc: chỉ đưa vào đây kỹ thuật đã có nguồn tham khảo cụ thể (link ở mục 8) và đã đối chiếu rõ chi phí VRAM/RAM. Những gì chưa tự kiểm chứng được (ví dụ checkpoint y khoa cụ thể) được đánh dấu rõ "CẦN THỰC NGHIỆM" thay vì khẳng định.

---

## 1. Mô hình Dense Embedding: giữ BGE-M3 làm nền, thêm 1 ứng viên nhẹ để thử nghiệm fusion

- **Giữ nguyên baseline: `BAAI/bge-m3`** (567M tham số, ~2.2GB VRAM fp16, context 8192 token, multilingual native Vi/En/Zh). Đây vẫn là lựa chọn an toàn nhất, đã được benchmark kỹ trong 07-NGHIEN-CUU-RERANKING-AI-GURU.md. Không có bằng chứng nào từ nghiên cứu mới đủ mạnh để thay hẳn baseline này.
- **Ứng viên đáng thử nghiệm thêm: `Qwen/Qwen3-Embedding-0.6B`** (639MB download, ước tính ~1–1.5GB VRAM). Cùng họ với Qwen3-Embedding-8B đang dẫn đầu MTEB Multilingual (70.58 điểm, 05/06/2025), có hỗ trợ **Matryoshka Representation Learning (MRL) gốc** — cho phép cắt giảm số chiều embedding mà không cần train lại, rất hợp với bài toán phải lưu 10–100 triệu vector.
  - **Rủi ro cần lưu ý**: Qwen3-Embedding-4B/8B cho điểm MTEB cao hơn hẳn nhưng cần 8–16GB VRAM ở fp16 — vượt ngân sách 6GB nếu không quantize (bản GGUF Q4_K_M của 4B chỉ ~2.5GB, khả thi nhưng CHƯA CÓ benchmark công khai nào đánh giá Qwen3-Embedding trên tác vụ retrieval y sinh đa ngôn ngữ Vi/En/Zh — khác hẳn domain huấn luyện gốc của nó.
  - **Cách thử nghiệm cụ thể (không thay baseline ngay)**: Thêm Qwen3-Embedding-0.6B như **tín hiệu fusion thứ 3** trong công thức RRF ở Giai đoạn 4 (bên cạnh Tantivy BM25 + BGE-M3 Dense). Vì mô hình nhỏ và chạy tuần tự (không nạp cùng lúc với BGE-M3), không tốn thêm VRAM đỉnh, chỉ tốn thêm thời gian batch. Đo $F_{2,doc}$ và $F_{2,chunk}$ tách tầng trên mock dev set trước/sau khi thêm tín hiệu này để quyết định giữ hay bỏ — đúng tinh thần Verification-Driven Development, không đoán.
- **Checkpoint fine-tune y khoa (MedEmbed, hoặc các claim "MMed-Embed" fine-tune BGE-M3 trên MMedBench/UMLS/xBioASQ)**: CÓ TỒN TẠI trên Hugging Face (ví dụ `abhinand/MedEmbed-*`) nhưng **CHƯA XÁC MINH được** các checkpoint này có hỗ trợ đa ngôn ngữ Vi/En/Zh hay chỉ tối ưu tiếng Anh, và license cụ thể ra sao. Không đổi baseline sang các checkpoint này khi chưa tự tay tải về, đọc model card (ngôn ngữ hỗ trợ, license) và đo $F_2$ trên mock dev set — đây là sự thật kiểm chứng được bằng thực nghiệm, không phải quyết định sản phẩm, nên phải tự đo trước khi quyết, không suy đoán.

---

## 2. Mô hình Reranker: giữ BGE-reranker-v2-m3, thêm 2 ứng viên A/B test

- **Giữ nguyên baseline: `BAAI/bge-reranker-v2-m3`** (560M, ~4.0–4.5GB VRAM ở `batch_size=16–32` trên RTX 3050) — đã tính toán kỹ trong doc 07, tiếp tục là lựa chọn an toàn nhất.
- **Ứng viên 1 — `Qwen/Qwen3-Reranker-0.6B`**: reranker sinh (generative pointwise) cùng họ Qwen3, siêu nhẹ (0.6B), **license Apache 2.0** (mở hoàn toàn). Có thể A/B test song song với BGE-reranker-v2-m3 trên mock dev set vì kích thước tương đương.
- **Ứng viên 2 — `jinaai/jina-reranker-v2-base-multilingual`**: một nghiên cứu so sánh multilingual reranker trích dẫn model này cho "kết quả macro tốt nhất", hỗ trợ tới 1024 token. Model này dùng license **CC-BY-NC 4.0** (phi thương mại), không phải Apache 2.0 như bge-reranker-v2-m3 — **nhưng [XÁC NHẬN CHÍNH THỨC 29/09/2026] BTC chỉ yêu cầu model "được công khai" (open weight, có trên Hugging Face hoặc kho tương tự) và không phải LLM đóng qua API thương mại, KHÔNG yêu cầu license phải cho phép mục đích thương mại** (xem [01-THONG-TIN-CUOC-THI.md](01-THONG-TIN-CUOC-THI.md) mục 4). Vì vậy model này hợp lệ để dùng, không cần hỏi lại BTC — chỉ cần benchmark trên mock dev set như các ứng viên khác.
- **ColBERT-style late-interaction siêu nhẹ** (ví dụ dòng "colbert-hash-nano" ~1M tham số): kỹ thuật thú vị làm tầng lọc trung gian rẻ giữa RRF và Cross-Encoder đầy đủ (nén token embedding bằng centroid-residual quantization, giảm 10× dung lượng lưu so với ColBERT gốc). Đây là **bổ sung kiến trúc mới** (thêm 1 tầng "1.5"), không cần thiết ngay nếu Dynamic Thresholding hiện tại đã đủ tốt — chỉ nên cân nhắc nếu benchmark cho thấy Top-500 candidates sau RRF vẫn còn quá nhiều nhiễu trước khi vào Cross-Encoder.

---

## 3. Chunking: Contextual Retrieval — nâng cấp cụ thể, chi phí gần như bằng 0

Kỹ thuật **Contextual Retrieval** (Anthropic) — báo cáo giảm tới 67% lỗi top-20 khi kết hợp với reranking — đơn giản hơn nhiều so với **Late Chunking** (Jina) và không cần thay đổi model:

- **Khác biệt quan trọng so với thiết kế hiện tại**: Tài liệu [03-MINDSET-KE-THUA-STAGE2.md](03-MINDSET-KE-THUA-STAGE2.md) và [04-KIEN-TRUC-HE-THONG-Y-KHOA.md](04-KIEN-TRUC-HE-THONG-Y-KHOA.md) hiện chỉ nối ngữ cảnh (`chunk_index ±1`) ở **tầng Rerank (Cross-Encoder)**. Contextual Retrieval khuyến nghị nối một đoạn ngữ cảnh ngắn (tiêu đề tài liệu + tên mục cha) vào **ĐẦU text của chunk NGAY TỪ KHI TẠO DENSE EMBEDDING ở Tầng 1** — giúp cải thiện luôn Recall của tầng lọc thô, không chỉ độ chính xác tầng rerank.
- **Chi phí thực thi**: gần như 0 VRAM thêm — chỉ là string concatenation từ metadata (`doc_title`, tiêu đề mục cha) đã có sẵn theo thiết kế chunking hiện tại (mục 3.3 trong [08-THAY-DOI-THE-LE-DATA-PIPELINE.md](08-THAY-DOI-THE-LE-DATA-PIPELINE.md)). Bản gốc của Anthropic dùng LLM sinh câu ngữ cảnh cho từng chunk (tốn thêm 1 lượt gọi LLM/chunk — không khả thi cho 10-100 triệu chunk trên 1 GPU cá nhân), nhưng bản rút gọn chỉ ghép metadata tĩnh (không gọi LLM) đã giữ được phần lớn lợi ích với chi phí thấp hơn rất nhiều — phù hợp ràng buộc phần cứng của dự án.
- **Late Chunking (Jina)**: khả thi về lý thuyết vì BGE-M3 có context 8192 token (đủ để embed toàn văn bản trước khi tách chunk), nhưng phức tạp hơn để cài đúng (cần mean-pooling token-level embedding theo đúng offset từng chunk) và nghiên cứu cho thấy độ đầy đủ (completeness) kém hơn Contextual Retrieval. **Không đề xuất áp dụng** trừ khi thực nghiệm trên mock dev set cho thấy Contextual Retrieval (bản rút gọn) không đủ.

---

## 4. Vấn đề cốt lõi phần cứng CHƯA được giải quyết trong thiết kế cũ: RAM lưu vector cho 30–100 triệu chunk

Tài liệu 07 mục 5 Hướng 4 đã cảnh báo đúng hướng nhưng chưa đưa ra giải pháp cụ thể: **30 triệu chunk × 1024 chiều float16 ≈ 60GB RAM** nếu giữ nguyên vector gốc — vượt xa 16GB RAM máy cá nhân dù có streaming ghi ra Qdrant/Faiss, vì chính các vector store này cũng cần nạp index vào RAM khi search.

**Kỹ thuật mới áp dụng được ngay: Embedding Quantization (scalar int8 / binary)** — thư viện `sentence-transformers` đã có sẵn hàm `quantize_embeddings` hỗ trợ cả hai chế độ:
- Scalar quantization (float32 → int8): giảm dung lượng 4 lần.
- Binary quantization: giảm dung lượng tới 32 lần.

**Kiến trúc cụ thể đề xuất cho Giai đoạn 4 (Candidate Retrieval)** — pattern "binary index + float rescore" mà Vespa và Sentence-Transformers đều khuyến nghị:
1. Lưu **2 bản vector** cho mỗi chunk: bản binary/int8 (cho lọc thô quy mô lớn) và bản float16 gốc (chỉ giữ lại cho các ứng viên đã qua lọc thô — vài trăm/câu).
2. Tầng lọc thô Top 200–500: dùng Faiss `IndexBinaryFlat` hoặc `IndexScalarQuantizer` trên toàn bộ corpus. Với 30 triệu chunk, vector binary 1024-bit chỉ chiếm **~3.75GB RAM** — vừa khít trong 16GB máy cá nhân, so với ~60GB nếu giữ float16 gốc.
3. Rescoring chính xác: chỉ với các ứng viên đã qua lọc thô (vài trăm/câu), tải lại vector float16 gốc để tính cosine similarity chính xác trước khi đưa vào Cross-Encoder.

Đây là thay đổi kỹ thuật **có tác động cao nhất** tới khả năng chạy được trên 16GB RAM ở quy mô hàng chục triệu chunk mà BTC công bố — nên đưa vào thiết kế Giai đoạn 4 ngay, không phải "nice-to-have" tùy chọn.

---

## 5. Model dịch/mở rộng truy vấn (Query Expansion LLM): xác nhận lựa chọn hiện tại vẫn đúng

Tra cứu xác nhận: `Qwen2.5-7B-Instruct` bản GGUF `Q4_K_M` chiếm khoảng **4.5–5GB VRAM**, chạy tốt trên RTX 3050 6GB (compute capability 8.0+ đạt yêu cầu), miễn giảm context window xuống ~2048 token để dành chỗ cho KV cache.

**Kết luận**: giữ nguyên `Qwen2.5-1.5B-Instruct` (siêu nhẹ, ~1.1GB VRAM) làm mặc định cho Giai đoạn 3 như đã chốt trong [10-CHIEN-LUOC-HARDWARE-LOCAL-6GB.md](10-CHIEN-LUOC-HARDWARE-LOCAL-6GB.md), có thể nâng lên `Qwen2.5-7B-Instruct` GGUF Q4_K_M khi cần chất lượng dịch thuật/trích xuất thuật ngữ y khoa tốt hơn — cả hai đều nằm trong ngân sách 6GB VRAM vì Giai đoạn 3 chạy độc lập, không nạp cùng lúc với model embedding/rerank.

---

## 6. Bảng tổng hợp quyết định

| Thành phần | Quyết định | Model đề xuất | VRAM/RAM ước tính | Cần thực nghiệm trước khi chốt? |
| :--- | :--- | :--- | :--- | :--- |
| Dense Embedding (baseline) | Giữ nguyên | `BAAI/bge-m3` | ~2.2GB VRAM | Không — đã vetted |
| Dense Embedding (fusion phụ, thử nghiệm) | Thêm để đo, chưa thay baseline | `Qwen/Qwen3-Embedding-0.6B` | ~1–1.5GB VRAM (chạy tuần tự) | **Có** — đo F2 trước/sau khi thêm fusion |
| Embedding fine-tune y khoa | Chưa dùng | MedEmbed / claim "MMed-Embed" | Chưa rõ | **Có** — verify ngôn ngữ + license trước |
| Cross-Encoder Reranker (baseline) | Giữ nguyên | `BAAI/bge-reranker-v2-m3` | ~4.0–4.5GB VRAM | Không — đã vetted |
| Reranker (A/B test) | Thử nghiệm | `Qwen/Qwen3-Reranker-0.6B` | Tương đương baseline | **Có** — A/B trên mock dev set |
| Reranker (A/B test) | Thử nghiệm | `jinaai/jina-reranker-v2-base-multilingual` (license CC-BY-NC, đã xác nhận hợp lệ với thể lệ) | Tương đương baseline | **Có** — chỉ cần benchmark trên mock dev set |
| Chunking | Nâng cấp | Contextual Retrieval (metadata tĩnh, không gọi LLM) | ~0 chi phí thêm | **Có** — đo Recall tầng 1 trước/sau |
| Vector Index quy mô lớn | Nâng cấp bắt buộc | Faiss Binary/Scalar Quantization + float rescore | 30M chunk: ~3.75GB RAM (binary) vs ~60GB (float16) | Không — nguyên lý đã kiểm chứng rộng rãi, chỉ cần implement đúng |
| Query Expansion LLM | Giữ nguyên | `Qwen2.5-1.5B-Instruct` (mặc định) / `Qwen2.5-7B-Instruct` Q4_K_M (nâng cấp) | ~1.1GB / ~4.5–5GB VRAM | Không — đã vetted |

---

## 7. Việc cần làm tiếp (theo Verification-Driven Development)

1. Cài `sentence-transformers` bản mới nhất, viết script đo thử `quantize_embeddings` (binary + scalar) trên 500 chunk mock data — đo dung lượng thực tế và Recall@50 so với float16 gốc trước khi áp dụng toàn corpus.
2. Sửa `medical_chunker.py` (mục 5 doc 08) để prepend metadata tĩnh (`doc_title` + tên mục cha) vào đầu `text` trước khi embed — đo lại $F_{2,doc}$ trên mock dev set.
3. Chạy song song BGE-M3 vs Qwen3-Embedding-0.6B như 2 tín hiệu fusion độc lập trong RRF — so sánh $F_{2,chunk}$.
4. A/B test BGE-reranker-v2-m3 vs Qwen3-Reranker-0.6B vs jina-reranker-v2-base-multilingual trên cùng mock dev set, cùng batch size (cả 3 đều hợp lệ về thể lệ, không cần hỏi BTC thêm).

---

## 8. Nguồn tham khảo

- [Best Embedding Models for RAG (2026)](https://www.premai.io/blog/best-embedding-models-for-rag-2026-ranked-by-mteb-score-cost-and-self-hosting/)
- [MTEB Leaderboard 2026](https://www.codesota.com/benchmarks/mteb)
- [Qwen3 Embedding (GitHub)](https://github.com/QwenLM/Qwen3-Embedding)
- [Qwen3 Embedding paper](https://arxiv.org/pdf/2506.05176)
- [Qwen/Qwen3-Reranker-0.6B (Hugging Face)](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B)
- [Top 7 Rerankers for RAG](https://www.analyticsvidhya.com/blog/2025/06/top-rerankers-for-rag/)
- [jinaai/jina-reranker-v2-base-multilingual (Hugging Face)](https://huggingface.co/jinaai/jina-reranker-v2-base-multilingual)
- [MMed-Bench-IR: Multilingual Medical Information Retrieval](https://arxiv.org/pdf/2606.24200)
- [MedEmbed: Fine-Tuned Embedding Models for Medical/Clinical IR](https://huggingface.co/blog/abhinand/medembed-finetuned-embedding-models-for-medical-ir)
- [From RAG to Context - 2025 year-end review](https://ragflow.io/blog/rag-review-2025-from-rag-to-context)
- [Anthropic Contextual Retrieval — trích dẫn qua RAGFlow review](https://ragflow.io/blog/rag-review-2025-from-rag-to-context)
- [Matryoshka Embeddings Explained (2026)](https://dataaspirant.com/blog/matryoshka-embeddings/)
- [Scaling Vector Search: Quantization and Matryoshka Embeddings](https://towardsdatascience.com/649627-2/)
- [Matryoshka + Binary vectors — Vespa Blog](https://blog.vespa.ai/combining-matryoshka-with-binary-quantization-using-embedder/)
- [Sentence-Transformers Embedding Quantization docs](https://sbert.net/examples/sentence_transformer/applications/embedding-quantization/)
- [ColBERT-Style Late Interaction](https://www.emergentmind.com/topics/colbert-style-late-interaction)
- [ColBERTv2 Retriever](https://www.emergentmind.com/topics/colbertv2-retriever)
- [Local LLM Hardware Requirements in 2026](https://overchat.ai/ai-hub/llm-hardware-requirements)
- [llama.cpp VRAM Requirements (2026)](https://localllm.in/blog/llamacpp-vram-requirements-for-local-llms)
