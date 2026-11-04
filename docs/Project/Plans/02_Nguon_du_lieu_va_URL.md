# 02 — Nguồn dữ liệu và URL (đã kiểm chứng 2026-11-03)

**Project:** `D:\Master Exers\Big Data\Recomendation_System`
**Nguồn dữ liệu chính:** MovieLens **ml-25m** (GroupLens, University of Minnesota)

---

## 1. Quyết định dataset

| Tiêu chí | Ứng viên A: Amazon Reviews 2023 | Ứng viên B: MovieLens ml-25m ✅ |
|---|---|---|
| Số quan sát gốc | ~701K (All_Beauty, 1 category) | **25.000.095 ratings** |
| Mật độ tương tác | quá thưa | dày, đủ cho implicit CF |
| Có timestamp | có | **có (1995-01-09 → 2019-11-21)** |
| Người dùng | không rõ | **162.541 users, ≥20 ratings/user** |
| Item | không rõ | **59.047 movies có rating** (+62.423 tổng) |
| License | khó tra (không rõ tag) | **rõ ràng, research-use, có DOI cite** |
| Truy cập | HF gated-ish | tải trực tiếp, không auth |

**Kết luận:** chọn **ml-25m**. Lý do quyết định:
1. Đề tài cần **timestamp thật** để nghiên cứu chiến lược split — ml-25m có timestamp Unix chuẩn.
2. Quy mô 25M rating đủ để **Spark thật sự có ý nghĩa** (không phải demo toy). Đây là yêu cầu môn Big Data.
3. Mỗi user ≥20 rating → hạn chế cold-start user, tập trung được vào **split-strategy** chứ không phải vào bản thân CF.
4. License research-use rõ ràng → không rủi ro pháp lý cho đồ án.

**Loại Amazon 2023:** PoC chạy thật trên `All_Beauty` cho kết quả 5-core chỉ còn **4.240 dòng / 477 user / 610 item** (từ 701.528 dòng gốc). Quá nhỏ để kết luận khoa học, và tỷ lệ "user/item chưa từng xuất hiện ở tập train" quá lớn để đo split-strategy một cách sạch.

---

## 2. Nguồn tải (đã tải thật, không giả định)

| Mục | URL | Trạng thái verify |
|---|---|---|
| Trang dataset | `https://grouplens.org/datasets/movielens/25m/` | OK |
| File zip | `https://files.grouplens.org/datasets/movielens/ml-25m.zip` | **OK — 261.978.986 bytes, tải 806s** |
| Bài báo gốc (bắt buộc cite) | Harper & Konstan (2015) *The MovieLens Datasets: History and Context*, ACM TiiS 5(4), 19:1–19:19 — **DOI `10.1145/2827872`** | OK |

