"""Per-user NDCG@10 + per-user popularity skew cho 3 split -> CSV cho kiem dinh thong ke.

Dong vai voi scripts/04_audit_spark.py (cung tham so ALS) nhung luu them:
  - ndcg_pop, ndcg_als, hit_pop, hit_als  (per user)
  - skew_pop, skew_als = mean(pop(item)/avg_pop_all) tren top-10 goi y cho user do
  - tail_cnt_pop, tail_cnt_als = so item long-tail (pop <= P20) trong top-10
Kết quả ghi: D:\\recsys_data\\poc\\peruser\\peruser_<split>.csv  +  summary JSON

Chay: python scripts/11_peruser_ndcg.py [split ...]
"""
import os, sys, io, json, time, datetime, argparse, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ["PYSPARK_PYTHON"] = sys.executable

ROOT = r"D:\Master Exers\Big Data\Recomendation_System"
OUTDIR = r"D:\recsys_data\poc\peruser"
os.makedirs(OUTDIR, exist_ok=True)
LOGP = os.path.join(OUTDIR, "peruser_run.log")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    with open(LOGP, "a", encoding="utf-8") as f:
        f.write(datetime.datetime.now().strftime("%H:%M:%S ") + s + "\n")


import numpy as np
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.ml.recommendation import ALS

PARQ = r"D:\recsys_data\parquet\ratings"
TMP = r"D:\recsys_data\spark_tmp"
os.makedirs(TMP, exist_ok=True)

TOPN = 10
THR = 4.0
MIN_TRAIN = 5
N_USERS = 30000
RANK, MAXITER, REG, ALPHA = 16, 8, 0.05, 10.0
SEED = 42

ap = argparse.ArgumentParser()
ap.add_argument("splits", nargs="*",
                default=["random80_20", "temporal_global", "leave_one_out"])
A = ap.parse_args()

spark = (SparkSession.builder
         .appName("RecSysPerUser").master("local[8]")
         .config("spark.sql.shuffle.partitions", "8")
         .config("spark.driver.memory", "8g")
         .config("spark.local.dir", TMP)
         .config("spark.ui.showConsoleProgress", "false")
         .config("spark.sql.session.timeZone", "UTC")
         .getOrCreate())
spark.sparkContext.setLogLevel("ERROR")
log("=== START", datetime.datetime.now().isoformat(), "splits=", A.splits)


