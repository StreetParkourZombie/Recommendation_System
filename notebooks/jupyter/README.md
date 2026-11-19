# Hướng dẫn chạy Notebooks Jupyter

Thư mục chứa các Jupyter Notebook cho luồng triển khai Recommender System theo triết lý **Notebook-First**: học từng bước, giải thích lý thuyết trước code, chạy thật và ghi checkpoint/log.

## Nguyên tắc vận hành

1. **Thứ tự thực hiện:** Chạy tuần tự từ 00 trở đi. Không nhảy cóc khi gate trước chưa PASS.
2. **Provenance & Audit:** Mỗi lần chạy tự động sinh thư mục `runs/<run_id>/` và log file `logs/notebooks/<run_id>.log`. Manifest lưu giữ SHA-256 dữ liệu đầu vào, thông số môi trường và trạng thái từng cell.
3. **Data Protection:** Không tải lại, không sửa đổi dữ liệu gốc trong `D:\recsys_data\raw\ml-25m`.
4. **Tự động hóa:** File nguồn notebook được sinh ra từ các script tương ứng trong thư mục `scripts/generate_notebook_*.py`. Sau khi sửa đổi generator, chạy lại script để cập nhật notebook.
5. **Logic dùng lại nằm ở `src/`:** notebook chỉ gọi hàm, in bảng và assert. Không định nghĩa lại công thức NDCG hay cách chia tập trong cell.

---

## Danh mục Notebooks & Tiến độ

| Notebook | Tên & Mục đích | Trạng thái Gate | Run ID đã kiểm chứng gần nhất |
|---|---|---|:---:|---|
| [00_environment_check.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/00_environment_check.ipynb) | Kiểm tra môi trường: Python 3.14.5, Java 24, PySpark 4.2.0, Spark `local[2]` probe | **L0 PASS** | `20261114_142212_00_environment_check_dfb5135b` |
| [01_verify_dataset.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/01_verify_dataset.ipynb) | Xác minh toàn vẹn MovieLens-25M: SHA-256, license, 25,000,095 dòng `ratings.csv` | **L1 PASS** | `20261114_152054_01_verify_dataset_111fd4ad` |
| [02_profile_ratings_with_spark.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/02_profile_ratings_with_spark.ipynb) | Profile DataFrame với Spark `local[4]`: 0 null, 162,541 users, 59,047 rated items | **L2 PASS** | `20261114_152321_02_profile_ratings_with_spark_a583229f` |
| [03_understand_interactions.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/03_understand_interactions.ipynb) | Khảo sát phân phối rating, ties timestamp (1.8M groups), duplicate pairs (0 cặp) | **L3 EXPLORATORY PASS** | `20261115_175614_03_understand_interactions_6acaa0ac` |
| [04_build_splits.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/04_build_splits.ipynb) | Sinh và ghi 3 chiến lược chia tập ra Parquet; kiểm tra số dòng + overlap | **L4 PASS** | `20261115_191009_04_build_splits_2a395f07` |
| [05_audit_split_leakage.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/05_audit_split_leakage.ipynb) | Audit rò rỉ thời gian (global + user-relative), item/user lạnh, tập eval | **L5 PASS** | `20261115_192229_05_audit_split_leakage_8e672786` |
| [06_mostpopular_baseline.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/06_mostpopular_baseline.ipynb) | Baseline MostPopular: NDCG/Hit/coverage/Gini/bias_ratio trên 3 split | **L6a PASS** | `20261115_192522_06_mostpopular_baseline_c39572de` |
| [07_ndcg_manual_check.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/07_ndcg_manual_check.ipynb) | Kiểm tra tay NDCG/DCG/Hit/Gini + fixture loại item đã thấy | **L6b PASS** | `20261115_190933_07_ndcg_manual_check_e1cc5714` |
| [08_als_implicit.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/08_als_implicit.ipynb) | ALS implicit + top-K NumPy chunk 2.000 user; lưu per-user NDCG | **L6c PASS** | `20261115_192654_08_als_implicit_0c1385ff` |
| [09_compare_and_reversal.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/09_compare_and_reversal.ipynb) | So sánh **5 model × 3 split** (Random, MostPopular, ALS, ItemKNN, SASRec), kiểm tra đảo chiều thứ hạng + đảo chiều ngôi đầu, xuất `comparison.json`, `reversal_table.csv`, `rq1_answer.md` | **L7 PASS** | `20261118_151159_09_compare_and_reversal_1e0f72fa` |
| [10_random_baseline.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/10_random_baseline.ipynb) | Baseline sàn Random: uniform từ catalog của train split, loại item đã thấy, per-user NDCG → `.npz` | **L10 PASS** | `20261118_144717_10_random_baseline_d8644ac1` |
| [11_itemknn_baseline.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/11_itemknn_baseline.ipynb) | ItemKNN cosine k=100 (`src/audit/itemknn.py`, scipy sparse trên driver, min_co=2), FULL 162.541 user, `driver_memory=10g` | **L11 PASS** | `20261118_150305_11_itemknn_baseline_0b7511ee` |
| [12_paired_stats.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/12_paired_stats.ipynb) | Kiểm định cặp per-user: **Wilcoxon signed-rank + 95% CI + rank-biserial r** cho 20 cặp model×split, chỉ đọc `.npz` đã lưu (không chạy lại pipeline) | **L12 PASS** | `20261118_151202_12_paired_stats_9b864f59` |
| [13_sasrec_ce.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/13_sasrec_ce.ipynb) | SASRec + cross-entropy softmax toàn catalog (`src/audit/sasrec.py`, PyTorch, **GPU local RTX 4050 Laptop 6 GB**, CUDA 12.6) — maxlen 50, hidden 50, 1 block, 1 head, dropout 0,2, lr 1e-3, batch 32 × accum 4 (effective 128), epochs 20 + early stop patience 3, val chia theo user 10 %, `tuning_budget = 0` — **tầng SOTA đã đăng kí**; hướng dẫn chạy `Implementation/06_Huong_Dan_Chay_SASRec_va_MRR.md` | ✅ **đã chạy 3 split** | `20261118_144646_13_sasrec_ce_8225755a` |

