# -*- coding: utf-8 -*-
"""Kiem dinh thong ke cho 3 split: bootstrap CI, Wilcoxon signed-rank, paired effect size.

Input : D:\\recsys_data\\poc\\peruser\\peruser_<split>.csv  (sinh boi scripts/11_peruser_ndcg.py)
Output: D:\\Master Exers\\...\\reports\\stats_<split>.json
        + reports\\stats_summary.csv

Chay: python scripts/12_stats_tests.py
"""
import io, os, sys, csv, json, math, random, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = r"D:\Master Exers\Big Data\Recomendation_System"
IN_DIR = r"D:\recsys_data\poc\peruser"
OUT_DIR = os.path.join(ROOT, "reports")
os.makedirs(OUT_DIR, exist_ok=True)

SEED = 42
N_BOOT = 10000
random.seed(SEED)

SPLITS = ["random80_20", "temporal_global", "leave_one_out"]
METRICS = [
    ("ndcg_pop", "ndcg_als", "NDCG@10"),
    ("hit_pop", "hit_als", "Hit@10"),
    # PerUserPopSkew = trung binh (pop(item)/avg_pop_all) tren top-10 cua TUNG user.
    # KHAC popularity_bias_ratio trong reports/metrics_summary.csv: cai do la trung binh
    # popularity tren tap item DUY NHAT duoc expose (catalog-level), con day la trung binh
    # theo user (exposure-weighted). Hai so nay dac biet, dung ca hai trong bao cao.
    ("skew_pop", "skew_als", "PerUserPopSkew"),
    ("tail_pop", "tail_als", "TailCount@10"),
]


