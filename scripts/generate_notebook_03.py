"""Generate Notebook 03: inspect interaction and timestamp semantics."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "jupyter" / "03_understand_interactions.ipynb"
OUT.parent.mkdir(parents=True, exist_ok=True)

def md(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source.strip("\n").splitlines(keepends=True)}

def code(source):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source.strip("\n").splitlines(keepends=True)}

cells = [
    md("""# 03 — Hiểu interactions trước khi chia tập

**Mục tiêu:** khám phá ratings, thời gian, lịch sử user và popularity bằng Spark. Đây là bước khảo sát, chưa chọn protocol, chưa tạo split, chưa train model.

**Input:** raw `ratings.csv` đã xác minh ở L1; profile L2 phải `COMPLETED`. Notebook chỉ đọc dữ liệu nguồn.

**Kết quả:** các profile aggregate, timestamp tie report, metric-input notes và checkpoints/log theo cell."""),
    md("""## Khái niệm cần nắm

Một dòng `ratings.csv` là một explicit rating: user đã chấm một phim tại Unix timestamp. Điều này khác implicit event như click/watch.

`rating >= 4.0` chỉ là ứng viên relevance rule, không phải quyết định đã chốt. Phải khai báo rule trước khi đánh giá model. Popularity cần tính từ train split sau này, không lấy test/full data để fit baseline.

Timestamp tie có hai dạng cần phân biệt: nhiều interactions cùng giây trong toàn cục, và nhiều interactions của cùng user cùng giây. Dạng thứ hai làm thứ tự tuần tự trong user không xác định chỉ bằng timestamp. Không tự phá tie bằng `movieId` rồi gọi thứ tự đó là thời gian thật.

Spark transformations thường lazy; `count`, `collect`, `first` kích hoạt jobs. Các bảng dưới đây đều đã được gom nhóm, chỉ lấy thống kê/tối đa 20 hàng về driver; không collect ratings thô."""),
    md("""## 1. Nạp input và kiểm tra L1/L2

