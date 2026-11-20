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


# --- Độ đo bổ sung theo Bài 04 (Phần 3, RecSys) -----------------------------
# Bài giảng liệt kê NDCG@k và MRR là chuẩn của RecSys/SIGIR, rồi yêu cầu bổ sung
# Diversity, Novelty, Serendipity vì NDCG một mình thưởng cho model chỉ đẩy item
# phổ biến. Ba hàm dưới đây cài đúng ba độ đo đó, thuần NumPy như phần còn lại.


def novelty_at_k(
    ranked: Sequence[int],
    popularity: dict[int, int],
    reference_total: int,
    k: int = DEFAULT_K,
) -> float:
    """Novelty@K = trung bình `-log2(pop(item) / reference_total)` trên top-K.

    Càng cao = càng đề xuất item hiếm (ít người tương tác). `reference_total` là
    mẫu số tham chiếu — trong đề tài dùng tổng số tương tác positive của **train**
    (không dùng test, để không rò rỉ). Item chiếm trọn mẫu số → novelty 0.0; item
    1 tương tác → `log2(reference_total)`. Item không có trong `popularity` (chưa
    ai tương tác ở train) coi như popularity = 1 để không sinh `log2(0)`.
    """
    top = list(ranked)[:k]
    if not top or reference_total <= 0:
        return 0.0
    total = 0.0
    for item in top:
        count = int(popularity.get(item, 0))
        if count <= 0:
            count = 1
        total += -np.log2(count / reference_total)
    return float(total / len(top))


def intra_list_diversity_at_k(
    ranked: Sequence[int],
    item_vectors: dict[int, Sequence[float]],
    k: int = DEFAULT_K,
) -> float:
    """Diversity@K trong danh sách = `1 - trung bình cosine` của mọi cặp item top-K.

    Gần 1.0 = các item trong danh sách khác nhau; gần 0.0 = gần trùng nhau
    (danh sách một màu). Danh sách có < 2 item, hoặc thiếu vector, trả 0.0.
    Vector không cần chuẩn hoá — hàm tự chuẩn hoá; vector toàn 0 bị bỏ qua.
    """
    top = [item for item in list(ranked)[:k] if item in item_vectors]
    if len(top) < 2:
        return 0.0
    matrix = np.asarray([np.asarray(item_vectors[i], dtype=float) for i in top])
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    matrix = matrix / norms
    similarity = matrix @ matrix.T
    n = len(top)
    upper = np.triu_indices(n, k=1)
    mean_cosine = float(similarity[upper].mean())
    return float(1.0 - mean_cosine)


def categorical_diversity_at_k(
    ranked: Sequence[int],
    category_sets: dict[int, Iterable[str]],
    k: int = DEFAULT_K,
) -> float:
    """Diversity@K theo nhãn phân loại = trung bình khoảng cách Jaccard giữa mọi cặp.

    Dùng cho MovieLens: mỗi phim có một tập genre (`{'Action','Comedy'}`), khoảng
    cách Jaccard giữa hai phim = `1 - |giao| / |hợp|`. Danh sách càng "một màu"
    thì giá trị càng gần 0; càng đa dạng càng gần 1.

    Chọn Jaccard thay vì cosine trên vector ALS vì (a) vector ALS không được lưu
    lại sau mỗi run, còn genre có sẵn trong `movies.csv`; (b) genre là thứ người
    xem cảm nhận được, không phải trục ẩn của model.

    Item không có genre (hoặc `(no genres listed)`) bị bỏ khỏi phép tính; còn
    dưới 2 item thì trả 0.0 chứ không NaN.
    """
    sets = []
    for item in list(ranked)[:k]:
        raw = category_sets.get(int(item))
        if not raw:
            continue
        tag = {str(t) for t in raw}
        if tag:
            sets.append(tag)
    if len(sets) < 2:
        return 0.0
    distances = []
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            union = sets[i] | sets[j]
            inter = sets[i] & sets[j]
            distances.append(1.0 - (len(inter) / len(union) if union else 1.0))
    return float(np.mean(distances))


def serendipity_at_k(
    ranked: Sequence[int],
    relevant: Iterable[int],
    novelty_by_item: dict[int, float],
    k: int = DEFAULT_K,
) -> float:
    """Serendipity@K = novelty trung bình của item **vừa relevant vừa lọt top-K**.

    Định nghĩa dùng trong đề tài (hẹp, tính được, không cần model "primitive"):
    một gợi ý chỉ được tính là "bất ngờ mà vẫn đúng" khi nó nằm trong danh sách
    **và** là item người dùng thực sự tương tác ở test. Không có cặp nào → 0.0.
    Bản đầy đủ của bài giảng (độ bất ngờ so với một recommender nguyên thuỷ)
    không dùng được vì đề tài không có model "primitive" làm mốc.
    """
    rel = set(relevant)
    hits = [item for item in list(ranked)[:k] if item in rel and item in novelty_by_item]
    if not hits:
        return 0.0
    return float(np.mean([novelty_by_item[item] for item in hits]))


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


