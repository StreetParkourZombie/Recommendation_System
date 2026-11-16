# Kế hoạch triển khai trả lời RQ1

**RQ1:** Chiến lược chia tập khác nhau có làm đảo chiều thứ hạng mô hình gợi ý không, và độ lớn đảo chiều là bao nhiêu?

## 1. Mục tiêu và phạm vi

Kiểm tra liệu thứ hạng `MostPopular` và `ALS` theo chất lượng ranking có thay đổi giữa `random80_20`, `temporal_global` và `leave_one_out` không; định lượng mức thay đổi và độ ổn định qua seed. Đây là controlled, method-informed implementation, không phải tái lập nguyên trạng Paper 01.

**Deadline scope:** MovieLens-25M project dataset; hai model (`MostPopular`, `ALS`); ba split; seed `42`, `2024`, `7`; `K=10`; relevance `rating >= 4.0`; `min_train >= 5` nếu tương thích với split hiện tại. Bảng chính dùng Spark `local[4]`, driver heap `6g`, một job tại một thời điểm, không dùng GPU. Smoke test có thể dùng `4g`, nhưng không gộp kết quả smoke khác cấu hình vào bảng chính.

Không đổi model, hyperparameter, dataset, relevance, metric hoặc resource profile giữa các split. Nếu buộc đổi cấu hình, tăng protocol version và chạy lại toàn bộ ô liên quan.

## 2. Metric contract và định nghĩa đổi hạng

- **Metric chính:** macro `NDCG@10` trên user đủ điều kiện.
- **Metric phụ:** macro `Recall@10` để kiểm tra độ nhạy kết luận.
- Mỗi ô `split × model × seed` lưu metric, số user đánh giá, số relevant test items và runtime. Ghi rõ cách loại user không có relevant test item.
- Với mỗi split và seed, tính `ΔNDCG@10 = NDCG_ALS - NDCG_MostPopular`; model có điểm cao hơn xếp hạng cao hơn.
- So sánh ba cặp split: random–temporal, random–LOO, temporal–LOO. “Đảo chiều” nghĩa là model thắng theo NDCG đổi giữa hai split. Báo cáo số cặp có đổi chiều trên tổng ba cặp, kèm từng seed và mean ± SD.
- Vì chỉ có hai model, không dùng hệ số tương quan thứ hạng làm bằng chứng chính; trình bày trực tiếp model thắng và chênh lệch metric.
- `Recall@10` là kiểm tra phụ. Nếu thứ hạng khác NDCG, nêu metric-dependent result, không chọn metric thuận lợi.

**Điểm cần chốt trước chạy:** split khác nhau có thể tạo population user và số test positives khác nhau. Xác định trước dùng population riêng của từng split hay tập user chung; ghi counts và áp dụng nhất quán.

## 3. Các giai đoạn

### Phase A — Audit protocol và code

1. Xác nhận split builder, train/test boundary, overlap và user eligibility cho cả ba split.
2. Kiểm tra recommender chỉ fit trên train; test không tham gia fit hoặc tuning. Top-K loại item đã thấy trong train; xác định tie handling, macro averaging và quy tắc user không có relevant item.
3. Kiểm tra ALS parameters, `MostPopular` tie-breaking và nguồn ngẫu nhiên. Seed project chỉ áp dụng phần có stochasticity; không mô tả seed do project thêm như seed có sẵn của paper.
4. Ghi protocol ID, dataset/preprocessing, split definition, relevance, K, min-train, model parameters, versions và resource profile.
5. Làm fixture nhỏ để đối chiếu thủ công NDCG/Recall và kiểm tra train-item exclusion.

**Gate A:** split counts hợp lý; metric sanity checks đạt; cấu hình cố định và truy nguyên được.

### Phase B — Smoke tests

1. Chạy `temporal_global × MostPopular × seed 42`.
2. Chạy `temporal_global × ALS × seed 42`.
3. Xác nhận output hữu hạn, schema nhất quán, user counts hợp lệ, model fit đúng train và log có runtime/config.
4. Smoke profile khác bảng chính thì chỉ dùng kiểm tra pipeline, không đưa số vào phân tích.

**Gate B:** cả hai model chạy hoàn tất, không còn leakage, NaN hoặc empty output chưa giải thích.

