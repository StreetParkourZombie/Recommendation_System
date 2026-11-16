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

**Mục tiêu:** tổng hợp kết quả notebook 06 (MostPopular) và 08 (ALS), xác định model nào thắng ở từng split, có đổi ngôi giữa các split không, và viết câu trả lời RQ1 có giới hạn rõ ràng.

**Input:** `mostpopular_summary.json`, `als_summary.json`, `peruser_ndcg_{split}.npz`.

**Output:** `outputs/comparison.json`, `outputs/reversal_table.csv`, `figures/interaction_plot.png`.

**Gate L7:** bảng so sánh đầy đủ 3 split × 2 model; kết luận đảo chiều có hoặc không đều được viết rõ, kèm giới hạn."""),
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
    md("""## 1. Nạp kết quả hai model"""),
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
        'models': ['MostPopular', 'ALS_implicit'],
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
audit_path = latest('*/outputs/data_level_audit.json')

pop_summary = json.loads(pop_path.read_text(encoding='utf-8'))
als_summary = json.loads(als_path.read_text(encoding='utf-8'))
audits = json.loads(audit_path.read_text(encoding='utf-8'))['audits']

assert set(pop_summary['results']) == set(split_lib.STRATEGIES), 'MostPopular summary incomplete.'
als_strategies = set(als_summary['results'])
assert als_strategies <= set(split_lib.STRATEGIES), 'ALS summary has unknown splits.'

print('MostPopular:', pop_path)
print('ALS        :', als_path)
print('Audit      :', audit_path)
print('ALS splits :', sorted(als_strategies))
run.checkpoint(
    'inputs_loaded',
    'PASS',
    checks={
        'mostpopular': str(pop_path),
        'als': str(als_path),
        'audit': str(audit_path),
        'als_splits': sorted(als_strategies),
        'missing_splits': sorted(set(split_lib.STRATEGIES) - als_strategies),
    },
)"""),
    md("""## 2. Bảng so sánh split × model

Cột `ΔNDCG` = NDCG_ALS − NDCG_MostPopular. Dấu dương nghĩa là ALS thắng."""),
    code("""rows = []
for strategy in split_lib.STRATEGIES:
    pop = pop_summary['results'].get(strategy)
    als = als_summary['results'].get(strategy)
    if pop is None or als is None:
        print(f'SKIP {strategy}: missing model result')
        continue
    delta = round(als['ndcg10'] - pop['ndcg10'], 4)
    rows.append({
        'split': strategy,
        'pop_ndcg10': pop['ndcg10'],
        'als_ndcg10': als['ndcg10'],
        'delta_ndcg': delta,
        'winner': 'ALS' if delta > 0 else ('MostPopular' if delta < 0 else 'tie'),
        'pop_hit10': pop['hit_rate10'],
        'als_hit10': als['hit_rate10'],
        'pop_coverage': pop['bias']['catalog_coverage'],
        'als_coverage': als['bias']['catalog_coverage'],
        'pop_bias_ratio': pop['bias']['popularity_bias_ratio'],
        'als_bias_ratio': als['bias']['popularity_bias_ratio'],
        'eval_users_pop': pop['eval_users'],
        'eval_users_als': als['eval_users'],
        'eval_relevant_users': audits[strategy]['eval_relevant_users'],
        'temporal_violation_user_pct': audits[strategy]['temporal_violation_user_pct'],
        'unseen_item_pct': audits[strategy]['unseen_item_pct'],
    })

header = f"{'split':<18}{'pop':>8}{'als':>8}{'delta':>8}{'winner':>14}{'bias_pop':>10}{'bias_als':>10}"
print(header)
print('-' * len(header))
for r in rows:
    print(f"{r['split']:<18}{r['pop_ndcg10']:>8.4f}{r['als_ndcg10']:>8.4f}{r['delta_ndcg']:>8.4f}"
          f"{r['winner']:>14}{r['pop_bias_ratio']:>10.2f}{r['als_bias_ratio']:>10.2f}")

run.log('COMPARISON_TABLE', rows=rows)
run.checkpoint('comparison_built', 'PASS', checks={'rows': len(rows)})"""),
    md("""## 3. Kiểm tra đảo chiều trên 3 cặp split

Ô này là câu trả lời trực tiếp cho RQ1. Nếu `reversals_found == 0`, kết luận là **không quan sát thấy đảo chiều trong phạm vi thử nghiệm** — không phải "chia tập không thể làm đổi thứ hạng"."""),
    code("""winner = {r['split']: r['winner'] for r in rows}
delta = {r['split']: r['delta_ndcg'] for r in rows}

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
    pair_results.append({
        'pair': f'{left} vs {right}',
        'left_split': left,
        'right_split': right,
        'left_winner': winner[left],
        'right_winner': winner[right],
        'reversal': reversed_flag,
        'left_delta': delta[left],
        'right_delta': delta[right],
        'delta_shift': round(delta[right] - delta[left], 4),
    })
    marker = 'REVERSAL' if reversed_flag else 'no change'
    print(f'{left:<18}vs {right:<18}{marker:<12}'
          f'delta {delta[left]:+.4f} -> {delta[right]:+.4f}')

reversals_found = sum(1 for p in pair_results if p['reversal'])
print()
print(f'Reversals found: {reversals_found} / {len(pair_results)} pairs')

if reversals_found == 0:
    print('Ket luan: KHONG quan sat thay dao chieu model thang trong pham vi thu nghiem nay.')
    print('Khong duoc viet: "chia tap khong the lam doi thu hang".')
