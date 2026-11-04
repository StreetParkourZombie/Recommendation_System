"""Nạp Parquet (ratings) lên HDFS trong container Hadoop.
Dung cho seminar "HDFS + Spark" va "MapReduce + HDFS".
Chay: python scripts/01_ingest_hdfs.py
"""
import os, sys, io, subprocess, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PARQ_FILE = r"D:\recsys_data\parquet\ratings\part-00000.parquet"
CONTAINER = "namenode"
HDFS_DIR  = "/recsys/ratings"
HDFS_FILE = HDFS_DIR + "/part-00000.parquet"

def sh(cmd, **kw):
    print("$", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.stdout.strip(): print(r.stdout.strip(), flush=True)
    if r.returncode != 0:
        print("STDERR:", r.stderr.strip()[:2000], flush=True)
    return r

# 1. tao thu muc
sh(["docker", "exec", CONTAINER, "hdfs", "dfs", "-mkdir", "-p", HDFS_DIR])

# 2. copy file vao container
t0 = time.time()
sh(["docker", "cp", PARQ_FILE, CONTAINER + ":/tmp/ratings.parquet"])
print("copied to container in %.0fs" % (time.time() - t0), flush=True)

# 3. put len HDFS
sh(["docker", "exec", CONTAINER, "hdfs", "dfs", "-put", "-f",
    "/tmp/ratings.parquet", HDFS_FILE])

# 4. xac nhan
r = sh(["docker", "exec", CONTAINER, "hdfs", "dfs", "-ls", "-h", HDFS_DIR])
r = sh(["docker", "exec", CONTAINER, "hdfs", "dfs", "-count", "-q", HDFS_DIR])
print("DONE", flush=True)
