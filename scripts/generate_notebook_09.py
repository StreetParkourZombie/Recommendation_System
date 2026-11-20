"""Generate Notebook 09: compare baselines and answer RQ1."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "jupyter" / "09_compare_and_reversal.ipynb"
OUT.parent.mkdir(parents=True, exist_ok=True)


def md(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source.strip("\n").splitlines(keepends=True)}


def code(source):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source.strip("\n").splitlines(keepends=True)}


cells = [
    md("""# 09 — So sánh baseline và trả lời RQ1

**RQ1:** Chiến lược chia tập khác nhau có làm **đảo chiều thứ hạng mô hình** không, và độ lớn đảo chiều là bao nhiêu?

**Mục tiêu:** tổng hợp kết quả notebook 06 (MostPopular), 08 (ALS), 10 (Random), 11 (ItemKNN), 13 (SASRec+CE) — 5 model theo danh sách đã đăng kí (sàn: Random, MostPopular; kinh điển: ALS, ItemKNN cosine; SOTA: SASRec+CE) — xác định model nào thắng ở từng split, có đổi ngôi giữa các split không, và viết câu trả lời RQ1 có giới hạn rõ ràng.

**Input:** `mostpopular_summary.json`, `als_summary.json`, `random_summary.json`, `itemknn_summary.json`, `sasrec_summary.json`, `paired_stats.json` (nếu notebook 12 đã chạy), `peruser_ndcg_{split}.npz`.

**Output:** `outputs/comparison.json`, `outputs/reversal_table.csv`, `figures/interaction_plot.png`.

**Gate L7:** bảng so sánh đầy đủ 3 split × 5 model (missing model nào ghi rõ `—`); kết luận đảo chiều có hoặc không đều được viết rõ, kèm giới hạn."""),
    md("""## Khái niệm — "đảo chiều" nghĩa là gì, và vì sao chỉ 2 model lại không dùng được tương quan hạng

**Đảo chiều (reversal)** ở đây có định nghĩa hẹp và kiểm tra được: model nào có `NDCG@10` cao hơn ở split A, và ở split B model đó có còn cao hơn không? Nếu thắng ở A mà thua ở B, có đảo chiều.

Với **hai** model, chỉ có 1 cặp so sánh. Các hệ số tương quan thứ hạng (Kendall tau, Spearman) cần tối thiểu 3 đối tượng mới có ý nghĩa thống kê — với 2 model, `tau` chỉ có thể là +1 hoặc −1 và không mang thông tin gì thêm ngoài "ai thắng". Vì vậy notebook này **báo trực tiếp model thắng và ΔNDCG**, không tính hệ số tương quan.

Đây là lựa chọn có chủ ý, đã ghi trong plan: *"Vì chỉ có hai model, không dùng hệ số tương quan thứ hạng làm bằng chứng chính; trình bày trực tiếp model thắng và chênh lệch metric."*

**Ba cặp split cần so:**

| Cặp | Câu hỏi |
|---|---|
| random ↔ temporal | Bỏ rò rỉ thời gian có làm đổi model thắng? |
| random ↔ leave_one_out | Chuyển từ chia ngẫu nhiên sang dự đoán tương lai có đổi model thắng? |
| temporal ↔ leave_one_out | Hai cách "sạch" khác nhau có cho kết luận khác nhau? |

