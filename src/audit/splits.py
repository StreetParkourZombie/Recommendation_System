"""Sinh 3 chiến lược chia tập và ghi ra Parquet.

Quy tắc chia phải khớp tuyệt đối với scripts/04_audit_spark.py; notebook chỉ
quan sát, không tự nghĩ ra cách chia khác.

`leave_one_out` dùng tie-break `movieId asc` để đơn định. Tie-break này KHÔNG
phải thứ tự thời gian thật: 1.799.454 nhóm timestamp trùng trên 78.496 user
làm thứ tự chỉ theo timestamp không xác định (xem MetErrors/datasets.md).
"""
from __future__ import annotations

from pathlib import Path

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

STRATEGIES = ("random80_20", "temporal_global", "leave_one_out")

SPLIT_DESCRIPTIONS = {
    "random80_20": "F.rand(seed) > 0.8 — ngẫu nhiên 80/20, bỏ qua thời gian",
    "temporal_global": "timestamp >= P80(timestamp) — cắt theo mốc thời gian toàn cục",
    "leave_one_out": "1 tương tác mới nhất mỗi user vào test, tie-break movieId asc",
}


def _temporal_threshold(df: DataFrame, quantile: float = 0.8) -> int:
    """Mốc timestamp tại phân vị cho trước.

    Spark 4.x dùng thang 0.0-1.0 cho percentile_approx. Giá trị là XẤP XỈ
    (relativeError mặc định 0.01), không phải phân vị chính xác.
    """
    row = df.select(
        F.expr(f"percentile_approx(timestamp, {quantile})").alias("t")
    ).first()
    return int(row["t"])


def build_split(
    ratings: DataFrame,
    strategy: str,
    seed: int = 42,
    test_fraction: float = 0.2,
) -> tuple[DataFrame, dict]:
    """Trả (df có cột is_test, metadata mô tả cách chia)."""
    if strategy not in STRATEGIES:
        raise ValueError(f"strategy must be one of {STRATEGIES}, got {strategy!r}")

    meta: dict = {
        "strategy": strategy,
        "seed": seed,
        "test_fraction": test_fraction,
        "description": SPLIT_DESCRIPTIONS[strategy],
    }

    if strategy == "random80_20":
        threshold = _temporal_threshold(ratings, 1.0 - test_fraction)
        meta["threshold_ts"] = threshold
        meta["threshold_approx"] = "percentile_approx(1-test_fraction), relativeError=0.01"
        marked = ratings.withColumn(
            "is_test", F.rand(seed) > F.lit(1.0 - test_fraction)
        )

    elif strategy == "temporal_global":
        threshold = _temporal_threshold(ratings, 1.0 - test_fraction)
        meta["threshold_ts"] = threshold
        meta["threshold_approx"] = "percentile_approx(1-test_fraction), relativeError=0.01"
        marked = ratings.withColumn("is_test", F.col("timestamp") >= F.lit(threshold))

    else:  # leave_one_out
        window = Window.partitionBy("userId").orderBy(
            F.col("timestamp").desc(), F.col("movieId").asc()
        )
        marked = (
            ratings.withColumn("_rn", F.row_number().over(window))
            .withColumn("is_test", F.col("_rn") == 1)
            .drop("_rn")
        )
        meta["threshold_ts"] = None
        meta["tie_break"] = "timestamp desc, movieId asc (không phải thứ tự thời gian thật)"

    return marked.select("userId", "movieId", "rating", "timestamp", "is_test"), meta


def materialize_split(
    marked: DataFrame,
    strategy: str,
    splits_dir: str | Path,
    num_partitions: int = 8,
) -> dict:
    """Ghi train/ và test/ dạng Parquet dưới `splits_dir/<strategy>/`.

    Ghi đè nếu đã tồn tại: notebook 04 là nguồn duy nhất sinh split, và manifest
    của run giữ checksum để phát hiện thay đổi.
    """
    root = Path(splits_dir) / strategy
    train_dir = root / "train"
    test_dir = root / "test"

    train = marked.filter(~F.col("is_test")).drop("is_test")
    test = marked.filter(F.col("is_test")).drop("is_test")

    train = train.repartition(num_partitions)
    test = test.repartition(max(1, num_partitions // 2))

    train.write.mode("overwrite").parquet(str(train_dir))
    test.write.mode("overwrite").parquet(str(test_dir))

    return {
        "strategy": strategy,
        "train_path": str(train_dir),
        "test_path": str(test_dir),
        "num_partitions": num_partitions,
    }


def load_split(strategy: str, splits_dir: str | Path) -> tuple[DataFrame, DataFrame]:
    """Đọc lại train/test đã ghi ở notebook 04."""
    from pyspark.sql import SparkSession

    spark = SparkSession.getActiveSession()
    if spark is None:
        raise RuntimeError("No active SparkSession; gọi get_spark() trước.")

    root = Path(splits_dir) / strategy
    train = spark.read.parquet(str(root / "train"))
    test = spark.read.parquet(str(root / "test"))
    return train, test


def verify_materialized(
    spark,
    strategy: str,
    splits_dir: str | Path,
    expected: dict | None = None,
) -> dict:
    """Đếm lại train/test đã ghi và so với số kỳ vọng.

    `expected` là dict {'train_rows': int, 'test_rows': int}; nếu None thì chỉ đếm.
    Trả dict gồm counts và cờ `matches_expected`.
    """
    from .io import dir_size_bytes, sha256_dir

    root = Path(splits_dir) / strategy
    train, test = load_split(strategy, splits_dir)
    result = {
        "strategy": strategy,
        "train_rows": train.count(),
        "test_rows": test.count(),
        "train_bytes": dir_size_bytes(root / "train"),
        "test_bytes": dir_size_bytes(root / "test"),
        "train_sha256": sha256_dir(root / "train"),
        "test_sha256": sha256_dir(root / "test"),
        "train_schema": train.schema.simpleString(),
        "test_schema": test.schema.simpleString(),
    }

    if expected:
        result["matches_expected"] = (
            result["train_rows"] == expected.get("train_rows")
            and result["test_rows"] == expected.get("test_rows")
        )
    return result


def overlap_check(train: DataFrame, test: DataFrame) -> dict:
    """Kiểm tra train/test có rò rỉ dòng nào không.

    Với random và temporal, mỗi dòng thuộc đúng một phía vì điều kiện chia là
    hàm của chính dòng đó. Với leave_one_out, cùng lý do. Nếu overlap > 0 thì
    logic chia sai.
    """
    train_keys = train.select("userId", "movieId", "timestamp").distinct()
    test_keys = test.select("userId", "movieId", "timestamp").distinct()
    shared = train_keys.join(test_keys, ["userId", "movieId", "timestamp"], "inner")
    return {"overlapping_rows": shared.count()}

