"""PoC v6 - FINAL: implicit ALS + nguong lien quan (rating >= 4)

Fix vua poc5 (phat hien quan trong - loi PHUONG PHAP chu phai loi code):
  - ALS EXPLICIT xep hang theo sai so DU DOAN RATING. Phim user cho diem 1.0
    se bi day xuong cuoi danh sach -> khong bao gio nam top-10 -> NDCG ~ 0.
  - Voi top-N recommendation, chuan la IMPLICIT FEEDBACK: chi xem tuong tac
    TICH DUC (rating >= 4) la relevant, va mo hinh implicit ALS.
  - Do do: relevance = test item co rating >= THRESH (mac dinh 4.0),
    ap dung GIOI HANG cho ca Popularity va ALS, cho ca 3 split -> so sanh cong bang.
  - implicitPrefs=True, alpha=10.0: confidence = alpha + rating implicit.

Output: D:\\recsys_data\\poc\\poc6_<split>.json
"""
import os, sys, io, json, time, datetime, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ["PYSPARK_PYTHON"] = sys.executable

LOG = open(r"C:\Users\PC\.openclaw\workspace\_poc6_out.txt", "a", encoding="utf-8")
def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.write(s + "\n"); LOG.flush()

import numpy as np
from collections import Counter
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.ml.recommendation import ALS

OUT  = r"D:\recsys_data\poc"
PARQ = r"D:\recsys_data\parquet\ratings"
TMP  = r"D:\recsys_data\spark_tmp"
os.makedirs(OUT, exist_ok=True); os.makedirs(TMP, exist_ok=True)

ap = argparse.ArgumentParser()
ap.add_argument("split", choices=["random80_20", "temporal_global", "leave_one_out"])
ap.add_argument("--seed", type=int, default=42)
ap.add_argument("--n-users", type=int, default=30000)
ap.add_argument("--rank", type=int, default=16)
ap.add_argument("--maxiter", type=int, default=8)
ap.add_argument("--reg", type=float, default=0.05)
ap.add_argument("--alpha", type=float, default=10.0)
ap.add_argument("--topn", type=int, default=10)
ap.add_argument("--min-train", type=int, default=5)
ap.add_argument("--thresh", type=float, default=4.0, help="nguong rating duoc coi la relevant")
A = ap.parse_args()
NAME = A.split
SEED = A.seed

spark = (SparkSession.builder
         .appName("RecSysAudit6_" + NAME).master("local[8]")
         .config("spark.sql.shuffle.partitions", "8")
         .config("spark.driver.memory", "8g")
         .config("spark.local.dir", TMP)
         .config("spark.ui.showConsoleProgress", "false")
         .config("spark.sql.session.timeZone", "UTC")
         .getOrCreate())
spark.sparkContext.setLogLevel("ERROR")
log("=== RUN", NAME, "thresh=%.1f n_users=%d rank=%d maxIter=%d alpha=%s" %
    (A.thresh, A.n_users, A.rank, A.maxiter, A.alpha))

