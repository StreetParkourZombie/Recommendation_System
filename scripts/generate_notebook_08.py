"""Generate Notebook 08: implicit ALS with NumPy top-K."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "jupyter" / "08_als_implicit.ipynb"
OUT.parent.mkdir(parents=True, exist_ok=True)


def md(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source.strip("\n").splitlines(keepends=True)}


def code(source):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source.strip("\n").splitlines(keepends=True)}


cells = [
    md("""# 08 — ALS implicit trên 3 chiến lược chia tập

**Mục tiêu:** fit ALS implicit trên train của từng split, lấy top-K bằng NumPy, đo NDCG/Hit/bias — cùng protocol với notebook 06 để so sánh được.

**Input:** split của notebook 04; `data_level_audit.json` của notebook 05; metric đã kiểm chứng ở notebook 07.

**Output:** `runs/<run_id>/outputs/als_{split}.json` + `peruser_ndcg_{split}.npz`.

**Gate L6c:** top-K không chứa item đã thấy trong train; NDCG khớp kết quả đo thật; per-user NDCG được lưu cho kiểm định cặp."""),
    md("""## Khái niệm — vì sao ALS implicit, không phải explicit

### Lỗi phương pháp đã phát hiện (PoC5)

ALS **explicit** tối ưu sai số dự đoán **rating**. Nếu user chấm một phim 1,0 điểm, explicit ALS học rằng "user này sẽ chấm phim đó 1,0" — và đẩy phim đó xuống cuối danh sách gợi ý. Nhưng với bài toán top-N recommendation, **chấm 1,0 vẫn là một tương tác**: user đã xem phim đó và có ý kiến. Đẩy nó xuống cuối là hiểu sai bài toán.

Hệ quả đo được: với explicit ALS, NDCG ≈ 0 vì mô hình học đúng theo mục tiêu sai.

### Cách đúng: implicit feedback

Chỉ coi tương tác **tích cực** (`rating >= 4.0`) là tín hiệu, bỏ hẳn tương tác tiêu cực khỏi tập fit. Dùng `implicitPrefs=True` với:

$$c_{ui} = 1 + \\alpha \\cdot r_{ui}$$

trong đó `alpha = 10.0` là độ tin cậy: một tương tác positive đáng tin gấp 11 lần "không có tương tác". Càng lớn `alpha`, mô hình càng bám sát dữ liệu positive quan sát được.

Đây là lý do relevance threshold và fit threshold **phải cùng một giá trị** (4.0). Nếu fit trên `>= 3.5` mà đo trên `>= 4.0`, mô hình đang tối ưu cho một bài toán khác bài toán đang đo.

### Vì sao lấy top-K bằng NumPy, không dùng `recommendForAllUsers`

`recommendForAllUsers` tính toàn bộ ma trận điểm: `162.541 user × 59.047 item ≈ 9,6 × 10⁹` giá trị. Với float32 là ~38 GB — OOM ngay trên máy local 16 GB.

Cách làm thay thế: lấy ma trận hệ số `U` (user × 16) và `V` (item × 16), nhân theo từng chunk 2.000 user (`U[chunk] @ V.T` → 2.000 × 59.047 ≈ 118M giá trị ≈ 470 MB), rồi `argpartition` lấy top-10. Cùng phép toán, cùng kết quả, bộ nhớ thấp hơn 80 lần.

Trước khi lấy top-K phải gán `-inf` cho item user **đã thấy trong train** — nếu không, mô hình sẽ gợi ý lại phim user vừa xem, làm NDCG tăng giả tạo.

### Vì sao trước đó subsample 30.000 user — và nay đã chạy FULL

