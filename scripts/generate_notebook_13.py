# -*- coding: utf-8 -*-
"""Generate Notebook 13: SASRec + cross-entropy (baseline SOTA da dang ki, GPU local).

Danh sach baseline dang ki (docs/About/Reseach_Method_Submission.md):
  san = Random, MostPopular | kinh dien = ALS, ItemKNN cosine | SOTA = SASRec + CE.
EASE khong chay (khong dang ki). BPR khong chay. Ma tran nhieu seed: bo (1 seed = 42).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "jupyter" / "13_sasrec_ce.ipynb"
OUT.parent.mkdir(parents=True, exist_ok=True)


def md(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source.strip("\n").splitlines(keepends=True)}


def code(source):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source.strip("\n").splitlines(keepends=True)}


cells = [
    md("""# 13 — SASRec + cross-entropy (baseline SOTA đã đăng kí) trên 3 chiến lược chia tập

**Mục tiêu:** đóng baseline cuối trong danh sách đã đăng kí ở `docs/About/Reseach_Method_Submission.md`:

| Tầng | Model | Notebook | Trạng thái |
|---|---|---|---|
| Sàn | Random, MostPopular | 10, 06 | ✅ FULL |
| Kinh điển | ALS, ItemKNN cosine | 08, 11 | ✅ FULL |
| **SOTA** | **SASRec + cross-entropy** | **13 (này)** | đang chạy |

**Input:** split Parquet của notebook 04 tại `D:\\recsys_data\\splits\\`; cùng protocol `project_protocol_v1` (K=10, relevance ≥ 4.0, seed=42, **FULL** user, loại item đã thấy).

**Output:** `runs/<run_id>/outputs/sasrec_{split}.json`, `peruser_ndcg_sasrec_{split}.npz`, `sasrec_summary.json`.

> [!IMPORTANT]
> **Khác biệt phần cứng phải khai báo.** Bốn baseline chạy trên Spark `local[4]` **CPU**; SASRec chạy trên **GPU RTX 4050 Laptop 6 GB** (`docs/About/Hardware_Resources.md`). Vì vậy **không so sánh runtime** SASRec với ALS/ItemKNN — chỉ so sánh **chất lượng** (NDCG@10, Hit@10, Recall@10) trên cùng protocol. Giới hạn này ghi vào `summary.hardware` và slide.

**Gate L13:** (1) `seen_exclusion` PASS mọi split; (2) SASRec > Random (sàn); (3) khai báo rõ `loss = cross_entropy full-catalog`, `device = cuda`, `tuning_budget = 0`.""")
    ,
    md("""## Khái niệm — SASRec và vì sao dùng cross-entropy full-catalog

### Mô hình
SASRec (Kang & McAuley, ICDM 2018) mã hoá **chuỗi tương tác theo thời gian** của user bằng self-attention có mặt nạ nhân quả (chỉ nhìn về quá khứ), rồi lấy vector tại vị trí cuối để chấm điểm mọi item:

$$h_u = \\mathrm{SASRec}([i_1, \\dots, i_{n}]), \\qquad s_{ui} = h_u \\cdot e_i$$

### Loss — cross-entropy trên toàn bộ catalog
Repo gốc của bài [03] (`docs/References/Papers/Code/dataLeakageRec/SASRec/train.py`) dùng `BCEWithLogitsLoss` với **1 negative mẫu ngẫu nhiên** cho mỗi vị trí. Đề tài này đăng kí **"SASRec kết hợp cross-entropy"**, nên bản ở đây dùng:

$$\\mathcal{L} = -\\frac{1}{|{(u,t)}|}\\sum_{(u,t)} \\log \\frac{\\exp(s_{u,y_{u,t}})}{\\sum_{j \\in \\mathcal{I}} \\exp(s_{u,j})}$$