def ts(x):
    if x is None:
        return None
    return datetime.datetime.fromtimestamp(int(x), datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


df = spark.read.parquet(os.path.join(PARQ, "part-00000.parquet"))
df = df.select("userId", "movieId", "rating", "timestamp").repartition(8).persist()
log("rows:", df.count())

summary = {}
for NAME in A.splits:
    t0 = time.time()
    log("---- SPLIT", NAME)
    THR_TS = None
    if NAME == "random80_20":
        THR_TS = df.select(F.expr("percentile_approx(timestamp, 0.8)").alias("t")).first()["t"]
        d = df.withColumn("is_test", F.rand(42) > F.lit(0.8))
    elif NAME == "temporal_global":
        THR_TS = df.select(F.expr("percentile_approx(timestamp, 0.8)").alias("t")).first()["t"]
        d = df.withColumn("timestamp") if False else df.withColumn("is_test", F.col("timestamp") >= F.lit(THR_TS))
    else:
        w = Window.partitionBy("userId").orderBy(F.col("timestamp").desc(), F.col("movieId").asc())
        d = df.withColumn("rn", F.row_number().over(w)).withColumn("is_test", F.col("rn") == 1)
    d = d.select("userId", "movieId", "rating", "timestamp", "is_test").persist()
    train = d.filter(~F.col("is_test")).persist()
    test = d.filter(F.col("is_test")).persist()
    tr_n, te_n = train.count(), test.count()
    log("  train=%d test=%d" % (tr_n, te_n))

    # eligible users (train >= MIN_TRAIN)
    elig = train.groupBy("userId").count().filter(F.col("count") >= F.lit(MIN_TRAIN)).select("userId")
    elig_ids = {r["userId"] for r in elig.collect()}
    log("  eligible users:", len(elig_ids))

    # popularity cua tung item ( tren TRAIN )
    popdf = train.groupBy("movieId").count().withColumnRenamed("count", "pop")
    pop_map = {int(r["movieId"]): int(r["pop"]) for r in popdf.select("movieId", "pop").collect()}
    all_pop = sorted(pop_map.values())
    avg_pop_all = float(np.mean(all_pop)) if all_pop else 0.0
    p20 = all_pop[int(len(all_pop) * 0.2)] if all_pop else 0
    tail_items = {m for m, p in pop_map.items() if p <= p20}
    log("  items=%d avg_pop_all=%.2f p20=%d tail_items=%d" % (len(pop_map), avg_pop_all, p20, len(tail_items)))

    top_pop = [int(r["movieId"]) for r in
               popdf.orderBy(F.col("pop").desc(), F.col("movieId").asc()).limit(TOPN).collect()]
    log("  popularity top10:", top_pop)

    # truth (relevant test items) cho eligible users
    truth = {int(r["userId"]): set(int(x) for x in r["rel"]) for r in
             test.join(F.broadcast(elig), "userId")
               .filter(F.col("rating") >= F.lit(THR))
               .groupBy("userId").agg(F.collect_list("movieId").alias("rel")).collect()}
    seen = {int(r["userId"]): set(int(x) for x in r["rel"]) for r in
            train.groupBy("userId").agg(F.collect_list("movieId").alias("rel")).collect()}
    log("  truth users=%d seen users=%d" % (len(truth), len(seen)))

    disc = 1.0 / np.log2(np.arange(2, TOPN + 2))

    def ndcg_of(rank_list, rel):
        dcg = 0.0
        hit = 0
        for i, mv in enumerate(rank_list):
            if mv in rel:
                dcg += disc[i]
                if i == 0:
                    hit = 1
        idcg = disc[:min(len(rel), TOPN)].sum()
        return (dcg / idcg if idcg > 0 else 0.0), hit

    def skew_of(rank_list):
        if not rank_list or avg_pop_all <= 0:
            return 0.0, 0
        sk = float(np.mean([pop_map.get(mv, 0) / avg_pop_all for mv in rank_list]))
        tc = sum(1 for mv in rank_list if mv in tail_items)
        return sk, tc

    # ---------------- ALS implicit (cung tham so nhu 04_audit_spark.py) ----------------
    sub_users = train.select("userId").distinct().limit(N_USERS).select("userId")
    tr = train.join(F.broadcast(sub_users), "userId").persist()
    tr_pos = tr.filter(F.col("rating") >= F.lit(THR)).persist()
    als = ALS(userCol="userId", itemCol="movieId", ratingCol="rating",
              rank=RANK, maxIter=MAXITER, regParam=REG, implicitPrefs=True, alpha=ALPHA,
              coldStartStrategy="drop", seed=SEED)
    m = als.fit(tr_pos)
    uf = m.userFactors.select("id", "features").collect()
    itf = m.itemFactors.select("id", "features").collect()
    U = np.array([r["features"] for r in uf], dtype=np.float32)
    ui = np.array([r["id"] for r in uf], dtype=np.int64)
    V = np.array([r["features"] for r in itf], dtype=np.float32)
    vi = np.array([r["id"] for r in itf], dtype=np.int64)
    o = np.argsort(ui); ui, U = ui[o], U[o]
    o = np.argsort(vi); vi, V = vi[o], V[o]
    vi_pos = {int(mid): j for j, mid in enumerate(vi)}
    log("  ALS U%s V%s" % (U.shape, V.shape))

    als_rec = {}
    B = 2000
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
            idx = np.argpartition(-sc[i - s], TOPN)[:TOPN]
            idx = idx[np.argsort(-sc[i - s, idx])]
            als_rec[u] = [int(vi[j]) for j in idx]
    log("  ALS rec users:", len(als_rec))

    # ---------------- ghi per-user CSV ----------------
    # tap user dung de so sanh capoi: eligible co truth
    rows = []
    for u, rel in truth.items():
        if not rel:
            continue
        pop_rank = top_pop
        n_pop, h_pop = ndcg_of(pop_rank, rel)
        sk_pop, tc_pop = skew_of(pop_rank)
        ar = als_rec.get(u)
        if ar is None:
            continue
        n_als, h_als = ndcg_of(ar, rel)
        sk_als, tc_als = skew_of(ar)
        rows.append((u, len(rel), round(n_pop, 6), h_pop, round(sk_pop, 6), tc_pop,
                     round(n_als, 6), h_als, round(sk_als, 6), tc_als))

    csv_path = os.path.join(OUTDIR, "peruser_%s.csv" % NAME)
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["userId", "n_rel", "ndcg_pop", "hit_pop", "skew_pop", "tail_pop",
                    "ndcg_als", "hit_als", "skew_als", "tail_als"])
        w.writerows(rows)
    log("  CSV rows=%d -> %s" % (len(rows), csv_path))

    arr = np.array([(r[2], r[6], r[4], r[8], r[1]) for r in rows], dtype=np.float64)
    s = {
        "split": NAME,
        "paired_users": int(len(rows)),
        "ndcg_pop_mean": round(float(arr[:, 0].mean()), 4) if len(arr) else None,
        "ndcg_als_mean": round(float(arr[:, 1].mean()), 4) if len(arr) else None,
        "hit_pop_mean": round(float(arr[:, 0].size and np.mean([r[3] for r in rows])), 4) if len(rows) else None,
        "hit_als_mean": round(float(np.mean([r[7] for r in rows])), 4) if len(rows) else None,
        "skew_pop_mean": round(float(arr[:, 2].mean()), 4) if len(arr) else None,
        "skew_als_mean": round(float(arr[:, 3].mean()), 4) if len(arr) else None,
        "tail_pop_mean": round(float(np.mean([r[5] for r in rows])), 4) if len(rows) else None,
        "tail_als_mean": round(float(np.mean([r[9] for r in rows])), 4) if len(rows) else None,
        "train_rows": int(tr_n), "test_rows": int(te_n),
        "eligible_users": int(len(elig_ids)), "avg_pop_all": round(avg_pop_all, 2),
        "items": int(len(pop_map)), "tail_items": int(len(tail_items)),
        "params": {"topn": TOPN, "thresh": THR, "min_train": MIN_TRAIN,
                   "n_users": N_USERS, "rank": RANK, "maxIter": MAXITER,
                   "reg": REG, "alpha": ALPHA, "seed": SEED},
        "seconds": round(time.time() - t0, 1),
        "run_at": datetime.datetime.now().isoformat(),
    }
    summary[NAME] = s
    log("  SUMMARY " + json.dumps(s, ensure_ascii=False))
    for x in (d, train, test, tr, tr_pos):
        try:
            x.unpersist()
        except Exception:
            pass

with open(os.path.join(OUTDIR, "peruser_summary.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
log("=== DONE", datetime.datetime.now().isoformat())
spark.stop()
