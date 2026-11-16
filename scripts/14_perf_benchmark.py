# -*- coding: utf-8 -*-
"""Do hieu nang Big Data: wall-clock + shuffle bytes cho MapReduce (YARN) va Spark SQL.

Yeu cau container Hadoop 5 node dang chay + du lieu /recsys/ratings_csv tren HDFS.

Do 3 lan moi pipeline de lay trung binh, co median.
- MapReduce: dung `hadoop jar` len container namenode, do bang `date +%s` quanh lenh,
  lay metrics tu YARN REST API (http://<resourcemanager>:8088/ws/v1/cluster/apps).
- Spark: do wall-clock trong Python, do shuffle bytes qua SparkListener (accumulator).

Output: D:\\Master Exers\\...\\reports\\perf_<engine>.json + reports\\perf_summary.csv
Chay: python scripts/14_perf_benchmark.py
"""
import io, os, sys, json, time, csv, subprocess, datetime, statistics, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Hadoop Shell class throws FileNotFoundException neu HADOOP_HOME va hadoop.home.dir
# deu unset -> Spark fail o prepareSubmitEnvironment. Dat env gia de qua check,
# winutils thieu chi la warning (local mode van chay).
_FAKE_HADOOP = r"C:\Users\PC\.openclaw\workspace\_fake_hadoop_home"
os.makedirs(_FAKE_HADOOP, exist_ok=True)
os.environ.setdefault("HADOOP_HOME", _FAKE_HADOOP)
os.environ.setdefault("PYSPARK_PYTHON", sys.executable)

ROOT = r"D:\Master Exers\Big Data\Recomendation_System"
OUT_DIR = os.path.join(ROOT, "reports")
os.makedirs(OUT_DIR, exist_ok=True)

CONTAINER = "namenode"
RM_HOST = "resourcemanager"
RM_URL = "http://%s:8088" % RM_HOST
HDFS_IN = "/recsys/ratings_csv"
HDFS_OUT = "/recsys/out/popularity_by_year"
JAR = "/tmp/mrbuild/popularity.jar"
REPEAT = 3

HADOOP_ENV = (
    "export HADOOP_HOME=/opt/hadoop-3.2.1; "
    "export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin; "
    "export HADOOP_CLASSPATH=$HADOOP_HOME/etc/hadoop:"
    "$HADOOP_HOME/share/hadoop/common/*:$HADOOP_HOME/share/hadoop/common/lib/*:"
    "$HADOOP_HOME/share/hadoop/hdfs/*:$HADOOP_HOME/share/hadoop/hdfs/lib/*:"
    "$HADOOP_HOME/share/hadoop/mapreduce/*:$HADOOP_HOME/share/hadoop/mapreduce/lib/*; "
    "export HADOOP_MAPRED_HOME=$HADOOP_HOME/share/hadoop/mapreduce; "
)


def sh(cmd, timeout=1800):
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def docker_sh(script, timeout=1800):
    return sh(["docker", "exec", CONTAINER, "bash", "-c", HADOOP_ENV + script], timeout=timeout)


def yarn_apps():
    try:
        r = sh(["docker", "exec", CONTAINER, "bash", "-c",
                "curl -s %s/ws/v1/cluster/apps?states=RUNNING,FINISHED,ACCEPTED" % RM_URL], 60)
        return json.loads(r.stdout)
    except Exception as e:
        print("  YARN REST loi:", str(e)[:120])
        return None


def pick_mr_app(apps, since_ts):
    """Chon app MapReduce moi nhat >= since_ts."""
    if not apps:
        return None
    apps = apps.get("apps") or {}
    app = apps.get("app") or []
    best = None
    for a in app:
        if a.get("name", "").startswith("PopularityByYear"):
            st = a.get("startedTime")
            if st and st >= since_ts:
                if best is None or st > best.get("startedTime"):
                    best = a
    return best