### Phase C — Ma trận chính

Chạy tuần tự `3 split × 2 model × 3 seed = 18 runs`, cùng resource profile và protocol. Lưu mỗi run dưới dạng raw result với `protocol_id`, split, model, seed, start/end, exit status, runtime, Spark config và log path. Không ghi đè lần chạy trước. Run lỗi ghi trạng thái và nguyên nhân; sau khi sửa, rerun cùng cấu hình.

**Gate C:** đủ 18 run thành công. Nếu thiếu, liệt kê ô thiếu và thu hẹp claim tương ứng; không suy rộng từ ma trận không đầy đủ.

### Phase D — Phân tích

1. Bảng `split × model`: mean ± SD qua seed cho NDCG@10, Recall@10, runtime; kèm số run và user counts.
2. Bảng `ΔNDCG@10` theo split và seed; xác định model thắng ở mỗi ô.
3. Tóm tắt đổi chiều cho ba cặp split; không che giấu kết quả bất ổn giữa seed.
4. Interaction plot: split trục x, metric trục y, model là đường riêng, error bar là SD qua seed.
5. So sánh split chỉ khi population/eligibility khác biệt được báo cáo. Nếu dùng population riêng, diễn giải metric như kết quả trên các population tương ứng.
6. Với ba seed, inferential statistics chỉ mang tính thăm dò; ưu tiên effect size và độ phân tán, không tuyên bố bằng chứng thống kê mạnh.

### Phase E — Viết câu trả lời RQ1

Nêu rõ: (a) có hay không quan sát đổi model thắng theo NDCG@10 và giữa split nào; (b) độ lớn `ΔNDCG@10` và biến thiên qua seed; (c) Recall@10 có đồng thuận không; (d) user/test-positive counts và ảnh hưởng đến diễn giải; (e) phạm vi giới hạn ở hai baseline, MovieLens-25M, protocol và máy đã khai báo. Nếu không có đảo chiều, viết “không quan sát thấy đảo chiều trong phạm vi thử nghiệm”, không khẳng định split không thể làm đổi ranking.

## 4. Deliverables và tiêu chí hoàn thành

- Protocol/manifest và log cho từng run.
- Raw results CSV/JSON, không chỉ bảng tổng hợp.
- Split/leakage diagnostics và bảng metric tổng hợp mean ± SD.
- Bảng chênh lệch `ALS - MostPopular`, số lần đổi model thắng và interaction plot.
- Phần trả lời RQ1, limitations, và nhãn `method-informed implementation`; không gọi ALS/MostPopular so sánh là reproduction Paper 01 nếu protocol/model khác paper.

Hoàn thành khi đủ 18 run truy nguyên được, metric contract đã kiểm chứng, kết quả đổi hạng và độ lớn chênh lệch được báo cáo. Nếu deadline không cho phép đủ 18, ưu tiên `3 split × 2 model × 1 seed`, ghi đây là phân tích rút gọn và không tuyên bố ổn định qua seed.

## 5. Rủi ro và ứng phó

| Rủi ro | Ứng phó |
|---|---|
| ALS OOM hoặc quá lâu | Kiểm tra một split trước; chốt iteration/config trước ma trận. Nếu đổi, tăng protocol version và áp dụng đồng đều cho mọi split. |
| Population khác nhau theo split | Ghi eligible users/test positives; chọn trước population riêng hay user chung, rồi giữ nhất quán. |
| Metric implementation lỗi | Dùng fixture nhỏ, kiểm tra thủ công top-K, NDCG, Recall, tie handling và loại train items. |
| Seed không tác động MostPopular | Giữ đủ records; ghi nhận model deterministic thay vì tạo stochasticity giả. |
| Thermal throttling | Chạy tuần tự; ghi runtime và điều kiện máy nếu đo được. Không suy luận hiệu năng cluster từ laptop. |

## 6. Việc tiếp theo

1. Audit code và chốt population, metric contract, split counts.
2. Xác minh Spark profile thực tế script sử dụng; chuẩn hóa về profile đã định.
3. Hoàn tất Gate A, sau đó hai smoke test Gate B.
4. Chạy ma trận 18 run; lưu manifest, raw output và log.
5. Tạo bảng/biểu đồ, rồi viết kết luận RQ1 kèm giới hạn.

