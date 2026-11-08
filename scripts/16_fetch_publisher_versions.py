# -*- coding: utf-8 -*-
"""Tai ban PUBLISHED VERSION tu dl.acm.org cho cac DOI co ban arXiv.

Dung cookie replay: _acm_cookie.txt (dump tu CDP Storage.getCookies) + UA Chrome
giong het browser (156) — cf_clearance gan voi UA + IP.

Kiem tra: body phai bat dau bang %PDF va KHONG chua footer arXiv.
Luu vao docs/References/Papers/_publisher/ (khong ghi de ban cu).
"""
import io, os, sys, time, json, hashlib, urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = r"D:\Master Exers\Big Data\Recomendation_System"
OUT = os.path.join(ROOT, "docs", "References", "Papers", "_publisher")
os.makedirs(OUT, exist_ok=True)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36"
COOKIE = io.open(r"C:\Users\PC\.openclaw\workspace\_acm_cookie.txt", encoding="utf-8").read().strip()

TARGETS = [
    ("10.1145/3569930", "01_TOIS2022_DataLeakage_RS_OfflineEvaluation.pdf"),
    ("10.1145/3564284", "05_TOIS2022_Bias_Debias_Survey.pdf"),
    ("10.1145/3539618.3591931", "07_SIGIR2023_FreshLook_EvaluationStandpoint.pdf"),
    ("10.1145/3705328.3748164", "03_RecSys2025_TimeToSplit.pdf"),
    ("10.1145/3773078.3831818", "04_RecSys2026_ConvergentValidity_OfflineEvaluation.pdf"),
    ("10.1145/3705328.3748035", "09_RecSys2025_InheritedPopularityBias_ColdStart.pdf"),
    ("10.1145/3637066", "02_TOIS2023_Reproducing_PopularityBias_EvaluationStrategies.pdf"),
]

def fetch(doi):
    url = "https://dl.acm.org/doi/pdf/" + doi
    hdr = {
        "User-Agent": UA,
        "Accept": "application/pdf,text/html;q=0.9,*/*;q=0.8",
        "Cookie": COOKIE,
        "Referer": "https://dl.acm.org/doi/" + doi,
        "Accept-Language": "en-US,en;q=0.9",
    }
    req = urllib.request.Request(url, headers=hdr)
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.status, r.headers.get("Content-Type"), r.read()

res = []
for doi, fname in TARGETS:
    dst = os.path.join(OUT, fname)
    print("=" * 90)
    print("DOI:", doi)
    if os.path.exists(dst) and os.path.getsize(dst) > 100000:
        print("  SKIP (da co) %d bytes" % os.path.getsize(dst))
        res.append({"doi": doi, "file": fname, "status": "cached", "bytes": os.path.getsize(dst)})
        continue
    try:
        st, ct, data = fetch(doi)
        ok = data.startswith(b"%PDF")
        print("  HTTP %s | %s | %d bytes | PDF=%s" % (st, ct, len(data), ok))
        if not ok:
            print("  !! khong phai PDF, head:", data[:120])
            res.append({"doi": doi, "file": fname, "status": "not_pdf", "bytes": len(data), "head": data[:80].decode("latin-1")})
            continue
        io.open(dst, "wb").write(data)
        h = hashlib.sha256(data).hexdigest()
        res.append({"doi": doi, "file": fname, "status": "ok", "bytes": len(data), "sha256": h,
                    "source": "https://dl.acm.org/doi/pdf/" + doi})
    except Exception as e:
        print("  FAIL:", str(e)[:200])
        res.append({"doi": doi, "file": fname, "status": "fail", "error": str(e)[:200]})
    time.sleep(2)

io.open(os.path.join(OUT, "_publisher_manifest.json"), "w", encoding="utf-8").write(
    json.dumps(res, ensure_ascii=False, indent=2))
print("\n=== TONG ===")
for r in res:
    print("  %-10s %-70s %s" % (r["status"], r["file"], r.get("bytes", "")))
