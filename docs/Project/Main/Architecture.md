# Architecture — Kiến trúc pipeline đánh giá hệ thống gợi ý

**Project:** `D:\Master Exers\Big Data\Recomendation_System`
**Cập nhật:** 2026-11-04

---

## 1. Tổng quan

Pipeline **4 tầng, chạy tuần tự, offline batch**, không service online:

```
┌─ TẦNG 1 ─ INGEST ─────────────────────────────────────────────────────┐
│  MovieLens ml-25m (ratings.csv 25.000.095 dòng, 678 MB)             │
│      │  _ml_to_parquet.py (pyarrow streaming, 26s)                  │
│      ▼                                                            │
│  data/interim/ratings/part-00000.parquet (176 MB, 31 row-groups)   │
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
┌─ TẦNG 3 ─ SPARK ────────────────────────────────────────────────────┐
│  S3  sinh 3 split:  random80_20 | temporal_global | leave_one_out  │
│  S4  audit tầng 1: temporal_violation, unseen_item, cold_start     │
│  S5  baseline Popularity (Spark SQL) → NDCG@10, DCG@10              │
│  S6  ALS (rank 16, maxIter 8, seed 42) → userFactors/itemFactors   │
│  S7  top-K bằng numpy: U[s:e] @ V.T → argpartition (chunk 2000)   │
│  S8  bias metrics: coverage, long-tail, Gini, popularity_bias_ratio│
└──────────────────────────────────────────────────────────────────────┘
                              │
┌─ TẦNG 4 ─ LƯU TRỮ & TRỰC QUAN ──────────────────────────────────────┐
│  S9  MongoDB: collection `audit_metrics` (split × model)           │
│      + collection `item_profile` (popularity, year, long-tail flag) │
│  S10 R + SparkR: thống kê mô tả, kiểm định, biểu đồ              │
│  S11 Streamlit: dashboard đọc MongoDB                             │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. Tầng 1 — Ingest

| Bước | Công cụ | Ghi chú |
|---|---|---|
| 1.1 Tải | `https://files.grouplens.org/datasets/movielens/ml-25m.zip` | 261.978.986 B |
| 1.2 Giải nén | `D:\recsys_data\raw\ml-25m\` | 8 file |
| 1.3 CSV → Parquet | **pyarrow** `pacsv.open_csv` + `pq.ParquetWriter` | 26s, schema cố định `userId int32, movieId int32, rating float32, timestamp int32` |
| 1.4 Checksum | SHA-256 từng file parquet → `ratings.parquet.sha256` | tái lập |

**Vì sao pyarrow chứ không phải Spark:** `df.write.parquet` trên Windows cần `winutils.exe` (`hadoop.home.dir` unset) → fail. Pyarrow ghi thẳng, không cần Hadoop native libs.

---

## 3. Tầng 2 — HDFS + MapReduce

**Mục tiêu:** chứng minh yêu cầu seminar "MapReduce + HDFS" và "MapReduce bằng Python" bằng **pipeline thật**, không phải demo.

### 3.1 Nạp vào HDFS

```bash
docker exec namenode hdfs dfs -mkdir -p /recsys/ratings
docker cp D:\recsys_data\parquet\ratings\part-00000.parquet namenode:/tmp/ratings.parquet
docker exec namenode hdfs dfs -put -f /tmp/ratings.parquet /recsys/ratings/part-00000.parquet


**Kốt quả:** 1 file, 167,8 MB, 175.961.682 byte (`hdfs dfs -count -q`).

