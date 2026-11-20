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


_GENRE_CACHE: dict[int, frozenset] | None = None


def genre_map(path=None) -> dict[int, frozenset]:
    """Đọc `movies.csv` của MovieLens → {movieId: frozenset(genre)}.

    Cache trong tiến trình: nhiều split trong cùng notebook gọi lại nhiều lần,
    đọc file 3 MB mỗi lần là phí. `(no genres listed)` thành frozenset rỗng.
    Không phụ thuộc Spark — chỉ đọc CSV bằng stdlib, dùng được ở mọi notebook.
    """
    global _GENRE_CACHE
    if _GENRE_CACHE is not None:
        return _GENRE_CACHE
    if path is None:
        from pathlib import Path

        from ..utils import spark_utils

        path = Path(spark_utils.RAW_DIR) / "movies.csv"
    import csv
    from pathlib import Path

    target = Path(path)
    table: dict[int, frozenset] = {}
    if not target.is_file():
        _GENRE_CACHE = table
        return table
    with target.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                movie_id = int(row["movieId"])
            except (KeyError, TypeError, ValueError):
                continue
            raw = (row.get("genres") or "").strip()
            if not raw or raw == "(no genres listed)":
                table[movie_id] = frozenset()
            else:
                table[movie_id] = frozenset(raw.split("|"))
    _GENRE_CACHE = table
    return table


def diversity_metrics(
    recommendations: dict[int, list[int]],
    popularity: dict[int, int],
    genre_sets: dict[int, frozenset],
    reference_total: int | None = None,
    k: int = 10,
    max_users: int = 5000,
    seed: int = 42,
) -> dict:
    """Novelty + Diversity trung bình trên top-K, cùng 1 mẫu user cố định.

    - `novelty_at_k` = trung bình `-log2(pop(item)/reference_total)`.
    - `diversity_at_k` = trung bình Jaccard-distance bộ genre của các cặp item.

    Lấy mẫu `max_users` user (seeded) vì hàm chạy theo từng danh sách: 162.541
    user × 45 cặp = 7,3M phép Jaccard, chậm mà không thêm thông tin — sai số
    của mẫu 5.000 user ở mức 1e-3. `max_users=0` nghĩa là chạy hết.
    """
    from . import metrics as metrics_lib

    if reference_total is None:
        reference_total = int(sum(int(v) for v in popularity.values()))

    users = sorted(recommendations)
    if max_users and len(users) > max_users:
        rng = np.random.default_rng(seed)
        pick = rng.choice(len(users), size=max_users, replace=False)
        users = [users[i] for i in sorted(pick)]

    novelty_values = []
    diversity_values = []
    for user in users:
        ranked = recommendations[user]
        novelty_values.append(
            metrics_lib.novelty_at_k(ranked, popularity, reference_total, k)
        )
        diversity_values.append(
            metrics_lib.categorical_diversity_at_k(ranked, genre_sets, k)
        )
    return {
        "novelty_at_k": round(float(np.mean(novelty_values)), 4) if novelty_values else 0.0,
        "diversity_at_k": round(float(np.mean(diversity_values)), 4) if diversity_values else 0.0,
        "users_measured": len(users),
        "users_available": len(recommendations),
        "diversity_kind": "genre_jaccard",
    }


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

