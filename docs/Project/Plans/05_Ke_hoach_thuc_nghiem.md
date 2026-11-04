# 05 — Kế hoạch thực nghiệm

**Project:** `D:\Master Exers\Big Data\Recomendation_System`
**Nguyên tắc:** mọi con số trong báo cáo phải truy được về 1 file log + 1 file JSON kết quả.

---

## 1. Ma trận thực nghiệm

### 1.1 Tầng 0 — Đặc tính dữ liệu (chạy 1 lần)

| Kiểm kê | Giá trị (đo thật 2026-11-03, Spark 4.2.0) |
|---|---|
| Tổng số tương tác | **25.000.095** |
| Số người dùng | **162.541** (mỗi user ≥ 20 rating theo thiết kế của GroupLens) |
| Số phim có rating | **59.047** (tổng catalog phim: 62.423) |
| Khoảng thời gian | **1995-01-09 11:46:49 → 2019-11-21 09:15:03** (24,85 năm) |
| File | `ratings.csv` 678.260.987 bytes |

### 1.2 Tầng 1 — Metrics cấp dữ liệu (không cần mô hình)

Chạy cho **3 chiến lược split**, mỗi chiến lược trả về:

| Chỉ số | Ý nghĩa | Kỳ vọng |
|---|---|---|
| `train_rows`, `test_rows` | kích thước hai tập | khác nhau đáng kể giữa 3 split |
| `train_max_ts`, `test_min_ts` | biên thời gian | random: **test_min ≪ train_max** (vi phạm); temporal: `test_min ≥ train_max`; LOO: `test_min ≥ train_max` |
| `temporal_violation` / `temporal_violation_pct` | **số tương tác test có timestamp < train_max** → định nghĩa định lượng của data leakage | random: **100%**; temporal: 0%; LOO: 0% |
| `unseen_item_rows` / `unseen_item_pct` | tương tác test mà item **chưa từng** xuất hiện ở train | random: nhỏ (~0,01%); temporal: **lớn** (phim mới) |
| `coldstart_user_rows` | tương tác test của user chưa từng có ở train | LOO: 0 (vì user luôn có ≥1 train) |
| `eval_users`, `eval_test_rows` | số user/tương tác còn lại sau bộ lọc cold-start (≥5 train interaction) | khác nhau giữa 3 split |

> **Đây là phần định lượng mạnh nhất của đề tài**: nó đo **rò rỉ dữ liệu** và **dịch chuyển miền** mà không phụ thuộc vào mô hình nào → kết quả không thể bị quy cho "do mô hình yếu".

### 1.3 Tầng 2 — Baseline Popularity

| Chỉ số | Công thức |
|---|---|
| `ndcg10` | mean over eval users của DCG@10 / IDCG@10 |
| `dcg10` | mean DCG@10 |
| `catalog_coverage` | số item được đề xuất (distinct) / số item trong catalog train |
| `longtail_coverage` | số item long-tail (pop ≤ P20) được đề xuất / tổng số item long-tail |
| `avg_pop_rec` / `avg_pop_all` | popularity trung bình của item được đề xuất / của toàn catalog |
| `popularity_bias_ratio` | `avg_pop_rec / avg_pop_all` — **> 1 nghĩa là thiên lệch về phim phổ biến** |

### 1.4 Tầng 3 — ALS (Implicit + Explicit)

| Tham số | Giá trị | Lý do |
|---|---|---|
| `rank` | 16 | đủ cho audit, rẻ |
| `maxIter` | 8 | cân bằng thời gian |
| `regParam` | 0.05 | mặc định hợp lý |
| `seed` | 42 | tái lập |
| `coldStartStrategy` | `drop` | bỏ user không có factor |
| subsample users | 30.000 (PoC) → tăng dần | tránh OOM ở `recommendForAllUsers` |

**Vì sao không dùng `recommendForAllUsers`:** 162.541 user × 59.047 item là cartesian quá lớn → OOM. Thay bằng **top-K bằng numpy** (`U @ V.T` chia chunk 2000 user/lần), trừ item user đã xem. Vẫn là đúng toán học của ALS, chỉ khác cách lấy top-K.

### 1.5 Tầng 4 — Mô hình nền khác (giai đoạn 05–06/11)

- **ItemKNN cosine** — cài đặt bằng Spark: `normalize` → `join` trên item → cosine sim → top-K neighbors → gợi ý.
- **ALS + time-aware re-rank** — thêm hệ số giảm dần theo `exp(-λ·Δt)` cho item đã xem lâu, để test xem re-rank có **cứu được** tín hiệu đo bị méo bởi split không.

---

## 2. Ba chiến lược split — định nghĩa chính xác