Nếu manifest L2 gần nhất chưa hoàn tất hoặc không khớp dataset SHA-256, dừng. Spark session dùng `local[4]`: bốn worker threads trên một máy, không phải cluster."""),
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
expected_sha256 = '9c85525758597dca76e8d98cebb9c13e018c2317b09a0878b6d383179526e385'
run = NotebookRun(project_root, '03_understand_interactions', metadata={'input': str(ratings_path), 'read_only': True, 'purpose': 'exploratory_profile_not_split'})
run.attach_ipython(get_ipython())

runs_dir = project_root / 'runs'
l1_candidates = sorted(runs_dir.glob('*/dataset_manifest.json'), key=lambda p: p.stat().st_mtime, reverse=True)
l2_candidates = sorted((p for p in runs_dir.glob('*/manifest.json') if json.loads(p.read_text(encoding='utf-8')).get('notebook_id') == '02_profile_ratings_with_spark'), key=lambda p: p.stat().st_mtime, reverse=True)
assert ratings_path.is_file(), f'ratings.csv missing: {ratings_path}'
assert l1_candidates and json.loads(l1_candidates[0].read_text(encoding='utf-8'))['ratings_sha256'] == expected_sha256, 'Verified L1 dataset manifest missing or hash mismatch.'
assert l2_candidates and json.loads(l2_candidates[0].read_text(encoding='utf-8')).get('status') == 'COMPLETED', 'Notebook 02 L2 run not COMPLETED.'
l2_manifest_path = l2_candidates[0]
print('Input:', ratings_path)
print('Verified L1:', l1_candidates[0])
print('Completed L2:', l2_manifest_path)
print('Run ID:', run.run_id)
run.checkpoint('verified_prerequisites', 'PASS', checks={'ratings_exists': True, 'l1_sha256_matches': True, 'l2_completed': True}, note=f'L2 manifest: {l2_manifest_path}')

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, IntegerType, FloatType, LongType
from pyspark.sql import functions as F

os.environ['PYSPARK_PYTHON'] = sys.executable
spark = (SparkSession.builder.appName('RecSysNotebook03Interactions')
         .master('local[4]')
         .config('spark.driver.memory', '6g')
         .config('spark.sql.shuffle.partitions', '8')
         .config('spark.ui.showConsoleProgress', 'false')
         .config('spark.sql.session.timeZone', 'UTC')
         .getOrCreate())
spark.sparkContext.setLogLevel('ERROR')
schema = StructType([
    StructField('userId', IntegerType(), nullable=False),
    StructField('movieId', IntegerType(), nullable=False),
    StructField('rating', FloatType(), nullable=False),
    StructField('timestamp', LongType(), nullable=False),
])
ratings = spark.read.option('header', True).schema(schema).csv(str(ratings_path))
print('Spark:', spark.version, '| master:', spark.sparkContext.master)
print('Schema:')
ratings.printSchema()
run.checkpoint('spark_input_ready', 'PASS', checks={'spark_version': spark.version, 'master': spark.sparkContext.master, 'schema': ratings.schema.simpleString()})"""),
    md("""## 2. Explicit ratings and candidate relevance thresholds

Rating distribution shows how much data each possible threshold retains. We report `>= 3.5` and `>= 4.0` as sensitivity context only; neither is silently selected as final relevance. Catalog universe and candidate filtering still need a written protocol."""),
    code("""started = time.perf_counter()
rating_counts = {row['rating']: row['count'] for row in ratings.groupBy('rating').count().orderBy('rating').collect()}
threshold_counts = ratings.agg(
    F.count('*').alias('rows'),
    F.sum(F.when(F.col('rating') >= 3.5, 1).otherwise(0)).alias('rating_ge_3_5'),
    F.sum(F.when(F.col('rating') >= 4.0, 1).otherwise(0)).alias('rating_ge_4_0'),
).first().asDict()
threshold_counts['rating_ge_3_5_fraction'] = round(threshold_counts['rating_ge_3_5'] / threshold_counts['rows'], 4)
threshold_counts['rating_ge_4_0_fraction'] = round(threshold_counts['rating_ge_4_0'] / threshold_counts['rows'], 4)
print('Rating distribution:', json.dumps(rating_counts, indent=2))
print('Threshold counts (exploratory):', json.dumps(threshold_counts, indent=2))
run.log('RATING_DISTRIBUTION', distribution=rating_counts, threshold_counts=threshold_counts, elapsed_seconds=round(time.perf_counter() - started, 2))
run.checkpoint('rating_relevance_profile', 'PASS', checks={'rating_levels': len(rating_counts), 'rows_match_l2': threshold_counts['rows'] == 25000095}, note='Thresholds are descriptive only; relevance policy remains undecided.')"""),
    md("""## 3. User history lengths

Group ratings by user, then summarize interactions per user. `approxQuantile(..., relativeError=0.01)` returns approximate quantiles; do not describe them as exact percentiles. These values help describe sparse histories and later eligibility choices; they do not yet define which users enter evaluation."""),
    code("""started = time.perf_counter()
user_history = ratings.groupBy('userId').agg(F.count('*').alias('interaction_count'))
user_history_summary = user_history.agg(
    F.count('*').alias('users'), F.min('interaction_count').alias('min_interactions'),
    F.max('interaction_count').alias('max_interactions'), F.avg('interaction_count').alias('mean_interactions'),
).first().asDict()
user_history_quantiles = user_history.approxQuantile('interaction_count', [0.0, 0.25, 0.5, 0.75, 0.9, 0.99, 1.0], 0.01)
print('User history summary:', json.dumps(user_history_summary, indent=2))
print('Approx quantiles (relativeError=0.01) [min, p25, p50, p75, p90, p99, max]:', user_history_quantiles)
run.log('USER_HISTORY_PROFILE', summary=user_history_summary, quantiles=user_history_quantiles, elapsed_seconds=round(time.perf_counter() - started, 2))
assert user_history_summary['users'] == 162541
run.checkpoint('user_history_profile', 'PASS', checks={'users_match_l2': user_history_summary['users'] == 162541, 'quantile_count': len(user_history_quantiles)})"""),
    md("""## 4. Item popularity distribution

Count ratings per item. Popularity here is descriptive full-dataset profiling only. A recommendation baseline must recompute counts on training data after split to prevent test leakage."""),
    code("""started = time.perf_counter()
item_counts = ratings.groupBy('movieId').agg(F.count('*').alias('rating_count'))
item_summary = item_counts.agg(
    F.count('*').alias('rated_items'), F.min('rating_count').alias('min_ratings'),
    F.max('rating_count').alias('max_ratings'), F.avg('rating_count').alias('mean_ratings'),
).first().asDict()
item_quantiles = item_counts.approxQuantile('rating_count', [0.0, 0.25, 0.5, 0.75, 0.9, 0.99, 1.0], 0.01)
top_items = [row.asDict() for row in item_counts.orderBy(F.desc('rating_count'), F.asc('movieId')).limit(20).collect()]
print('Rated item summary:', json.dumps(item_summary, indent=2))
print('Approx item-count quantiles (relativeError=0.01) [min, p25, p50, p75, p90, p99, max]:', item_quantiles)
print('Top 20 items by rating count (descriptive only):')
for row in top_items:
    print(row)
run.log('ITEM_POPULARITY_PROFILE', summary=item_summary, quantiles=item_quantiles, top_items=top_items, elapsed_seconds=round(time.perf_counter() - started, 2))
assert item_summary['rated_items'] == 59047
run.checkpoint('item_popularity_profile', 'PASS', checks={'rated_items_match_l2': item_summary['rated_items'] == 59047, 'top_items_limit': len(top_items) == 20})"""),
    md("""## 5. Duplicate user-item pairs

MovieLens commonly has one rating per user-item pair, but verify this file. Count repeated pairs and extra rows before deciding handling. Repeated pair could mean rating update or duplicate; do not drop or collapse without protocol decision."""),
    code("""started = time.perf_counter()
user_item_counts = ratings.groupBy('userId', 'movieId').agg(F.count('*').alias('events_per_pair'))
duplicate_pairs = user_item_counts.filter(F.col('events_per_pair') > 1)
duplicate_summary = duplicate_pairs.agg(
    F.count('*').alias('duplicate_user_item_pairs'),
    F.sum('events_per_pair').alias('rows_in_duplicate_pairs'),
    F.sum(F.col('events_per_pair') - 1).alias('extra_rows_beyond_one_per_pair'),
    F.max('events_per_pair').alias('max_events_per_pair'),
).first().asDict()
if duplicate_summary['duplicate_user_item_pairs'] == 0:
    duplicate_summary.update(rows_in_duplicate_pairs=0, extra_rows_beyond_one_per_pair=0, max_events_per_pair=0)
top_duplicate_pairs = [row.asDict() for row in duplicate_pairs.orderBy(F.desc('events_per_pair'), F.asc('userId'), F.asc('movieId')).limit(10).collect()]
duplicate_summary['top_examples'] = top_duplicate_pairs
print('Duplicate user-item summary:', json.dumps(duplicate_summary, indent=2))
run.log('DUPLICATE_USER_ITEM_PAIRS', summary=duplicate_summary, elapsed_seconds=round(time.perf_counter() - started, 2))
run.checkpoint('duplicate_pair_profile', 'PASS', checks={'duplicate_pair_count_nonnegative': duplicate_summary['duplicate_user_item_pairs'] >= 0, 'extra_rows_nonnegative': duplicate_summary['extra_rows_beyond_one_per_pair'] >= 0})"""),
    md("""## 6. Timestamp ties

Global same-second timestamps can complicate a global temporal cutoff. Per-user same-second timestamps are more important for sequential leave-one-out: timestamp alone cannot determine which item came first. Count both kinds; do not invent ordering."""),
    code("""started = time.perf_counter()
global_time_counts = ratings.groupBy('timestamp').agg(F.count('*').alias('events_at_timestamp'))
global_tie_groups = global_time_counts.filter(F.col('events_at_timestamp') > 1)
global_tie_summary = global_tie_groups.agg(
    F.count('*').alias('global_tied_timestamps'),
    F.sum('events_at_timestamp').alias('interactions_in_global_tied_timestamps'),
    F.max('events_at_timestamp').alias('largest_global_tie_group'),
).first().asDict()
user_time_counts = ratings.groupBy('userId', 'timestamp').agg(F.count('*').alias('events_at_timestamp'))
tie_groups = user_time_counts.filter(F.col('events_at_timestamp') > 1)
tie_summary = tie_groups.agg(
    F.count('*').alias('tied_user_timestamp_groups'),
    F.sum('events_at_timestamp').alias('interactions_in_tied_groups'),
    F.max('events_at_timestamp').alias('largest_tie_group'),
).first().asDict()
users_with_ties = tie_groups.select('userId').distinct().count()
top_ties = [row.asDict() for row in tie_groups.orderBy(F.desc('events_at_timestamp'), F.asc('userId'), F.asc('timestamp')).limit(10).collect()]
tie_summary.update(global_tie_summary)
tie_summary['users_with_ties'] = users_with_ties
tie_summary['top_examples'] = top_ties
print('Global timestamp ties:', json.dumps(global_tie_summary, indent=2))
print('Per-user timestamp ties:', json.dumps(tie_summary, indent=2))
run.log('TIMESTAMP_TIES', summary=tie_summary, elapsed_seconds=round(time.perf_counter() - started, 2))
run.checkpoint('timestamp_tie_profile', 'PASS', checks={'global_tie_groups_nonnegative': global_tie_summary['global_tied_timestamps'] >= 0, 'user_tie_groups_nonnegative': tie_summary['tied_user_timestamp_groups'] >= 0, 'example_limit': len(top_ties) <= 10}, note='A tie requires a declared policy before temporal/sequential split; no ordering chosen here.')"""),
    md("""## 6. Ghi nhận kết quả và câu hỏi chưa chốt

`59,047` là số phim có rating; catalog README nêu `62,423` phim. Đây là hai tập khác nhau, nên coverage phải khai báo mẫu số.

Notebook lưu aggregate JSON và câu hỏi thiết kế. Các giá trị dưới đây **không phải lựa chọn mặc định**: relevance threshold, duplicate interaction handling, timestamp tie policy, eligibility, candidate universe và split protocol đều cần căn cứ đề tài/rubric."""),
    code("""analysis = {
    'input_rows': threshold_counts['rows'],
    'explicit_rating_distribution': rating_counts,
    'candidate_relevance_threshold_counts': {
        'rating_ge_3_5': threshold_counts['rating_ge_3_5'],
        'rating_ge_4_0': threshold_counts['rating_ge_4_0'],
    },
    'user_history_summary': user_history_summary,
    'user_history_quantiles_min_p25_p50_p75_p90_p99_max': user_history_quantiles,
    'rated_item_summary': item_summary,
    'rated_item_quantiles_min_p25_p50_p75_p90_p99_max': item_quantiles,
    'duplicate_user_item_profile': duplicate_summary,
    'per_user_timestamp_ties': tie_summary,
    'catalog_movies_from_verified_readme': 62423,
    'rated_items_from_l2': 59047,
    'open_protocol_decisions': [
        'relevance threshold and rating-to-positive interpretation',
        'duplicate (userId, movieId) interaction handling',
        'global and per-user timestamp tie policy',
        'eligible-user and evaluation-cohort rules',
        'candidate universe and seen-item exclusion',
        'split strategy and temporal cutoff semantics',
    ],
    'decision': 'exploratory_only_no_split_no_model',
}
output_path = run.run_dir / 'outputs' / 'interaction_profile.json'
output_path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
reloaded = json.loads(output_path.read_text(encoding='utf-8'))
assert reloaded['decision'] == 'exploratory_only_no_split_no_model'
assert len(reloaded['open_protocol_decisions']) == 6
run.checkpoint('interaction_profile_saved', 'PASS', checks={'output_readback': True, 'open_decisions_recorded': len(reloaded['open_protocol_decisions']), 'no_split_or_model': True}, note=str(output_path))
run.finish('COMPLETED', summary={'ratings_rows': threshold_counts['rows'], 'rated_items': item_summary['rated_items'], 'tie_groups': tie_summary['tied_user_timestamp_groups'], 'profile_path': str(output_path), 'decision': analysis['decision']})
print('L3 exploratory profile saved:', output_path)
print('No relevance, eligibility, tie-break, or split protocol selected.')
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

