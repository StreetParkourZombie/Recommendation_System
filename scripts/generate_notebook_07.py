"""Generate Notebook 07: manual NDCG verification on hand-worked fixtures."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "jupyter" / "07_ndcg_manual_check.ipynb"
OUT.parent.mkdir(parents=True, exist_ok=True)


def md(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source.strip("\n").splitlines(keepends=True)}


def code(source):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source.strip("\n").splitlines(keepends=True)}


cells = [
    md("""# 07 — Kiểm tra NDCG bằng tính tay

**Mục tiêu:** chứng minh công thức NDCG/DCG/Hit trong `src/audit/metrics.py` đúng **trước khi** tin bất kỳ con số nào ở notebook 06 và 08.

**Input:** không cần dữ liệu lớn. Notebook chạy trong vài giây.

**Output:** `runs/<run_id>/outputs/metric_fixtures.json`.

**Gate L6b:** 5 ca tính tay khớp code; kiểm tra loại item đã thấy; kiểm tra Gini."""),
    md("""## Khái niệm — NDCG đo cái gì

**DCG@K** (Discounted Cumulative Gain) cộng điểm cho item relevant, nhưng giảm dần theo vị trí:

$$DCG@K = \\sum_{i=1}^{K} \\frac{rel_i}{\\log_2(i+1)}$$

Item relevant ở vị trí 1 được 1 điểm; ở vị trí 2 được 0,63; ở vị trí 10 được 0,29. Ý tưởng: gợi ý đúng ở đầu danh sách có giá trị hơn gợi ý đúng ở cuối.

**IDCG@K** (Ideal DCG) là DCG của thứ tự hoàn hảo — đặt toàn bộ item relevant lên đầu.

$$NDCG@K = \\frac{DCG@K}{IDCG@K}$$

NDCG = 1,0 nghĩa là xếp hạng hoàn hảo. NDCG = 0 nghĩa là không có item relevant nào trong top-K.

### Ba quyết định phải khai báo, không được để ngầm

1. **Ai vào mẫu trung bình?** User không có item relevant trong test bị **loại** khỏi mẫu (không tính là 0). Nếu tính là 0, NDCG của split có nhiều user không relevant sẽ bị kéo xuống vô nghĩa.
2. **IDCG tính trên bao nhiêu item?** `min(số item relevant, K)`. User có 3 relevant thì IDCG chỉ cộng 3 discount đầu.
3. **Xếp hạng ngắn hơn K thì sao?** Không được trả NDCG = 1,0. Ca 5 dưới đây bắt đúng lỗi này.

### Vì sao phải kiểm tra tay trước

Nếu công thức NDCG sai, mọi kết luận của đề tài đều sai — và sai một cách im lặng. Một off-by-one trong IDCG làm NDCG lệch vài phần trăm nhưng không có exception nào. Kiểm tra tay 5 ca mất 10 phút, tiết kiệm việc phát hiện lỗi sau khi đã viết xong báo cáo.

### Gini exposure

Gini đo mức độ tập trung: 0 = mọi item được đề xuất số lần như nhau; → 1 = dồn hết vào một vài item. Dùng để trả lời "mô hình này có thực sự đa dạng hơn MostPopular, hay chỉ dồn vào nhóm phim phổ biến khác?"."""),
    md("""## 1. Tính tay 5 ca

Bảng dưới đây là kết quả tính bằng giấy. Code phải khớp, không phải ngược lại.

| # | Ca | ranked (top-10) | relevant | DCG | IDCG | NDCG kỳ vọng |
|---|---|---|---|---|---|---|
| 1 | Hit vị trí 1 | `[10,20,...]` | `{10}` | `1/log2(2)=1.0` | `1/log2(2)=1.0` | **1.0** |
| 2 | Hit vị trí 10 | `[1..10]` | `{10}` | `1/log2(11)=0.2891` | `1.0` | **0.2891** |
| 3 | Không hit | `[1..10]` | `{99}` | `0` | `1.0` | **0.0** |
| 4 | 2 hit ở vị trí 1,3 | `[7,8,9,...]` | `{7,9}` | `1/log2(2)+1/log2(4)=1.5` | `1/log2(2)+1/log2(3)=1.6309` | **0.9197** |
| 5 | ranked ngắn hơn K | `[1,2,3]` | `{1..20}` | `1+0.6309+0.5=2.1309` | `sum(1/log2(2..11))=4.5439` | **0.4690** |

