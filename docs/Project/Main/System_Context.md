# System Context — Đánh giá tác động chiến lược chia tập dữ liệu đến tín hiệu đo và thiên lệch phổ biến trong hệ thống gợi ý

**Project:** `D:\Master Exers\Big Data\Recomendation_System`
**Phục vụ:** IT252BIDA (Xử lý dữ liệu lớn) + IT252STRM (Phương pháp nghiên cứu khoa học)
**Cập nhật:** 2026-11-20 10:00 GMT+7 (bổ sung Novelty/Diversity/Friedman; rerun 06/08/09/10/11/13 — xem §12.4)

> **Change note:** Từ cập nhật này, tài liệu phân biệt hai track: (A) reproduction Paper 01 và (B) controlled experiment của project. Kết quả hai track không gộp chung.
>
> **Deadline policy:** Track B ở dạng `method-informed implementation` là deliverable chính khi còn vài ngày. Track A chỉ cần smoke test, difference ledger và classification; full BPR/10 seed không phải gate.

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
S3  Spark: sinh 3 split → ghi xuống đĩa → audit metrics cấp dữ liệu (tầng 1)
   │  random80_20 | temporal_global | leave_one_out
│  S3b Spark: Popularity + ALS implicit + Random baseline (numpy top-K)   │  D:\recsys_data\splits\<strategy>\{train,test}\part-*.parquet  (735 MB)
   │  → temporal_violation (toàn cục + user-relative), unseen_item, cold_start
   ▼
S3b Spark: Popularity baseline + ALS implicit (numpy top-K)
   │  đọc split đã materialize (KHÔNG đọc lại ratings.csv)
   │  → NDCG@10, Hit@10, catalog_coverage, longtail_coverage, Gini, bias_ratio
   ▼
S4  MongoDB: metrics theo split × model + item profile
   │  recsys.audit_metrics (6 docs / 42 field) · recsys.item_profile (62.423 docs)
   ▼
S5  PER-USER metrics → kiểm định thống kê
   │  peruser_ndcg_<split>.npz (notebook 08) hoặc scripts/11_peruser_ndcg.py
   │  → bootstrap CI 95%, Wilcoxon, Cohen's dz, rank-biserial, Kendall tau-b
   ▼
S6  So sánh & đảo chiều thứ hạng (notebook 09)
   │  → comparison.json, reversal_table.csv, rq1_answer.md
   ▼
S7  R 4.6.2 (đọc MongoDB, ghi recsys.audit_metrics_r) → 7 PNG + 2 CSV
   ▼
S8  PRISMA 2020 flow (9/9 paper) + benchmark Big Data (wall-clock, shuffle bytes)
   ▼
