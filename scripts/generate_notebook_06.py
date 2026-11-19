"""Generate Notebook 06: MostPopular baseline across the three splits."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "jupyter" / "06_mostpopular_baseline.ipynb"
OUT.parent.mkdir(parents=True, exist_ok=True)


def md(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source.strip("\n").splitlines(keepends=True)}


def code(source):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source.strip("\n").splitlines(keepends=True)}


cells = [
    md("""# 06 — Baseline MostPopular trên 3 chiến lược chia tập

**Mục tiêu:** đo hiệu năng của mô hình "gợi ý phim phổ biến nhất" trên cả 3 split, làm sàn so sánh cho ALS ở notebook 08.

**Input:** split của notebook 04, audit của notebook 05 (cần `eval_users`).

**Output:** `runs/<run_id>/outputs/mostpopular_{split}.json`.

**Gate L6a:** Popularity tính **trên train** (không phải full data), tie-break đơn định, NDCG khớp kết quả đo thật."""),
    md("""## Khái niệm — vì sao baseline này quan trọng

MostPopular là mô hình rẻ nhất có thể tưởng tượng: đếm item nào được xem nhiều nhất trong train, đề xuất đúng danh sách đó cho mọi user. Vì nó không học gì từ sở thích cá nhân, nó là **sàn hiệu năng**.

Giá trị của nó trong đề tài này **không** phải để thấy nó yếu. Giá trị là:

1. Nếu MostPopular thắng ALS ở một split nào đó, ta biết split đó có vấn đề (mô hình không học được gì từ dữ liệu test).
2. Nó cho một điểm neo để đọc `popularity_bias_ratio`: một mô hình "cá nhân hóa" mà vẫn có bias gần bằng MostPopular thì thực chất chỉ là MostPopular đội lốt.

Hai quy tắc phải giữ tuyệt đối:

- **Popularity tính trên train.** Dùng full dataset để đếm là rò rỉ test vào baseline, làm sàn bị đẩy cao giả tạo.
- **Tie-break đơn định.** Rất nhiều item có cùng số tương tác; không tie-break thì top-10 thay đổi giữa các lần chạy và kết quả không tái lập được. Ở đây dùng `movieId` tăng dần.

**Về chỉ số thiên lệch:**

- `catalog_coverage`: bao nhiêu phần trăm catalog được đề xuất. MostPopular luôn chỉ đề xuất 10 item → coverage cực thấp. Đó là bản chất, không phải bug.
- `gini_exposure`: 0 là mọi item được đề xuất như nhau, → 1 là dồn hết vào một vài item. MostPopular gần 1.
- `popularity_bias_ratio` = popularity trung bình của item được đề xuất / popularity trung bình toàn catalog. MostPopular luôn rất cao vì nó chọn đúng item phổ biến nhất."""),
    md("""## 1. Nạp split và audit"""),
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
from src.audit import leakage, popularity as pop_lib
from src.audit import metrics
from pyspark.sql import functions as F

run = NotebookRun(
    project_root,
    '06_mostpopular_baseline',
    metadata={
        'protocol_id': spark_utils.PROTOCOL_ID,
        'model': 'MostPopular',
        'k': spark_utils.TOP_K,
        'relevance_threshold': spark_utils.RELEVANCE_THRESHOLD,
        'min_train': spark_utils.MIN_TRAIN,
        'purpose': 'popularity floor across split strategies',
    },
)
run.attach_ipython(get_ipython())
print('Run ID:', run.run_id)

runs_dir = project_root / 'runs'
audit_candidates = sorted(runs_dir.glob('*/outputs/data_level_audit.json'), key=lambda p: p.stat().st_mtime, reverse=True)
assert audit_candidates, 'data_level_audit.json not found; run notebook 05 first.'
audit_path = audit_candidates[0]
audit_doc = json.loads(audit_path.read_text(encoding='utf-8'))
audits = audit_doc['audits']
assert set(audits) == set(split_lib.STRATEGIES)
print('Audit source:', audit_path)
print('Protocol:', audit_doc['protocol_id'])
run.checkpoint('audit_loaded', 'PASS', checks={'audit_path': str(audit_path), 'strategies': list(audits)})"""),
    code("""spark = spark_utils.get_spark('RecSys06MostPopular')
print('Spark:', spark.version, '| master:', spark.sparkContext.master)"""),
    md("""## 2. Popularity phải tính trên train

Ô dưới đây đếm lại số tương tác mỗi item từ train của từng split, in top-10. Chú ý top-10 thay đổi giữa các split — đó là bằng chứng popularity phụ thuộc vào cách chia, không phải hằng số của dataset."""),
    code("""topk_by_split = {}
popularity_by_split = {}

