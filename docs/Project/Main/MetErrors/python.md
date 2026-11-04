# Error Log — Python, pandas, sklearn, PySpark

Lỗi ở tầng ngôn ngữ và thư viện. Ghi lại vì chúng sẽ tái diễn khi chạy lại pipeline.

Format: `### [YYYY-MM-DD] [Category] Title` → Vấn đề / Nguyên nhân / Giải pháp

---

## 1. Python built-ins

### [2026-10-29] [Import] `importlib.util` không có sau `import importlib`

- **Vấn đề:**
  ```
  AttributeError: module 'importlib' has no attribute 'util'
  ```
- **Nguyên nhân:** `import importlib` **không** tự import submodule `importlib.util`.
- **Giải pháp:**
  ```python
  import importlib.util                      # đúng
  from importlib import util                 # hoặc
  ```
- **Bài học:** submodule của stdlib thường phải import tường minh.

### [2026-10-29] [Type] `int | None` chỉ chạy từ Python 3.10

- **Vấn đề:** `def f(x: int | None = None)` raise `TypeError` trên Python ≤3.9.
- **Bối cảnh:** Máy này Python 3.14.5, nên OK. Nhưng nếu chạy trên Colab/VM cũ thì hỏng.
- **Giải pháp:** Đã đặt `from __future__ import annotations` ở đầu mọi module → không
  evaluate annotation lúc runtime, tương thích ngược.

### [2026-10-29] [Unicode] Console cp1252 làm hỏng log tiếng Việt

- **Vấn đề:** `UnicodeEncodeError: 'charmap' codec can't encode character`.
- **Giải pháp:** `$env:PYTHONIOENCODING="utf-8"` + `python -u`. Xem `io.md` §3.

---

## 2. pandas 3.0

### [2026-10-29] [pandas] `read_csv` với file 6,34 GB không khả thi

- **Vấn đề:** `pd.read_csv("mdrfoiThru2025.txt")` cần ~15–20 GB RAM cho 23,6M dòng × 86 cột.
  Máy còn 10,5 GB trống → `MemoryError` hoặc swap chết.
- **Giải pháp:** Streaming generator (`src/data/io.py:read_maude`), batch 200.000 dòng
  → `pyarrow.parquet.ParquetWriter`. Hoặc PySpark.
- **Bài học:** Ở quy mô này pandas không phải công cụ sai — nó là công cụ **sai tầng**.

### [2026-10-29] [pandas] `na_values` mặc định biến chuỗi rỗng thành `NaN`

- **Vấn đề:** MAUDE dùng chuỗi rỗng làm null. `read_csv` mặc định coi `""` là `NaN`.
- **Hệ quả:** Ghi parquet thành `null`, mất phân biệt "rỗng" và "không tồn tại".
- **Giải pháp:** `keep_default_na=False, na_values=[]`.

### [2026-10-29] [pandas] Suy luận kiểu làm mất `PATIENT_AGE` dạng text

- **Vấn đề:** `PATIENT_AGE` có `"056"`, `"5 months"`, `"U"`. `read_csv` suy ra `float64` →
  `"5 months"` thành `NaN`.
- **Giải pháp:** Đọc mọi cột là `string`, ép kiểu sau với luật viết tay.

---

## 3. scikit-learn

### [2026-10-29] [sklearn] `LogisticRegression(multi_class=...)` đã deprecate

- **Vấn đề:** `FutureWarning: 'multi_class' was deprecated in 1.5 and will be removed in 1.7`.
- **Bối cảnh:** Máy này sklearn 1.9.0 — tham số **đã bị bỏ**, không chỉ warning.
- **Giải pháp:** Bỏ `multi_class`; multinomial là mặc định với `lbfgs` từ 1.5.
  Nếu cần one-vs-rest thì dùng `OneVsRestClassifier`.
- **Trạng thái:** ✅ **đã sửa** (2026-10-30). `scripts/s6_rq2.py` dòng 154 có comment
  `# sklearn >= 1.5: 'multi_class' is removed; lbfgs is multinomial by default.`
  và không còn truyền tham số này.