def mr_metrics(app):
    if not app:
        return {}
    out = {}
    out["application_id"] = app.get("id")
    out["state"] = app.get("state")
    out["final_status"] = app.get("finalStatus")
    out["started_time"] = app.get("startedTime")
    out["finished_time"] = app.get("finishedTime")
    if out["started_time"] and out["finished_time"]:
        out["yarn_wallclock_ms"] = out["finished_time"] - out["started_time"]
    for m in app.get("metrics") or []:
        if m.get("key") in (" shuffleBytes ", " shuffleBytes",
                             " elapsedTime ", " elapsedTime",
                             " mapInputBytes ", " mapInputBytes",
                             " reduceOutputBytes ", " reduceOutputBytes"):
            out[m["key"].strip()] = m["value"]
    counters = {}
    for c in app.get("counters") or []:
        for k in (c.get("counterGroupName") or "").lower().split(","):
            pass
    # YARN counters: dua vao dict de doc nhanh
    try:
        for c in app.get("counters") or []:
            for cn in c.get("counters") or []:
                counters[cn.get("name")] = cn.get("totalCounterValue")
    except Exception:
        pass
    out["counters"] = counters
    return out


def run_mapreduce_once():
    t0 = time.time()
    since = int(t0 * 1000)
    script = (
        "hdfs dfs -rm -r -f {out} >/dev/null 2>&1 || true; "
        "START=$(date +%s%3N); "
        "hadoop jar {jar} PopularityByYear {hin} {out} > /tmp/mr_run.log 2>&1; RC=$?; "
        "END=$(date +%s%3N); "
        "echo MR_RC=$RC; echo MR_WALL_MS=$((END-START)); "
        "cat /tmp/mr_run.log | tail -25"
    ).format(out=HDFS_OUT, jar=JAR, hin=HDFS_IN)
    r = docker_sh(script, 3600)
    wall = None
    rc = None
    for line in r.stdout.splitlines():
        m = re.match(r"MR_RC=(\d+)", line.strip())
        if m:
            rc = int(m.group(1))
        m = re.match(r"MR_WALL_MS=(\d+)", line.strip())
        if m:
            wall = int(m.group(1))
    app = pick_mr_app(yarn_apps(), since)
    met = mr_metrics(app)
    met.update({"exit_code": rc, "client_wallclock_ms": wall,
                "host_elapsed_ms": int((time.time() - t0) * 1000)})
    return met


def make_spark():
    from pyspark.sql import SparkSession
    return (SparkSession.builder
            .appName("PerfBenchmark").master("local[4]")
            .config("spark.sql.shuffle.partitions", "8")
            .config("spark.driver.memory", "6g")
            .config("spark.local.dir", r"D:\recsys_data\spark_tmp")
            .config("spark.ui.showConsoleProgress", "false")
            .config("spark.sql.session.timeZone", "UTC")
            .getOrCreate())


_SHUFFLE = {"value": 0}


def _install_shuffle_listener(spark):
    """Gan listener MOT LAN cho ca SparkSession.

    Gan nhieu listener se lam moi listener dem lai cung mot byte -> so shuffle
    bytes phong dao theo so lan chay. Listener nen ton tai suot session,
    moi run do baseline de lay delta.
    """
    if getattr(spark.sparkContext, "_shuffle_listener_installed", False):
        return
    from pyspark.scheduler import SparkListener

    class L(SparkListener):
        def onTaskEnd(self, e):
            m = e.taskMetrics
            if m and m.shuffleWriteMetrics and m.shuffleWriteMetrics.bytesWritten:
                _SHUFFLE["value"] += m.shuffleWriteMetrics.bytesWritten

    try:
        spark.sparkContext.addSparkListener(L())
    except Exception:
        spark.sparkContext._jsc.sc().addSparkListener(L())
    spark.sparkContext._shuffle_listener_installed = True
    print("  shuffle listener: da gan (session-wide)", flush=True)


