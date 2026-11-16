# Kế hoạch hệ thống gợi ý Big Data (bản nền tảng)

**Điểm bắt đầu triển khai:** theo notebook-first workflow tại `docs/Project/Plans/Research/Implementation/00_Notebook_First_Plan.md`. L0–L2 và L3 exploratory đã chạy; relevance, xử lý duplicate, tie policy, cohort và split protocol vẫn chưa chốt. Gate 1 Hadoop/HDFS/MapReduce/MongoDB còn mở do service chưa smoke-test. Chỉ đánh dấu gate khi có log/checkpoint chạy thật.


## Triển khai lại từ đầu — 2026-11-14

Người mới bắt đầu theo notebook, không theo script legacy:

1. `notebooks/jupyter/00_environment_check.ipynb` — kernel/Python/Java/PySpark/Spark local. L0 PASS.
2. `notebooks/jupyter/01_verify_dataset.ipynb` — xác minh raw GroupLens có sẵn, chỉ đọc. L1 PASS; không tải lại.
3. `notebooks/jupyter/02_profile_ratings_with_spark.ipynb` — schema/count/quality bằng Spark. L2 PASS trên `local[4]`.
4. `notebooks/jupyter/03_understand_interactions.ipynb` — L3 exploratory profile: ratings/history/popularity, duplicate pairs, global and per-user timestamp ties. Completed; protocol decisions remain open.

Notebook 03 run `20261114_162433_03_understand_interactions_a85f2c2b` completed on Spark `local[4]`; all 7 code cells and 8 checkpoints passed. Profile: 25,000,095 ratings; 12,452,811 ratings `>= 4.0` (exploratory count only); 162,541 users; 59,047 rated items; 0 duplicate `(userId,movieId)` pairs; 1,799,454 per-user timestamp groups tied across 78,496 users; 2,225,836 global tied timestamps. `approxQuantile` results use relative error 0.01. Relevance, tie policy, eligibility/cohort and split are not selected. Details: `runs/20261114_162433_03_understand_interactions_a85f2c2b/outputs/interaction_profile.json`.

Notebook source and generator ở `notebooks/jupyter/` và `scripts/generate_notebook_*.py`. Mỗi run lưu manifest, log theo cell và checkpoints dưới `runs/<run_id>/`, `logs/notebooks/`. Executed notebooks là output tạm; không commit. Dataset nằm ngoài repo ở `D:\recsys_data\raw\ml-25m`; không redistribute theo README.

Gate 1 Hadoop/MongoDB chưa qua: Docker và MongoDB service không start được trong phiên hiện tại. Xem `Normal/02_Instructor_Requirements_Checklist.md`; không gọi Spark local là cluster.

Xây dựng hệ thống gợi ý phim dạng batch có thể chạy từ dữ liệu MovieLens-25M đến danh sách top-N cá nhân hóa, dùng Hadoop/Spark cho xử lý dữ liệu quy mô lớn, lưu kết quả và trình bày được qua giao diện hoặc báo cáo.

Đây là track **hệ thống kỹ thuật Big Data**. Không kế thừa RQ, SLI, tuyên bố novelty hoặc ma trận thực nghiệm của track **Research** trừ khi giảng viên yêu cầu rõ. Có thể tối ưu sau khi bản nền tảng chạy ổn.

## Người dùng và chức năng

- Người dùng chọn hoặc nhập `userId`.
- Hệ thống trả top-10 phim chưa được user đánh giá, kèm tên phim và điểm dự đoán/xếp hạng.
- Nếu user chưa có lịch sử hoặc ALS không có user factor: fallback sang MostPopular.
- Quản trị viên chạy pipeline batch, xem trạng thái, số bản ghi, thời gian xử lý và lỗi.

Không xây real-time streaming, API production, đăng nhập hay triển khai cloud trong phiên bản đầu.

## Kiến trúc tối thiểu

```text
MovieLens-25M CSV
  → Hadoop HDFS (raw zone)
  → Hadoop MapReduce (batch aggregation / đối chiếu Big Data)
  → Spark ETL + split + ALS implicit
  → Top-N recommendations + MostPopular fallback
  → MongoDB (recommendations, catalog, run metadata)
  → Streamlit demo / báo cáo
```

- HDFS là lưu trữ phân tán trong cụm Hadoop hiện có.
- MapReduce thực hiện job tổng hợp batch có đầu vào/đầu ra truy nguyên được.
- Spark local hiện có được dùng cho ETL/model nếu không có Spark cluster phù hợp. Ghi rõ `local[4]`; **không gọi Spark local là xử lý Spark phân tán**.
- MongoDB là kho kết quả ứng dụng, không phải bằng chứng tự thân cho xử lý Big Data.

## Lựa chọn mô hình bản đầu

1. **Fallback:** MostPopular, tính trên train, tie-break bằng `movieId`.
2. **Recommender chính:** implicit ALS trên tương tác dương (`rating >= 4.0`), tham số cố định từ config.
3. Candidate phải loại phim user đã tương tác trong train. User mới dùng MostPopular.
4. Chỉ thêm ItemKNN, re-ranking, SOTA hoặc personalization nâng cao sau khi pipeline nền tảng hoàn tất.

Đây là lựa chọn triển khai phù hợp phạm vi, không phải khẳng định ALS tốt nhất.

## Đầu ra phiên bản đầu

- HDFS raw dataset và kết quả MapReduce có thể kiểm tra.
- Parquet/feature tables đã chuẩn hóa.
- Model ALS đã lưu hoặc artifacts đủ tái tạo.
- Collection MongoDB `recommendations` với `userId`, `rank`, `movieId`, `score`, `model`, `runId`, `generatedAt`.
- Fallback Popularity cho cold-start user.
- Demo tra user và xem top-10; trang trạng thái batch đơn giản.
- Báo cáo: kiến trúc, data flow, cấu hình máy/cụm, thời gian từng stage, dung lượng/input-output, lỗi/giới hạn.

## Tiêu chí hoàn thành

1. Pipeline chạy end-to-end trên dữ liệu MovieLens-25M đã xác minh.
2. Hadoop job hoàn tất và output cross-check đúng với phép tính độc lập trên sample/key tương ứng.
3. Spark ALS fit thành công; output top-10 hợp lệ, không có item đã thấy trong train.
4. Fallback hoạt động khi user mới hoặc ALS không trả kết quả.
5. Kết quả ghi/đọc được từ MongoDB và hiển thị trong demo hoặc CLI.
6. Có manifest/config/log, lệnh chạy, versions, runtime, row counts và giới hạn tài nguyên.
7. Đánh giá offline tối thiểu bằng temporal holdout: NDCG@10, Recall@10/HitRate@10, coverage; nêu user eligibility và relevance definition.

## Không nằm trong MVP

- Tái lập Paper 01 hoặc tuyên bố faithful reproduction.
- 10-seed full research matrix, kiểm định giả thuyết mở rộng, R/PRISMA.
- BPR/NeuMF/SASRec/LightGCN, deep learning, online learning.
- SLI như đóng góp nghiên cứu chính.
- So sánh Spark cluster nếu chỉ chạy local mode.
