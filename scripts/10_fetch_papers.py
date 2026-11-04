# -*- coding: utf-8 -*-
"""Tai 9 paper RecSys cho PPNCKH vao docs/References/Papers/.

Nguon: OpenAlex (best_oa_location / primary_location / locations) -> arXiv -> Unpaywall.
Sinh _manifest.json kem sha256 de kiem chong toan venh.

Chay:  python scripts/10_fetch_papers.py
Ghi chu: doi voi paper khong co OA PDF o nguon machine-readable (ACM Cloudflare chan
script) thi can tai thu cong qua trinh duyet; script se ghi status="manual_required"
va khong ghi de file da ton tai.

Fallback cho ACM DL (Cloudflare): dat env ACM_COOKIE_HEADER voi Cookie header lay
tu Chrome DevTools (Storage.getCookies cho domain dl.acm.org, gom `cf_clearance`).
Khi co env nay, DOI 08 duoc tai truc tiep tu https://dl.acm.org/doi/pdf/<doi>.
"""
import io, json, os, sys, time, hashlib, urllib.request, urllib.parse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = r"D:\Master Exers\Big Data\Recomendation_System"
PAPERS_DIR = os.path.join(ROOT, "docs", "References", "Papers")
os.makedirs(PAPERS_DIR, exist_ok=True)

TARGETS = [
    ("10.1145/3569930", "01_TOIS2022_DataLeakage_RS_OfflineEvaluation.pdf",
     "A Critical Study on Data Leakage in Recommender System Offline Evaluation"),
    ("10.1145/3637066", "02_TOIS2023_Reproducing_PopularityBias_EvaluationStrategies.pdf",
     "Reproducing Popularity Bias in Recommendation: The Effect of Evaluation Strategies"),
    ("10.1145/3705328.3748164", "03_RecSys2025_TimeToSplit.pdf",
     "Time to Split: Exploring Data Splitting Strategies for Offline Evaluation of Sequential Recommenders"),
    ("10.1145/3773078.3831818", "04_RecSys2026_ConvergentValidity_OfflineEvaluation.pdf",
     "On the Convergent Validity of Offline Evaluation Designs for Recommender Systems"),
    ("10.1145/3564284", "05_TOIS2022_Bias_Debias_Survey.pdf",
     "Bias and Debias in Recommender System: A Survey and Future Directions"),
    ("10.1007/s11257-024-09406-0", "06_UMAI2024_Survey_PopularityBias.pdf",
     "A survey on popularity bias in recommender systems"),
    ("10.1145/3539618.3591931", "07_SIGIR2023_FreshLook_EvaluationStandpoint.pdf",
     "Take a Fresh Look at Recommender Systems from an Evaluation Standpoint"),
    ("10.1145/3604915.3609495", "08_RecSys2023_Challenges_OfflineEvaluation.pdf",
     "On Challenges of Evaluating Recommender Systems in an Offline Setting"),
    ("10.1145/3705328.3748035", "09_RecSys2025_InheritedPopularityBias_ColdStart.pdf",
     "On Inherited Popularity Bias in Cold-Start Item Recommendation"),
]

# nguon dua khi API tra link hong dung
FALLBACK = {
    "10.1145/3569930": "https://arxiv.org/pdf/2010.11060",
    "10.1145/3637066": "https://ir.cwi.nl/pub/33989/33989.pdf",
    "10.1145/3705328.3748164": "https://arxiv.org/pdf/2507.16289",
    "10.1145/3773078.3831818": "https://arxiv.org/pdf/2607.25097",
    "10.1145/3564284": "https://arxiv.org/pdf/2010.03240",
    "10.1007/s11257-024-09406-0": "https://arxiv.org/pdf/2308.01118",
    "10.1145/3539618.3591931": "https://arxiv.org/pdf/2210.04149",
    "10.1145/3705328.3748035": "https://arxiv.org/pdf/2510.11402",
    "10.1145/3604915.3609495": "https://dl.acm.org/doi/pdf/10.1145/3604915.3609495",
}

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"

