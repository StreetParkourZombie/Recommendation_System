"""Generate beginner-friendly Notebook 02 for Spark CSV profiling."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "jupyter" / "02_profile_ratings_with_spark.ipynb"
OUT.parent.mkdir(parents=True, exist_ok=True)

def md(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source.strip("\n").splitlines(keepends=True)}

def code(source):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source.strip("\n").splitlines(keepends=True)}

cells = [
    md("""# 02 — Đọc và kiểm tra ratings bằng Spark

**Mục tiêu:** dùng Spark DataFrame đọc raw MovieLens-25M với schema tường minh, đếm interactions và kiểm tra vài quy tắc chất lượng. Không thu thập 25M dòng về pandas/Python.

**Điều kiện trước:** Notebook 00 và 01 đạt. Input `ratings.csv` có SHA-256 đã khóa trong manifest L1.

**Kết quả:** Spark profile JSON, checkpoints và log theo cell."""),
    md("""## Lý thuyết — DataFrame, schema và lazy execution

Spark DataFrame mô tả dữ liệu phân tán. Các phép chọn/cột là transformations; aggregate/count là actions kích hoạt computation. Schema tường minh tránh inferSchema phải quét/đoán kiểu. `count()` đọc toàn bộ CSV một lượt; aggregate một lượt gồm row count, null, min/max sẽ tiết kiệm lượt scan thêm. `first()`/`show()` chỉ lấy vài dòng; không dùng `.collect()` trên toàn bảng."""),
    md("""## 1. Nạp run context và input đã xác minh

Cell này đọc manifest mới nhất của Notebook 01. Nếu không có manifest PASS, dừng để không phân tích dataset chưa xác minh."""),
    code("""from pathlib import Path
import json
import os
import sys
import time

project_root = Path.cwd().resolve()
while project_root != project_root.parent and not (project_root / 'src').is_dir():
    project_root = project_root.parent
sys.path.insert(0, str(project_root))
from src.recsys.notebook_logging import NotebookRun
from IPython import get_ipython

data_dir = Path('D:/recsys_data/raw/ml-25m')
ratings_path = data_dir / 'ratings.csv'
run = NotebookRun(project_root, '02_profile_ratings_with_spark', metadata={'input': str(ratings_path), 'read_only': True})
run.attach_ipython(get_ipython())
prior_manifests = sorted((project_root / 'runs').glob('*/dataset_manifest.json'), key=lambda p: p.stat().st_mtime, reverse=True)
assert prior_manifests, 'Notebook 01 dataset manifest not found; finish L1 first.'
source_manifest_path = prior_manifests[0]
source_manifest = json.loads(source_manifest_path.read_text(encoding='utf-8'))
assert ratings_path.is_file(), f'ratings.csv missing: {ratings_path}'
assert source_manifest['ratings_sha256'] == '9c85525758597dca76e8d98cebb9c13e018c2317b09a0878b6d383179526e385', 'Input hash differs from the verified L1 dataset.'
print('Input:', ratings_path)
print('L1 manifest:', source_manifest_path)
print('Run ID:', run.run_id)
run.checkpoint('verified_input', 'PASS', checks={'ratings_exists': ratings_path.is_file(), 'sha256_matches_l1': True, 'source_manifest': str(source_manifest_path)})"""),
    md("""## 2. Read CSV with explicit schema

MovieLens `ratings.csv` fields are 32-bit IDs, float rating and 64-bit Unix timestamp. Read only the needed columns for this profile. Spark may emit Windows `winutils.exe` warning; only a completed action counts as PASS."""),
    code("""from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, IntegerType, FloatType, LongType
from pyspark.sql import functions as F

os.environ['PYSPARK_PYTHON'] = sys.executable
spark = (SparkSession.builder.appName('RecSysNotebook02Profile')
         .master('local[4]')
         .config('spark.driver.memory', '6g')
         .config('spark.sql.shuffle.partitions', '8')
         .config('spark.ui.showConsoleProgress', 'false')
         .config('spark.sql.session.timeZone', 'UTC')
         .getOrCreate())
