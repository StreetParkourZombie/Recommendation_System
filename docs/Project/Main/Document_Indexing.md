# Chỉ Mục Tài Liệu Hệ Thống — Recommender System Project

**Đề tài:** Phân tích rò rỉ, thiên lệch phổ biến trong hệ thống gợi ý bằng kiểm toán chiến lược chia tập trên Spark.
**Cập nhật:** 2026-11-20
**Trạng thái:** luồng notebook-first `00`–`13` đã chạy xong, gate PASS; rerun 2026-11-20 thêm Novelty/Diversity (06/08/10/11/13) + Friedman (09).

---

## 1. Thư mục `docs/Project/Main/` — tài liệu kỹ thuật nền tảng

| Tên file | Mô tả & nội dung cốt lõi |
|---|---|
| [System_Context.md](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/docs/Project/Main/System_Context.md) | Ngữ cảnh toàn hệ thống: luồng dữ liệu 25M dòng, ranh giới Track A/B, hai đường thực thi (§1), ràng buộc môi trường đã giải quyết (§5), cập nhật notebook-first + RQ1 (§12). |
| [Architecture.md](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/docs/Project/Main/Architecture.md) | Kiến trúc các tầng: Storage (HDFS/Parquet) → Compute (MapReduce/PySpark) → Persist (MongoDB) → Presentation (Streamlit/CLI). |
| [Environment.md](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/docs/Project/Main/Environment.md) | Môi trường thực tế: Python 3.14.5, Java 24.0.2, PySpark 4.2.0, `local[4]`, `HADOOP_HOME` + winutils/hadoop.dll, Jupyter kernel `recsys-project-venv`. |
| [Dataset_Selection.md](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/docs/Project/Main/Dataset_Selection.md) | Lý do chọn MovieLens-25M, bản quyền, SHA-256 tầng L1, profile phân phối tương tác L2/L3. |
| [Metrics.md](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/docs/Project/Main/Metrics.md) | Định nghĩa toán học các chỉ số: tầng dữ liệu (rò rỉ 2 định nghĩa), tầng gợi ý (NDCG/Hit/Coverage), tầng công bằng (Gini/Bias Ratio). §4.4 kiểm định thống kê, **§4.5 đối chiếu hai đường tính**, **§4.12 Novelty/Diversity/Friedman**. |
| [Drawbacks.md](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/docs/Project/Main/Drawbacks.md) | Hạn chế: Spark local không phải cluster, 1 seed, timestamp ties, `longtail_coverage = 0`, Serendipity KHÔNG đo, ALS có Diversity@10 thấp hơn MostPopular, giới hạn đánh giá offline. |
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
| [06_mostpopular_baseline.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/06_mostpopular_baseline.ipynb) | Baseline MostPopular: NDCG@10, Hit@10, MRR, coverage, Gini, `bias_ratio`, novelty/diversity (rerun 20/11) | **L6a PASS** | `20261120_004801_06_mostpopular_baseline_cde8a34b` (rerun 20/11 novelty/diversity; trước: `20261118_021147_..._6d59bb2c` lưu npz, `20261115_192522_..._c39572de`) |
| [07_ndcg_manual_check.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/07_ndcg_manual_check.ipynb) | Kiểm tra công thức NDCG/Hit bằng 5 fixture tính tay, tolerance `1e-12` | **L6b PASS** | `20261115_190933_07_ndcg_manual_check_e1cc5714` |
| [08_als_implicit.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/08_als_implicit.ipynb) | ALS implicit (rank 16, `alpha` 10), numpy top-K, assert loại item đã xem, per-user NDCG → `.npz` | **L6c PASS** | `20261120_012429_08_als_implicit_73a9947b` (rerun 20/11 novelty/diversity; trước FULL `20261117_234312_..._da15debf`, subsample cũ `20261115_192654_..._0c1385ff`) |
| [09_compare_and_reversal.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/09_compare_and_reversal.ipynb) | So sánh 5 mô hình × 3 split (Random/MostPopular/ALS/ItemKNN/SASRec), kiểm tra đảo chiều thứ hạng + đảo chiều ngôi đầu, xuất RQ1, Friedman (rerun 20/11) | **L7 PASS** | `20261120_012944_09_compare_and_reversal_21d0811a` (rerun 20/11 thêm `friedman`; trước `20261118_151159_..._1e0f72fa`) |
| [10_random_baseline.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/10_random_baseline.ipynb) | Baseline sàn Random: uniform từ catalog train, loại item đã thấy, per-user NDCG → `.npz` | **L10 PASS** | `20261120_004945_10_random_baseline_dc453187` (rerun 20/11 novelty/diversity) |
| [11_itemknn_baseline.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/11_itemknn_baseline.ipynb) | ItemKNN cosine k=100 (`src/audit/itemknn.py`, scipy sparse trên driver, min_co=2), FULL 162.541 user | **L11 PASS** | `20261120_005139_11_itemknn_baseline_979f28e2` (rerun 20/11 novelty/diversity) |
| [12_paired_stats.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/12_paired_stats.ipynb) | Kiểm định cặp per-user (Wilcoxon signed-rank + 95% CI + rank-biserial r) trên `.npz` đã lưu, 20 cặp, không chạy lại pipeline | **L12 PASS** | `20261118_151202_12_paired_stats_9b864f59` |
| [13_sasrec_ce.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/13_sasrec_ce.ipynb) | SASRec + cross-entropy softmax toàn catalog (`src/audit/sasrec.py`, PyTorch, **GPU local RTX 4050 Laptop 6 GB**, CUDA 12.6) — maxlen 50, hidden 50, 1 block, 1 head, dropout 0,2, lr 1e-3, batch 32 × accum 4 (effective 128), epochs 20 + early stop patience 3, val chia theo user 10 %, `tuning_budget = 0` — **tầng SOTA đã đăng kí**; hướng dẫn chạy `Implementation/06_Huong_Dan_Chay_SASRec_va_MRR.md` | ✅ **đã chạy 3 split** | `20261120_005943_13_sasrec_ce_f31d7945` (rerun 20/11 novelty/diversity; trước `20261118_144646_..._8225755a`) |

