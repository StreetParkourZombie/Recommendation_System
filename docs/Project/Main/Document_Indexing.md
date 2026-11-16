# Chỉ Mục Tài Liệu Hệ Thống — Recommender System Project

**Đề tài:** Phân tích rò rỉ, thiên lệch phổ biến trong hệ thống gợi ý bằng kiểm toán chiến lược chia tập trên Spark.
**Cập nhật:** 2026-11-15
**Trạng thái:** luồng notebook-first `00`–`09` đã chạy xong, 6/6 gate (L4–L7) PASS.

---

## 1. Thư mục `docs/Project/Main/` — tài liệu kỹ thuật nền tảng

| Tên file | Mô tả & nội dung cốt lõi |
|---|---|
| [System_Context.md](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/docs/Project/Main/System_Context.md) | Ngữ cảnh toàn hệ thống: luồng dữ liệu 25M dòng, ranh giới Track A/B, hai đường thực thi (§1), ràng buộc môi trường đã giải quyết (§5), cập nhật notebook-first + RQ1 (§12). |
| [Architecture.md](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/docs/Project/Main/Architecture.md) | Kiến trúc các tầng: Storage (HDFS/Parquet) → Compute (MapReduce/PySpark) → Persist (MongoDB) → Presentation (Streamlit/CLI). |
| [Environment.md](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/docs/Project/Main/Environment.md) | Môi trường thực tế: Python 3.14.5, Java 24.0.2, PySpark 4.2.0, `local[4]`, `HADOOP_HOME` + winutils/hadoop.dll, Jupyter kernel `recsys-project-venv`. |
| [Dataset_Selection.md](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/docs/Project/Main/Dataset_Selection.md) | Lý do chọn MovieLens-25M, bản quyền, SHA-256 tầng L1, profile phân phối tương tác L2/L3. |
| [Metrics.md](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/docs/Project/Main/Metrics.md) | Định nghĩa toán học các chỉ số: tầng dữ liệu (rò rỉ 2 định nghĩa), tầng gợi ý (NDCG/Hit/Coverage), tầng công bằng (Gini/Bias Ratio). §4.4 kiểm định thống kê, **§4.5 đối chiếu hai đường tính**. |
| [Drawbacks.md](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/docs/Project/Main/Drawbacks.md) | Hạn chế: Spark local không phải cluster, ALS subsample 30k, 1 seed, timestamp ties, `longtail_coverage = 0`, giới hạn đánh giá offline. |
| [Document_Indexing.md](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/docs/Project/Main/Document_Indexing.md) | File chỉ mục này. |

---

## 2. Thư mục `docs/Project/Main/MetErrors/` — nhật ký lỗi thực tế

| File | Phạm vi ghi nhận |
|---|---|
| [MetErrors/datasets.md](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/docs/Project/Main/MetErrors/datasets.md) | Hiểu sai cấu trúc dữ liệu, cặp trùng (duplicate pairs), timestamp ties (1.799.454 nhóm / 78.496 user), giá phải trả của `temporal_global` (cold-start 4.235.246 dòng), định nghĩa split. |
| [MetErrors/io.md](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/docs/Project/Main/MetErrors/io.md) | `HADOOP_HOME and hadoop.home.dir are unset` → `UnsatisfiedLinkError NativeIO$Windows.access0` → chốt cần **cả** `winutils.exe` **và** `hadoop.dll`; SHA-256 CSV/Parquet; dọn `spark_tmp`; I/O Windows MAX_PATH. |
| [MetErrors/python.md](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/docs/Project/Main/MetErrors/python.md) | Jupyter `PySpark missing in this kernel` (kernel trỏ `.venv` sai), PySpark 4.2 API (`percentile_approx`, `F.slice`), `recommendForAllUsers` OOM, NPE `PartitionKeyedAccumulator.byPartition()` lành tính. |

---

## 3. Thư mục `notebooks/jupyter/` — luồng Notebook-First

