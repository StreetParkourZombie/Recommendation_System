"""Audit tầng dữ liệu: rò rỉ thời gian, dịch chuyển item, user lạnh.

Chỉ số ở đây KHÔNG phụ thuộc mô hình, nên không thể bị quy cho "mô hình yếu".
Đây là phần định lượng mạnh nhất của đề tài.

Hai định nghĩa temporal_violation phải luôn báo cáo cùng nhau:
- global: so với max(train.timestamp) của toàn bộ train
- user:   so với max(train(u).timestamp) của chính user đó
Định nghĩa global cho số vô nghĩa với leave_one_out (99,9988%) vì test của
user A có thể nằm trước tương tác mới nhất của user B. Định nghĩa user mới là
định nghĩa đúng về rò rỉ nhân quả.
"""
from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def data_level_audit(
    train: DataFrame,
    test: DataFrame,
    relevance_threshold: float = 4.0,
    min_train: int = 5,
    split_name: str | None = None,
) -> dict:
    """Tính bộ chỉ số tầng 1 cho một cặp train/test."""
    train = train.persist()
    test = test.persist()

    try:
        train_rows = train.count()
        test_rows = test.count()

        bounds = train.agg(F.max("timestamp").alias("mx")).first()
        train_max_ts = int(bounds["mx"]) if bounds["mx"] is not None else 0
        bounds = test.agg(F.min("timestamp").alias("mn")).first()
        test_min_ts = int(bounds["mn"]) if bounds["mn"] is not None else 0

        # (a) rò rỉ toàn cục
        viol_global = test.filter(F.col("timestamp") < F.lit(train_max_ts)).count()

        # (b) rò rỉ tương đối theo user
        user_max_train = train.groupBy("userId").agg(F.max("timestamp").alias("umax"))
        viol_user = (
            test.join(F.broadcast(user_max_train), "userId")
            .filter(F.col("timestamp") < F.col("umax"))
            .count()
        )

        # user lạnh: có trong test, không có trong train
        train_users = train.select("userId").distinct()
        coldstart_users = test.join(F.broadcast(train_users), "userId", "left_anti").count()

        # item chưa thấy: có trong test, không có trong train
        train_items = train.select("movieId").distinct()
        unseen_rows = test.join(F.broadcast(train_items), "movieId", "left_anti").count()

        # tập user đủ điều kiện đánh giá
        eligible = (
            train.groupBy("userId")
            .count()
            .filter(F.col("count") >= F.lit(min_train))
            .select("userId")
        )
        eligible = eligible.persist()
        eval_users = eligible.count()

        test_eval = test.join(F.broadcast(eligible), "userId").persist()
        eval_test_rows = test_eval.count()

        rel_eval = test_eval.filter(F.col("rating") >= F.lit(relevance_threshold))
        test_relevant_rows = test.filter(
            F.col("rating") >= F.lit(relevance_threshold)
        ).count()
        test_relevant_eval_rows = rel_eval.count()
        eval_relevant_users = rel_eval.select("userId").distinct().count()

        pct = lambda part, total: round(100.0 * part / total, 4) if total else 0.0  # noqa: E731

        result = {
            "split": split_name,
            "train_rows": train_rows,
            "test_rows": test_rows,
            "train_max_ts": train_max_ts,
            "test_min_ts": test_min_ts,
            "temporal_violation_global": viol_global,
            "temporal_violation_global_pct": pct(viol_global, test_rows),
            "temporal_violation_user": viol_user,
            "temporal_violation_user_pct": pct(viol_user, test_rows),
            "unseen_item_rows": unseen_rows,
            "unseen_item_pct": pct(unseen_rows, test_rows),
            "coldstart_user_rows": coldstart_users,
            "coldstart_user_pct": pct(coldstart_users, test_rows),
            "eval_users": eval_users,
            "eval_test_rows": eval_test_rows,
            "test_relevant_rows": test_relevant_rows,
            "test_relevant_eval_rows": test_relevant_eval_rows,
            "eval_relevant_users": eval_relevant_users,
            "relevance_threshold": relevance_threshold,
            "min_train_threshold": min_train,
        }

        test_eval.unpersist()
        eligible.unpersist()
        return result

    finally:
        train.unpersist()
        test.unpersist()


def eligible_users(train: DataFrame, min_train: int = 5) -> DataFrame:
    """Tập user có ít nhất `min_train` tương tác trong train."""
    return (
        train.groupBy("userId")
        .count()
        .filter(F.col("count") >= F.lit(min_train))
        .select("userId")
    )


def relevance_profile(
    test: DataFrame, threshold: float = 4.0, levels: tuple[float, ...] = (3.5, 4.0)
) -> dict:
    """Đếm số dòng vượt từng ngưỡng relevance — dùng cho phân tích độ nhạy.

    Không chọn ngưỡng ở đây; protocol đã chốt 4.0. Hàm này chỉ để so sánh.
    """
    expressions = [F.count("*").alias("rows")]
    for level in levels:
        expressions.append(
            F.sum(F.when(F.col("rating") >= F.lit(level), 1).otherwise(0)).alias(
                f"ge_{str(level).replace('.', '_')}"
            )
        )
    row = test.agg(*expressions).first().asDict()
    total = row["rows"] or 0
    out = {"rows": total}
    for key, value in row.items():
        if key == "rows":
            continue
        count = value or 0
        out[key] = count
        out[f"{key}_fraction"] = round(count / total, 4) if total else 0.0
    out["decision"] = "descriptive_only; protocol chốt relevance = 4.0"
    return out
