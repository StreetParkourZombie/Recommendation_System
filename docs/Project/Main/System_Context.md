# System Context — Đánh giá tác động chiến lược chia tập dữ liệu đến tín hiệu đo và thiên lệch phổ biến trong hệ thống gợi ý

**Project:** `D:\Master Exers\Big Data\Recomendation_System`
**Phục vụ:** IT252BIDA (Xử lý dữ liệu lớn) + IT252STRM (Phương pháp nghiên cứu khoa học)
**Cập nhật:** 2026-11-09 23:48 GMT+7

> **Change note:** Từ cập nhật này, tài liệu phân biệt hai track: (A) reproduction Paper 01 và (B) controlled experiment của project. Kết quả hai track không gộp chung.

---

## 1. Ranh giới hệ thống

Hệ thống là **offline batch pipeline** đánh giá, **không phải** service gợi ý online. Đầu vào: 25.000.095 tương tác người dùng–phim (MovieLens ml-25m). Đầu ra: bộ số liệu định lượng về (a) chất lượng tín hiệu đo, (b) thiên lệch phổ biến, (c) chi phí vận hành — theo **3 chiến lược chia tập dữ liệu**.

```
MovieLens ml-25m (ratings.csv, 25.000.095 dòng)
   │
   ▼
S1  Chuẩn hoá → Parquet (pyarrow streaming, 176 MB, 31 row-groups)
   │  D:\recsys_data\parquet\ratings\part-00000.parquet
   ▼
S2  HDFS ingest → MapReduce (Java) → popularity theo năm, coverage
   │  hdfs://namenode:9000/recsys/ratings/     JOB_STATUS=SUCCESS, 323.737 key
   │  → Gate G3 cross-check PASS 100%
   ▼
S3  Spark: sinh 3 split → audit metrics cấp dữ liệu (tầng 1)
   │  random80_20 | temporal_global | leave_one_out
   │  → temporal_violation (toàn cục + user-relative), unseen_item, cold_start
   ▼
S4  Spark: Popularity baseline + ALS implicit (numpy top-K)
   │  → NDCG@10, Hit@10, catalog_coverage, longtail_coverage, Gini, bias_ratio
   ▼
S5  MongoDB: metrics theo split × model + item profile
   │  recsys.audit_metrics (6 docs / 42 field) · recsys.item_profile (62.423 docs)
   ▼
S6  PER-USER metrics → kiểm định thống kê
   │  scripts/11_peruser_ndcg.py → peruser_<split>.csv
   │  scripts/12_stats_tests.py → bootstrap CI 95%, Wilcoxon, Cohen's dz,
   │                               rank-biserial, Kendall tau-b
   ▼
S7  R 4.6.2 (đọc MongoDB, ghi recsys.audit_metrics_r) → 7 PNG + 2 CSV
   ▼
S8  PRISMA 2020 flow (9/9 paper) + benchmark Big Data (wall-clock, shuffle bytes)
   ▼
S9  Streamlit dashboard đọc MongoDB → screenshot fig9_dashboard.png
```

**Nằm ngoài phạm vi:**

- Không xây API server, không auth, không service thời gian thực.
- **Không dùng deep learning.** Lý do: (a) đóng góp của đề tài là *đóng khung vấn đề đánh giá*, không phải kiến trúc mô hình; (b) tránh trùng đồ án ConvNeXt-Tiny/otoscopy của anh.
- **Không so sánh state-of-the-art accuracy.** Mục tiêu là *audit framework*, 4 mô hình (Popularity, ItemKNN, ALS, ALS+re-rank) là đủ.

---

## 2. Ba chiến lược chia tập — trục thí nghiệm

| Tên | Định nghĩa | Kỳ vọng quan sát |
|---|---|---|
| `random80_20` | `F.rand(42) > 0.8` | Vi phạm thời gian ~100% → rò rỉ dữ liệu |
| `temporal_global` | `timestamp ≥ P80(timestamp)` | Không rò rỉ, nhưng item mới không có trong train |
| `leave_one_out` | mỗi user giữ 1 tương tác mới nhất | Không rò rỉ, test rất nhỏ → phương sai lớn |

---

## 3. Đặc tính dữ liệu (đo thật 2026-11-03, Spark 4.2.0)