S9  Streamlit dashboard đọc MongoDB → screenshot fig9_dashboard.png
```

**Hai đường thực thi song song (không trộn số):**

| Đường | Vào | Ra | Trạng thái |
|---|---|---|---|
| **Script-driven** (baseline đo 2026-11-04) | `scripts/04_audit_spark.py` → `05_store_mongodb.py` | `D:\recsys_data\poc\poc6_*.json` (CSV `reports/*.csv` đã gỡ khỏi repo) | Giữ để truy vết lịch sử |
| **Notebook-first** (từ 2026-11-15) | `notebooks/jupyter/04`–`13` → `src/audit/*` | `runs/<run_id>/outputs/*.json` | ✅ đã chạy, gate PASS; rerun 2026-11-20 xem §12.4 |

Notebook 04–09 là đường **quan sát được từng bước**; script vẫn là nguồn số cũ. Hai đường dùng **cùng protocol** (`project_protocol_v1`, seed 42, `rating ≥ 4,0`, K=10) nhưng khác đường chọn tập user đánh giá → chênh lệch nhỏ ở NDCG. Xem `Metrics.md` §4.5.

**Nằm ngoài phạm vi:**

- Không xây API server, không auth, không service thời gian thực.
- **Không dùng deep learning.** Lý do: (a) đóng góp của đề tài là *đóng khung vấn đề đánh giá*, không phải kiến trúc mô hình; (b) tránh trùng đồ án ConvNeXt-Tiny/otoscopy của anh.
- **So sánh accuracy có SOTA, nhưng không so runtime.** Mục tiêu là *audit framework*; cả 5 baseline đăng kí đã chạy: Random, MostPopular, ALS, ItemKNN cosine (CPU) + SASRec+CE (GPU local RTX 4050 6 GB). SASRec fit FULL user nhưng eval subset (`val_fraction_users=0.1`), `tuning_budget=0`, 1 seed — không gọi là model thắng. ALS+time-aware re-rank chỉ là phương án bổ sung tùy chọn, không nằm trong danh sách đăng kí.

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

| Mã | Thành phần | Công nghệ | Trạng thái (2026-11-15) |
|---|---|---|---|
| S1 | Ingest & chuẩn hoá | Python + pyarrow 26.0.0 | ✅ chạy được (26s cho 25M dòng) |
| S2 | HDFS + MapReduce | Hadoop 3.2.1 (container) + **Java** | ✅ **chạy thật** — `JOB_STATUS=SUCCESS`, 323.737 key, G3 pass 100% |
| S3 | Split strategies + audit | PySpark 4.2.0 | ✅ chạy thật, 3 split, **materialize 735 MB** xuống `D:\recsys_data\splits\` |
| S3b | Baseline + ALS implicit | PySpark 4.2.0 + numpy top-K | ✅ chạy thật, 3 split (notebook 06, 08) |
| S4 | Lưu trữ metrics | MongoDB 8.0.12 | ✅ `recsys.audit_metrics` 6 docs / 42 field; `item_profile` 62.423 docs |
| S5 | Phân tích + kiểm định | R 4.6.2 + numpy/scipy | ✅ R tạo 7 PNG + 2 CSV; per-user `.npz` + kiểm định 3 split |
| S6 | So sánh & đảo chiều | Python | ✅ notebook 09: `comparison.json`, `reversal_table.csv`, `rq1_answer.md` |
| S7 | Dashboard | Streamlit | ✅ chạy, `HTTP 200`, đã chụp screenshot `fig9_dashboard.png` |
| S8 | Rà soát học thuật | PRISMA 2020 + 9 paper | ✅ `fig8_prisma_flow.svg` + 9/9 PDF có manifest |

> **Lưu ý:** `R` **không** dùng SparkR (chưa cài, cần Spark + R cùng môi trường). R đóng vai trò
> phân tích + trực quan, đọc JSON/CSV/MongoDB. Xử lý dữ liệu lớn do PySpark đảm nhiệm.
> Phải nói rõ giới hạn này trong báo cáo.

## 5. Ràng buộc môi trường đã phát hiện (quan trọng cho người triển khai sau)

| Vấn đề | Nguyên nhân | Xử lý đã áp dụng |
|---|---|---|
| Spark **ghi** Parquet fail: `HADOOP_HOME and hadoop.home.dir are unset` | `RawLocalFileSystem.setPermission` cần `winutils.exe` | ✅ **ĐÃ GIẢI QUYẾT 2026-11-15** — đặt `HADOOP_HOME=D:\recsys_data\tools\hadoop`, có `bin\winutils.exe`; `df.write.parquet` chạy được |
| Spark **đọc thư mục** Parquet fail: `UnsatisfiedLinkError NativeIO$Windows.access0` | `winutils.exe` một mình chưa đủ — Hadoop cần thêm `hadoop.dll` cho directory listing | ✅ **ĐÃ GIẢI QUYẾT** — thêm `bin\hadoop.dll`, prepend `bin` vào `PATH`; đọc cả thư mục lẫn file đơn OK |
| `recommendForAllUsers` OOM | 162.541 × 59.047 cartesian | **numpy top-K** chia chunk 2.000 user/lần |
| `percentile_approx` sai | Spark 4.x nhận quantile 0.0–1.0 | dùng `F.expr("percentile_approx(timestamp, 0.8)")` — **giá trị xấp xỉ**, không phải phân vị chính xác |
| `F.slice` trả array không phải số | IDCG cần 1 số | `F.aggregate(slice(...), 0D, (acc,x) -> acc+x)` |
| PyArrow `ParquetWriter` không ghi vào thư mục | chỉ ghi 1 file | pyarrow giữ vai trò **ingest CSV → Parquet gốc**; Parquet của split do Spark ghi |
| `compression_level` không dùng với snappy | pyarrow chỉ hỗ trợ level cho codec khác | bỏ tham số |
| Spark session chết sau ~35 phút | job quá nặng cho local[4] | `maxIter=8`, subsample 30.000 user, Parquet cache |
| Path >260 ký tự | Windows MAX_PATH | `robocopy` + `cmd /c rd /s /q "\\?\D:\..."` |
| Streamlit app crash `ValueError: I/O operation on closed file` | `sys.stdout = io.TextIOWrapper(sys.stdout.buffer)` — Streamlit đóng stdout cũ | dùng `sys.stdout.reconfigure(...)` |
| `chrome --screenshot` ra ảnh trống | Streamlit render qua websocket, CLI chụp quá sớm | dùng CDP (`scripts/15_screenshot_dashboard.py`) |
| Job > 30 phút bị SIGKILL | trần exec session | chia theo split; vector hoá bootstrap |
| Cliffs delta trên dữ liệu ghép | chỉ số cho 2 mẫu độc lập, O(n²) | dùng **rank-biserial** + **Kendall tau-b** |
| Metric hằng số cho `p = 0.0` giả | normal approx khi mọi hiệu số = 0 | chặn `n_nonzero == 0` → `p = None` |
| Jupyter kernel `PySpark missing in this kernel` | kernel trỏ `.venv` của project khác | tạo `.venv` riêng + kernel `recsys-project-venv`, hardcode đường dẫn Python trong `kernel.json` |
| `executor-heartbeater` NPE `PartitionKeyedAccumulator.byPartition()` | lỗi nội bộ Spark 4.2.0 khi reuse session | **lành tính** — notebook vẫn `COMPLETED`, checkpoint PASS; dùng `scripts/run_notebook.py` để tách process |

---

## 6. Liên kết tài liệu

| Tài liệu | Nội dung |
|---|---|
| [`Plans/Research/00_README.md`](../Plans/Research/00_README.md) | mục lục, quyết định chốt, cảnh báo môi trường |
| [`Plans/Research/00_QUICKSTART.md`](../Plans/Research/00_QUICKSTART.md) | đường chạy nhanh nhất từ dữ liệu thô → kết quả |
| [`Plans/Research/01_De_tai_va_Ke_hoach.md`](../Plans/Research/01_De_tai_va_Ke_hoach.md) | đề tài, gap, RQ, W5H2, FINER, kiến trúc, timeline |
| [`Plans/Research/02_Nguon_du_lieu_va_URL.md`](../Plans/Research/02_Nguon_du_lieu_va_URL.md) | URL, license, schema, checksum |
| [`Plans/Research/03_Tai_lieu_tham_khao.md`](../Plans/Research/03_Tai_lieu_tham_khao.md) | DOI đã verify + vai trò từng bài |
| [`Plans/Research/04_Ma_tran_tong_quan_5_cot.md`](../Plans/Research/04_Ma_tran_tong_quan_5_cot.md) | synthesis matrix + bảng đối chiếu tính mới |
| [`Plans/Research/05_Ke_hoach_thuc_nghiem.md`](../Plans/Research/05_Ke_hoach_thuc_nghiem.md) | ma trận thực nghiệm, tái lập, lưu vết |
| [`Plans/Research/05B_Ma_tran_tieu_chi_thiet_ke.md`](../Plans/Research/05B_Ma_tran_tieu_chi_thiet_ke.md) | tiêu chí thiết kế + ánh xạ RQ → thực nghiệm |
| [`Plans/Research/05C_Baseline_3_tang_DSRM.md`](../Plans/Research/05C_Baseline_3_tang_DSRM.md) | baseline 3 tầng DSRM |
| [`Plans/Research/06_Du_phong_va_phuong_an_B.md`](../Plans/Research/06_Du_phong_va_phuong_an_B.md) | dự phòng, phương án đã loại, rủi ro |
| [`Plans/Research/07_Gap_3_phan_Known_CriticalGap_Proposed.md`](../Plans/Research/07_Gap_3_phan_Known_CriticalGap_Proposed.md) | gap 3 phần |
| [`Plans/Research/08_Tao_tac_SLI_va_giao_thuc_audit.md`](../Plans/Research/08_Tao_tac_SLI_va_giao_thuc_audit.md) | SLI + giao thức audit |
| [`Plans/Research/Implementation/00_Notebook_First_Plan.md`](../Plans/Research/Implementation/00_Notebook_First_Plan.md) | kế hoạch notebook 00–09, gate, vị trí file |
| [`Plans/Research/Others/TEMP.md`](../Plans/Research/Others/TEMP.md) | kế hoạch chi tiết 04–09 (cell-level) |
| [`Architecture.md`](Architecture.md) | kiến trúc 4 tầng + tầng kiểm định + quy trình tái lập master |
| [`Metrics.md`](Metrics.md) | định nghĩa chỉ số + công thức + tầng kiểm định (§4.4) + hai đường tính (§4.5) |
| [`Environment.md`](Environment.md) | môi trường đã verify + cảnh báo |
| [`Dataset_Selection.md`](Dataset_Selection.md) | lý do chọn MovieLens-25M, SHA-256, profile |
| [`Drawbacks.md`](Drawbacks.md) | hạn chế hạ tầng, dữ liệu, đánh giá offline |
| [`MetErrors/datasets.md`](MetErrors/datasets.md) | error log: hiểu sai dữ liệu, rò rỉ, định nghĩa split |
| [`MetErrors/io.md`](MetErrors/io.md) | error log: winutils/hadoop.dll, ghi Parquet Windows, Streamlit, CDP |
| [`MetErrors/python.md`](MetErrors/python.md) | error log: Jupyter kernel, PySpark 4.x API, Spark NPE |
| [`../../notebooks/jupyter/README.md`](../../notebooks/jupyter/README.md) | bảng 10 notebook + run ID + cách chạy |
| [`../../docs/References/Papers/_manifest.json`](../References/Papers/_manifest.json) | manifest 9/9 paper (DOI, file, sha256, bytes) |
| `runs/<run_id>/outputs/comparison.json` | so sánh **5 mô hình** × 3 split (notebook 09, run `20261118_151159_..._1e0f72fa`) |
| `runs/<run_id>/outputs/paired_stats.json` | 20 cặp kiểm định Wilcoxon + 95% CI + rank-biserial r (notebook 12, run `20261118_151202_..._9b864f59`) |
| `runs/<run_id>/outputs/reversal_table.csv` | bảng đảo chiều thứ hạng |
| `docs/Project/Main/report/Big_Data/figures/` | fig1–fig7 (R) · fig8 PRISMA (SVG) · fig9 dashboard (PNG) · fig_interaction (notebook 09) |

## 7. Track reproduction Paper 01 — bổ sung 2026-11-09

Paper neo: **Ji et al., A Critical Study on Data Leakage in Recommender System Offline Evaluation**, ACM TOIS, DOI `10.1145/3569930`.

### Mục tiêu

Kiểm tra có thể tái lập logic và kết quả chính của bài trên đúng protocol hay không. Đây không phải bước thay thế pipeline project.

### Điều kiện được gọi là reproduction

Phải ghi và đối chiếu: dataset interval/filter; split leave-last-one-out; BPR, NeuMF, SASRec, LightGCN; metric/cutoff; preprocessing; seed; dependency; hardware; output. Paper dùng MovieLens-25M subset 9.808.925 interactions, 62.202 users, 56.774 items, time span 2009-11-21 đến 2019-11-20, không filtering. Không thay model bằng ALS/MostPopular rồi gọi reproduction.

### Artifact

Repository chính thức: `https://github.com/putatu/dataLeakageRec`. Clone/pin ở thư mục riêng ngoài source project, ví dụ `D:\recsys_papers\dataLeakageRec`. Không sửa repository gốc. Mọi patch lưu trong reproduction log.

### Output bắt buộc

- [`Plans/Research/Implementation/02_Reproduction_Report_Template.md`](../Plans/Research/Implementation/02_Reproduction_Report_Template.md) được copy thành report Paper 01.
- Commit hash, environment manifest, command, smoke-test log, dataset checksum.
- Difference ledger Paper 01 vs local run.
- Classification: `faithful_reproduction`, `partial_reproduction`, `method_informed_implementation` hoặc `blocked`.

## 8. Track B — controlled experiment của project

Project vẫn dùng MovieLens-25M project protocol, `random80_20`, `temporal_global`, `leave_one_out`, MostPopular và ALS trước. Track này trả lời RQ1–RQ4; không dùng để khẳng định đã tái lập Paper 01.

### Gates trước khi chạy full

1. Paper 01 README/dependency/dataset setup được ghi.
2. Smoke test Paper 01 chạy hoặc có log blocked.
3. Paper protocol vs project protocol được lập bảng.
4. Không trộn output/repository/environment hai track.
5. Với deadline mode, chạy project matrix trước: 3 split × 5 model × 1 seed (42) — **đã hoàn thành**; ma trận seed là mở rộng, không phải gate.
6. Chỉ mở rộng nhiều seed hoặc Paper 01 full model nếu còn thời gian và tài nguyên (hiện **không** nằm trong phạm vi đã đăng kí).

Project result khác dataset/model/protocol Paper 01 phải ghi `method_informed_implementation`, không ghi faithful reproduction.


## 10. Cập nhật liên kết

- [Paper 01 exploration](../../References/Papers/Exploration/01_Data_Leakage.md)
- [Implementation map](../Plans/Research/Implementation/04_Research_Questions_Gaps_and_Action_Map.md)
- [Reproduction template](../Plans/Research/Implementation/02_Reproduction_Report_Template.md)

## 11. Lịch sử kết quả project

Các kết quả PoC trước cập nhật này vẫn là kết quả project-controlled, không phải reproduction Paper 01. Giữ nguyên để truy vết lịch sử.

### 11.1 Bốn phát hiện chính (đã kiểm định thống kê)

1. **Thứ hạng mô hình không đảo chiều** (ALS > Popularity ở cả 3 split, Wilcoxon p < 0,001),
   nhưng **độ lớn thay đổi 5,45 lần** và **hiệu ứng co lại** theo độ khó split
   (`dz` của NDCG@10: 0,764 → 0,521 → 0,169).
2. **Định nghĩa rò rỉ phải tương đối theo user** — toàn cục cho `leave_one_out` = 99,9988%
   (vô nghĩa) vs user-relative = 0,0000% (đúng).
3. **Đổi rò rỉ lấy dịch chuyển miền** — `temporal_global` mất **96,1%** mẫu đánh giá
   (158.688 → 6.219 user).
4. **Giảm thiên lệch ≠ xử lý thiên lệch** — `PerUserPopSkew` giảm mạnh (dz −2,28 đến −3,46,
   có ý nghĩa) nhưng `longtail_coverage = 0` ở cả 6 tổ hợp.

### 11.2 Ràng buộc thiết kế đã chốt

| Quyết định | Lý do |
|---|---|
| Mô hình: Popularity + ALS implicit (rank 16, maxIter 8, reg 0,05, alpha 10, seed 42) | ALS explicit cho NDCG ≈ 0 — sai phương pháp đánh giá top-N |
| Ngưỡng liên quan `rating ≥ 4,0` **giống nhau** cho mọi mô hình | nếu khác thì mọi so sánh vô nghĩa |
| MapReduce viết bằng **Java** | container Hadoop không có Python |
| Spark + MapReduce cùng timezone **UTC** | lệch 7,65% số key nếu không |
| Python ghi `recsys.audit_metrics`, R chỉ đọc | R từng drop/insert phá schema 42 field |
| Kiểm định dùng **chỉ số per-user** | chỉ số cấp tập không có phương sai |
| Mẫu ALS = **FULL 162.541 user** (2026-11-17; subsample 30.000 là lịch sử run 15/11) | `topk_numpy` chunked tránh OOM của `recommendForAllUsers` (162.541 × 59.047) |

### 11.3 Kết quả kiểm định — đường script, đo 2026-11-04 (rút gọn)

| Split | n_paired | Δ NDCG@10 (ALS − Pop) | Wilcoxon p | Cohen's dz | rank-biserial r |
|---|---:|---:|---:|---:|---:|
| `random80_20` | 29.337 | +0,1707 | < 0,001 | 0,764 | 0,784 |
| `temporal_global` | 1.363 | +0,0929 | < 0,001 | 0,521 | 0,729 |
| `leave_one_out` | 17.704 | +0,0286 | < 0,001 | 0,169 | 0,537 |

Chi tiết đầy đủ: [`Metrics.md`](Metrics.md) §4.4 (đường A, lịch sử).

> **Bản chính thức hiện nay là §12.2b + [`Metrics.md`](Metrics.md) §4.10–4.11**: 20 cặp kiểm định trên 5 model, run `20261118_151202_12_paired_stats_9b864f59`. Bảng dưới đây (đường A, 2 model, subsample 30k, `reports/stats_*.json` đã bị gỡ khỏi repo) **không dùng để trích cho slide/đề cương**.

---

## 12. Cập nhật 2026-11-15 — luồng notebook-first đã chạy xong

9 notebook (`04`–`09`, `10`–`12`) thay đường quan sát thủ công bằng luồng **cell-by-cell có checkpoint**. Code dùng lại nằm ở `src/audit/*`, notebook chỉ gọi và in bảng.

### 12.1 Gate đã PASS

| Gate | Notebook | Run ID | Kết quả |
|---|---|---|---|
| L4 | `04_build_splits` | `20261115_191009_04_build_splits_2a395f07` | 3 split ghi đĩa, `matches_expected=True`, `overlap=0` |
| L5 | `05_audit_split_leakage` | `20261115_192229_05_audit_split_leakage_8e672786` | audit cấp dữ liệu 3 split |
| L6a | `06_mostpopular_baseline` | `20261115_192522_06_mostpopular_baseline_c39572de` | MostPopular NDCG 3 split |
| L6b | `07_ndcg_manual_check` | `20261115_190933_07_ndcg_manual_check_e1cc5714` | 5 fixture NDCG, tolerance `1e-12` |
| L6c | `08_als_implicit` | `20261115_192654_08_als_implicit_0c1385ff` | ALS implicit 3 split + `seen_exclusion PASS` |
| L6c-FULL | `08_als_implicit` | `20261117_185700_08_als_implicit_7be22080` | ALS fit FULL 162.541 user |
| L10 | `10_random_baseline` | `20261118_144717_10_random_baseline_d8644ac1` | Random sàn 3 split + MRR, bias ≈ 1 |
| L6a-RERUN | `06_mostpopular_baseline` | `20261118_144642_06_mostpopular_baseline_eaa120f4` | MostPopular chạy lại + MRR, gate reproduction PASS (0,0852/0,0455/0,0183) + **lưu `peruser_ndcg_{split}.npz`** 3 split |
| L7 | `09_compare_and_reversal` | `20261118_151159_09_compare_and_reversal_1e0f72fa` | so sánh **5 model** + RQ1 (reversals 0 ở cặp vs sàn; **2/3 ở cặp ngôi đầu**) |
| L11 | `11_itemknn_baseline` | `20261118_150305_11_itemknn_baseline_0b7511ee` | ItemKNN cosine scipy sparse 3 split + MRR, seen PASS, NDCG > Random |
| L12 | `12_paired_stats` | `20261118_151202_12_paired_stats_9b864f59` | Wilcoxon + 95% CI + rank-biserial r, **20 cặp / 5 model**, all `n>=30`, min 6.214 |

### 12.2 RQ1 — đảo chiều ngôi đầu GIỮA HAI MODEL KINH ĐIỂN

| Split | Random (sàn) | MostPopular | ItemKNN | ALS | ALS/sàn | Model đầu |
|---|---:|---:|---:|---:|---:|---|
| `random80_20` | 0,0003 | 0,0852 | **0,2679** | 0,2581 | 860,3× | ItemKNN |
| `temporal_global` | 0,0009 | 0,0455 | **0,1409** | 0,1332 | 148,0× | ItemKNN |
| `leave_one_out` | 0,0001 | 0,0183 | 0,0461 | **0,0469** | 469,0× | ALS |

**Hai kết luận khác nhau tuỳ cặp so sánh** (run ghép `20261118_151159_09_compare_and_reversal_1e0f72fa`, `reversals_found = 0`, `best_model_reversals_found = 2`):

1. Cặp **model vs sàn** (ALS/ItemKNN so MostPopular): ΔNDCG luôn dương ở 3/3 split → **không đảo chiều**.
2. Cặp **hai model ngang tầm** (ALS vs ItemKNN): ngôi đầu **đổi chỗ ở 2/3 cặp split** → **CÓ đảo chiều thứ hạng**.

Đây là phát hiện phương pháp quan trọng nhất của RQ1: nếu thực nghiệm chỉ so model với đường cơ sở tầm thường thì **kết luận "chia tập không làm đổi thứ hạng" là sai lệch** — độ phân giải của so sánh quyết định phát hiện.

Số FULL run cuối: ALS `20261118_144944_08_als_implicit_aaf45746`, ItemKNN `20261118_150305_11_itemknn_baseline_0b7511ee`, Random `20261118_144717_10_random_baseline_d8644ac1`, MostPopular `20261118_144642_06_mostpopular_baseline_eaa120f4`, SASRec `20261118_144646_13_sasrec_ce_8225755a`.

### 12.2b RQ1 — kiểm định cặp (notebook 12, run cuối `20261118_151202_12_paired_stats_9b864f59`, 20 cặp / 5 model)

Chênh NDCG trung bình chưa đủ bằng chứng. Notebook 12 đọc trực tiếp `peruser_ndcg_*.npz` đã lưu (**không chạy lại pipeline**), khớp user per-user, kiểm định **Wilcoxon signed-rank** + 95% CI của hiệu số + effect size **rank-biserial r** (quy định Bài giảng 04 Phần 4; NDCG per-user lệch phải nặng nên không dùng t-test).

| Cặp (split) | n | mean d | p | 95% CI | r | Mức |
|---|---:|---:|---:|---|---:|---|
| `random80_20` ALS vs MostPopular | 158.626 | +0,1729 | <1e-300 | [+0,1718, +0,1740] | 0,696 | trung bình |
| `random80_20` ALS vs Random | 158.626 | +0,2578 | <1e-300 | [+0,2567, +0,2589] | 0,999 | lớn |
| `random80_20` ItemKNN vs MostPopular | 158.692 | +0,1827 | <1e-300 | [+0,1816, +0,1838] | 0,736 | lớn |
| `random80_20` ALS vs ItemKNN | 158.626 | −0,0099 | 2,8e-60 | [−0,0109, −0,0089] | −0,030 | gần không |
| `temporal_global` ALS vs MostPopular | 6.214 | +0,0878 | 1,1e-297 | [+0,0833, +0,0924] | 0,647 | trung bình |
| `temporal_global` ALS vs Random | 6.214 | +0,1323 | <1e-300 | [+0,1274, +0,1371] | 0,986 | lớn |
| `temporal_global` ItemKNN vs MostPopular | 6.219 | +0,0954 | <1e-300 | [+0,0909, +0,0999] | 0,702 | lớn |
| `temporal_global` ALS vs ItemKNN | 6.214 | −0,0077 | 3,0e-03 | [−0,0118, −0,0036] | −0,016 | gần không |
| `leave_one_out` ALS vs MostPopular | 95.977 | +0,0286 | <1e-300 | [+0,0276, +0,0297] | 0,531 | trung bình |
| `leave_one_out` ALS vs Random | 95.977 | +0,0468 | <1e-300 | [+0,0458, +0,0479] | 0,996 | lớn |
| `leave_one_out` ItemKNN vs MostPopular | 96.003 | +0,0278 | <1e-300 | [+0,0268, +0,0289] | 0,517 | trung bình |
| `leave_one_out` ALS vs ItemKNN | 95.977 | +0,0008 | 0,153 | [−0,0003, +0,0018] | 0,005 | gần không |

Đọc số: **11/20 cặp** có p < 0,05 và CI **không chứa 0**. Cặp duy nhất không có ý nghĩa: ALS vs ItemKNN ở `leave_one_out` (p = 0,153, CI chứa 0) → ở split sạch nhất, **không đủ bằng chứng** nói hai model khác nhau. Chênh lệch ALS–MostPopular cũng co dần theo độ khó split (0,1729 → 0,0878 → 0,0286): bằng chứng thống kê cho "độ lớn hiệu ứng phụ thuộc chiến lược chia" (RQ1), không chỉ là thứ hạng trung bình.

Điểm phải nói kèm: cặp ALS vs ItemKNN có p nhỏ nhưng **|r| chỉ 0,005–0,030** — khác biệt ~0,008 điểm NDCG, tức **về thực hành hai model ngang nhau**. Đảo chiều THỨ TỰ có thật; đảo chiều ĐỘ LỚN không đáng kể.

Nguồn run per-user cuối: MostPopular `20261118_144642_...eaa120f4`, ALS `20261118_144944_...aaf45746`, Random `20261118_144717_...d8644ac1`, ItemKNN `20261118_150305_...0b7511ee`, SASRec `20261118_144646_...8225755a`. Artifact: `paired_stats.json` (20 cặp).

> **Giới hạn bắt buộc khai báo:** 1 seed (42); cả 5 baseline đăng kí đã chạy (Random, MostPopular, ALS, ItemKNN CPU + SASRec+CE GPU) — EASE không đăng kí nên không chạy. SASRec fit FULL 162.541 user nhưng eval subset (`val_fraction_users=0.1`), pairing dùng giao user, `tuning_budget=0`; **KHÔNG so runtime GPU-vs-CPU**. ALS/ItemKNN fit FULL user; ItemKNN chạy trên driver (scipy sparse) nên chi phí không so được với ALS trong môi trường phân tán thật; mỗi split có population riêng nên NDCG **không so cặp** giữa split; kiểm định cặp chỉ so **trong cùng split**; memory chưa instrument.

### 12.3 Vị trí artifact

```
src/utils/spark_utils.py        PATHS, get_spark(), read_ratings(), hằng protocol
src/audit/splits.py             STRATEGIES, build_split, materialize_split, verify_materialized
src/audit/leakage.py            data_level_audit, eligible_users, relevance_profile
src/audit/popularity.py         train_popularity, mostpopular_topk, bias_metrics, genre_map, diversity_metrics
src/audit/metrics.py            dcg/idcg/ndcg/hit/precision/recall/mrr/gini/coverage + novelty_at_k/intra_list_diversity_at_k/categorical_diversity_at_k/serendipity_at_k + 15 FIXTURES
src/audit/als_rec.py            fit_als_implicit, topk_numpy, collect_truth, subsample_users
src/audit/itemknn.py            fit() + score_users() — ItemKNN cosine bằng scipy sparse (min_co=2)
src/audit/io.py                 sha256, save_json, readback_ok

runs/<run_id>/manifest.json + checkpoints/<step>.json + outputs/ + figures/
logs/notebooks/<run_id>.log
D:\recsys_data\splits\<strategy>\{train,test}\part-*.parquet   (735.030.695 B, 3 split)
```

Tái lập toàn bộ dãy notebook:

```powershell
cd "D:\Master Exers\Big Data\Recomendation_System"
python scripts\run_notebook.py notebooks\jupyter\04_build_splits.ipynb
python scripts\run_notebook.py notebooks\jupyter\05_audit_split_leakage.ipynb
python scripts\run_notebook.py notebooks\jupyter\06_mostpopular_baseline.ipynb
python scripts\run_notebook.py notebooks\jupyter\07_ndcg_manual_check.ipynb
python scripts\run_notebook.py notebooks\jupyter\08_als_implicit.ipynb
python scripts\run_notebook.py notebooks\jupyter\09_compare_and_reversal.ipynb
```

`run_notebook.py` tách mỗi notebook thành process riêng — tránh NPE `PartitionKeyedAccumulator.byPartition()` của Spark 4.2.0 khi reuse session (xem `MetErrors/python.md` §3).

### 12.4 Bổ sung Bài 04 (2026-11-20) — Novelty/Diversity/Friedman

Rerun 06/08/10/11/13 để ghi `novelty10`/`diversity10` vào `*_summary.json`; rerun 09 để ghi key `friedman` vào `comparison.json`. Số, công thức, run id: [`Metrics.md`](Metrics.md) §4.12. Ba phát hiện phải nói kèm:

1. Random có Novelty@10 cao nhất (20,2–21,1) nhưng NDCG ≈ 0 — novelty phải đọc cùng NDCG.
2. ALS có Diversity@10 thấp nhất (0,735–0,747), thấp hơn cả MostPopular (0,765–0,788) ở cả 3 split — cá nhân hoá không tự động tăng đa dạng genre.
3. Friedman bác bỏ "mọi model ngang nhau" ở 3 split (p ≈ 0) nhưng không chỉ ra cặp nào; Nemenyi KHÔNG chạy. Serendipity KHÔNG đo; memory KHÔNG đo.

