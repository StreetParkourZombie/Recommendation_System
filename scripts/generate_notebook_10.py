"""Generate Notebook 10: Random baseline trên 3 chiến lược chia tập."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "jupyter" / "10_random_baseline.ipynb"
OUT.parent.mkdir(parents=True, exist_ok=True)


def md(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source.strip("\n").splitlines(keepends=True)}


def code(source):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source.strip("\n").splitlines(keepends=True)}


cells = [
    md("""# 10 — Baseline Random trên 3 chiến lược chia tập

**Mục tiêu:** thêm baseline **Random** (sàn, theo danh sách baseline đã đăng kí đề tài: Random, MostPopular / ALS, ItemKNN / SASRec+CE). Random gợi ý ngẫu nhiên cố định seed cho mỗi user — dùng làm sàn để đo ALS/MostPopular hơn sàn bao nhiêu.

**Input:** split của notebook 04; `data_level_audit.json` của notebook 05; cùng protocol với notebook 06/08 (K=10, relevance >= 4.0, seed=42).

**Output:** `runs/<run_id>/outputs/random_{split}.json`, `peruser_ndcg_random_{split}.npz`, `random_summary.json`.

**Gate L10:** seen exclusion PASS mọi split; NDCG Random thấp nhất trong các model (hợp lý); per-user NDCG lưu cho kiểm định cặp.""" ),
    md("""## Khái niệm — vì sao cần Random

Random là **sàn tuyệt đối**: gợi ý không học gì từ dữ liệu. Ba vai trò:

1. **Chuẩn hoá mức "khó" của split:** nếu NDCG của model thay đổi theo split chủ yếu vì split khó hơn (user ít relevant hơn), chênh NDCG giữa model tốt và Random cho biết phần "cố ý học được" còn lại bao nhiêu ở mỗi split.
2. **Chống khoe số tuyệt đối:** NDCG 0,2581 của ALS không có ý nghĩa nếu không có sàn so. Sàn Random gần như thấp nhất (chỉ hơn đoán sai cấu trúc).
3. **Ngôn ngữ bài giảng (Bài 04):** bảng đối chuẩn cần nhóm "Sàn" (Random, MostPopular) tách khỏi nhóm "kinh điển" (ALS, ItemKNN) và "SOTA" (SASRec+CE).