Ca 5 là ca quan trọng nhất: nhiều implementation trả `1.0` vì thấy mọi item trong ranked đều relevant, nhưng IDCG@10 tính trên 10 vị trí nên NDCG đúng chỉ 0.469."""),
    code("""from pathlib import Path
import json
import sys

project_root = Path.cwd().resolve()
while project_root != project_root.parent and not (project_root / 'src').is_dir():
    project_root = project_root.parent
sys.path.insert(0, str(project_root))

from IPython import get_ipython
from src.recsys.notebook_logging import NotebookRun
from src.audit import metrics

run = NotebookRun(
    project_root,
    '07_ndcg_manual_check',
    metadata={'k': 10, 'purpose': 'verify metric implementation against hand-worked fixtures', 'data_required': False},
)
run.attach_ipython(get_ipython())
print('Run ID:', run.run_id)
run.log('RUN_CONTEXT', note='no large data; fixtures only')"""),
    md("""## 2. Chạy fixture và đối chiếu

`assert_against_fixture()` raise `AssertionError` nếu bất kỳ ca nào lệch quá 1e-12 — không có dung sai lỏng, vì đây là số học chính xác."""),
    code("""results = metrics.assert_against_fixture(k_default=10)
for row in results:
    print(f"PASS  {row['case']:<40} ndcg={row['got_ndcg']:<10} hit={row['got_hit']}")
print()
print(f'All {len(results)} fixtures passed.')

run.log('FIXTURES_PASSED', count=len(results), results=results)
run.checkpoint(
    'fixtures_passed',
    'PASS',
    checks={'fixture_count': len(results), 'tolerance': '1e-12'},
)"""),
    md("""## 3. Kiểm tra IDCG bị chặn bởi số item relevant

Hai user có cùng top-1 hit nhưng số item relevant khác nhau phải có IDCG khác nhau. Nếu implementation bỏ qua điều này, user có 1 item relevant sẽ bị chấm thấp oan."""),
    code("""ranked = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]

cases = [
    ('1 relevant, hit top-1', ranked, {100}),
    ('3 relevant, hit top-1', ranked, {100, 999, 998}),
    ('10 relevant, hit top-1', ranked, set(range(100, 110))),
]

print(f"{'case':<26}{'dcg':>10}{'idcg':>10}{'ndcg':>10}")
print('-' * 56)
for name, r, rel in cases:
    dcg = metrics.dcg_at_k(r, rel, 10)
    idcg = metrics.idcg_at_k(len(rel), 10)
    ndcg = metrics.ndcg_at_k(r, rel, 10)
    print(f'{name:<26}{dcg:>10.4f}{idcg:>10.4f}{ndcg:>10.4f}')

# Cung DCG nhung IDCG khac -> NDCG giam khi co nhieu relevant item hon ma van chi hit 1.
ndcg_1 = metrics.ndcg_at_k(ranked, {100}, 10)
ndcg_10 = metrics.ndcg_at_k(ranked, set(range(100, 110)), 10)
assert ndcg_1 == 1.0 and ndcg_10 < ndcg_1, 'IDCG must be capped by number of relevant items.'

print()
print('Ket luan: cung mot lan hit top-1, user co 10 relevant item chi dat', round(ndcg_10, 4),
      'vi IDCG cua ho la 10 vi tri, khong phai 1.')
print('Day la hanh vi dung. Neu NDCG cua ho cung bang 1.0 thi IDCG da bi tinh sai.')
run.checkpoint('idcg_capping', 'PASS', checks={'ndcg_single_relevant': ndcg_1, 'ndcg_ten_relevant': round(ndcg_10, 4)})"""),
    md("""## 4. Kiểm tra loại item đã thấy (seen exclusion)

Đây là lỗi im lặng nguy hiểm nhất trong recommender: gợi ý lại phim user **đã xem**. Không exception, NDCG thậm chí **tăng** vì item đã xem thường relevant. Ô dưới mô phỏng đúng phép toán của `topk_numpy` với một user nhỏ để chứng minh `-inf` loại đúng.

Fixture: 5 item, user đã xem item index 0 và 2. Không loại thì top-2 là `[0, 2]`; có loại thì phải là `[1, 3]` hoặc `[3, 1]`."""),
    code("""import numpy as np