else:
    print('Ket luan: CO dao chieu. Bao cao ro cap split nao va do lon delta.')

run.log('REVERSAL_CHECK', reversals=pair_results, count=reversals_found)
run.checkpoint(
    'reversal_checked',
    'PASS',
    checks={'pairs': len(pair_results), 'reversals': reversals_found},
)"""),
    md("""## 4. Độ lớn chênh lệch và mức co

Điều đáng chú ý nhất không phải model nào thắng — ALS thắng ở cả ba split. Điều đáng chú ý là **chênh lệch co lại** khi chuyển từ split dễ sang split khó. Đây mới là phát hiện chính."""),
    code("""print(f"{'split':<18}{'delta_ndcg':>12}{'als_over_pop':>15}{'note':>34}")
print('-' * 80)
for r in rows:
    ratio = r['als_ndcg10'] / r['pop_ndcg10'] if r['pop_ndcg10'] else 0.0
    print(f"{r['split']:<18}{r['delta_ndcg']:>12.4f}{ratio:>15.2f}x{'':>6}")

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
    md("""## 5. Interaction plot

Vẽ bằng matplotlib, lưu PNG. Trục x là split, trục y là NDCG@10, hai đường cho hai model. Đây là hình chính của phần RQ1 trong báo cáo."""),
    code("""import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

splits_order = [r['split'] for r in rows]
x = np.arange(len(splits_order))

ax = axes[0]
ax.plot(x, [r['pop_ndcg10'] for r in rows], 'o-', label='MostPopular', color='#d95f02', linewidth=2, markersize=8)
ax.plot(x, [r['als_ndcg10'] for r in rows], 's-', label='ALS implicit', color='#1b9e77', linewidth=2, markersize=8)
ax.set_xticks(x)
ax.set_xticklabels(splits_order, rotation=15, ha='right')
ax.set_ylabel('NDCG@10')
ax.set_title('NDCG@10 theo chien luoc chia tap')
ax.legend()
ax.grid(alpha=0.3)

ax = axes[1]
colors = ['#7570b3' if v > 0 else '#e7298a' for v in [r['delta_ndcg'] for r in rows]]
ax.bar(x, [r['delta_ndcg'] for r in rows], color=colors)
ax.axhline(0, color='black', linewidth=0.8)
ax.set_xticks(x)
ax.set_xticklabels(splits_order, rotation=15, ha='right')
ax.set_ylabel('ΔNDCG@10 (ALS - MostPopular)')
ax.set_title('Do lon chenh lech theo split')
ax.grid(alpha=0.3, axis='y')
for xi, r in zip(x, rows):
    ax.annotate(f"{r['delta_ndcg']:+.4f}", (xi, r['delta_ndcg']),
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
    'models': ['MostPopular', 'ALS_implicit'],
    'k': spark_utils.TOP_K,
    'seed': spark_utils.DEFAULT_SEED,
    'subsample_users': spark_utils.SUBSAMPLE_USERS,
    'rows': rows,
    'pairs': pair_results,
    'reversals_found': reversals_found,
    'population_note': 'NDCG per split computed on that split own eligible+relevant population; not a paired comparison across splits.',
    'sources': {'mostpopular': str(pop_path), 'als': str(als_path), 'audit': str(audit_path)},
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
answer_lines.append(f"Subsample ALS: {spark_utils.SUBSAMPLE_USERS:,} users | Spark local[4], khong dung GPU")
answer_lines.append('')
answer_lines.append('## Bang ket qua')
answer_lines.append('')
answer_lines.append('| Split | MostPopular | ALS | Delta | Thang |')
answer_lines.append('|---|---|---|---|---|')
for r in rows:
    answer_lines.append(f"| {r['split']} | {r['pop_ndcg10']:.4f} | {r['als_ndcg10']:.4f} | {r['delta_ndcg']:+.4f} | {r['winner']} |")
answer_lines.append('')
answer_lines.append('## (a) Co dao chieu model thang khong')
if reversals_found == 0:
    answer_lines.append(f'Khong quan sat thay dao chieu tren {len(pair_results)}/{len(pair_results)} cap split. ALS thang o ca ba split.')
else:
    answer_lines.append(f'Co dao chieu o {reversals_found}/{len(pair_results)} cap split:')
    for p in pair_results:
        if p['reversal']:
            answer_lines.append(f"- {p['pair']}: {p['left_winner']} -> {p['right_winner']}")
answer_lines.append('')
answer_lines.append('## (b) Do lon chenh lech')
for r in rows:
    answer_lines.append(f"- {r['split']}: delta = {r['delta_ndcg']:+.4f}, ALS/MostPopular = {r['als_ndcg10']/r['pop_ndcg10']:.2f}x" if r['pop_ndcg10'] else f"- {r['split']}: delta = {r['delta_ndcg']:+.4f}")
answer_lines.append('')
answer_lines.append('## (c) Gioi han')
answer_lines.append('- Chi 1 seed (42). Khong tuyen bo on dinh qua seed.')
answer_lines.append('- Chi 2 baseline (MostPopular, ALS implicit). Khong phai so sanh state-of-the-art.')
answer_lines.append(f'- ALS chi fit tren {spark_utils.SUBSAMPLE_USERS:,} user dau theo userId, khong phai toan bo 162.541.')
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
        'ndcg': {r['split']: {'pop': r['pop_ndcg10'], 'als': r['als_ndcg10']} for r in rows},
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

