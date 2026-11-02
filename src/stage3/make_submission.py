"""Tạo bài nộp Public Test từ 1.200 câu hỏi thật.

Mỗi câu hỏi thật có trung bình ~71 doc và ~75 chunk tham chiếu (đo từ kết quả chấm 14/10/2026),
nên bài nộp phải trả nhiều doc chứ không phải 3-5. Truy hồi một lần (RRF của BM25 + dense, độ
sâu DEPTH mỗi nguồn, lưu cache), rồi xuất nhiều biến thể "D doc, C doc đầu có chunk, cửa sổ W token": doc xếp theo lần
xuất hiện đầu tiên trong danh sách xếp hạng; chunk của một doc là chunk xếp cao nhất của nó ghép
với các chunk liền kề (nguyên văn, bỏ phần overlap) tới ~W token, vì overlap chấm bằng LCS chia độ
dài chunk tham chiếu nên đoạn dài chỉ có lợi cho Recall chunk.

Chạy:
    python make_submission.py --source rerank 150x90x900 150x45x900xm2
"""

import argparse
import glob
import json
import zipfile

import numpy as np
import polars as pl
import torch
from transformers import AutoTokenizer

import hybrid_search as hs
import tantivy_indexer as ti

OUT_DIR = ti.ROOT / "data" / "submission"
DEPTH = {"rrf": 300, "rrf600": 600, "rrf600v2": 600, "bm25": 1000, "rerank": 0}


def rerank_ranking() -> list[dict]:
    """Xếp hạng chunk theo điểm rerank (mọi file rerank_r*.jsonl của rerank_deep.py), phần đuôi RRF nối sau."""
    rrf = {r["id"]: r["ranking"] for r in map(json.loads, open(OUT_DIR / "candidates_rrf_d300.jsonl", encoding="utf-8"))}
    scored: dict[int, list[tuple[float, list[int]]]] = {}
    for path in sorted(OUT_DIR.glob("rerank_r*.jsonl")):
        for line in open(path, encoding="utf-8"):
            r = json.loads(line)
            scored.setdefault(r["id"], []).extend(zip(r["scores"], r["keys"]))
    rows = []
    for qid, pairs in scored.items():
        pairs.sort(key=lambda p: -p[0])
        seen = {tuple(k) for _, k in pairs}
        rows.append({"id": qid, "ranking": [k for _, k in pairs] + [k for k in rrf[qid] if tuple(k) not in seen], "scores": [s for s, _ in pairs]})
    return rows


def retrieve(queries: pl.DataFrame, source: str) -> list[dict]:
    if source == "rerank":
        return rerank_ranking()
    depth = DEPTH[source]
    path = OUT_DIR / f"candidates_{source}_d{depth}.jsonl"
    if path.exists():
        return [json.loads(line) for line in open(path, encoding="utf-8")]
    texts = queries["query"].to_list()
    vectors = [None] * len(texts)
    if source.startswith("rrf"):
        encoder = hs.QueryEncoder()
        vectors = np.concatenate([encoder.encode(texts[i:i + 32]) for i in range(0, len(texts), 32)])
        del encoder
        torch.cuda.empty_cache()
    searcher = hs.HybridSearcher()
    rows = []
    for n, (qid, query, vector) in enumerate(zip(queries["id"], texts, vectors)):
        ranking = searcher.bm25(query, depth)
        if source.startswith("rrf"):
            ranking = [key for key, _ in hs.rrf([ranking, searcher.dense_search(vector, depth)], depth)]
        rows.append({"id": int(qid), "ranking": [list(k) for k in ranking]})
        if n % 100 == 0:
            print(f"truy hồi {n}/{len(texts)}", flush=True)
    with open(path, "w", encoding="utf-8") as out:
        for row in rows:
            out.write(json.dumps(row) + "\n")
    return rows