# Cookie header lay tu Chrome (CDP Storage.getCookies, domain dl.acm.org).
# Cloudflare chan request khong co cf_clearance; browser profile thi van load duoc.
ACM_COOKIE_HEADER = os.environ.get("ACM_COOKIE_HEADER", "").strip()


def http(url, timeout=90, accept="*/*", cookie=None, referer=None):
    headers = {"User-Agent": UA, "Accept": accept}
    if cookie:
        headers["Cookie"] = cookie
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def save_pdf(url, path, timeout=180):
    if "dl.acm.org" in url and ACM_COOKIE_HEADER:
        data = http(url, timeout, "application/pdf,*/*",
                    cookie=ACM_COOKIE_HEADER,
                    referer="https://dl.acm.org/doi/" + url.rsplit("/", 1)[-1])
    else:
        data = http(url, timeout, "application/pdf,*/*")
    if not data.startswith(b"%PDF"):
        raise ValueError("khong phai PDF (%d bytes): %s" % (len(data), data[:40]))
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def candidate_urls(doi):
    """Tra danh sach URL PDF theo thu tu uu tien."""
    urls = []
    try:
        j = json.loads(http("https://api.openalex.org/works/doi:" + urllib.parse.quote(doi), 60, "application/json").decode("utf-8"))
        locs = []
        for key in ("best_oa_location", "primary_location"):
            if j.get(key):
                locs.append(j[key])
        locs += (j.get("locations") or [])
        for loc in locs:
            pdf = loc.get("pdf_url") or ""
            if pdf and pdf not in urls:
                urls.append(pdf)
            landing = loc.get("landing_page_url") or ""
            if "arxiv.org" in landing:
                aid = landing.rstrip("/").split("/")[-1].replace("abs", "")
                u = "https://arxiv.org/pdf/" + aid
                if u not in urls:
                    urls.append(u)
    except Exception as e:
        print("  OpenAlex loi:", str(e)[:100])

    try:
        up = json.loads(http("https://api.unpaywall.org/v2/" + doi + "?email=nguyentran20051807@gmail.com",
                             60, "application/json").decode("utf-8"))
        for loc in up.get("oa_locations") or []:
            u = loc.get("url_for_pdf") or loc.get("url") or ""
            if u and u not in urls:
                urls.append(u)
    except Exception as e:
        print("  Unpaywall loi:", str(e)[:100])

    if doi in FALLBACK and FALLBACK[doi] not in urls:
        urls.append(FALLBACK[doi])
    return urls


manifest = []
for doi, fname, title in TARGETS:
    out = os.path.join(PAPERS_DIR, fname)
    print("=" * 74)
    print("DOI:", doi, "|", title[:62])
    rec = {"doi": doi, "file": fname, "title": title}

    if os.path.exists(out) and os.path.getsize(out) > 20000:
        print("  SKIP (da ton tai) %d bytes" % os.path.getsize(out))
        rec.update(bytes=os.path.getsize(out), sha256=sha256_of(out), status="cached")
        if doi in FALLBACK:
            rec["source"] = FALLBACK[doi]
        manifest.append(rec)
        continue

    ok = False
    for url in candidate_urls(doi):
        try:
            n = save_pdf(url, out)
            print("  OK -> %s (%d bytes)" % (url[:70], n))
            rec.update(bytes=n, sha256=sha256_of(out), status="ok", source=url)
            ok = True
            break
        except Exception as e:
            print("  fail %s : %s" % (url[:70], str(e)[:80]))

    if not ok:
        print("  -> can tai thu cong qua trinh duyet (Cloudflare chan script)")
        rec["status"] = "manual_required"
    manifest.append(rec)
    time.sleep(1.0)

mp = os.path.join(PAPERS_DIR, "_manifest.json")
io.open(mp, "w", encoding="utf-8").write(json.dumps(manifest, ensure_ascii=False, indent=2))

ok_n = sum(1 for m in manifest if m["status"] in ("ok", "cached"))
print("\n=== KET QUA ===")
print("san co: %d / %d" % (ok_n, len(manifest)))
for m in manifest:
    print("  %-14s %-58s %s" % (m["status"], m["file"], m.get("bytes", "")))
print("manifest:", mp)
