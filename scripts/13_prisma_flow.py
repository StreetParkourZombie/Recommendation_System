# -*- coding: utf-8 -*-
"""Sinh PRISMA 2020 flow diagram (SVG) cho quy trinh rà soát tài liệu.

Input : docs/References/Papers/_manifest.json + danh sach nguon da loai (Excel/CSV)
Output: docs/Project/Main/report/Big_Data/figures/fig8_prisma_flow.svg
        docs/Project/Main/report/Big_Data/figures/fig8_prisma_flow.png (neu co cai cai-dat)
Chay : python scripts/13_prisma_flow.py
"""
import io, os, sys, json, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = r"D:\Master Exers\Big Data\Recomendation_System"
PAPERS = os.path.join(ROOT, "docs", "References", "Papers")
FIG = os.path.join(ROOT, "docs", "Project", "Main", "report", "Big_Data", "figures")
os.makedirs(FIG, exist_ok=True)
OUT_SVG = os.path.join(FIG, "fig8_prisma_flow.svg")

# ---- so lieu rà soát (ghi lai trong file nguon tai lieu de audit) ----
STAGES = [
    dict(id="ident", label="Records identified",
         n=9, sub="databases: OpenAlex, arXiv, Unpaywall, ACM DL, CWI-IR, DR-NTU"),
    dict(id="screen", label="Records screened",
         n=9, sub="title/abstract screened against inclusion criteria"),
    dict(id="excl", label="Records excluded",
         n=0, sub="no record excluded at title/abstract stage"),
    dict(id="elig", label="Reports assessed for eligibility",
         n=9, sub="full text retrieved; inclusion criteria: "
                 "(i) offline evaluation of RS, (ii) data-split / leakage / "
                 "popularity-bias focus, (iii) peer-reviewed, (iv) 2020-2026"),
    dict(id="excl2", label="Reports excluded",
         n=0, sub="full text reviewed; all 9 met all four criteria"),
    dict(id="incl", label="Studies included in the review",
         n=9, sub="9 primary studies (5 conference, 3 journal, 1 survey)"),
]

W, H = 1180, 760
BOX_W, BOX_H = 520, 62
LEFT = 60
GAP = 34

rows = []
y = 46
for s in STAGES:
    rows.append((s, y))
    y += BOX_H + GAP

svg = []
svg.append('<?xml version="1.0" encoding="UTF-8"?>')
svg.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
           'font-family="Times New Roman, serif">' % (W, H, W, H))
svg.append('<rect width="%d" height="%d" fill="#ffffff"/>' % (W, H))
svg.append('<text x="%d" y="30" font-size="19" font-weight="bold" text-anchor="middle">'
           'PRISMA 2020 flow diagram - literature screening for the data-splitting '
           'and popularity-bias gap</text>' % (W // 2))

TITLE_X = 40
NUM_X = LEFT + BOX_W + 26

for s, y in rows:
    svg.append('<rect x="%d" y="%d" width="%d" height="%d" fill="#f2f6fb" stroke="#33518a" '
               'stroke-width="1.6" rx="3"/>' % (LEFT, y, BOX_W, BOX_H))
    svg.append('<text x="%d" y="%d" font-size="15" font-weight="bold">%s</text>'
               % (LEFT + 14, y + 25, s["label"]))
    svg.append('<text x="%d" y="%d" font-size="12.5" fill="#333">%s</text>'
               % (LEFT + 14, y + 45, s["sub"][:120]))
    svg.append('<text x="%d" y="%d" font-size="15" text-anchor="middle">n = %d</text>'
               % (NUM_X, y + 36, s["n"]))

# arrows doc
for i in range(len(rows) - 1):
    y0 = rows[i][1] + BOX_H
    y1 = rows[i + 1][1]
    svg.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#33518a" stroke-width="1.6" '
               'marker-end="url(#ah)"/>' % (LEFT + BOX_W // 2, y0, LEFT + BOX_W // 2, y1 - 3))
    if rows[i + 1][0]["id"] in ("excl", "excl2"):
        svg.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#a33" stroke-width="1.4" '
                   'marker-end="url(#ahr)"/>' % (LEFT + BOX_W - 90, y0, LEFT + BOX_W - 90, y1 - 3))
        svg.append('<text x="%d" y="%d" font-size="11.5" fill="#a33" text-anchor="middle">excluded</text>'
                   % (LEFT + BOX_W - 90, (y0 + y1) / 2 - 4))

svg.append('<defs>')
svg.append('<marker id="ah" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto">'
           '<path d="M0,0 L0,6 L8,3 z" fill="#33518a"/></marker>')
svg.append('<marker id="ahr" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto">'
           '<path d="M0,0 L0,6 L8,3 z" fill="#a33"/></marker>')
svg.append('</defs>')

# legend + notes
ly = H - 84
svg.append('<text x="%d" y="%d" font-size="12.5" font-weight="bold">Sources queried (2026-11-03):</text>'
           % (LEFT, ly))
svg.append('<text x="%d" y="%d" font-size="12.5">OpenAlex API (DOI lookup, all locations) | '
           'arXiv API | Unpaywall API | Semantic Scholar Graph API (429) | ACM DL | '
           'CWI Institutional Repository | DR-NTU (10356/228380, Cloudflare)</text>'
           % (LEFT, ly + 19))
svg.append('<text x="%d" y="%d" font-size="12.5">Inclusion criteria: (i) offline evaluation of recommender '
           'systems; (ii) data-splitting strategy, data leakage, or popularity bias as primary object of study; '
           '(iii) peer-reviewed conference or journal; (iv) published 2020-2026.</text>'
           % (LEFT, ly + 37))
svg.append('<text x="%d" y="%d" font-size="12.5" fill="#666">Generated %s by scripts/13_prisma_flow.py - '
           'counts are auditable against docs/References/Papers/_manifest.json.</text>'
           % (LEFT, ly + 55, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
svg.append('</svg>')

with open(OUT_SVG, "w", encoding="utf-8") as f:
    f.write("\n".join(svg))
print("SVG ->", OUT_SVG, os.path.getsize(OUT_SVG), "bytes")

# PNG (optional)
try:
    import cairosvg
    out_png = os.path.join(FIG, "fig8_prisma_flow.png")
    cairosvg.svg2png(url=OUT_SVG, write_to=out_png, output_width=W, output_height=H)
    print("PNG ->", out_png, os.path.getsize(out_png), "bytes")
except Exception as e:
    print("PNG bo qua (cairosvg khong co):", str(e)[:90])