### [2026-10-29] [sklearn] `f1_score(labels=...)` với nhãn vắng mặt

- **Vấn đề:** Nếu test set không có lớp `D` nào, `f1_score(average=None)` trả mảng ngắn hơn.
- **Giải pháp:** Luôn truyền `labels=LABELS` và `zero_division=0`.
  `scripts/s6_rq2.py` đã làm.

### [2026-10-29] [sklearn] TF-IDF trên 10,8M document — `max_features` là bắt buộc

- **Vấn đề:** Vocabulary thật của 10,8M narrative có thể >2M token. Không giới hạn → OOM.
- **Giải pháp:** `max_features=300_000`, `min_df=3`.

### [2026-10-29] [sklearn] `MultiLabelBinarizer` với danh sách rỗng

- **Vấn đề:** Báo cáo không có mã nào → list rỗng. `mlb.transform([[]])` cần
  `classes_` đã fit.
- **Giải pháp:** Fit trên **toàn bộ** danh sách (kể cả rỗng) trước, transform sau.
  `scripts/s6_rq2.py` dùng `sorted(dev.get(k, ()))`.

---

## 4. PySpark

### [2026-10-29] [Spark] Windows thiếu `winutils.exe` / `HADOOP_HOME`

- **Vấn đề:**
  ```
  java.io.IOException: Could not locate executable null\bin\winutils.exe
  ```
- **Nguyên nhân:** Spark cần Hadoop native binary trên Windows.
- **Giải pháp:**
  ```powershell
  # tải winutils.exe tương ứng Hadoop 3.3.x, đặt vào C:\hadoop\bin\
  $env:HADOOP_HOME = "C:\hadoop"
  $env:PATH = "C:\hadoop\bin;$env:PATH"
  ```
- **Trạng thái:** **chưa kiểm tra** trên máy này — sẽ gặp ở giai đoạn 3.

### [2026-10-29] [Spark] `defaultParallelism = 2` dù máy có 16 core

- **Vấn đề:** Spark mặc định 2 task song song → chậm.
- **Giải pháp:** `--master "local[8]"` (không dùng `local[*]` để chừa RAM cho OS).
- **Ghi chú:** Project Prompt Injection đo được `local[4]` là điểm cân bằng.

### [2026-10-29] [Spark] Driver OOM khi xử lý 10,8M dòng

- **Vấn đề:** `java.lang.OutOfMemoryError: Java heap space` ở driver.
- **Giải pháp:**
  ```
  --driver-memory 10g
  --conf spark.local.dir=D:\spark_tmp
  --conf spark.driver.maxResultSize=2g
  ```
- **Bài học (từ project trước):** luôn đặt `spark.local.dir` ra ổ D:, mặc định là `C:\tmp`
  và sẽ đầy.

### [2026-10-29] [Spark] `pyspark` + `pandas 3.0` — tương thích chưa chắc

- **Vấn đề:** `pyspark.sql.pandas` (Arrow-based) có thể không tương thích pandas 3.0.
- **Trạng thái:** chưa test. Nếu hỏng: dùng `df.rdd` thay vì `toPandas()`.

---

## 5. MongoDB / pymongo

### [2026-10-29] [Mongo] Service không tự start

- **Vấn đề:** `MongoClient()` treo hoặc `ServerSelectionTimeoutError`.
- **Nguyên nhân:** Service `MongoDB` để `StartType = Manual`.
- **Giải pháp:** `Start-Service MongoDB` trước khi chạy `s3_load_mongo.py`.
  Script đã `ping()` và in hướng dẫn nếu không kết nối được.

### [2026-10-29] [Mongo] 23,6M document — phải dùng `bulk_write` không `insert_one`

- **Vấn đề:** `insert_one` 23,6M lần = 23,6M round-trip → vài ngày.
- **Giải pháp:** `bulk_write([UpdateOne(...)], ordered=False)`, batch 50.000.
  `ordered=False` cho phép MongoDB chạy song song và không dừng ở lỗi đầu.