NEW_CORPUS = ti.ROOT / "data" / "ViBioMIR_new" / "links_corpus_vi_en_zh.parquet"
PUBMED_MIN_ID = 4_420_562
MIN_ANCHOR_GAP = 4
MIN_DOCS = 10
MIN_WINDOWS = 5


def select(candidates: list[dict], doc_k: int, chunk_docs: int, aggregate: str, per_doc: int) -> dict[int, tuple[list[int], list[tuple[int, int]]]]:
    """Mỗi câu: doc_k doc xếp đầu, và với chunk_docs doc đầu tiên, tối đa per_doc chunk neo xếp cao nhất.

    aggregate="first": doc xếp theo lần xuất hiện đầu tiên; "sum": theo tổng 1/(RRF_K + hạng) của mọi chunk của doc.
    Các chunk neo cùng doc cách nhau ít nhất MIN_ANCHOR_GAP chunk để cửa sổ không chồng nhau.
    """
    chosen = {}
    for c in candidates:
        chunks_of: dict[int, list[int]] = {}
        score: dict[int, float] = {}
        for rank, (doc, chunk) in enumerate(c["ranking"], start=1):
            chunks_of.setdefault(doc, []).append(chunk)
            score[doc] = score.get(doc, 0.0) + (1.0 / (hs.RRF_K + rank) if aggregate == "sum" else 0.0)
        docs = list(chunks_of) if aggregate == "first" else sorted(chunks_of, key=lambda d: -score[d])
        docs = docs[:doc_k]
        anchors = []
        for doc in docs[:chunk_docs]:
            picked: list[int] = []
            for chunk in chunks_of[doc]:
                if len(picked) < per_doc and all(abs(chunk - other) >= MIN_ANCHOR_GAP for other in picked):
                    picked.append(chunk)
            anchors.extend((doc, chunk) for chunk in picked)
        chosen[c["id"]] = (docs, anchors)
    return chosen


def blend_qwen(candidates: list[dict], path: str, weight: float) -> None:
    """Ghép điểm Qwen3-Reranker vào điểm BGE của top doc (z-score trong từng câu, quy về thang BGE để giữ ngưỡng).

    Chỉ chunk neo của doc (đã chấm Qwen) đổi điểm; chunk khác cùng doc bị chặn dưới điểm neo để neo luôn xếp đầu doc.
    """
    qwen = {r["id"]: r for r in map(json.loads, open(OUT_DIR / path, encoding="utf-8"))}
    z = lambda a: (a - a.mean()) / (a.std() + 1e-9)
    for c in candidates:
        q = qwen.get(c["id"])
        if q is None:
            continue
        bge = np.array(q["bge"])
        blended = bge.mean() + bge.std() * ((1 - weight) * z(bge) + weight * z(np.array(q["qwen"])))
        anchor = {tuple(k): float(s) for k, s in zip(q["keys"], blended)}
        doc_score = {k[0]: s for k, s in anchor.items()}
        scored = list(zip(c["ranking"][:len(c["scores"])], c["scores"]))
        rescored = [(tuple(k), anchor[tuple(k)] if tuple(k) in anchor else (min(s, doc_score[k[0]] - 1e-3) if k[0] in doc_score else s)) for k, s in scored]
        rescored.sort(key=lambda p: -p[1])
        c["ranking"] = [list(k) for k, _ in rescored] + c["ranking"][len(c["scores"]):]
        c["scores"] = [s for _, s in rescored]


def restrict_corpus(candidates: list[dict], drop_pubmed: bool = False) -> None:
    """Bỏ mọi chunk thuộc doc ngoài corpus mới của BTC (18/10/2026): nhãn chỉ nằm trong corpus mới."""
    allowed = set(pl.read_parquet(NEW_CORPUS)["id"].to_list())
    if drop_pubmed:
        allowed = {doc for doc in allowed if doc < PUBMED_MIN_ID}
    dropped = total = 0
    for c in candidates:
        n_scored = len(c.get("scores", []))
        keep = [i for i, (doc, _) in enumerate(c["ranking"]) if doc in allowed]
        total += len(c["ranking"])
        dropped += len(c["ranking"]) - len(keep)
        if "scores" in c:
            c["scores"] = [c["scores"][i] for i in keep if i < n_scored]
        c["ranking"] = [c["ranking"][i] for i in keep]
    print(f"lọc corpus mới: bỏ {dropped}/{total} chunk ({dropped / total:.1%})", flush=True)


