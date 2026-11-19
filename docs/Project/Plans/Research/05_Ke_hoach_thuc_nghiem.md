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
| subsample users | FULL 162.541 (2026-11-17); subsample 30.000 là PoC lịch sử | topk_numpy chunked tránh OOM ở `recommendForAllUsers` |

**Vì sao không dùng `recommendForAllUsers`:** 162.541 user × 59.047 item là cartesian quá lớn → OOM. Thay bằng **top-K bằng numpy** (`U @ V.T` chia chunk 2000 user/lần), trừ item user đã xem. Vẫn là đúng toán học của ALS, chỉ khác cách lấy top-K.

### 1.5 Tầng 4 — Ba tầng baseline bắt buộc của Bài 03

> Chi tiết đầy đủ: `05C_Baseline_3_tang_DSRM.md`. Đây là **điều kiện bắt buộc** của thầy:
> phải có 1 baseline truyền thống + 1 kinh điển + 1 SOTA, **cả ba đều tái lập được**.

| Tầng | Mô hình | Code | Seed | Phần cứng | Trạng thái |
|---|---|---|---|---|---|
| **Sàn (truyền thống)** | `Random`, `MostPopular` | PySpark built-in + MapReduce Java (đã chạy 04/11, 323.737 key) | 42 | máy anh | ✅ có sẵn |
| **Kinh điển** | `ALS` (MF), `ItemKNN` cosine | `pyspark.ml.recommendation.ALS`; ItemKNN: `src/audit/itemknn.py` (scipy sparse, cosine trên co-count) | 42 (1 seed — giới hạn đã khai báo) | máy anh | ✅ ALS xong (FULL) · ✅ ItemKNN xong (run `20261118_150305_..._0b7511ee`, 503 s) |
| **SOTA (≤2 năm)** | `SASRec` + cross-entropy (đúng danh sách đăng kí) | `github.com/pmixer/SASRec.pytorch` · `github.com/antklen/sasrec-bert4rec-recsys23` | 42 | GPU local RTX 4050 Laptop 6 GB | ✅ đã chạy 3 split trên GPU local RTX 4050, seed 42, `tuning_budget=0`; không gọi là model thắng |
| **Bổ sung (tùy chọn)** | `ALS + time-aware re-rank` | tự viết: `exp(-λ·Δt)` cho item xem lâu | 42 | máy anh | ⏳ nếu còn thời gian |

**Ngân sách tinh chỉnh phải bằng nhau cho mọi mô hình, gồm baseline.** Bắt chước đúng [03] RecSys'25:
hidden 32–256 · self-attention blocks 1–3 · heads 1–4 · dropout 0.1–0.5 · batch 256 · seq_len 128 ·
Adam lr 1e-3 · max 300 epoch · early stop patience 10 (BERT4Rec 20).

**Không có phương án EASE:** EASE **không nằm trong danh sách baseline đã đăng kí** (`docs/About/Reseach_Method_Submission.md`) nên đề tài **không chạy**. SASRec+CE đã chạy được trên GPU local RTX 4050, nên giữ cả 5 model đã đăng kí và **khai báo giới hạn** "tầng SOTA đã reproduce 3 split trên GPU local (không tuning) trong giai đoạn này" (xem `docs/Project/Main/Drawbacks.md` §3.5).


**Không dùng [13] và [14] làm mốc so sánh số** — dataset private, không repo, không seed
(chi tiết `05C_Baseline_3_tang_DSRM.md` §3).

### 1.6 Khai báo bắt buộc trong Chương 3

