"""Ranking metrics thuần Python/NumPy, không phụ thuộc Spark.

Notebook 07 kiểm tra module này bằng tính tay trước khi tin bất kỳ số NDCG
nào ở notebook 06/08. Mọi hàm nhận `relevant` là tập itemId liên quan.

Quy ước:
- NDCG@K macro trên user: mỗi user một NDCG, rồi lấy trung bình.
- IDCG@K = tổng K discount lớn nhất có thể, giới hạn bởi số item relevant.
- User không có item relevant trong test bị loại khỏi mẫu (không tính là 0).
  Đây là quyết định protocol, phải nêu rõ trong báo cáo.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np

DEFAULT_K = 10


def discounts(k: int = DEFAULT_K) -> np.ndarray:
    """Vector discount 1/log2(rank+1) cho rank 1..k."""
    if k <= 0:
        raise ValueError("k must be positive")
    return 1.0 / np.log2(np.arange(2, k + 2))


def dcg_at_k(ranked: Sequence[int], relevant: Iterable[int], k: int = DEFAULT_K) -> float:
    """DCG@K của một danh sách xếp hạng."""
    rel = set(relevant)
    if not rel:
        return 0.0
    disc = discounts(k)
    total = 0.0
    for position, item in enumerate(list(ranked)[:k]):
        if item in rel:
            total += disc[position]
    return float(total)


def idcg_at_k(n_relevant: int, k: int = DEFAULT_K) -> float:
    """IDCG@K: xếp hạng lý tưởng đặt toàn bộ item relevant lên đầu."""
    if n_relevant <= 0:
        return 0.0
    disc = discounts(k)
    return float(disc[: min(n_relevant, k)].sum())


def ndcg_at_k(ranked: Sequence[int], relevant: Iterable[int], k: int = DEFAULT_K) -> float:
    """NDCG@K của một user. Trả 0.0 nếu không có item relevant."""
    rel = set(relevant)
    ideal = idcg_at_k(len(rel), k)
    if ideal <= 0:
        return 0.0
    return dcg_at_k(ranked, rel, k) / ideal


def hit_at_k(ranked: Sequence[int], relevant: Iterable[int], k: int = DEFAULT_K) -> int:
    """1 nếu có ít nhất một item relevant trong top-K, ngược lại 0."""
    rel = set(relevant)
    return int(any(item in rel for item in list(ranked)[:k]))


def precision_at_k(ranked: Sequence[int], relevant: Iterable[int], k: int = DEFAULT_K) -> float:
    """Tỷ lệ item relevant trong top-K."""
    rel = set(relevant)
    top = list(ranked)[:k]
    if not top:
        return 0.0
    return sum(1 for item in top if item in rel) / k


def recall_at_k(ranked: Sequence[int], relevant: Iterable[int], k: int = DEFAULT_K) -> float:
    """Tỷ lệ item relevant được lấy ra trong top-K."""
    rel = set(relevant)
    if not rel:
        return 0.0
    top = list(ranked)[:k]
    return sum(1 for item in top if item in rel) / len(rel)


def mrr_at_k(ranked: Sequence[int], relevant: Iterable[int], k: int = DEFAULT_K) -> float:
    """MRR@K: 1/rank của item relevant đầu tiên trong top-K (0 nếu không có).

    Độ đo thứ bậc theo bài giảng PPNCKH Bài 04 (Phần 3, RecSys):
    MRR = (1/Q) * sum(1/rank_i) — macro trung bình trên user, cùng quy ước NDCG.
    """
    rel = set(relevant)
    if not rel:
        return 0.0
    for position, item in enumerate(list(ranked)[:k]):
        if item in rel:
            return 1.0 / (position + 1)
    return 0.0


def mean_metric(
    recommendations: dict[int, Sequence[int]],
    truth: dict[int, Iterable[int]],
    fn,
    k: int = DEFAULT_K,
) -> tuple[float, list[tuple[int, float]]]:
    """Trung bình macro của `fn` trên user có mặt ở cả hai dict và có truth.

    Trả (mean, danh sách per-user) — per-user phải được giữ cho kiểm định cặp.
    """
    per_user: list[tuple[int, float]] = []
    for user, relevant in truth.items():
        rel = set(relevant)
        if not rel:
            continue
        ranked = recommendations.get(user)
        if ranked is None:
            continue
        per_user.append((user, float(fn(ranked, rel, k))))
    if not per_user:
        return 0.0, []
    return float(np.mean([value for _, value in per_user])), per_user


def gini(values: Iterable[float]) -> float:
    """Hệ số Gini của vector exposure (0 = đồng đều, → 1 = dồn một chỗ)."""
    array = np.sort(np.asarray(list(values), dtype=float))
    n = array.size
    total = array.sum()
    if n == 0 or total <= 0:
        return 0.0
    cumulative = float(np.sum(np.arange(1, n + 1) * array))
    return float((2.0 * cumulative) / (n * total) - (n + 1) / n)


def coverage(recommended_items: Iterable[int], catalog_size: int) -> float:
    """Tỷ lệ item trong catalog được đề xuất ít nhất một lần."""
    if catalog_size <= 0:
        return 0.0
    return len({int(i) for i in recommended_items}) / catalog_size


def longtail_coverage(recommended_items: Iterable[int], tail_items: Iterable[int]) -> float:
    """Tỷ lệ item long-tail được đề xuất."""
    tail = {int(i) for i in tail_items}
    if not tail:
        return 0.0
    return len({int(i) for i in recommended_items} & tail) / len(tail)


def tail_threshold(popularity: dict[int, int], quantile: float = 0.2) -> int:
    """Ngưỡng popularity tại phân vị P20 của train — item <= ngưỡng là long-tail."""
    if not popularity:
        return 0
    values = sorted(popularity.values())
    return int(values[int(len(values) * quantile)])


FIXTURES = [
    {
        "name": "hit o vi tri 1",
        "ranked": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
        "relevant": {10},
        "k": 10,
        "expect_ndcg": 1.0,
        "expect_hit": 1,
    },
    {
        "name": "hit o vi tri 10",
        "ranked": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "relevant": {10},
        "k": 10,
        "expect_ndcg": float(1.0 / np.log2(11)),
        "expect_hit": 1,
    },
    {
        "name": "khong hit",
        "ranked": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "relevant": {99},
        "k": 10,
        "expect_ndcg": 0.0,
        "expect_hit": 0,
    },
    {
        "name": "hai relevant o vi tri 1 va 3",
        "ranked": [7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
        "relevant": {7, 9},
        "k": 10,
        "expect_ndcg": float(
            (1.0 / np.log2(2) + 1.0 / np.log2(4)) / (1.0 / np.log2(2) + 1.0 / np.log2(3))
        ),
        "expect_hit": 1,
    },
    {
        # ranked chỉ có 3 item nên không thể đạt IDCG@10: đây là ca bắt lỗi
        # implementation nào trả 1.0 khi danh sách ngắn hơn K.
        "name": "ranked ngan hon K, relevant nhieu hon K",
        "ranked": [1, 2, 3],
        "relevant": set(range(1, 21)),
        "k": 10,
        "expect_ndcg": float(
            (1.0 / np.log2(2) + 1.0 / np.log2(3) + 1.0 / np.log2(4))
            / sum(1.0 / np.log2(r) for r in range(2, 12))
        ),
        "expect_hit": 1,
    },
]


def assert_against_fixture(k_default: int = DEFAULT_K) -> list[dict]:
    """So code với kết quả tính tay. Raise AssertionError nếu lệch."""
    results = []
    for case in FIXTURES:
        k = case.get("k", k_default)
        got_ndcg = ndcg_at_k(case["ranked"], case["relevant"], k)
        got_hit = hit_at_k(case["ranked"], case["relevant"], k)
        assert abs(got_ndcg - case["expect_ndcg"]) < 1e-12, (
            f"NDCG lệch ở ca '{case['name']}': got {got_ndcg}, expect {case['expect_ndcg']}"
        )
        assert got_hit == case["expect_hit"], (
            f"Hit lệch ở ca '{case['name']}': got {got_hit}, expect {case['expect_hit']}"
        )
        results.append(
            {
                "case": case["name"],
                "expected_ndcg": round(case["expect_ndcg"], 6),
                "got_ndcg": round(got_ndcg, 6),
                "expected_hit": case["expect_hit"],
                "got_hit": got_hit,
                "status": "PASS",
            }
        )
    return results
