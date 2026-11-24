# Architecture — Kiến trúc pipeline đánh giá hệ thống gợi ý

**Project:** `D:\Master Exers\Big Data\Recomendation_System`
**Cập nhật:** 2026-11-20 (bổ sung §0 Novelty/Diversity/Friedman; rerun 06/08/10/11/13)

> Architecture contains two isolated tracks: Paper 01 reproduction and project controlled experiment.
>
> **Từ 2026-11-15:** pipeline project có **hai đường thực thi** — notebook-first (`notebooks/jupyter/04`–`13` + `src/audit/*`, đã PASS gate; rerun 2026-11-20 thêm Novelty/Diversity + Friedman) và script-driven (`scripts/04_audit_spark.py`, giữ làm tham chiếu và nguồn số 2026-11-04). Cùng protocol, khác đường chọn tập user đánh giá → chênh NDCG ≤ 0,0053. Xem `Metrics.md` §4.5. Rerun 2026-11-20: 06/08/10/11/13 ghi `novelty10`/`diversity10`; 09 ghi `friedman`. Xem §4.12.

---

## 0. Đường thực thi notebook-first (bổ sung 2026-11-15; cập nhật 2026-11-20)

Script đơn khối `04_audit_spark.py` chạy 40–60 phút và chỉ in kết quả cuối — không quan sát được bước nào hỏng. Notebook 04–13 chia nhỏ theo gate, mỗi bước ghi checkpoint.

```
04_build_splits          3 split → D:\recsys_data\splits\<strategy>\{train,test}\*.parquet
   │                     verify_materialized + overlap_check → L4 PASS
05_audit_split_leakage   temporal_violation (toàn cục + user), unseen_item, cold_start → L5 PASS
   │
   ├── 06_mostpopular_baseline   Popularity top-K, NDCG/Hit/coverage/Gini/bias → L6a PASS
   │                             (rerun 2026-11-18: peruser_ndcg_{split}.npz → nguyên liệu L12;
   │                              rerun 2026-11-20: novelty10/diversity10)
   ├── 07_ndcg_manual_check      5 fixture NDCG tính tay, tol 1e-12          → L6b PASS
   │                             (từ 2026-11-20: 15 fixture, thêm novelty/diversity/serendipity)
   ├── 08_als_implicit           ALS implicit + numpy top-K + seen_exclusion  → L6c PASS
   │                             (rerun 2026-11-20: novelty10/diversity10)
   ├── 10_random_baseline        Random sàn (catalog uniform, seen excluded) → L10 PASS
   │                             (rerun 2026-11-20: novelty10/diversity10)
   ├── 11_itemknn_baseline       ItemKNN cosine k=100, scipy sparse (min_co=2) → L11 PASS
   │                             (rerun 2026-11-20: novelty10/diversity10)
   └── 13_sasrec_ce              SASRec+CE, GPU local, eval subset user      → đã chạy 3 split
                                  (rerun 2026-11-20: novelty10/diversity10)
                │
                ▼
09_compare_and_reversal   comparison.json (5 model), reversal_table.csv, rq1_answer.md → L7 PASS
                          (rerun 2026-11-20: thêm key `friedman`; Nemenyi KHÔNG chạy)
12_paired_stats           đọc peruser_ndcg_*.npz, không chạy lại pipeline → Wilcoxon + 95% CI
                          + rank-biserial r, 20 cặp (5 model) → L12 PASS
```

| Nguyên tắc | Lý do |
|---|---|
| Code dùng lại nằm ở `src/audit/*`, notebook chỉ gọi + in bảng | cell notebook đọc được, không ẩn logic trong 800 dòng |
| Mỗi notebook một process (`scripts/run_notebook.py`) | tránh NPE `PartitionKeyedAccumulator.byPartition()` khi reuse Spark session |
| Split materialize xuống đĩa một lần | 05/06/08 đọc cùng một file; không tính lại `F.rand` |
| Mọi assert ghi vào `runs/<run_id>/checkpoints/<step>.json` | truy vết số về từng bước |

**Phần cứng theo tầng.** 4 baseline chạy **CPU**: PySpark 4.2.0 trên Windows, `local[4]` dùng 4 core; ItemKNN dùng scipy sparse trên driver. Tầng SOTA SASRec+CE chạy **GPU local** (RTX 4050 Laptop 6 GB, CUDA 12.6) qua notebook 13 — **vì vậy cấm so sánh runtime giữa SASRec và 4 baseline** (khác thiết bị, vi phạm yêu cầu so sánh công bằng của Bài giảng 04); `sasrec_summary.json` mang field `hardware.note = "KHONG so sanh runtime"`. `netlib-blas: dlopen(libopenblas.dll) failed` là cảnh báo lành tính — numpy fallback reference BLAS, chỉ chậm hơn.

---

## 1. Tổng quan

Pipeline project là **offline batch pipeline**, không service online. Paper 01 reproduction chạy ngoài pipeline project, trong repository/environment riêng.

```text
TRACK A — PAPER 01 REPRODUCTION
official repository + paper protocol
  -> pinned commit + isolated environment
  -> paper dataset/split/models/metrics
  -> smoke test -> reproduction report

TRACK B — PROJECT CONTROLLED EXPERIMENT
MovieLens-25M project preprocessing
  -> 3 project splits
  -> Random, MostPopular, ALS, ItemKNN + SASRec+CE (5 baseline đã đăng kí)
  -> leakage + popularity bias + runtime
  -> Spark/HDFS/MongoDB/R/Streamlit

Không nối output Track A vào MongoDB project nếu chưa có mapping protocol.
```

