# Notebook-first triển khai Recommendation System

**Mục tiêu:** học flow qua Jupyter notebook, giải thích khái niệm trước code. Mỗi notebook làm một việc, có kết quả mong đợi và checkpoint. Logic dùng lại đặt trong `src/`; notebook gọi hàm, không thành tập script dài.

**Tên đề tài đã nộp:** Phân tích rò rỉ, thiên lệch phổ biến trong hệ thống gợi ý bằng kiểm toán chiến lược chia tập trên Spark.

Dataset và data dẫn xuất đã bị xóa. Chạy lại từ dữ liệu sạch; không coi output cũ là kết quả mới. Ghi protocol version, dataset hash và log cho mọi run.

## Cách trình bày notebook

Mỗi notebook theo nhịp: (1) mục tiêu/điều kiện đầu vào, (2) khái niệm và lý do, (3) code nhỏ, (4) giải thích output, (5) assertion/checkpoint, (6) lưu artifact. Notebook chạy từ đầu trong kernel mới. Cell tốn thời gian cần opt-in rõ ràng; không bấm Run All mù quáng.

## Ghi log, runs và checkpoint

Có, plan nay quy định lưu vết theo cách tương tự Deep Learning `logs/` và `runs/`; Jupyter output tự hiển thị trong notebook không được xem là bản lưu duy nhất.

- **Mỗi lần chạy notebook** tạo `runs/<run_id>/` riêng, ví dụ `runs/20261114_113000_n02_data_profile/`; không ghi đè run cũ.
- **Mỗi notebook** có log UTF-8 tại `logs/notebooks/<notebook_id>_<run_id>.log`. Log ghi run ID, notebook, cell index/nhãn, thời điểm bắt đầu/kết thúc, trạng thái, thời lượng, tham số, số dòng/output quan trọng và traceback khi lỗi. Cell instrumentation dùng helper nhỏ trong `src/recsys/notebook_logging.py`; không monkey-patch IPython/Jupyter hooks phức tạp.
- **Checkpoint có cấu trúc**: `runs/<run_id>/manifest.json` (git commit, protocol ID, dataset SHA-256, versions, Spark config, seed, paths, start/end/status); `outputs/` cho CSV/JSON/Parquet; `figures/`; `checks/` cho assertions/counts; `logs/` hoặc link tới log notebook. Checkpoint báo DONE khi artifact đã ghi và đọc lại kiểm tra thành công.
- **Trạng thái run**: `RUNNING` lúc bắt đầu; `COMPLETED` chỉ sau khi lưu và verify artifacts; `FAILED` kèm cell/error; `INTERRUPTED` nếu kernel tắt hoặc mất kết nối. Khi notebook chạy lại, tạo run ID mới và chỉ resume từ checkpoint đã xác minh; không giả định cell trước đã hoàn tất chỉ vì output còn hiện trên giao diện.
- **Mỗi checkpoint** lưu tên bước, input artifact/hash, output artifact/hash, row counts/schema, protocol/config liên quan, thời gian, trạng thái PASS/FAIL và ghi chú. Giữ raw output/per-user records cần cho paired statistics; summary không thay thế raw data.
- **Git hygiene**: commit notebook source, helper và manifest mẫu; không commit dataset, output lớn, checkpoint model hay log/run artifacts. Thêm `data/`, `logs/`, `runs/`, `results/` sinh ra vào `.gitignore` phù hợp; sao lưu cần thiết ngoài Git.

### Cấu trúc artifacts

```text
logs/notebooks/<notebook_id>_<run_id>.log
runs/<run_id>/
  manifest.json
  checkpoints/<step_id>.json
  outputs/
  figures/
  checks/
data/raw/ml-25m/       # dataset, không commit
data/processed/        # derived data, không commit
```

Bắt đầu/kết thúc mỗi notebook bằng cell logger tạo/đóng run. Sau mỗi bước tốn thời gian, ghi checkpoint ngay, rồi đọc lại manifest/checkpoint để xác nhận. Cell log cụ thể cần triển khai ở Notebook 00; đến khi helper đó có thật, coi ghi log này là yêu cầu của plan, chưa phải tính năng đã hoạt động.


Mỗi notebook theo nhịp: (1) mục tiêu/điều kiện đầu vào, (2) khái niệm và lý do, (3) code nhỏ, (4) giải thích output, (5) assertion/checkpoint, (6) lưu artifact. Notebook chạy từ đầu trong kernel mới. Cell tốn thời gian cần opt-in rõ ràng; không bấm Run All mù quáng.

## Dataset và repo cần tải

**Project dataset:** MovieLens-25M raw từ GroupLens: `https://grouplens.org/datasets/movielens/25m/`; link archive trực tiếp: `https://files.grouplens.org/datasets/movielens/ml-25m.zip`. Tải vào `data/raw/ml-25m/` hoặc một thư mục ngoài repo đã ghi trong config. Xác minh archive, ghi ngày tải, SHA-256, schema và số dòng. Không commit dataset. Spark tự suy ra `year` từ `timestamp` khi cần.