### [2026-10-29] [Mongo] `$push` vào mảng lồng mà document chưa tồn tại

- **Vấn đề:** `update_one({"records.mdr_report_key": k}, {"$push": ...})` không khớp
  document nào nếu chưa có → im lặng không làm gì.
- **Giải pháp:** Nạp `reports` **trước**, enrich **sau**. `s3_load_mongo.py` làm đúng thứ tự.

### [2026-10-29] [Mongo] Index tạo trước khi nạp làm chậm 5–10×

- **Giải pháp:** Nạp xong mới `create_index`. `s3_load_mongo.py` làm vậy.

---

## 6. NumPy / SciPy

### [2026-10-29] [numpy] `np.random.choice` trên list dài 10,8M rất chậm

- **Vấn đề:** `rng.choice(keys, 1_500_000, replace=False)` trên list 10,8M mất vài phút.
- **Giải pháp:** Chuyển sang `np.array` trước, hoặc dùng `rng.permutation` rồi cắt.
- **Trạng thái:** `scripts/s6_rq2.py` đang dùng `rng.choice` — chấp nhận được cho 1 lần chạy.

### [2026-10-29] [scipy] `chi2.sf(x, df=1)` cho p-value của PRR

- **Ghi chú:** Với bảng 2×2, `chi2 = (ad-bc)²·N / ((a+b)(c+d)(a+c)(b+d))`, df=1.
  `scipy.stats.chi2.sf(chi2, 1)` = p-value một phía. Đúng cho BH-FDR.
  `scripts/s7_rq3.py` dùng đúng.

### [2026-10-29] [scipy] `spearmanr(...).statistic` — API mới

- **Vấn đề:** scipy cũ trả tuple `(rho, p)`, scipy 1.18 trả `SignificanceResult`.
- **Giải pháp:** Dùng `.statistic` (đã làm trong `s7_rq3.py`), hoặc `[0]` cho cả hai.

---

## 7. Windows-specific

### [2026-10-29] [Windows] Đường dẫn >260 ký tự

- **Vấn đề:** `OSError: [WinError 206] The filename or extension is too long`.
- **Bối cảnh:** `D:\Master Exers\Big Data\Medical_Equipment\data\interim\...` khá dài.
- **Giải pháp:** Bật long path:
  ```powershell
  # chạy 1 lần với quyền Admin
  New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
    -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
  ```

### [2026-10-29] [Windows] `python` vs `python3`

- **Vấn đề:** `python3` không tồn tại trên Windows mặc định.
- **Giải pháp:** Dùng `python`. Đường dẫn thật:
  `C:\Users\PC\AppData\Local\Python\pythoncore-3.14-64\python.exe`.

### [2026-10-29] [Windows] `Get-Content` mặc định không đọc UTF-8

- **Vấn đề:** File `.md` tiếng Việt hiện thành `?` hoặc ký tự lạ.
- **Giải pháp:** `Get-Content file -Encoding UTF8`. Với file lớn:
  `Get-Content file -TotalCount 50 -Encoding UTF8`.

---

## 8. Bộ nhớ: OOM thật và OOM "trông giống OOM"

### [2026-10-31] [Memory] `Counter` trên 23,1 triệu chuỗi — 2,5 GB cho một histogram

- **Vấn đề:** `scripts/s4_audit.py` bị kill 2 lần. Dòng code gây lỗi:
  ```python
  families = collections.Counter()      # key = REPORT_NUMBER (str)
  ...
  families[rn] += 1                     # 23.1M distinct keys
  fam_sizes = collections.Counter(families.values())
  ```
  Mỗi entry `dict` của Python tốn ~100 byte overhead + object str riêng →
  **~2,5 GB** chỉ để tính phân bố kích thước family.

- **Nguyên nhân:** Nhu cầu thật chỉ là **histogram của số lần xuất hiện**,
  không cần biết chuỗi nào. Giữ chuỗi là giữ dữ liệu không dùng.

