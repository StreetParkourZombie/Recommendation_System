"""ALS implicit + lấy top-K bằng NumPy.

Không dùng `recommendForAllUsers`: 162.541 × 59.047 là cartesian ~9,6e9 điểm,
OOM trên máy local. Nhân ma trận theo chunk 2.000 user rồi argpartition cho ra
đúng top-K của cùng phép toán, chỉ khác cách lấy.

Implicit ALS chỉ coi tương tác TÍCH CỰC (rating >= threshold) là tín hiệu.
Dùng explicit ALS sẽ xếp hạng theo sai số dự đoán rating, đẩy phim bị chấm 1.0
xuống cuối -> NDCG ~ 0. Đây là lỗi phương pháp đã phát hiện ở PoC5.
"""
from __future__ import annotations

import time
from collections.abc import Iterable

import numpy as np
from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def fit_als_implicit(
    train_positive: DataFrame,
    rank: int = 16,
    max_iter: int = 8,
    reg: float = 0.05,
    alpha: float = 10.0,
    seed: int = 42,
):
    """Fit ALS implicit trên các tương tác positive.

    Trả (U, ui, V, vi, fit_seconds) với U/V là float32, ui/vi là id đã sắp tăng.
    """
    from pyspark.ml.recommendation import ALS

    started = time.perf_counter()
    als = ALS(
        userCol="userId",
        itemCol="movieId",
        ratingCol="rating",
        rank=rank,
        maxIter=max_iter,
        regParam=reg,
        implicitPrefs=True,
        alpha=alpha,
        coldStartStrategy="drop",
        seed=seed,
    )
    model = als.fit(train_positive)
    fit_seconds = time.perf_counter() - started

    user_rows = model.userFactors.select("id", "features").collect()
    item_rows = model.itemFactors.select("id", "features").collect()

    ui = np.array([row["id"] for row in user_rows], dtype=np.int64)
    U = np.array([row["features"] for row in user_rows], dtype=np.float32)
    vi = np.array([row["id"] for row in item_rows], dtype=np.int64)
    V = np.array([row["features"] for row in item_rows], dtype=np.float32)

    user_order = np.argsort(ui)
    item_order = np.argsort(vi)
    return U[user_order], ui[user_order], V[item_order], vi[item_order], fit_seconds


def topk_numpy(
    U: np.ndarray,
    ui: np.ndarray,
    V: np.ndarray,
    vi: np.ndarray,
    seen_by_user: dict[int, Iterable[int]] | None = None,
    k: int = 10,
    chunk: int = 2000,
    only_users: Iterable[int] | None = None,
    progress=None,
) -> dict[int, np.ndarray]:
    """Top-K item cho từng user, loại item đã thấy trong train.

    `only_users` giới hạn tập user cần tính (ví dụ chỉ user có relevant trong
    test) — không đổi kết quả của user được tính, chỉ bỏ việc vô ích.
    `progress(done, total)` gọi sau mỗi chunk để notebook in tiến độ.
    """
    seen_by_user = seen_by_user or {}
    targets = set(int(u) for u in only_users) if only_users is not None else None
    item_position = {int(movie_id): position for position, movie_id in enumerate(vi)}

    out: dict[int, np.ndarray] = {}
    total = len(ui)
    for start in range(0, total, chunk):
        stop = min(start + chunk, total)
        scores = U[start:stop] @ V.T
        for offset in range(start, stop):
            user = int(ui[offset])
            if targets is not None and user not in targets:
                continue
            row_scores = scores[offset - start]
            seen = seen_by_user.get(user)
            if seen:
                blocked = [item_position[i] for i in seen if i in item_position]
                if blocked:
                    row_scores[blocked] = -np.inf
            candidate = np.argpartition(-row_scores, k)[:k]
            candidate = candidate[np.argsort(-row_scores[candidate])]
            out[user] = vi[candidate]
        if progress is not None:
            progress(stop, total)
    return out


def collect_truth(
    test: DataFrame, eligible: DataFrame, threshold: float = 4.0
) -> dict[int, set[int]]:
    """Tập item relevant trong test cho từng user đủ điều kiện."""
    rows = (
        test.join(F.broadcast(eligible), "userId")
        .filter(F.col("rating") >= F.lit(threshold))
        .groupBy("userId")
        .agg(F.collect_list("movieId").alias("relevant"))
        .collect()
    )
    return {int(row["userId"]): {int(i) for i in row["relevant"]} for row in rows}


def collect_seen(train: DataFrame) -> dict[int, set[int]]:
    """Tập item đã thấy trong train cho từng user."""
    rows = (
        train.groupBy("userId")
        .agg(F.collect_list("movieId").alias("seen"))
        .collect()
    )
    return {int(row["userId"]): {int(i) for i in row["seen"]} for row in rows}


def subsample_users(train: DataFrame, n_users: int = 30_000) -> DataFrame:
    """Chọn n_user đầu theo userId tăng dần — đơn định, không phụ thuộc partition."""
    return train.select("userId").distinct().orderBy("userId").limit(n_users).select("userId")


def check_seen_exclusion(
    recommendations: dict[int, np.ndarray], seen_by_user: dict[int, set[int]]
) -> dict:
    """Kiểm tra top-K không chứa item user đã tương tác trong train."""
    violations = 0
    checked = 0
    examples = []
    for user, items in recommendations.items():
        seen = seen_by_user.get(user)
        if not seen:
            continue
        checked += 1
        leaked = [int(i) for i in items if int(i) in seen]
        if leaked:
            violations += 1
            if len(examples) < 5:
                examples.append({"userId": user, "leaked_items": leaked})
    return {
        "users_checked": checked,
        "users_with_leak": violations,
        "examples": examples,
        "status": "PASS" if violations == 0 else "FAIL",
    }