---

## Chạy notebook bằng dòng lệnh

```powershell
# Chạy một notebook, lưu .executed.ipynb
.\.venv\Scripts\python.exe scripts\run_notebook.py 04

# Chạy nhiều notebook tuần tự
.\.venv\Scripts\python.exe scripts\run_notebook.py 05 06 07
```

`run_notebook.py` dùng `nbclient` với kernel `recsys-project-venv`, `allow_errors=False` — cell lỗi là dừng ngay, không ghi đè artifact cũ.

## Sinh lại notebook sau khi sửa generator

```powershell
.\.venv\Scripts\python.exe scripts\generate_notebook_04.py
```

Generator kiểm tra `compile()` mọi code cell trước khi ghi file, nên lỗi cú pháp phát hiện ngay, không cần mở Jupyter.

---

## Cần lưu ý

- **File `.executed.ipynb` và `.failed.ipynb`** là artifact trung gian khi chạy test tự động, đã được cấu hình bỏ qua trong `.gitignore`, không commit lên kho lưu trữ mã nguồn.
- **Spark Local:** Phiên Spark chạy cấu hình `local[4]`, tương đương 4 luồng xử lý cục bộ, không phải cluster phân tán.
- **GPU:** 4 baseline (Random, MostPopular, ALS, ItemKNN) **chạy CPU** — PySpark `local[4]` đa luồng, NumPy dùng BLAS CPU. Riêng tầng SOTA **SASRec+CE** (notebook 13, `src/audit/sasrec.py`) được viết để chạy trên **GPU local NVIDIA GeForce RTX 4050 Laptop 6 GB** (xem `docs/About/Hardware_Resources.md`); **chưa có số** cho tới khi notebook 13 chạy xong. Hướng dẫn chạy: `docs/Project/Plans/Research/Implementation/06_Huong_Dan_Chay_SASRec_va_MRR.md`.
- **Windows + Parquet:** cần `D:\recsys_data\tools\hadoop\bin\{winutils.exe, hadoop.dll}` và `HADOOP_HOME`. `spark_utils.ensure_hadoop_home()` tự cấu hình.
- **Split được ghi một lần ở notebook 04.** Notebook 05–13 đọc lại từ `D:\recsys_data\splits\`, không dựng lại từ `ratings.csv` — để tập test của mọi bước là **cùng một tập**.
- **Thứ tự phụ thuộc:** 06/08/10/11 phải chạy trước 12 (notebook 12 chỉ đọc `peruser_ndcg_*.npz` mà 4 notebook đó lưu); 06/08/10/11 phải chạy trước 09 (09 ghép `*_summary.json`).
- **Trần thời gian:** `run_notebook.py` mặc định timeout 3600 s/notebook; notebook 11 cần `--timeout 21600` nếu chạy lại bản Spark. Bản scipy sparse hiện tại chỉ tốn 503 s.