> **Rerun 2026-11-20:** 06/08/10/11/13 ghi `novelty10`/`diversity10`; 09 ghi `friedman`. Chi tiết: `Metrics.md` §4.12.

Chi tiết cách chạy + bảng gate đầy đủ: [`notebooks/jupyter/README.md`](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/README.md)

---

## 4. Thư mục `src/` — code dùng lại

| File | Nội dung |
|---|---|
| [`src/utils/spark_utils.py`](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/src/utils/spark_utils.py) | `PATHS` (`RAW_RATINGS_CSV`, `PARQUET_RATINGS`, `SPLITS_DIR`, `SPARK_TMP`, `HADOOP_HOME`), `ensure_hadoop_home()`, `get_spark()`, `read_ratings()`, `stop_spark()`; hằng protocol (`DEFAULT_SEED=42`, `TOP_K=10`, `RELEVANCE_THRESHOLD=4.0`, `MIN_TRAIN=5`, `SUBSAMPLE_USERS=30_000`, `RATINGS_SHA256`, `RATINGS_ROWS`). |
| [`src/audit/splits.py`](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/src/audit/splits.py) | `STRATEGIES`, `build_split`, `materialize_split`, `load_split`, `verify_materialized`, `overlap_check`. |
| [`src/audit/leakage.py`](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/src/audit/leakage.py) | `data_level_audit`, `eligible_users`, `relevance_profile`. |
| [`src/audit/metrics.py`](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/src/audit/metrics.py) | `dcg`, `idcg`, `ndcg`, `hit`, `precision`, `recall`, `mrr`, `gini`, `coverage`, `longtail_coverage`, `tail_threshold`, `novelty_at_k`, `intra_list_diversity_at_k`, `categorical_diversity_at_k`, `serendipity_at_k`; `FIXTURES` + `SUPPLEMENTARY_FIXTURES` (15/15 PASS). |
| [`src/audit/popularity.py`](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/src/audit/popularity.py) | `train_popularity`, `mostpopular_topk`, `popularity_recommendations`, `bias_metrics`, `genre_map`, `diversity_metrics`. |
| [`src/audit/als_rec.py`](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/src/audit/als_rec.py) | `fit_als_implicit`, `topk_numpy`, `collect_truth`, `collect_seen`, `subsample_users`, `check_seen_exclusion`. |
| [`src/audit/io.py`](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/src/audit/io.py) | `sha256_file`, `sha256_dir`, `save_json`, `load_json`, `readback_ok`, `dir_size_bytes`. |

---

## 5. Script

| Script | Vai trò | Còn dùng? |
|---|---|:---:|
| `scripts/generate_notebook_00.py` … `generate_notebook_13.py` | Sinh notebook từ code Python có kiểm tra cú pháp | ✅ |
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
| Thực thi | `Implementation/00_Notebook_First_Plan.md`, `01_Phase_Plan.md`, `02_Reproduction_Report_Template.md`, `03_Paper_Experiment_Matrix.md`, `04_Research_Questions_Gaps_and_Action_Map.md`, `05_Benchmark_Chi_Phi_Van_Hanh_RQ3.md`, `06_Huong_Dan_Chay_SASRec_va_MRR.md` |
| Nháp | `Others/TEMP.md` (kế hoạch cell-level cho 04–09) |

---

## 8. Thứ tự đọc đề nghị

1. `System_Context.md` — bức tranh toàn cảnh, hai đường thực thi.
2. `Dataset_Selection.md` → `Metrics.md` (§1–§3 định nghĩa, §4.5 đối chiếu số).
3. `Architecture.md` — cách từng tầng nối nhau.
4. `notebooks/jupyter/README.md` — chạy lại được từ đầu.
5. `Drawbacks.md` — đọc **trước khi** viết kết luận.
6. `MetErrors/*` — khi gặp lỗi môi trường.