---
---

# KẾ HOẠCH NOTEBOOK CHO BƯỚC CHIA TẬP (04 → 09)

**Lập ngày:** 2026-11-15
**Trạng thái hiện tại:** Notebook `00`–`03` đã chạy xong (L0, L1, L2, L3 PASS). Script `scripts/04_audit_spark.py` đã chạy thật 3 split và sinh kết quả trong `D:\recsys_data\poc\poc6_*.json`. Chưa có notebook nào cho phần chia tập.

**Mục tiêu:** chuyển toàn bộ luồng trong `scripts/04_audit_spark.py` (303 dòng, một file monolithic) thành chuỗi notebook quan sát được, mỗi notebook một việc, logic dùng lại đẩy vào `src/audit/`.

---

## 1. Vấn đề của trạng thái hiện tại

| Vấn đề | Hệ quả |
|---|---|
| `04_audit_spark.py` gộp 4 việc: đọc dữ liệu, chia tập, audit tầng 1, Popularity, ALS | Không quan sát được bước nào sinh ra số nào; sửa 1 chỗ phải chạy lại 40–110 giây |
| Kết quả ghi vào `D:\recsys_data\poc\` và log vào `C:\Users\PC\.openclaw\workspace\_poc6_out.txt` | Nằm ngoài `runs/<run_id>/`, không có manifest, không truy nguyên theo protocol |
| Không có file split nào được lưu xuống đĩa | Mỗi lần chạy ALS/Popularity phải dựng lại split từ `ratings.csv`, không tái lập được tập test của lần trước |
| `src/audit/`, `src/utils/` chỉ còn `__pycache__` (`split_audit.cpython-314.pyc`, `spark_utils.cpython-314.pyc`) | Source đã mất, notebook không import được gì |
| `NotebookRun` (`src/recsys/notebook_logging.py`) chưa được dùng cho phần split | Không có checkpoint/traceback theo cell như 00–03 |

---

## 2. Thay đổi môi trường đã xác minh trong phiên này

> [!IMPORTANT]
> `df.write.parquet()` **đã ghi được** trên máy này sau khi đặt `HADOOP_HOME=D:\recsys_data\tools\hadoop` với `bin\winutils.exe` (112.640 B) **và** `bin\hadoop.dll` (85.504 B).
> Test thật: `WRITE_OK rows= 2`. Trước đó chỉ có `winutils.exe` → vẫn `UnsatisfiedLinkError: NativeIO$Windows.access0`.

Điều này làm thay đổi kết luận cũ trong [io.md](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/docs/Project/Main/MetErrors/io.md) ("phải dùng pyarrow, không dùng `df.write.parquet`"). Kết luận mới:

- Ghi Parquet bằng **Spark** được, nếu `HADOOP_HOME` trỏ đúng thư mục có đủ 2 file trên.
- Giữ pyarrow cho **ingest CSV → Parquet gốc** (nhanh hơn, không cần JVM).
- Dùng **Spark** cho **ghi split** (cần partition + metadata Spark, pyarrow làm được nhưng thủ công hơn).

---

## 3. Kiến trúc `src/`

Mọi thứ dài hơn ~30 dòng vào `src/`, notebook chỉ gọi hàm + in + assert.

```text
src/
  utils/
    spark_utils.py       # get_spark(), ensure_hadoop_home(), PATHS hằng số
  audit/
    __init__.py
    splits.py            # STRATEGIES, build_split(), materialize_split()
    leakage.py           # data_level_audit() -> dict 42 field như poc6
    popularity.py        # mostpopular_topk(), bias_metrics()
    metrics.py           # dcg_at_k, ndcg_at_k, gini, coverage (thuần Python/NumPy)
    als_rec.py           # fit_als_implicit(), topk_numpy()
    io.py                # save_json(), sha256_file(), write_parquet()
