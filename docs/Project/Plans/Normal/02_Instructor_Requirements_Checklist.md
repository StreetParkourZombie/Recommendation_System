# Yêu cầu giảng viên cần xác nhận — Big Data recommender

## Trạng thái triển khai hiện tại (2026-11-14)

- **Đã xác minh cục bộ:** MovieLens-25M raw; GroupLens README/license; `ratings.csv` SHA-256/header/25,000,095 dòng; Spark `local[4]` profile: 0 null, 162,541 users, 59,047 rated items. Notebook 03 exploratory run `20261114_162433_03_understand_interactions_a85f2c2b` COMPLETED; duplicate `(userId,movieId)` pairs = 0; tied per-user timestamps = 1,799,454 groups across 78,496 users; global tied timestamps = 2,225,836. `rating >= 4.0` count 12,452,811 is descriptive only, not agreed relevance. Eligibility/cohort, timestamp policy and split protocol remain open. Run profile: `runs/20261114_162433_03_understand_interactions_a85f2c2b/outputs/interaction_profile.json`.
- **Chưa đạt Gate 1 Hadoop/MongoDB:** Docker engine không kết nối được và `com.docker.service`/`MongoDB` không start được do `Cannot open ... service` trong phiên này; HDFS/MapReduce/MongoDB read/write chưa smoke-test. Không khai là Hadoop/MongoDB pipeline đã hoạt động.
- Các câu dưới đây vẫn cần rubric/giảng viên trả lời trước khi quyết định topology/MVP cuối cùng.

Trước khi đầu tư vào tối ưu, xác nhận các câu sau với rubric/giảng viên:

1. “Có liên quan Big Data” yêu cầu xử lý dataset lớn trên Hadoop/Spark, hay bắt buộc execution phân tán thật trên nhiều worker?
2. Hadoop MapReduce có bắt buộc, hay Spark-only được chấp nhận?
3. Quy mô MovieLens-25M đáp ứng yêu cầu dữ liệu không; cần thể hiện row count, throughput, scale-up hay benchmark?
4. Sản phẩm cần một hệ thống gợi ý chạy được, hay báo cáo nghiên cứu có RQ/giả thuyết/kiểm định?
5. Bắt buộc baseline nào, UI/API/demo nào, và tiêu chí chấm performance nào?
6. Local Spark `local[4]` có được tính là phần xử lý hay chỉ được ghi như local prototype?

## Quyết định an toàn cho đến khi có trả lời

- Có pipeline ứng dụng thật: HDFS + Hadoop MapReduce job + Spark ALS + Popularity fallback + MongoDB + demo.
- Báo cáo trung thực phần phân tán; không gọi Spark local là Spark cluster.
- Không thêm SOTA/deep learning/research matrix nếu rubric không đòi.
- Lưu thời gian, row counts, data sizes, topology và logs để chứng minh phần Big Data.