### Ranh giới model

Paper 01: BPR, NeuMF, SASRec, LightGCN. Project (Track B): cả 5 baseline đăng kí đã chạy — Random, MostPopular (sàn) + ALS, ItemKNN cosine (kinh điển) + SASRec+CE (SOTA, GPU local, tuning_budget=0, eval subset user). ALS result không được trình bày là Paper 01 reproduction.

### Ranh giới dữ liệu

Paper 01 dùng MovieLens subset theo paper; project dùng full MovieLens-25M. Hai dataset phải lưu checksum và report riêng.

### Data lineage

`paper_run_id` dành cho reproduction report. `protocol_id=project_protocol_v1` dành cho results/MongoDB/reports project. Không overwrite project result bằng Paper artifact.

### 1.1 Sơ đồ 4 tầng

```
┌─ TẦNG 1 ─ INGEST ─────────────────────────────────────────────────────┐
│  MovieLens ml-25m (ratings.csv 25.000.095 dòng, 678 MB)             │
│      │  scripts/01_ml_to_parquet.py (pyarrow streaming, 26s)         │
│      ▼                                                            │
│  D:\recsys_data\parquet\ratings\part-00000.parquet                  │
│  (175.961.682 B, 31 row-groups)                                     │
└──────────────────────────────────────────────────────────────────────┘
                              │
┌─ TẦNG 2 ─ BIG DATA (HDFS + MapReduce) ──────────────────────────────┐
│  hdfs://namenode:9000/recsys/ratings/part-00000.parquet             │
│      │                                                            │
│      │  MapReduce bằng JAVA (Hadoop 3.2.1, YARN) — S2:              │
│      │    Mapper  : đếm (movieId, year) → (pop, year)              │
│      │    Reducer : cộng dồn → popularity theo năm                  │
│      │    → HDFS out: /recsys/out/popularity_by_year/                │
│      ▼                                                            │
│  /recsys/out/  (coverage, long-tail threshold)                     │
└──────────────────────────────────────────────────────────────────────┘
                              │
┌─ TẦNG 3 ─ SPARK (local[4]) ─────────────────────────────────────────┐
│  S3  sinh 3 split:  random80_20 | temporal_global | leave_one_out  │
│      └─ materialize → D:\recsys_data\splits\        (notebook 04)   │
│  S4  audit tầng 1: temporal_violation, unseen_item, cold_start     │
│      (notebook 05)                                                  │
│  S5  baseline Popularity (Spark SQL) → NDCG@10, DCG@10              │
│      (notebook 06)                                                  │
│  S6  ALS implicit (rank 16, maxIter 8, alpha 10, seed 42)          │
│      → userFactors/itemFactors              (notebook 08)           │
│  S7  top-K bằng numpy: U[s:e] @ V.T → argpartition (chunk 2000)   │
│  S8  bias metrics: coverage, long-tail, Gini, popularity_bias_ratio│
│  S8a Random baseline: uniform từ catalog train, seen excluded       │
│      (notebook 10)                                                  │
│  S8b so sánh 5 mô hình × 3 split, kiểm tra đảo chiều (notebook 09)  │
│  S8c Novelty@10 / Diversity@10 từ top-K (06/08/10/11/13, mới 20/11) │
│  S8d SASRec+CE GPU local, eval subset user         (notebook 13)    │
└──────────────────────────────────────────────────────────────────────┘
                              │
┌─ TẦNG 4 ─ LƯU TRỮ & TRỰC QUAN ──────────────────────────────────────┐
│  S9  MongoDB: collection `audit_metrics` (split × model)           │
│      + collection `item_profile` (popularity, year, long-tail flag) │
│  S9b runs/<run_id>/: manifest + checkpoints + outputs + figures    │
│  S10 R 4.6.2 (không SparkR): thống kê mô tả, kiểm định, biểu đồ    │
│  S11 Streamlit: dashboard đọc MongoDB                             │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. Tầng 1 — Ingest

| Bước             | Công cụ                                                     | Ghi chú                                                                                |
| ------------------ | ------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| 1.1 Tải           | `https://files.grouplens.org/datasets/movielens/ml-25m.zip` | 261.978.986 B                                                                           |
| 1.2 Giải nén     | `D:\recsys_data\raw\ml-25m\`                                | 8 file                                                                                  |
| 1.3 CSV → Parquet | **pyarrow** `pacsv.open_csv` + `pq.ParquetWriter`   | 26s, schema cố định `userId int32, movieId int32, rating float32, timestamp int32` |
| 1.4 Checksum       | SHA-256 file CSV + thư mục parquet                        | `ratings.csv` = `9c855257…26e385` (678.260.987 B); parquet dir = `379d0b2e…9657c` |

**Vì sao pyarrow cho ingest:** `_ml_to_parquet.py` cần stream 678 MB CSV → Parquet với schema cố định, không cần dựng Spark session chỉ để đổi định dạng. pyarrow làm trong 26s.

> **Đã giải quyết 2026-11-15:** `df.write.parquet` trên Windows **chạy được** sau khi đặt `HADOOP_HOME=D:\recsys_data\tools\hadoop` và đặt **cả** `bin\winutils.exe` **lẫn** `bin\hadoop.dll` (prepend `bin` vào `PATH`). Thiếu `winutils.exe` → `hadoop.home.dir are unset`. Có `winutils.exe` mà thiếu `hadoop.dll` → `UnsatisfiedLinkError: NativeIO$Windows.access0`. Cả hai cùng có → đọc/ghi thư mục Parquet đều OK. Đây là cách `materialize_split` ghi 3 split xuống `D:\recsys_data\splits\`. Chi tiết: `MetErrors/io.md`.

---

## 3. Tầng 2 — HDFS + MapReduce

**Mục tiêu:** chứng minh yêu cầu seminar "MapReduce + HDFS" và "MapReduce bằng Python" bằng **pipeline thật**, không phải demo.

### 3.1 Nạp vào HDFS

```bash
docker exec namenode hdfs dfs -mkdir -p /recsys/ratings
docker cp "D:\recsys_data\parquet\ratings\part-00000.parquet" namenode:/tmp/ratings.parquet
docker exec namenode hdfs dfs -put -f /tmp/ratings.parquet /recsys/ratings/part-00000.parquet
```

**Kết quả:** 1 file, 167,8 MiB, 175.961.682 byte (`hdfs dfs -count -q`).

> MapReduce job cần **CSV text** chứ không phải Parquet (MapReduce đọc `TextInputFormat`). Vì vậy `scripts/03_run_mapreduce.sh` nạp thêm `/recsys/ratings_csv/part-00000.csv` (646,8 MB) từ `/tmp/ratings.csv` trong container. Parquet vẫn giữ vai trò nguồn cho Spark.

### 3.2 Job MapReduce (Java — `scripts/02_PopularityByYear.java`)

**Vì sao Java chứ không phải Python/mrjob:** container `namenode` (image `bde2020/hadoop:2.0.0-hadoop3.2.1-java8`) **không có Python** (`python3: command not found`) và không có `pip`. Để đáp ứng đúng yêu cầu seminar "MapReduce + HDFS", job được viết bằng Java và biên dịch bằng `javac` có sẵn trong container (OpenJDK 1.8.0_232).

```java
public static class PopMapper extends Mapper<Object, Text, Text, IntWritable> {
  protected void map(Object key, Text value, Context context) {
    String[] p = value.toString().split(",");     // userId,movieId,rating,timestamp
    int movieId = Integer.parseInt(p[1].trim());
    long ts     = Long.parseLong(p[3].trim());
    int year    = Integer.parseInt(SDF.format(new Date(ts * 1000L)));   // SDF: UTC
    outKey.set(movieId + "," + year);
    context.write(outKey, outVal);                 // IntWritable(1)
  }
}