```

### 3.1 `src/utils/spark_utils.py`

| Hàm / hằng | Trách nhiệm |
|---|---|
| `PATHS` | `RAW_CSV`, `PARQUET_RATINGS`, `SPLITS_DIR`, `SPARK_TMP`, `POC_DIR` — một nguồn duy nhất, không hardcode rải rác |
| `ensure_hadoop_home()` | Set `HADOOP_HOME` + prepend `bin` vào `PATH` nếu `winutils.exe` + `hadoop.dll` tồn tại; trả `True/False` để notebook log được |
| `get_spark(app_name, master="local[4]", driver_memory="6g", shuffle_partitions=8)` | Builder cố định: `spark.local.dir=SPARK_TMP`, `spark.sql.session.timeZone=UTC`, `spark.ui.showConsoleProgress=false`, log level `ERROR`. Không notebook nào tự dựng builder riêng |
| `stop_spark(spark)` | `spark.stop()` an toàn |

### 3.2 `src/audit/splits.py`

```python
STRATEGIES = ("random80_20", "temporal_global", "leave_one_out")

def build_split(ratings_df, strategy, seed=42, test_fraction=0.2) -> (df_with_is_test, threshold_ts_or_None)
def materialize_split(df, strategy, out_dir, train_partitions=8) -> dict   # ghi train/ + test/ parquet
def load_split(strategy, splits_dir) -> (train_df, test_df)
def verify_materialized(strategy, splits_dir) -> dict                     # đếm lại, so khớp manifest
```

Quy tắc chia phải khớp **tuyệt đối** với `04_audit_spark.py`:

| Strategy | Công thức | Ghi chú |
|---|---|---|
| `random80_20` | `F.rand(seed) > 0.8` | seed 42 mặc định |
| `temporal_global` | `timestamp >= percentile_approx(timestamp, 0.8)` | quantile dạng **0.0–1.0** (Spark 4.x) |
| `leave_one_out` | `row_number() over (partition by userId order by timestamp desc, movieId asc) == 1` | tie-break bằng `movieId` để đơn định; khai báo rõ đây **không** phải thứ tự thời gian thật |

### 3.3 `src/audit/leakage.py`

`data_level_audit(train, test, relevance_threshold=4.0, min_train=5)` trả đúng bộ field đã đo:

`train_rows`, `test_rows`, `train_max_ts`, `test_min_ts`, `temporal_violation_global(_pct)`, `temporal_violation_user(_pct)`, `unseen_item_rows(_pct)`, `coldstart_user_rows`, `eval_users`, `eval_test_rows`, `test_relevant_rows`, `test_relevant_eval_rows`, `eval_relevant_users`, `relevance_threshold`, `min_train_threshold`.

Xử lý `None` trên tập rỗng: `int(row[0] or 0)` — đây là bug đã vấp (xem [datasets.md §1](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/docs/Project/Main/MetErrors/datasets.md)).

### 3.4 `src/audit/popularity.py`

- `mostpopular_topk(train, k=10)` — `orderBy(pop desc, movieId asc)`, tie-break đơn định.
- `bias_metrics(recommended, popularity_map)` — `catalog_coverage`, `longtail_coverage` (ngưỡng P20 của train), `gini_exposure`, `avg_pop_rec`, `avg_pop_all`, `popularity_bias_ratio`.

### 3.5 `src/audit/metrics.py`

Thuần Python/NumPy, không Spark — để notebook `07` kiểm tra tay được.

- `dcg_at_k(ranked, relevant, k)`, `idcg_at_k(n_rel, k)`, `ndcg_at_k(...)`
- `per_user_ndcg_from_rec(rec: dict[user] -> array, truth: dict[user] -> set, k)` → `(mean, list)`
- `hit_rate_at_k(...)`
- `gini(values)`
- `assert_against_fixture()` — bộ 5 ca tay: hit ở vị trí 1, hit ở vị trí 10, không hit, 2 relevant, relevant nhiều hơn K.

### 3.6 `src/audit/als_rec.py`

- `fit_als_implicit(train_positive, rank=16, max_iter=8, reg=0.05, alpha=10.0, seed=42)` — trả `(U, ui, V, vi, fit_seconds)`.
- `topk_numpy(U, ui, V, vi, seen_by_user, k=10, chunk=2000, only_users=None)` — chia chunk, `-inf` cho item đã thấy, `argpartition` + sort. Không dùng `recommendForAllUsers`.

### 3.7 `src/audit/io.py`

- `save_json(path, obj)` — `ensure_ascii=False, indent=2, default=str`.
- `sha256_file(path)` — 1 MB block.
- Ghi artifact luôn vào `run.run_dir / "outputs"`, không ghi vào `D:\recsys_data\poc\`.

---

## 4. Chuỗi notebook

Tất cả dùng kernel `recsys-project-venv`, `NotebookRun` cho log/checkpoint, mỗi notebook tạo `runs/<run_id>/` riêng.

### `04_build_splits.ipynb` — Gate L4

| Cell | Nội dung | Checkpoint |
|---|---|---|
| 1 | Điều kiện: L3 manifest `COMPLETED`, `ratings.csv` SHA-256 khớp, Parquet cache tồn tại | `prereq_ok` |
| 2 | Khái niệm: chia tập là **quyết định protocol**, không phải tiền xử lý kỹ thuật. 3 chiến lược trả lời 3 câu hỏi khác nhau | — |
| 3 | `get_spark('RecSys04BuildSplits')`, log `hadoop_home_ok` | `spark_ready` |
| 4 | Đọc Parquet cache + đếm (25.000.095) | `input_ready` |
| 5 | Với từng strategy: `build_split` → `materialize_split` → `verify_materialized` | `split_<name>` ×3 |
| 6 | Bảng tổng hợp: `train_rows`, `test_rows`, `threshold_ts`, `parquet_bytes`, `sha256` | `splits_materialized` |
| 7 | Assert đối chiếu số đã đo: random 19.997.974 / 5.002.121; temporal 19.999.279 / 5.000.816; LOO 24.837.554 / 162.541 | — |
| 8 | Ghi `outputs/split_manifest.json`, `finish('COMPLETED')` | `manifest_saved` |

**Output:** `D:\recsys_data\splits\<strategy>\{train,test}\part-00000.parquet` + `runs/<run_id>/outputs/split_manifest.json`.

### `05_audit_split_leakage.ipynb` — Gate L5

| Cell | Nội dung | Checkpoint |
|---|---|---|
| 1 | Nạp 3 split từ đĩa bằng `load_split` (không dựng lại) | `splits_loaded` |
| 2 | Khái niệm: 2 định nghĩa `temporal_violation` (global vs user-relative); vì sao global vô nghĩa với LOO | — |
| 3 | Chạy `data_level_audit` cho từng split | `audit_<name>` ×3 |
| 4 | Bảng so sánh 3 split, 14 chỉ số | — |
| 5 | Assert: random `temporal_violation_user_pct ≈ 98,9158`; temporal `= 0,0`; LOO `global_pct ≈ 99,9988` nhưng `user_pct = 0,0` | `audit_assertions` |
| 6 | Ghi `outputs/data_level_audit.json` + `data_level_audit.csv` | `audit_saved` |

### `06_mostpopular_baseline.ipynb` — Gate L6a

| Cell | Nội dung | Checkpoint |
|---|---|---|
| 1 | Nạp split + audit (cần `eval_users`) | — |
| 2 | Khái niệm: popularity phải tính **trên train**, không trên full data; tie-break bằng `movieId` | — |
| 3 | `mostpopular_topk(train, k=10)` cho từng split, in top-10 | `topk_<name>` |
| 4 | NDCG/DCG trên tập `eval_users` | `pop_metrics_<name>` |
| 5 | `bias_metrics` cho cả 3 split | `pop_bias_<name>` |
| 6 | Assert đối chiếu: NDCG 0,0852 / 0,0455 / 0,0183 (dung sai ±0,002 vì `rand` seed phụ thuộc partition) | `pop_assertions` |
| 7 | Ghi `outputs/mostpopular_<split>.json` | `pop_saved` |

### `07_ndcg_manual_check.ipynb` — Gate L6b

Không đọc dữ liệu lớn. Toàn bộ trên fixture.

| Cell | Nội dung |
|---|---|
| 1 | Khái niệm: DCG, IDCG, NDCG; vì sao `NDCG@10` của 2 model chỉ so được khi cùng `eval_users` |
| 2 | Tính tay 3 ca trên giấy (markdown bảng) |
| 3 | `assert_against_fixture()` — so code với tính tay |
| 4 | Kiểm tra loại item đã thấy: user có 5 item trong train, tất cả bị `-inf`, top-10 không chứa item nào trong train |
| 5 | Kiểm tra `gini` trên 3 vector tay: đồng đều, dồn 1 item, rỗng |

**Gate:** code metric khớp tính tay trước khi tin bất kỳ số NDCG nào ở notebook 06/08.

### `08_als_implicit.ipynb` — Gate L6c

| Cell | Nội dung | Checkpoint |
|---|---|---|
| 1 | Nạp split, cắt subsample `n_users=30000` theo `userId` tăng dần (đơn định) | `subsample_ready` |
| 2 | Khái niệm: implicit ALS, `alpha` là confidence; vì sao phải lọc `rating >= 4.0` trước khi fit | — |
| 3 | `fit_als_implicit` | `als_fit_<name>` (lưu `fit_seconds`) |
| 4 | `topk_numpy` | `topk_done_<name>` |
| 5 | `per_user_ndcg_from_rec` + `hit_rate_at_k` + `bias_metrics` | `als_metrics_<name>` |
| 6 | Assert: NDCG 0,2556 / 0,1311 / 0,0467 ±0,01; `rec` không chứa item đã thấy | `als_assertions` |
| 7 | Ghi `outputs/als_<split>.json` + `outputs/peruser_ndcg_<split>.npz` | `als_saved` |

> `peruser_ndcg_<split>.npz` là đầu vào bắt buộc cho kiểm định cặp ở notebook 10. Không thay bằng summary.

### `09_compare_and_reversal.ipynb` — Gate L7

| Cell | Nội dung |
|---|---|
| 1 | Nạp 6 JSON (2 model × 3 split) + 3 file per-user |
| 2 | Bảng `split × model`: NDCG@10, Hit@10, catalog_coverage, gini, bias_ratio |
| 3 | `ΔNDCG@10 = NDCG_ALS − NDCG_POP` cho từng split; xác định model thắng |
| 4 | 3 cặp split (random–temporal, random–LOO, temporal–LOO): có đổi model thắng không |
| 5 | Interaction plot: x=split, y=NDCG@10, 2 đường model |
| 6 | Viết câu trả lời RQ1 theo mẫu Phase E của file này (§RQ1 phía trên); nêu rõ giới hạn 1 seed |

**Kết quả dự kiến từ số đã đo:** ALS thắng ở **cả 3** split (0,2556 / 0,1311 / 0,0467 so với 0,0852 / 0,0455 / 0,0183) → **không quan sát thấy đảo chiều** trong phạm vi này. Chênh lệch co từ +0,1704 (random) xuống +0,0284 (LOO). Đây là phát hiện chính, không phải thất bại.

---

## 5. Hợp đồng dùng chung (protocol v1)

| Tham số | Giá trị | Ghi ở đâu |
|---|---|---|
| `protocol_id` | `project_protocol_v1` | manifest mọi notebook |
| `seed` | 42 | manifest |
| `K` | 10 | manifest |
| `relevance` | `rating >= 4.0` | manifest |
| `min_train` | 5 | manifest |
| `ALS` | rank 16, maxIter 8, reg 0.05, alpha 10.0, `implicitPrefs=True`, `coldStartStrategy=drop` | manifest |
| `subsample_users` | 30.000 | manifest |
| Spark | `local[4]`, driver 6g, shuffle 8, timeZone UTC, `spark.local.dir=D:\recsys_data\spark_tmp` | log cell |

Không notebook nào được đổi các giá trị này mà không tăng `protocol_id`.

---

## 6. Số đã đo thật (dùng làm assert, không phải kỳ vọng lý thuyết)

Nguồn: `D:\recsys_data\poc\poc6_{random80_20,temporal_global,leave_one_out}.json`, chạy 2026-11-15 18:14–18:20.

| Chỉ số | random80_20 | temporal_global | leave_one_out |
|---|---|---|---|
| `train_rows` | 19.997.974 | 19.999.279 | 24.837.554 |
| `test_rows` | 5.002.121 | 5.000.816 | 162.541 |
| `temporal_violation_global_pct` | 100,0000 | 0,0000 | 99,9988 |
| `temporal_violation_user_pct` | 98,9158 | 0,0000 | 0,0000 |
| `unseen_item_pct` | 0,0573 | 8,7595 | 0,0388 |
| `coldstart_user_rows` | 0 | 4.235.246 | 0 |
| `eval_users` | 162.541 | 137.839 | 162.541 |
| `eval_relevant_users` | 158.692 | 6.219 | 96.003 |
| Popularity `ndcg10` | 0,0852 | 0,0455 | 0,0183 |
| ALS `ndcg10` | 0,2556 | 0,1311 | 0,0467 |
| ALS `hit_rate10` | 0,2901 | 0,1595 | 0,0135 |
| ALS `popularity_bias_ratio` | 12,6285 | 10,6271 | 12,7596 |
| ALS `fit_seconds` | 34,6 | 88,1 | 95,7 |

**Sai lệch chấp nhận:** `random80_20` dùng `F.rand(seed)` không kèm partition seed → số có thể lệch nhỏ nếu `spark.sql.shuffle.partitions` khác 8. Assert với dung sai, không `==` tuyệt đối. Hai split còn lại tất định, assert chặt.

---

## 7. Rủi ro và cách chặn

| Rủi ro | Chặn |
|---|---|
| Notebook 04 ghi 3 split chiếm ~600 MB | Đo dung lượng trong cell 6; đĩa D: còn 44,3 GB. Ghi xong đọc lại verify, không giữ bản trung gian |
| Spark session cũ còn sống khi đổi `spark.local.dir` | `get_spark` kiểm tra `SparkSession.getActiveSession()`; nếu có mà config khác → `stop` + tạo lại |
| ALS fit lại 3 lần tốn ~220 giây | Notebook 08 cho chọn `SPLITS_TO_RUN`; mặc định cả 3, ghi rõ |
| `approxQuantile` trả xấp xỉ | Không dùng để assert; chỉ dùng để mô tả. P80 của temporal lấy bằng `percentile_approx` như script gốc, ghi rõ là xấp xỉ |
| Số NDCG lệch so với poc6 | So sánh trước khi kết luận: khác do partition/seed hay do logic? Nếu logic khác, dừng, sửa về khớp script gốc |

---

## 8. Việc cần điều chỉnh ở docs (sau khi notebook chạy)

| File | Sửa gì |
|---|---|
| `Implementation/00_Notebook_First_Plan.md` | Bảng notebook flow: đổi 04–09 thành tên thật (`04_build_splits`, `05_audit_split_leakage`, `06_mostpopular_baseline`, `07_ndcg_manual_check`, `08_als_implicit`, `09_compare_and_reversal`); bỏ nhãn "Blocked pending protocol decisions" ở 04 vì protocol đã chốt; ghi `src/audit/*` là nơi chứa logic |
| `notebooks/jupyter/README.md` | Thêm dòng trạng thái 04–09 + run ID sau khi chạy |
| `00_QUICKSTART.md` | Cảnh báo đầu file nói "chưa xác minh Spark ghi Parquet trên Windows" → đã xác minh, cập nhật điều kiện `HADOOP_HOME` + `winutils.exe` + `hadoop.dll` |
| `Main/Environment.md` | Thêm mục công cụ: `D:\recsys_data\tools\hadoop\bin\{winutils.exe,hadoop.dll}` và biến `HADOOP_HOME` |
| `Main/MetErrors/io.md` | Sửa kết luận "không dùng `df.write.parquet`" → dùng được khi có đủ 2 binary; giữ pyarrow cho ingest |
| `Main/MetErrors/python.md` | Thêm mục kernel/`HADOOP_HOME` nếu phát sinh lỗi mới |

---

## 9. Thứ tự thực thi

1. Viết `src/utils/spark_utils.py`, `src/audit/{__init__,splits,leakage,popularity,metrics,als_rec,io}.py`.
2. Viết `scripts/generate_notebook_04.py` … `generate_notebook_09.py` theo đúng khuôn `generate_notebook_00..03.py` (helper `md()`/`code()`, `id` cell, `compile()` kiểm tra, kernelspec `recsys-project-venv`).
3. Chạy generator, mở từng notebook bằng kernel project, chạy tuần tự 04 → 09.
4. Đối chiếu số với §6; lệch thì dừng và truy nguyên trước khi sang notebook sau.
5. Cập nhật docs theo §8.

**Không làm trong đợt này:** ItemKNN, BPR, SASRec/EASE (Ba tầng baseline Bài 03), ma trận 3 seed, MapReduce/HDFS. Các phần đó tách đợt sau để Gate L4–L7 đóng trước.
