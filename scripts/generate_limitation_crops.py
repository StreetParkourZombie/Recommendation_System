# -*- coding: utf-8 -*-
"""Sinh ảnh chụp đoạn "limitation" của 4 bài trung tâm cho slide 7 (bằng chứng gap).

Mỗi bài: tìm câu chứa từ khoá trên đúng trang đã verify bằng text search, crop
vùng văn bản đó (kèm margin), render 200 dpi -> PNG. Không cắt nguyên trang vì
slide cần 4 ảnh cạnh nhau và vẫn đọc được chữ.

Chạy:  python scripts/generate_limitation_crops.py
Ra:    docs/Project/Main/Presentation/Slides/figures/limitation/<slug>.png
       .../limitation/index.json   (nguồn: file, trang, câu tìm, sha256)

Tái lập được: không phụ thuộc thứ tự chạy, ghi đè ảnh cũ.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "docs" / "References" / "Papers"
OUT_DIR = ROOT / "docs" / "Project" / "Main" / "Presentation" / "Slides" / "figures" / "limitation"
DPI = 200
PAD_X, PAD_Y = 6, 5

# slug | file | trang (1-based, đã verify bằng text search) | regex câu cần crop
TARGETS = [
    {
        "slug": "01_TOIS2022_Ji_scope",
        "file": "01_TOIS2022_DataLeakage_RS_OfflineEvaluation.pdf",
        "page": 22,
        "pattern": r"The key focus of most studies in time-aware",
        "max_lines": 4,
        "doi": "10.1145/3569930",
        "label": "[1] Ji et al., TOIS 41(3) — tr.22",
        "gap": "Thiếu SLI theo lịch sử từng người",
    },
    {
        "slug": "02_TOIS2023_Navarro_limitations",
        "file": "02_TOIS2023_Reproducing_PopularityBias_EvaluationStrategies.pdf",
        "page": 8,
        "pattern": r"by changing the item candidates for recommendation",
        "max_lines": 3,
        "doi": "10.1145/3637066",
        "label": "[2] Daniil et al., TORS 2(1) — tr.8",
        "gap": "Chưa đo đổi thứ hạng/chi phí",
    },
    {
        "slug": "03_RecSys2025_TimeToSplit_limitation",
        "file": "03_RecSys2025_TimeToSplit.pdf",
        "page": 8,
        "pattern": r"targets for sequential recommendations",
        "max_lines": 2,
        "doi": "10.1145/3705328.3748164",
        "label": "[3] Gusak et al., RecSys '25 — tr.8",
        "gap": "Chỉ mô hình chuỗi; thiếu bias/chi phí",
    },
    {
        "slug": "04_RecSys2026_Discussion_Limitations",
        "file": "04_RecSys2026_ConvergentValidity_OfflineEvaluation.pdf",
        "page": 7,
        "pattern": r"positive correlations may be the efect",
        "max_lines": 2,
        "doi": "10.1145/3773078.3831818",
        "label": "[4] Parajuli et al., RecSys '26 — tr.7",
        "gap": "Chưa gắn Big Data; thiếu bias quy mô lớn",
    },
]


def sentence_rect(page: fitz.Page, pattern: str, max_lines: int = 3):
    """Rect của các dòng chứa pattern (nối các dòng liên tiếp thành 1 khối)."""
    rx = re.compile(pattern)
    blocks = []
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0:  # bỏ hình
            continue
        for ln in b["lines"]:
            txt = "".join(sp["text"] for sp in ln["spans"])
            blocks.append((fitz.Rect(ln["bbox"]), txt))
    idx = [i for i, (r, t) in enumerate(blocks) if rx.search(t)]
    if not idx:
        return None
    rect = fitz.Rect(blocks[idx[0]][0])
    # nối tối đa max_lines-1 dòng phía sau để câu trọn vẹn (tiếng Anh xuống dòng liên tục)
    for j in range(idx[0] + 1, min(idx[0] + max_lines, len(blocks))):
        nxt_r, nxt_t = blocks[j]
        if nxt_r.y0 - rect.y1 > 6:  # nhảy cột/bảng -> dừng
            break
        rect |= nxt_r
        if re.search(r"[.!?:]", nxt_t):
            break
    return rect


def crop(pdf: fitz.Document, page_no: int, rect: fitz.Rect, out_png: Path) -> dict:
    page = pdf[page_no - 1]
    clip = fitz.Rect(
        max(rect.x0 - PAD_X, page.rect.x0),
        max(rect.y0 - PAD_Y, page.rect.y0),
        min(rect.x1 + PAD_X, page.rect.x1),
        min(rect.y1 + PAD_Y, page.rect.y1),
    )
    pix = page.get_pixmap(dpi=DPI, clip=clip)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    pix.save(str(out_png))
    raw = out_png.read_bytes()
    return {
        "png": str(out_png),
        "page": page_no,
        "clip": [round(v, 1) for v in clip],
        "px": [pix.width, pix.height],
        "sha256": hashlib.sha256(raw).hexdigest()[:16],
    }


def main() -> int:
    index = []
    for t in TARGETS:
        pdf_path = PAPERS / t["file"]
        assert pdf_path.is_file(), f"thieu PDF: {pdf_path}"
        doc = fitz.open(pdf_path)
        page = doc[t["page"] - 1]
        rect = sentence_rect(page, t["pattern"], t.get("max_lines", 2))
        if rect is None:
            print(f"[FAIL] khong tim thay {t['pattern']!r} o {t['file']} tr.{t['page']}")
            return 1
        out_png = OUT_DIR / f"{t['slug']}.png"
        info = crop(doc, t["page"], rect, out_png)
        info.update(slug=t["slug"], doi=t["doi"], label=t["label"], gap=t["gap"], file=t["file"])
        index.append(info)
        print(f"[OK] {t['slug']}.png  {info['px'][0]}x{info['px'][1]}px  sha={info['sha256']}")
        doc.close()

    (OUT_DIR / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n{len(index)} anh -> {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