**Nơi lưu:** `D:\recsys_data\raw\ml-25m\`
- `ml-25m.zip` — 262 MB (giữ lại để reproduce, không commit git)
- `ml-25m/ratings.csv` — 678.260.987 bytes
- `ml-25m/movies.csv` — 3.038.099 bytes
- `ml-25m/tags.csv` — 38.810.332 bytes
- `ml-25m/genome-scores.csv` — 435.164.157 bytes
- `ml-25m/genome-tags.csv` — 18.103 bytes
- `ml-25m/links.csv` — 1.368.578 bytes
- `ml-25m/README.txt` — 10.460 bytes

---

## 3. Schema (verify từ README.txt + đếm dòng thật)

### 3.1 `ratings.csv` (bảng chính — 25.000.095 dòng)

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `userId` | INT | định danh người dùng (đã anonymize) |
| `movieId` | INT | định danh phim |
| `rating` | DOUBLE | điểm 0.5–5.0, thang 5 sao |
| `timestamp` | INT | Unix seconds, thời điểm đánh giá |

Đo thật bằng Spark 4.2.0 (`_poc2_spark.py`):
```
raw rows: 25000095
ts range: 1995-01-09 11:46:49  ->  2019-11-21 09:15:03
users: 162541
items: 59047
```

### 3.2 `movies.csv` (62.423 phim)

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `movieId` | INT | khóa ngoại → `ratings.movieId` |
| `title` | STRING | tên phim kèm năm, **có dấu tiếng Đức** (`$` ký tự escape kiểu CSV) |
| `genres` | STRING | pipe-delimited, ví dụ `Action\|Adventure\|Sci-Fi` |

### 3.3 `tags.csv` (1.093.360 tag application)

`userId, movieId, tag, timestamp` — dùng cho **side-information** (content-based hybrid), không bắt buộc cho PoC split-strategy.

### 3.4 `genome-scores.csv` (435 MB)

`movieId, tagId, score` — relevance score của tag so với phim, dùng cho **content-based re-ranker**. Quá nặng cho phạm vi đồ án → chỉ nạp nếu có thời gian.

### 3.5 `links.csv`
`movieId, imdbId, tmdbId` — định danh phim ở nguồn ngoài. Dùng để join metadata nếu cần.

---

## 4. License và ràng buộc đạo đức (trích nguyên văn `README.txt`)

> "The data set may be used for any research purposes under the following conditions:
> - The user may not state or imply any endorsement from the University of Minnesota or the GroupLens Research Group.
> - The user must acknowledge the use of the data set in publications resulting from the use of the data set.
> - The user may not redistribute the data without separate permission.
> - The user may not use this information for any commercial or revenue-bearing purposes without first obtaining permission…"

**Cách tuân thủ trong đồ án:**
1. **Trích dẫn bắt buộc** mỗi lần dùng: Harper, F. M., & Konstan, J. A. (2015). *The MovieLens Datasets: History and Context*. ACM Transactions on Interactive Intelligent Systems (TiiS), 5(4), Article 19. https://doi.org/10.1145/2827872
2. **Không** khẳng định GroupLens/Đại học Minnesota bảo trợ hay chấp thuận đề tài.
3. **Không redistribute** file gốc → `.gitignore` loại `data/raw/`, chỉ commit mã + manifest + checksum.
4. Chỉ dùng cho **mục đích nghiên cứu học thuật, không thương mại**.
5. Ghi rõ trong báo cáo: dữ liệu đã anonymize, không có thuộc tính nhân khẩu học → **không có rủi ro đạo đức cá nhân**, không cần IRB.

---

## 5. Dataset dự phòng (không tải trước, chỉ khi cần)

| Dataset | Vai trò | Trạng thái |
|---|---|---|
| Amazon Reviews 2023 (`McAuley-Lab/Amazon-Reviews-2023`) | cross-domain: chứng minh hiện tượng không riêng của phim | HF có sẵn; PoC All_Beauty đã chạy được nhưng dữ liệu thưa |
| Steam reviews (132.976.950 bytes) | cross-domain, khác tỷ lệ user/item | mirror `mcauleylab.ucsd.edu` OK |
| Retailrocket | cross-domain, hành vi click không phải rating | Kaggle endpoint **404** → loại; mirror HF `DanielKiani/RetailRocket-Recommender-Data` |
| Yelp (`yelp_review_full`) | cross-domain, đánh giá dịch vụ | train.parquet 299 MB OK; `yelp_business` **401 gated** |

**Lưu ý:** nếu cross-domain, phải dùng **cùng một logic split** (cùng script, cùng metric) để so sánh được. Không đổi dataset giữa chừng.

---

## 6. Lỗi cần tránh (đã gặp)

1. **ALS yêu cầu `userId`/`itemId` kiểu NUMERIC.** Bản `All_Beauty` của Amazon dùng chuỗi → `IllegalArgumentException: requirement failed: Column user_id must be of type numeric but was actually of type string`. → Phải ép kiểu trước khi fit ALS. ml-25m vốn đã là INT nên không vướng.
2. **Không đọc file 678 MB vào RAM bằng `read`/pandas trong exec** → bị SIGKILL. Dùng `spark.read.csv` (Spark tự stream) hoặc `pandas.read_csv(chunksize=...)`.
3. **PowerShell redirect tạo UTF-16** → luôn bọc `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")`.
4. `hadoop.home.dir` unset → warning `Did not find winutils.exe`; **không chặn job local mode**, nhưng nếu đọc/ghi HDFS thật thì phải set `HADOOP_HOME` trỏ vào container Hadoop.
5. `pandas >= 3.0.0` chưa được PySpark hỗ trợ đầy đủ → warning, không chặn; tránh dùng pandas API trong Spark context.
6. `df.withColumn` cần import `F` từ `pyspark.sql.functions`; `transform` với lambda chỉ dùng cho column dạng array của kiểu cấu trúc.

---

## 7. Checksum để tái lập

Tạo file `data/raw/CHECKSUMS.sha256` sau khi tải (lệnh `Get-FileHash -Algorithm SHA256`), commit file này (chỉ chứa hash, không chứa dữ liệu).
