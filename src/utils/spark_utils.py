"""Đường dẫn dùng chung và khởi tạo Spark session cho pipeline RecSys.

Mọi notebook 04+ phải dùng module này, không tự dựng SparkSession riêng, để
cấu hình (master, driver memory, timezone, local dir) không lệch giữa các notebook.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------- paths

DATA_ROOT = Path(r"D:\recsys_data")

RAW_DIR = DATA_ROOT / "raw" / "ml-25m"
RAW_RATINGS_CSV = RAW_DIR / "ratings.csv"
RAW_README = RAW_DIR / "README.txt"

PARQUET_DIR = DATA_ROOT / "parquet" / "ratings"
PARQUET_RATINGS = PARQUET_DIR / "part-00000.parquet"

SPLITS_DIR = DATA_ROOT / "splits"
SPARK_TMP = DATA_ROOT / "spark_tmp"
HADOOP_HOME = DATA_ROOT / "tools" / "hadoop"

# SHA-256 xác minh thật, lấy từ runs/<run_id>/dataset_manifest.json
RATINGS_SHA256 = "9c85525758597dca76e8d98cebb9c13e018c2317b09a0878b6d383179526e385"
RATINGS_ROWS = 25_000_095
RATINGS_BYTES = 678_260_987

# Hợp đồng protocol dùng chung cho notebook 04-09.
PROTOCOL_ID = "project_protocol_v1"
DEFAULT_SEED = 42
TOP_K = 10
RELEVANCE_THRESHOLD = 4.0
MIN_TRAIN = 5
SUBSAMPLE_USERS = 30_000


def ensure_hadoop_home() -> bool:
    """Đặt HADOOP_HOME để Spark ghi/đọc Parquet được trên Windows.

    Cần đủ `bin/winutils.exe` VÀ `bin/hadoop.dll`. Chỉ có winutils.exe thì
    `df.write.parquet` vẫn fail với UnsatisfiedLinkError NativeIO$Windows.access0.

    Trả True nếu đã cấu hình được, False nếu thiếu binary.
    """
    winutils = HADOOP_HOME / "bin" / "winutils.exe"
    hadoop_dll = HADOOP_HOME / "bin" / "hadoop.dll"
    if not (winutils.is_file() and hadoop_dll.is_file()):
        return False
    os.environ["HADOOP_HOME"] = str(HADOOP_HOME)
    os.environ["hadoop.home.dir"] = str(HADOOP_HOME)
    bin_dir = str(HADOOP_HOME / "bin")
    current = os.environ.get("PATH", "")
    if bin_dir not in current.split(os.pathsep):
        os.environ["PATH"] = bin_dir + os.pathsep + current
    return True


def get_spark(
    app_name: str = "RecSysAudit",
    master: str = "local[4]",
    driver_memory: str = "6g",
    shuffle_partitions: int = 8,
    reuse: bool = True,
):
    """Tạo SparkSession với cấu hình cố định của project.

    Không dùng cấu hình khác giữa các notebook, trừ driver_memory khi chạy smoke.
    """
    from pyspark.sql import SparkSession

    ensure_hadoop_home()
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

    SPLITS_DIR.mkdir(parents=True, exist_ok=True)
    SPARK_TMP.mkdir(parents=True, exist_ok=True)

    if reuse:
        active = SparkSession.getActiveSession()
        if active is not None:
            configured = active.conf.get("spark.master", "")
            if configured and configured != master:
                active.stop()
                active = None
            if active is not None:
                return active

    spark = (
        SparkSession.builder.appName(app_name)
        .master(master)
        .config("spark.driver.memory", driver_memory)
        .config("spark.sql.shuffle.partitions", str(shuffle_partitions))
        .config("spark.local.dir", str(SPARK_TMP))
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.ui.showConsoleProgress", "false")
        .config("spark.sql.parquet.compression.codec", "snappy")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    return spark


def read_ratings(spark, source: str = "parquet"):
    """Đọc ratings từ Parquet cache (mặc định) hoặc CSV gốc.

    `source="csv"` dùng schema tường minh; chậm hơn parquet nhưng không phụ thuộc cache.
    """
    from pyspark.sql.types import (
        FloatType,
        IntegerType,
        LongType,
        StructField,
        StructType,
    )

    if source == "parquet":
        if not PARQUET_RATINGS.is_file():
            raise FileNotFoundError(
                f"Parquet cache missing: {PARQUET_RATINGS}. Chạy ingest trước, hoặc dùng source='csv'."
            )
        return spark.read.parquet(str(PARQUET_RATINGS)).select(
            "userId", "movieId", "rating", "timestamp"
        )

    if source == "csv":
        schema = StructType(
            [
                StructField("userId", IntegerType(), False),
                StructField("movieId", IntegerType(), False),
                StructField("rating", FloatType(), False),
                StructField("timestamp", LongType(), False),
            ]
        )
        return spark.read.option("header", True).schema(schema).csv(str(RAW_RATINGS_CSV))

    raise ValueError(f"source must be 'parquet' or 'csv', got {source!r}")


def stop_spark(spark) -> None:
    """Dừng session nếu còn sống."""
    try:
        if spark is not None:
            spark.stop()
    except Exception:  # session có thể đã chết do lỗi JVM
        pass