| Tên | Định nghĩa | Đặc trưng |
|---|---|---|
| `random80_20` | `F.rand(42) > 0.8` → test | **Ngẫu nhiên theo dòng**, không quan tâm thời gian → rò rỉ thời gian |
| `temporal_global` | test = `timestamp ≥ P80(timestamp)` | Theo **timeline toàn cục**: mô hình chỉ thấy quá khứ, giống deployment thật. Nhưng **item mới** trong tương lai không có trong train → phân phối item lệch |
| `leave_one_out` | mỗi user giữ lại 1 tương tác **mới nhất** làm test | Theo **timeline từng user**: giữ được quan hệ "không rò rỉ" + tái hiện đúng kịch bản dự đoán tương lai gần nhất. Nhưng test rất nhỏ (162K dòng) → phương sai lệch lớn hơn |

**Lý do chọn 3 chiến lược này:** tương ứng 3 bài báo neo:
- `random80_20` → S3 (TOIS 2022, data leakage) — cách mặc định của ngành.
- `temporal_global` → cách được khuyến nghị để tránh leakage.
- `leave_one_out` → cách chuẩn của sequential RS (S5, RecSys 2025).

---

## 3. Inventory script

| Script | Vai trò |
|---|---|
| `scripts/00_download_movielens.py` | tải ml-25m (đã chạy: 262 MB, 806 s) |
| `scripts/01_ingest_hdfs.py` | copy CSV → HDFS → Parquet, partition theo năm |
| `scripts/02_mapreduce_popularity.py` | **MapReduce bằng Python** (`mrjob`): item popularity theo năm, coverage |
| `scripts/03_split_strategies.py` | sinh 3 split → Parquet trên HDFS |
| `scripts/04_audit_spark.py` | chạy ma trận thực nghiệm (nội dung `_poc3_spark.py` đã chốt) |
| `scripts/05_store_mongodb.py` | ghi metrics + item profile vào MongoDB |
| `scripts/06_analysis_r.R` | SparkR: thống kê mô tả, kiểm định, biểu đồ |
| `scripts/07_dashboard.py` | Streamlit đọc MongoDB |

**PoC đã chốt (file `_poc3_spark.py`)** — sẽ chuyển thành `scripts/04_audit_spark.py` khi pipeline chính thức.

---

## 4. Quy trình tái lập (reproducibility)

1. `seed = 42` cho `F.rand`, ALS, NumPy.
2. Mỗi lần chạy ghi:
   - `<out>/logs/audit_<YYYYMMDD_HHMMSS>.log` — UTF-8, toàn bộ stdout
   - `<out>/results/audit_<timestamp>.json` — kết quả có cấu trúc
   - `<out>/results/manifest.json` — phiên bản Spark, dataset checksum, tham số, thời gian chạy
3. **Checksum dataset** lưu trong `data/raw/CHECKSUMS.sha256` (chỉ hash, không commit dữ liệu).
4. Không dùng `F.rand` không seed; không dùng `current_date` trong logic.

---

## 5. Quy trình ghi "lưu vết thực nghiệm" (yêu cầu PPNCKH)

| Yêu cầu | Cách thực hiện |
|---|---|
| Log thực nghiệm | `logs/*.log` UTF-8, không xoá sau mỗi lần chạy |
| Cấu hình thí nghiệm | `configs/` YAML cho mỗi tổ hợp (split × model × seed) |
| Kết quả định lượng | `results/*.json` + bảng trong `reports/` |
| Đạo đức dữ liệu | `02_Nguon_du_lieu_va_URL.md` §4 + trích dẫn Harper & Konstan (2015) |
| Tính tái lập | mã nguồn trong `src/`, lệnh chạy ghi trong `README.md` |
| Ảnh chụp minh hoạ | 4 ảnh Zotero theo yêu cầu `02_Tong Quan Tai Lieu.pdf` |

---

## 6. Ngưỡng dừng (stop criteria) — tránh mất thời gian

| Điều kiện | Hành động |
|---|---|
| ALS trên 20M dòng > 20 phút | giảm `maxIter` xuống 5, hoặc subsample 30K user (đã có sẵn trong PoC) |
| `recommendForAllUsers` OOM | **luôn** dùng numpy top-K (đã sửa trong PoC) |
| R cài > 30 phút lỗi | bỏ R, dùng Python, ghi rõ trong phụ lục đề cương |
| Deadline 06/11 tới mà chưa xong Tầng 2+3 | chốt dataset chính, bỏ cross-domain |
| Deadline 07/11 tới mà chưa xong Tầng 4 | bỏ ItemKNN và time-aware re-rank, giữ Popularity + ALS |
