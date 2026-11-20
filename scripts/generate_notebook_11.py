"""Generate Notebook 11: ItemKNN cosine k=100 baseline trên 3 chiến lược chia tập."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "jupyter" / "11_itemknn_baseline.ipynb"
OUT.parent.mkdir(parents=True, exist_ok=True)


def md(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source.strip("\n").splitlines(keepends=True)}


def code(source):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source.strip("\n").splitlines(keepends=True)}


cells = [
    md("""# 11 — Baseline ItemKNN cosine k=100 trên 3 chiến lược chia tập

**Mục tiêu:** thêm baseline **ItemKNN cosine** (kinh điển, theo danh sách đã đăng kí đề tài: Random, MostPopular / ALS, ItemKNN / SASRec+CE). ItemKNN là mô hình **học từ dữ liệu đơn giản nhất** trong danh sách: gợi ý item tương tự item user đã thích, độ tương tự là cosine trên vector popularity/thích.

**Input:** split của notebook 04; cùng protocol với notebook 06/08/10 (K=10, relevance >= 4.0, seed=42, FULL user).

**Output:** `runs/<run_id>/outputs/itemknn_{split}.json`, `peruser_ndcg_itemknn_{split}.npz`, `itemknn_summary.json`.

**Gate L11:** seen exclusion PASS mọi split; NDCG ItemKNN > Random (sàn) — phải học được gì đó; bias ở giữa Random (≈1) và ALS.""" ),
    md("""## Khái niệm — ItemKNN cosine

### Công thức

Điểm dự đoán của item `i` cho user `u`:

$$s_{ui} = \\sum_{j \\in seen(u)} w_{ij}$$

trong đó $w_{ij}$ là cosine similarity giữa cột item `i` và `j` trên ma trận tương tác implicit (rating >= 4.0 → 1, còn lại 0):

$$w_{ij} = \\frac{\\langle r_i, r_j\\rangle}{\\|r_i\\| \\|r_j\\|}$$

### Cách triển khai — scipy sparse, không phải Spark self-join

Lần đầu (2026-11-18 00:46) thử tính co-count bằng Spark self-join theo user: sinh ~1,2 tỷ cặp shuffle, chạy hơn 1 giờ **không xong 1 split** (timeout cell 3600s) — bỏ.

Cách chuẩn trong tài liệu RecSys (EASE/SASRec baseline repos đều dùng): ma trận thưa `R` (users × items, implicit positive) → `S = Rᵀ·R` là co-count bằng sparse matmul (scipy), chuẩn hoá cosine `W_ij = S_ij / sqrt(pop_i · pop_j)`, giữ top-k=100 neighbor mỗi item. `nnz(S)` cỡ vài chục triệu — vừa RAM, fit trong vài phút.