public static class PopReducer extends Reducer<Text, IntWritable, Text, IntWritable> {
  protected void reduce(Text key, Iterable<IntWritable> values, Context context) {
    int sum = 0;
    for (IntWritable v : values) sum += v.get();
    context.write(key, new IntWritable(sum));
  }
}
```

**Chạy:**

```bash
docker cp D:\recsys_data\raw\ml-25m\ratings.csv namenode:/tmp/ratings.csv
docker cp scripts\02_PopularityByYear.java namenode:/tmp/PopularityByYear.java
docker exec namenode bash /tmp/run_mr.sh
```

Output: `/recsys/out/popularity_by_year/part-r-00000` → **323.737 dòng** (key `movieId,year`).

**2 lỗi đã gặp và cách sửa (xem `Environment.md` §5):**

| Lỗi                                                                             | Nguyên nhân                                                           | Sửa                                                                                                                              |
| -------------------------------------------------------------------------------- | ----------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `Type mismatch in value from map: expected LongWritable, received IntWritable` | `setOutputValueClass` = output reducer nhưng map ghi `IntWritable` | Thống nhất **cả 3** (map, combiner, reducer) dùng `IntWritable` + thêm `setMapOutputValueClass(IntWritable.class)` |
| `wrong value class: LongWritable is not IntWritable`                           | Combiner ghi `LongWritable`, reducer input là `IntWritable`        | Combiner dùng `IntWritable`                                                                                                    |

### 3.3 Kiểm chứng tương đương (Gate G3) — ĐÃ CHẠY, PASS

Bắt buộc: kết quả MapReduce phải **khớp tuyệt đối** kết quả Spark `groupBy("movieId","year").count()` trên cùng tập → chứng minh 2 đường xử lý cho cùng kết quả (điểm báo cáo rất tốt cho môn Big Data).

Script: `scripts/08_crosscheck_g3.py` → `results/g3_crosscheck.json`.

| Chỉ số                       | Kết quả                               |
| ------------------------------ | --------------------------------------- |
| MapReduce rows                 | 323.737                                 |
| Spark SQL rows                 | 323.737                                 |
| Union keys                     | 323.737                                 |
| **Exact match**          | **323.737 / 323.737 = 100,0000%** |
| Tổng tương tác (MR)        | 25.000.095                              |
| Tổng tương tác (Spark)     | 25.000.095                              |
| Tổng tương tác (kỳ vọng) | 25.000.095                              |
| **gate_G3_passed**       | ✅ **true**                       |

> **Bẫy timezone đã ghi nhận:** MapReduce dùng `SimpleDateFormat` với **UTC**, Spark mặc định `from_unixtime` theo **local (UTC+7)** → lệch 24.778/323.775 key (7,65%). Phải set `.config("spark.sql.session.timeZone", "UTC")`. Đây là loại lỗi âm thầm mà chỉ phát hiện được khi có đối chiếu số — lý do G3 là bắt buộc, không phải thủ tục.

## 4. Tầng 3 — Spark

### 4.1 Sinh split

| Tên                | Mã Spark                                                                                                   |
| ------------------- | ----------------------------------------------------------------------------------------------------------- |
| `random80_20`     | `df.withColumn("is_test", F.rand(42) > F.lit(0.8))`                                                       |
| `temporal_global` | `df.withColumn("is_test", F.col("timestamp") >= F.lit(THR))`, `THR = percentile_approx(timestamp, 0.8)` |
| `leave_one_out`   | `Window.partitionBy("userId").orderBy(timestamp.desc(), movieId.asc())` → `rn == 1`                    |

### 4.2 Audit tầng 1 (Spark SQL thuần)

```python
viol  = test.filter(F.col("timestamp") < train_max_ts).count()
unseen = test.join(broadcast(train.select("movieId").distinct()), "movieId", "left_anti").count()
cold   = test.join(broadcast(train.select("userId").distinct()), "userId", "left_anti").count()
elig   = train.groupBy("userId").count().filter(F.col("count") >= 5).select("userId")
```

### 4.3 ALS implicit + top-K numpy

> **Phải là `implicitPrefs=True`.** ALS explicit xếp hạng theo sai số dự đoán rating → phim user chấm 5,0 mà mô hình đoán 3,2 vẫn bị đẩy xuống cuối → NDCG ≈ 0. Sai phương pháp cho đánh giá top-N. Xem `Metrics.md` §2.0.

```python
als = ALS(userCol="userId", itemCol="movieId", ratingCol="rating",
          rank=16, maxIter=8, regParam=0.05, implicitPrefs=True, alpha=10.0,
          coldStartStrategy="drop", seed=42)
