"""Generate Notebook 05: audit data-level leakage per split."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "jupyter" / "05_audit_split_leakage.ipynb"
OUT.parent.mkdir(parents=True, exist_ok=True)


def md(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source.strip("\n").splitlines(keepends=True)}


def code(source):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source.strip("\n").splitlines(keepends=True)}


cells = [
    md("""# 05 — Audit rò rỉ dữ liệu theo từng chiến lược chia tập

**Mục tiêu:** đo bằng số cái giá của mỗi chiến lược chia, **không cần mô hình nào**. Đây là tầng có giá trị khoa học cao nhất của đề tài: không con số nào ở đây có thể bị quy cho "mô hình yếu".

**Input:** 3 split đã ghi ở notebook 04 (`D:\\recsys_data\\splits\\<strategy>\\{train,test}`).

**Output:** `runs/<run_id>/outputs/data_level_audit.{json,csv}`.

**Gate L5:** 3 split cùng được audit bằng cùng định nghĩa; số rò rỉ khớp kết quả đo thật."""),
    md("""## Khái niệm — hai định nghĩa rò rỉ thời gian, và tại sao phải có cả hai

**(a) Toàn cục:** đếm tương tác test có `timestamp` nhỏ hơn `max(timestamp)` của **toàn bộ** train.

```
temporal_violation_global = |{ r in test : r.timestamp < max(train.timestamp) }|
```

**(b) Tương đối theo user:** đếm tương tác test có `timestamp` nhỏ hơn `max(timestamp)` của **chính user đó** trong train.

```
temporal_violation_user = |{ r in test : r.timestamp < max(train(u).timestamp) }|
```

Vì sao cần cả hai: với `leave_one_out`, định nghĩa toàn cục cho **99,9988%** — nghe như thảm họa. Nhưng con số đó chỉ phản ánh việc user A có thể có tương tác mới nhất năm 2019 trong khi test của user B là năm 1996. Trong khi đó định nghĩa tương đối cho **0%** — đúng như thiết kế LOO. Chỉ định nghĩa tương đối mới đo rò rỉ **nhân quả**.

Báo cáo chỉ một trong hai con số là báo cáo sai. Báo cả hai và giải thích khác biệt là cách đúng.

**Hai chỉ số dịch chuyển miền:**

- `unseen_item_pct`: test trỏ tới phim chưa từng có trong train → mô hình không thể có trọng số cho phim đó, lỗi không tránh được.
- `coldstart_user_rows`: test có user hoàn toàn mới → lỗi không tránh được với mọi mô hình lọc cộng tác.

