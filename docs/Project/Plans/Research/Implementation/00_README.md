# Implementation Reading-First

For a beginner-friendly notebook workflow, start with [`00_Notebook_First_Plan.md`](00_Notebook_First_Plan.md). It replaces the reading-first phase plan as the entry point for learning and running the project from a clean dataset.

Project không chạy theo thứ tự "viết code trước, đọc bài sau". Có hai chế độ:

- **Normal:** reproduction chọn lọc trước, controlled comparison sau.
- **Deadline:** controlled comparison method-informed là deliverable chính; Paper 01 chỉ cần smoke test và difference ledger.

Thứ tự bắt buộc:

1. Đọc bài neo, ghi claim và thiết kế thí nghiệm.
2. Xác minh dataset, split, model, metric, seed, hardware, repository.
3. Tách kết quả reproduction khỏi controlled comparison của project.
4. Chạy pipeline project với phạm vi đủ nhỏ để có kết quả trong deadline.
5. Chỉ mở rộng Paper 01 full run nếu runtime cho phép.

## Project đang nghiên cứu gì?

Đây là nghiên cứu đánh giá offline recommender systems. Leakage, split sensitivity và popularity bias là các trục kiểm tra độ tin cậy của evaluation, không phải chủ đề thay thế recommender systems.

## 14 bài dùng thế nào?

- Bài 01: anchor về data leakage và global timeline; ưu tiên reproduction.
- Bài 02: anchor về popularity bias và evaluation strategy; ưu tiên reproduction chọn lọc.
- Bài 03: anchor về các chiến lược split sequential; ưu tiên đọc và chạy repository nếu dependency phù hợp.
- Bài 04: nền tảng convergent validity; đọc phương pháp, chưa dùng làm reproduction chính nếu dense judgments không có.
- Bài 05-10: nền tảng bias, survey, evaluation standpoint, cold-start và debias; chủ yếu đọc để định nghĩa và gap.
- Bài 11: kiểm tra metric consistency; dùng làm rule kiểm tra implementation.
- Bài 12: tiền thân của bài 03; đọc để hiểu lịch sử split strategy.
- Bài 13: chứng minh pipeline Spark/Hadoop cho RS; tham khảo kiến trúc Big Data.
- Bài 14: framework evaluation trong Big Data; đọc phương pháp runtime/Spark, không giả định giống bài toán MovieLens của project.

## Có cần tải code không?

Có, nhưng không tải tất cả.

- Bắt buộc thử code bài 01: `https://github.com/putatu/dataLeakageRec`
- Bắt buộc thử code bài 02: `https://github.com/SavvinaDaniil/UnfairnessOfPopularityBias`
- Ưu tiên thử code bài 03: `https://github.com/monkey0head/time-to-split`
- Bài 04 có code tại Zenodo `https://doi.org/10.5281/zenodo.21549024`; chỉ chạy nếu lấy được đúng dense-judgment data.
- Bài 05-14: chỉ tải code khi hồ sơ bài xác nhận repository chính thức và code phục vụ câu hỏi project.

Tải code không đồng nghĩa với reproduction thành công. Mỗi repository phải qua: pin commit, đọc README, tạo environment riêng, chạy smoke test, ghi lỗi dependency, đối chiếu dataset/preprocessing/split/metric, rồi mới chạy full.

## Quy tắc kết quả

- `paper_replication`: chạy gần đúng thiết kế bài báo, dùng dataset/code/parameter mà bài công bố.
- `project_controlled_comparison`: cùng dataset, cùng preprocessing, cùng metric, cùng hardware, so sánh 3 split và baseline của project.
- Không gọi kết quả Spark local giả lập là kết quả cluster.
- Không lấy seed project để nói bài báo dùng seed đó. Nếu bài không báo seed, ghi `not_reported`.

## Trạng thái hiện tại

> [!NOTE]
> Cập nhật 2026-11-19: pipeline đã chạy xong notebook 12/13; 5 model × 3 split, 20 cặp kiểm định, slide + plan đã regenerate. Hướng dẫn chạy/đối chiếu: `06_Huong_Dan_Chay_SASRec_va_MRR.md`.

- PDF và text 14 bài đã có ở `docs/References/Papers/`.
- `Exploration/` trước đây trống; bộ hồ sơ cạnh đây là tài liệu đọc đầu tiên.
- Protocol project đã khóa ở `configs/experiment_protocol_v1.json`.
- Đã qua: hồ sơ 01-04 + full matrix 5 model × 3 split (10/10 gate PASS); SASRec+CE đã đo 3 split, run `20261118_144646_13_sasrec_ce_8225755a`.

## Definition of Done

### Deadline deliverable

Project được xem là đủ cho deadline khi có:

- `method_informed_implementation` trên MovieLens-25M project dataset.
- Ba split: `random80_20`, `temporal_global`, `leave_one_out`.
- Model đã đăng kí: sàn `Random` + `MostPopular`, kinh điển `ALS` + `ItemKNN cosine`, SOTA đối chiếu `SASRec+CE`. **Trạng thái 2026-11-19: 5/5 đã chạy; SASRec+CE = 3 split trên GPU local, `tuning_budget=0`, eval subset user; không so runtime với 4 baseline CPU.**
- **1 seed (42)** — đã chốt, ghi rõ trong mọi artifact (`protocol_id = project_protocol_v1`); ma trận nhiều seed bị bỏ vì mâu thuẫn với giới hạn đã khai báo trên slide.
- HR/NDCG, leakage diagnostics, popularity metrics, runtime.
- CSV/JSON raw outputs, hardware/environment manifest; thay bảng mean ± std bằng **bảng per-split + kiểm định cặp Wilcoxon (p, 95 % CI, rank-biserial r)** vì chỉ có 1 seed.
- Paper 01 comparison table và difference ledger.
- BPR **không nằm trong danh sách đăng kí** → không chạy, không có smoke test. EASE cũng bị loại (chỉ nhắc ở dạng phủ định).

### Full reproduction mở rộng

Paper 01 faithful reproduction, nhiều seed, NeuMF/LightGCN và full BPR là mở rộng sau deadline (không thuộc danh sách đã đăng kí). Không để các mục này chặn deliverable chính.

Mọi kết quả phải phân loại `faithful_reproduction`, `partial_reproduction`, `method_informed_implementation` hoặc `blocked`.