- **Giải pháp:** hash về uint64, giữ trong `array.array("Q")`, dùng `np.unique`:
  ```python
  def hash64(s):
      return int.from_bytes(
          hashlib.blake2b(s.encode("latin-1", "replace"), digest_size=8).digest(),
          "little")

  hashes = array.array("Q")          # 8 byte/key thay vì ~100+
  ...
  arr = np.frombuffer(hashes, dtype=np.uint64)
  uniq, counts = np.unique(arr, return_counts=True)
  sizes, size_counts = np.unique(counts, return_counts=True)
  ```
  Kết quả: **185 MB** thay vì 2,5 GB, nhanh hơn.

- **Về rủi ro collision:** 23,1M giá trị trong không gian 2⁶⁴ → kỳ vọng
  ~1,4×10⁻⁵ cặp trùng. Và collision chỉ **gộp 2 family trong histogram**, không
  ảnh hưởng split (split dùng chuỗi thật). Nên chấp nhận được — nhưng **phải ghi
  lý do vào comment**, nếu không người đọc sau sẽ không biết đây là hash.

- **Bài học:** Trước khi "tăng RAM", hỏi: **có thực sự cần giữ key không?**
  Rất nhiều bài toán đếm chỉ cần **tập giá trị** hoặc **histogram**, không cần ánh xạ.

### [2026-10-31] [Memory] `set` 10,8 triệu key — dùng `searchsorted` trên mảng sắp xếp

- **Vấn đề:** Cần kiểm tra "report này có trong cohort không" cho 29 triệu dòng
  mã sự cố. `set` của 10,8M chuỗi → ~1,5 GB.
- **Giải pháp:** Hash cả hai phía về uint64, sort một lần, rồi
  `np.searchsorted` + so sánh:
  ```python
  idx = np.searchsorted(cohort_sorted, q)
  np.clip(idx, 0, cohort_sorted.size - 1, out=idx)
  hit = cohort_sorted[idx] == q
  flags[idx[hit]] = True
  ```
  86 MB thay vì 1,5 GB, và vector hoá được theo batch 2 triệu.
- **Bài học:** Khi cần membership test trên tập lớn **chỉ để lọc**, mảng sắp xếp
  + `searchsorted` là lựa chọn tốt hơn `set` về bộ nhớ, và không chậm hơn.

### [2026-10-31] [Process] `SIGKILL` ở đúng 15 triệu dòng **không phải** OOM

- **Vần đề:** Process chết ở mốc `15,000,000 rows`, log kết thúc bằng
  `Process exited with signal SIGKILL`. Nghĩ ngay là hết RAM.
- **Kiểm chứng:** RAM còn **11,9 / 31,7 GB** trống. Và `WorkingSetSize` của process
  chỉ ~120 MB. **Không phải OOM.**
- **Nguyên nhân thật:** exec session của shell thu hồi process khi vượt ngưỡng.
- **Giải pháp:** chạy detached bằng `Start-Process`. Xem `io.md` §6.
- **Bài học:** **Đo trước khi sửa.** Nếu đã "tối ưu bộ nhớ" mà vẫn chết ở cùng
  một mốc, thì nguyên nhân không phải bộ nhớ. Kiểm tra `WorkingSetSize` và RAM
  trống là hai lệnh đầu tiên, không phải là việc cuối.

### [2026-10-31] [numpy] `np.frombuffer` trên `array.array` — zero-copy, nhưng đừng xoá nguồn

- **Ghi chú:** `np.frombuffer(hashes, dtype=np.uint64)` **không copy**. Nếu `del hashes`
  trước khi dùng xong `arr` thì mảng vẫn trỏ tới bộ nhớ đó; an toàn vì `arr`
  giữ reference. Nhưng nếu buffer là biến tạm trong hàm đã return thì dữ liệu
  có thể bị giải phóng.
- **Quy tắc:** `arr = np.frombuffer(buf, ...)` rồi chỉ `del buf` **sau** khi đã
  `np.sort`/`np.unique` xong (hai hàm này tạo mảng mới).

