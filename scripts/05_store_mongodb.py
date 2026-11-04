"""Nap ket qua audit (poc6) vao MongoDB + item_profile tu movies.csv.
Chay: python scripts/05_store_mongodb.py [--reset]
"""
import os, sys, io, json, csv, datetime, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pymongo import MongoClient, ASCENDING

OUT  = r"D:\recsys_data\poc"
BASE = r"D:\recsys_data\raw\ml-25m"
DB_NAME = "recsys"

ap = argparse.ArgumentParser()
ap.add_argument("--reset", action="store_true")
A = ap.parse_args()

client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=8000)
print("mongo ok:", client.server_info()["version"])
db = client[DB_NAME]
if A.reset:
    db.audit_metrics.drop(); db.item_profile.drop(); print("dropped")

db.audit_metrics.create_index([("split", ASCENDING), ("model", ASCENDING)], unique=True)
db.item_profile.create_index([("movieId", ASCENDING)], unique=True)

# ---- item_profile ----
if db.item_profile.count_documents({}) == 0:
    n = 0
    with open(os.path.join(BASE, "movies.csv"), "r", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            try:
                mid = int(row["movieId"])
            except (ValueError, KeyError):
                continue
            year = None
            t = (row.get("title") or "").rstrip()
            if t.endswith(")"):
                i = t.rfind("(")
                if i > 0:
                    try: year = int(t[i + 1:-1])
                    except ValueError: year = None
            genres = [g.strip() for g in (row.get("genres") or "").split("|") if g.strip()]
            db.item_profile.insert_one({"movieId": mid, "title": row.get("title"),
                                        "year": year, "genres": genres})
            n += 1
    print("item_profile inserted:", n)
else:
    print("item_profile already has", db.item_profile.count_documents({}), "docs")

# ---- audit_metrics ----
total = 0
for fn in sorted(os.listdir(OUT)):
    if not (fn.startswith("poc6_") and fn.endswith(".json")):
        continue
    R = json.load(open(os.path.join(OUT, fn), "r", encoding="utf-8"))
    split = R.get("split")
    base = {
        "split": split,
        "train_rows": R.get("train_rows"), "test_rows": R.get("test_rows"),
        "train_max_ts": R.get("train_max_ts"), "test_min_ts": R.get("test_min_ts"),
        "train_max_ts_iso": R.get("train_max_ts_iso"), "test_min_ts_iso": R.get("test_min_ts_iso"),
        "temporal_violation_global": R.get("temporal_violation_global"),
        "temporal_violation_global_pct": R.get("temporal_violation_global_pct"),
        "temporal_violation_user": R.get("temporal_violation_user"),
        "temporal_violation_user_pct": R.get("temporal_violation_user_pct"),
        "unseen_item_rows": R.get("unseen_item_rows"),
        "unseen_item_pct": R.get("unseen_item_pct"),
        "coldstart_user_rows": R.get("coldstart_user_rows"),
        "eval_users": R.get("eval_users"), "eval_test_rows": R.get("eval_test_rows"),
        "eval_relevant_users": R.get("eval_relevant_users"),
        "test_relevant_eval_rows": R.get("test_relevant_eval_rows"),
        "relevance_threshold": R.get("relevance_threshold"),
        "min_train_threshold": R.get("min_train_threshold"),
        "seed": R.get("seed"), "spark_version": R.get("spark_version"),
        "dataset": "MovieLens ml-25m",
        "run_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    for model_key in ("popularity", "als"):
        m = R.get(model_key)
        if not m or m.get("error"):
            continue
        doc = dict(base)
        doc.update({
            "model": "Popularity" if model_key == "popularity" else "ALS_implicit",
            "ndcg10": m.get("ndcg10"), "dcg10": m.get("dcg10"),
            "hit_rate10": m.get("hit_rate10"),
            "eval_users_model": m.get("eval_users"),
            "catalog_coverage": m.get("catalog_coverage"),
            "longtail_coverage": m.get("longtail_coverage"),
            "gini_exposure": m.get("gini_exposure"),
            "avg_pop_rec": m.get("avg_pop_rec"), "avg_pop_all": m.get("avg_pop_all"),
            "popularity_bias_ratio": m.get("popularity_bias_ratio"),
            "subsample_users": m.get("subsample_users"),
            "rank": m.get("rank"), "maxIter": m.get("maxIter"),
            "regParam": m.get("regParam"), "implicitPrefs": m.get("implicitPrefs"),
            "alpha": m.get("alpha"),
            "fit_seconds": m.get("fit_seconds"), "total_seconds": m.get("total_seconds"),
        })
        db.audit_metrics.replace_one({"split": split, "model": doc["model"]}, doc, upsert=True)
        total += 1
        print("  upsert %-16s %-13s ndcg=%-8s cov=%-10s tail=%-9s gini=%-8s bias=%s" % (
            split, doc["model"], doc["ndcg10"], doc["catalog_coverage"],
            doc["longtail_coverage"], doc["gini_exposure"], doc["popularity_bias_ratio"]))

print("audit_metrics upserted:", total)
print("\n--- BANG TONG HOP ---")
for d in db.audit_metrics.find({}, {"_id": 0, "split": 1, "model": 1, "ndcg10": 1,
        "hit_rate10": 1, "catalog_coverage": 1, "longtail_coverage": 1,
        "gini_exposure": 1, "popularity_bias_ratio": 1,
        "temporal_violation_global_pct": 1, "temporal_violation_user_pct": 1,
        "unseen_item_pct": 1, "eval_users": 1}).sort([("split", 1), ("model", 1)]):
    print(d)