# Ma tran gia: 1 user, 5 item. Score giam dan theo index de de doc.
U = np.array([[1.0, 0.0]], dtype=np.float32)
V = np.array([
    [5.0, 0.0],   # item 0 - user da xem
    [4.0, 0.0],   # item 1
    [3.0, 0.0],   # item 2 - user da xem
    [2.0, 0.0],   # item 3
    [1.0, 0.0],   # item 4
], dtype=np.float32)
vi = np.array([0, 1, 2, 3, 4], dtype=np.int64)
ui = np.array([1], dtype=np.int64)

scores = U @ V.T
naive_top2 = vi[np.argsort(-scores[0])[:2]]
print('Khong loai item da xem -> top-2:', naive_top2.tolist())

seen = {1: {0, 2}}
item_position = {int(m): i for i, m in enumerate(vi)}
blocked = [item_position[i] for i in seen[1] if i in item_position]
masked = scores.copy()
masked[0, blocked] = -np.inf
excluded_top2 = vi[np.argsort(-masked[0])[:2]]
print('Co loai item da xem   -> top-2:', excluded_top2.tolist())

assert set(naive_top2.tolist()) & {0, 2}, 'Fixture khong dung: naive top phai chua item da xem.'
assert not (set(excluded_top2.tolist()) & {0, 2}), 'Seen exclusion failed: top-K van chua item da xem.'
print()
print('PASS: -inf loai dung item da tuong tac trong train.')
run.checkpoint('seen_exclusion_fixture', 'PASS', checks={'naive_top2': naive_top2.tolist(), 'excluded_top2': excluded_top2.tolist()})"""),
    md("""## 5. Gini exposure

Ba vector kiểm tra: đồng đều (Gini 0), dồn một chỗ (Gini → 1), và rỗng (Gini 0, không chia cho 0)."""),
    code("""vectors = {
    'deu (10 item x 10 lan)': [10] * 10,
    'don 1 cho (1 item x 100)': [100] + [0] * 99,
    'chi 2 item co exposure': [50, 50] + [0] * 98,
    'rong': [],
}

for name, vector in vectors.items():
    print(f'{name:<30}gini={metrics.gini(vector):.4f}')

assert abs(metrics.gini([10] * 10)) < 1e-12, 'Uniform exposure must give Gini 0.'
assert metrics.gini([100] + [0] * 99) > 0.98, 'Concentrated exposure must give Gini near 1.'
assert metrics.gini([]) == 0.0, 'Empty vector must give 0, not ZeroDivisionError.'

print()
print('PASS: Gini xu ly dung ca 3 truong hop bien.')
run.checkpoint(
    'gini_fixture',
    'PASS',
    checks={name: round(metrics.gini(vec), 4) for name, vec in vectors.items()},
)"""),
    md("""## 6. Ghi artifact và kết luận

Từ notebook 08 trở đi, `src/audit/metrics.py` được coi là đã kiểm chứng. Nếu sau này sửa file đó, phải chạy lại notebook này trước khi tin bất kỳ kết quả mới."""),
    code("""outputs_dir = run.run_dir / 'outputs'
outputs_dir.mkdir(parents=True, exist_ok=True)
path = outputs_dir / 'metric_fixtures.json'
payload = {
    'k': 10,
    'fixtures': results,
    'idcg_capping': {'single_relevant_ndcg': ndcg_1, 'ten_relevant_ndcg': round(float(ndcg_10), 6)},
    'seen_exclusion': {'naive_top2': naive_top2.tolist(), 'excluded_top2': excluded_top2.tolist()},
    'gini': {name: round(metrics.gini(vec), 6) for name, vec in vectors.items()},
    'decision': 'metric implementation verified against hand-worked cases',
}
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
reloaded = json.loads(path.read_text(encoding='utf-8'))
assert reloaded['decision'] == 'metric implementation verified against hand-worked cases'
print('Saved:', path)

run.checkpoint('fixtures_saved', 'PASS', checks={'readback': True}, note=str(path))
run.finish('COMPLETED', summary={'fixtures': len(results), 'output': str(path)})
print('L6b COMPLETE. Metrics verified. Next: 08_als_implicit.ipynb')"""),
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