## 9. RecSys — thống kê và PySpark 4.x (2026-11-04)

### [2026-11-04] [scipy] `Cliff's delta` trên dữ liệu **ghép** không có ý nghĩa + ăn RAM

- **Vấn đề:** Tính Cliff's delta bằng cách so sánh mọi cặp trong vector `diffs` (n = 29.337):

  ```python
  idx = rng.integers(0, n, size=(2000, n))   # (2000, 29337)
  s = d[idx]
  pos = (s[:, :, None] > s[:, None, :]).sum()   # tensor (2000, 29337, 29337)
  ```

  → tensor ~**1,7 tỷ phần tử**, RAM tăng vọt, job treo.

- **Nguyên nhân:** (a) Cliff's delta là chỉ số cho **hai mẫu độc lập**, không phải cho
  dữ liệu **ghép** (paired) như Wilcoxon. (b) Cách tính bằng tensor 3 chiều là O(n²) vô ích.

- **Giải pháp:**
  - Với dữ liệu **ghép** → dùng **rank-biserial correlation** `r = (W+ − W−) / (W+ + W−)`
    (đây chính là hiệu ứng đo lớn chuẩn cho Wilcoxon signed-rank).
  - Bỏ Cliff's delta khỏi pipeline.
  - Thêm **Kendall's tau-b** (`scipy.stats.kendalltau(x, y, variant="b")`, O(n log n))
    để đo **mức độ đồng thay đổi theo cặp** giữa Popularity và ALS.

- **Bài học:** Chọn chỉ số theo **thiết kế thí nghiệm** (độc lập vs ghép), không theo
  "chỉ số nào quen thuộc". Và kiểm tra **complexity** trước khi chạy: tensor 3 chiều
  với n=30k là bằng chứng sai.

### [2026-11-04] [scipy] Metric **hằng số** trên mọi user → `p = 0.0` giả, phải chặn

- **Vấn đề:** `TailCount@10` bằng 0 ở **cả 2 mô hình × cả 3 split** → vector `diffs`
  toàn 0. Kết quả in ra:

  ```
  TailCount@10  pop=0.0000  als=0.0000  diff=+0.0000  p=0.0  SIGNIFICANT
  ```

  → báo **SIGNIFICANT** cho một metric không có variance nào. Sai hoàn toàn.

- **Nguyên nhân:** Normal approximation của Wilcoxon khi toàn bộ hiệu số = 0 cho ra `z = -inf`
  → `p = 0.0`. Không có "khác biệt" nào để kiểm định.

- **Bằng chứng đo được:** `n_nonzero = 0` cho `TailCount@10` ở cả 3 split.

- **Giải pháp (đã sửa trong `scripts/12_stats_tests.py`):**
  ```python
  if n_nonzero == 0:
      return {"W": 0.0, "z": None, "p": None, "n_pairs": int(n), "n_nonzero": 0,
              "median_diff": 0.0, "mean_diff": 0.0,
              "note": "all paired differences are zero - test not applicable"}
  ```
  Kèm cờ `constant_metric: true` và ép `significant_0.05 = false`.

- **Bài học:** `p = 0.0` là kết quả **đáng ngờ**, đặc biệt khi effect size (`dz`, `r`) là
  `None`. Kiểm tra `n_nonzero` và `sd(diffs) == 0` **trước khi** kết luận.

### [2026-11-04] [scipy] Kendall tau-b = `nan` khi một chuỗi hằng số

- **Vấn đề:** `kendalltau(pop_skew, als_skew)` trả `nan` vì `pop_skew` bằng nhau ở mọi user
  (Popularity đề xuất cùng một tập item phổ biến cho mọi user → popularity trung bình
  giống nhau).

- **Giải pháp:** Kiểm tra `np.all(x == x[0])` trước → trả `{"tau_b": None, "p": None,
  "note": "one series is constant - Kendall tau-b undefined"}` thay vì `nan`.

- **Bài học:** `nan` trong output thống kê phải được **giải thích**, không được để nguyên.

