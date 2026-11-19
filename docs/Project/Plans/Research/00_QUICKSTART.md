# Quickstart — Bắt đầu từ con số 0

> **Đã thay thế cho luồng học/chạy hiện tại.** Bắt đầu tại [`Implementation/00_Notebook_First_Plan.md`](Implementation/00_Notebook_First_Plan.md). Hướng dẫn cũ bên dưới dùng script; phần notebook 00–09 là luồng chính thức.
>
> **Cập nhật 2026-11-15:** Spark ghi Parquet trên Windows **đã verify được**. Cần đủ `winutils.exe` + `hadoop.dll` trong `D:\recsys_data\tools\hadoop\bin` và `HADOOP_HOME` trỏ tới thư mục đó; `src/utils/spark_utils.ensure_hadoop_home()` tự set. Chi tiết: [MetErrors/io.md](../Main/MetErrors/io.md).

**Mục tiêu:** Chạy được pipeline đầu tiên từ tải dataset → Spark → kết quả đầu tiên trong 1-2 giờ.

**Nguyên tắc:** Không bỏ qua bước nào. Mỗi bước có checkpoint rõ ràng.

---

## Bước 0: Kiểm tra môi trường

**Cần có sẵn:**
- ✅ Python 3.10+ (đã có)
- ✅ Java JDK (đã có, cần cho Spark)
- ✅ Docker Desktop (đã có, cho Hadoop cluster)

**Kiểm tra:**
```powershell
python --version          # Python 3.11 trở lên
java -version            # Java 17 hoặc 24
docker --version         # Docker 28.x
```

**Checkpoint G0:** Cả 3 lệnh chạy không lỗi → Sang Bước 1.

---

## Bước 1: Tải MovieLens-25M dataset