> MapReduce job cần **CSV text** chứ không phải Parquet (MapReduce đọc `TextInputFormat`). Vì vậy `scripts/03_run_mapreduce.sh` nạp thêm `/recsys/ratings_csv/part-00000.csv` (646,8 MB) từ `/tmp/ratings.csv` trong container. Parquet vẫn giữ vai trò nguồn cho Spark.
```

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

| Lỗi | Nguyên nhân | Sửa |
|---|---|---|
| `Type mismatch in value from map: expected LongWritable, received IntWritable` | `setOutputValueClass` = output reducer nhưng map ghi `IntWritable` | Thống nhất **cả 3** (map, combiner, reducer) dùng `IntWritable` + thêm `setMapOutputValueClass(IntWritable.class)` |
| `wrong value class: LongWritable is not IntWritable` | Combiner ghi `LongWritable`, reducer input là `IntWritable` | Combiner dùng `IntWritable` |

### 3.3 Kiểm chứng tương đương (Gate G3) — ĐÃ CHẠY, PASS

Bắt buộc: kết quả MapReduce phải **khớp tuyệt đối** kết quả Spark `groupBy("movieId","year").count()` trên cùng tập → chứng minh 2 đường xử lý cho cùng kết quả (điểm báo cáo rất tốt cho môn Big Data).

Script: `scripts/08_crosscheck_g3.py` → `results/g3_crosscheck.json`.

| Chỉ số | Kết quả |
|---|---|
| MapReduce rows | 323.737 |
| Spark SQL rows | 323.737 |
| Union keys | 323.737 |
| **Exact match** | **323.737 / 323.737 = 100,0000%** |
| Tổng tương tác (MR) | 25.000.095 |
| Tổng tương tác (Spark) | 25.000.095 |
| Tổng tương tác (kỳ vọng) | 25.000.095 |
| **gate_G3_passed** | ✅ **true** |

> **Bẫy timezone đã ghi nhận:** MapReduce dùng `SimpleDateFormat` với **UTC**, Spark mặc định `from_unixtime` theo **local (UTC+7)** → lệch 24.778/323.775 key (7,65%). Phải set `.config("spark.sql.session.timeZone", "UTC")`. Đây là loại lỗi âm thầm mà chỉ phát hiện được khi có đối chiếu số — lý do G3 là bắt buộc, không phải thủ tục.

## 4. Tầng 3 — Spark

### 4.1 Sinh split

| Tên | Mã Spark |
|---|---|
| `random80_20` | `df.withColumn("is_test", F.rand(42) > F.lit(0.8))` |
| `temporal_global` | `df.withColumn("is_test", F.col("timestamp") >= F.lit(THR))`, `THR = percentile_approx(timestamp, 0.8)` |
| `leave_one_out` | `Window.partitionBy("userId").orderBy(timestamp.desc(), movieId.asc())` → `rn == 1` |

### 4.2 Audit tầng 1 (Spark SQL thuần)

```python
viol  = test.filter(F.col("timestamp") < train_max_ts).count()
unseen = test.join(broadcast(train.select("movieId").distinct()), "movieId", "left_anti").count()
cold   = test.join(broadcast(train.select("userId").distinct()), "userId", "left_anti").count()
elig   = train.groupBy("userId").count().filter(F.col("count") >= 5).select("userId")
```

### 4.3 ALS + top-K numpy

```python
als = ALS(userCol="userId", itemCol="movieId", ratingCol="rating",
          rank=16, maxIter=8, regParam=0.05, coldStartStrategy="drop", seed=42)
m = als.fit(train_subsample)
U = np.array([r["features"] for r in m.userFactors.collect()])   # (n_user, 16)
V = np.array([r["features"] for r in m.itemFactors.collect()])   # (n_item, 16)

for s in range(0, len(U), 2000):          # chunk để không OOM
    sc = U[s:s+2000] @ V.T
    # mask item user đã xem -> -inf
    # np.argpartition(-row, 10)[:10] -> top-10
```

**Vì sao không `recommendForAllUsers`:** hàm này tạo cartesian 162.541 × 59.047 ≈ 9,6 tỷ cặp → OOM. Cách numpy chunk 2.000 user cho **cùng kết quả toán học** (top-K theo `U·V`) nhưng kiểm soát được bộ nhớ.

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

| Collection | Schema | Nguồn |
|---|---|---|
| `audit_metrics` | **42 field** đầy đủ: `{split, model, ndcg10, dcg10, hit_rate10, catalog_coverage, longtail_coverage, gini_exposure, avg_pop_rec, avg_pop_all, popularity_bias_ratio, train_rows, test_rows, train_max_ts, train_max_ts_iso, test_min_ts, test_min_ts_iso, temporal_violation_global, temporal_violation_global_pct, temporal_violation_user, temporal_violation_user_pct, unseen_item_rows, unseen_item_pct, coldstart_user_rows, eval_users, eval_test_rows, eval_relevant_users, test_relevant_eval_rows, relevance_threshold, min_train_threshold, seed, spark_version, dataset, run_at, + tham số ALS}` | `scripts/05_store_mongodb.py` ← `results/poc6_*.json` |
| `item_profile` | `{movieId, title, year, genres[]}` | `movies.csv` (62.423 phim) |
| `audit_metrics_r` | schema rút gọn 12 field (bảng chung phục vụ báo cáo R) | `scripts/06_analysis_r.R` |

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
6. Xuất: `reports/metrics_summary.csv`, `reports/data_level_metrics.csv`, 7 PNG vào `reports/figures/`.

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
                    audit_metrics (tầng 1)    ALS → top-K → bias metrics
                                                    │
                                                    ▼
                                          MongoDB → R/SparkR → Streamlit
```