**Paper 01 processed data:** README trong `dataLeakageRec` dẫn Google Drive `https://drive.google.com/drive/folders/1TyQysstuaUo4IYb3WaVt4dVFOyZu3oN_?usp=sharing`. Đây là artifact tác giả chuẩn bị cho code bài báo, không thay cho raw GroupLens trong thí nghiệm project. Chỉ tải ở phase reproduction; lưu riêng, kiểm tra schema/tên file/hash, không trộn giữa hai protocol.

**Không cần clone repo bài báo ngay.** Đầu tiên học pipeline project bằng Random, MostPopular, ALS và split tự triển khai có kiểm thử. Sau đó mới chọn repo paper để smoke-test/reproduction riêng: Paper 01 `https://github.com/putatu/dataLeakageRec`, Paper 02 `https://github.com/SavvinaDaniil/UnfairnessOfPopularityBias`, Paper 03 `https://github.com/monkey0head/time-to-split`. Pin commit, đọc license/README, ghi environment và sai khác. Tự code theo ý tưởng paper gọi là `method-informed implementation`; không gọi là reproduction. Nếu nghi code paper sai, trước khi sửa phải giữ nguyên bằng chứng, tạo toy counterexample tái hiện lỗi, giải thích expected vs actual, rồi mới ghi patch riêng.

## Notebook flow

| # | Notebook | Học gì / làm gì | Checkpoint |
|---|---|---|---|
| 00 | `00_environment_check.ipynb` | Kernel, Python/Java/PySpark, Spark session, `local[4]`, memory, đường dẫn và disk. Chưa cần Hadoop/HDFS/MongoDB. | Spark local start/stop được; version và config được ghi log. |
| 01 | `01_download_and_verify_dataset.ipynb` | Raw vs processed, nguồn/license, archive, checksum, giải nén an toàn. Download chỉ chạy khi bật biến xác nhận. | `ratings.csv` và metadata tồn tại; checksum, schema, bytes được lưu manifest. |
| 02 | `02_read_data_with_spark.ipynb` | DataFrame, schema, lazy transformation/action; đọc ratings bằng schema tường minh, đếm dòng/user/item, null, timestamp range. | Count/schema hợp lý; không collect toàn bộ 25M dòng vào pandas. |
| 03 | `03_understand_interactions.ipynb` | Explicit ratings; exploratory threshold counts; user/item history; duplicate user-item pairs; global/per-user timestamp ties. | L3 exploratory profile completed with logs/checkpoints. Does not select relevance, eligibility, tie or split policy. |
| 04 | `04_build_splits.ipynb` | Sinh và ghi **cả 3** chiến lược chia tập ra Parquet. Protocol đã chốt (random80_20 / temporal_global / leave_one_out); notebook này không quyết định lại chính sách, chỉ thực thi và kiểm tra số dòng + overlap. | 3 split ghi được, đọc lại khớp số đo, overlap = 0. `runs/<run_id>/outputs/split_manifest.json`. |
| 05 | `05_audit_split_leakage.ipynb` | Đo rò rỉ thời gian (global + user-relative), item/user lạnh, tập user đủ điều kiện cho từng split. Không dùng mô hình. | 3 split audit bằng cùng định nghĩa; số khớp baseline đo 2026-11-15; `data_level_audit.{json,csv}`. |
| 06 | `06_mostpopular_baseline.ipynb` | Baseline MostPopular: đếm item trên **train**, tie-break `movieId`, tính NDCG/Hit/coverage/Gini/bias_ratio. | Top-10 đơn định; NDCG khớp baseline; `mostpopular_{split}.json`. |
| 07 | `07_ndcg_manual_check.ipynb` | Kiểm tra tay NDCG/DCG/Hit/Gini trên 5 ca cố định + fixture loại item đã thấy. Không cần dữ liệu lớn. | Metric khớp tính tay với dung sai 1e-12; `metric_fixtures.json`. |
| 08 | `08_als_implicit.ipynb` | ALS implicit (rank 16, maxIter 8, alpha 10.0) fit trên train, top-K bằng NumPy chunk 2.000 user, loại item đã thấy. | Top-K không chứa item đã thấy; NDCG khớp baseline; `als_{split}.json` + `peruser_ndcg_{split}.npz`. |
| 09 | `09_compare_and_reversal.ipynb` | So sánh 2 model × 3 split; xác định model thắng và có đảo chiều không; interaction plot; viết câu trả lời RQ1. | Bảng đầy đủ; kết luận đảo chiều có/không kèm giới hạn; `comparison.json`, `reversal_table.csv`, `interaction_plot.png`, `rq1_answer.md`. |
| 10 | `10_statistics_and_uncertainty.ipynb` | Paired differences, 95% CI, p-value, effect size, test assumptions, multiple comparisons. | Pair the same users; report statistic/p/CI/effect size and limits. Do not treat 25M interactions as independent samples. |
| 11 | `11_popularity_bias_audit.ipynb` | Popularity from train; test bias as split strategy changes while model/relevance/group/candidate protocol stays fixed. | Every bias metric has definition, denominator, aggregation and popularity source. |
| 12 | `12_spark_cost_benchmark.ipynb` | Only after metric correctness: wall time, shuffle, memory/disk if available, input size, hardware. | Record cache/resource profile; never call local Spark cluster scalability. |