tức softmax trên **toàn bộ catalog** (~38.328 item có trong train positive, đo thực từ smoke run `20261118_143029_..._29c68c40`). Lợi ích phương pháp luận: loss và thủ tục eval (xếp hạng toàn catalog, loại item đã thấy) dùng **cùng một không gian ứng viên** — không có độ lệch "train sampled-negatives / eval full-catalog".

### Chuỗi đầu vào
Chỉ dùng **positive implicit** (`rating ≥ 4.0`) — cùng định nghĩa relevance với 4 baseline. Sắp xếp theo `timestamp` tăng dần, cắt **đuôi** giữ `maxlen` phần tử muộn nhất.

### Ngân sách tinh chỉnh = 0 (điều kiện so sánh công bằng)
Bài giảng PPNCKH Bài 04 yêu cầu các model so với nhau phải có **cùng điều kiện tinh chỉnh**. ALS dùng đúng một cấu hình cố định (rank 16, maxIter 8, reg 0.05, alpha 10.0) và ItemKNN cũng vậy (cosine, k=100, min_co=2) — **không tìm kiếm lưới**. SASRec ở đây giữ nguyên kỷ luật đó: **một cấu hình cố duy nhất**, không grid search. Early stopping chỉ là cơ chế chống quá khớp, **không dùng test** (xem mục validation dưới).""")
    ,
    md("""## 1. Kiểm tra GPU và nạp thư viện

Cell này **dừng ngay** nếu PyTorch bản CUDA chưa được cài. Xem hướng dẫn cài ở `docs/Project/Plans/Research/Implementation/06_Huong_Dan_Chay_SASRec_va_MRR.md`.""")
    ,
    code("""from pathlib import Path
import gc
import json
import os
import random
import sys
import time

import numpy as np

project_root = Path.cwd().resolve()
while project_root != project_root.parent and not (project_root / 'src').is_dir():
    project_root = project_root.parent
sys.path.insert(0, str(project_root))

from IPython import get_ipython

try:
    import torch
except ImportError as exc:
    raise SystemExit(
        'Chua cai PyTorch. Chay:  .\\\\.venv\\\\Scripts\\\\python.exe -m pip install torch --index-url '
        'https://download.pytorch.org/whl/cu126  (xem docs/Project/Plans/Research/Implementation/'
        '06_Huong_Dan_Chay_SASRec_va_MRR.md)'
    ) from exc

from src.recsys.notebook_logging import NotebookRun
from src.utils import spark_utils
from src.audit import splits as split_lib
from src.audit import leakage, popularity as pop_lib, als_rec, metrics
from src.audit import sasrec
from pyspark.sql import functions as F

# --- cau hinh SASRec + cross-entropy: MOT cau hinh co dinh, khong grid search ---
SASREC_CFG = {
    'maxlen': 50,
    'hidden_units': 50,
    'num_blocks': 1,
    'num_heads': 1,
    'dropout_rate': 0.2,
    'lr': 1e-3,
    'batch_size': 32,
    'accum_steps': 4,
    'weight_decay': 0.0,
    'epochs': 20,
    'patience': 3,
    'loss': 'cross_entropy_full_catalog_softmax',
}
VAL_FRACTION = 0.1          # cat theo user, dung cho early stopping — KHONG phai test
SMOKE_USERS = None          # dat 3000 de thu pipeline trong vai phut, de None de chay that

SPLITS_TO_RUN = list(split_lib.STRATEGIES)  # doi thanh ['random80_20'] de chay tung split

run = NotebookRun(
    project_root,
    '13_sasrec_ce',
    metadata={
        'protocol_id': spark_utils.PROTOCOL_ID,
        'model': 'SASRec_CE',
        'params': SASREC_CFG,
        'seed': spark_utils.DEFAULT_SEED,
        'k': spark_utils.TOP_K,
        'relevance_threshold': spark_utils.RELEVANCE_THRESHOLD,
        'fit_scope': 'FULL 162,541 users — cung protocol voi 4 baseline',
        'registered_baseline': 'SASRec ket hop cross-entropy (SOTA) — docs/About/Reseach_Method_Submission.md',
        'tuning_budget': 0,
        'splits': SPLITS_TO_RUN,
    },
)
run.attach_ipython(get_ipython())
print('Run ID:', run.run_id)
print('Splits to run:', SPLITS_TO_RUN)
print('Config:', json.dumps(SASREC_CFG))