---

## 7. Điểm kiểm soát chất lượng (quality gate)

| Gate | Điều kiện | Trạng thái 04/11 | Hành động nếu fail |
|---|---|---|---|
| G1 | `rows == 25.000.095` | ✅ pass | dừng, kiểm tra checksum |
| G2 | `ts_min == 1995-01-09 11:46:49` và `ts_max == 2019-11-21 09:15:03` | ✅ pass | dừng |
| G3 | MapReduce popularity == Spark popularity, **khớp tuyệt đối** | ✅ **pass 100%** (323.737/323.737) | dừng, sửa job / kiểm tra timezone |
| G4 | `temporal_violation_global_pct(random) > 95%` | ✅ pass (100,0000%) | kiểm tra lại định nghĩa split |
| G5 | `temporal_violation_global_pct(temporal_global) == 0` | ✅ pass (0,0000%) | kiểm tra threshold |
| G6 | NDCG của ALS ≥ NDCG popularity (sanity) | ✅ pass (3/3 split) | kiểm tra top-K/mask |
| G7 | `eval_relevant_users` > 0 ở mọi split (tập đánh giá khả dụng) | ✅ pass (temporal: 6.219 > 0) | cảnh báo khi so sánh NDCG giữa split |
| G8 | Gap 3 phần nằm trong 200–250 từ | ✅ pass (237 từ) | rút gọn `scripts/09_count_gap.py` |

## 8. Tầng 6 — Kiểm định thống kê (bổ sung 2026-11-04)

Đây là tầng **mới**, nằm sau tầng 5 (MongoDB) và trước khi trích xuất kết luận.

### 8.1 Vì sao cần

Các chỉ số ở tầng 1–3 là **một số cho cả tập** → không có phương sai, không kiểm định được.
Muốn trả lời "khác biệt giữa Popularity và ALS có **thật** không, hay chỉ là nhiễu mẫu?"
thì phải có **một giá trị cho mỗi user**.

### 8.2 Thành phần

| Mã | Thành phần | Công nghệ | Script | Trạng thái |
|---|---|---|---|---|
| S5.1 | Sinh per-user metrics | PySpark 4.2.0 + numpy | `scripts/11_peruser_ndcg.py` | ✅ chạy thật, 3 split |
| S5.2 | Bootstrap CI + Wilcoxon + Cohen's dz + Kendall tau-b | numpy (vector hoá) + scipy 1.18.0 | `scripts/12_stats_tests.py` | ✅ chạy thật, 3 split |
| S5.3 | PRISMA 2020 flow | SVG thuần (không cần Cairo) | `scripts/13_prisma_flow.py` | ✅ SVG |
| S5.4 | Benchmark Big Data | PySpark + YARN REST | `scripts/14_perf_benchmark.py` | 🔄 đang chạy |
| S5.5 | Chụp dashboard | Chrome DevTools Protocol | `scripts/15_screenshot_dashboard.py` | ✅ PNG 1920×1260 |

### 8.3 Sơ đồ luồng (mở rộng)

```
                        ┌──────────────────────────────┐
peruser_<split>.csv ──►│ scripts/12_stats_tests.py     │
(29.337 / 1.363 /      │  • bootstrap CI 95% (10.000)  │
17.704 user)            │  • Wilcoxon signed-rank        │
                        │  • Cohen's dz, rank-biserial   │
                        │  • Kendall tau-b              │
                        └──────────────┬───────────────┘
                                       ▼
             reports/stats_<split>.json  +  reports/stats_summary.csv
```

### 8.4 Điểm kiểm soát chất lượng (bổ sung)

