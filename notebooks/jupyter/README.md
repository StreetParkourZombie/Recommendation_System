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
| [09_compare_and_reversal.ipynb](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/09_compare_and_reversal.ipynb) | So sánh 2 model × 3 split, kiểm tra đảo chiều, trả lời RQ1 | **L7 PASS** | `20261115_193151_09_compare_and_reversal_66fefc4f` |

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
- **GPU:** pipeline này **không dùng GPU**. PySpark chạy trên CPU đa luồng; NumPy dùng BLAS CPU. Không có bước nào hưởng lợi từ GPU ở cấu hình hiện tại.
- **Windows + Parquet:** cần `D:\recsys_data\tools\hadoop\bin\{winutils.exe, hadoop.dll}` và `HADOOP_HOME`. `spark_utils.ensure_hadoop_home()` tự cấu hình.
- **Split được ghi một lần ở notebook 04.** Notebook 05–08 đọc lại từ `D:\recsys_data\splits\`, không dựng lại từ `ratings.csv` — để tập test của mọi bước là **cùng một tập**.