m = als.fit(train_full)                                           # FULL 162.541 user (run 2026-11-17); subsample 30k là phương án lịch sử run 15/11
U = np.array([r["features"] for r in m.userFactors.collect()])    # (n_user, 16)
V = np.array([r["features"] for r in m.itemFactors.collect()])    # (n_item, 16)

for s in range(0, len(U), 2000):          # chunk để không OOM
    sc = U[s:s+2000] @ V.T
    # mask item user đã xem -> -inf
    # np.argpartition(-row, 10)[:10] -> top-10
```

**Vì sao không `recommendForAllUsers`:** hàm này tạo cartesian 162.541 × 59.047 ≈ 9,6 tỷ cặp → OOM. Cách numpy chunk 2.000 user cho **cùng kết quả toán học** (top-K theo `U·V`) nhưng kiểm soát được bộ nhớ. Notebook 08 assert `seen_exclusion` để chắc item đã xem không lọt vào top-K.

### 4.4 Cấu hình Spark bắt buộc

```python
.config("spark.sql.shuffle.partitions", "8")
.config("spark.driver.memory", "8g")
.config("spark.local.dir", r"D:\recsys_data\spark_tmp")   # KHÔNG để mặc định trên C
.config("spark.ui.showConsoleProgress", "false")
.config("spark.sql.session.timeZone", "UTC")
```

---

## 5. Tầng 4 — Lưu trữ & trực quan

### 5.1 MongoDB

| Collection          | Schema                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Nguồn                                                     |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------- |
| `audit_metrics`   | **42 field** đầy đủ: `{split, model, ndcg10, dcg10, hit_rate10, catalog_coverage, longtail_coverage, gini_exposure, avg_pop_rec, avg_pop_all, popularity_bias_ratio, train_rows, test_rows, train_max_ts, train_max_ts_iso, test_min_ts, test_min_ts_iso, temporal_violation_global, temporal_violation_global_pct, temporal_violation_user, temporal_violation_user_pct, unseen_item_rows, unseen_item_pct, coldstart_user_rows, eval_users, eval_test_rows, eval_relevant_users, test_relevant_eval_rows, relevance_threshold, min_train_threshold, seed, spark_version, dataset, run_at, + tham số ALS}` | `scripts/05_store_mongodb.py` ← `D:\recsys_data\poc\poc6_*.json` (đường A) |
| `item_profile`    | `{movieId, title, year, genres[]}`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | `movies.csv` (62.423 phim)                               |
| `audit_metrics_r` | schema rút gọn 12 field (bảng chung phục vụ báo cáo R)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | `scripts/06_analysis_r.R`                                |

**Index:** `{split: 1, model: 1}` unique trên `audit_metrics`; `{movieId: 1}` unique trên `item_profile`.

> **Quy tắc 1 nguồn ghi:** `recsys.audit_metrics` **chỉ** do `scripts/05_store_mongodb.py` (Python) ghi. Script R chỉ **đọc** collection này và ghi vào `recsys.audit_metrics_r`. Lý do: R script phiên bản đầu dùng `$drop()` + `$insert()` với schema rút gọn đã **ghi đè mất** 30 field của schema đầy đủ → phá vỡ dashboard. Đã sửa và ghi lại trong `Environment.md`.

### 5.2 R (SparkR chưa dùng — đã ghi rõ giới hạn)

**R 4.6.2** tại `C:\Program Files\R\R-4.6.2`, user library `D:\R-library`. Package: `jsonlite`, `dplyr`, `ggplot2`, `mongolite`, `corrplot`.

Luồng thực tế (`scripts/06_analysis_r.R`):

1. Đọc `D:/recsys_data/poc/poc6_<split>.json` bằng `jsonlite::fromJSON` → 2 data frame (cấp dữ liệu + hiệu quả/bias).
2. Kiểm tra thứ tự mô hình (Spearman) — kết luận **ALS > Popularity ở cả 3 split**.
3. Chuẩn hoá NDCG trong từng split (max = 1) → so sánh **độ lớn tương đối**.
4. Ma trận tương quan 6 tổ hợp (`corrplot`) — bỏ `longtail_coverage` vì bằng 0 ở cả 6 dòng (SD = 0).
5. Đọc MongoDB (`mongolite`) để kiểm tra, ghi bảng chung vào `recsys.audit_metrics_r`.
6. Xuất: 7 PNG vào `reports/figures/`. (Hai CSV `metrics_summary.csv`, `data_level_metrics.csv` đã bị gỡ khỏi repo — số liệu nay lấy từ `runs/<run_id>/outputs/`.)

**Giới hạn đã ghi nhận:** `SparkR` / `sparklyr` **không cài** (cần Spark + R trong cùng môi trường). R hiện đóng vai trò **phân tích + trực quan**, phần xử lý dữ liệu lớn do PySpark đảm nhiệm. Trong báo cáo phải nói rõ giới hạn này.

**Lỗi R đã gặp:**

- `mongo(mongo = MONGO, ...)` → `unused argument` → đúng cú pháp là `mongo(url = MONGO, ...)`.
- `$insert()` không nhận list-of-list → phải truyền **vector chuỗi JSON** (`toJSON(auto_unbox = TRUE, na = "null")`).
- `corrplot()` chưa `library(corrplot)` → `could not find function`.
- `cor()` trên cột hằng số → `the standard deviation is zero` → loại cột `longtail_coverage` khỏi ma trận.

### 5.3 Streamlit — ĐÃ CHẠY

`scripts/07_dashboard.py`, chạy bằng `python -m streamlit run scripts\07_dashboard.py` (đã verify `HTTP 200` + `/_stcore/health → ok`).

- Sidebar: `st.multiselect` lọc theo chiến lược chia tập và mô hình.
- KPI: tổng tương tác, tỷ lệ rò rỉ (toàn cục + tương đối user), số dòng kết quả.
- Bảng 1: chỉ số cấp dữ liệu (train/test, rò rỉ, unseen item, user lạnh, tập đánh giá).
- Bảng 2: NDCG@10, Hit Rate@10, độ phủ danh mục, độ phủ đuôi dài, Gini, tỷ lệ thiên lệch.
- 3 tab biểu đồ: NDCG@10 · thiên lệch phổ biến + Gini · rò rỉ thời gian.
- Hồ sơ phim: tra `recsys.item_profile` theo `movieId`.
- Nguồn: MongoDB đọc trực tiếp (không copy ra CSV trung gian).

**Lưu ý vận hành:** `streamlit` **không có trong PATH** → phải gọi `python -m streamlit`. Nếu port 8501 còn bị chiếm, kill process theo port rồi khởi động lại.

---

## 6. Sơ đồ luồng dữ liệu (data lineage)

```
ratings.csv ──► part-00000.parquet ──► HDFS /recsys/ratings/
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
             random80_20          temporal_global        leave_one_out
                    │                     │                     │
                    └──────────┬──────────┴──────────┬──────────┘
                               ▼                     ▼
                 D:\recsys_data\splits\<split>\   (materialize 735 MB)
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
            MostPopular top-K      ALS implicit → numpy top-K
                    │                     │
                    └──────────┬──────────┘
                               ▼
                audit_metrics (tầng 1) + bias metrics
                               │
                               ▼
              MongoDB → R → Streamlit  |  runs/<run_id>/outputs/