for strategy in split_lib.STRATEGIES:
    train_df, _ = split_lib.load_split(strategy, spark_utils.SPLITS_DIR)
    pop_map = pop_lib.train_popularity(train_df)
    topk = pop_lib.mostpopular_topk(train_df, k=spark_utils.TOP_K, popularity=pop_map)
    topk_by_split[strategy] = topk
    popularity_by_split[strategy] = pop_map

    print(f'--- {strategy} ---')
    print(f'  catalog in train: {len(pop_map):,} items')
    print(f'  top-{spark_utils.TOP_K}: {topk}')
    print(f'  top item count: {pop_map[topk[0]]:,}')
    run.log('POPULARITY_TOPK', strategy=strategy, topk=topk, catalog=len(pop_map))

print()
print('So sanh top-10 giua 3 split:')
for strategy in split_lib.STRATEGIES:
    print(f'  {strategy:<18}{topk_by_split[strategy]}')
run.checkpoint(
    'topk_computed',
    'PASS',
    checks={
        'catalog_sizes': {s: len(popularity_by_split[s]) for s in split_lib.STRATEGIES},
        'topk_lengths': {s: len(topk_by_split[s]) for s in split_lib.STRATEGIES},
    },
)"""),
    md("""## 3. NDCG và HitRate trên tập eval_users

Với MostPopular, mọi user nhận cùng 10 item, nên chỉ cần đếm item nào trong 10 item đó là relevant cho từng user. Code dưới dùng đúng `src.audit.metrics` mà notebook 07 sẽ kiểm tra tay — không viết công thức NDCG riêng ở đây."""),
    code("""metrics_by_split = {}
peruser_by_split = {}

for strategy in split_lib.STRATEGIES:
    started = time.perf_counter()
    train_df, test_df = split_lib.load_split(strategy, spark_utils.SPLITS_DIR)
    eligible = leakage.eligible_users(train_df, spark_utils.MIN_TRAIN)

    truth_rows = (
        test_df.join(F.broadcast(eligible), 'userId')
        .filter(F.col('rating') >= F.lit(spark_utils.RELEVANCE_THRESHOLD))
        .groupBy('userId')
        .agg(F.collect_list('movieId').alias('relevant'))
        .collect()
    )
    truth = {int(r['userId']): {int(i) for i in r['relevant']} for r in truth_rows}

    topk = topk_by_split[strategy]
    recommendations = pop_lib.popularity_recommendations(topk, list(truth.keys()))

    ndcg_mean, ndcg_per_user = metrics.mean_metric(recommendations, truth, metrics.ndcg_at_k, spark_utils.TOP_K)
    dcg_mean, _ = metrics.mean_metric(recommendations, truth, metrics.dcg_at_k, spark_utils.TOP_K)
    hit_mean, _ = metrics.mean_metric(recommendations, truth, metrics.hit_at_k, spark_utils.TOP_K)
    recall_mean, _ = metrics.mean_metric(recommendations, truth, metrics.recall_at_k, spark_utils.TOP_K)
    mrr_mean, _ = metrics.mean_metric(recommendations, truth, metrics.mrr_at_k, spark_utils.TOP_K)

    metrics_by_split[strategy] = {
        'model': 'MostPopular',
        'strategy': strategy,
        'ndcg10': round(ndcg_mean, 4),
        'dcg10': round(dcg_mean, 4),
        'hit_rate10': round(hit_mean, 4),
        'recall10': round(recall_mean, 4),
        'mrr10': round(mrr_mean, 4),
        'eval_users': len(ndcg_per_user),
        'relevant_test_items': sum(len(v) for v in truth.values()),
        'topk': topk,
        'elapsed_seconds': round(time.perf_counter() - started, 1),
    }

    peruser_by_split[strategy] = ndcg_per_user

    print(f'--- {strategy} ---')
    print(f"  ndcg@10={ndcg_mean:.4f}  dcg@10={dcg_mean:.4f}  hit@10={hit_mean:.4f}  recall@10={recall_mean:.4f}  mrr@10={mrr_mean:.4f}")
    print(f'  eval users={len(ndcg_per_user):,}  relevant test items={sum(len(v) for v in truth.values()):,}')
    run.log('POPULARITY_METRICS', strategy=strategy, metrics=metrics_by_split[strategy])

run.checkpoint('metrics_computed', 'PASS', checks={'strategies': list(metrics_by_split)})"""),
    md("""## 4. Chỉ số thiên lệch phổ biến

