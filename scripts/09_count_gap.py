"""Dem tu phan Gap 3 phan (Known / Critical Gap / Proposed) - quality gate cho PPNCKH.
Yeu cau: 200-250 tu (ban tieng Viet).
Chay: python scripts/09_count_gap.py
"""
import io, re, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

GAP_MD = r"D:\Master Exers\Big Data\Recomendation_System\docs\Project\Plans\07_Gap_3_phan_Known_CriticalGap_Proposed.md"


def count_words(block):
    plain = re.sub(r"\*\*", "", block)
    plain = re.sub(r"\*", "", plain)
    plain = re.sub(r"`", "", plain)
    return len([w for w in plain.split() if re.search(r"[0-9A-Za-zÀ-ỹ]", w)])


s = io.open(GAP_MD, encoding="utf-8").read()

sections = {}
patterns = {
    "Known": r"\*\*Đã biết \(Known\)\.\*\*\s*(.+?)(?=\n\n\*\*|\n\n---|\Z)",
    "CriticalGap": r"\*\*Khoảng trống cốt lõi \(Critical Gap\)\.\*\*\s*(.+?)(?=\n\n\*\*|\n\n---|\Z)",
    "Proposed": r"\*\*Đề xuất \(Proposed\)\.\*\*\s*(.+?)(?=\n\n\*\*|\n\n---|\Z)",
}
for key, pat in patterns.items():
    m = re.search(pat, s, re.S)
    if m:
        sections[key] = m.group(1).strip()
    else:
        print(f"  !! khong tim thay section {key}")

total = 0
res = {}
for k, v in sections.items():
    c = count_words(v)
    res[k] = c
    total += c
    print(f"  {k}: {c} words")

res["total"] = total
res["required_min"] = 200
res["required_max"] = 250
res["passed"] = 200 <= total <= 250
print(f"\nTOTAL: {total} words | required 200-250 | PASSED: {res['passed']}")
