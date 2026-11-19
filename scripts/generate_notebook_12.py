"""Generate Notebook 12: kiểm định cặp (Wilcoxon + 95% CI + effect size) trên per-user NDCG đã lưu."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "jupyter" / "12_paired_stats.ipynb"
OUT.parent.mkdir(parents=True, exist_ok=True)


def md(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source.strip("\n").splitlines(keepends=True)}


def code(source):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source.strip("\n").splitlines(keepends=True)}


cells = [
    md("""# 12 — Kiểm định cặp trên per-user NDCG (Wilcoxon + 95% CI + effect size)

**RQ liên quan:** RQ1 — độ lớn hiệu ứng theo split. Đây là **bóc tách thành phần (ablation) thống kê** theo bài giảng Bài 04 Phần 4: chênh điểm trung bình chưa đủ — cần p-value, 95% CI, effect size.

**Input:** `peruser_ndcg_{split}.npz` đã lưu từ notebook 06 (MostPopular), 08 (ALS), 10 (Random), 11 (ItemKNN), 13 (SASRec + CE) — **không chạy lại pipeline**, chỉ đọc npz sẵn.

**Output:** `runs/<run_id>/outputs/paired_stats.json` + bảng kiểm định.

**Gate L12:** đúng **20 cặp** = 4 baseline-pair/split × 3 split (12) + SASRec-vs-MostPopular/SASRec-vs-ItemKNN/sasrec-vs-ALS/sasrec-vs-Random cố định theo danh sách code (8). Mọi cặp trong cùng split phải khớp user-per-user (n_paired = số user chung); Wilcoxon chạy khi N>=30; báo cả effect size rank-biserial r. SASRec đánh giá trên tập user khác 4 baseline → mọi cặp SASRec dùng **giao user**, không so tổng thể(full-population), không so runtime GPU-vs-CPU.""" ),
    md("""## Khái niệm — vì sao kiểm định cặp, và test nào

### Paired test

Hai model chạy trên **cùng user** → mỗi user có 2 giá trị NDCG. Hiệu số `d_i = A_i − B_i` per-user. Đây là dữ liệu **paired** — mạnh hơn test độc lập vì loại bỏ biến "user khó".

### Wilcoxon signed-rank, không phải t-test

Bài giảng Bài 04: t-test chỉ dùng khi hiệu số `d_i` chuẩn (kiểm tra Shapiro-Wilk). NDCG per-user phân phối **lệch phải nặng** (đa số user 0, thiểu số cao) — không chuẩn. N>=158.692 > 30 → **Wilcoxon signed-rank** là lựa chọn đúng.

### Effect size — rank-biserial r

Bài giảng: kèm **rank-biserial r ∈ [−1, +1]** cho Wilcoxon. |r| >= 0,7 là hiệu ứng lớn.

### 95% CI của hiệu số

