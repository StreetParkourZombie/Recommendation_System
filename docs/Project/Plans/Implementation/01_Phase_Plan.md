# Kế hoạch triển khai theo phase

## Phase 0 — Dọn nhận thức

**Mục tiêu:** người thực hiện hiểu bài báo nói gì trước khi xem kết quả code.

- Đọc `Exploration/01` đến `Exploration/04` theo thứ tự.
- Tự viết 5 dòng cho mỗi bài: problem, method, evidence, limitation, liên quan project.
- Đánh dấu chỗ nào là claim của bài, chỗ nào là giả thuyết project.
- Không chạy full experiment.

**Gate 0:** trả lời được: bài 01 chống leakage bằng cách nào; bài 02 vì sao kết quả bias khác nhau; bài 03/12 split nào được so sánh; bài 04 đo convergent validity bằng gì.

## Phase 1 — Kiểm kê khả năng tái lập

Tạo một environment riêng cho từng repository. Không trộn dependency vào environment project.

| Paper | Repository | Việc phải làm | Kết quả cần ghi |
|---|---|---|---|
| 01 | `putatu/dataLeakageRec` | pin commit, đọc README, tìm MovieLens-25M setup, smoke test | commit, Python/framework, command, lỗi |
| 02 | `SavvinaDaniil/UnfairnessOfPopularityBias` | pin commit, xác định dataset/preprocessing/metric, smoke test | commit, environment, output mẫu |
| 03 | `monkey0head/time-to-split` | kiểm tra RePlay và sequential models, smoke test | dependency, dataset, split, runtime |
| 04 | Zenodo `10.5281/zenodo.21549024` | kiểm tra code và dense judgment data | có/không đủ dữ liệu để chạy |

Không sửa repository gốc. Ghi patch nội bộ nếu cần.

**Gate 1:** ít nhất một smoke test chạy được; mọi lỗi còn lại có log và nguyên nhân.

## Phase 2 — Reproduction chọn lọc

### 2.1 Bài 01

Mục tiêu: tái hiện logic global timeline và tác động leakage trên MovieLens-25M. Ghi rõ bốn model trong bài: BPR, NeuMF, SASRec, LightGCN; không thay bằng ALS rồi gọi là reproduction.

Đầu ra: split definition, train/test counts, temporal violation, metric bài dùng, model ranking, seed/hardware nếu bài công bố.

### 2.2 Bài 02

Mục tiêu: tái hiện một cấu hình popularity-bias tối thiểu. Không khẳng định reproduction nếu thiếu đúng dataset/preprocessing/grouping/evaluation strategy.

Đầu ra: popularity definition, user groups, %ΔGAP hoặc metric tương ứng, evaluation strategy, divergence sources.

### 2.3 Bài 03/12

Mục tiêu: kiểm tra split strategy ảnh hưởng ranking/metric. Chạy repository nếu dependency khả thi; nếu không, ghi “method-informed project implementation”, không ghi replication.

### 2.4 Bài 04

Không đưa dense evaluation vào claim chính nếu project không có dense judgment tương ứng. Dùng bài làm lý do kiểm tra convergent validity và sensitivity.

**Gate 2:** có reproduction report riêng, có bảng sai khác giữa paper và project.

## Phase 3 — Chuyển sang controlled comparison của project

Cố định:

- MovieLens-25M, preprocessing project.
- `random80_20`, `temporal_global`, `leave_one_out`.
- `MostPopular`, `ALS`; SOTA chỉ sau baseline.
- relevance `rating >= 4.0`, `min_train >= 5`, `K=10`.
- project seeds: 42, 2024, 7, 1337, 2025, 11, 88, 99, 314, 2718.
- hardware và Spark local mode ghi trong manifest.

Đầu ra: ranking metrics, bias metrics, leakage diagnostics, runtime. Mọi output gắn `protocol_id`, `seed`, `split`, `model`.

**Gate 3:** smoke test 1 split × 1 seed đạt; sau đó 3 split × 10 seed.

## Phase 4 — Big Data integration

- Chạy PySpark local/Colab giả lập nếu không có cluster.
- Ghi chính xác `local mode`, CPU, RAM, Spark, Java; không gọi là Hadoop cluster.
- Đưa cùng input/output qua HDFS hoặc filesystem mô phỏng theo yêu cầu môn học.
- Chạy MapReduce Java, MongoDB và Streamlit như lớp tích hợp, không để chúng thay đổi protocol đánh giá.

## Phase 5 — Phân tích và viết

- So sánh effect size và độ lệch qua seed, không chỉ so một con số.
- Kiểm tra metric consistency theo bài 11.
- Viết gap theo Known → Critical Gap → Proposed.
- Phân biệt limitation: dataset, cold-start, local execution, thiếu dense ground truth, dependency.

## Thứ tự việc tiếp theo

1. Đọc `Exploration/01.md` đến `04.md`.
2. Chạy smoke test repository bài 01.
3. Chạy smoke test repository bài 02.
4. Ghi `environment_manifest` và `reproduction_report`.
5. Chỉ khi Gate 2 đạt mới chạy `04_audit_spark.py` full matrix.
