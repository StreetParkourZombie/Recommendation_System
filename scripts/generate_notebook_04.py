"""Generate Notebook 04: build and materialize the three split strategies."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "jupyter" / "04_build_splits.ipynb"
OUT.parent.mkdir(parents=True, exist_ok=True)


def md(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source.strip("\n").splitlines(keepends=True)}


def code(source):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source.strip("\n").splitlines(keepends=True)}


cells = [
    md("""# 04 — Sinh 3 chiến lược chia tập

**Mục tiêu:** tạo đúng 3 split đã khai báo trong protocol và ghi ra Parquet để các notebook sau đọc lại, không dựng lại từ `ratings.csv`.

**Input:** L3 `exploratory profile` đã `COMPLETED`; Parquet cache `D:\\recsys_data\\parquet\\ratings\\part-00000.parquet`.

**Output:** `D:\\recsys_data\\splits\\<strategy>\\{train,test}\\` + `runs/<run_id>/outputs/split_manifest.json`.

**Gate L4:** cả 3 split ghi được, đọc lại khớp số dòng, không overlap giữa train và test."""),
    md("""## Khái niệm — chia tập là quyết định protocol, không phải tiền xử lý

Ba cách chia trả lời ba câu hỏi khác nhau, và **cả ba đều hợp lệ**. Không có cách "đúng nhất":

| Chiến lược | Trả lời câu hỏi | Đánh đổi |
|---|---|---|
| `random80_20` | Mô hình xếp hạng tốt đến đâu khi dữ liệu test giống dữ liệu train? | Cho mô hình "nhìn thấy tương lai" nếu timestamp quan trọng |
| `temporal_global` | Mô hình dự đoán được tương tác **sau** một mốc thời gian? | Nhiều item/user mới chưa từng xuất hiện trong train |
| `leave_one_out` | Mô hình đoán đúng tương tác **tiếp theo** của mỗi user? | Test rất nhỏ (1 dòng/user), phương sai lớn |

Điểm mấu chốt của đề tài: **cùng một mô hình, cùng dữ liệu, ba cách chia cho ba con số khác nhau**. Chênh lệch đó là tín hiệu cần đo, không phải lỗi cần sửa.

Một lưu ý về `leave_one_out`: khi user có nhiều tương tác cùng giây, `timestamp` một mình không xác định được cái nào "mới nhất". Notebook này tie-break bằng `movieId` tăng dần để kết quả đơn định — nhưng đó **không phải** thứ tự thời gian thật. Phải ghi rõ điều này khi báo cáo.

Spark transformations lazy: mỗi `count`/`write` mới kích hoạt job. Bảng dưới đây chỉ ghi aggregate, không collect dữ liệu thô về driver."""),
    md("""## 1. Điều kiện đầu vào