| Notebook | Vai trò | Gate | Run ID |
|---|---|:---:|---|
| [00_environment_check.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/00_environment_check.ipynb) | Kernel, Python, Java, PySpark, probe Spark local | **L0 PASS** | — |
| [01_verify_dataset.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/01_verify_dataset.ipynb) | SHA-256, license, toàn vẹn 25.000.095 dòng `ratings.csv` | **L1 PASS** | — |
| [02_profile_ratings_with_spark.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/02_profile_ratings_with_spark.ipynb) | Profile DataFrame: 0 null, 162.541 user, 59.047 item có rating | **L2 PASS** | — |
| [03_understand_interactions.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/03_understand_interactions.ipynb) | Phân phối rating, duplicate pairs (0 cặp), timestamp ties (1,8M nhóm) | **L3 PASS** | — |
| [04_build_splits.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/04_build_splits.ipynb) | Sinh 3 split (`random80_20`, `temporal_global`, `leave_one_out`), ghi Parquet xuống `D:\recsys_data\splits\`, verify `matches_expected` + `overlap=0` | **L4 PASS** | `20261115_191009_04_build_splits_2a395f07` |
| [05_audit_split_leakage.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/05_audit_split_leakage.ipynb) | Audit cấp dữ liệu: `temporal_violation` (toàn cục + user), `unseen_item`, `cold_start`, `eval_*` | **L5 PASS** | `20261115_192229_05_audit_split_leakage_8e672786` |
| [06_mostpopular_baseline.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/06_mostpopular_baseline.ipynb) | Baseline MostPopular: NDCG@10, Hit@10, coverage, Gini, `bias_ratio` | **L6a PASS** | `20261115_192522_06_mostpopular_baseline_c39572de` |
| [07_ndcg_manual_check.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/07_ndcg_manual_check.ipynb) | Kiểm tra công thức NDCG/Hit bằng 5 fixture tính tay, tolerance `1e-12` | **L6b PASS** | `20261115_190933_07_ndcg_manual_check_e1cc5714` |
| [08_als_implicit.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/08_als_implicit.ipynb) | ALS implicit (rank 16, `alpha` 10), numpy top-K, assert loại item đã xem, per-user NDCG → `.npz` | **L6c PASS** | `20261115_192654_08_als_implicit_0c1385ff` |
| [09_compare_and_reversal.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/09_compare_and_reversal.ipynb) | So sánh 2 mô hình × 3 split, kiểm tra đảo chiều thứ hạng, xuất RQ1 | **L7 PASS** | `20261115_193151_09_compare_and_reversal_66fefc4f` |

Chi tiết cách chạy + bảng gate đầy đủ: [`notebooks/jupyter/README.md`](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/README.md)

---

## 4. Thư mục `src/` — code dùng lại

| File | Nội dung |
|---|---|
| [`src/utils/spark_utils.py`](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/src/utils/spark_utils.py) | `PATHS` (`RAW_RATINGS_CSV`, `PARQUET_RATINGS`, `SPLITS_DIR`, `SPARK_TMP`, `HADOOP_HOME`), `ensure_hadoop_home()`, `get_spark()`, `read_ratings()`, `stop_spark()`; hằng protocol (`DEFAULT_SEED=42`, `TOP_K=10`, `RELEVANCE_THRESHOLD=4.0`, `MIN_TRAIN=5`, `SUBSAMPLE_USERS=30_000`, `RATINGS_SHA256`, `RATINGS_ROWS`). |
| [`src/audit/splits.py`](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/src/audit/splits.py) | `STRATEGIES`, `build_split`, `materialize_split`, `load_split`, `verify_materialized`, `overlap_check`. |
| [`src/audit/leakage.py`](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/src/audit/leakage.py) | `data_level_audit`, `eligible_users`, `relevance_profile`. |
| [`src/audit/metrics.py`](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/src/audit/metrics.py) | `dcg`, `idcg`, `ndcg`, `hit`, `precision`, `recall`, `gini`, `coverage`, `longtail_coverage`, `tail_threshold`; `FIXTURES` + `assert_against_fixture`. |
| [`src/audit/popularity.py`](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/src/audit/popularity.py) | `train_popularity`, `mostpopular_topk`, `popularity_recommendations`, `bias_metrics`. |
| [`src/audit/als_rec.py`](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/src/audit/als_rec.py) | `fit_als_implicit`, `topk_numpy`, `collect_truth`, `collect_seen`, `subsample_users`, `check_seen_exclusion`. |
| [`src/audit/io.py`](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/src/audit/io.py) | `sha256_file`, `sha256_dir`, `save_json`, `load_json`, `readback_ok`, `dir_size_bytes`. |

---

## 5. Script

| Script | Vai trò | Còn dùng? |
|---|---|:---:|
| `scripts/generate_notebook_00.py` … `generate_notebook_09.py` | Sinh notebook từ code Python có kiểm tra cú pháp | ✅ |
| `scripts/run_notebook.py` | Chạy notebook bằng `nbclient`, `allow_errors=False`, ghi `.executed.ipynb` | ✅ |
| `scripts/04_audit_spark.py` | Audit + model theo split (đường A) | Giữ làm tham chiếu |
| `scripts/11_peruser_ndcg.py`, `12_stats_tests.py` | Per-user metrics + kiểm định (đường A) | Giữ làm tham chiếu |
| `scripts/05_store_mongodb.py` | Ghi `recsys.audit_metrics` | ✅ |
| `scripts/06_analysis_r.R` | R: đọc MongoDB/JSON → 7 PNG | ✅ |
| `scripts/07_dashboard.py`, `15_screenshot_dashboard.py` | Streamlit + CDP screenshot | ✅ |
| `scripts/13_prisma_flow.py`, `10_fetch_papers.py`, `16_fetch_publisher_versions.py` | PRISMA + tải paper | ✅ |
| `scripts/14_perf_benchmark.py` | Benchmark wall-clock/shuffle | ✅ |

---

## 6. Artifact sinh ra khi chạy

```
runs/<run_id>/manifest.json                    metadata + môi trường
runs/<run_id>/checkpoints/<step>.json          PASS/FAIL từng bước
runs/<run_id>/outputs/*.json | *.csv | *.npz   số liệu
runs/<run_id>/figures/*.png                    hình
logs/notebooks/<run_id>.log                    log Spark/notebook

D:\recsys_data\parquet\ratings\part-00000.parquet      176 MB, cache gốc
D:\recsys_data\splits\<strategy>\{train,test}\*.parquet  735 MB, 3 split
```

| Gate | Output chính |
|---|---|
| L4 | `outputs/split_manifest.json` |
| L5 | `outputs/data_level_audit.{json,csv}` |
| L6a | `outputs/mostpopular_{split}.json`, `mostpopular_summary.json` |
| L6b | `outputs/metric_fixtures.json` |
| L6c | `outputs/als_{split}.json`, `peruser_ndcg_{split}.npz`, `als_summary.json` |
| L7 | `outputs/comparison.json`, `reversal_table.csv`, `rq1_answer.md`, `figures/interaction_plot.png` |

---

## 7. Tài liệu kế hoạch (`docs/Project/Plans/Research/`)

| Nhóm | File |
|---|---|
| Nhập môn | `00_README.md`, `00_QUICKSTART.md` |
| Đề tài & dữ liệu | `01_De_tai_va_Ke_hoach.md`, `02_Nguon_du_lieu_va_URL.md`, `03_Tai_lieu_tham_khao.md` |
| Thiết kế nghiên cứu | `04_Ma_tran_tong_quan_5_cot.md`, `05_Ke_hoach_thuc_nghiem.md`, `05B_Ma_tran_tieu_chi_thiet_ke.md`, `05C_Baseline_3_tang_DSRM.md` |
| Gap & dự phòng | `06_Du_phong_va_phuong_an_B.md`, `07_Gap_3_phan_Known_CriticalGap_Proposed.md`, `08_Tao_tac_SLI_va_giao_thuc_audit.md` |
| Thực thi | `Implementation/00_Notebook_First_Plan.md`, `01_Phase_Plan.md`, `02_Reproduction_Report_Template.md`, `03_Paper_Experiment_Matrix.md`, `04_Research_Questions_Gaps_and_Action_Map.md` |
| Nháp | `Others/TEMP.md` (kế hoạch cell-level cho 04–09) |

---

## 8. Thứ tự đọc đề nghị

1. `System_Context.md` — bức tranh toàn cảnh, hai đường thực thi.
2. `Dataset_Selection.md` → `Metrics.md` (§1–§3 định nghĩa, §4.5 đối chiếu số).
3. `Architecture.md` — cách từng tầng nối nhau.
4. `notebooks/jupyter/README.md` — chạy lại được từ đầu.
5. `Drawbacks.md` — đọc **trước khi** viết kết luận.
6. `MetErrors/*` — khi gặp lỗi môi trường.