def select_dynamic(candidates: list[dict], doc_min: float, doc_cap: int, window_budget: int, window_cap: int) -> dict[int, tuple[list[int], list[tuple[int, int]]]]:
    """Chọn doc và cửa sổ theo điểm rerank thay cho K cố định.

    Doc: chunk xếp cao nhất của doc có điểm >= doc_min, tối đa doc_cap doc. Cửa sổ: lấy window_budget cửa sổ
    điểm cao nhất trên toàn bộ các câu (mỗi câu tối đa window_cap), mọi cửa sổ đều thuộc doc đã chọn.
    Mỗi câu luôn có ít nhất MIN_DOCS doc và MIN_WINDOWS cửa sổ để không trả danh sách rỗng.
    """
    per_query = {}
    for c in candidates:
        seen, docs = set(), []
        for (doc, chunk), score in zip(c["ranking"], c["scores"]):
            if doc not in seen and (score >= doc_min or len(docs) < MIN_DOCS) and len(docs) < doc_cap:
                seen.add(doc)
                docs.append((score, doc, chunk))
        per_query[c["id"]] = docs
    pool = sorted((score for docs in per_query.values() for score, _, _ in docs[:window_cap]), reverse=True)
    window_min = pool[min(window_budget, len(pool)) - 1]
    print(f"{sum(len(d) for d in per_query.values()) / len(per_query):.1f} doc/câu, ngưỡng điểm cửa sổ {window_min:.2f}", flush=True)
    return {qid: ([d for _, d, _ in docs], [(d, ch) for rank, (sc, d, ch) in enumerate(docs[:window_cap]) if sc >= window_min or rank < MIN_WINDOWS]) for qid, docs in per_query.items()}


def merge_chunks(members: list[tuple[int, int]], fields: dict) -> str:
    text, end = None, None
    for key in sorted(members, key=lambda k: k[1]):
        piece, start, stop = fields[key][:3]
        if text is None:
            text = piece
        elif start < end:
            text += piece[end - start:]
        else:
            text += "\n" + piece
        end = max(stop, end or stop)
    return text


def window_texts(searcher: hs.HybridSearcher, anchors: set[tuple[int, int]], max_tokens: int) -> dict[tuple[int, int], str]:
    """Ghép chunk neo với các chunk liền kề cùng tài liệu thành một đoạn dài tối đa max_tokens token (đếm thật)."""
    tokenizer = AutoTokenizer.from_pretrained(glob.glob(str(ti.ROOT / "data" / "hf_cache" / "models--BAAI--bge-m3" / "snapshots" / "*"))[0])
    position = lambda key: np.searchsorted(searcher.sorted_keys, (key[0] << 12) | key[1])
    exists = lambda key: position(key) < len(searcher.sorted_keys) and searcher.sorted_keys[position(key)] == (key[0] << 12) | key[1]
    neighbours = {a: {(a[0], a[1] + d) for d in (-2, -1, 1, 2) if a[1] + d >= 0 and exists((a[0], a[1] + d))} for a in anchors}
    fields = searcher.chunk_fields(sorted(anchors | {k for ks in neighbours.values() for k in ks}), ["text", "char_start", "char_end"])
    windows = {}
    for anchor in anchors:
        members, best = [anchor], fields[anchor][0]
        for step in (1, -1, 2, -2):
            key = (anchor[0], anchor[1] + step)
            if key not in neighbours[anchor]:
                continue
            trial = merge_chunks(members + [key], fields)
            if len(tokenizer(trial, add_special_tokens=False)["input_ids"]) <= max_tokens:
                members, best = members + [key], trial
        windows[anchor] = best
    return windows