def run_spark_once(spark):
    """Mot lan do wall-clock + shuffle bytes. Reuse cung mot SparkSession (Spark
    khong cho tao moi SparkSession sau khi stop trong cung JVM)."""
    from pyspark.sql import functions as F
    parq = r"D:\recsys_data\parquet\ratings\part-00000.parquet"

    spark.sparkContext.setLogLevel("ERROR")
    _install_shuffle_listener(spark)
    baseline = _SHUFFLE["value"]

    t0 = time.time()
    df = spark.read.parquet(parq).select("userId", "movieId", "rating", "timestamp")
    df = df.withColumn("year", F.year(F.from_unixtime(F.col("timestamp"))))
    df.cache().count()
    t_read = time.time() - t0

    t1 = time.time()
    out = (df.groupBy("movieId", "year").count())
    n = out.count()          # trigger shuffle
    t_shuffle = time.time() - t1

    t2 = time.time()
    (df.groupBy("movieId", "year").count()
       .write.mode("overwrite").parquet(r"D:\recsys_data\poc\perf_spark_out"))
    t_write = time.time() - t2

    res = {
        "engine": "Spark-SQL(local[8])",
        "read_seconds": round(t_read, 2),
        "shuffle_aggregate_seconds": round(t_shuffle, 2),
        "write_parquet_seconds": round(t_write, 2),
        "total_seconds": round(time.time() - t0, 2),
        "rows_out": int(n),
        "shuffle_write_bytes": int(_SHUFFLE["value"] - baseline),
        "shuffle_write_mb": round((_SHUFFLE["value"] - baseline) / (1024 ** 2), 2),
        "shuffle_partitions": 8,
    }
    return res


def agg_runs(runs, key):
    vals = [r[key] for r in runs if r.get(key) is not None]
    if not vals:
        return None
    return {"min": min(vals), "median": statistics.median(vals),
            "max": max(vals), "mean": round(sum(vals) / len(vals), 2), "n": len(vals)}


def main():
    results = {"generated_at": datetime.datetime.now().isoformat(), "repeat": REPEAT}

    print("=== A) Spark SQL benchmark (%d lan) ===" % REPEAT, flush=True)
    spark_runs = []
    spark = make_spark()
    for i in range(REPEAT):
        r = run_spark_once(spark)
        spark_runs.append(r)
        print("  run %d: %s" % (i + 1, json.dumps(r, ensure_ascii=False)), flush=True)
    spark.stop()
    results["spark"] = {"runs": spark_runs,
                        "total_seconds": agg_runs(spark_runs, "total_seconds"),
                        "shuffle_aggregate_seconds": agg_runs(spark_runs, "shuffle_aggregate_seconds"),
                        "shuffle_write_bytes": agg_runs(spark_runs, "shuffle_write_bytes")}

    print("\n=== B) MapReduce benchmark (%d lan) ===" % REPEAT, flush=True)
    mr_runs = []
    for i in range(REPEAT):
        r = run_mapreduce_once()
        mr_runs.append(r)
        print("  run %d: %s" % (i + 1, json.dumps(r, ensure_ascii=False)[:400]), flush=True)
    results["mapreduce"] = {"runs": mr_runs,
                            "client_wallclock_ms": agg_runs(mr_runs, "client_wallclock_ms"),
                            "yarn_wallclock_ms": agg_runs(mr_runs, "yarn_wallclock_ms"),
                            "shuffle_bytes": agg_runs(mr_runs, "shuffleBytes")}

    op = os.path.join(OUT_DIR, "perf_summary.json")
    with open(op, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("SAVED", op)

    csvp = os.path.join(OUT_DIR, "perf_summary.csv")
    with open(csvp, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["engine", "metric", "min", "median", "max", "mean", "n"])
        for eng, keys in (("spark", ["total_seconds", "shuffle_aggregate_seconds", "shuffle_write_bytes"]),
                          ("mapreduce", ["client_wallclock_ms", "yarn_wallclock_ms", "shuffleBytes"])):
            for k in keys:
                a = results[eng].get(k)
                if a:
                    w.writerow([eng, k, a["min"], a["median"], a["max"], a["mean"], a["n"]])
    print("SAVED", csvp)
    print("DONE")


if __name__ == "__main__":
    main()