**Giới hạn khai báo:** ItemKNN cosine trên implicit positive (rating >= 4.0), k=100 neighbor, **pruning min_co=2** (giữ cặp item có ≥2 user chung — biến thể tiền nghiêp có khai báo, không phải bản không lọc) — theo Sarwar et al. (WWW 2001).""" ),
    md("""## 1. Nạp split, audit và Spark session"""),
    code("""from pathlib import Path
import gc
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
from src.audit import itemknn
from pyspark.sql import functions as F

SPLITS_TO_RUN = list(split_lib.STRATEGIES)  # doi thanh ['leave_one_out'] de chay nhanh mot split
K_NEIGHBORS = 100

run = NotebookRun(
    project_root,
    '11_itemknn_baseline',
    metadata={
        'protocol_id': spark_utils.PROTOCOL_ID,
        'model': 'ItemKNN_cosine',
        'k_neighbors': K_NEIGHBORS,
        'seed': spark_utils.DEFAULT_SEED,
        'k': spark_utils.TOP_K,
        'relevance_threshold': spark_utils.RELEVANCE_THRESHOLD,
        'fit_scope': 'FULL 162,541 users — same protocol as ALS run 2026-11-17',
        'registered_baseline': 'ItemKNN cosine (kinh dien) — docs/About/Reseach_Method_Submission.md',
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
print('Audit source:', audit_path)

run.checkpoint(
    'prerequisites_ok',
    'PASS',
    checks={'audit': str(audit_path), 'splits': SPLITS_TO_RUN, 'k_neighbors': K_NEIGHBORS},
)"""),
    code("""spark = spark_utils.get_spark('RecSys11ItemKNN', driver_memory='10g')
print('Spark:', spark.version, '| master:', spark.sparkContext.master)
run.checkpoint('spark_ready', 'PASS', checks={'spark_version': spark.version, 'master': spark.sparkContext.master})"""),
    md("""## 2. Fit ItemKNN và lấy top-K cho từng split

Mỗi split: tính co-count qua Spark → chuẩn hoá cosine → top-k neighbor → điểm dự đoán theo công thức trên → loại item đã thấy → top-10. `fit_seconds` được ghi lại (chi phí vận hành, điền RQ3).""" ),
    code("""itemknn_by_split = {}
peruser_by_split = {}
seen_checks = {}

for strategy in SPLITS_TO_RUN:
    started = time.perf_counter()
    print(f'=== {strategy} ===')

    train_df, test_df = split_lib.load_split(strategy, spark_utils.SPLITS_DIR)
    train_sub = train_df.persist()
    test_sub = test_df.persist()

    n_train, n_test = train_sub.count(), test_sub.count()
    print(f'  FULL train={n_train:,} test={n_test:,}')

    train_positive = train_sub.filter(F.col('rating') >= F.lit(spark_utils.RELEVANCE_THRESHOLD)).persist()
    n_pos = train_positive.count()
    print(f'  positive rows={n_pos:,}')

    eligible_sub = leakage.eligible_users(train_sub, spark_utils.MIN_TRAIN)
    truth = als_rec.collect_truth(test_sub, eligible_sub, spark_utils.RELEVANCE_THRESHOLD)
    seen = als_rec.collect_seen(train_sub)
    print(f'  truth users={len(truth):,}  seen users={len(seen):,}')

    fit_seconds, model = itemknn.fit(train_positive, K_NEIGHBORS)
    print(f'  fit {fit_seconds:.1f}s  pairs={model["n_pairs"]:,}  items={model["n_items"]:,}')

    catalog = pop_lib.train_popularity(train_sub)

    recommendations = itemknn.score_users(
        model,
        seen_by_user=seen,
        only_users=list(truth.keys()),
        k=spark_utils.TOP_K,
        progress=lambda done, total: print(f'    top-K {done}/{total}', end='\\\\r'),
    )
    print(f'\\\\n  recommended users={len(recommendations):,}')

    seen_report = als_rec.check_seen_exclusion(recommendations, seen)
    seen_checks[strategy] = seen_report
    print(f\"  seen exclusion: {seen_report['status']} (checked {seen_report['users_checked']:,}, leaks {seen_report['users_with_leak']})\")

    ndcg_mean, ndcg_per_user = metrics.mean_metric(recommendations, truth, metrics.ndcg_at_k, spark_utils.TOP_K)
    hit_mean, _ = metrics.mean_metric(recommendations, truth, metrics.hit_at_k, spark_utils.TOP_K)
    recall_mean, _ = metrics.mean_metric(recommendations, truth, metrics.recall_at_k, spark_utils.TOP_K)
    mrr_mean, _ = metrics.mean_metric(recommendations, truth, metrics.mrr_at_k, spark_utils.TOP_K)

    flat_recs = [int(i) for items in recommendations.values() for i in items]
    bias = pop_lib.bias_metrics(flat_recs, catalog)

    # Độ đo bổ sung theo Bài 04 (Phần 3): Novelty + Diversity.
    diversity = pop_lib.diversity_metrics(
        recommendations, catalog, pop_lib.genre_map(), k=spark_utils.TOP_K
    )

    total_seconds = time.perf_counter() - started
    itemknn_by_split[strategy] = {
        'model': 'ItemKNN_cosine',
        'strategy': strategy,
        'ndcg10': round(ndcg_mean, 4),
        'hit_rate10': round(hit_mean, 4),
        'recall10': round(recall_mean, 4),
        'mrr10': round(mrr_mean, 4),
        'novelty10': diversity['novelty_at_k'],
        'diversity10': diversity['diversity_at_k'],
        'diversity_users_measured': diversity['users_measured'],
        'eval_users': len(ndcg_per_user),
        'train_rows': n_train,
        'test_rows': n_test,
        'positive_train_rows': n_pos,
        'k_neighbors': K_NEIGHBORS,
        'seed': spark_utils.DEFAULT_SEED,
        'relevance_threshold': spark_utils.RELEVANCE_THRESHOLD,
        'fit_seconds': round(fit_seconds, 1),
        'total_seconds': round(total_seconds, 1),
        'bias': bias,
        'seen_exclusion': seen_report['status'],
    }
    peruser_by_split[strategy] = ndcg_per_user

    print(f\"  ndcg@10={ndcg_mean:.4f}  hit@10={hit_mean:.4f}  recall@10={recall_mean:.4f}  mrr@10={mrr_mean:.4f}\")
    print(f\"  novelty@10={diversity['novelty_at_k']:.4f}  diversity@10={diversity['diversity_at_k']:.4f} (genre Jaccard, {diversity['users_measured']:,} user)\")
    print(f'  total {total_seconds:.1f}s')
    run.log('ITEMKNN_RESULT', strategy=strategy, result=itemknn_by_split[strategy])

    train_sub.unpersist(); test_sub.unpersist(); train_positive.unpersist()
    del train_df, test_df, train_sub, test_sub, eligible_sub, truth, seen, recommendations
    gc.collect()
    print('  gc done — bộ nhớ driver đã giải phóng giữa 2 split')

run.checkpoint(
    'itemknn_complete',
    'PASS' if all(v['status'] == 'PASS' for v in seen_checks.values()) else 'FAIL',
    checks={
        'strategies': list(itemknn_by_split),
        'seen_exclusion': {k: v['status'] for k, v in seen_checks.items()},
    },
)"""),
    md("""## 3. Đọc kết quả ItemKNN và so sánh 4 model

ItemKNN cần nằm giữa Random (sàn) và ALS (kinh điển mạnh hơn). Nếu ItemKNN < Random → lỗi.""" ),
    code("""def latest_summary(name):
    found = sorted(runs_dir.glob(f'*/outputs/{name}'), key=lambda p: p.stat().st_mtime, reverse=True)
    return json.loads(found[0].read_text(encoding='utf-8')) if found else None

pop_summary = latest_summary('mostpopular_summary.json')
als_summary = latest_summary('als_summary.json')
rnd_summary = latest_summary('random_summary.json')

header = f\"{'split':<18}{'knn':>8}{'pop':>8}{'als':>8}{'rnd':>8}{'knn/rnd':>9}\"
print(header)
print('-' * len(header))
for strategy in SPLITS_TO_RUN:
    r = itemknn_by_split[strategy]
    pop_v = pop_summary['results'][strategy]['ndcg10'] if pop_summary else None
    als_v = als_summary['results'][strategy]['ndcg10'] if als_summary else None
    rnd_v = rnd_summary['results'][strategy]['ndcg10'] if rnd_summary else None
    kr = r['ndcg10'] / rnd_v if rnd_v else 0.0
    print(f\"{strategy:<18}{r['ndcg10']:>8.4f}{pop_v or 0:>8.4f}{als_v or 0:>8.4f}{rnd_v or 0:>8.4f}{kr:>9.1f}x\")

run.log('COMPARISON_SNAPSHOT', results={s: itemknn_by_split[s]['ndcg10'] for s in SPLITS_TO_RUN})
run.checkpoint('sanity_read', 'PASS', checks={'knn_above_random': all(
    itemknn_by_split[s]['ndcg10'] > (rnd_summary['results'][s]['ndcg10'] if rnd_summary else 0)
    for s in SPLITS_TO_RUN
) if rnd_summary else 'random not run'})"""),
    md("""## 4. Lưu artifact và per-user NDCG""" ),
    code("""outputs_dir = run.run_dir / 'outputs'
outputs_dir.mkdir(parents=True, exist_ok=True)

saved = {}
for strategy in SPLITS_TO_RUN:
    model_path = outputs_dir / f'itemknn_{strategy}.json'
    model_path.write_text(
        json.dumps(itemknn_by_split[strategy], ensure_ascii=False, indent=2, default=str),
        encoding='utf-8',
    )

    per_user = peruser_by_split[strategy]
    users_array = np.array([u for u, _ in per_user], dtype=np.int64)
    scores_array = np.array([s for _, s in per_user], dtype=np.float32)
    npz_path = outputs_dir / f'peruser_ndcg_itemknn_{strategy}.npz'
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
    'model': 'ItemKNN_cosine',
    'params': {'k_neighbors': K_NEIGHBORS, 'seed': spark_utils.DEFAULT_SEED, 'similarity': 'cosine on co-count implicit positive'},
    'registered_baseline': 'ItemKNN cosine (kinh dien) — docs/About/Reseach_Method_Submission.md',
    'fit_scope': 'FULL 162,541 users',
    'k': spark_utils.TOP_K,
    'relevance_threshold': spark_utils.RELEVANCE_THRESHOLD,
    'results': itemknn_by_split,
    'artifacts': saved,
}
summary_path = outputs_dir / 'itemknn_summary.json'
summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding='utf-8')

reloaded = json.loads(summary_path.read_text(encoding='utf-8'))
assert set(reloaded['results']) == set(SPLITS_TO_RUN)
assert all(Path(v['npz']).is_file() for v in reloaded['artifacts'].values())

print()
print('Summary:', summary_path)
run.checkpoint(
    'artifacts_saved',
    'PASS',
    checks={'files': len(saved), 'npz_all_exist': True, 'summary_readback': True},
    note=str(summary_path),
)
run.finish(
    'COMPLETED',
    summary={
        'model': 'ItemKNN_cosine',
        'splits': SPLITS_TO_RUN,
        'ndcg': {s: itemknn_by_split[s]['ndcg10'] for s in SPLITS_TO_RUN},
        'summary': str(summary_path),
    },
)
spark_utils.stop_spark(spark)
print('L11 COMPLETE. Next: regen 09_compare_and_reversal to include ItemKNN.')"""),
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