def write_zip(chosen: dict, texts: dict, name: str) -> None:
    submission = []
    for qid, (docs, anchors) in chosen.items():
        chunks = [{"doc_id": doc, "chunk_text": texts[(doc, chunk)]} for doc, chunk in anchors]
        submission.append({"id": qid, "relevant_docs": docs, "relevant_chunks": chunks})
    json_path = OUT_DIR / f"submission_{name}" / "submission.json"
    json_path.parent.mkdir(exist_ok=True)
    json_path.write_text(json.dumps(submission, ensure_ascii=False), encoding="utf-8")
    zip_path = OUT_DIR / f"submission_{name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.write(json_path, "submission.json")
    print(f"Bài {name}: {len(submission)} câu, zip {zip_path.stat().st_size / 1e6:.2f} MB", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=sorted(DEPTH), default="rrf")
    parser.add_argument("--dynamic", nargs=4, type=float, metavar=("DOC_MIN", "DOC_CAP", "WINDOW_BUDGET", "WINDOW_CAP"), help="chọn doc/cửa sổ theo điểm rerank (chỉ với --source rerank)")
    parser.add_argument("--qwen", nargs=2, metavar=("FILE", "WEIGHT"), help="ghép điểm Qwen3-Reranker từ FILE (rerank_qwen.py) với trọng số WEIGHT (chỉ với --source rerank)")
    parser.add_argument("--new-corpus", action="store_true", help="chỉ giữ doc có trong corpus mới (links_corpus_vi_en_zh.parquet)")
    parser.add_argument("--no-pubmed", action="store_true", help="với --new-corpus: bỏ luôn doc PubMed (id > 4.420.561), để tách tác động của PubMed")
    parser.add_argument("--window-tokens", type=int, default=900, help="trần token mỗi cửa sổ khi dùng --dynamic")
    parser.add_argument("variants", nargs="*", help="dạng DxCxW[xsum][xmN], ví dụ 150x45x900xm2: 150 doc, 45 doc đầu mỗi doc 2 cửa sổ <=900 token")
    args = parser.parse_args()
    variants = {v: v.split("x") for v in args.variants}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    candidates = retrieve(pl.read_parquet(ti.ROOT / "data" / "ViBioMIR" / "query.parquet"), args.source)
    if args.qwen:
        blend_qwen(candidates, args.qwen[0], float(args.qwen[1]))
    if args.new_corpus:
        restrict_corpus(candidates, args.no_pubmed)
    searcher = hs.HybridSearcher()
    if args.dynamic:
        doc_min, doc_cap, budget, window_cap = args.dynamic
        chosen = select_dynamic(candidates, doc_min, int(doc_cap), int(budget), int(window_cap))
        anchors = {k for _, keys in chosen.values() for k in keys}
        write_zip(chosen, window_texts(searcher, anchors, args.window_tokens), f"rerank_dyn{doc_min:g}_{int(doc_cap)}_{int(budget)}" + (f"_w{args.window_tokens}" if args.window_tokens != 900 else "") + (f"_qwen{args.qwen[1]}" if args.qwen else "") + ("_newcorpus" if args.new_corpus else "") + ("_nopubmed" if args.no_pubmed else ""))
    for name, (doc_k, chunk_docs, window_tokens, *options) in variants.items():
        per_doc = next((int(o[1:]) for o in options if o.startswith("m")), 1)
        chosen = select(candidates, int(doc_k), int(chunk_docs), "sum" if "sum" in options else "first", per_doc)
        anchors = {k for _, keys in chosen.values() for k in keys}
        write_zip(chosen, window_texts(searcher, anchors, int(window_tokens)), f"{args.source}_{name}")


if __name__ == "__main__":
    main()
