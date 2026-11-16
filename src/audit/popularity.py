"""Baseline MostPopular + chỉ số thiên lệch phổ biến.

Popularity PHẢI tính trên train, không trên full data — dùng full data là rò rỉ
test vào baseline. Tie-break bằng `movieId asc` để top-10 đơn định giữa các lần chạy.
"""
from __future__ import annotations

import numpy as np
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from .metrics import coverage, gini, longtail_coverage, tail_threshold


def train_popularity(train: DataFrame) -> dict[int, int]:
    """Đếm số tương tác mỗi item trong train → {movieId: popularity}."""
    rows = train.groupBy("movieId").count().collect()
    return {int(row["movieId"]): int(row["count"]) for row in rows}


def mostpopular_topk(
    train: DataFrame, k: int = 10, popularity: dict[int, int] | None = None
) -> list[int]:
    """Top-K item phổ biến nhất trong train, tie-break movieId tăng dần."""
    pop = popularity
    if pop is None:
        pop = train_popularity(train)
    ordered = sorted(pop.items(), key=lambda pair: (-pair[1], pair[0]))
    return [movie_id for movie_id, _ in ordered[:k]]


def popularity_recommendations(topk: list[int], users: list[int]) -> dict[int, list[int]]:
    """Popularity đề xuất cùng một danh sách cho mọi user."""
    return {int(user): list(topk) for user in users}


def bias_metrics(
    recommended_items,
    popularity: dict[int, int],
    catalog_size: int | None = None,
    tail_quantile: float = 0.2,
) -> dict:
    """Chỉ số thiên lệch phổ biến của một tập item được đề xuất.

    `popularity_bias_ratio` = avg_pop_rec / avg_pop_all. > 1 nghĩa là item được
    đề xuất phổ biến hơn mức trung bình của catalog.
    """
    items = [int(i) for i in recommended_items]
    unique = sorted(set(items))
    if catalog_size is None:
        catalog_size = len(popularity)

    threshold = tail_threshold(popularity, tail_quantile)
    tail_items = {movie_id for movie_id, pop in popularity.items() if pop <= threshold}

    avg_pop_rec = (
        float(np.mean([popularity.get(movie_id, 0) for movie_id in unique]))
        if unique
        else 0.0
    )
    avg_pop_all = float(np.mean(list(popularity.values()))) if popularity else 0.0

    counts: dict[int, int] = {}
    for movie_id in items:
        counts[movie_id] = counts.get(movie_id, 0) + 1
    exposure = [counts.get(int(movie_id), 0) for movie_id in popularity]

    return {
        "catalog_coverage": round(coverage(unique, catalog_size), 6),
        "longtail_coverage": round(longtail_coverage(unique, tail_items), 6),
        "gini_exposure": round(gini(exposure), 4),
        "avg_pop_rec": round(avg_pop_rec, 2),
        "avg_pop_all": round(avg_pop_all, 2),
        "popularity_bias_ratio": (
            round(avg_pop_rec / avg_pop_all, 4) if avg_pop_all else 0.0
        ),
        "tail_threshold_pop": threshold,
        "tail_items": len(tail_items),
        "distinct_recommended": len(unique),
        "catalog_size": catalog_size,
    }