Đây là **cái giá** phải trả khi loại bỏ rò rỉ thời gian. Không có bữa trưa miễn phí."""),
    md("""## 1. Nạp split đã ghi và Spark session"""),
    code("""from pathlib import Path
import json
import sys
import time

project_root = Path.cwd().resolve()
while project_root != project_root.parent and not (project_root / 'src').is_dir():
    project_root = project_root.parent
sys.path.insert(0, str(project_root))

from IPython import get_ipython
from src.recsys.notebook_logging import NotebookRun
from src.utils import spark_utils
from src.audit import splits as split_lib
from src.audit import leakage

run = NotebookRun(
    project_root,
    '05_audit_split_leakage',
    metadata={
        'protocol_id': spark_utils.PROTOCOL_ID,
        'relevance_threshold': spark_utils.RELEVANCE_THRESHOLD,
        'min_train': spark_utils.MIN_TRAIN,
        'purpose': 'data-level audit: leakage, domain shift, eligibility',
    },
)
run.attach_ipython(get_ipython())
print('Run ID:', run.run_id)

runs_dir = project_root / 'runs'
manifest_candidates = sorted(
    (
        p
        for p in runs_dir.glob('*/outputs/split_manifest.json')
        if p.parent.parent.name.endswith('04_build_splits') or True
    ),
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)
assert manifest_candidates, 'split_manifest.json not found; run notebook 04 first.'
split_manifest_path = manifest_candidates[0]
split_manifest = json.loads(split_manifest_path.read_text(encoding='utf-8'))
assert set(split_manifest['strategies']) == set(split_lib.STRATEGIES), 'Manifest does not cover all strategies.'
print('Split manifest:', split_manifest_path)
print('Protocol:', split_manifest['protocol_id'], '| seed:', split_manifest['seed'])

for strategy in split_lib.STRATEGIES:
    train_dir = Path(split_manifest['splits_dir']) / strategy / 'train'
    test_dir = Path(split_manifest['splits_dir']) / strategy / 'test'
    assert train_dir.is_dir() and test_dir.is_dir(), f'{strategy} artifacts missing: {train_dir} / {test_dir}'

run.checkpoint(
    'splits_loaded',
    'PASS',
    checks={
        'manifest': str(split_manifest_path),
        'strategies': list(split_lib.STRATEGIES),
        'all_dirs_exist': True,
    },
)"""),
    code("""spark = spark_utils.get_spark('RecSys05AuditSplitLeakage')
print('Spark:', spark.version, '| master:', spark.sparkContext.master)
run.checkpoint('spark_ready', 'PASS', checks={'spark_version': spark.version, 'master': spark.sparkContext.master})"""),
    md("""## 2. Audit từng split

Cùng một hàm `data_level_audit` cho cả 3 split. Đây là điều kiện để so sánh công bằng: cùng định nghĩa, cùng ngưỡng relevance, cùng `min_train`."""),
    code("""audits = {}
started = time.perf_counter()

for strategy in split_lib.STRATEGIES:
    train_df, test_df = split_lib.load_split(strategy, spark_utils.SPLITS_DIR)
    audit = leakage.data_level_audit(
        train_df,
        test_df,
        relevance_threshold=spark_utils.RELEVANCE_THRESHOLD,
        min_train=spark_utils.MIN_TRAIN,
        split_name=strategy,
    )
    audits[strategy] = audit
    print(f'--- {strategy} ---')
    for key in (
        'train_rows', 'test_rows',
        'temporal_violation_global', 'temporal_violation_global_pct',
        'temporal_violation_user', 'temporal_violation_user_pct',
        'unseen_item_rows', 'unseen_item_pct',
        'coldstart_user_rows',
        'eval_users', 'eval_relevant_users',
    ):
        print(f'  {key:<34}{audit[key]}')
    run.log('DATASET_AUDIT', strategy=strategy, audit=audit)

print()
print(f'Total audit time: {time.perf_counter() - started:.1f}s')
run.checkpoint('audits_complete', 'PASS', checks={'strategies': list(audits)})"""),
    md("""## 3. Đối chiếu với kết quả đo thật

Các số dưới đây đã đo bằng `scripts/04_audit_spark.py` ngày 2026-11-15. Notebook tái lập chúng để chứng minh logic trong `src/audit/leakage.py` khớp script gốc — không phải so với con số lý thuyết."""),
    code("""expected = {
    'random80_20': {
        'train_rows': 19_997_974, 'test_rows': 5_002_121,
        'temporal_violation_global_pct': 100.0,
        'temporal_violation_user_pct': 98.9158,
        'unseen_item_pct': 0.0573,
        'coldstart_user_rows': 0,
        'eval_users': 162_541,
        'eval_relevant_users': 158_692,
    },
    'temporal_global': {
        'train_rows': 19_999_279, 'test_rows': 5_000_816,
        'temporal_violation_global_pct': 0.0,
        'temporal_violation_user_pct': 0.0,
        'unseen_item_pct': 8.7595,
        'coldstart_user_rows': 4_235_246,
        'eval_users': 137_839,
        'eval_relevant_users': 6_219,
    },
    'leave_one_out': {
        'train_rows': 24_837_554, 'test_rows': 162_541,
        'temporal_violation_global_pct': 99.9988,
        'temporal_violation_user_pct': 0.0,
        'unseen_item_pct': 0.0388,
        'coldstart_user_rows': 0,
        'eval_users': 162_541,
        'eval_relevant_users': 96_003,
    },
}

mismatches = []
for strategy, fields in expected.items():
    for key, want in fields.items():
        got = audits[strategy][key]
        ok = abs(got - want) <= 0.01 if isinstance(want, float) else got == want
        status = 'OK  ' if ok else 'DIFF'
        if not ok:
            mismatches.append((strategy, key, want, got))
        print(f'{status} {strategy:<17}{key:<34}got={got!r:<20}want={want!r}')

print()
if mismatches:
    print('MISMATCHES:', len(mismatches))
    for item in mismatches:
        print('  ', item)
else:
    print('All data-level figures reproduce the measured baseline.')

run.log('REPRODUCTION_CHECK', mismatches=len(mismatches), detail=mismatches)
run.checkpoint(
    'reproduction_check',
    'PASS' if not mismatches else 'FAIL',
    checks={'mismatches': len(mismatches), 'detail': mismatches},
    note='random80_20 uses F.rand; counts may drift slightly with shuffle partitions. temporal/LOO are deterministic.',
)"""),
    md("""## 4. Bảng so sánh 3 chiến lược

Đọc bảng này theo ba câu hỏi, không theo thứ tự cột:

1. **Rò rỉ:** `random80_20` rò rỉ ở cả hai nghĩa. `temporal_global` sạch hoàn toàn. `leave_one_out` sạch theo nghĩa nhân quả, nhưng con số toàn cục 99,9988% là hiện tượng do trộn timeline nhiều user, không phải lỗi.
2. **Cái giá:** `temporal_global` trả giá bằng 8,76% item chưa thấy và 4,2 triệu dòng user lạnh.
3. **Mẫu đánh giá:** `temporal_global` chỉ còn **6.219 user** có ít nhất 1 item relevant trong test, so với 158.692 user của random. Đây là lý do NDCG của temporal không so trực tiếp được với random nếu không nêu rõ population."""),
    code("""columns = [
    ('train_rows', 'train'),
    ('test_rows', 'test'),
    ('temporal_violation_global_pct', 'viol_global_%'),
    ('temporal_violation_user_pct', 'viol_user_%'),
    ('unseen_item_pct', 'unseen_item_%'),
    ('coldstart_user_rows', 'coldstart'),
    ('eval_users', 'eval_users'),
    ('eval_relevant_users', 'eval_relevant'),
]
header = f"{'metric':<24}" + ''.join(f'{s:>19}' for s in split_lib.STRATEGIES)
print(header)
print('-' * len(header))
for key, label in columns:
    line = f'{label:<24}'
    for strategy in split_lib.STRATEGIES:
        value = audits[strategy][key]
        line += f'{value:>19,}' if isinstance(value, int) else f'{value:>19.4f}'
    print(line)

print()
print('Test population co lai manh o temporal_global:')
for strategy in split_lib.STRATEGIES:
    a = audits[strategy]
    ratio = 100.0 * a['eval_relevant_users'] / a['eval_users'] if a['eval_users'] else 0.0
    print(f"  {strategy:<18}{ratio:>6.1f}% eval_users co it nhat 1 relevant item")"""),
    md("""## 5. Ghi artifact

`data_level_audit.json` là nguồn cho notebook 06, 08 (cần `eval_users`) và cho bảng trong báo cáo. File CSV để dán vào phụ lục."""),
    code("""import csv

outputs_dir = run.run_dir / 'outputs'
outputs_dir.mkdir(parents=True, exist_ok=True)

json_path = outputs_dir / 'data_level_audit.json'
json_path.write_text(
    json.dumps(
        {
            'protocol_id': spark_utils.PROTOCOL_ID,
            'relevance_threshold': spark_utils.RELEVANCE_THRESHOLD,
            'min_train': spark_utils.MIN_TRAIN,
            'split_manifest': str(split_manifest_path),
            'audits': audits,
            'reproduction_mismatches': mismatches,
        },
        ensure_ascii=False,
        indent=2,
        default=str,
    ),
    encoding='utf-8',
)

csv_path = outputs_dir / 'data_level_audit.csv'
fieldnames = ['split'] + [k for k in audits['random80_20'] if k != 'split']
with csv_path.open('w', newline='', encoding='utf-8') as stream:
    writer = csv.DictWriter(stream, fieldnames=fieldnames)
    writer.writeheader()
    for strategy in split_lib.STRATEGIES:
        writer.writerow(audits[strategy])

reloaded = json.loads(json_path.read_text(encoding='utf-8'))
assert set(reloaded['audits']) == set(split_lib.STRATEGIES)
print('JSON:', json_path, json_path.stat().st_size, 'bytes')
print('CSV :', csv_path, csv_path.stat().st_size, 'bytes')

run.checkpoint(
    'audit_saved',
    'PASS',
    checks={
        'json_readback': True,
        'csv_exists': csv_path.is_file(),
        'strategies': len(reloaded['audits']),
        'mismatches': len(mismatches),
    },
    note=str(json_path),
)
run.finish(
    'COMPLETED',
    summary={
        'splits_audited': list(split_lib.STRATEGIES),
        'mismatches': len(mismatches),
        'leakage_random_user_pct': audits['random80_20']['temporal_violation_user_pct'],
        'leakage_temporal_user_pct': audits['temporal_global']['temporal_violation_user_pct'],
        'output': str(json_path),
    },
)
spark_utils.stop_spark(spark)
print('L5 COMPLETE. Next: 06_mostpopular_baseline.ipynb')"""),
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