| Chỉ số | Giá trị |
|---|---|
| Tương tác | 25.000.095 |
| Người dùng | 162.541 |
| Phim có rating | 59.047 (catalog 62.423) |
| Khoảng thời gian | 1995-01-09 11:46:49 → 2019-11-21 09:15:03 |
| Parquet cache | 176.0 MB, 31 row-groups, SHA-256 `379d0b2e…9657c` |

---

## 4. Thành phần hệ thống

| Mã | Thành phần | Công nghệ | Trạng thái (2026-11-04) |
|---|---|---|---|
| S1 | Ingest & chuẩn hoá | Python + pyarrow 26.0.0 | ✅ chạy được (26s cho 25M dòng) |
| S2 | HDFS + MapReduce | Hadoop 3.2.1 (container) + **Java** | ✅ **chạy thật** — `JOB_STATUS=SUCCESS`, 323.737 key, G3 pass 100% |
| S3 | Split strategies + audit | PySpark 4.2.0 | ✅ chạy thật, 3 split |
| S4 | Baseline + ALS implicit | PySpark 4.2.0 + numpy top-K | ✅ chạy thật, 3 split |
| S5 | Lưu trữ metrics | MongoDB 8.0.12 | ✅ `recsys.audit_metrics` 6 docs / 42 field; `item_profile` 62.423 docs |
| S6 | Phân tích + kiểm định | R 4.6.2 + numpy/scipy | ✅ R tạo 7 PNG + 2 CSV; kiểm định thống kê 3 split (12 dòng kết quả) |
| S7 | Dashboard | Streamlit | ✅ chạy, `HTTP 200`, đã chụp screenshot `fig9_dashboard.png` |
| S8 | Rà soát học thuật | PRISMA 2020 + 9 paper | ✅ `fig8_prisma_flow.svg` + 9/9 PDF có manifest |

> **Lưu ý:** `R` **không** dùng SparkR (chưa cài, cần Spark + R cùng môi trường). R đóng vai trò
> phân tích + trực quan, đọc JSON/CSV/MongoDB. Xử lý dữ liệu lớn do PySpark đảm nhiệm.
> Phải nói rõ giới hạn này trong báo cáo.

## 5. Ràng buộc môi trường đã phát hiện (quan trọng cho người triển khai sau)

| Vấn đề | Nguyên nhân | Xử lý đã áp dụng |
|---|---|---|
| Spark **ghi** Parquet fail: `HADOOP_HOME and hadoop.home.dir are unset` | `RawLocalFileSystem.setPermission` cần `winutils.exe` | **Ghi Parquet bằng pyarrow**, không dùng `df.write.parquet` |
| Spark **đọc thư mục** Parquet fail: `UnsatisfiedLinkError NativeIO$Windows.access0` | Hadoop cần `hadoop.dll` cho directory listing | **Đọc file đơn** `…/ratings/part-00000.parquet` → OK 25.000.095 rows |
| `recommendForAllUsers` OOM | 162.541 × 59.047 cartesian | **numpy top-K** chia chunk 2.000 user/lần |
| `percentile_approx` sai | Spark 4.x nhận quantile 0.0–1.0 | dùng `F.expr("percentile_approx(timestamp, 0.8)")` |
| `F.slice` trả array không phải số | IDCG cần 1 số | `F.aggregate(slice(...), 0D, (acc,x) -> acc+x)` |
| PyArrow `ParquetWriter` không ghi vào thư mục | chỉ ghi 1 file | ghi `part-00000.parquet` trong folder, Spark đọc file đó |
| `compression_level` không dùng với snappy | pyarrow chỉ hỗ trợ level cho codec khác | bỏ tham số |
| Spark session chết sau ~35 phút | job quá nặng cho local | `maxIter=8`, subsample 30.000 user, Parquet cache |
| Path >260 ký tự | Windows MAX_PATH | `robocopy` + `cmd /c rd /s /q "\\?\D:\..."` |
| Spark **ghi** file fail dù đã đặt `HADOOP_HOME` giả | `winutils.exe` không tồn tại trên máy này | **ghi bằng pyarrow**, tuyệt đối không `df.write.parquet` |
| Streamlit app crash `ValueError: I/O operation on closed file` | `sys.stdout = io.TextIOWrapper(sys.stdout.buffer)` — Streamlit đóng stdout cũ | dùng `sys.stdout.reconfigure(...)` |
| `chrome --screenshot` ra ảnh trống | Streamlit render qua websocket, CLI chụp quá sớm | dùng CDP (`scripts/15_screenshot_dashboard.py`) |
| Job > 30 phút bị SIGKILL | trần exec session OpenClaw | chia theo split; vector hoá bootstrap |
| Cliffs delta trên dữ liệu ghép | chỉ số cho 2 mẫu độc lập, O(n²) | dùng **rank-biserial** + **Kendall tau-b** |
| Metric hằng số cho `p = 0.0` giả | normal approx khi mọi hiệu số = 0 | chặn `n_nonzero == 0` → `p = None` |