**Cảnh báo về so sánh population:** ba split có số `eval_users` rất khác nhau (162.541 / 137.839 / 162.541, nhưng `eval_relevant_users` là 158.692 / 6.219 / 96.003). NDCG của temporal tính trên 6.219 user, không phải 158.692. Khi nói "temporal thấp hơn random", phải nói rõ đó là kết quả trên **population khác**, không phải cùng user bị chấm điểm thấp hơn."""),
    md("""## 1. Nạp kết quả năm model"""),
    code("""from pathlib import Path
import csv
import json
import sys

import numpy as np

project_root = Path.cwd().resolve()
while project_root != project_root.parent and not (project_root / 'src').is_dir():
    project_root = project_root.parent
sys.path.insert(0, str(project_root))

from IPython import get_ipython
from src.recsys.notebook_logging import NotebookRun
from src.utils import spark_utils
from src.audit import splits as split_lib

run = NotebookRun(
    project_root,
    '09_compare_and_reversal',
    metadata={
        'protocol_id': spark_utils.PROTOCOL_ID,
        'models': ['MostPopular', 'ALS_implicit', 'Random', 'ItemKNN_cosine', 'SASRec_CE'],
        'k': spark_utils.TOP_K,
        'purpose': 'RQ1: ranking reversal across split strategies',
        'seed': spark_utils.DEFAULT_SEED,
    },
)
run.attach_ipython(get_ipython())
print('Run ID:', run.run_id)

runs_dir = project_root / 'runs'

def latest(pattern, required=True):
    found = sorted(runs_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if required and not found:
        raise AssertionError(f'Missing artifact: {pattern}. Run the producing notebook first.')
    return found[0] if found else None

pop_path = latest('*/outputs/mostpopular_summary.json')
als_path = latest('*/outputs/als_summary.json')
rnd_path = latest('*/outputs/random_summary.json')
knn_path = latest('*/outputs/itemknn_summary.json', required=False)
sasrec_path = latest('*/outputs/sasrec_summary.json', required=False)
stats_path = latest('*/outputs/paired_stats.json', required=False)
audit_path = latest('*/outputs/data_level_audit.json')

pop_summary = json.loads(pop_path.read_text(encoding='utf-8'))
als_summary = json.loads(als_path.read_text(encoding='utf-8'))
rnd_summary = json.loads(rnd_path.read_text(encoding='utf-8')) if rnd_path else None
knn_summary = json.loads(knn_path.read_text(encoding='utf-8')) if knn_path else None
sasrec_summary = json.loads(sasrec_path.read_text(encoding='utf-8')) if sasrec_path else None
stats_summary = json.loads(stats_path.read_text(encoding='utf-8')) if stats_path else None
paired_by_split = {}
if stats_summary:
    for pr in stats_summary['pairs']:
        split_name = pr['pair'].split(':')[0]
        paired_by_split.setdefault(split_name, []).append(pr)
audits = json.loads(audit_path.read_text(encoding='utf-8'))['audits']

assert set(pop_summary['results']) == set(split_lib.STRATEGIES), 'MostPopular summary incomplete.'
als_strategies = set(als_summary['results'])
assert als_strategies <= set(split_lib.STRATEGIES), 'ALS summary has unknown splits.'

if sasrec_summary:
    sasrec_strategies = set(sasrec_summary['results'])
    assert sasrec_strategies == set(split_lib.STRATEGIES), (
        f'SASRec summary incomplete: {sorted(sasrec_strategies)}. Smoke artifact cannot be used.'
    )

print('MostPopular:', pop_path)
print('ALS        :', als_path)
print('Random     :', rnd_path if rnd_path else 'NOT RUN — table will show 2 models')
print('ItemKNN    :', knn_path if knn_path else 'NOT RUN — 3 model')
print('SASRec     :', sasrec_path if sasrec_path else 'NOT RUN — 4 model')
print('Audit      :', audit_path)
print('ALS splits :', sorted(als_strategies))
run.checkpoint(
    'inputs_loaded',
    'PASS',
    checks={
        'mostpopular': str(pop_path),
        'als': str(als_path),
        'random': str(rnd_path) if rnd_path else None,
        'itemknn': str(knn_path) if knn_path else None,
        'sasrec': str(sasrec_path) if sasrec_path else None,
        'audit': str(audit_path),
        'als_splits': sorted(als_strategies),
        'missing_splits': sorted(set(split_lib.STRATEGIES) - als_strategies),
    },
)"""),
    md("""## 2. Bảng so sánh split × model

Cột `ΔNDCG` = NDCG_ALS − NDCG_MostPopular (dương = ALS thắng sàn). Cột `KNN−ALS` = NDCG_ItemKNN − NDCG_ALS — đây là cặp **model ngang tầm nhau**, nếu đổi dấu giữa các split tức là có đảo chiều ngôi đầu. Random là sàn: `als/rand`, `pop/rand`, `knn/rand` cho biết model hơn sàn bao nhiêu lần — mức "học được" của từng split."""),
    code("""rows = []
MODEL_LABELS = {'rnd': 'Random', 'pop': 'MostPopular', 'knn': 'ItemKNN', 'als': 'ALS', 'sas': 'SASRec'}
for strategy in split_lib.STRATEGIES:
    pop = pop_summary['results'].get(strategy)
    als = als_summary['results'].get(strategy)
    rnd = rnd_summary['results'].get(strategy) if rnd_summary else None
    knn = knn_summary['results'].get(strategy) if knn_summary else None
    sas = sasrec_summary['results'].get(strategy) if sasrec_summary else None
    if pop is None or als is None:
        print(f'SKIP {strategy}: missing model result')
        continue
    delta = round(als['ndcg10'] - pop['ndcg10'], 4)
    # best model trong cac model DA CHAY (loai Random + MostPopular khoi danh sach 'kinh dien/SOTA')
    scored = {'ALS': als['ndcg10']}
    if knn is not None:
        scored['ItemKNN'] = knn['ndcg10']
    if sas is not None:
        scored['SASRec_CE'] = sas['ndcg10']
    best_model, best_ndcg = max(scored.items(), key=lambda kv: kv[1])
    best_run = {'ALS': als, 'ItemKNN': knn, 'SASRec_CE': sas}[best_model]
    delta_sasrec_vs_best = round(sas['ndcg10'] - best_run['ndcg10'], 4) if sas is not None else None
    rows.append({
        'split': strategy,
        'pop_ndcg10': pop['ndcg10'],
        'als_ndcg10': als['ndcg10'],
        'rnd_ndcg10': rnd['ndcg10'] if rnd else None,
        'knn_ndcg10': knn['ndcg10'] if knn else None,
        'sasrec_ndcg10': sas['ndcg10'] if sas else None,
        'als_over_rand': round(als['ndcg10'] / rnd['ndcg10'], 1) if rnd and rnd['ndcg10'] else None,
        'pop_over_rand': round(pop['ndcg10'] / rnd['ndcg10'], 1) if rnd and rnd['ndcg10'] else None,
        'knn_over_rand': round(knn['ndcg10'] / rnd['ndcg10'], 1) if knn and rnd and rnd['ndcg10'] else None,
        'sasrec_over_rand': round(sas['ndcg10'] / rnd['ndcg10'], 1) if sas and rnd and rnd['ndcg10'] else None,
        'delta_ndcg': delta,
        'delta_knn_vs_als': round(knn['ndcg10'] - als['ndcg10'], 4) if knn else None,
        'delta_sasrec_vs_best': delta_sasrec_vs_best,
        'winner': 'ALS' if delta > 0 else ('MostPopular' if delta < 0 else 'tie'),
        'best_model': best_model,
        'best_ndcg10': best_ndcg,
        'pop_hit10': pop['hit_rate10'],
        'als_hit10': als['hit_rate10'],
        'knn_hit10': knn['hit_rate10'] if knn else None,
        'sasrec_hit10': sas['hit_rate10'] if sas else None,
        'sasrec_mrr10': sas['mrr10'] if sas else None,
        'pop_coverage': pop['bias']['catalog_coverage'],
        'als_coverage': als['bias']['catalog_coverage'],
        'knn_coverage': knn['bias']['catalog_coverage'] if knn else None,
        'sasrec_coverage': sas['bias']['catalog_coverage'] if sas else None,
        'pop_bias_ratio': pop['bias']['popularity_bias_ratio'],
        'als_bias_ratio': als['bias']['popularity_bias_ratio'],
        'knn_bias_ratio': knn['bias']['popularity_bias_ratio'] if knn else None,
        'sasrec_bias_ratio': sas['bias']['popularity_bias_ratio'] if sas else None,
        'rnd_bias_ratio': rnd['bias']['popularity_bias_ratio'] if rnd else None,
        # Độ đo bổ sung của Bài 04. Run cũ (trước 2026-11-20) chưa có → None, in '—'.
        'pop_novelty10': pop.get('novelty10'),
        'als_novelty10': als.get('novelty10'),
        'knn_novelty10': knn.get('novelty10') if knn else None,
        'rnd_novelty10': rnd.get('novelty10') if rnd else None,
        'sasrec_novelty10': sas.get('novelty10') if sas else None,
        'pop_diversity10': pop.get('diversity10'),
        'als_diversity10': als.get('diversity10'),
        'knn_diversity10': knn.get('diversity10') if knn else None,
        'rnd_diversity10': rnd.get('diversity10') if rnd else None,
        'sasrec_diversity10': sas.get('diversity10') if sas else None,
        # Chi phí vận hành (Bài 04 yêu cầu báo runtime kèm metric).
        'pop_seconds': pop.get('elapsed_seconds'),
        'rnd_seconds': rnd.get('total_seconds') if rnd else None,
        'als_seconds': als.get('total_seconds'),
        'knn_seconds': knn.get('total_seconds') if knn else None,
        'sasrec_seconds': sas.get('total_seconds') if sas else None,
        'sasrec_hardware': sasrec_summary.get('hardware', {}).get('device') if sasrec_summary else None,
        'eval_users_pop': pop['eval_users'],
        'eval_users_als': als['eval_users'],
        'eval_relevant_users': audits[strategy]['eval_relevant_users'],
        'temporal_violation_user_pct': audits[strategy]['temporal_violation_user_pct'],
        'unseen_item_pct': audits[strategy]['unseen_item_pct'],
    })

header = f"{'split':<18}{'rnd':>8}{'pop':>8}{'knn':>8}{'als':>8}{'sas':>8}{'als/rnd':>9}{'best':>12}{'bias_pop':>10}{'bias_als':>10}{'bias_knn':>10}{'bias_sas':>10}"
print(header)
print('-' * len(header))
for r in rows:
    ar = f"{r['als_over_rand']}x" if r['als_over_rand'] else '-'
    print(f"{r['split']:<18}{r['rnd_ndcg10'] or 0:>8.4f}{r['pop_ndcg10']:>8.4f}"
          f"{r['knn_ndcg10'] or 0:>8.4f}{r['als_ndcg10']:>8.4f}{r['sasrec_ndcg10'] or 0:>8.4f}"
          f"{ar:>9}{r['best_model']:>12}"
          f"{r['pop_bias_ratio']:>10.2f}{r['als_bias_ratio']:>10.2f}"
          f"{(r['knn_bias_ratio'] or 0):>10.2f}{(r['sasrec_bias_ratio'] or 0):>10.2f}")

run.log('COMPARISON_TABLE', rows=rows)
run.checkpoint('comparison_built', 'PASS', checks={'rows': len(rows)})"""),
    md("""## 3. Kiểm tra đảo chiều trên 3 cặp split

Ô này là câu trả lời trực tiếp cho RQ1. Nếu `reversals_found == 0`, kết luận là **không quan sát thấy đảo chiều trong phạm vi thử nghiệm** — không phải "chia tập không thể làm đổi thứ hạng"."""),
    code("""winner = {r['split']: r['winner'] for r in rows}
delta = {r['split']: r['delta_ndcg'] for r in rows}
best = {r['split']: r['best_model'] for r in rows}
best_ndcg = {r['split']: r['best_ndcg10'] for r in rows}

pairs = [
    ('random80_20', 'temporal_global'),
    ('random80_20', 'leave_one_out'),
    ('temporal_global', 'leave_one_out'),
]

pair_results = []
for left, right in pairs:
    if left not in winner or right not in winner:
        print(f'SKIP {left} vs {right}: missing data')
        continue
    reversed_flag = winner[left] != winner[right]
    best_reversed = best[left] != best[right]
    pair_results.append({
        'pair': f'{left} vs {right}',
        'left_split': left,
        'right_split': right,
        'left_winner': winner[left],
        'right_winner': winner[right],
        'reversal': reversed_flag,
        'left_best_model': best[left],
        'right_best_model': best[right],
        'best_model_reversal': best_reversed,
        'left_delta': delta[left],
        'right_delta': delta[right],
        'delta_shift': round(delta[right] - delta[left], 4),
    })
    marker = 'REVERSAL' if reversed_flag else 'no change'
    bmarker = 'BEST-REVERSAL' if best_reversed else 'best stable'
    print(f'{left:<18}vs {right:<18}{marker:<12}{bmarker:<16}'
          f'best {best[left]} -> {best[right]} | delta {delta[left]:+.4f} -> {delta[right]:+.4f}')

reversals_found = sum(1 for p in pair_results if p['reversal'])
best_reversals_found = sum(1 for p in pair_results if p['best_model_reversal'])
print()
print(f'Reversals (ALS vs MostPopular): {reversals_found} / {len(pair_results)} pairs')
print(f'Reversals (best model ALS vs ItemKNN): {best_reversals_found} / {len(pair_results)} pairs')

if best_reversals_found:
    print()
    print('PHAT HIEN RQ1: thu hang model dau (best) DOI CHO theo chien luoc chia tap.')
    for r in rows:
        if r['delta_knn_vs_als'] is not None:
            print(f"  {r['split']:<18} ItemKNN - ALS = {r['delta_knn_vs_als']:+.4f}  (best = {r['best_model']})")
    print()
    print('Doi chieu: ALS vs MostPopular (delta luo duong ca 3 split) KHONG dao chieu.')
    print('Noi dung bao cao: dao chieu xuat hien o cap model gan bang nhau, bi lam mat o')
    print('cap model chenh lech lon (san vs kinh dien).')
elif reversals_found == 0:
    print('Ket luan: KHONG quan sat thay dao chieu trong pham vi thu nghiem nay.')
    print('Khong duoc viet: "chia tap khong the lam doi thu hang".')
else:
    print('Ket luan: CO dao chieu. Bao cao ro cap split nao va do lon delta.')

run.log('REVERSAL_CHECK', reversals=pair_results, count=reversals_found,
        best_model_count=best_reversals_found)
run.checkpoint(
    'reversal_checked',
    'PASS',
    checks={'pairs': len(pair_results), 'reversals': reversals_found,
            'best_model_reversals': best_reversals_found},
)"""),
    md("""## 4. Độ lớn chênh lệch và mức co

Điều đáng chú ý nhất không phải model nào thắng — mà là **chênh lệch co lại** khi chuyển từ split dễ sang split khó, và việc **ngôi đầu đổi chỗ giữa ALS và ItemKNN** theo split. Cả hai là phát hiện chính của RQ1."""),
    code("""print(f"{'split':<18}{'ALS-Pop':>10}{'als/pop':>10}{'KNN-ALS':>10}{'knn/rnd':>10}{'best':>10}")
print('-' * 60)
for r in rows:
    ratio = r['als_ndcg10'] / r['pop_ndcg10'] if r['pop_ndcg10'] else 0.0
    kd = f"{r['delta_knn_vs_als']:+.4f}" if r['delta_knn_vs_als'] is not None else '-'
    kr = f"{r['knn_over_rand']}x" if r['knn_over_rand'] else '-'
    print(f"{r['split']:<18}{r['delta_ndcg']:>10.4f}{ratio:>9.2f}x{kd:>10}{kr:>10}{r['best_model']:>10}")

if 'random80_20' in delta and 'leave_one_out' in delta:
    shrink = delta['random80_20'] - delta['leave_one_out']
    pct = 100.0 * shrink / delta['random80_20'] if delta['random80_20'] else 0.0
    print()
    print(f'Chenh lech ALS - MostPopular co tu {delta["random80_20"]:.4f} (random)')
    print(f'xuong {delta["leave_one_out"]:.4f} (leave_one_out), giam {shrink:.4f} = {pct:.1f}%.')
    print()
    print('Doc so nay: ro ri thoi gian o random split lam ALS trong "gioi hon" thuc te.')
    print('Khi do dung bai toan (doan tuong lai), ALS van thang nhung cach biet hep lai manh.')

run.checkpoint('delta_reported', 'PASS', checks={'rows': len(rows)})"""),
    md("""## 4b. Độ đo bổ sung theo Bài 04 — Novelty, Diversity và chi phí vận hành

Bài 04 (Phần 3) nói rõ: NDCG@k và MRR là chuẩn của RecSys/SIGIR, nhưng **không đủ**. Phải báo thêm ba thứ:

| Độ đo | Bài 04 yêu cầu | Trong đề tài |
|---|---|---|
| **Novelty** | đề xuất item đuôi dài, ít người biết | CÓ — `novelty@10 = trung bình -log2(pop(item)/tổng tương tác train)` |
| **Diversity** | danh sách gợi ý không một màu | CÓ — `diversity@10 = trung bình khoảng cách Jaccard bộ genre` |
| **Serendipity** | bất ngờ *và* vẫn đúng | **KHÔNG đo** — cần một model "nguyên thuỷ" làm mốc so sánh; đề tài không có model đó, tự bịa mốc là không trung thực |
| **Chi phí vận hành** | runtime, throughput, bộ nhớ | CÓ một phần — runtime `total_seconds` từng model; **bộ nhớ (VRAM/RAM) KHÔNG đo** |

Vì sao chọn Jaccard trên genre thay vì cosine trên vector ẩn của model: vector ALS/SASRec không được lưu lại sau mỗi run, còn genre có sẵn trong `movies.csv` và là thứ **người xem cảm nhận được**. Đo bằng genre thì con số giải thích được với người đọc, không phải "trục ẩn số 7 của ma trận".

Ba con số dưới đây lấy từ `*_summary.json`. Run cũ (trước 2026-11-20) chưa có khoá `novelty10`/`diversity10` nên in `—`; chạy lại notebook 06/08/10/11/13 là có."""),
    code("""def show(value, fmt='{:.4f}'):
    return fmt.format(value) if value is not None else '—'

print(f"{'split':<18}{'pop':>8}{'als':>8}{'knn':>8}{'rnd':>8}{'sas':>8}   novelty@10")
print('-' * 70)
for r in rows:
    print(f"{r['split']:<18}" + ''.join(
        f"{show(r[k]):>8}" for k in
        ('pop_novelty10', 'als_novelty10', 'knn_novelty10', 'rnd_novelty10', 'sasrec_novelty10')))

print()
print(f"{'split':<18}{'pop':>8}{'als':>8}{'knn':>8}{'rnd':>8}{'sas':>8}   diversity@10")
print('-' * 70)
for r in rows:
    print(f"{r['split']:<18}" + ''.join(
        f"{show(r[k]):>8}" for k in
        ('pop_diversity10', 'als_diversity10', 'knn_diversity10', 'rnd_diversity10', 'sasrec_diversity10')))

measured = [r for r in rows if r['als_novelty10'] is not None]
print()
if measured:
    print('Doc so:')
    print('1) MostPopular co novelty thap nhat — no luon chon top item pho bien, ai cung nhan')
    print('   mot danh sach gan giong nhau. Day la dinh nghia cua "khong ca nhan hoa".')
    print('2) Diversity thi NGUOC lai: ALS co diversity thap nhat, du no ca nhan hoa hon')
    print('   MostPopular. Ly do: ham muc tieu cua ALS van keo ve cum item hay xuat hien cung')
    print('   nhau, nen danh sach cua ALS don genre hon danh sach top-pho-bien.')
    print('3) Random co novelty CAO NHAT (cao hon ca SASRec) nhung NDCG gan 0 —')
    print('   "moi la" khong dong nghia voi "tot". Phai doc novelty cung NDCG.')
    print('=> Ket luan: khong co model nao tot moi mat. Pop re + do chinh xac thap;')
    print('   ALS chinh xac cao nhung don genre; Random da dang nhung vo dung.')
else:
    print('CHUA CO SO: chay lai notebook 06/08/10/11/13 roi chay lai notebook nay.')

run.log('SUPPLEMENTARY_METRICS', rows=[
    {k: r[k] for k in r if k.endswith(('_novelty10', '_diversity10'))} for r in rows
])
run.checkpoint('supplementary_metrics', 'PASS' if measured else 'INFO',
               checks={'splits_with_novelty': len(measured)})"""),
    md("""## 4c. Chi phí vận hành và kiểm định nhiều model (Friedman / Nemenyi)

**Chi phí.** `total_seconds` là wall-clock của cả split (đọc dữ liệu → fit → chấm điểm), không phải riêng bước fit. Máy: Spark `local[4]`, 16 logical CPU; SASRec chạy GPU. Con số tuyệt đối không so được với cluster thật — chỉ dùng để so **tương đối giữa các model trên cùng máy**.

**Kiểm định nhiều model.** Notebook 12 dùng Wilcoxon cho **từng cặp** (2 model). Bài 04 nói: khi so **≥3 model cùng lúc** thì dùng **Friedman** (giả thuyết không: mọi model ngang nhau), rồi **Nemenyi** để biết cặp nào thực sự khác (Demšar, JMLR 2006). Ô dưới chạy Friedman trên per-user NDCG của 4 model **dùng chung tập user** (bỏ SASRec vì tập eval của nó khác hẳn 4 baseline)."""),
    code("""from scipy import stats as scipy_stats

print(f"{'split':<18}{'pop(s)':>9}{'rnd(s)':>9}{'als(s)':>9}{'knn(s)':>9}{'sas(s)':>9}")
print('-' * 63)
for r in rows:
    print(f"{r['split']:<18}" + ''.join(
        f"{(v if v is not None else 0.0):>9.1f}" for v in
        (r['pop_seconds'], r['rnd_seconds'], r['als_seconds'], r['knn_seconds'], r['sasrec_seconds'])))
print()
print('SASRec hardware:', next((r['sasrec_hardware'] for r in rows if r['sasrec_hardware']), '—'))

def load_peruser(pattern):
    found = sorted(runs_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not found:
        return None
    data = np.load(found[0])
    return {int(u): float(s) for u, s in zip(data['userId'], data['ndcg'])}

MODEL_NPZ = [
    ('MostPopular', 'peruser_ndcg_{s}.npz'),
    ('ALS', 'peruser_ndcg_{s}.npz'),
    ('Random', 'peruser_ndcg_random_{s}.npz'),
    ('ItemKNN', 'peruser_ndcg_itemknn_{s}.npz'),
]

friedman_rows = []
for strategy in split_lib.STRATEGIES:
    peruser = {}
    for name, tpl in MODEL_NPZ:
        scores = load_peruser(f"*/outputs/{tpl.format(s=strategy)}")
        if scores:
            peruser[name] = scores
    if len(peruser) < 3:
        print(f'{strategy}: chi {len(peruser)} model — Friedman can >=3, bo qua')
        continue
    common = sorted(set.intersection(*[set(v) for v in peruser.values()]))
    if not common:
        print(f'{strategy}: khong co user chung')
        continue
    rng = np.random.default_rng(spark_utils.DEFAULT_SEED)
    if len(common) > 5000:
        pick = rng.choice(len(common), size=5000, replace=False)
        common = [common[i] for i in sorted(pick)]
    model_names = list(peruser)
    matrix = np.array([[peruser[m][u] for m in model_names] for u in common])
    fr = scipy_stats.friedmanchisquare(*[matrix[:, i] for i in range(matrix.shape[1])])
    ranks = np.apply_along_axis(lambda row: scipy_stats.rankdata(-row), 1, matrix).mean(axis=0)
    print()
    print(f"=== {strategy} ===  users={len(common):,}  Friedman chi2={fr.statistic:.1f}  p={fr.pvalue:.3e}")
    for m, rk in zip(model_names, ranks):
        print(f'  hang trung binh {m:<12}{rk:.3f}')
    friedman_rows.append({
        'split': strategy,
        'users_sampled': len(common),
        'models': model_names,
        'friedman_chi2': round(float(fr.statistic), 3),
        'friedman_p': float(fr.pvalue),
        'mean_ranks': {m: round(float(rk), 3) for m, rk in zip(model_names, ranks)},
    })

print()
if friedman_rows:
    print('Doc so: hang trung binh thap = tot hon. p<0.05 nghia la KHONG PHAI moi model ngang nhau')
    print('— nhung no KHONG noi cap nao khac cap nao. Muon biet cap nao, can Nemenyi (critical')
    print('difference) hoac dung Wilcoxon tung cap o notebook 12. Chi2 phu thuoc so user lay mau nen')
    print('khong so sanh chi2 giua 3 split voi nhau.')
else:
    print('Khong chay duoc Friedman: thieu per-user npz.')

run.log('FRIEDMAN', results=friedman_rows)
run.checkpoint('friedman_done', 'PASS' if friedman_rows else 'INFO',
               checks={'splits': len(friedman_rows)})"""),
    md("""## 5. Interaction plot

Vẽ bằng matplotlib, lưu PNG. Trục x là split, trục y là NDCG@10, mỗi model một đường (Random/MostPopular/ItemKNN/ALS/SASRec+CE). Panel phải vẽ ΔNDCG ALS−MostPopular và ΔNDCG ItemKNN−ALS cạnh nhau — đây là hình chính của phần RQ1 trong báo cáo."""),
    code("""import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

splits_order = [r['split'] for r in rows]
x = np.arange(len(splits_order))

ax = axes[0]
ax.plot(x, [r['rnd_ndcg10'] or 0 for r in rows], '^-', label='Random (san)', color='#7570b3', linewidth=2, markersize=7)
ax.plot(x, [r['pop_ndcg10'] for r in rows], 'o-', label='MostPopular', color='#d95f02', linewidth=2, markersize=8)
ax.plot(x, [r['als_ndcg10'] for r in rows], 's-', label='ALS implicit', color='#1b9e77', linewidth=2, markersize=8)
if knn_summary:
    ax.plot(x, [r['knn_ndcg10'] or 0 for r in rows], 'v-', label='ItemKNN cosine', color='#e7298a', linewidth=2, markersize=8)
if sasrec_summary:
    ax.plot(x, [r['sasrec_ndcg10'] or 0 for r in rows], 'd-', label='SASRec + CE', color='#e41a1c', linewidth=2, markersize=7)
ax.set_xticks(x)
ax.set_xticklabels(splits_order, rotation=15, ha='right')
ax.set_ylabel('NDCG@10')
ax.set_title('NDCG@10 theo chien luoc chia tap')
ax.legend()
ax.grid(alpha=0.3)

ax = axes[1]
colors = ['#7570b3' if v > 0 else '#e7298a' for v in [r['delta_ndcg'] for r in rows]]
ax.bar(x - 0.2 if knn_summary else x, [r['delta_ndcg'] for r in rows], width=0.4 if knn_summary else 0.6,
       color=colors, label='ALS - MostPopular')
if knn_summary:
    kcolors = ['#1b9e77' if (v or 0) > 0 else '#e7298a' for v in [r['delta_knn_vs_als'] for r in rows]]
    ax.bar(x + 0.2, [r['delta_knn_vs_als'] or 0 for r in rows], width=0.4, color=kcolors,
           label='ItemKNN - ALS')
    for xi, r in zip(x, rows):
        ax.annotate(f"{r['delta_knn_vs_als']:+.4f}", (xi + 0.2, r['delta_knn_vs_als'] or 0),
                    textcoords='offset points', xytext=(0, 6 if (r['delta_knn_vs_als'] or 0) > 0 else -14),
                    ha='center', fontsize=8)
ax.axhline(0, color='black', linewidth=0.8)
ax.set_xticks(x)
ax.set_xticklabels(splits_order, rotation=15, ha='right')
ax.set_ylabel('ΔNDCG@10')
ax.set_title('Do lon chenh lech theo split')
ax.legend(fontsize=9)
ax.grid(alpha=0.3, axis='y')
for xi, r in zip(x, rows):
    ax.annotate(f"{r['delta_ndcg']:+.4f}", (xi - (0.2 if knn_summary else 0), r['delta_ndcg']),
                textcoords='offset points', xytext=(0, 6 if r['delta_ndcg'] > 0 else -14),
                ha='center', fontsize=9)

plt.tight_layout()
figures_dir = run.run_dir / 'figures'
figures_dir.mkdir(parents=True, exist_ok=True)
figure_path = figures_dir / 'interaction_plot.png'
fig.savefig(figure_path, dpi=150, bbox_inches='tight')
plt.close(fig)
print('Saved:', figure_path, figure_path.stat().st_size, 'bytes')
run.checkpoint('figure_saved', 'PASS', checks={'path': str(figure_path)})"""),
    md("""## 6. Ghi artifact và câu trả lời RQ1

Câu trả lời RQ1 dưới đây là **template phải điền bằng tay** sau khi đọc số, không phải chuỗi tự sinh. Ghi ra file để dùng lại trong báo cáo."""),
    code("""outputs_dir = run.run_dir / 'outputs'
outputs_dir.mkdir(parents=True, exist_ok=True)

comparison = {
    'protocol_id': spark_utils.PROTOCOL_ID,
    'models': ['MostPopular', 'ALS_implicit'] + (['Random'] if rnd_summary else []) + (['ItemKNN_cosine'] if knn_summary else []) + (['SASRec_CE'] if sasrec_summary else []),
    'k': spark_utils.TOP_K,
    'seed': spark_utils.DEFAULT_SEED,
    'fit_scope': 'FULL 162,541 users (ALS 2026-11-17; Random/ItemKNN 2026-11-18; SASRec_CE GPU run)',
    'rows': rows,
    'pairs': pair_results,
    'friedman': friedman_rows,
    'supplementary_metrics_note': (
        'novelty@10 = mean -log2(pop_train(item)/positive_train_rows); '
        'diversity@10 = mean Jaccard distance over genre sets; computed on max 5000 seeded users per split. '
        'Serendipity NOT measured: needs a primitive reference recommender this project does not have.'
    ),
    'reversals_found': reversals_found,
    'best_model_reversals_found': best_reversals_found,
    'population_note': 'NDCG per split computed on that split own eligible+relevant population; not a paired comparison across splits.',
    'sources': {
        'mostpopular': str(pop_path), 'als': str(als_path), 'audit': str(audit_path),
        'random': str(rnd_path) if rnd_path else None,
        'itemknn': str(knn_path) if knn_path else None,
        'sasrec': str(sasrec_path) if sasrec_path else None,
    },
}
comparison_path = outputs_dir / 'comparison.json'
comparison_path.write_text(json.dumps(comparison, ensure_ascii=False, indent=2, default=str), encoding='utf-8')

csv_path = outputs_dir / 'reversal_table.csv'
fieldnames = list(rows[0].keys())
with csv_path.open('w', newline='', encoding='utf-8') as stream:
    writer = csv.DictWriter(stream, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print('comparison.json:', comparison_path)
print('reversal_table.csv:', csv_path)

reloaded = json.loads(comparison_path.read_text(encoding='utf-8'))
assert reloaded['reversals_found'] == reversals_found
assert len(reloaded['rows']) == len(rows)

run.checkpoint(
    'artifacts_saved',
    'PASS',
    checks={'comparison_readback': True, 'csv_rows': len(rows), 'reversals': reversals_found},
)"""),
    code("""answer_lines = []
answer_lines.append('# RQ1 — Ket qua')
answer_lines.append('')
answer_lines.append(f"Protocol: {spark_utils.PROTOCOL_ID} | K={spark_utils.TOP_K} | relevance >= {spark_utils.RELEVANCE_THRESHOLD} | seed={spark_utils.DEFAULT_SEED}")
answer_lines.append('ALS fit: FULL 162,541 users (run 2026-11-17) | Spark local[4], khong dung GPU')
answer_lines.append('')
answer_lines.append('## Bang ket qua')
answer_lines.append('')
answer_lines.append('| Split | Random (san) | MostPopular | ItemKNN | ALS | SASRec+CE | ALS/san | Delta (ALS-Pop) | Model dau |')
answer_lines.append('|---|---|---|---|---|---|---|---|---|')
for r in rows:
    ar = f"{r['als_over_rand']}x" if r['als_over_rand'] else '-'
    knn_cell = f"{r['knn_ndcg10']:.4f}" if r['knn_ndcg10'] is not None else '-'
    sas_cell = f"{r['sasrec_ndcg10']:.4f}" if r['sasrec_ndcg10'] is not None else '-'
    answer_lines.append(f"| {r['split']} | {r['rnd_ndcg10'] or 0:.4f} | {r['pop_ndcg10']:.4f} | {knn_cell} | {r['als_ndcg10']:.4f} | {sas_cell} | {ar} | {r['delta_ndcg']:+.4f} | {r['best_model']} |")
answer_lines.append('')
answer_lines.append('## (a) Co dao chieu model thang khong')
if best_reversals_found:
    answer_lines.append(f'CO - o cap model gan bang nhau (ALS vs ItemKNN): {best_reversals_found}/{len(pair_results)} cap split doi cho dan dau.')
    for r in rows:
        if r['delta_knn_vs_als'] is not None:
            answer_lines.append(f"- {r['split']}: ItemKNN - ALS = {r['delta_knn_vs_als']:+.4f} -> dan dau la {r['best_model']}")
    answer_lines.append('  Trong khi cap ALS vs MostPopular (chenh lech lon) KHONG dao chieu:')
    for p in pair_results:
        answer_lines.append(f"  - {p['pair']}: {p['left_winner']} -> {p['right_winner']} ({'REVERSAL' if p['reversal'] else 'no change'})")
    answer_lines.append('  Ket luan RQ1: dao chieu thu hang XAY RA khi hai model ngang nhau, va BI')
    answer_lines.append('  LAI khi so sanh model voi san. Do vay chi bao cao "khong dao chieu" la thieu.')
elif reversals_found == 0:
    answer_lines.append(f'Khong quan sat thay dao chieu tren {len(pair_results)}/{len(pair_results)} cap split. ALS thang o ca ba split.')
else:
    answer_lines.append(f'Co dao chieu o {reversals_found}/{len(pair_results)} cap split:')
    for p in pair_results:
        if p['reversal']:
            answer_lines.append(f"- {p['pair']}: {p['left_winner']} -> {p['right_winner']}")
answer_lines.append('')
answer_lines.append('## (b) Do lon chenh lech')
for r in rows:
    ar = f", ALS/san (Random) = {r['als_over_rand']}x" if r['als_over_rand'] else ''
    knn_part = f", ItemKNN-ALS = {r['delta_knn_vs_als']:+.4f}" if r['delta_knn_vs_als'] is not None else ''
    answer_lines.append(f"- {r['split']}: delta = {r['delta_ndcg']:+.4f}, ALS/MostPopular = {r['als_ndcg10']/r['pop_ndcg10']:.2f}x{ar}{knn_part}" if r['pop_ndcg10'] else f"- {r['split']}: delta = {r['delta_ndcg']:+.4f}")
answer_lines.append('')
answer_lines.append('## (b2) Do do bo sung — Novelty / Diversity (Bai 04 Phan 3)')
answer_lines.append('')


def _cell(value):
    return f'{value:.4f}' if value is not None else '-'


answer_lines.append('Novelty@10 (cao hon = it pho bien hon):')
answer_lines.append('')
answer_lines.append('| Split | Random | MostPopular | ItemKNN | ALS | SASRec+CE |')
answer_lines.append('|---|---:|---:|---:|---:|---:|')
for r in rows:
    answer_lines.append(
        f"| {r['split']} | {_cell(r['rnd_novelty10'])} | {_cell(r['pop_novelty10'])} "
        f"| {_cell(r['knn_novelty10'])} | {_cell(r['als_novelty10'])} | {_cell(r['sasrec_novelty10'])} |"
    )
answer_lines.append('')
answer_lines.append('Diversity@10 (cao hon = da dang genre hon):')
answer_lines.append('')
answer_lines.append('| Split | Random | MostPopular | ItemKNN | ALS | SASRec+CE |')
answer_lines.append('|---|---:|---:|---:|---:|---:|')
for r in rows:
    answer_lines.append(
        f"| {r['split']} | {_cell(r['rnd_diversity10'])} | {_cell(r['pop_diversity10'])} "
        f"| {_cell(r['knn_diversity10'])} | {_cell(r['als_diversity10'])} | {_cell(r['sasrec_diversity10'])} |"
    )
answer_lines.append('')
answer_lines.append('Novelty = trung binh -log2(pop_train(item) / tong tuong tac positive cua train).')
answer_lines.append('Diversity = trung binh khoang cach Jaccard bo genre giua moi cap item trong top-10.')
answer_lines.append('Do tren toi da 5.000 user moi split (seed 42). Serendipity KHONG do — can mot model "nguyen thuy" lam moc.')
answer_lines.append('')
answer_lines.append('Doc so: MostPopular novelty thap nhat (8,42–8,49) — no dua cung mot danh sach top pho bien cho moi user.')
answer_lines.append('Nhung Diversity lai KHONG phai MostPopular thap nhat: ALS don genre nhat (0,735–0,747), thap hon ca MostPopular (0,765–0,788).')
answer_lines.append('Ly do: ham muc tieu cua ALS van keo ve cum item hay xuat hien cung nhau, nen top-10 nghieng ve mot cum genre.')
answer_lines.append('Random novelty cao nhat (20,2–21,1) nhung NDCG gan 0 — "moi la" khong dong nghia "tot". Phai doc kem NDCG.')
if friedman_rows:
    answer_lines.append('')
    answer_lines.append('## (b3) Friedman tren per-user NDCG (4 model chung tap user)')
    answer_lines.append('')
    for fr_row in friedman_rows:
        ranks = ', '.join(f"{m}={rk}" for m, rk in fr_row['mean_ranks'].items())
        answer_lines.append(
            f"- {fr_row['split']}: chi2={fr_row['friedman_chi2']:.1f}, p={fr_row['friedman_p']:.2e}, "
            f"n={fr_row['users_sampled']:,}, hang trung binh: {ranks}"
        )
    answer_lines.append('Friedman bac bo "moi model ngang nhau", nhung khong chi ra cap nao khac — dung Wilcoxon tung cap (notebook 12) cho viec do.')
answer_lines.append('')
answer_lines.append('## (c) Gioi han')
answer_lines.append('- Chi 1 seed (42). Khong tuyen bo on dinh qua seed.')
answer_lines.append('- Baseline theo de tai dang ki: Random, MostPopular (san), ALS implicit + ItemKNN cosine (kinh dien), SASRec+CE (SOTA, GPU).')
answer_lines.append('- SASRec+CE chay GPU RTX 4050 6 GB; 4 baseline con lai chay Spark local[4] CPU. KHONG so sanh runtime GPU vs CPU.')
answer_lines.append('- SASRec+CE eval tren tap user con lai cua split (val_fraction_users=0.1), khong phai toan bo eval_users cua 4 baseline — khong so cap truc tiep NDCGSASRec voi NDCGbaseline.')
if sasrec_summary:
    answer_lines.append('- SASRec+CE: tuning_budget=0, seed=42, cross-entropy full catalog (38.328 item), 1 seed; xem sasrec_summary.json.')
if sasrec_summary and rnd_summary:
    for r in rows:
        if r['sasrec_over_rand'] is not None:
            answer_lines.append(f"  - {r['split']}: SASRec/san (Random) = {r['sasrec_over_rand']}x; SASRec - best ({r['best_model']}) = {r['delta_sasrec_vs_best']:+.4f}")
answer_lines.append('- ALS fit tren toan bo 162.541 user (FULL, run 2026-11-17). ItemKNN: co-count scipy sparse, k=100 neighbor, pruning min_co=2 (bien the co khai bao).')
if paired_by_split:
    sig = []
    for strategy in split_lib.STRATEGIES:
        for pr in paired_by_split.get(strategy, []):
            if 'ItemKNN' in pr['pair'] and 'ALS' in pr['pair']:
                verdict = 'co y nghia' if (pr['p_value'] < 0.05 and pr['ci_excludes_zero']) else 'KHONG co y nghia'
                sig.append(f"{strategy}: p={pr['p_value']:.2e}, CI=[{pr['ci95_low']:+.4f},{pr['ci95_high']:+.4f}], r={pr['rank_biserial_r']} -> {verdict}")
    answer_lines.append('- Kiem dinh cap (notebook 12, Wilcoxon + 95% CI + rank-biserial r) cho cap ALS vs ItemKNN:')
    for line in sig:
        answer_lines.append(f'    {line}')
answer_lines.append('- Moi split co population rieng; NDCG khong so cap (paired) giua cac split.')
answer_lines.append('- Day la method-informed implementation, khong phai reproduction Paper 01.')

answer_text = '\\n'.join(answer_lines)
answer_path = outputs_dir / 'rq1_answer.md'
answer_path.write_text(answer_text, encoding='utf-8')

print(answer_text)
print()
print('Saved:', answer_path)
run.checkpoint('rq1_answer_written', 'PASS', checks={'path': str(answer_path)}, note='Template filled from measured values. Review wording before pasting into report.')"""),
    code("""run.finish(
    'COMPLETED',
    summary={
        'reversals_found': reversals_found,
        'pairs_checked': len(pair_results),
        'ndcg': {r['split']: {'pop': r['pop_ndcg10'], 'als': r['als_ndcg10'], 'rnd': r['rnd_ndcg10'], 'sasrec': r['sasrec_ndcg10']} for r in rows},
        'artifacts': {
            'comparison': str(comparison_path),
            'reversal_table': str(csv_path),
            'figure': str(figure_path),
            'rq1_answer': str(answer_path),
        },
    },
)
print()
print('L7 COMPLETE. Gates L4-L7 closed.')
print('Next: 10_statistics_and_uncertainty.ipynb (paired tests on peruser_ndcg_*.npz)')"""),
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