def ts(x):
    if x is None: return None
    return datetime.datetime.fromtimestamp(int(x), datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

t0 = time.time()
df = spark.read.parquet(os.path.join(PARQ, "part-00000.parquet"))
df = df.select("userId", "movieId", "rating", "timestamp").repartition(8).persist()
n = df.count()
log("rows:", n, "(%.0fs)" % (time.time() - t0))
mn = df.agg(F.min("timestamp").alias("a"), F.max("timestamp").alias("b")).first()
log("ts range:", ts(mn["a"]), "->", ts(mn["b"]))
log("users:", df.select("userId").distinct().count(), "items:", df.select("movieId").distinct().count())

THR = None
if NAME == "random80_20":
    THR = df.select(F.expr("percentile_approx(timestamp, 0.8)").alias("t")).first()["t"]
    d = df.withColumn("is_test", F.rand(SEED) > F.lit(0.8))
elif NAME == "temporal_global":
    THR = df.select(F.expr("percentile_approx(timestamp, 0.8)").alias("t")).first()["t"]
    d = df.withColumn("is_test", F.col("timestamp") >= F.lit(THR))
else:
    w = Window.partitionBy("userId").orderBy(F.col("timestamp").desc(), F.col("movieId").asc())
    d = df.withColumn("rn", F.row_number().over(w)).withColumn("is_test", F.col("rn") == 1)
if THR is not None:
    log("temporal threshold P80:", ts(THR))

d = d.select("userId", "movieId", "rating", "timestamp", "is_test").persist()
train = d.filter(~F.col("is_test")).persist()
test  = d.filter(F.col("is_test")).persist()

# ---------------- tầng 1 ----------------
tr_n, te_n = train.count(), test.count()
mx = train.agg(F.max("timestamp").alias("m")).first()["m"]
mnts = test.agg(F.min("timestamp").alias("m")).first()["m"]
viol_g = test.filter(F.col("timestamp") < F.lit(mx)).count()
user_max_train = train.groupBy("userId").agg(F.max("timestamp").alias("umax"))
viol_u = test.join(F.broadcast(user_max_train), "userId").filter(F.col("timestamp") < F.col("umax")).count()
tu = train.select("userId").distinct()
cold_u = test.join(F.broadcast(tu), "userId", "left_anti").count()
ti = train.select("movieId").distinct()
unseen = test.join(F.broadcast(ti), "movieId", "left_anti").count()
elig = train.groupBy("userId").count().filter(F.col("count") >= F.lit(A.min_train)).select("userId")
elig_n = elig.count()
te_eval = test.join(F.broadcast(elig), "userId").count()
# so luong tuong tac TEST >= thresh (relevant) -> moc do "relevance" cua tung split
te_rel_all = test.filter(F.col("rating") >= F.lit(A.thresh)).count()
te_rel_eval = test.join(F.broadcast(elig), "userId").filter(F.col("rating") >= F.lit(A.thresh)).count()
# so user co it nhat 1 relevant trong test
te_rel_users = test.join(F.broadcast(elig), "userId").filter(F.col("rating") >= F.lit(A.thresh)) \
                  .select("userId").distinct().count()

R = dict(split=NAME, train_rows=tr_n, test_rows=te_n,
         train_max_ts=int(mx or 0), test_min_ts=int(mnts or 0),
         train_max_ts_iso=ts(mx), test_min_ts_iso=ts(mnts),
         temporal_violation_global=int(viol_g),
         temporal_violation_global_pct=round(100.0 * viol_g / te_n, 4) if te_n else 0.0,
         temporal_violation_user=int(viol_u),
         temporal_violation_user_pct=round(100.0 * viol_u / te_n, 4) if te_n else 0.0,
         unseen_item_rows=int(unseen),
         unseen_item_pct=round(100.0 * unseen / te_n, 4) if te_n else 0.0,
         coldstart_user_rows=int(cold_u),
         eval_users=int(elig_n), eval_test_rows=int(te_eval),
         relevance_threshold=A.thresh,
         test_relevant_rows=int(te_rel_all), test_relevant_eval_rows=int(te_rel_eval),
         eval_relevant_users=int(te_rel_users),
         min_train_threshold=A.min_train, seed=SEED, spark_version="4.2.0")
log("DATA", NAME, json.dumps(R, ensure_ascii=False))

def save():
    p = os.path.join(OUT, "poc6_%s.json" % NAME)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(R, f, indent=2, ensure_ascii=False)
    log("[checkpoint]", p)
save()

# ---------------- popularity baseline (relevance >= thresh) ----------------
def popularity_baseline():
    popdf = train.groupBy("movieId").count().withColumnRenamed("count", "pop")
    top_ids = [r["movieId"] for r in
               popdf.orderBy(F.col("pop").desc(), F.col("movieId").asc()).limit(A.topn).collect()]
    log("   top%d: %s" % (A.topn, top_ids))
    te = test.join(F.broadcast(elig), "userId").filter(F.col("rating") >= F.lit(A.thresh))
    gexpr = " + ".join("if(movieId = %d, 1.0/log2(%d), 0.0)" % (m, i + 2)
                        for i, m in enumerate(top_ids))
    te = te.withColumn("dcg", F.expr(gexpr))
    per_user = te.groupBy("userId").agg(F.sum("dcg").alias("dcg"), F.count("*").alias("nrel"))
    idcg_terms = ", ".join("1.0/log2(%d)" % (i + 2) for i in range(A.topn))
    per_user = per_user.withColumn("idcg", F.expr(
        "aggregate(slice(array(%s), 1, least(nrel, %d)), 0D, (acc, x) -> acc + x)"
        % (idcg_terms, A.topn)))
    per_user = per_user.withColumn("ndcg",
        F.when(F.col("idcg") > 0, F.col("dcg") / F.col("idcg")).otherwise(0.0))
    agg = per_user.agg(F.count("*").alias("users"), F.avg("ndcg").alias("ndcg10"),
                        F.avg("dcg").alias("dcg10")).first()
    pop_map = {r["movieId"]: r["pop"] for r in popdf.select("movieId", "pop").collect()}
    n_items = len(pop_map)
    exposed = set(top_ids)
    cov = len(exposed) / max(n_items, 1)
    all_pop = sorted(pop_map.values())
    thr20 = all_pop[int(len(all_pop) * 0.2)] if all_pop else 0
    tail_items = {m for m, p in pop_map.items() if p <= thr20}
    tail_cov = len(exposed & tail_items) / max(len(tail_items), 1)
    avg_pop_rec = float(np.mean([pop_map[m] for m in exposed])) if exposed else 0.0
    avg_pop_all = float(np.mean(all_pop)) if all_pop else 0.0
    expo = sorted([agg["users"] or 0] * len(exposed) + [0] * max(n_items - len(exposed), 0))
    tot = sum(expo); gini = 0.0
    if tot > 0:
        nE = len(expo)
        cum = sum((i + 1) * v for i, v in enumerate(expo))
        gini = (2 * cum) / (nE * tot) - (nE + 1) / nE
    r = dict(model="popularity", ndcg10=round(float(agg["ndcg10"] or 0), 4),
             dcg10=round(float(agg["dcg10"] or 0), 4), eval_users=int(agg["users"] or 0),
             catalog_coverage=round(cov, 6), longtail_coverage=round(tail_cov, 6),
             gini_exposure=round(float(gini), 4),
             avg_pop_rec=round(avg_pop_rec, 2), avg_pop_all=round(avg_pop_all, 2),
             popularity_bias_ratio=round(avg_pop_rec / avg_pop_all, 4) if avg_pop_all else 0.0)
    log("POP", NAME, json.dumps(r, ensure_ascii=False))
    return r

R["popularity"] = popularity_baseline()
save()

# ---------------- implicit ALS + numpy top-K ----------------
def als_run():
    t0 = time.time()
    sub_users = train.select("userId").distinct().orderBy("userId").limit(A.n_users).select("userId")
    tr = train.join(F.broadcast(sub_users), "userId").persist()
    te = test.join(F.broadcast(sub_users), "userId").persist()
    # implicit: chi phai tuong tac POSITIVE (rating >= thresh)
    tr_pos = tr.filter(F.col("rating") >= F.lit(A.thresh)).persist()
    tr_n2, te_n2, trp_n = tr.count(), te.count(), tr_pos.count()
    log("   ALS subsample train=%d test=%d positive_train=%d" % (tr_n2, te_n2, trp_n))
    als = ALS(userCol="userId", itemCol="movieId", ratingCol="rating",
              rank=A.rank, maxIter=A.maxiter, regParam=A.reg,
              implicitPrefs=True, alpha=A.alpha,
              coldStartStrategy="drop", seed=SEED)
    m = als.fit(tr_pos)
    fit_s = time.time() - t0
    uf = m.userFactors.select("id", "features").collect()
    itf = m.itemFactors.select("id", "features").collect()
    U = np.array([r["features"] for r in uf], dtype=np.float32)
    ui = np.array([r["id"] for r in uf], dtype=np.int64)
    V = np.array([r["features"] for r in itf], dtype=np.float32)
    vi = np.array([r["id"] for r in itf], dtype=np.int64)
    o = np.argsort(ui); ui, U = ui[o], U[o]
    o = np.argsort(vi); vi, V = vi[o], V[o]
    log("   ALS fit %.0fs  U%s V%s" % (fit_s, U.shape, V.shape))
    vi_pos = {int(mid): j for j, mid in enumerate(vi)}

    elig2 = tr.groupBy("userId").count().filter(F.col("count") >= F.lit(A.min_train)).select("userId")
    truth = {r["userId"]: set(r["rel"]) for r in
             te.join(F.broadcast(elig2), "userId")
               .filter(F.col("rating") >= F.lit(A.thresh))
               .groupBy("userId").agg(F.collect_list("movieId").alias("rel")).collect()}
    seen = {r["userId"]: set(r["rel"]) for r in
            tr.groupBy("userId").agg(F.collect_list("movieId").alias("rel")).collect()}
    log("   truth users=%d  seen users=%d" % (len(truth), len(seen)))

    disc = 1.0 / np.log2(np.arange(2, A.topn + 2))
    rec = {}
    B = 2000
    t1 = time.time()
    for s in range(0, len(ui), B):
        e = min(s + B, len(ui))
        sc = U[s:e] @ V.T
        for i in range(s, e):
            u = int(ui[i])
            if u not in truth:
                continue
            sv = seen.get(u)
            if sv:
                idxs = [vi_pos[x] for x in sv if x in vi_pos]
                if idxs:
                    sc[i - s, idxs] = -np.inf
            idx = np.argpartition(-sc[i - s], A.topn)[:A.topn]
            idx = idx[np.argsort(-sc[i - s, idx])]
            rec[u] = vi[idx]
        if (s // B) % 5 == 0:
            log("   top-K progress %d/%d (%.0fs)" % (e, len(ui), time.time() - t1))
    log("   top-K done %.0fs, rec users=%d" % (time.time() - t1, len(rec)))

    ndcgs = []
    hit1 = 0
    for u, rel in truth.items():
        r10 = rec.get(u)
        if r10 is None or not rel:
            continue
        dcg = 0.0
        for i, mv in enumerate(r10):
            if int(mv) in rel:
                dcg += disc[i]
                if i == 0: hit1 += 1
        idcg = disc[:min(len(rel), A.topn)].sum()
        if idcg > 0:
            ndcgs.append(dcg / idcg)
    ndcg = float(np.mean(ndcgs)) if ndcgs else 0.0
    hr10 = hit1 / max(len(ndcgs), 1)

    exposed = [int(mv) for lst in rec.values() for mv in lst]
    uniq = set(exposed)
    popdf = tr.groupBy("movieId").count().withColumnRenamed("count", "pop")
    pop = {r["movieId"]: r["pop"] for r in popdf.select("movieId", "pop").collect()}
    n_items = len(pop)
    cov = len(uniq) / max(n_items, 1)
    all_pop = sorted(pop.values())
    thr20 = all_pop[int(len(all_pop) * 0.2)] if all_pop else 0
    tail_items = {mm for mm, p in pop.items() if p <= thr20}
    tail_cov = len(uniq & tail_items) / max(len(tail_items), 1)
    cnt = Counter(exposed)
    exp = sorted(cnt.get(int(i), 0) for i in vi)
    tot = sum(exp); gini = 0.0
    if tot > 0:
        nE = len(exp)
        cum = sum((i + 1) * v for i, v in enumerate(exp))
        gini = (2 * cum) / (nE * tot) - (nE + 1) / nE
    avg_pop_rec = float(np.mean([pop.get(mv, 0) for mv in uniq])) if uniq else 0.0
    avg_pop_all = float(np.mean(all_pop)) if all_pop else 0.0
    r = dict(model="ALS_implicit", ndcg10=round(ndcg, 4), hit_rate10=round(hr10, 4),
             eval_users=len(ndcgs),
             catalog_coverage=round(cov, 6), longtail_coverage=round(tail_cov, 6),
             gini_exposure=round(float(gini), 4),
             avg_pop_rec=round(avg_pop_rec, 2), avg_pop_all=round(avg_pop_all, 2),
             popularity_bias_ratio=round(avg_pop_rec / avg_pop_all, 4) if avg_pop_all else 0.0,
             subsample_users=int(A.n_users), rank=A.rank, maxIter=A.maxiter,
             regParam=A.reg, implicitPrefs=True, alpha=A.alpha, seed=SEED,
             relevance_threshold=A.thresh,
             fit_seconds=round(fit_s, 1), total_seconds=round(time.time() - t0, 1))
    log("ALS", NAME, json.dumps(r, ensure_ascii=False))
    tr.unpersist(); te.unpersist(); tr_pos.unpersist()
    return r

try:
    R["als"] = als_run()
except Exception as e:
    import traceback; traceback.print_exc(file=LOG); LOG.flush()
    log("   ALS FAILED:", repr(e))
    R["als"] = {"error": repr(e)}
save()
log("SAVED", os.path.join(OUT, "poc6_%s.json" % NAME))
spark.stop()
log("DONE", NAME)