---

## 6. Liên kết tài liệu

| Tài liệu | Nội dung |
|---|---|
| `docs/Project/Plans/00_README.md` | mục lục, quyết định chốt, cảnh báo môi trường |
| `docs/Project/Plans/01_De_tai_va_Ke_hoach.md` | đề tài, gap, RQ, W5H2, FINER, kiến trúc, timeline |
| `docs/Project/Plans/02_Nguon_du_lieu_va_URL.md` | URL, license, schema, checksum |
| `docs/Project/Plans/03_Tai_lieu_tham_khao.md` | DOI đã verify + vai trò từng bài |
| `docs/Project/Plans/04_Ma_tran_tong_quan_5_cot.md` | synthesis matrix + bảng đối chiếu tính mới |
| `docs/Project/Plans/05_Ke_hoach_thuc_nghiem.md` | ma trận thực nghiệm, tái lập, lưu vết |
| `docs/Project/Plans/06_Du_phong_va_phuong_an_B.md` | dự phòng, phương án đã loại, rủi ro |
| `docs/Project/Main/Architecture.md` | kiến trúc 4 tầng + tầng kiểm định + quy trình tái lập master |
| `docs/Project/Main/Metrics.md` | định nghĩa chỉ số + công thức + tầng kiểm định (§4.4) |
| `docs/Project/Main/Environment.md` | môi trường đã verify + cảnh báo 2026-11-04 |
| `docs/Project/Main/MetErrors/datasets.md` | error log: hiểu sai dữ liệu, rò rỉ, định nghĩa split |
| `docs/Project/Main/MetErrors/io.md` | error log: tải paper (ACM/Cloudflare), ghi file, Streamlit, CDP |
| `docs/Project/Main/MetErrors/python.md` | error log: thống kê, numpy/scipy, PySpark 4.x |
| `docs/References/Papers/_manifest.json` | manifest 9/9 paper (DOI, file, sha256, bytes) |
| `reports/stats_summary.csv` | 12 dòng kết quả kiểm định (3 split × 4 metric) |
| `docs/Project/Main/report/Big_Data/figures/` | fig1–fig7 (R) · fig8 PRISMA (SVG) · fig9 dashboard (PNG) |

## 8. Track reproduction Paper 01 — bổ sung 2026-11-09

Paper neo: **Ji et al., A Critical Study on Data Leakage in Recommender System Offline Evaluation**, ACM TOIS, DOI `10.1145/3569930`.

### Mục tiêu

Kiểm tra có thể tái lập logic và kết quả chính của bài trên đúng protocol hay không. Đây không phải bước thay thế pipeline project.

### Điều kiện được gọi là reproduction

Phải ghi và đối chiếu: dataset interval/filter; split leave-last-one-out; BPR, NeuMF, SASRec, LightGCN; metric/cutoff; preprocessing; seed; dependency; hardware; output. Paper dùng MovieLens-25M subset 9.808.925 interactions, 62.202 users, 56.774 items, time span 2009-11-21 đến 2019-11-20, không filtering. Không thay model bằng ALS/MostPopular rồi gọi reproduction.

### Artifact

Repository chính thức: `https://github.com/putatu/dataLeakageRec`. Clone/pin ở thư mục riêng ngoài source project, ví dụ `D:\recsys_papers\dataLeakageRec`. Không sửa repository gốc. Mọi patch lưu trong reproduction log.

### Output bắt buộc