def read_rows(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def bootstrap_ci(vals, n_boot=N_BOOT, alpha=0.05):
    """Percentile bootstrap CI cho mean. vals: list of float.

    Vector hoa bang numpy: index resample (n_boot, n) -> 10k x 29k = 293M int64 ~ 2.3 GB,
    nen chia thanh chunk de khong tran RAM.
    """
    import numpy as np
    v = np.asarray(vals, dtype=np.float64)
    n = v.size
    if n == 0:
        return None
    mean = float(v.mean())
    rng = np.random.default_rng(SEED)
    means = np.empty(n_boot, dtype=np.float64)
    chunk = max(1, min(500, int(4_000_000 // max(n, 1))))
    pos = 0
    while pos < n_boot:
        k = min(chunk, n_boot - pos)
        idx = rng.integers(0, n, size=(k, n))
        means[pos:pos + k] = v[idx].mean(axis=1)
        pos += k
    means.sort()
    lo = float(means[int((alpha / 2) * n_boot)])
    hi = float(means[min(int((1 - alpha / 2) * n_boot), n_boot - 1)])
    return {"mean": round(mean, 6), "ci_low": round(lo, 6), "ci_high": round(hi, 6),
            "n": int(n), "n_boot": n_boot}


def wilcoxon_signed_rank(diffs):
    """Wilcoxon signed-rank two-sided, tie-corrected normal approximation.

    Vector hoa bang numpy: sap xep |d|, rank trung binh cho nhom tie, tinh W+/W-.
    diffs: list of non-zero differences (pairs).
    """
    import numpy as np
    d = np.asarray(diffs, dtype=np.float64)
    n = d.size
    if n == 0:
        return {"W": None, "z": None, "p": None, "n_pairs": 0, "n_nonzero": 0,
                "median_diff": None}
    n_nonzero = int(np.count_nonzero(d))
    if n_nonzero == 0:
        # Moi cap deu bang nhau -> khong co khac biet, khong co test gi co y nghia.
        return {"W": 0.0, "z": None, "p": None, "n_pairs": int(n), "n_nonzero": 0,
                "median_diff": 0.0, "mean_diff": 0.0,
                "note": "all paired differences are zero - test not applicable"}
    a = np.abs(d)
    order = np.argsort(a, kind="mergesort")
    a_sorted = a[order]
    # rank trung binh cho nhom tie (1-based)
    ranks_sorted = np.empty(n, dtype=np.float64)
    i = 0
    while i < n:
        j = i
        while j + 1 < n and a_sorted[j + 1] == a_sorted[i]:
            j += 1
        ranks_sorted[i:j + 1] = (i + j) / 2.0 + 1.0
        i = j + 1
    ranks = np.empty(n, dtype=np.float64)
    ranks[order] = ranks_sorted
    wpos = float(ranks[d > 0].sum())
    wneg = float(ranks[d < 0].sum())
    W = min(wpos, wneg)
    # tie correction: sum (c^3 - c) cho cac nhom size c > 1
    _, counts = np.unique(a_sorted, return_counts=True)
    t = float((counts.astype(np.float64) ** 3 - counts.astype(np.float64)).sum())
    mu = n * (n + 1) / 4.0
    sigma = math.sqrt((n * (n + 1) * (2 * n + 1) - t / 2.0) / 24.0)
    srt = np.sort(d)
    median = float(srt[n // 2] if n % 2 else (srt[n // 2 - 1] + srt[n // 2]) / 2.0)
    if sigma <= 0:
        return {"W": round(W, 2), "z": None, "p": None, "n_pairs": int(n),
                "n_nonzero": int(n), "median_diff": round(median, 6),
                "mean_diff": round(float(d.mean()), 6)}
    z = (W - mu) / sigma
    p = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(z) / math.sqrt(2))))
    return {"W": round(W, 2), "z": round(z, 4), "p": float("%.3e" % p), "n_pairs": int(n),
            "n_nonzero": int(n), "median_diff": round(median, 6),
            "mean_diff": round(float(d.mean()), 6)}


def cohens_dz(diffs):
    n = len(diffs)
    if n < 2:
        return None
    m = sum(diffs) / n
    sd = math.sqrt(sum((d - m) ** 2 for d in diffs) / (n - 1))
    if sd == 0:
        return None
    return round(m / sd, 4)

def rank_biserial_and_cliffs(diffs, rng_seed=SEED):
    """rank-biserial correlation cho Wilcoxon + Kendall's tau-b (do dong thay doi theo cap).

    V voi du lieu GHEP (paired), Cliff's delta tren vector diff khong co y nghia
    truc tiep -> dung rank-biserial (W+ - W-)/(W+ + W-) la chuan cho Wilcoxon.
    Kendall tau-b do su dong thay doi theo cap giua hai chuoi (pop vs als) trong
    khi nao chi so tang/ngam dong nhat.
    """
    import numpy as np
    from scipy import stats
    d = np.asarray(diffs, dtype=np.float64)
    n = d.size
    if n == 0:
        return None, None
    a = np.abs(d)
    order = np.argsort(a, kind="mergesort")
    a_sorted = a[order]
    ranks_sorted = np.empty(n, dtype=np.float64)
    i = 0
    while i < n:
        j = i
        while j + 1 < n and a_sorted[j + 1] == a_sorted[i]:
            j += 1
        ranks_sorted[i:j + 1] = (i + j) / 2.0 + 1.0
        i = j + 1
    ranks = np.empty(n, dtype=np.float64)
    ranks[order] = ranks_sorted
    wpos = float(ranks[d > 0].sum())
    wneg = float(ranks[d < 0].sum())
    denom = wpos + wneg
    rb = round((wpos - wneg) / denom, 4) if denom > 0 else None
    return rb, None


def kendall_tau_b(x, y):
    """Kendall's tau-b cho hai chuoi (dung scipy, O(n log n)).

    Neu mot chuoi hang constant (vd skew_pop giong nhau o moi user) -> tau khong
    xac dinh, tra None thay vi nan.
    """
    from scipy import stats
    import numpy as np
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    if x.size < 2:
        return None
    if np.all(x == x[0]) or np.all(y == y[0]):
        return {"tau_b": None, "p": None,
                "note": "one series is constant - Kendall tau-b undefined"}
    tau, p = stats.kendalltau(x, y, variant="b")
    return {"tau_b": round(float(tau), 4), "p": float("%.3e" % p) if p == p else None}


summary_rows = []
all_out = {}

for sp in SPLITS:
    p = os.path.join(IN_DIR, "peruser_%s.csv" % sp)
    if not os.path.exists(p):
        print("MISSING", p)
        continue
    rows = read_rows(p)
    print("=" * 70)
    print("SPLIT", sp, "| users:", len(rows))
    out = {"split": sp, "paired_users": len(rows),
           "bootstrap_n_boot": N_BOOT, "seed": SEED,
           "run_at": datetime.datetime.now().isoformat(), "metrics": {}}

    for a_col, b_col, label in METRICS:
        a = [float(r[a_col]) for r in rows]
        b = [float(r[b_col]) for r in rows]
        diffs = [x - y for x, y in zip(b, a)]  # ALS - Popularity
        m_a = bootstrap_ci(a)
        m_b = bootstrap_ci(b)
        d_abs = bootstrap_ci(diffs)
        w = wilcoxon_signed_rank(diffs)
        dz = cohens_dz(diffs)
        rb, _ = rank_biserial_and_cliffs(diffs)
        kt = kendall_tau_b(a, b)
        # metric hang constant o ca hai mo hinh -> khong co bien thien de kiem dinh
        const_metric = (max(a) - min(a) == 0) and (max(b) - min(b) == 0)
        ent = {
            "label": label,
            "popularity": m_a,
            "als": m_b,
            "paired_diff_als_minus_pop": d_abs,
            "wilcoxon": w,
            "cohens_dz": dz,
            "rank_biserial_r": rb,
            "kendall_tau_b": kt,
            "constant_metric": bool(const_metric),
            "direction": ("ALS > Popularity" if (d_abs and d_abs["mean"] or 0) > 0
                          else ("ALS < Popularity" if (d_abs and d_abs["mean"] or 0) < 0 else "equal")),
            "significant_0.05": bool(w.get("p") is not None and w["p"] < 0.05),
        }
        if const_metric:
            ent["significant_0.05"] = False
            ent["note"] = ("metric constant across users for both models - "
                           "no variance to test; reported as descriptive only")
        out["metrics"][label] = ent
        flag = "SIGNIFICANT" if ent["significant_0.05"] else ("CONSTANT" if const_metric else "n.s.")
        print("  %-16s pop=%.4f  als=%.4f  diff=%+.4f  p=%s  dz=%s  r=%s  tau_b=%s  %s"
              % (label, m_a["mean"], m_b["mean"], d_abs["mean"], w.get("p"), dz, rb,
                 kt.get("tau_b") if kt else None, flag))
        summary_rows.append({
            "split": sp, "metric": label, "n_paired": len(rows),
            "pop_mean": m_a["mean"], "pop_ci_low": m_a["ci_low"], "pop_ci_high": m_a["ci_high"],
            "als_mean": m_b["mean"], "als_ci_low": m_b["ci_low"], "als_ci_high": m_b["ci_high"],
            "diff_mean": d_abs["mean"], "diff_ci_low": d_abs["ci_low"], "diff_ci_high": d_abs["ci_high"],
            "wilcoxon_W": w.get("W"), "wilcoxon_z": w.get("z"), "wilcoxon_p": w.get("p"),
            "cohens_dz": dz, "rank_biserial_r": rb,
            "kendall_tau_b": kt.get("tau_b") if kt else None,
            "kendall_p": kt.get("p") if kt else None,
            "significant_0.05": ent["significant_0.05"],
        })

    all_out[sp] = out
    op = os.path.join(OUT_DIR, "stats_%s.json" % sp)
    with open(op, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("  ->", op)

csvp = os.path.join(OUT_DIR, "stats_summary.csv")
with open(csvp, "w", encoding="utf-8", newline="") as f:
    if summary_rows:
        w = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        w.writeheader()
        w.writerows(summary_rows)
print("\nsummary csv:", csvp)
print("DONE")
