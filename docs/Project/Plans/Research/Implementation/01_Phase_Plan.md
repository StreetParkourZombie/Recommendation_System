# Kế hoạch triển khai theo phase — tài liệu nâng cao

> **Điểm bắt đầu đã đổi:** người mới học theo [`00_Notebook_First_Plan.md`](00_Notebook_First_Plan.md). File này là kế hoạch nghiên cứu/phase nâng cao, không phải hướng dẫn chạy từng cell; một số phần giả định người đọc đã biết thuật ngữ, code và protocol. Không chạy full matrix/reproduction trước khi hoàn tất checkpoint của notebook flow.

## Chế độ deadline

Khi chỉ còn vài ngày, deliverable chính là **method-informed implementation**: dùng phương pháp data-leakage của Paper 01 trên environment project hiện có. Paper 01 faithful reproduction chỉ là track phụ; không để BPR/TensorFlow 1.14 full training chặn kết quả chính.

Phạm vi tối thiểu: MovieLens-25M project dataset, `random80_20` / `temporal_global` / `leave_one_out`, `MostPopular` / `ALS`, 3 seed `[42, 2024, 7]`, HR/NDCG, leakage diagnostics, popularity metrics và runtime.

Kết quả phải ghi là `method_informed_implementation` nếu khác dataset subset, model, preprocessing, environment hoặc protocol Paper 01. Smoke test Paper 01 ghi `smoke_test_pass`; full run không khả thi ghi `blocked` hoặc `partial_reproduction`.

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

**Gate 3:** smoke test 1 split × 1 seed đạt. Sau đó chạy bảng chính 3 split × 3 seed. Chỉ mở rộng lên 10 seed nếu còn thời gian và không ảnh hưởng báo cáo chính.

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

## Thứ tự việc tiếp theo — deadline mode

1. Chốt metric contract và kiểm tra output hiện có của `MostPopular`/`ALS`.
2. Chạy hoặc tái sử dụng tầng leakage diagnostics cho 3 split.
3. Chạy bảng chính 3 split × 2 model × 3 seed.
4. Ghi CSV/JSON, runtime và hardware manifest.
5. Tạo bảng mean ± std và biểu đồ split/model.
6. Viết Paper 01 comparison table: paper protocol, project protocol, gap, classification.
7. Đưa BPR smoke-test log vào phụ lục; không chạy BPR full CPU.

Full Paper 01 training, 10 seed và model SOTA là mở rộng sau deadline, không phải điều kiện hoàn thành.