# Fixture tính tay cho 3 độ đo bổ sung của Bài 04. Kiểu khai báo giống FIXTURES:
# mỗi ca tự khai `expect_*`, assert so tuyệt đối với 1e-12.
SUPPLEMENTARY_FIXTURES = [
    {
        # -log2(100/100)=0, -log2(50/100)=1, -log2(25/100)=2 → trung bình 1.0
        "name": "novelty: 3 item giam dan do pho bien",
        "metric": "novelty",
        "ranked": [1, 2, 3],
        "popularity": {1: 100, 2: 50, 3: 25},
        "reference_total": 100,
        "k": 3,
        "expect_novelty": 1.0,
    },
    {
        # item 9 chưa ai tương tác ở train → coi popularity=1 → -log2(1/100)=6.643856
        # item 1 = popularity 100 = n_users → 0.0 ; trung bình 2 ca = 3.321928
        "name": "novelty: item khong co trong popularity khong sinh log2(0)",
        "metric": "novelty",
        "ranked": [1, 9],
        "popularity": {1: 100},
        "reference_total": 100,
        "k": 2,
        "expect_novelty": float(-np.log2(1 / 100) / 2),
    },
    {
        # hai vector trực giao → cosine 0 → diversity = 1.0
        "name": "diversity: hai vector truc giao",
        "metric": "diversity",
        "ranked": [1, 2],
        "item_vectors": {1: [1.0, 0.0], 2: [0.0, 1.0]},
        "k": 2,
        "expect_diversity": 1.0,
    },
    {
        # hai vector trùng hướng (một cái dài gấp 3) → cosine 1 → diversity = 0.0
        "name": "diversity: hai vector cung huong",
        "metric": "diversity",
        "ranked": [1, 2],
        "item_vectors": {1: [1.0, 2.0], 2: [3.0, 6.0]},
        "k": 2,
        "expect_diversity": 0.0,
    },
    {
        # ca bắt lỗi: danh sách 1 item không có cặp nào → phải trả 0.0, không NaN
        "name": "diversity: danh sach 1 item",
        "metric": "diversity",
        "ranked": [1],
        "item_vectors": {1: [1.0, 0.0]},
        "k": 10,
        "expect_diversity": 0.0,
    },
    {
        # genre hoan toan khac nhau -> Jaccard 0 -> diversity 1.0
        "name": "diversity genre: hai phim khac genre hoan toan",
        "metric": "categorical_diversity",
        "ranked": [1, 2],
        "category_sets": {1: {"Action"}, 2: {"Comedy"}},
        "k": 2,
        "expect_diversity": 1.0,
    },
    {
        # Action+Comedy vs Action -> giao 1, hop 2 -> Jaccard 0.5 -> diversity 0.5
        "name": "diversity genre: giao mot nua",
        "metric": "categorical_diversity",
        "ranked": [1, 2],
        "category_sets": {1: {"Action", "Comedy"}, 2: {"Action"}},
        "k": 2,
        "expect_diversity": 0.5,
    },
    {
        # ca bat loi: moi phim mot genre giong nhau het -> 0.0, khong NaN
        "name": "diversity genre: danh sach mot mau",
        "metric": "categorical_diversity",
        "ranked": [1, 2, 3],
        "category_sets": {1: {"Drama"}, 2: {"Drama"}, 3: {"Drama"}},
        "k": 3,
        "expect_diversity": 0.0,
    },
    {
        # chỉ item relevant (5, 6) được tính; item 7 lọt top nhưng không relevant → bỏ
        # mean(3.0, 1.0) = 2.0
        "name": "serendipity: chi tinh item relevant va bat ngo",
        "metric": "serendipity",
        "ranked": [5, 6, 7],
        "relevant": {5, 6},
        "novelty_by_item": {5: 3.0, 6: 1.0, 7: 5.0},
        "k": 3,
        "expect_serendipity": 2.0,
    },
    {
        # không item relevant nào lọt top-K → 0.0 (không phải NaN)
        "name": "serendipity: khong co item relevant trong top-K",
        "metric": "serendipity",
        "ranked": [7, 8],
        "relevant": {5},
        "novelty_by_item": {5: 3.0, 7: 5.0, 8: 1.0},
        "k": 2,
        "expect_serendipity": 0.0,
    },
]


def _check_supplementary(case: dict) -> float:
    """Chạy 1 ca của SUPPLEMENTARY_FIXTURES, trả giá trị đo được."""
    k = case.get("k", DEFAULT_K)
    metric = case["metric"]
    if metric == "novelty":
        got = novelty_at_k(case["ranked"], case["popularity"], case["reference_total"], k)
        expect = case["expect_novelty"]
    elif metric == "diversity":
        got = intra_list_diversity_at_k(case["ranked"], case["item_vectors"], k)
        expect = case["expect_diversity"]
    elif metric == "categorical_diversity":
        got = categorical_diversity_at_k(case["ranked"], case["category_sets"], k)
        expect = case["expect_diversity"]
    elif metric == "serendipity":
        got = serendipity_at_k(
            case["ranked"], case["relevant"], case["novelty_by_item"], k
        )
        expect = case["expect_serendipity"]
    else:  # pragma: no cover - phòng khi gõ sai tên metric trong fixture
        raise ValueError(f"Unknown fixture metric: {metric}")
    assert abs(got - expect) < 1e-12, (
        f"{metric} lệch ở ca '{case['name']}': got {got}, expect {expect}"
    )
    return got


def assert_against_fixture(k_default: int = DEFAULT_K) -> list[dict]:
    """So code với kết quả tính tay. Raise AssertionError nếu lệch.

    Gồm 2 nhóm: fixture NDCG/Hit gốc, và fixture 3 độ đo bổ sung của Bài 04
    (novelty / diversity / serendipity).
    """
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
    for case in SUPPLEMENTARY_FIXTURES:
        got = _check_supplementary(case)
        results.append(
            {
                "case": case["name"],
                "metric": case["metric"],
                "got": round(got, 6),
                "status": "PASS",
            }
        )
    return results