**Dataset chính thức:** [GroupLens MovieLens 25M](https://grouplens.org/datasets/movielens/25m/)

**Tải về:**
```powershell
# Tạo thư mục data
New-Item -ItemType Directory -Force -Path "D:\recsys_data\raw"

# Tải zip (262 MB)
# Cách 1: Dùng trình duyệt tải về https://files.grouplens.org/datasets/movielens/ml-25m.zip
# Cách 2: PowerShell (nếu không bị chặn)
Invoke-WebRequest -Uri "https://files.grouplens.org/datasets/movielens/ml-25m.zip" `
  -OutFile "D:\recsys_data\raw\ml-25m.zip"

# Giải nén
Expand-Archive -Path "D:\recsys_data\raw\ml-25m.zip" `
  -DestinationPath "D:\recsys_data\raw\" -Force
```

**Kiểm tra:**
```powershell
Get-ChildItem "D:\recsys_data\raw\ml-25m"
```

Phải thấy:
- `ratings.csv` (678 MB)
- `movies.csv`
- `tags.csv`
- `links.csv`
- `README.txt`

**Checkpoint G1:** File `ratings.csv` tồn tại và ~678 MB → Sang Bước 2.

---

## Bước 2: Cài đặt Python packages

**File requirements tối thiểu:**
```powershell
# Tạo requirements.txt
@"
pyspark==4.2.0
pandas==2.2.3
numpy==2.1.3
scipy==1.14.1
scikit-learn==1.5.2
pymongo==4.10.1
"@ | Set-Content -Path "D:\Master Exers\Big Data\Recomendation_System\requirements_minimal.txt" -Encoding UTF8

# Cài đặt
cd "D:\Master Exers\Big Data\Recomendation_System"
pip install -r requirements_minimal.txt
```

**Kiểm tra:**
```powershell
python -c "import pyspark; print(pyspark.__version__)"
```

Phải in ra: `4.2.0`

**Checkpoint G2:** PySpark import không lỗi → Sang Bước 3.

---

## Bước 3: Smoke test — Đọc CSV bằng Spark local

**Script đơn giản nhất:** `scripts/00_smoke_test.py`

```python
"""Smoke test: Đọc ratings.csv bằng Spark local, đếm dòng."""
import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
os.environ['PYSPARK_PYTHON'] = sys.executable

from pyspark.sql import SparkSession
import time

# Tạo Spark session local
spark = (SparkSession.builder
         .appName("SmokeTest")
         .master("local[4]")
         .config("spark.driver.memory", "6g")
         .config("spark.sql.shuffle.partitions", "8")
         .getOrCreate())

spark.sparkContext.setLogLevel("ERROR")

print("=== Smoke Test: Đọc MovieLens-25M ===")
t0 = time.time()

# Đọc ratings.csv
df = spark.read.csv(
    "D:/recsys_data/raw/ml-25m/ratings.csv",
    header=True,
    inferSchema=True
)

# Đếm dòng
n = df.count()
elapsed = time.time() - t0

print(f"✓ Đọc xong: {n:,} ratings trong {elapsed:.1f} giây")
print(f"✓ Schema: {df.columns}")
print(f"✓ Mẫu 5 dòng:")
df.show(5, truncate=False)

spark.stop()
print("✓ Smoke test PASS")
```

**Chạy:**
```powershell
python scripts/00_smoke_test.py
```

**Kết quả mong đợi:**
```
✓ Đọc xong: 25,000,095 ratings trong ~30 giây
✓ Schema: ['userId', 'movieId', 'rating', 'timestamp']
✓ Mẫu 5 dòng: ...
✓ Smoke test PASS
```

**Checkpoint G3:** Script chạy xong, in ra đúng 25,000,095 dòng → Sang Bước 4.

---

## Bước 4: Chia train/test đơn giản — Random 80/20

**Script:** `scripts/01_split_random.py`

```python
"""Chia random 80/20, lưu parquet."""
import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
os.environ['PYSPARK_PYTHON'] = sys.executable

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import time

spark = (SparkSession.builder
         .appName("SplitRandom")
         .master("local[4]")
         .config("spark.driver.memory", "6g")
         .config("spark.sql.shuffle.partitions", "8")
         .getOrCreate())

spark.sparkContext.setLogLevel("ERROR")

print("=== Bước 4: Chia random 80/20 ===")
t0 = time.time()

# Đọc CSV
df = spark.read.csv(
    "D:/recsys_data/raw/ml-25m/ratings.csv",
    header=True,
    inferSchema=True
).select("userId", "movieId", "rating", "timestamp")

print(f"Tổng: {df.count():,} ratings")

# Chia random 80/20 với seed cố định
df = df.withColumn("is_test", F.rand(42) > F.lit(0.8))

train = df.filter(~F.col("is_test")).select("userId", "movieId", "rating", "timestamp")
test = df.filter(F.col("is_test")).select("userId", "movieId", "rating", "timestamp")

train_n = train.count()
test_n = test.count()

print(f"Train: {train_n:,} ({100*train_n/25000095:.1f}%)")
print(f"Test:  {test_n:,} ({100*test_n/25000095:.1f}%)")

# Lưu parquet
OUT = "D:/recsys_data/splits/random80_20"
os.makedirs(OUT, exist_ok=True)

print("Đang lưu train parquet...")
train.write.mode("overwrite").parquet(f"{OUT}/train.parquet")

print("Đang lưu test parquet...")
test.write.mode("overwrite").parquet(f"{OUT}/test.parquet")

elapsed = time.time() - t0
print(f"✓ Hoàn tất trong {elapsed:.1f} giây")
print(f"✓ Parquet lưu tại: {OUT}")

spark.stop()
```

**Chạy:**
```powershell
python scripts/01_split_random.py
```

**Kết quả mong đợi:**
```
Train: ~20,000,000 (80%)
Test:  ~5,000,000 (20%)
✓ Hoàn tất trong ~60 giây
✓ Parquet lưu tại: D:/recsys_data/splits/random80_20
```

**Checkpoint G4:** File `train.parquet` và `test.parquet` tồn tại → Sang Bước 5.

---

## Bước 5: Baseline đầu tiên — MostPopular

**Ý tưởng:**
- Gợi ý Top 10 phim được rate nhiều nhất trong train
- Đo NDCG@10 trên test
- Không cần GPU, chạy ~5 phút

**Script:** `scripts/02_baseline_popularity.py`

```python
"""Baseline MostPopular: Top-10 phim phổ biến nhất."""
import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
os.environ['PYSPARK_PYTHON'] = sys.executable

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import numpy as np
import time, json

spark = (SparkSession.builder
         .appName("PopularityBaseline")
         .master("local[4]")
         .config("spark.driver.memory", "6g")
         .config("spark.sql.shuffle.partitions", "8")
         .getOrCreate())

spark.sparkContext.setLogLevel("ERROR")

print("=== Bước 5: MostPopular Baseline ===")
t0 = time.time()

SPLIT = "random80_20"
TOPN = 10
THR = 4.0
MIN_TRAIN = 5

# Đọc train/test
train = spark.read.parquet(f"D:/recsys_data/splits/{SPLIT}/train.parquet")
test = spark.read.parquet(f"D:/recsys_data/splits/{SPLIT}/test.parquet")

print(f"Train: {train.count():,}, Test: {test.count():,}")

# User đủ điều kiện (train ≥5 ratings)
elig = train.groupBy("userId").count() \
    .filter(F.col("count") >= F.lit(MIN_TRAIN)) \
    .select("userId")
elig_n = elig.count()
print(f"Eligible users: {elig_n:,}")

# Top-10 phim phổ biến
popdf = train.groupBy("movieId").count() \
    .withColumnRenamed("count", "pop") \
    .orderBy(F.col("pop").desc(), F.col("movieId").asc()) \
    .limit(TOPN)

top_ids = [int(r["movieId"]) for r in popdf.collect()]
print(f"Top-{TOPN} phim: {top_ids}")

# Test relevant (rating ≥4)
te = test.join(F.broadcast(elig), "userId") \
    .filter(F.col("rating") >= F.lit(THR))

# Tính NDCG@10
gexpr = " + ".join(f"if(movieId = {m}, 1.0/log2({i+2}), 0.0)"
                   for i, m in enumerate(top_ids))
te = te.withColumn("dcg", F.expr(gexpr))

per_user = te.groupBy("userId").agg(
    F.sum("dcg").alias("dcg"),
    F.count("*").alias("nrel")
)

idcg_terms = ", ".join(f"1.0/log2({i+2})" for i in range(TOPN))
per_user = per_user.withColumn(
    "idcg",
    F.expr(f"aggregate(slice(array({idcg_terms}), 1, least(nrel, {TOPN})), 0D, (acc, x) -> acc + x)")
)

per_user = per_user.withColumn(
    "ndcg",
    F.when(F.col("idcg") > 0, F.col("dcg") / F.col("idcg")).otherwise(0.0)
)

agg = per_user.agg(
    F.count("*").alias("users"),
    F.avg("ndcg").alias("ndcg10")
).first()

ndcg10 = float(agg["ndcg10"] or 0)
eval_users = int(agg["users"] or 0)

elapsed = time.time() - t0

result = {
    "split": SPLIT,
    "model": "MostPopular",
    "topn": TOPN,
    "threshold": THR,
    "min_train": MIN_TRAIN,
    "ndcg10": round(ndcg10, 4),
    "eval_users": eval_users,
    "eligible_users": elig_n,
    "elapsed_sec": round(elapsed, 1)
}

print(json.dumps(result, indent=2, ensure_ascii=False))

# Lưu kết quả
OUT = "D:/recsys_data/results"
os.makedirs(OUT, exist_ok=True)
with open(f"{OUT}/popularity_{SPLIT}.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"✓ Kết quả lưu tại: {OUT}/popularity_{SPLIT}.json")
spark.stop()
```

**Chạy:**
```powershell
python scripts/02_baseline_popularity.py
```

**Kết quả mong đợi:**
```json
{
  "split": "random80_20",
  "model": "MostPopular",
  "ndcg10": 0.0532,
  "eval_users": 29000,
  "elapsed_sec": 45.2
}
```

**Checkpoint G5:** File JSON có `ndcg10` > 0 → **Xong flow cơ bản!**

---

## Bước 6: Hiểu được gì từ 5 bước trên

**Flow tổng thể:**
```
CSV → Spark read → Split → Parquet → Baseline → Metrics → JSON
```

**Ba thành phần chính:**
1. **Data pipeline:** CSV → Parquet (bước 3-4)
2. **Model:** MostPopular (bước 5)
3. **Evaluation:** NDCG@10 (bước 5)

**Tại sao dùng Parquet:**
- CSV đọc chậm, Parquet nhanh hơn ~5-10 lần
- Spark ghi Parquet không cần `winutils.exe` (dùng pyarrow backend)

**Metric NDCG@10:**
- Đo thứ hạng Top-10 gợi ý
- Discount logarit: vị trí càng cao càng quan trọng
- `ndcg10=0.0532` nghĩa là 5.32% "chất lượng lý tưởng"

---

## Bước 7: Tiếp theo làm gì?

**Ba việc tiếp:**

1. **Thêm baseline ALS** (matrix factorization):
   - Script `scripts/03_baseline_als.py`
   - Chạy ~10-15 phút
   - So sánh NDCG ALS vs MostPopular

2. **Thêm split `temporal_global` và `leave_one_out`:**
   - Copy `01_split_random.py` → sửa logic chia
   - Chạy lại baseline trên 3 split
   - So sánh kết quả → trả lời RQ1

3. **Thêm seed và kiểm định thống kê:**
   - Chạy mỗi split × 3 seed (42, 2024, 7)
   - Tính Mean ± SD
   - Paired t-test hoặc Wilcoxon

---

## Giải thích thuật ngữ

**Spark local[4]:**
- Chạy Spark trên 1 máy với 4 CPU core
- Không cần cluster Hadoop (dùng sau cho RQ3)

**Parquet:**
- Format lưu trữ dạng cột, nén tốt
- Đọc nhanh hơn CSV ~5-10 lần

**NDCG@10 (Normalized Discounted Cumulative Gain):**
- Độ đo chuẩn cho ranking
- Công thức: DCG = Σ(rel_i / log2(i+1))
- Chuẩn hóa bằng IDCG (lý tưởng)
- Giá trị [0, 1], càng cao càng tốt

**Eligible users:**
- User có ≥5 ratings trong train
- Loại user quá ít data (không đủ học)

**Relevant items:**
- Item có rating ≥4.0 trong test
- Xem như "user thích" → dùng làm ground truth

---

## Checklist tự kiểm tra

Đã đạt được:
- [ ] G0: Python/Java/Docker chạy được
- [ ] G1: File `ratings.csv` 678 MB tồn tại
- [ ] G2: PySpark import không lỗi
- [ ] G3: Smoke test đọc được 25M ratings
- [ ] G4: Parquet train/test đã lưu
- [ ] G5: MostPopular có kết quả NDCG > 0

**Nếu đạt đủ 6 ô → Bạn đã hiểu flow cơ bản.**

Tiếp theo đọc:
- `01_De_tai_va_Ke_hoach.md` — Hiểu RQ1/RQ2/RQ3
- `05_Ke_hoach_thuc_nghiem.md` — Ma trận 3 split × 5 model đã đăng kí (Random, MostPopular, ALS, ItemKNN, SASRec+CE) × 1 seed (42), 20 cặp Wilcoxon
- `05C_Baseline_3_tang_DSRM.md` — Ba tầng baseline (sàn/kinh điển/SOTA)

---

**Ghi chú quan trọng:**

1. **Không cần Hadoop/HDFS ngay:**
   Spark local đủ cho phân tích ban đầu. HDFS dùng sau cho RQ3 (Big Data metrics).

2. **Dataset không commit vào git:**
   `ml-25m/` và `splits/` nằm ngoài repo (file lớn + license không cho redistribute).

3. **Nếu bị lỗi encoding:**
   Luôn thêm đầu script:
   ```python
   sys.stdout.reconfigure(encoding='utf-8', errors='replace')
   ```

4. **RAM cần ~10 GB free:**
   Spark driver 6g + overhead ~4g. Nếu thiếu RAM, giảm `spark.driver.memory` xuống `4g`.

---

**Có câu hỏi về bước nào?**
Hỏi ngay trước khi sang bước tiếp.