Với MostPopular, `longtail_coverage` sẽ bằng 0 vì nó chỉ đề xuất 10 item phổ biến nhất — đó là định nghĩa của baseline này, không phải lỗi. Con số này quan trọng khi **so với ALS** ở notebook 08: ALS có thực sự phân tán hơn, hay cũng dồn vào item phổ biến?"""),
    code("""for strategy in split_lib.STRATEGIES:
    bias = pop_lib.bias_metrics(
        topk_by_split[strategy],
        popularity_by_split[strategy],
    )
    metrics_by_split[strategy]['bias'] = bias
    print(f'--- {strategy} ---')
    for key in ('catalog_coverage', 'longtail_coverage', 'gini_exposure',
                'avg_pop_rec', 'avg_pop_all', 'popularity_bias_ratio',
                'tail_threshold_pop', 'tail_items'):
        print(f'  {key:<26}{bias[key]}')
    run.log('POPULARITY_BIAS', strategy=strategy, bias=bias)

print()
print('Doc so: MostPopular chi de xuat', spark_utils.TOP_K, 'item nen coverage gan 0 va gini gan 1.')
print('popularity_bias_ratio hang chuc lan nghia la no chon dung nhom phim pho bien nhat.')"""),
    md("""## 5. Đối chiếu kết quả đo thật và ghi artifact"""),
    code("""expected_ndcg = {'random80_20': 0.0852, 'temporal_global': 0.0455, 'leave_one_out': 0.0183}
mismatches = []
for strategy, want in expected_ndcg.items():
    got = metrics_by_split[strategy]['ndcg10']
    ok = abs(got - want) <= 0.003
    print(f"{'OK  ' if ok else 'DIFF'} {strategy:<18}ndcg@10 got={got:<8}want={want}")
    if not ok:
        mismatches.append((strategy, want, got))

print()
if mismatches:
    print('MISMATCH:', mismatches)
    print('Kiem tra: top-10 co doi khong (tie-break), relevance threshold, eval_users.')
else:
    print('NDCG khop ket qua do that.')

run.log('REPRODUCTION_CHECK', mismatches=len(mismatches), detail=mismatches)
run.checkpoint(
    'reproduction_check',
    'PASS' if not mismatches else 'FAIL',
    checks={'mismatches': len(mismatches), 'detail': mismatches},
    note='Tolerance 0.003: popularity counts depend on split partition layout.',
)"""),
    code("""outputs_dir = run.run_dir / 'outputs'
outputs_dir.mkdir(parents=True, exist_ok=True)

paths = {}
for strategy in split_lib.STRATEGIES:
    path = outputs_dir / f"mostpopular_{strategy}.json"
    path.write_text(
        json.dumps(metrics_by_split[strategy], ensure_ascii=False, indent=2, default=str),
        encoding='utf-8',
    )
    paths[strategy] = str(path)
    print('saved:', path)

    # per-user NDCG cho kiem dinh cap (notebook 12) — cung dinh dang voi notebook 08/10
    users_array = np.array([u for u, _ in peruser_by_split[strategy]], dtype=np.int64)
    scores_array = np.array([s for _, s in peruser_by_split[strategy]], dtype=np.float32)
    npz_path = outputs_dir / f'peruser_ndcg_{strategy}.npz'
    np.savez_compressed(npz_path, userId=users_array, ndcg=scores_array)
    print('saved:', npz_path, f'({users_array.size:,} users)')

summary = {
    'protocol_id': spark_utils.PROTOCOL_ID,
    'model': 'MostPopular',
    'k': spark_utils.TOP_K,
    'relevance_threshold': spark_utils.RELEVANCE_THRESHOLD,
    'results': {s: {k: v for k, v in metrics_by_split[s].items() if k != 'topk'} for s in split_lib.STRATEGIES},
    'mismatches': mismatches,
}
summary_path = outputs_dir / 'mostpopular_summary.json'
summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding='utf-8')

reloaded = json.loads(summary_path.read_text(encoding='utf-8'))
assert set(reloaded['results']) == set(split_lib.STRATEGIES)

print()
header = f"{'split':<18}{'ndcg@10':>10}{'hit@10':>10}{'gini':>9}{'bias_ratio':>12}{'eval_users':>12}"
print(header)
print('-' * len(header))
for strategy in split_lib.STRATEGIES:
    m = metrics_by_split[strategy]
    print(f"{strategy:<18}{m['ndcg10']:>10.4f}{m['hit_rate10']:>10.4f}"
          f"{m['bias']['gini_exposure']:>9.4f}{m['bias']['popularity_bias_ratio']:>12.2f}{m['eval_users']:>12,}")

run.checkpoint(
    'artifacts_saved',
    'PASS',
    checks={'files': len(paths), 'summary_readback': True, 'mismatches': len(mismatches)},
    note=str(summary_path),
)
run.finish('COMPLETED', summary={'model': 'MostPopular', 'summary': str(summary_path), 'mismatches': len(mismatches)})
spark_utils.stop_spark(spark)
print('L6a COMPLETE. Next: 07_ndcg_manual_check.ipynb')"""),
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

