# -*- coding: utf-8 -*-
"""Probe: doc shuffle bytes tu executed plan (Spark 4.x, AQE aware).

Voi AdaptiveSparkPlanExec phai lay finalPhysicalPlan() truoc khi lay metrics().
Chay: python scripts/_probe_shuffle_metrics.py
"""
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

_FAKE = r"C:\Users\PC\.openclaw\workspace\_fake_hadoop_home"
os.makedirs(_FAKE, exist_ok=True)
os.environ.setdefault("HADOOP_HOME", _FAKE)
os.environ.setdefault("PYSPARK_PYTHON", sys.executable)

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

PARQ = r"D:\recsys_data\parquet\ratings\part-00000.parquet"

spark = (SparkSession.builder
         .appName("ProbeShuffle").master("local[4]")
         .config("spark.sql.shuffle.partitions", "8")
         .config("spark.ui.showConsoleProgress", "false")
         .config("spark.sql.session.timeZone", "UTC")
         .getOrCreate())
spark.sparkContext.setLogLevel("ERROR")

df = spark.read.parquet(PARQ).select("userId", "movieId", "rating", "timestamp")
df = df.withColumn("year", F.year(F.from_unixtime(F.col("timestamp"))))
out = df.groupBy("movieId", "year").count()
n = out.count()
print("rows_out =", n)

plan = out._jdf.queryExecution().executedPlan()
print("plan class:", plan.getClass().getName())

# AQE: unwrap AdaptiveSparkPlanExec -> final physical plan
if hasattr(plan, "finalPhysicalPlan"):
    try:
        plan = plan.finalPhysicalPlan()
        print("final plan class:", plan.getClass().getName())
    except Exception as ex:
        print("finalPhysicalPlan failed:", ex)

m = plan.metrics()
it = m.entrySet().iterator()
shuffle_bytes = 0
shuffle_write_bytes = 0
while it.hasNext():
    e = it.next()
    key = e.getKey()
    val = e.getValue()
    try:
        nm = val.name()
        v = val.value()
    except Exception:
        continue
    try:
        nm = str(nm)
        v = int(v)
    except Exception:
        continue
    print("  metric:", key, "|", nm, "|", v)
    low = nm.lower()
    if "shuffle" in low and "write" in low:
        shuffle_write_bytes += v
    elif "shuffle" in low and "bytes" in low:
        shuffle_bytes += v
print("SHUFFLE_BYTES_WRITE:", shuffle_write_bytes)
print("SHUFFLE_BYTES_TOTAL:", shuffle_write_bytes + shuffle_bytes)

spark.stop()
print("DONE")