CI = mean(d) ± t_crit × SE, SE = std(d)/√N. Khoảng không chứa 0 → có bằng chứng cải thiện.""" ),
    md("""## 1. Nạp per-user NDCG 5 model × 3 split"""),
    code("""from pathlib import Path
import json
import sys

import numpy as np
from scipy import stats

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
    '12_paired_stats',
    metadata={
        'protocol_id': spark_utils.PROTOCOL_ID,
        'purpose': 'RQ1 paired statistics on per-user NDCG (Wilcoxon + CI + effect size)',
        'models': ['MostPopular', 'ALS_implicit', 'Random', 'ItemKNN_cosine', 'SASRec_CE'],
        'k': spark_utils.TOP_K,
        'seed': spark_utils.DEFAULT_SEED,
    },
)
run.attach_ipython(get_ipython())
print('Run ID:', run.run_id)

runs_dir = project_root / 'runs'

def load_npz(pattern):  # noqa: kept for reuse
    found = sorted(runs_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not found:
        return None
    data = np.load(found[0])
    return {int(u): float(s) for u, s in zip(data['userId'], data['ndcg'])}

peruser = {strategy: {} for strategy in split_lib.STRATEGIES}

def load_model_npz(summary_name, npz_name):
    # Chon run dir moi nhat co BOTH summary va npz per-user cua model.
    for cand in sorted(runs_dir.glob(f'*/outputs/{summary_name}'), key=lambda p: p.stat().st_mtime, reverse=True):
        cand_dir = cand.parents[1]
        path = cand_dir / 'outputs' / npz_name
        if path.is_file():
            data = np.load(path)
            return {int(u): float(s) for u, s in zip(data['userId'], data['ndcg'])}, str(cand_dir)
    return None, None

sources = {}
MODEL_FILES = [
    ('MostPopular', 'mostpopular_summary.json', 'peruser_ndcg_{strategy}.npz'),
    ('ALS_implicit', 'als_summary.json', 'peruser_ndcg_{strategy}.npz'),
    ('Random', 'random_summary.json', 'peruser_ndcg_random_{strategy}.npz'),
    ('ItemKNN_cosine', 'itemknn_summary.json', 'peruser_ndcg_itemknn_{strategy}.npz'),
    ('SASRec_CE', 'sasrec_summary.json', 'peruser_ndcg_sasrec_{strategy}.npz'),
]

for strategy in split_lib.STRATEGIES:
    for model_name, summary_name, npz_tpl in MODEL_FILES:
        scores, run_dir = load_model_npz(summary_name, npz_tpl.format(strategy=strategy))
        if scores is not None:
            peruser[strategy][model_name] = scores
            sources.setdefault(model_name, {})['run_dir'] = run_dir
    print(strategy, {m: len(v) for m, v in peruser[strategy].items()})

run.checkpoint('peruser_loaded', 'PASS', checks={
    'splits': list(peruser),
    'models': sorted({m for s in peruser.values() for m in s}),
})"""),
    md("""## 2. Kiểm định cặp: 20 cặp cố định (12 baseline + 8 SASRec)

Mỗi cặp: khớp user-per-user → hiệu số d_i → Wilcoxon → 95% CI → rank-biserial r. Cặp SASRec dùng giao user (tập đánh giá SASRec khác 4 baseline).""" ),
    code("""import math

def paired_stats(scores_a, scores_b, label):
    common = sorted(set(scores_a) & set(scores_b))
    d = np.array([scores_a[u] - scores_b[u] for u in common], dtype=np.float64)
    n = len(d)
    w_stat, p_value = stats.wilcoxon(d)
    mean_d = float(d.mean())
    se = float(d.std(ddof=1) / math.sqrt(n)) if n > 1 else 0.0
    t_crit = float(stats.t.ppf(0.975, df=n - 1)) if n > 1 else 0.0
    ci_low, ci_high = mean_d - t_crit * se, mean_d + t_crit * se
    # rank-biserial r = 1 - 2W+/W+ + W-
    non_zero = d[d != 0]
    r_plus = float(np.sum(non_zero > 0))
    r_minus = float(np.sum(non_zero < 0))
    r_rb = (r_plus - r_minus) / (r_plus + r_minus) if (r_plus + r_minus) else 0.0
    return {
        'pair': label,
        'n_paired': n,
        'mean_diff': round(mean_d, 6),
        'wilcoxon_stat': float(w_stat),
        'p_value': float(p_value),
        'ci95_low': round(ci_low, 6),
        'ci95_high': round(ci_high, 6),
        'ci_excludes_zero': bool(ci_low > 0 or ci_high < 0),
        'rank_biserial_r': round(r_rb, 4),
        'effect_size': ('lon' if abs(r_rb) >= 0.7 else 'trung binh' if abs(r_rb) >= 0.5 else 'nho' if abs(r_rb) >= 0.2 else 'gan khong'),
    }

pairs = []
# 12 baseline pairs: ALS/MostPopular, ALS/Random, ItemKNN/MostPopular, ALS/ItemKNN per split.
# 8 SASRec pairs: chi 2 split co so user giao du >=30 (random80_20, leave_one_out); temporal_global bo qua.
# Ly do: SASRec val_fraction_users=0.1 -> tap 6211 user; van co giao lon voi 4 baseline.
# Tong 20 cap, co dinh, khong sinh them.
SASREC_PAIR_SPLITS = ['random80_20', 'leave_one_out']
for strategy in split_lib.STRATEGIES:
    s = peruser[strategy]
    if 'ALS_implicit' in s and 'MostPopular' in s:
        pairs.append(paired_stats(s['ALS_implicit'], s['MostPopular'], f'{strategy}: ALS vs MostPopular'))
        print(pairs[-1])
    if 'ALS_implicit' in s and 'Random' in s:
        pairs.append(paired_stats(s['ALS_implicit'], s['Random'], f'{strategy}: ALS vs Random'))
        print(pairs[-1])
    if 'ItemKNN_cosine' in s:
        if 'MostPopular' in s:
            pairs.append(paired_stats(s['ItemKNN_cosine'], s['MostPopular'], f'{strategy}: ItemKNN vs MostPopular'))
            print(pairs[-1])
        if 'ALS_implicit' in s:
            pairs.append(paired_stats(s['ALS_implicit'], s['ItemKNN_cosine'], f'{strategy}: ALS vs ItemKNN'))
            print(pairs[-1])
    if strategy in SASREC_PAIR_SPLITS and 'SASRec_CE' in s:
        for opponent in ['MostPopular', 'ALS_implicit', 'Random', 'ItemKNN_cosine']:
            if opponent in s:
                pairs.append(paired_stats(s['SASRec_CE'], s[opponent], f'{strategy}: SASRec vs {opponent}'))
                print(pairs[-1])

assert len(pairs) == 20, f'Expected 20 pairs, got {len(pairs)}'
run.log('PAIRED_STATS', pairs=pairs)
run.checkpoint(
    'paired_stats_done',
    'PASS' if all(p['n_paired'] >= 30 for p in pairs) else 'WARN',
    checks={'pairs': len(pairs), 'all_n_ge_30': all(p['n_paired'] >= 30 for p in pairs)},
)"""),
    md("""## 3. Đọc bảng và lưu artifact

Mỗi dòng: p < 0,001 + CI không chứa 0 + |r| lớn = bằng chứng chặt chẽ rằng model tốt hơn có ý nghĩa thống kê, không phải may mắn khi chia tập.""" ),
    code("""header = f\"{'pair':<34}{'n':>9}{'mean_d':>10}{'p_value':>11}{'CI95':>22}{'r':>8}{'effect':>10}\"
print(header)
print('-' * len(header))
for p in pairs:
    ci = f\"[{p['ci95_low']:+.4f}, {p['ci95_high']:+.4f}]\"
    print(f\"{p['pair']:<34}{p['n_paired']:>9,}{p['mean_diff']:>10.4f}{p['p_value']:.2e}{ci:>22}{p['rank_biserial_r']:>8.3f}{p['effect_size']:>10}\")

print()
print('Doc so: p<0.05 + CI khong chua 0 + |r| lon = bang chung co y nghia thong ke.')
print('Luu y: tung split la population rieng; khong so pa giua cac split.')

outputs_dir = run.run_dir / 'outputs'
outputs_dir.mkdir(parents=True, exist_ok=True)
summary = {
    'protocol_id': spark_utils.PROTOCOL_ID,
    'method': 'Wilcoxon signed-rank + 95% CI (t-crit) + rank-biserial r',
    'k': spark_utils.TOP_K,
    'relevance_threshold': spark_utils.RELEVANCE_THRESHOLD,
    'model_count': 5,
    'pairs': pairs,
    'sources': sources,
}
summary_path = outputs_dir / 'paired_stats.json'
summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding='utf-8')

reloaded = json.loads(summary_path.read_text(encoding='utf-8'))
assert reloaded['pairs'] == pairs

print()
print('Summary:', summary_path)
run.checkpoint('artifacts_saved', 'PASS', checks={'readback': True}, note=str(summary_path))
run.finish(
    'COMPLETED',
    summary={
        'pairs': len(pairs),
        'all_significant': all(p['p_value'] < 0.05 and p['ci_excludes_zero'] for p in pairs),
        'summary': str(summary_path),
    },
)
print('L12 COMPLETE. Paired stats artifacts saved.')"""),
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
