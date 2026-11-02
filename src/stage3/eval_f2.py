"""Do Macro F2 tach tang (Document-level va Chunk-level) theo dung cong thuc
chinh thuc cua BTC - xem docs/phan-tich/02-DANH-GIA-VA-CONG-THUC-F2.md.

Hai cap do dung HAI cong thuc KHAC NHAU, khong phai cung mot cong thuc set-based:

  Document-level (set-based tren doc_id):
    P = |D_pred ∩ D_gold| / |D_pred|,  R = |D_pred ∩ D_gold| / |D_gold|

  Chunk-level (content-overlap tren chunk_text, KHONG phai set-based tren chunk_id):
    P = (so chunk relevant) / (tong so chunk tra ve)
    R = (so phan tu cua I duoc bao phu) / |I|
    voi I la tap cac "phan thong tin can thiet" (gold info spans) cho cau hoi do,
    va mot chunk duoc tinh la "relevant" neu noi dung trung/overlap du voi it nhat
    mot phan tu cua I.

  Luat khop chunk (hướng dẫn chấm chính thức của BTC, 12/10/2026): NFKC + giai ma HTML entity +
  chu thuong + gop khoang trang, roi LCS_token(chunk, doan tham chieu) / |doan tham chieu|
  >= 0,40. Cach tach token cho tieng Trung tai lieu cham khong neu: ta tach tung chu Han (gia dinh).

Chay:
    python eval_f2.py                                   # chi chay self-test voi
                                                          # cac vi du da co ket qua
                                                          # biet truoc trong doc 02
    python eval_f2.py predictions.json gold.json         # cham that
"""

import argparse
import html
import json
import re
import sys
import unicodedata


def f2_score(precision: float, recall: float) -> float:
    """F2 = 5PR / (4P + R). Tra ve 0 neu P=0 va R=0 (khong chia cho 0)."""
    if precision == 0.0 and recall == 0.0:
        return 0.0
    return 5 * precision * recall / (4 * precision + recall)


def document_level_scores(pred_docs: list, gold_docs: list) -> dict:
    """Set-based tren doc_id, dung theo 02-DANH-GIA-VA-CONG-THUC-F2.md muc 1.1."""
    d_pred, d_gold = set(pred_docs), set(gold_docs)
    if not d_pred:
        return {"precision": 0.0, "recall": 0.0, "f2": 0.0}
    hit = len(d_pred & d_gold)
    precision = hit / len(d_pred)
    recall = hit / len(d_gold) if d_gold else 0.0
    return {"precision": precision, "recall": recall, "f2": f2_score(precision, recall)}


_TOKEN_RE = re.compile(r"[一-鿿]|\w+", re.UNICODE)
OFFICIAL_MIN_OVERLAP = 0.40


def _tokenize(text: str) -> list:
    """Chuan hoa NFKC + giai ma HTML entity + chu thuong, roi tach token. Chu Han tach tung chu
    (tai lieu cham khong neu cach tach token cho tieng Trung - day la gia dinh cua ta)."""
    normalized = unicodedata.normalize("NFKC", html.unescape(text)).lower()
    return _TOKEN_RE.findall(normalized)


def _lcs_length(first: list, second: list) -> int:
    previous = [0] * (len(second) + 1)
    for token in first:
        current = [0]
        for j, other in enumerate(second):
            current.append(previous[j] + 1 if token == other else max(previous[j + 1], current[j]))
        previous = current
    return previous[-1]


def is_chunk_relevant(chunk_text: str, info_span: str, min_overlap_ratio: float = OFFICIAL_MIN_OVERLAP) -> bool:
    """Luat khop chunk chinh thuc (hướng dẫn chấm chính thức của BTC): LCS token giua chunk nop va
    doan tham chieu, chia cho do dai doan tham chieu, >= 0,40. Rang buoc cung doc_id do noi goi
    kiem tra (ham nay chi nhan van ban)."""
    gold_tokens = _tokenize(info_span)
    if not gold_tokens:
        return False
    return _lcs_length(_tokenize(chunk_text), gold_tokens) / len(gold_tokens) >= min_overlap_ratio


def chunk_level_scores(
    pred_chunks: list, gold_info_spans: list, min_overlap_ratio: float = OFFICIAL_MIN_OVERLAP
) -> dict:
    """Content-overlap tren chunk_text, dung theo 02-DANH-GIA-VA-CONG-THUC-F2.md muc 1.2."""
    if not pred_chunks:
        return {"precision": 0.0, "recall": 0.0, "f2": 0.0}

    relevant_count = 0
    covered_spans = set()
    for chunk_text in pred_chunks:
        chunk_is_relevant = False
        for idx, span in enumerate(gold_info_spans):
            if is_chunk_relevant(chunk_text, span, min_overlap_ratio):
                chunk_is_relevant = True
                covered_spans.add(idx)
        if chunk_is_relevant:
            relevant_count += 1

    precision = relevant_count / len(pred_chunks)
    recall = len(covered_spans) / len(gold_info_spans) if gold_info_spans else 0.0
    return {"precision": precision, "recall": recall, "f2": f2_score(precision, recall)}


def macro_average(values: list) -> float:
    return sum(values) / len(values) if values else 0.0


