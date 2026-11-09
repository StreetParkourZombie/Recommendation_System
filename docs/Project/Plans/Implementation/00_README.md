# Implementation Reading-First

Project không chạy theo thứ tự "viết code trước, đọc bài sau". Thứ tự bắt buộc:

1. Đọc bài neo, ghi lại claim và thiết kế thí nghiệm.
2. Xác minh dataset, split, model, metric, seed, hardware, repository.
3. Chọn bài có code để chạy reproduction tối thiểu.
4. Tách kết quả reproduction khỏi kết quả controlled comparison của project.
5. Chỉ sau đó chạy pipeline Big Data và trả lời RQ.

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

- PDF và text 14 bài đã có ở `docs/References/Papers/`.
- `Exploration/` trước đây trống; bộ hồ sơ cạnh đây là tài liệu đọc đầu tiên.
- Protocol project đã khóa ở `configs/experiment_protocol_v1.json`.
- Chưa được phép chạy full matrix trước khi hoàn tất hồ sơ 01-04 và smoke test repository 01-03.

## Definition of Done

Project chỉ chuyển sang chạy full khi có:

- Hồ sơ đọc 14 bài, nguồn trích dẫn và mức chắc chắn.
- Bảng mapping claim → experiment → metric → evidence.
- Environment manifest cho từng repository đã thử.
- Reproduction report cho ít nhất bài 01 và bài 02.
- Protocol project đã phân biệt reproduction với controlled comparison.
- Dataset checksum, hardware log, seed log và raw outputs.
