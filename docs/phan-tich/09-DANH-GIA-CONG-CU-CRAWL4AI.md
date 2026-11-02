# Đánh giá Kỹ thuật: Công cụ Crawl4AI cho R2AI Stage 3

Tài liệu đánh giá chuyên sâu thư viện mã nguồn mở `unclecode/crawl4ai` (GitHub: https://github.com/unclecode/crawl4ai) về tính hợp lệ thể lệ, ưu nhược điểm thực tế trên hạ tầng máy cá nhân và kiến trúc tích hợp cho cuộc thi.

---

## 1. Tính hợp lệ theo thể lệ cuộc thi

- **Giấy phép:** Mã nguồn mở hoàn toàn (Apache 2.0), public trên GitHub.
- **Mốc thời gian phát hành:** Phát hành từ đầu năm 2024 (trước mốc giới hạn ngày 01/08/2026 của Ban Tổ chức — xem cập nhật mới nhất tại [01-THONG-TIN-CUOC-THI.md](01-THONG-TIN-CUOC-THI.md)).
- **Quy chế dữ liệu và công cụ:** Thư viện thuần túy xử lý dữ liệu và web scraping, không phải LLM đóng thương mại (như GPT-4o API), do đó **100% HỢP LỆ** theo quy định của Ban Tổ chức.

---

## 2. Bốn ưu điểm vượt trội của Crawl4AI đối với Stage 3

1. **Đầu ra Markdown phân cấp chuẩn cho RAG:**
   Tự động chuyển đổi HTML sang Markdown giữ nguyên tiêu đề (`#`, `##`, `###`), danh sách, bảng biểu và đoạn văn. Đây là đặc điểm quý giá nhất vì giúp hệ thống giữ được ngữ cảnh tiêu đề mục cha khi cắt chunk (đúng theo **Bài học số 3 từ Stage 2: Giữ ngữ cảnh, đừng làm phẳng**).

2. **Tự động lọc bỏ nội dung rác (Boilerplate Stripping):**
   Tích hợp sẵn bộ lọc heuristics loại bỏ menu, navigation bar, chân trang (footer), banner quảng cáo và các liên kết ngoài không liên quan đến nội dung y khoa.

3. **Xử lý tốt các trang Web động (SPA / Dynamic Rendering):**
   Xây dựng trên Playwright/Chromium nên đọc được các trang tin y tế xây dựng bằng React, Vue, Next.js mà các trình request HTTP thông thường (như `requests` hay `curl`) chỉ lấy được file HTML rỗng.

4. **Điều tiết bộ nhớ thông minh (Memory-Adaptive Dispatcher):**
   Cơ chế tự động theo dõi RAM hệ thống và điều tiết số lượng tab trình duyệt đồng thời để tránh gây tràn RAM / treo hệ thống.

---

## 3. Hạn chế và Ranh giới cần lưu ý trên hạ tầng RTX 3050 6GB

- **Nhược điểm về tốc độ và tài nguyên (Overhead của Chromium):**
  Mỗi phiên trình duyệt headless Chromium tiêu tốn từ 50–150 MB RAM và tải CPU đáng kể.
  - Với danh sách nhỏ (1.000 – 5.000 URL): Crawl4AI chạy rất tốt và cho kết quả sạch nhất.
  - Với danh sách lớn (50.000 – 100.000+ URL): Nếu bật trình duyệt cho từng URL sẽ mất nhiều giờ và dễ gây nóng máy. Tốc độ trung bình của Playwright đạt khoảng 3–8 trang/giây, trong khi trình HTTP thuần đạt 80–150 trang/giây.

---

## 4. Kiến trúc Thu thập Lai khuyến nghị (Two-Tier Hybrid Ingestion)

Để tối ưu giữa **Tốc độ** và **Chất lượng văn bản Markdown**, khuyến nghị kết hợp 2 tầng:

```
[Danh sách URL tiếng Việt / tiếng Trung từ BTC]
                       |
                       v
         +----------------------------+
         | Tầng 1: Fast HTTP Path     |
         | (httpx + trafilatura)      | -> Của 80-90% URL thông thường
         | Tốc độ: 80-120 trang/giây  |    (Báo điện tử, bài viết tĩnh)
         +----------------------------+
                       |
       Có bị lỗi hoặc cần chạy JS?
           /                       \
        [Không]                   [Có]
          |                         |
          v                         v
   [Markdown sạch]        +-----------------------------+
                          | Tầng 2: Smart Dynamic Path  |
                          | (crawl4ai / Playwright)     |
                          | Xử lý SPA, chặn bot, JS     |
                          +-----------------------------+
                                    |
                                    v
                             [Markdown sạch]
                                    |
                                    v
                     [Context-preserving Chunker]
```

---

## 5. Lệnh cài đặt và đoạn mã sử dụng mẫu

### Cài đặt
```bash
pip install crawl4ai
crawl4ai-setup # Cài đặt trình duyệt Chromium đi kèm
```

### Mã nguồn mẫu thu thập bài viết y khoa ra Markdown
```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def crawl_medical_article(url: str):
    browser_cfg = BrowserConfig(
        headless=True,
        verbose=False,
        extra_args=["--disable-gpu", "--disable-dev-shm-usage"]
    )
    crawl_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        word_count_threshold=50,      # Bỏ qua các trang quá ngắn
        remove_overlay_elements=True  # Bỏ popup quảng cáo
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(url=url, config=crawl_cfg)
        if result.success:
            print(f"Tiêu đề: {result.metadata.get('title')}")
            # Markdown đã được lọc sạch rác:
            clean_markdown = result.markdown
            return clean_markdown
        else:
            print(f"Lỗi cào URL: {result.error_message}")
            return None

# asyncio.run(crawl_medical_article("https://example-medical-site.com/bai-viet-y-khoa"))
```