def evaluate(predictions: list, gold: list, min_overlap_ratio: float = OFFICIAL_MIN_OVERLAP) -> dict:
    """predictions, gold: list cac dict {"id", "relevant_docs", "relevant_chunks"}.
    gold moi phan tu them truong "info_spans" (tap cac doan thong tin can thiet -
    chi dung cho cham chunk-level, khong anh huong doc-level)."""
    gold_by_id = {g["id"]: g for g in gold}

    doc_f2s, chunk_f2s = [], []
    per_query = []
    for pred in predictions:
        qid = pred["id"]
        g = gold_by_id.get(qid)
        if g is None:
            raise ValueError(f"Khong tim thay gold cho query id={qid!r}")

        doc_result = document_level_scores(pred.get("relevant_docs", []), g.get("relevant_docs", []))
        chunk_result = chunk_level_scores(
            pred.get("relevant_chunks", []),
            g.get("info_spans", []),
            min_overlap_ratio,
        )
        doc_f2s.append(doc_result["f2"])
        chunk_f2s.append(chunk_result["f2"])
        per_query.append({"id": qid, "document": doc_result, "chunk": chunk_result})

    return {
        "macro_f2_document": macro_average(doc_f2s),
        "macro_f2_chunk": macro_average(chunk_f2s),
        "num_queries": len(predictions),
        "per_query": per_query,
    }


def _run_self_tests() -> None:
    """Doi chieu truc tiep voi cac vi du co ket qua biet truoc trong
    02-DANH-GIA-VA-CONG-THUC-F2.md muc 2 (bang do nhay) va muc 3 (sup bay xa chunk)."""

    # Muc 2 - bang do nhay F2 (document-level, |G_gold|=2)
    cases = [
        (["a", "b"], ["a", "b"], 1.000),           # Chinh xac tuyet doi
        (["a", "b", "c"], ["a", "b"], 0.909),       # Lay du + du phong nhe
        (["a", "b", "c", "d", "e"], ["a", "b"], 0.769),  # Lay du + du thua vua
        (["a"], ["a", "b"], 0.556),                 # Bo sot 1/2
    ]
    for pred, gold, expected in cases:
        result = document_level_scores(pred, gold)
        assert abs(result["f2"] - expected) < 0.001, (
            f"document_level_scores({pred}, {gold}) = {result['f2']:.3f}, ky vong {expected}"
        )

    # Xa chunk bua bai: 20 phan tu tra ve, 2 hit, |G|=2 -> F2 = 0.357
    xa_bua = [f"x{i}" for i in range(18)] + ["a", "b"]
    result = document_level_scores(xa_bua, ["a", "b"])
    assert abs(result["f2"] - 0.357) < 0.001, f"xa chunk bua bai = {result['f2']:.3f}, ky vong 0.357"

    # Luat LCS: thu tu token quan trong, khong chi tap token chung
    assert is_chunk_relevant("a b c d e f g h i j", "a b c d e")
    assert not is_chunk_relevant("e d c b a x y z", "a b c d e")
    assert _tokenize("Ｔhuốc &amp; liều") == _tokenize("thuốc & liều") == ["thuốc", "liều"]
    assert _tokenize("心肌梗死") == ["心", "肌", "梗", "死"]

    # Muc 3 - sup bay "xa toan bo chunk": 25 chunk toan bo tai lieu vs 3 chunk top rerank,
    # chi dung 1 chunk thuc su chua thong tin can thiet.
    info_span = "huong dan dieu tri soi than cap tinh can nhap vien ngay"
    chunk_dung = "Phac do huong dan dieu tri soi than cap tinh can nhap vien ngay lap tuc."
    chunk_nhieu = ["Thong tin khong lien quan ve dinh duong hang ngay." for _ in range(24)]

    xa_toan_bo = chunk_nhieu + [chunk_dung]
    result_xa = chunk_level_scores(xa_toan_bo, [info_span])
    assert abs(result_xa["f2"] - 0.172) < 0.01, f"xa toan bo 25 chunk = {result_xa['f2']:.3f}, ky vong ~0.172"

    chon_loc = ["Thong tin khong lien quan khac." for _ in range(2)] + [chunk_dung]
    result_chon = chunk_level_scores(chon_loc, [info_span])
    assert abs(result_chon["f2"] - 0.714) < 0.01, f"chon loc 3 chunk = {result_chon['f2']:.3f}, ky vong ~0.714"

    # f2_score bien: P=0, R=0 -> 0 (khong duoc chia cho 0)
    assert f2_score(0.0, 0.0) == 0.0

    print("Tat ca self-test PASS - khop cac vi du co ket qua biet truoc trong doc 02.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("predictions", nargs="?", help="File JSON ket qua du doan")
    parser.add_argument("gold", nargs="?", help="File JSON nhan chuan (gold)")
    parser.add_argument("--overlap-ratio", type=float, default=OFFICIAL_MIN_OVERLAP)
    args = parser.parse_args()

    _run_self_tests()

    if args.predictions and args.gold:
        with open(args.predictions, encoding="utf-8") as f:
            predictions = json.load(f)
        with open(args.gold, encoding="utf-8") as f:
            gold = json.load(f)
        result = evaluate(predictions, gold, args.overlap_ratio)
        print(f"\nSo cau hoi: {result['num_queries']}")
        print(f"Macro F2 (Document): {result['macro_f2_document']:.4f}")
        print(f"Macro F2 (Chunk):    {result['macro_f2_chunk']:.4f}")
    elif args.predictions or args.gold:
        print("Can truyen ca predictions va gold, hoac khong truyen gi de chi chay self-test.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