| Gate | Điều kiện | Trạng thái 04/11 | Hành động nếu fail |
|---|---|---|---|
| G9 | `n_paired > 0` ở cả 3 split | ✅ pass (29.337 / 1.363 / 17.704) | kiểm tra `min_train`, ngưỡng liên quan |
| G10 | Metric hằng số **không** được báo "có ý nghĩa" | ✅ pass (cờ `constant_metric`) | kiểm tra `n_nonzero == 0` |
| G11 | Bootstrap CI phải hẹp hơn khoảng cách hiệu ứng khi kết luận "có ý nghĩa" | ✅ pass (CI không chạm 0) | kiểm tra lại số lần bootstrap |
| G12 | Mọi khẳng định về thiên lệch phải kèm `longtail_coverage` | ✅ pass (0 ở cả 6 tổ hợp → **không** khẳng định "đã xử lý") | sửa phần diễn giải |

---

## 9. Tầng 7 — Tài liệu tham khảo & quy trình rà soát học thuật (2026-11-04)

### 9.1 Tải paper tự động

`scripts/10_fetch_papers.py` — fallback chain `OpenAlex → Unpaywall → arXiv → OA aggregator`,
ghi `docs/References/Papers/_manifest.json` (DOI, file, title, source, sha256, bytes).
**Bảo toàn file tồn tại**: script không ghi đè PDF đã tải.

### 9.2 Trạng thái 9/9 paper

| # | File | DOI / nguồn |
|---|---|---|
| 01 | `01_TOIS2022_DataLeakage_RS_OfflineEvaluation.pdf` | `10.1145/3539594` (arXiv 2010.11060) |
| 02 | `02_TOIS2023_Reproducing_PopularityBias_EvaluationStrategies.pdf` | CWI IR (ir.cwi.nl/pub/33989) |
| 03 | `03_RecSys2025_TimeToSplit.pdf` | arXiv 2507.16289 |
| 04 | `04_RecSys2026_ConvergentValidity_OfflineEvaluation.pdf` | ACM DL (hybrid) |
| 05 | `05_TOIS2022_Bias_Debias_Survey.pdf` | ACM DL |
| 06 | `06_UMAI2024_Survey_PopularityBias.pdf` | — |
| 07 | `07_SIGIR2023_FreshLook_EvaluationStandpoint.pdf` | ACM DL |
| 08 | `08_RecSys2023_Challenges_OfflineEvaluation.pdf` | `10.1145/3604915.3609495` — 414.562 B, SHA-256 `FA37C1CD…19F94` |
| 09 | `09_RecSys2025_InheritedPopularityBias_ColdStart.pdf` | ACM DL |

### 9.3 PRISMA

`scripts/13_prisma_flow.py` sinh `docs/Project/Main/report/Big_Data/figures/fig8_prisma_flow.svg`
(1180×760, Times New Roman, 4.619 B). SVG thuần → **không cần** `cairosvg`/native Cairo.

---

## 10. Quy trình tái lập đầy đủ (master)

```powershell
cd "D:\Master Exers\Big Data\Recomendation_System"

# 0. hạ tầng
docker start namenode datanode resourcemanager nodemanager historyserver

# 1. ingest
python scripts\01_ml_to_parquet.py

# 2. HDFS + MapReduce (Java) -> G3 cross-check
bash scripts/run_mr.sh
python scripts\08_crosscheck_g3.py

# 3. audit + model (3 split) -> MongoDB
python scripts\04_audit_spark.py
python scripts\05_store_mongodb.py

# 4. per-user + kiểm định thống kê
python scripts\11_peruser_ndcg.py random80_20
python scripts\11_peruser_ndcg.py temporal_global
python scripts\11_peruser_ndcg.py leave_one_out
python scripts\12_stats_tests.py

# 5. R (đọc MongoDB, ghi recsys.audit_metrics_r)
Rscript scripts\06_analysis_r.R

# 6. PRISMA + benchmark
python scripts\13_prisma_flow.py
python scripts\14_perf_benchmark.py

# 7. dashboard + screenshot
python -m streamlit run scripts\07_dashboard.py --server.headless true --server.port 8501
python scripts\15_screenshot_dashboard.py

# 8. tài liệu tham khảo
python scripts\10_fetch_papers.py
```

> **Trần thời gian:** mỗi lệnh phải < 30 phút (trần exec session của OpenClaw). Bước 4 và 6 là
> các ứng viên vượt trần nếu gộp — phải tách theo split / theo engine.