```

**Sau 2026-11-15:** S3 **materialize** split xuống `D:\recsys_data\splits\`; S4 (Popularity) và S3b (ALS) đọc từ đó, **không đọc lại `ratings.csv`**. Nhờ vậy 3 notebook độc lập nhìn thấy đúng cùng một tập train/test — không phụ thuộc `F.rand(42)` được sinh lại.

---

## 7. Điểm kiểm soát chất lượng (quality gate)

| Gate | Điều kiện                                                            | Trạng thái 04/11                       | Hành động nếu fail                   |
| ---- | ----------------------------------------------------------------------- | ---------------------------------------- | ---------------------------------------- |
| G1   | `rows == 25.000.095`                                                  | ✅ pass                                  | dừng, kiểm tra checksum                |
| G2   | `ts_min == 1995-01-09 11:46:49` và `ts_max == 2019-11-21 09:15:03` | ✅ pass                                  | dừng                                    |
| G3   | MapReduce popularity == Spark popularity, **khớp tuyệt đối**  | ✅ **pass 100%** (323.737/323.737) | dừng, sửa job / kiểm tra timezone     |
| G4   | `temporal_violation_global_pct(random) > 95%`                         | ✅ pass (100,0000%)                      | kiểm tra lại định nghĩa split       |
| G5   | `temporal_violation_global_pct(temporal_global) == 0`                 | ✅ pass (0,0000%)                        | kiểm tra threshold                      |
| G6   | NDCG của ALS ≥ NDCG popularity (sanity)                               | ✅ pass (3/3 split)                      | kiểm tra top-K/mask                     |
| G7   | `eval_relevant_users` > 0 ở mọi split (tập đánh giá khả dụng) | ✅ pass (temporal: 6.214 > 0 — số ALS)            | cảnh báo khi so sánh NDCG giữa split |
| G8   | Gap 3 phần nằm trong 200–250 từ                                     | ✅ pass (237 từ)                        | rút gọn `scripts/09_count_gap.py`    |

### 7.1 Gate notebook-first (2026-11-15)

| Gate | Điều kiện | Trạng thái | Run ID |
|---|---|---|:---:|
| L4 | 3 split ghi đĩa, `matches_expected=True`, `overlap=0` | ✅ PASS | `20261115_191009_04_build_splits_2a395f07` |
| L5 | `temporal_violation_global_pct(random) > 95%` và `== 0` với temporal | ✅ PASS (98,9158% user-relative / 0,0000%) | `20261115_192229_05_audit_split_leakage_8e672786` |
| L6a | MostPopular NDCG giảm đơn điệu random → temporal → LOO | ✅ PASS (0,0852 → 0,0455 → 0,0183) | `20261115_192522_06_mostpopular_baseline_c39572de`; rerun `20261118_021147_06_mostpopular_baseline_6d59bb2c` (thêm npz per-user); rerun 2026-11-20 `20261120_004801_06_mostpopular_baseline_cde8a34b` (thêm novelty10/diversity10) |
| L6b | 5 fixture NDCG khớp tính tay, tolerance `1e-12` | ✅ PASS | `20261115_190933_07_ndcg_manual_check_e1cc5714` |
| L6c | ALS ≥ MostPopular cả 3 split + `seen_exclusion` PASS | ✅ PASS (3/3) | `20261115_192654_08_als_implicit_0c1385ff` (FULL: `20261117_185700_08_als_implicit_7be22080`, rerun FULL `20261117_234312_08_als_implicit_da15debf`); rerun 2026-11-20 `20261120_012429_08_als_implicit_73a9947b` (thêm novelty10/diversity10) |
| L10 | Random sàn: NDCG thấp nhất mọi split, `seen_exclusion` PASS, bias ≈ 1 | ✅ PASS (3/3) | `20261118_144717_10_random_baseline_d8644ac1`; rerun 2026-11-20 `20261120_004945_10_random_baseline_dc453187` (thêm novelty10/diversity10) |
| L7 | `reversals_found == 0` hoặc liệt kê rõ cặp đảo chiều | ✅ PASS (0 ở 3/3 cặp so với sàn; `best_model_reversals_found = 2`) | `20261118_151159_09_compare_and_reversal_1e0f72fa` (ghép **5 model**; bản 4 model: `20261118_022749_..._c9482d3f`; rerun 2026-11-20 `20261120_012944_09_compare_and_reversal_21d0811a` (thêm `friedman`) |
| L11 | ItemKNN `seen_exclusion` PASS và NDCG > Random mọi split | ✅ PASS (3/3 seen; `knn_above_random` = true, 893,0× / 156,6× / 461,0× Random) | `20261118_150305_11_itemknn_baseline_0b7511ee` (503 s, scipy sparse driver-bound); rerun 2026-11-20 `20261120_005139_11_itemknn_baseline_979f28e2` |
| L12 | Mọi cặp kiểm định: `n_paired >= 30`, báo đủ p + 95% CI + r | ✅ PASS (**20/20 cặp, 5 model**, min n=6.214; CI không chứa 0 ở 19/20, ngoại lệ ALS-vs-ItemKNN ở LOO p=0,153) | `20261118_151202_12_paired_stats_9b864f59` (bản 12 cặp: `20261118_022320_..._077f538e`) |

> **Rerun 2026-11-20 (Bài 04):** 06/08/10/11/13 ghi `novelty10`/`diversity10` vào `*_summary.json`; 09 ghi key `friedman` vào `comparison.json`. Số + run id: `Metrics.md` §4.12. Serendipity KHÔNG đo; Nemenyi KHÔNG chạy.

> **G7 cảnh báo:** `eval_relevant_users` chênh rất lớn giữa split (158.692 / 6.219 / 96.003 — số của Popularity/Random/ItemKNN; ALS: 158.626 / 6.214 / 95.977). NDCG **không** so cặp được giữa các split. Xem `Drawbacks.md` §3.3.

## 8. Tầng 6 — Kiểm định thống kê (bổ sung 2026-11-04)

Đây là tầng **mới**, nằm sau tầng 5 (MongoDB) và trước khi trích xuất kết luận.

> **Đường notebook-first (2026-11-18):** `notebooks/jupyter/12_paired_stats.ipynb` (gen bằng `scripts/generate_notebook_12.py`) là bản kiểm định chính thức của đề tài — đọc `peruser_ndcg_*.npz` do notebook 06/08/10/11 lưu, chạy **Wilcoxon signed-rank + 95% CI + rank-biserial r** cho từng cặp model trong **cùng một split**, xuất `paired_stats.json` (gate L12). Phần §8 dưới đây là đường script cũ (bootstrap/Kendall trên tập user nhỏ), giữ làm tham chiếu.

### 8.1 Vì sao cần

Các chỉ số ở tầng 1–3 là **một số cho cả tập** → không có phương sai, không kiểm định được.
Muốn trả lời "khác biệt giữa Popularity và ALS có **thật** không, hay chỉ là nhiễu mẫu?"
thì phải có **một giá trị cho mỗi user**.

### 8.2 Thành phần

| Mã  | Thành phần                                         | Công nghệ                        | Script                                 | Trạng thái            |
| ---- | ---------------------------------------------------- | ---------------------------------- | -------------------------------------- | ----------------------- |
| S5.1 | Sinh per-user metrics                                | PySpark 4.2.0 + numpy              | `scripts/11_peruser_ndcg.py`         | ✅ chạy thật, 3 split |
| S5.2 | Bootstrap CI + Wilcoxon + Cohen's dz + Kendall tau-b | numpy (vector hoá) + scipy 1.18.0 | `scripts/12_stats_tests.py`          | ✅ chạy thật, 3 split |
| S5.3 | PRISMA 2020 flow                                     | SVG thuần (không cần Cairo)     | `scripts/13_prisma_flow.py`          | ✅ SVG                  |
| S5.4 | Benchmark Big Data                                   | PySpark + YARN REST                | `scripts/14_perf_benchmark.py`       | ⏸️ script lịch sử — RQ3 hiện lấy từ `fit_seconds`/`total_seconds` trong summary JSON, xem `Implementation/05_Benchmark_...md` |
| S5.5 | Chụp dashboard                                      | Chrome DevTools Protocol           | `scripts/15_screenshot_dashboard.py` | ✅ PNG 1920×1260       |

### 8.3 Sơ đồ luồng (mở rộng)

```
                        ┌──────────────────────────────┐