## Học thống kê đúng cho thiết kế này

Bài 4 gợi ý ranking metrics cho RecSys và paired t-test/Wilcoxon, CI 95%, p-value, effect size. Với hai model trên cùng user/cohort, phân tích chênh lệch per-user theo cặp. Dùng paired t-test nếu giả định hợp lý; nếu không, Wilcoxon signed-rank, ghi cách xử lý ties/zero differences. Báo mean/SD hoặc median, CI, test statistic, p-value và effect size. Điều chỉnh multiple testing hoặc đánh dấu phân tích khám phá khi so nhiều model/split/metric. Chọn bootstrap unit theo đơn vị độc lập; không giả định user hoàn toàn độc lập nếu thiết kế/nhóm dữ liệu không hỗ trợ.

Friedman/Nemenyi thường dùng so model qua nhiều benchmark datasets/conditions; không áp dụng máy móc cho từng user của một dataset như thể mỗi user là dataset độc lập. Kiểm định không thay thế effect size và ý nghĩa thực tiễn.

## Vị trí file đề nghị

```text
notebooks/jupyter/
  README.md
  00_environment_check.ipynb
  01_verify_dataset.ipynb
  02_profile_ratings_with_spark.ipynb
  03_understand_interactions.ipynb
  04_build_splits.ipynb
  05_audit_split_leakage.ipynb
  06_mostpopular_baseline.ipynb
  07_ndcg_manual_check.ipynb
  08_als_implicit.ipynb
  09_compare_and_reversal.ipynb
  10_statistics_and_uncertainty.ipynb      # chưa tạo
  11_popularity_bias_audit.ipynb           # chưa tạo
  12_spark_cost_benchmark.ipynb            # chưa tạo
src/
  recsys/notebook_logging.py               # NotebookRun: run dir, manifest, checkpoint
  utils/spark_utils.py                     # PATHS, ensure_hadoop_home, get_spark, read_ratings
  audit/
    __init__.py
    splits.py                              # STRATEGIES, build_split, materialize_split, load_split
    leakage.py                             # data_level_audit, eligible_users, relevance_profile
    popularity.py                          # train_popularity, mostpopular_topk, bias_metrics
    metrics.py                             # dcg/ndcg/hit/recall/gini + FIXTURES
    als_rec.py                             # fit_als_implicit, topk_numpy, collect_truth, collect_seen
    io.py                                  # sha256_file, sha256_dir, save_json, readback_ok
scripts/
  generate_notebook_00.py .. 09.py         # sinh notebook từ code Python
  run_notebook.py                          # chạy notebook qua nbclient, lưu .executed.ipynb
  04_audit_spark.py                        # script PoC gốc (nguồn của baseline số)
configs/experiment_protocol_v1.json
logs/
results/
data/raw/ml-25m/        # không commit
data/processed/         # sinh từ notebook, không commit
```

**Nguyên tắc tách code:** logic dài hơn ~30 dòng vào `src/`, notebook chỉ gọi hàm + in bảng + assert. Notebook 07 chứng minh `src/audit/metrics.py` đúng bằng tính tay; các notebook sau dùng lại mà không định nghĩa lại công thức.

Không tạo cả bộ notebook trước khi Notebook 00 chạy được. Bắt chước Deep Learning project ở phần giải thích trước code, chia mục tiêu nhỏ, biểu đồ/bảng và checkpoint; không sao chép cứng cấu trúc training ảnh sang recommender.

## Việc làm đầu tiên

1. Mở Jupyter từ project Recommendation System và chọn đúng kernel project.
2. Tạo/chạy riêng `00_environment_check.ipynb`; xác nhận Java, PySpark, Spark local và paths.
3. Tạo `01_download_and_verify_dataset.ipynb`; tải raw GroupLens, xác minh archive và manifest.
4. Tạo `02_read_data_with_spark.ipynb`; đọc schema, count và profile.
5. Dừng, đọc kết quả/checkpoint trước khi viết notebook split. Chưa clone paper repo, chưa chạy ALS/SASRec, chưa bật Hadoop.

## Guardrails

- Kiểm tra data folder trước download để tránh tải trùng archive lớn.
- Không hứa runtime trước khi đo trên máy hiện tại.
- `local[4]` là bốn worker thread trên một máy, không phải bốn máy. Cấu hình driver memory đặt trước Spark session; nếu session đã tồn tại, restart kernel.
- Giữ paper reproduction riêng khỏi project-controlled comparison.
- Không tuyên bố cohort/model thắng chỉ từ một seed hoặc mẫu user khác nhau.

## Definition of Done

Người mới chạy notebook từ kernel sạch, giải thích từng checkpoint, dựng được một split và MostPopular baseline có metric kiểm tra tay; mọi data/output có provenance và không nhầm reproduction với method-informed implementation. Sau đó mới mở rộng baseline ba tầng và ma trận nghiên cứu.