| Trường | Nội dung |
|---|---|
| Mã nguồn | commit hash repo mình + 3 link repo baseline |
| Seed | **1 seed duy nhất: 42** (giới hạn đã khai báo trong đề cương + slide 14). Ma trận nhiều seed **không chạy** — xem `docs/Project/Main/Drawbacks.md` §1.4. Báo per-split, không báo Mean ± Std bừa. |
| CPU / GPU / RAM | `lscpu`, `nproc`, `free -h`, `spark.version`, `java -version` → `logs/hardware.txt` |
| Thời gian chạy | wall-clock mỗi mô hình × mỗi split (`time.perf_counter()`) |
| Ngân sách tinh chỉnh | số cấu hình thử cho **mỗi** mô hình, kể cả baseline (vd 30) |

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
| `src/audit/itemknn.py` | **ItemKNN cosine** bằng `scipy.sparse` (co-count → cosine, k=100, min_co=2) — tầng kinh điển, ✅ đã chạy trong notebook 11. Bản RDD `cartesian`/self-join không dùng được (timeout 3600 s) |
| `scripts/18_hardware_log.py` | **Ghi cấu hình phần cứng** (`nproc`, `free -h`, `lscpu`, `java -version`, `spark.version`) → `logs/hardware.txt` — tiêu chí (6) của Bài 03 |
| `scripts/19_baseline_3tang.py` | (dự kiến, không dùng) — đường thực tế là `notebooks/jupyter/06,08,10,11` cho 4 baseline × 3 split × seed 42, ghép ở `09`, kiểm định ở `12` |

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
5. **Seed: 42 cho mọi mô hình** (1 seed — giới hạn đã khai báo, không phải 10 seed). Vì không có Mean ± Std, mọi kết luận chênh lệch phải kèm **kiểm định cặp per-user** (Wilcoxon + 95% CI + effect size r) — notebook 12, 20 cặp.
6. **Khai báo phần cứng** mỗi lần chạy: `scripts/18_hardware_log.py` → `logs/hardware.txt` (tiêu chí 6 của Bài 03).
7. **Ngân sách tinh chỉnh bằng nhau** giữa mô hình đề xuất và baseline — ghi rõ số cấu hình thử.
8. **Ba tầng baseline** (sàn / kinh điển / SOTA) — xem §1.5 và `05C_Baseline_3_tang_DSRM.md`.
9. **Dùng đúng file split công bố** của [12] (`github.com/mengzaiqiao/data_splits`) để so sánh cùng dữ liệu.

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

## 6. Chính sách phạm vi khi tài nguyên/thời gian giới hạn

Khi không đủ thời gian hoặc phần cứng cho full Paper 01, deliverable chính là **method-informed implementation** trên environment project hiện có. Không gọi kết quả này là faithful reproduction.

### Phạm vi chốt tối thiểu

- Dataset: MovieLens-25M project dataset, ghi rõ khác subset Paper 01.
- Split: `random80_20`, `temporal_global`, `leave_one_out`.
- Model: 4 baseline đã đăng kí và **đã chạy đủ** — `Random`, `MostPopular` (sàn), `ALS`, `ItemKNN` cosine (kinh điển); `SASRec`+CE (SOTA) đã chạy trên GPU local RTX 4050.
- Metrics: HR/NDCG theo metric contract project, leakage diagnostics, catalog/popularity metrics và wall-clock runtime.
- Seeds: **1 seed 42** cho toàn bộ bảng chính (giới hạn đã khai báo). Ma trận seed là mở rộng, không phải gate, và **không nằm trong phạm vi đã đăng kí**.
- Hardware/software: dùng environment project hiện có và ghi manifest thực tế.

### Phân loại kết quả

| Kết quả | Cách ghi |
|---|---|
| Paper 01 smoke test | `smoke_test_pass`; chứng minh code/environment chạy |
| Paper 01 full protocol không chạy vì runtime | `blocked` hoặc `partial_reproduction`, kèm log và lý do |
| Project chạy khác dataset/model/protocol paper | `method_informed_implementation` |
| Project chạy đúng các điều kiện công bố đủ artifact | `faithful_reproduction` |

Không chạy BPR 300 epoch trên CPU trong critical path. Smoke test BPR đã mất 489,40 giây cho 1 epoch và 10 user; dùng làm bằng chứng giới hạn runtime, không dùng làm accuracy chính.

---

## 7. Ngưỡng dừng (stop criteria) — tránh mất thời gian

| Điều kiện | Hành động |
|---|---|
| ALS trên 20M dòng > 20 phút | fit FULL mất ~37s/split thực tế (run 17/11) + `topk_numpy` chunked |
| `recommendForAllUsers` OOM | **luôn** dùng numpy top-K (đã sửa trong PoC) |
| R cài > 30 phút lỗi | bỏ R, dùng Python, ghi rõ trong phụ lục đề cương |
| Deadline 06/11 tới mà chưa xong Tầng 2+3 | chốt dataset chính, bỏ cross-domain |
| Deadline 07/11 tới mà chưa xong Tầng SOTA | **vẫn phải giữ đủ 3 tầng baseline** — tất cả 5 model đã đăng kí đã chạy đủ 3 split; tầng SOTA khai báo "đã reproduce 3 split trên GPU local RTX 4050 (không tuning)" |
| Không chạy được SASRec+CE (thiếu GPU/thời gian) | **không thay bằng EASE** (không đăng kí) — giữ 5 model, khai báo giới hạn tầng SOTA trong đề cương và slide 13/14 |
| ItemKNN quá chậm trên ml-25m | ✅ đã xử lý: v1 Spark self-join timeout 3600 s → v2 `scipy.sparse` trên driver, 503 s cho 3 split (run `20261118_150305_..._0b7511ee`) |