peruser_ndcg_<split>.npz│ scripts/12_stats_tests.py     │
hoặc peruser_<split>.csv│  • bootstrap CI 95% (10.000)  │
(29.229 / 1.348 /       │  • Wilcoxon signed-rank        │
17.673 user — notebook 08)│ • Cohen's dz, rank-biserial   │
                        │  • Kendall tau-b              │
                        └──────────────┬───────────────┘
                                       ▼
                     runs/<run_id>/outputs/stats_<split>.json
```

> `reports/stats_summary.csv` đã bị gỡ khỏi repo. Số kiểm định nay đọc từ `runs/<run_id>/outputs/` (đường B) hoặc `D:\recsys_data\` (đường A).

### 8.4 Điểm kiểm soát chất lượng (bổ sung)

| Gate | Điều kiện                                                                         | Trạng thái 04/11                                                             | Hành động nếu fail                       |
| ---- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------ | -------------------------------------------- |
| G9   | `n_paired > 0` ở cả 3 split                                                      | ✅ pass (29.337 / 1.363 / 17.704)                                              | kiểm tra `min_train`, ngưỡng liên quan |
| G10  | Metric hằng số **không** được báo "có ý nghĩa"                       | ✅ pass (cờ `constant_metric`)                                              | kiểm tra `n_nonzero == 0`                 |
| G11  | Bootstrap CI phải hẹp hơn khoảng cách hiệu ứng khi kết luận "có ý nghĩa" | ✅ pass (CI không chạm 0)                                                    | kiểm tra lại số lần bootstrap            |
| G12  | Mọi khẳng định về thiên lệch phải kèm `longtail_coverage`                 | ✅ pass (0 ở cả 6 tổ hợp → **không** khẳng định "đã xử lý") | sửa phần diễn giải                       |

---

## 9. Tầng 7 — Tài liệu tham khảo & quy trình rà soát học thuật (2026-11-04)

### 9.1 Tải paper tự động — **chỉ bản nhà xuất bản**

Từ **2026-11-07**, tiêu chí tài liệu là: **chỉ bài đã publish bởi ACM / IEEE / Springer / Elsevier**
(giảng viên PPNCKH không chấp nhận preprint arXiv). Hai script:

- `scripts/10_fetch_papers.py` — phát hiện DOI + lấy PDF open-access (OpenAlex → Unpaywall).
  **Chỉ dùng để dò metadata**, không dùng để lấy bản cuối cho ACM.
- `scripts/16_fetch_publisher_versions.py` — tải **published version** từ `dl.acm.org/doi/pdf/<doi>`
  bằng cookie replay (CDP `Storage.getCookies` + UA Chrome 156 + `cf_clearance` của browser OpenClaw).

Manifest: `docs/References/Papers/_manifest.json` — trường `provenance` ghi rõ venue bản xuất bản.

### 9.2 Trạng thái 13/14 paper (bản nhà xuất bản)

| #  | File                                                                | DOI                            | Venue (Crossref)                                 |
| -- | ------------------------------------------------------------------- | ------------------------------ | ------------------------------------------------ |
| 01 | `01_TOIS2022_DataLeakage_RS_OfflineEvaluation.pdf`                | `10.1145/3569930`            | ACM TOIS 41(3) Art.75                            |
| 02 | `02_TOIS2023_Reproducing_PopularityBias_EvaluationStrategies.pdf` | `10.1145/3637066`            | ACM TORS 2(1) Art.5                              |
| 03 | `03_RecSys2025_TimeToSplit.pdf`                                   | `10.1145/3705328.3748164`    | RecSys '25, 874–883                             |
| 04 | `04_RecSys2026_ConvergentValidity_OfflineEvaluation.pdf`          | `10.1145/3773078.3831818`    | RecSys '26, 410–418                             |
| 05 | `05_TOIS2022_Bias_Debias_Survey.pdf`                              | `10.1145/3564284`            | ACM TOIS 41(3) Art.67                            |
| 06 | `06_UMAI2024_Survey_PopularityBias.pdf`                           | `10.1007/s11257-024-09406-0` | Springer UMAI 34(5)                              |
| 07 | `07_SIGIR2023_FreshLook_EvaluationStandpoint.pdf`                 | `10.1145/3539618.3591931`    | SIGIR '23, 2629–2638                            |
| 08 | `08_RecSys2023_Challenges_OfflineEvaluation.pdf`                  | `10.1145/3604915.3609495`    | RecSys '23 tutorial                              |
| 09 | `09_RecSys2025_InheritedPopularityBias_ColdStart.pdf`             | `10.1145/3705328.3748035`    | RecSys '25                                       |
| 10 | `10_TOIS2023_Relieving_PopularityBias_Interactive.pdf`            | `10.1145/3618107`            | ACM TOIS 42(2) Art.52                            |
| 11 | `11_RecSys2021_QualityMetrics_Consistency.pdf`                    | `10.1145/3460231.3478848`    | RecSys '21, 708–713                             |
| 12 | `12_RecSys2020_DataSplitting_Strategies.pdf`                      | `10.1145/3383313.3418479`    | RecSys '20, 681–686                             |
| 13 | `13_JBigData2019_Elearning_RS_Spark_Hadoop.pdf`                   | `10.1186/s40537-019-0169-4`  | Springer J. Big Data 6(1):2                      |
| 14 | `14_ESWA2023_EvaluationFramework_BigData.pdf`                     | `10.1016/j.eswa.2023.120659` | Elsevier ESWA 231:120659 — **CHƯA TẢI** |

**Kiểm chứng bản thật:** `pypdf` đọc `/Creator`; bản arXiv là `arXiv GenPDF`, bản xuất bản là
`acmart` / `MiKTeX-pdfTeX` / `Acrobat Distiller` / `Springer` + footer bản quyền ACM/Springer.

**Đã loại:** `10.48550/arxiv.2011.07931` (arXiv-only, không có bản tạp chí).

### 9.3 PRISMA

`scripts/13_prisma_flow.py` sinh `docs/Project/Main/report/Big_Data/figures/fig8_prisma_flow.svg`
(1180×760, Times New Roman, 4.619 B). SVG thuần → **không cần** `cairosvg`/native Cairo.

---

## 10. Quy trình tái lập đầy đủ (master)

```powershell
cd "D:\Master Exers\Big Data\Recomendation_System"