cuda_ok = bool(torch.cuda.is_available())
print('torch', torch.__version__, '| cuda build', torch.version.cuda, '| available', cuda_ok)
if not cuda_ok:
    print('CANH BAO: torch.cuda.is_available() == False — se chay CPU, rat cham (hang gio/split).')
    print('        Cai ban CUDA:  .\\\\.venv\\\\Scripts\\\\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cu126')
else:
    print('device:', torch.cuda.get_device_name(0))

run.checkpoint(
    'gpu_check',
    'PASS' if cuda_ok else 'WARN',
    checks={'torch_version': torch.__version__, 'cuda_build': torch.version.cuda,
            'cuda_available': cuda_ok,
            'device': torch.cuda.get_device_name(0) if cuda_ok else 'cpu'},
)""")
    ,
    code("""# Ngau nhien co dinh cho viec cat tap validation (torch se duoc seed rieng trong train_model)
random.seed(spark_utils.DEFAULT_SEED)
np.random.seed(spark_utils.DEFAULT_SEED)
if cuda_ok:
    torch.manual_seed(spark_utils.DEFAULT_SEED)
    torch.cuda.manual_seed_all(spark_utils.DEFAULT_SEED)
    torch.backends.cuda.matmul.allow_tf32 = True
device = torch.device('cuda' if cuda_ok else 'cpu')
print('device =', device)

spark = spark_utils.get_spark('RecSys13SASRec', driver_memory='6g')
print('Spark:', spark.version, '| master:', spark.sparkContext.master)
run.checkpoint('spark_ready', 'PASS', checks={'spark_version': spark.version, 'master': spark.sparkContext.master})""")
    ,
    md("""## 2. Fit và đánh giá SASRec theo từng split

Mỗi split, theo đúng thứ tự:

1. Nạp train/test Parquet (Spark) → lọc positive `rating ≥ 4.0` → `toPandas()` (chỉ 3 cột) để dựng chuỗi theo `timestamp`.
2. **Chia validation theo user** (`VAL_FRACTION`): dùng cho early stopping. Tập test **không** tham gia vào bất quyết định tinh chỉnh nào.
3. Fit cross-entropy full-catalog, giữ trọng số tốt nhất theo **val** NDCG@10.
4. Với mỗi user đủ điều kiện: đưa **toàn bộ chuỗi train** vào mạng → chấm mọi item → **mask item đã thấy** → top-10.
5. Tính NDCG@10 / Hit@10 / Recall@10 / MRR@10 + chỉ số thiên lệch, bằng đúng hàm ở `src/audit/metrics.py` mà 4 baseline đã dùng.

`fit_seconds` và `total_seconds` được ghi vào summary (chỉ số RQ3, nhưng **có khai báo** CPU-vs-GPU).""")
    ,
    code("""sasrec_by_split = {}
peruser_by_split = {}
seen_checks = {}
train_histories = {}