**Cách triển khai:** dùng seed cố định (`numpy` Generator, seed 42) — cùng seed của protocol. Gợi ý **10 item ngẫu nhiên từ catalog** của train split đó, loại item user đã thấy trong train (cùng luật seen exclusion với ALS) — nếu không loại, Random có lợi thế giả tạo so với model bị loại.""" ),
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
from pyspark.sql import functions as F

SPLITS_TO_RUN = list(split_lib.STRATEGIES)  # doi thanh ['leave_one_out'] de chay nhanh mot split

run = NotebookRun(
    project_root,
    '10_random_baseline',
    metadata={
        'protocol_id': spark_utils.PROTOCOL_ID,
        'model': 'Random',
        'seed': spark_utils.DEFAULT_SEED,
        'k': spark_utils.TOP_K,
        'relevance_threshold': spark_utils.RELEVANCE_THRESHOLD,
        'fit_scope': 'FULL 162,541 users — same protocol as ALS run 2026-11-17',
        'registered_baseline': 'Random (san) — docs/About/Reseach_Method_Submission.md',
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
print('Audit source:', audit_path)

run.checkpoint(
    'prerequisites_ok',
    'PASS',
    checks={'audit': str(audit_path), 'splits': SPLITS_TO_RUN},
)"""),
    code("""spark = spark_utils.get_spark('RecSys10RandomBaseline')
print('Spark:', spark.version, '| master:', spark.sparkContext.master)
run.checkpoint('spark_ready', 'PASS', checks={'spark_version': spark.version, 'master': spark.sparkContext.master})"""),
    md("""## 2. Sinh gợi ý Random cho từng split

Mỗi split: lấy catalog từ train → random lấy 10 item cho mỗi eligible user, loại item đã thấy → đo NDCG/Hit/Recall/bias. Không có bước fit nên `fit_seconds = 0`.""" ),
    code("""random_by_split = {}
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

    eligible_sub = leakage.eligible_users(train_sub, spark_utils.MIN_TRAIN)
    truth = als_rec.collect_truth(test_sub, eligible_sub, spark_utils.RELEVANCE_THRESHOLD)
    seen = als_rec.collect_seen(train_sub)
    print(f'  truth users={len(truth):,}  seen users={len(seen):,}')

    catalog = pop_lib.train_popularity(train_sub)
    catalog_ids = np.array(sorted(catalog.keys()), dtype=np.int64)
    print(f'  catalog={len(catalog_ids):,} items')

    rng = np.random.default_rng(spark_utils.DEFAULT_SEED)
    item_position = {int(i): pos for pos, i in enumerate(catalog_ids)}

    # Sinh top-K ngau nhien, loai item da thay trong train
    recommendations = {}
    for user in sorted(truth):
        blocked_mask = np.zeros(len(catalog_ids), dtype=bool)
        for item in seen.get(user, ()):  # da thay trong train
            pos = item_position.get(int(item))
            if pos is not None:
                blocked_mask[pos] = True
        candidates = catalog_ids[~blocked_mask]
        if len(candidates) <= spark_utils.TOP_K:
            picks = candidates
        else:
            picks = rng.choice(candidates, size=spark_utils.TOP_K, replace=False)
        recommendations[user] = picks

    print(f'  recommended users={len(recommendations):,}')

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
    random_by_split[strategy] = {
        'model': 'Random',
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
        'catalog_items': int(len(catalog_ids)),
        'seed': spark_utils.DEFAULT_SEED,
        'relevance_threshold': spark_utils.RELEVANCE_THRESHOLD,
        'fit_seconds': 0.0,
        'total_seconds': round(total_seconds, 1),
        'bias': bias,
        'seen_exclusion': seen_report['status'],
    }
    peruser_by_split[strategy] = ndcg_per_user

    print(f\"  ndcg@10={ndcg_mean:.4f}  hit@10={hit_mean:.4f}  recall@10={recall_mean:.4f}  mrr@10={mrr_mean:.4f}\")
    print(f\"  novelty@10={diversity['novelty_at_k']:.4f}  diversity@10={diversity['diversity_at_k']:.4f} (genre Jaccard, {diversity['users_measured']:,} user)\")
    print(f'  total {total_seconds:.1f}s')
    run.log('RANDOM_RESULT', strategy=strategy, result=random_by_split[strategy])

    train_sub.unpersist(); test_sub.unpersist()
    del train_df, test_df, train_sub, test_sub, eligible_sub, truth, seen, recommendations
    gc.collect()
    print('  gc done — bộ nhớ driver đã giải phóng giữa 2 split')

run.checkpoint(
    'random_complete',
    'PASS' if all(v['status'] == 'PASS' for v in seen_checks.values()) else 'FAIL',
    checks={
        'strategies': list(random_by_split),
        'seen_exclusion': {k: v['status'] for k, v in seen_checks.items()},
    },
)"""),
    md("""## 3. Đọc kết quả Random và so sánh với MostPopular / ALS

Ba điều cần đọc:

1. **NDCG Random thấp nhất** — nếu không thấp nhất, có lỗi (ngẫu nhiên không thể thắng model có học).
2. **Bias ratio Random ≈ 1** — ngẫu nhiên theo phân phối catalog, không nghiêng phổ biến (khác hẳn MostPopular > 18).
3. **Catalog coverage cao nhất** — Random chọn đều khắp catalog, khác MostPopular chỉ chọn 10 item.""" ),
    code("""# so sanh voi summary MostPopular va ALS moi nhat
def latest_summary(name):
    found = sorted(runs_dir.glob(f'*/outputs/{name}'), key=lambda p: p.stat().st_mtime, reverse=True)
    return json.loads(found[0].read_text(encoding='utf-8')) if found else None

pop_summary = latest_summary('mostpopular_summary.json')
als_summary = latest_summary('als_summary.json')

header = f\"{'split':<18}{'random':>8}{'mostpop':>9}{'als':>8}{'als/rand':>10}{'pop/rand':>10}{'bias_rnd':>10}{'cov_rnd':>9}\"
print(header)
print('-' * len(header))
for strategy in SPLITS_TO_RUN:
    r = random_by_split[strategy]
    b = r['bias']
    pop_v = pop_summary['results'][strategy]['ndcg10'] if pop_summary and strategy in pop_summary['results'] else None
    als_v = als_summary['results'][strategy]['ndcg10'] if als_summary and strategy in als_summary['results'] else None
    ar = als_v / r['ndcg10'] if als_v else 0.0
    pr = pop_v / r['ndcg10'] if pop_v else 0.0
    print(f\"{strategy:<18}{r['ndcg10']:>8.4f}{pop_v if pop_v else 0:>9.4f}{als_v if als_v else 0:>8.4f}{ar:>10.2f}x{pr:>10.2f}x\"
          f\"{b['popularity_bias_ratio']:>10.2f}{b['catalog_coverage']:>9.4f}\")

run.log('COMPARISON_SNAPSHOT', strategy=strategy, random=random_by_split[strategy],
        pop=pop_v, als=als_v)
run.checkpoint('sanity_read', 'PASS', checks={'random_is_lowest': all(
    (pop_summary['results'][s]['ndcg10'] > random_by_split[s]['ndcg10']) if pop_summary else True
    for s in SPLITS_TO_RUN
) or pop_summary is None})"""),
    md("""## 4. Lưu artifact và per-user NDCG

`peruser_ndcg_random_{split}.npz` cho kiểm định cặp ở notebook sau (so ALS vs Random per-user).""" ),
    code("""outputs_dir = run.run_dir / 'outputs'
outputs_dir.mkdir(parents=True, exist_ok=True)

saved = {}
for strategy in SPLITS_TO_RUN:
    model_path = outputs_dir / f'random_{strategy}.json'
    model_path.write_text(
        json.dumps(random_by_split[strategy], ensure_ascii=False, indent=2, default=str),
        encoding='utf-8',
    )

    per_user = peruser_by_split[strategy]
    users_array = np.array([u for u, _ in per_user], dtype=np.int64)
    scores_array = np.array([s for _, s in per_user], dtype=np.float32)
    npz_path = outputs_dir / f'peruser_ndcg_random_{strategy}.npz'
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
    'model': 'Random',
    'params': {'seed': spark_utils.DEFAULT_SEED, 'strategy': 'uniform choice from train catalog, seen excluded'},
    'registered_baseline': 'Random (san) — docs/About/Reseach_Method_Submission.md',
    'fit_scope': 'FULL 162,541 users',
    'k': spark_utils.TOP_K,
    'relevance_threshold': spark_utils.RELEVANCE_THRESHOLD,
    'results': random_by_split,
    'artifacts': saved,
}
summary_path = outputs_dir / 'random_summary.json'
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
        'model': 'Random',
        'splits': SPLITS_TO_RUN,
        'ndcg': {s: random_by_split[s]['ndcg10'] for s in SPLITS_TO_RUN},
        'summary': str(summary_path),
    },
)
spark_utils.stop_spark(spark)
print('L10 COMPLETE. Next: regen 09_compare_and_reversal to include Random.')"""),
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
