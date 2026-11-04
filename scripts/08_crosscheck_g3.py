"""G3 quality gate - doi chieu MapReduce (Java) voi Spark SQL tren cung du lieu.
Chay: python scripts/08_crosscheck_g3.py
Output: D:\\recsys_data\\poc\\g3_crosscheck.json
"""
import os, sys, io, json, subprocess, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pyspark.sql import SparkSession, functions as F

PARQ = r"D:\recsys_data\parquet\ratings\part-00000.parquet"
OUT = r"D:\recsys_data\poc\g3_crosscheck.json"
CONTAINER = "namenode"
MR_OUT = "/recsys/out/popularity_by_year"

spark = (SparkSession.builder
         .appName("G3_Crosscheck").master("local[*]")
         .config("spark.sql.shuffle.partitions", "8")
         .config("spark.driver.memory", "6g")
         # QUAN TRONG: MapReduce dung SimpleDateFormat voi UTC.
         # Spark phai dung cung timezone de year() khop voi MR.
         .config("spark.sql.session.timeZone", "UTC")
         .getOrCreate())
spark.sparkContext.setLogLevel("WARN")

print("=== 1. Spark SQL: popularity theo (movieId, year) ===", flush=True)
df = (spark.read.parquet(PARQ)
      .withColumn("year", F.year(F.from_unixtime(F.col("timestamp")))))
spark_pop = (df.groupBy("movieId", "year").count()
             .select(F.col("movieId").cast("string"), F.col("year").cast("string"),
                     F.col("count").cast("long"))
             .toPandas())
print("spark rows:", len(spark_pop), flush=True)

# --- doc ket qua MapReduce tu HDFS ---
print("=== 2. Doc ket qua MapReduce tu HDFS ===", flush=True)
cmd = ["docker", "exec", CONTAINER, "bash", "-c",
       "export HADOOP_HOME=/opt/hadoop-3.2.1; export PATH=$PATH:$HADOOP_HOME/bin; "
       "hdfs dfs -cat /recsys/out/popularity_by_year/part-r-00000 2>/dev/null"]
r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
mr_lines = [l for l in r.stdout.splitlines() if l.strip()]
print("mr rows:", len(mr_lines), flush=True)

mr = {}
for l in mr_lines:
    try:
        k, v = l.rsplit("\t", 1)
        mid, yr = k.split(",")
        mr[(mid, yr)] = int(v)
    except ValueError:
        continue

# --- doi chieu ---
sp = {}
for _, row in spark_pop.iterrows():
    sp[(str(row["movieId"]), str(row["year"]))] = int(row["count"])

keys = set(mr) | set(sp)
diff = {k: (mr.get(k), sp.get(k)) for k in keys if mr.get(k) != sp.get(k)}
match = len(keys) - len(diff)

res = {
    "checked_at": datetime.datetime.now().isoformat(),
    "spark_rows": len(sp),
    "mapreduce_rows": len(mr),
    "union_keys": len(keys),
    "exact_match_keys": match,
    "mismatch_keys": len(diff),
    "match_pct": round(100.0 * match / max(1, len(keys)), 6),
    "spark_total_interactions": int(sum(sp.values())),
    "mapreduce_total_interactions": int(sum(mr.values())),
    "expected_total_interactions": 25000095,
    "sample_mismatch": [{"key": list(k), "mr": v[0], "spark": v[1]} for k, v in list(diff.items())[:10]],
    "gate_G3_passed": len(diff) == 0 and sum(sp.values()) == 25000095,
}
json.dump(res, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("\n=== KET QUA G3 ===")
for k, v in res.items():
    if k != "sample_mismatch":
        print(f"  {k}: {v}")
if res["sample_mismatch"]:
    print("  sample mismatch:", res["sample_mismatch"][:3])
print("SAVED", OUT)
spark.stop()