Kiểm tra L3 manifest `COMPLETED` và Parquet cache tồn tại. Nếu thiếu, dừng — không tự dựng lại dữ liệu."""),
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

ratings_path = spark_utils.RAW_RATINGS_CSV
parquet_path = spark_utils.PARQUET_RATINGS
expected_sha256 = spark_utils.RATINGS_SHA256

run = NotebookRun(
    project_root,
    '04_build_splits',
    metadata={
        'protocol_id': spark_utils.PROTOCOL_ID,
        'seed': spark_utils.DEFAULT_SEED,
        'test_fraction': 0.2,
        'source': str(parquet_path),
        'purpose': 'materialize split strategies for downstream notebooks',
    },
)
run.attach_ipython(get_ipython())
print('Run ID:', run.run_id)

runs_dir = project_root / 'runs'
l3_candidates = sorted(
    (
        p
        for p in runs_dir.glob('*/manifest.json')
        if json.loads(p.read_text(encoding='utf-8')).get('notebook_id') == '03_understand_interactions'
    ),
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)
assert l3_candidates, 'Notebook 03 run not found.'
assert json.loads(l3_candidates[0].read_text(encoding='utf-8')).get('status') == 'COMPLETED', 'L3 not COMPLETED.'
assert parquet_path.is_file(), f'Parquet cache missing: {parquet_path}'
assert ratings_path.is_file(), f'Raw ratings missing: {ratings_path}'

print('Parquet cache:', parquet_path, parquet_path.stat().st_size, 'bytes')
print('Raw ratings  :', ratings_path, ratings_path.stat().st_size, 'bytes')
print('L3 manifest  :', l3_candidates[0])
run.checkpoint(
    'prereq_ok',
    'PASS',
    checks={
        'l3_completed': True,
        'parquet_exists': True,
        'ratings_exists': True,
        'ratings_sha256': expected_sha256,
        'raw_bytes_match': ratings_path.stat().st_size == spark_utils.RATINGS_BYTES,
    },
    note=f'L3 manifest: {l3_candidates[0]}',
)"""),
    md("""## 2. Spark session

`get_spark()` cố định `local[4]`, driver `6g`, `shuffle.partitions=8`, `timeZone=UTC`. Không tự dựng builder riêng để cấu hình không lệch giữa notebook.

Ô này cũng gọi `ensure_hadoop_home()`. Trên Windows, ghi Parquet cần **cả** `winutils.exe` **và** `hadoop.dll`; chỉ có `winutils.exe` thì vẫn `UnsatisfiedLinkError: NativeIO$Windows.access0`."""),
    code("""hadoop_ok = spark_utils.ensure_hadoop_home()
spark = spark_utils.get_spark('RecSys04BuildSplits')
print('Spark:', spark.version, '| master:', spark.sparkContext.master)
print('HADOOP_HOME configured:', hadoop_ok, '->', spark_utils.HADOOP_HOME)
print('shuffle.partitions:', spark.conf.get('spark.sql.shuffle.partitions'))
print('session.timeZone:', spark.conf.get('spark.sql.session.timeZone'))
assert hadoop_ok, 'winutils.exe + hadoop.dll required for Parquet write on Windows.'
run.checkpoint(
    'spark_ready',
    'PASS',
    checks={
        'spark_version': spark.version,
        'master': spark.sparkContext.master,
        'hadoop_home_ok': hadoop_ok,
        'hadoop_home': str(spark_utils.HADOOP_HOME),
        'shuffle_partitions': spark.conf.get('spark.sql.shuffle.partitions'),
        'timezone': spark.conf.get('spark.sql.session.timeZone'),
    },
)"""),
    md("""## 3. Đọc ratings từ Parquet cache

Đọc file đơn `part-00000.parquet`, không trỏ vào thư mục (đã vấp lỗi `NativeIO` khi trỏ thư mục ở môi trường cũ). `repartition(8)` để số partition cố định, giúp `F.rand(seed)` nhất quán hơn giữa các lần chạy."""),
    code("""started = time.perf_counter()
ratings = spark_utils.read_ratings(spark, 'parquet').repartition(8).persist()
rows = ratings.count()
users = ratings.select('userId').distinct().count()
items = ratings.select('movieId').distinct().count()
elapsed = round(time.perf_counter() - started, 2)
print(f'rows={rows:,} users={users:,} items={items:,} ({elapsed}s)')
print('schema:', ratings.schema.simpleString())
assert rows == spark_utils.RATINGS_ROWS, f'Expected {spark_utils.RATINGS_ROWS:,}, got {rows:,}'
assert users == 162_541 and items == 59_047
run.log('RATINGS_LOADED', rows=rows, users=users, items=items, elapsed_seconds=elapsed, schema=ratings.schema.simpleString())
run.checkpoint('input_ready', 'PASS', checks={'rows': rows, 'users': users, 'items': items, 'schema': ratings.schema.simpleString()})"""),
    md("""## 4. Sinh và ghi 3 split

Mỗi split chia bằng một điều kiện đơn định:

- `random80_20`: `F.rand(42) > 0.8` — mỗi dòng gán ngẫu nhiên theo seed.
- `temporal_global`: `timestamp >= P80(timestamp)` — `percentile_approx(0.8)`, giá trị **xấp xỉ** (relativeError 0.01).
- `leave_one_out`: `row_number() == 1` theo `timestamp desc, movieId asc`.

Sau khi ghi, đọc lại và đếm để xác nhận artifact trên đĩa đúng, không chỉ tin cell không ném exception."""),
    code("""expected_counts = {
    'random80_20': {'train_rows': 19_997_974, 'test_rows': 5_002_121},
    'temporal_global': {'train_rows': 19_999_279, 'test_rows': 5_000_816},
    'leave_one_out': {'train_rows': 24_837_554, 'test_rows': 162_541},
}

split_meta = {}
verify_results = {}

for strategy in split_lib.STRATEGIES:
    started = time.perf_counter()
    marked, meta = split_lib.build_split(ratings, strategy, seed=spark_utils.DEFAULT_SEED)
    meta.update(split_lib.materialize_split(marked, strategy, spark_utils.SPLITS_DIR, num_partitions=8))
    meta['build_seconds'] = round(time.perf_counter() - started, 1)

    verify = split_lib.verify_materialized(spark, strategy, spark_utils.SPLITS_DIR, expected_counts[strategy])
    train_df, test_df = split_lib.load_split(strategy, spark_utils.SPLITS_DIR)
    overlap = split_lib.overlap_check(train_df, test_df)
    verify.update(overlap)

    split_meta[strategy] = meta
    verify_results[strategy] = verify

    print(f'--- {strategy} ---')
    print(' ', meta['description'])
    print(f"  train={verify['train_rows']:,} test={verify['test_rows']:,} "
          f"expected_match={verify['matches_expected']} overlap={overlap['overlapping_rows']}")
    print(f"  train_sha256={verify['train_sha256'][:16]}... test_sha256={verify['test_sha256'][:16]}...")
    run.log('SPLIT_BUILT', strategy=strategy, meta=meta, verify=verify)

    assert verify['matches_expected'], f'{strategy} counts differ from measured baseline: {verify}'
    assert overlap['overlapping_rows'] == 0, f'{strategy} has train/test overlap'

ratings.unpersist()
run.checkpoint(
    'splits_materialized',
    'PASS',
    checks={
        'strategies': list(split_lib.STRATEGIES),
        'all_match_expected': all(v['matches_expected'] for v in verify_results.values()),
        'all_zero_overlap': all(v['overlapping_rows'] == 0 for v in verify_results.values()),
    },
)"""),
    md("""## 5. Bảng tổng hợp

Đọc bảng dưới đây như **mô tả hình dạng dữ liệu**, không phải kết quả. Con số NDCG chỉ xuất hiện từ notebook 06 trở đi."""),
    code("""summary_rows = []
for strategy in split_lib.STRATEGIES:
    v = verify_results[strategy]
    m = split_meta[strategy]
    total = v['train_rows'] + v['test_rows']
    summary_rows.append({
        'strategy': strategy,
        'train_rows': v['train_rows'],
        'test_rows': v['test_rows'],
        'test_pct': round(100.0 * v['test_rows'] / total, 2),
        'threshold_ts': m.get('threshold_ts'),
        'train_bytes': v['train_bytes'],
        'test_bytes': v['test_bytes'],
        'overlap': v['overlapping_rows'],
    })

header = f"{'strategy':<18}{'train':>12}{'test':>12}{'test%':>8}{'MB':>10}{'overlap':>9}"
print(header)
print('-' * len(header))
for row in summary_rows:
    mb = (row['train_bytes'] + row['test_bytes']) / 1e6
    print(f"{row['strategy']:<18}{row['train_rows']:>12,}{row['test_rows']:>12,}"
          f"{row['test_pct']:>8.2f}{mb:>10.1f}{row['overlap']:>9}")

print()
print('Luu y: leave_one_out test chi 1 dong/user -> phuong sai lon nhat trong 3 split.')
print('Luu y: random80_20 test ~20% nhung vi pham thoi gian (xem notebook 05).')
run.log('SPLIT_SUMMARY', rows=summary_rows)"""),
    md("""## 6. Ghi manifest và đóng run

Manifest là nguồn duy nhất cho notebook 05–09 biết split nào tồn tại và checksum của nó."""),
    code("""manifest = {
    'protocol_id': spark_utils.PROTOCOL_ID,
    'seed': spark_utils.DEFAULT_SEED,
    'test_fraction': 0.2,
    'source_parquet': str(parquet_path),
    'source_rows': spark_utils.RATINGS_ROWS,
    'source_sha256_csv': spark_utils.RATINGS_SHA256,
    'splits_dir': str(spark_utils.SPLITS_DIR),
    'strategies': split_meta,
    'verification': verify_results,
    'summary': summary_rows,
    'notes': [
        'leave_one_out tie-break by movieId is deterministic but not real temporal order',
        'temporal_global threshold from percentile_approx (relativeError 0.01), approximate',
    ],
}

output_path = run.run_dir / 'outputs' / 'split_manifest.json'
output_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
reloaded = json.loads(output_path.read_text(encoding='utf-8'))
assert set(reloaded['strategies']) == set(split_lib.STRATEGIES)
assert reloaded['source_rows'] == spark_utils.RATINGS_ROWS

from src.audit.io import dir_size_bytes

total_bytes = dir_size_bytes(spark_utils.SPLITS_DIR)
print('Manifest:', output_path)
print(f'Total split storage: {total_bytes / 1e6:.1f} MB at {spark_utils.SPLITS_DIR}')

run.checkpoint(
    'manifest_saved',
    'PASS',
    checks={'output_readback': True, 'strategies': len(reloaded['strategies']), 'total_bytes': total_bytes},
    note=str(output_path),
)
run.finish('COMPLETED', summary={'strategies': list(split_lib.STRATEGIES), 'manifest': str(output_path), 'total_bytes': total_bytes})
spark_utils.stop_spark(spark)
print('L4 COMPLETE. Next: 05_audit_split_leakage.ipynb')"""),
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