### [2026-11-04] [numpy] Bootstrap + Wilcoxon bằng Python thuần chạy > 12 phút

- **Vấn đề:** 10.000 lần bootstrap × 29.337 user × 4 metric × 3 split, vòng lặp Python
  thuần → > 12 phút, bị SIGKILL.

- **Giải pháp:** **Vector hoá** — resample theo **chunk 500** bằng `rng.integers`,
  tính mean theo trục, gom `np.percentile` cho CI. Wilcoxon tính rank bằng **argsort +
  average-rank cho ties** (numpy, không cần `scipy.stats.wilcoxon` vì cần kiểm soát
  trường hợp toàn 0).

- **Kết quả:** rút từ > 12 phút (chết) xuống **~2 phút / split**, đủ dưới trần 30 phút.

- **Bài học:** Trước khi tối ưu thuật toán, hãy **đo** xem thời gian nằm ở đâu. Với
  bootstrap, vector hoá là đủ — không cần viết lại thuật toán.

### [2026-11-04] [scipy] Có `scipy 1.18.0` sẵn — dùng thư viện thay vì tự viết

- **Bài học:** Trước khi tự viết một kiểm định thống kê, **kiểm tra `scipy`** đã có chưa.
  `scipy.stats.kendalltau` có sẵn → viết lại `rank_biserial_and_cliffs` chỉ còn 15 dòng
  thay vì 40 dòng tự tính + tensor 3 chiều.

### [2026-11-04] [Spark] `spark.range(10).col` không tồn tại (PySpark 4.x)

- **Vấn đề:**
  ```python
  PySparkAttributeError: [ATTRIBUTE_NOT_SUPPORTED] Attribute `col` is not supported.
  ```

- **Nguyên nhân:** `col` là hàm của `pyspark.sql.functions`, không phải thuộc tính của
  `Column`. Viết `s.range(10).col % 3` là sai cú pháp.

- **Giải pháp:** `from pyspark.sql import functions as F` → `F.col("id") % 3`.

### [2026-11-04] [Spark] `SparkSession` không tạo lại được sau `stop()` trong cùng JVM

- **Vấn đề:** `scripts/14_perf_benchmark.py` gọi `run_spark_once()` lặp 3 lần, mỗi lần
  tạo `SparkSession` mới và `spark.stop()` → lần 2 crash `IllegalStateException` /
  `SparkSession` không khởi tạo lại được.

- **Giải pháp:** Tách `make_spark()` (tạo **một** session) và `run_spark_once(spark)`
  (nhận session làm tham số). `spark.stop()` **một lần** ở cuối, sau cả 3 lần lặp.

- **Bài học:** Trong benchmark, **session là tài nguyên dùng chung**, không phải tài nguyên
  theo lần lặp.

### [2026-11-04] [Spark] `SparkListener` cho shuffle bytes — cắm qua `_jsc.sc()`

- **Bằng chứng đo được:** đo `shuffleWriteMetrics.bytesWritten` qua listener gắn bằng
  `spark.sparkContext._jsc.sc().addSparkListener(L())`, cộng dồn trong `onTaskEnd`.

- **Lưu ý:** import đúng tên class là `SparkListenerTaskEnd` (không phải
  `SparkListenerRead` / `SparkListenerShuffleRead` — cả 2 đều sai và gây `ImportError`).

### [2026-11-04] [PySpark] `recommendForAllUsers` OOM — đã dùng numpy top-K chunk

- **Bằng chứng:** catalog 59.047 item × 162.541 user = cartesian không nạp nổi.

- **Giải pháp:** `ALS` fit trên mẫu `30.000` user, rồi **numpy top-K** trên `userFactors ×
  itemFactors` chia chunk `2.000` user/lần, `argpartition` thay vì `argsort` toàn bộ.

- **Bài học:** Giữ `seed` cố định và `chunk` cố định thì kết quả **tái lập được**;
  đổi chunk size có thể đổi số thứ hạng sát biên.