Lần đầu (run 2026-11-15) notebook chỉ fit 30.000 user đầu theo `userId` tăng dần — **đơn định**, không phụ thuộc partition — để có kết quả trong ~2 phút/split; quyết định có ghi trong manifest, không cắt bớt ngầm. Lần chạy FULL (run 2026-11-17, `20261117_185700_08_als_implicit_7be22080`): ALS fit toàn bộ 162.541 user trên ~20–25M dòng/split, fit ~35–38s mỗi split — nhanh hơn dự báo. NDCG chênh 1% so với subsample (0,2556 → 0,2581 random80_20): subsample trước đủ đại diện. Số chính thức của đề tài là số FULL.»"""),
    md("""## 1. Nạp split, audit và Spark session"""),
    code("""from pathlib import Path
import json
import sys
import time

import numpy as np

project_root = Path.cwd().resolve()
while project_root != project_root.parent and not (project_root / 'src').is_dir():
    project_root = project_root.parent
sys.path.insert(0, str(project_root))

from IPython import get_ipython
from src.recsys.notebook_logging import NotebookRun
from src.utils import spark_utils
from src.audit import splits as split_lib
from src.audit import leakage, popularity as pop_lib, als_rec, metrics
from pyspark.sql import functions as F

SPLITS_TO_RUN = list(split_lib.STRATEGIES)  # doi thanh ['leave_one_out'] de chay nhanh mot split

run = NotebookRun(
    project_root,
    '08_als_implicit',
    metadata={
        'protocol_id': spark_utils.PROTOCOL_ID,
        'model': 'ALS_implicit',
        'rank': 16, 'max_iter': 8, 'reg': 0.05, 'alpha': 10.0,
        'seed': spark_utils.DEFAULT_SEED,
        'k': spark_utils.TOP_K,
        'relevance_threshold': spark_utils.RELEVANCE_THRESHOLD,
        'subsample_users': spark_utils.SUBSAMPLE_USERS,
        'fit_scope': 'FULL 162,541 users (run 2026-11-17) — subsample 30,000 chỉ dùng ở run 2026-11-15',
        'splits': SPLITS_TO_RUN,
    },
)
run.attach_ipython(get_ipython())
print('Run ID:', run.run_id)
print('Splits to run:', SPLITS_TO_RUN)

runs_dir = project_root / 'runs'
audit_candidates = sorted(runs_dir.glob('*/outputs/data_level_audit.json'), key=lambda p: p.stat().st_mtime, reverse=True)
assert audit_candidates, 'Run notebook 05 first.'
audit_path = audit_candidates[0]
audits = json.loads(audit_path.read_text(encoding='utf-8'))['audits']

fixture_candidates = sorted(runs_dir.glob('*/outputs/metric_fixtures.json'), key=lambda p: p.stat().st_mtime, reverse=True)
assert fixture_candidates, 'Run notebook 07 first — metrics must be verified before trusting NDCG.'
print('Verified metric fixtures:', fixture_candidates[0])
print('Audit source:', audit_path)

run.checkpoint(
    'prerequisites_ok',
    'PASS',
    checks={'audit': str(audit_path), 'metric_fixtures': str(fixture_candidates[0]), 'splits': SPLITS_TO_RUN},
)"""),
    code("""spark = spark_utils.get_spark('RecSys08ALSImplicit')
print('Spark:', spark.version, '| master:', spark.sparkContext.master)
run.checkpoint('spark_ready', 'PASS', checks={'spark_version': spark.version, 'master': spark.sparkContext.master})"""),
    md("""## 2. Fit ALS và lấy top-K cho từng split

Mỗi split chạy độc lập: lọc positive trên train → fit → nhân ma trận theo chunk → loại item đã thấy → top-10. `fit_seconds` được ghi lại vì nó là một chỉ số của đề tài (chi phí vận hành)."""),
    code("""als_by_split = {}
peruser_by_split = {}
seen_checks = {}

for strategy in SPLITS_TO_RUN:
    started = time.perf_counter()
    print(f'=== {strategy} ===')

    train_df, test_df = split_lib.load_split(strategy, spark_utils.SPLITS_DIR)

    # FULL: dùng thẳng split (run 2026-11-17); subsample 30k đã comment — chỉ bật khi cần chạy nhanh
    # sub_users = als_rec.subsample_users(train_df, spark_utils.SUBSAMPLE_USERS)
    # train_sub = train_df.join(F.broadcast(sub_users), 'userId').persist()
    # test_sub  = test_df.join(F.broadcast(sub_users), 'userId').persist()

    train_sub = train_df.persist()
    test_sub  = test_df.persist()

    # implicit: chi tuong tac tich cuc
    train_positive = train_sub.filter(F.col('rating') >= F.lit(spark_utils.RELEVANCE_THRESHOLD)).persist()
    n_train, n_test, n_pos = train_sub.count(), test_sub.count(), train_positive.count()
    print(f'  FULL train={n_train:,} test={n_test:,} positive={n_pos:,}')

    U, ui, V, vi, fit_seconds = als_rec.fit_als_implicit(
        train_positive,
        rank=16, max_iter=8, reg=0.05, alpha=10.0, seed=spark_utils.DEFAULT_SEED,
    )
    print(f'  fit {fit_seconds:.1f}s  U{U.shape} V{V.shape}')

    eligible_sub = leakage.eligible_users(train_sub, spark_utils.MIN_TRAIN)
    truth = als_rec.collect_truth(test_sub, eligible_sub, spark_utils.RELEVANCE_THRESHOLD)
    seen = als_rec.collect_seen(train_sub)
    print(f'  truth users={len(truth):,}  seen users={len(seen):,}')

    recommendations = als_rec.topk_numpy(
        U, ui, V, vi,
        seen_by_user=seen,
        k=spark_utils.TOP_K,
        chunk=2000,
        only_users=list(truth.keys()),
        progress=lambda done, total: print(f'    top-K {done}/{total}', end='\\r'),
    )
    print(f'\\n  recommended users={len(recommendations):,}')

    seen_report = als_rec.check_seen_exclusion(recommendations, seen)
    seen_checks[strategy] = seen_report
    print(f"  seen exclusion: {seen_report['status']} (checked {seen_report['users_checked']:,}, leaks {seen_report['users_with_leak']})")

    ndcg_mean, ndcg_per_user = metrics.mean_metric(recommendations, truth, metrics.ndcg_at_k, spark_utils.TOP_K)
    hit_mean, _ = metrics.mean_metric(recommendations, truth, metrics.hit_at_k, spark_utils.TOP_K)
    recall_mean, _ = metrics.mean_metric(recommendations, truth, metrics.recall_at_k, spark_utils.TOP_K)
    mrr_mean, _ = metrics.mean_metric(recommendations, truth, metrics.mrr_at_k, spark_utils.TOP_K)

    catalog = pop_lib.train_popularity(train_sub)
    flat_recs = [int(i) for items in recommendations.values() for i in items]
    bias = pop_lib.bias_metrics(flat_recs, catalog)

    total_seconds = time.perf_counter() - started
    als_by_split[strategy] = {
        'model': 'ALS_implicit',
        'strategy': strategy,
        'ndcg10': round(ndcg_mean, 4),
        'hit_rate10': round(hit_mean, 4),
        'recall10': round(recall_mean, 4),
        'mrr10': round(mrr_mean, 4),
        'eval_users': len(ndcg_per_user),
        'train_rows': n_train,
        'test_rows': n_test,
        'positive_train_rows': n_pos,
        'rank': 16, 'max_iter': 8, 'reg': 0.05, 'alpha': 10.0,
        'seed': spark_utils.DEFAULT_SEED,
        'relevance_threshold': spark_utils.RELEVANCE_THRESHOLD,
        'fit_seconds': round(fit_seconds, 1),
        'total_seconds': round(total_seconds, 1),
        'bias': bias,
        'seen_exclusion': seen_report['status'],
    }
    peruser_by_split[strategy] = ndcg_per_user

    print(f"  ndcg@10={ndcg_mean:.4f}  hit@10={hit_mean:.4f}  recall@10={recall_mean:.4f}  mrr@10={mrr_mean:.4f}")
    print(f'  total {total_seconds:.1f}s')
    run.log('ALS_RESULT', strategy=strategy, result=als_by_split[strategy])

    train_sub.unpersist(); test_sub.unpersist(); train_positive.unpersist()

run.checkpoint(
    'als_complete',
    'PASS' if all(v['status'] == 'PASS' for v in seen_checks.values()) else 'FAIL',
    checks={
        'strategies': list(als_by_split),
        'seen_exclusion': {k: v['status'] for k, v in seen_checks.items()},
    },
)"""),
    md("""## 3. Đọc kết quả ALS

Ba điều cần đọc từ bảng dưới, không chỉ NDCG:

1. **NDCG giảm dần** random → temporal → LOO. Đó là cái giá của việc loại bỏ rò rỉ: mô hình thật sự khó hơn khi phải dự đoán tương lai.
2. **Bias ratio vẫn cao** (~10–13) dù đã cá nhân hóa. Nghĩa là ALS vẫn nghiêng về phim phổ biến — nó không "chữa" được thiên lệch, chỉ giảm nhẹ so với MostPopular.
3. **`catalog_coverage` tăng vọt** so với MostPopular (0,06 vs 0,0002). Đây là dấu hiệu mô hình thực sự cá nhân hóa, không chỉ chọn 10 phim giống nhau cho mọi user."""),
    code("""expected_ndcg = {'random80_20': 0.2556, 'temporal_global': 0.1311, 'leave_one_out': 0.0467}
mismatches = []
for strategy in SPLITS_TO_RUN:
    got = als_by_split[strategy]['ndcg10']
    want = expected_ndcg[strategy]
    ok = abs(got - want) <= 0.01
    print(f"{'OK  ' if ok else 'DIFF'} {strategy:<18}ndcg@10 got={got:<8}want={want}")
    if not ok:
        mismatches.append((strategy, want, got))

print()
if mismatches:
    print('MISMATCH:', mismatches)
    print('Kiem tra: fit FULL dataset, tren positive only, chunk 2000, seen exclusion.')
else:
    print('NDCG khop ket qua do that (dung sai 0.01).')

header = f"{'split':<18}{'ndcg@10':>10}{'hit@10':>9}{'cov':>9}{'gini':>8}{'bias':>8}{'fit_s':>8}{'users':>10}"
print()
print(header)
print('-' * len(header))
for strategy in SPLITS_TO_RUN:
    r = als_by_split[strategy]
    b = r['bias']
    print(f"{strategy:<18}{r['ndcg10']:>10.4f}{r['hit_rate10']:>9.4f}{b['catalog_coverage']:>9.4f}"
          f"{b['gini_exposure']:>8.4f}{b['popularity_bias_ratio']:>8.2f}{r['fit_seconds']:>8.1f}{r['eval_users']:>10,}")

run.log('REPRODUCTION_CHECK', mismatches=len(mismatches), detail=mismatches)
run.checkpoint(
    'reproduction_check',
    'PASS' if not mismatches else 'FAIL',
    checks={'mismatches': len(mismatches), 'detail': mismatches},
    note='Tolerance 0.01: ALS init is seeded but factor rotation may vary slightly.',
)"""),
    md("""## 4. Lưu artifact và per-user NDCG

`peruser_ndcg_{split}.npz` là đầu vào **bắt buộc** cho kiểm định cặp ở notebook 10. Không thay bằng summary — kiểm định cặp cần từng giá trị per-user, không chỉ trung bình."""),
    code("""outputs_dir = run.run_dir / 'outputs'
outputs_dir.mkdir(parents=True, exist_ok=True)

saved = {}
for strategy in SPLITS_TO_RUN:
    model_path = outputs_dir / f'als_{strategy}.json'
    model_path.write_text(
        json.dumps(als_by_split[strategy], ensure_ascii=False, indent=2, default=str),
        encoding='utf-8',
    )

    per_user = peruser_by_split[strategy]
    users_array = np.array([u for u, _ in per_user], dtype=np.int64)
    scores_array = np.array([s for _, s in per_user], dtype=np.float32)
    npz_path = outputs_dir / f'peruser_ndcg_{strategy}.npz'
    np.savez_compressed(npz_path, userId=users_array, ndcg=scores_array)

    saved[strategy] = {
        'json': str(model_path),
        'npz': str(npz_path),
        'users': int(users_array.size),
        'mean': float(scores_array.mean()) if scores_array.size else 0.0,
    }
    print(f'{strategy:<18}json={model_path.stat().st_size:>8,}B  npz users={users_array.size:,}  mean={saved[strategy]["mean"]:.4f}')

summary = {
    'protocol_id': spark_utils.PROTOCOL_ID,
    'model': 'ALS_implicit',
    'params': {'rank': 16, 'maxIter': 8, 'regParam': 0.05, 'alpha': 10.0, 'implicitPrefs': True, 'seed': spark_utils.DEFAULT_SEED},
    'subsample_users': spark_utils.SUBSAMPLE_USERS,
    'fit_scope': 'FULL 162,541 users (run 2026-11-17) — subsample 30,000 chỉ dùng ở run 2026-11-15',
    'k': spark_utils.TOP_K,
    'relevance_threshold': spark_utils.RELEVANCE_THRESHOLD,
    'results': als_by_split,
    'artifacts': saved,
    'mismatches': mismatches,
}
summary_path = outputs_dir / 'als_summary.json'
summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding='utf-8')

reloaded = json.loads(summary_path.read_text(encoding='utf-8'))
assert set(reloaded['results']) == set(SPLITS_TO_RUN)
assert all(Path(v['npz']).is_file() for v in reloaded['artifacts'].values())

print()
print('Summary:', summary_path)
run.checkpoint(
    'artifacts_saved',
    'PASS',
    checks={'files': len(saved), 'npz_all_exist': True, 'summary_readback': True, 'mismatches': len(mismatches)},
    note=str(summary_path),
)
run.finish(
    'COMPLETED',
    summary={
        'model': 'ALS_implicit',
        'splits': SPLITS_TO_RUN,
        'ndcg': {s: als_by_split[s]['ndcg10'] for s in SPLITS_TO_RUN},
        'mismatches': len(mismatches),
        'summary': str(summary_path),
    },
)
spark_utils.stop_spark(spark)
print('L6c COMPLETE. Next: 09_compare_and_reversal.ipynb')"""),
]

for index, cell in enumerate(cells):
    cell['id'] = f'cell-{index + 1:03d}'
    if cell['cell_type'] == 'code':
        compile(''.join(cell['source']), f'notebook-cell-{index + 1}', 'exec')

notebook = {
    'cells': cells,
    'metadata': {
        'kernelspec': {
            'display_name': 'Python 3.14 (BigData RecSys .venv)',
            'language': 'python',
            'name': 'recsys-project-venv',
        },
        'language_info': {'name': 'python'},
    },
    'nbformat': 4,
    'nbformat_minor': 5,
}
OUT.write_text(json.dumps(notebook, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'Created {OUT} with {len(cells)} cells; all code cells compile')