- `docs/Project/Plans/Implementation/02_Reproduction_Report_Template.md` được copy thành report Paper 01.
- Commit hash, environment manifest, command, smoke-test log, dataset checksum.
- Difference ledger Paper 01 vs local run.
- Classification: `faithful_reproduction`, `partial_reproduction`, `method_informed_implementation` hoặc `blocked`.

## 9. Track B — controlled experiment của project

Project vẫn dùng MovieLens-25M project protocol, `random80_20`, `temporal_global`, `leave_one_out`, MostPopular và ALS trước. Track này trả lời RQ1–RQ4; không dùng để khẳng định đã tái lập Paper 01.

### Gates trước khi chạy full

1. Paper 01 README/dependency/dataset setup được ghi.
2. Smoke test Paper 01 chạy hoặc có log blocked.
3. Paper protocol vs project protocol được lập bảng.
4. Không trộn output/repository/environment hai track.
5. Chỉ sau đó chạy controlled comparison full matrix.

## 10. Cập nhật liên kết

- [Paper 01 exploration](../../References/Papers/Exploration/01_Data_Leakage.md)
- [Implementation map](../Plans/Implementation/04_Research_Questions_Gaps_and_Action_Map.md)
- [Reproduction template](../Plans/Implementation/02_Reproduction_Report_Template.md)

## 11. Lịch sử kết quả project

Các kết quả PoC trước cập nhật này vẫn là kết quả project-controlled, không phải reproduction Paper 01. Giữ nguyên để truy vết lịch sử.

### 7.1 Bốn phát hiện chính (đã kiểm định thống kê)

1. **Thứ hạng mô hình không đảo chiều** (ALS > Popularity ở cả 3 split, Wilcoxon p < 0,001),
   nhưng **độ lớn thay đổi 5,45 lần** và **hiệu ứng co lại** theo độ khó split
   (`dz` của NDCG@10: 0,764 → 0,521 → 0,169).
2. **Định nghĩa rò rỉ phải tương đối theo user** — toàn cục cho `leave_one_out` = 99,9988%
   (vô nghĩa) vs user-relative = 0,0000% (đúng).
3. **Đổi rò rỉ lấy dịch chuyển miền** — `temporal_global` mất **96,1%** mẫu đánh giá
   (158.688 → 6.219 user).
4. **Giảm thiên lệch ≠ xử lý thiên lệch** — `PerUserPopSkew` giảm mạnh (dz −2,28 đến −3,46,
   có ý nghĩa) nhưng `longtail_coverage = 0` ở cả 6 tổ hợp.

### 7.2 Ràng buộc thiết kế đã chốt

| Quyết định | Lý do |
|---|---|
| Mô hình: Popularity + ALS implicit (rank 16, maxIter 8, reg 0,05, alpha 10, seed 42) | ALS explicit cho NDCG ≈ 0 — sai phương pháp đánh giá top-N |
| Ngưỡng liên quan `rating ≥ 4,0` **giống nhau** cho mọi mô hình | nếu khác thì mọi so sánh vô nghĩa |
| MapReduce viết bằng **Java** | container Hadoop không có Python |
| Spark + MapReduce cùng timezone **UTC** | lệch 7,65% số key nếu không |
| Python ghi `recsys.audit_metrics`, R chỉ đọc | R từng drop/insert phá schema 42 field |
| Kiểm định dùng **chỉ số per-user** | chỉ số cấp tập không có phương sai |
| Mẫu ALS = **30.000 user** | `recommendForAllUsers` OOM (162.541 × 59.047) |

### 7.3 Kết quả kiểm định (rút gọn)

| Split | n_paired | Δ NDCG@10 (ALS − Pop) | Wilcoxon p | Cohen's dz | rank-biserial r |
|---|---:|---:|---:|---:|---:|
| `random80_20` | 29.337 | +0,1707 | < 0,001 | 0,764 | 0,784 |
| `temporal_global` | 1.363 | +0,0929 | < 0,001 | 0,521 | 0,729 |
| `leave_one_out` | 17.704 | +0,0286 | < 0,001 | 0,169 | 0,537 |

Chi tiết đầy đủ: `docs/Project/Main/Metrics.md` §4.4 và `reports/stats_summary.csv`.
