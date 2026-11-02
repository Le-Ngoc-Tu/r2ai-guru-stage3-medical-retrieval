"""Chia trang đã crawl (markdown của trafilatura) thành chunk theo ngân sách token
của tokenizer BGE-M3 (đo thật: tiếng Trung ~0,64 token/ký tự, tiếng Việt ~0,28 -
xem doc 14 / AGENTS.md mục 2 Giai đoạn 3, nên không dùng giới hạn theo ký tự).

Ràng buộc cuộc thi: chunk_text nộp bài phải là văn bản trích thật từ tài liệu
(cấm "tạo chunk thay thế ID"). Vì vậy `text` luôn là body[char_start:char_end]
nguyên văn; phần ngữ cảnh (Contextual Retrieval bản tĩnh, doc 11 mục 3) chỉ nằm ở
`embed_text` dùng để tạo embedding, không bao giờ đưa vào bài nộp.
"""

import glob
import re
from dataclasses import dataclass
from pathlib import Path

from tokenizers import Tokenizer

ROOT = Path(__file__).resolve().parents[2]

MAX_CHUNK_TOKENS = 420  # chừa ~90 token cho tiêu đề/mục trong embed_text (giới hạn 512)
OVERLAP_TOKENS = 60
MAX_TITLE_CHARS = 80
FFFD_LIMIT = 10  # trang có >= ngần này ký tự U+FFFD là lỗi mã hóa (doc 14), bỏ qua

_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n?", re.DOTALL)
_TITLE_LINE = re.compile(r"^title:\s*(.+)$", re.MULTILINE)
_BLOCK = re.compile(r"\S(?:.*?\S)?(?=\n\s*\n|\Z)", re.DOTALL)
_HEADING = re.compile(r"^#{1,6}\s+(.+)$")
_SENTENCE = re.compile(r"[^。！？；!?;.\n]*[。！？；!?;.\n]+|[^。！？；!?;.\n]+$")
_HAN = re.compile(r"[一-鿿]")


@dataclass
class Chunk:
    doc_id: int
    chunk_id: str
    chunk_index: int
    doc_title: str
    section: str
    language: str
    text: str
    embed_text: str
    char_start: int
    char_end: int
    n_tokens: int


@dataclass
class _Unit:
    start: int
    end: int
    n_tokens: int
    section: str


def load_tokenizer() -> Tokenizer:
    path = glob.glob(str(ROOT / "data" / "hf_cache" / "models--BAAI--bge-m3" / "snapshots" / "*" / "tokenizer.json"))[0]
    tokenizer = Tokenizer.from_file(path)
    tokenizer.no_truncation()
    tokenizer.no_padding()
    return tokenizer


def split_page(markdown: str) -> tuple[str, str, int]:
    """Tách frontmatter. Trả về (title, body, offset của body trong markdown)."""
    match = _FRONTMATTER.match(markdown)
    if not match:
        return "", markdown, 0
    title_match = _TITLE_LINE.search(match.group(1))
    title = title_match.group(1).strip().strip("\"'") if title_match else ""
    return title, markdown[match.end():], match.end()


def detect_language(text: str) -> str:
    han = len(_HAN.findall(text))
    return "zh" if han / max(1, len(text)) > 0.2 else "vi"


def _token_count(tokenizer: Tokenizer, texts: list[str]) -> list[int]:
    return [len(e.ids) for e in tokenizer.encode_batch(texts, add_special_tokens=False)]


def _hard_split(tokenizer: Tokenizer, body: str, start: int, end: int, section: str) -> list[_Unit]:
    """Câu dài hơn ngân sách (không có dấu câu): cắt cứng theo offset token."""
    encoding = tokenizer.encode(body[start:end], add_special_tokens=False)
    units = []
    for i in range(0, len(encoding.offsets), MAX_CHUNK_TOKENS):
        piece = encoding.offsets[i:i + MAX_CHUNK_TOKENS]
        units.append(_Unit(start + piece[0][0], start + piece[-1][1], len(piece), section))
    return units


def _build_units(tokenizer: Tokenizer, body: str) -> list[_Unit]:
    blocks = [(m.start(), m.end()) for m in _BLOCK.finditer(body)]
    counts = _token_count(tokenizer, [body[s:e] for s, e in blocks])
    units: list[_Unit] = []
    section = ""
    for (start, end), n_tokens in zip(blocks, counts):
        heading = _HEADING.match(body[start:end])
        if heading and "\n" not in body[start:end]:
            section = heading.group(1).strip()
        if n_tokens <= MAX_CHUNK_TOKENS:
            units.append(_Unit(start, end, n_tokens, section))
            continue
        sentences = [(start + m.start(), start + m.end()) for m in _SENTENCE.finditer(body[start:end]) if m.group().strip()]
        sentence_counts = _token_count(tokenizer, [body[s:e] for s, e in sentences])
        for (s, e), n in zip(sentences, sentence_counts):
            if n <= MAX_CHUNK_TOKENS:
                units.append(_Unit(s, e, n, section))
            else:
                units.extend(_hard_split(tokenizer, body, s, e, section))
    return units


def build_embed_text(doc_title: str, section: str, text: str) -> str:
    """Contextual Retrieval tĩnh: thêm tiêu đề + mục vào trước text (chỉ để embed)."""
    heading_already_in_text = bool(section) and text.startswith(("#", "**")) and section in text.split("\n", 1)[0]
    context = "\n".join(part for part in (doc_title, "" if heading_already_in_text else section) if part)
    return f"{context}\n{text}" if context else text


def _first_unit_after_overlap(units: list[_Unit], first: int, last: int) -> int:
    """Chỉ số đơn vị bắt đầu chunk kế tiếp: lùi lại tối đa OVERLAP_TOKENS token,
    nhưng luôn tiến ít nhất 1 đơn vị so với chunk vừa tạo để không lặp vô hạn."""
    next_start = last + 1
    budget = OVERLAP_TOKENS
    while next_start - 1 > first and units[next_start - 1].n_tokens <= budget:
        budget -= units[next_start - 1].n_tokens
        next_start -= 1
    return next_start


def chunk_page(doc_id: int, markdown: str, tokenizer: Tokenizer) -> list[Chunk]:
    """Trả về [] cho trang lỗi mã hóa hoặc không có thân bài."""
    if markdown.count("�") >= FFFD_LIMIT:
        return []
    title, body, _ = split_page(markdown)
    units = _build_units(tokenizer, body)
    if not units:
        return []

    language = detect_language(body)
    doc_title = title[:MAX_TITLE_CHARS]
    chunks: list[Chunk] = []
    first = 0
    while first < len(units):
        last = first
        total = units[first].n_tokens
        while last + 1 < len(units) and total + units[last + 1].n_tokens <= MAX_CHUNK_TOKENS:
            last += 1
            total += units[last].n_tokens
        char_start, char_end = units[first].start, units[last].end
        section = units[first].section
        text = body[char_start:char_end]
        index = len(chunks)
        chunks.append(Chunk(
            doc_id=doc_id,
            chunk_id=f"{doc_id}_c{index:03d}",
            chunk_index=index,
            doc_title=doc_title,
            section=section,
            language=language,
            text=text,
            embed_text=build_embed_text(doc_title, section, text),
            char_start=char_start,
            char_end=char_end,
            n_tokens=total,
        ))
        if last + 1 >= len(units):
            break
        first = _first_unit_after_overlap(units, first, last)
    return chunks