for strategy in SPLITS_TO_RUN:
    started = time.perf_counter()
    print(f'=== {strategy} ===')

    train_df, test_df = split_lib.load_split(strategy, spark_utils.SPLITS_DIR)
    train_sub = train_df.persist()
    test_sub = test_df.persist()
    n_train, n_test = train_sub.count(), test_sub.count()

    train_positive = train_sub.filter(
        F.col('rating') >= F.lit(spark_utils.RELEVANCE_THRESHOLD)
    ).persist()
    n_pos = train_positive.count()
    print(f'  FULL train={n_train:,} test={n_test:,} positive={n_pos:,}')

    # --- dung chuoi theo timestamp (pandas/Arrow, khong collect Row objects) ---
    pdf = train_positive.select('userId', 'movieId', 'timestamp').toPandas()
    print(f'  toPandas {len(pdf):,} dong')

    eligible_sub = leakage.eligible_users(train_sub, spark_utils.MIN_TRAIN)
    truth = als_rec.collect_truth(test_sub, eligible_sub, spark_utils.RELEVANCE_THRESHOLD)
    seen = als_rec.collect_seen(train_sub)
    print(f'  truth users={len(truth):,}  seen users={len(seen):,}')

    uniq_items, vocab_pos = sasrec.build_vocab(pdf['movieId'].to_numpy())
    n_items = int(uniq_items.size)
    print(f'  catalog (items co trong train positive) = {n_items:,}')

    seqs_all = sasrec.build_sequences(
        pdf['userId'].to_numpy(),
        pdf['movieId'].map(vocab_pos).to_numpy(),
        pdf['timestamp'].to_numpy(),
        max_len=SASREC_CFG['maxlen'],
    )
    del pdf
    gc.collect()
    if SMOKE_USERS:
        keep_users = sorted(seqs_all)[:SMOKE_USERS]
        seqs_all = {u: seqs_all[u] for u in keep_users}
    print(f'  users co chuoi >= 2 phan tu = {len(seqs_all):,}')

    # --- chia validation theo user, don dinh theo seed ---
    rng = np.random.default_rng(spark_utils.DEFAULT_SEED)
    users_sorted = np.array(sorted(seqs_all), dtype=np.int64)
    val_mask = rng.random(users_sorted.size) < VAL_FRACTION
    val_users = set(users_sorted[val_mask].tolist())
    seqs_fit = {int(u): s for u, s in seqs_all.items() if int(u) not in val_users}
    seqs_val = {int(u): s for u, s in seqs_all.items() if int(u) in val_users}
    data_fit = sasrec.SeqData(seqs_fit)
    data_val = sasrec.SeqData(seqs_val)
    print(f'  fit users={len(data_fit):,}  val users={len(data_val):,}')

    net = sasrec.make_model(
        torch, n_items, SASREC_CFG['hidden_units'], SASREC_CFG['maxlen'],
        SASREC_CFG['num_blocks'], SASREC_CFG['num_heads'], SASREC_CFG['dropout_rate'], device,
    )
    n_params = sum(p.numel() for p in net.parameters())
    print(f'  so tham so = {n_params:,}')

    def _prog(epoch, total, loss, vndcg, elapsed, _s=strategy):
        print(f'    [{_s}] epoch {epoch}/{total}  loss={loss:.4f}  val_ndcg10={vndcg:.4f}  {elapsed:.0f}s')

    fit_seconds, history, fit_meta = sasrec.train_model(
        torch, net, data_fit, data_val, n_items, device,
        epochs=SASREC_CFG['epochs'], lr=SASREC_CFG['lr'], batch_size=SASREC_CFG['batch_size'],
        accum_steps=SASREC_CFG['accum_steps'], weight_decay=SASREC_CFG['weight_decay'],
        patience=SASREC_CFG['patience'], seed=spark_utils.DEFAULT_SEED, k_eval=spark_utils.TOP_K,
        progress=_prog,
    )
    train_histories[strategy] = {'history': history, 'meta': fit_meta, 'n_params': int(n_params)}
    print(f\"  fit xong {fit_seconds:.1f}s  best_epoch={fit_meta['best_epoch']}  val_ndcg10={fit_meta['best_val_ndcg10']:.4f}\")

    eval_users = [u for u in truth if u in seqs_all]
    print(f'  users se danh gia (co chuoi train) = {len(eval_users):,}')
    recommendations = sasrec.recommend_topk(
        torch, net, seqs_all, eval_users, seen, vocab_pos, n_items, device,
        k=spark_utils.TOP_K, chunk=128,
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

    catalog = pop_lib.train_popularity(train_sub)
    flat_recs = [int(i) for items in recommendations.values() for i in items]
    bias = pop_lib.bias_metrics(flat_recs, catalog)

    total_seconds = time.perf_counter() - started
    sasrec_by_split[strategy] = {
        'model': 'SASRec_CE',
        'strategy': strategy,
        'ndcg10': round(ndcg_mean, 4),
        'hit_rate10': round(hit_mean, 4),
        'recall10': round(recall_mean, 4),
        'mrr10': round(mrr_mean, 4),
        'eval_users': len(ndcg_per_user),
        'train_rows': n_train,
        'test_rows': n_test,
        'positive_train_rows': n_pos,
        'n_items': n_items,
        'n_params': int(n_params),
        'best_epoch': fit_meta['best_epoch'],
        'best_val_ndcg10': fit_meta['best_val_ndcg10'],
        'epochs_run': fit_meta['epochs_run'],
        'seed': spark_utils.DEFAULT_SEED,
        'relevance_threshold': spark_utils.RELEVANCE_THRESHOLD,
        'fit_seconds': round(fit_seconds, 1),
        'total_seconds': round(total_seconds, 1),
        'bias': bias,
        'seen_exclusion': seen_report['status'],
    }
    peruser_by_split[strategy] = ndcg_per_user

    print(f\"  ndcg@10={ndcg_mean:.4f}  hit@10={hit_mean:.4f}  recall@10={recall_mean:.4f}  mrr@10={mrr_mean:.4f}\")
    print(f'  total {total_seconds:.1f}s  (GPU — KHONG so sanh duoc voi runtime CPU cua ALS/ItemKNN)')
    run.log('SASREC_RESULT', strategy=strategy, result=sasrec_by_split[strategy])

    del net, recommendations, seqs_all, seqs_fit, seqs_val, data_fit, data_val
    if cuda_ok:
        torch.cuda.empty_cache()
    train_sub.unpersist(); test_sub.unpersist(); train_positive.unpersist()
    del train_df, test_df, train_sub, test_sub, train_positive, eligible_sub, truth, seen
    gc.collect()
    print('  gc done — bo nho driver/GPU da giai phong giua 2 split')

run.checkpoint(
    'sasrec_complete',
    'PASS' if all(v['status'] == 'PASS' for v in seen_checks.values()) else 'FAIL',
    checks={
        'strategies': list(sasrec_by_split),
        'seen_exclusion': {k: v['status'] for k, v in seen_checks.items()},
    },
)""")
    ,
    md("""## 3. Đọc kết quả và so sánh 5 model

Kỳ vọng theo tài liệu: SASRec ≥ ALS/ItemKNN trên `random80_20` (chia ngẫu nhiên → thông tin chuoi ít bị mất do mốc thời gian), khoảng cách hẹp lại hoặc đảo trên `temporal_global` (bài [03] chính là báo hiệu chia tập làm thay đổi xếp hạng).""")
    ,
    code("""def latest_summary(name):
    found = sorted((project_root / 'runs').glob(f'*/outputs/{name}'), key=lambda p: p.stat().st_mtime, reverse=True)
    return json.loads(found[0].read_text(encoding='utf-8')) if found else None

pop_summary = latest_summary('mostpopular_summary.json')
als_summary = latest_summary('als_summary.json')
rnd_summary = latest_summary('random_summary.json')
knn_summary = latest_summary('itemknn_summary.json')

header = f\"{'split':<18}{'sas':>8}{'knn':>8}{'als':>8}{'pop':>8}{'rnd':>8}{'sas/rnd':>10}\"
print(header)
print('-' * len(header))
for strategy in SPLITS_TO_RUN:
    r = sasrec_by_split[strategy]
    def g(sm):
        return sm['results'][strategy]['ndcg10'] if sm and strategy in sm['results'] else None
    pop_v, als_v, rnd_v, knn_v = g(pop_summary), g(als_summary), g(rnd_summary), g(knn_summary)
    sr = r['ndcg10'] / rnd_v if rnd_v else float('inf')
    print(f\"{strategy:<18}{r['ndcg10']:>8.4f}{knn_v or 0:>8.4f}{als_v or 0:>8.4f}{pop_v or 0:>8.4f}{rnd_v or 0:>8.4f}{sr:>10.1f}x\")

run.log('COMPARISON_SNAPSHOT', results={s: sasrec_by_split[s]['ndcg10'] for s in SPLITS_TO_RUN})
run.checkpoint('sanity_read', 'PASS', checks={'sasrec_above_random': all(
    sasrec_by_split[s]['ndcg10'] > (rnd_summary['results'][s]['ndcg10'] if rnd_summary else 0)
    for s in SPLITS_TO_RUN
) if rnd_summary else 'random not run'})""")
    ,
    md("""## 4. Lưu artifact và per-user NDCG

`peruser_ndcg_sasrec_{split}.npz` để notebook 12 chạy kiểm định cặp (Wilcoxon + 95% CI + rank-biserial *r*) SASRec vs từng baseline còn lại.""")
    ,
    code("""outputs_dir = run.run_dir / 'outputs'
outputs_dir.mkdir(parents=True, exist_ok=True)

saved = {}
for strategy in SPLITS_TO_RUN:
    model_path = outputs_dir / f'sasrec_{strategy}.json'
    model_path.write_text(
        json.dumps(sasrec_by_split[strategy], ensure_ascii=False, indent=2, default=str),
        encoding='utf-8',
    )

    per_user = peruser_by_split[strategy]
    users_array = np.array([u for u, _ in per_user], dtype=np.int64)
    scores_array = np.array([s for _, s in per_user], dtype=np.float32)
    npz_path = outputs_dir / f'peruser_ndcg_sasrec_{strategy}.npz'
    np.savez_compressed(npz_path, userId=users_array, ndcg=scores_array)

    saved[strategy] = {
        'json': str(model_path),
        'npz': str(npz_path),
        'users': int(users_array.size),
        'mean': float(scores_array.mean()) if scores_array.size else 0.0,
    }
    print(f'{strategy:<18}json={model_path.stat().st_size:>8,}B  npz users={users_array.size:,}  mean={saved[strategy][\"mean\"]:.4f}')

summary = {
    'protocol_id': spark_utils.PROTOCOL_ID,
    'model': 'SASRec_CE',
    'params': SASREC_CFG,
    'registered_baseline': 'SASRec ket hop cross-entropy (SOTA) — docs/About/Reseach_Method_Submission.md',
    'fit_scope': 'FULL 162,541 users',
    'tuning_budget': 0,
    'k': spark_utils.TOP_K,
    'relevance_threshold': spark_utils.RELEVANCE_THRESHOLD,
    'seed': spark_utils.DEFAULT_SEED,
    'val_fraction_users': VAL_FRACTION,
    'hardware': {
        'device': str(device),
        'used_for_this_model': 'GPU' if cuda_ok else 'CPU',
        'note': '4 baseline con lai (Random, MostPopular, ALS, ItemKNN) chay Spark local[4] CPU — KHONG so sanh runtime',
        'spark': {'version': spark.version, 'master': spark.sparkContext.master, 'driver_memory': '6g'},
        'sasrec_cuda': sasrec.cuda_report(torch),
    },
    'training': train_histories,
    'results': sasrec_by_split,
    'artifacts': saved,
}
summary_path = outputs_dir / 'sasrec_summary.json'
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
        'model': 'SASRec_CE',
        'splits': SPLITS_TO_RUN,
        'ndcg': {s: sasrec_by_split[s]['ndcg10'] for s in SPLITS_TO_RUN},
        'hardware': summary['hardware']['used_for_this_model'],
        'summary': str(summary_path),
    },
)
spark_utils.stop_spark(spark)
print('L13 COMPLETE. Next: chay lai 09_compare_and_reversal (5 model) va 12_paired_tests (them cap SASRec).')""")
    ,
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