# 0. hạ tầng (bật thủ công)
docker start namenode datanode resourcemanager nodemanager historyserver

# A. ĐƯỜNG B — notebook-first (khuyến nghị, quan sát được từng bước)
python scripts\run_notebook.py notebooks\jupyter\00_environment_check.ipynb
python scripts\run_notebook.py notebooks\jupyter\01_verify_dataset.ipynb
python scripts\run_notebook.py notebooks\jupyter\02_profile_ratings_with_spark.ipynb
python scripts\run_notebook.py notebooks\jupyter\03_understand_interactions.ipynb
python scripts\run_notebook.py notebooks\jupyter\04_build_splits.ipynb
python scripts\run_notebook.py notebooks\jupyter\05_audit_split_leakage.ipynb
python scripts\run_notebook.py notebooks\jupyter\06_mostpopular_baseline.ipynb
python scripts\run_notebook.py notebooks\jupyter\07_ndcg_manual_check.ipynb
python scripts\run_notebook.py notebooks\jupyter\08_als_implicit.ipynb
python scripts\run_notebook.py notebooks\jupyter\09_compare_and_reversal.ipynb

# B. ĐƯỜNG A — script (nguồn số 2026-11-04, giữ làm tham chiếu)
python scripts\01_ml_to_parquet.py
bash scripts/run_mr.sh
python scripts\08_crosscheck_g3.py
python scripts\04_audit_spark.py
python scripts\05_store_mongodb.py
python scripts\11_peruser_ndcg.py random80_20
python scripts\11_peruser_ndcg.py temporal_global
python scripts\11_peruser_ndcg.py leave_one_out
python scripts\12_stats_tests.py

# C. Trực quan + tài liệu tham khảo
Rscript scripts\06_analysis_r.R
python scripts\13_prisma_flow.py
python scripts\14_perf_benchmark.py
python -m streamlit run scripts\07_dashboard.py --server.headless true --server.port 8501
python scripts\15_screenshot_dashboard.py
python scripts\10_fetch_papers.py
```

> **Trần thời gian:** mỗi lệnh phải < 30 phút. Bước B (`04_audit_spark.py`) và `11_peruser_ndcg.py` là ứng viên vượt trần nếu gộp — phải tách theo split.
>
> **Không chạy A và B rồi trộn số.** Hai đường cho NDCG chênh ≤ 0,0053 (xem `Metrics.md` §4.5). Chọn một đường, ghi rõ đường nào.