spark.sparkContext.setLogLevel('ERROR')
ratings_schema = StructType([
    StructField('userId', IntegerType(), nullable=False),
    StructField('movieId', IntegerType(), nullable=False),
    StructField('rating', FloatType(), nullable=False),
    StructField('timestamp', LongType(), nullable=False),
])
df = spark.read.option('header', True).schema(ratings_schema).csv(str(ratings_path))
print('Spark version:', spark.version)
print('Master:', spark.sparkContext.master)
print('Schema:')
df.printSchema()
print('First 5 rows:')
df.show(5, truncate=False)
run.log('SPARK_READ_CONFIG', spark_version=spark.version, master=spark.sparkContext.master, schema=df.schema.simpleString(), input=str(ratings_path))
run.checkpoint('spark_read', 'PASS', checks={'spark_version': spark.version, 'master': spark.sparkContext.master, 'schema': df.schema.simpleString()})"""),
    md("""## 3. One-pass data quality profile

Aggregate count, null counts, rating range, timestamp range and distinct user/item counts. Distinct counts may be expensive; this is a deliberate full dataset profile and uses Spark aggregation rather than Python collection."""),
    code("""started = time.perf_counter()
profile = df.agg(
    F.count('*').alias('rows'),
    F.sum(F.when(F.col('userId').isNull(), 1).otherwise(0)).alias('null_userId'),
    F.sum(F.when(F.col('movieId').isNull(), 1).otherwise(0)).alias('null_movieId'),
    F.sum(F.when(F.col('rating').isNull(), 1).otherwise(0)).alias('null_rating'),
    F.sum(F.when(F.col('timestamp').isNull(), 1).otherwise(0)).alias('null_timestamp'),
    F.min('rating').alias('min_rating'), F.max('rating').alias('max_rating'),
    F.min('timestamp').alias('min_timestamp'), F.max('timestamp').alias('max_timestamp'),
    F.countDistinct('userId').alias('distinct_users'),
    F.countDistinct('movieId').alias('distinct_items'),
).first().asDict()
profile['elapsed_seconds'] = round(time.perf_counter() - started, 2)
profile['spark_version'] = spark.version
profile['master'] = spark.sparkContext.master
print(json.dumps(profile, indent=2, ensure_ascii=False))
expected_rows = source_manifest['ratings_rows_by_line_count']
quality_checks = {
    'expected_row_count': profile['rows'] == expected_rows == 25000095,
    'no_nulls': all(profile[f'null_{col}'] == 0 for col in ['userId', 'movieId', 'rating', 'timestamp']),
    'rating_range': profile['min_rating'] == 0.5 and profile['max_rating'] == 5.0,
    'timestamp_range_ordered': profile['min_timestamp'] < profile['max_timestamp'],
    'distinct_users_expected': profile['distinct_users'] == 162541,
}
print('Quality checks:', quality_checks)
assert all(quality_checks.values()), 'Spark profile disagrees with source manifest/expected data; inspect before continuing.'
profile_path = run.run_dir / 'outputs' / 'ratings_profile.json'
profile_path.write_text(json.dumps({'profile': profile, 'checks': quality_checks}, ensure_ascii=False, indent=2), encoding='utf-8')
run.checkpoint('ratings_profiled', 'PASS', checks=quality_checks, note=f'Profile saved to {profile_path}')
run.log('RATINGS_PROFILE', profile=profile, quality_checks=quality_checks)
print('Profile saved:', profile_path)"""),
    md("""## 4. Kết luận và tiếp theo

L2 pass nếu count và quality checks đều đúng. `local[4]` nghĩa là tối đa bốn local worker threads trên một máy, không phải cluster. Notebook này không chia split hay huấn luyện mô hình. Notebook tiếp theo giải thích interactions, timestamps và relevance policy trước khi chọn train/test protocol."""),
    code("""run.finish('COMPLETED', summary={'ratings_rows': profile['rows'], 'distinct_users': profile['distinct_users'], 'distinct_items': profile['distinct_items'], 'quality_checks': quality_checks, 'profile_path': str(profile_path)})
print('L2 PASS — Spark schema, count and data quality checks verified.')
spark.stop()"""),
]

for index, cell in enumerate(cells):
    cell['id'] = f'cell-{index + 1:03d}'
    if cell['cell_type'] == 'code':
        compile(''.join(cell['source']), f'notebook-cell-{index + 1}', 'exec')
notebook = {
    'cells': cells,
    'metadata': {'kernelspec': {'display_name': 'Python 3.14 (BigData RecSys .venv)', 'language': 'python', 'name': 'recsys-project-venv'}, 'language_info': {'name': 'python'}},
    'nbformat': 4,
    'nbformat_minor': 5,
}
OUT.write_text(json.dumps(notebook, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'Created {OUT} with {len(cells)} cells; all code cells compile')

