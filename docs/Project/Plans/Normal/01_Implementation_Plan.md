# Kế hoạch triển khai hệ thống gợi ý Big Data

## Quyết định phạm vi

**Sản phẩm:** hệ thống gợi ý phim top-N dạng batch, có fallback, chạy từ MovieLens-25M và dùng hạ tầng Hadoop/Spark/MongoDB đang có.

**Mục tiêu học phần:** chứng minh pipeline xử lý dữ liệu lớn có thể ingest, phân tích, huấn luyện/gợi ý, lưu kết quả và đo vận hành. Không lấy “có Spark/MongoDB” làm bằng chứng Big Data; phải trình bày dataset 25M dòng, partition/data flow, job thực chạy, input/output và runtime.

**Tên đề xuất:** *Xây dựng hệ thống gợi ý phim cá nhân hóa theo lô trên nền tảng xử lý dữ liệu lớn sử dụng Apache Spark và Hadoop*.

Tên và tiêu chí Big Data cuối cùng cần đối chiếu rubric/giảng viên. Kế hoạch không giả định yêu cầu kỹ thuật chưa được xác nhận.

## Use cases

- UC1: quản trị viên chạy pipeline từ dữ liệu ratings đến recommendations.
- UC2: người xem yêu cầu gợi ý bằng `userId` và nhận tối đa 10 phim.
- UC3: user mới nhận top phổ biến toàn cục.
- UC4: quản trị viên kiểm tra run ID, trạng thái, số dòng và thời gian từng stage.

## Các thành phần

| Thành phần | Trách nhiệm | Công nghệ hiện có |
|---|---|---|
| Raw storage | Lưu CSV nguồn, không sửa nguyên bản | HDFS |
| Batch aggregation | Tính tổng hợp MapReduce kiểm chứng được | Hadoop 3.2.1, Java |
| ETL/training | Chuẩn hóa, split, ALS, candidate scoring | PySpark 4.2.0 |
| Catalog | Ánh xạ `movieId` sang title/genres | MovieLens `movies.csv` |
| Result store | Lưu top-N, model/run metadata | MongoDB |
| UI | Tra `userId`, hiển thị top-N và trạng thái | Streamlit hoặc CLI nếu UI tốn thời gian |

## Luồng dữ liệu và ranh giới Big Data

1. **Ingest:** xác minh checksum/row count của ratings; nạp raw vào HDFS; không commit dataset nếu license không cho phép.
2. **MapReduce:** chạy ít nhất một job có mục đích sản phẩm rõ (ví dụ số rating/phim theo năm hoặc popularity aggregate); lưu input/output, counters, job ID, log và cross-check.
3. **ETL:** chuẩn hóa schema và timestamp/timezone; xử lý null/duplicate; ghi Parquet; log rows vào/ra và partition strategy.
4. **Split:** temporal holdout nhất quán; chỉ train dùng để fit popularity/ALS. Ghi rõ global cutoff, train/test counts, user eligibility, cold-start và relevant-item rule.
5. **Train:** MostPopular + implicit ALS (`rating >= 4.0`) trên train; config cố định, seed khai báo, log fit time/model dimensions.
6. **Recommend:** sinh candidates theo batch; bỏ item user đã đánh giá; lấy top-10 deterministic khi tie; cold-start fallback MostPopular.
7. **Persist:** ghi kết quả versioned theo `runId`; không ghi đè run cũ.
8. **Present:** truy vấn theo userId; hiển thị title, rank, score, model/fallback và timestamp.

> Nếu Spark chỉ chạy `.master("local[4]")`, mô tả chính xác là Spark local multi-threaded trên dữ liệu lớn, còn HDFS/MapReduce là phần Hadoop cluster. Chỉ tuyên bố Spark distributed khi thực sự chạy Spark trên cluster và ghi topology.

## Data contract

- Rating key: `(userId, movieId, timestamp)`; giữ rating và timestamp.
- Catalog key: `movieId`; title/genres có thể null được xử lý rõ.
- Recommendation key: `(runId, userId, rank)`; duy nhất trong một run.
- Relevance bản đầu: test rating `>= 4.0`, nếu giảng viên/đề tài yêu cầu implicit recommendation; khóa trước đánh giá.
- Exclude train-seen items trước top-K.
- Bảng đánh giá báo cả eligible users, users có relevant test item, candidate/catalog size; không so model trên cohorts khác nhau mà không ghi.

## Cấu hình hệ thống ban đầu

- Dataset: MovieLens-25M, nguồn/citation theo kế hoạch nguồn dữ liệu hiện hành.
- Spark: giới hạn một job; profile ban đầu `local[4]`, driver `6g`, shuffle partitions `8`, temp ở `D:\recsys_data\spark_tmp`.
- GPU: không cần cho ALS/Spark.
- HDFS/Hadoop: dùng cụm hiện có, ghi node/container topology và memory config thực tế.
- MongoDB: collection tách theo dữ liệu catalog, recommendations, run metadata.
- Vì laptop có RAM khả dụng biến động và thermal throttling, chạy tuần tự, ghi runtime và tình trạng máy; không so runtime tuyệt đối giữa hai profile khác nhau.

Cấu hình này là điểm xuất phát cần smoke test, không bảo đảm mọi stage fit trong RAM. Không chạy nhiều Spark job đồng thời.

## Notebook-first: cách triển khai cho người mới

Điểm bắt đầu: `docs/Project/Plans/Research/Implementation/00_Notebook_First_Plan.md`. Học và chạy từng notebook; đọc phần khái niệm, chạy cell, xem log/checkpoint, rồi mới sang gate tiếp. Không chạy Hadoop/Spark job nặng trước khi gate dữ liệu và split đạt.

Mỗi lần chạy tạo `run_id`, log UTF-8 theo cell, manifest, checkpoint và artifact riêng trong `runs/` và `logs/`. Chỉ đánh dấu gate đạt khi manifest/checkpoint `PASS` và output được đọc lại xác nhận. Dataset, log, output lớn và executed notebook không commit.

### Trạng thái preflight đã xác minh — 2026-11-14

- Notebook `00_environment_check.ipynb` chạy hết: Python 3.14.5, PySpark 4.2.0, JupyterLab 4.6.4; Spark `local[2]` probe count 10.
- MovieLens-25M raw còn ở `D:\recsys_data\raw\ml-25m`; `ratings.csv` 678,260,987 bytes. Không tải lại. SHA-256 quan sát: `9C85525758597DCA76E8D98CEBB9C13E018C2317B09A0878B6D383179526E385`; Notebook 01 vẫn phải xác minh source/schema/count và ghi manifest chính thức.
- D còn khoảng 44.8 GB trống tại thời điểm kiểm tra. Đây là snapshot, không phải mức cố định.
- Docker engine không kết nối được; Windows service MongoDB đang `Stopped`. HDFS/MapReduce/MongoDB chưa qua smoke gate.
- Có cảnh báo thiếu `winutils.exe` và pandas 3.x với PySpark; Spark local probe vẫn chạy. Chưa suy ra Parquet/HDFS write sẽ chạy.

### Notebook learning gates

- **L0:** Notebook 00 không lỗi; manifest `COMPLETED`, package và Spark checkpoints `PASS`. Đã đạt (2026-11-14).
- **L1:** Notebook 01 đã xác minh GroupLens README/license/citation, file inventory, `ratings.csv` size 678,260,987 bytes, SHA-256 `9c85525758597dca76e8d98cebb9c13e018c2317b09a0878b6d383179526e385`, header `userId,movieId,rating,timestamp`, và 25,000,095 dòng. Dataset manifest và checkpoints `PASS`; kernel hoàn tất `COMPLETED`; dữ liệu chỉ đọc, không tải lại. Chi tiết trong `runs/<run_id>/dataset_manifest.json` và `logs/notebooks/<run_id>.log`.
- **L2:** Đạt 2026-11-14. Spark `local[4]`/4.2.0 đọc bằng schema tường minh; 25,000,095 rows, 0 nulls, rating 0.5–5.0, timestamp range ordered, 162,541 distinct users, 59,047 distinct rated items. Profile/checkpoint PASS. `movies.csv` catalog có 62,423 phim theo README; rating interactions chỉ chạm 59,047 phim, khác biệt cần giữ rõ khi định nghĩa catalog coverage.
- **L3 exploratory:** Notebook 03 run `20261114_162433_03_understand_interactions_a85f2c2b` completed on Spark `local[4]`; 7 code cells and all 8 checkpoints PASS. Profile saved/read back at `runs/20261114_162433_03_understand_interactions_a85f2c2b/outputs/interaction_profile.json`. Rating `>= 3.5`: 15,630,129; `>= 4.0`: 12,452,811 (descriptive alternatives, not a selected relevance rule). There are 0 duplicate `(userId,movieId)` pairs; no deduplication needed for this dataset snapshot. Ties: 2,225,836 global timestamps with multiple events (7,110,664 interactions in those groups); 1,799,454 `(userId,timestamp)` groups affecting 78,496 users (6,121,555 interactions, largest group 255). Timestamp alone cannot order tied events. User history: 162,541 users, 20–32,202 ratings, mean 153.81; item frequency: 59,047 rated items, 1–81,491 ratings, mean 423.39. Quantiles are approximate (`approxQuantile`, relative error 0.01), not exact percentiles.
- **L3 scope:** exploratory profile only. Relevance definition, timestamp tie policy, eligibility/cohort, candidate universe, and split strategy remain open; no split/model run. Do not mark research protocol as finalized. Catalog 62,423 versus 59,047 rated items are distinct denominators.
- Docker/Hadoop/MongoDB Gate 1 remains untested/unpassed; local Spark run does not close it.

## Giai đoạn triển khai

### Phase 0 — Xác nhận yêu cầu và đóng phạm vi

- Lấy rubric Big Data của giảng viên: định nghĩa Big Data, công nghệ bắt buộc, yêu cầu phân tán, demo, báo cáo, đánh giá.
- Chốt có bắt buộc UI hay CLI/demo là đủ; chốt yêu cầu nghiên cứu độc lập hay chỉ sản phẩm kỹ thuật.
- Giữ MVP: MovieLens-25M + Hadoop job + Spark ALS + Popularity fallback + MongoDB + CLI/Streamlit + offline evaluation.

**Gate 0:** scope, rubric, demo acceptance criteria được ghi trong manifest.

### Phase 1 — Audit dữ liệu và môi trường

- Xác minh dataset version, license/citation, checksum, 25,000,095 rows và schema.
- Kiểm tra Hadoop containers, HDFS read/write, MapReduce sample, MongoDB read/write, PySpark local smoke.
- Ghi hardware/software versions, topology, RAM/disk headroom; đặt giới hạn một job.

**Gate 1:** không lỗi quyền/đường dẫn; HDFS và MongoDB smoke pass; sample counts đối chiếu.

### Phase 2 — Data pipeline Big Data

- Nạp dữ liệu vào HDFS theo raw zone.
- Chạy MapReduce aggregate end-to-end trên dữ liệu đủ lớn; ghi counters/runtime/output.
- Cross-check output bằng script độc lập trên sample hoặc aggregation Spark; sai lệch phải bằng 0 hoặc được giải thích.
- Chuẩn hóa Parquet, UTC timestamps, schema, quality checks và row-count ledger.

**Gate 2:** raw → HDFS → MapReduce/Spark ETL hoàn tất; output tái lập được.

### Phase 3 — Recommender MVP

- Tạo temporal train/test; không dùng test để fit/tune.
- Huấn luyện MostPopular và ALS implicit; ghi config và run IDs.
- Sinh top-10 cho sample users trước; loại train-seen; kiểm tra uniqueness/range/title mapping.
- Kiểm tra cold-start fallback; sau đó chạy batch output đủ quy mô mục tiêu.

**Gate 3:** user đủ điều kiện có recommendations; fallback và exclusion tests pass.

### Phase 4 — Đánh giá offline và Big Data operation

- Metric tối thiểu: NDCG@10, Recall@10 hoặc HitRate@10, catalog coverage.
- Cùng test cohort cho so sánh model; macro aggregation và relevance rules khai báo.
- Đo ingest, MapReduce, ETL, ALS fit, scoring, MongoDB write/read riêng; ghi wall-clock, rows, file size, shuffle bytes/task metrics nếu có.
- Báo phần chạy trên Hadoop cluster và phần Spark local tách biệt.

**Gate 4:** metric fixture pass; cohort/denominator rõ; run log đủ stage.

### Phase 5 — Demo, báo cáo, đóng gói

- UI tối thiểu: nhập userId, xem top-10, source model/fallback, batch timestamp.
- Nếu UI không kịp, CLI truy vấn + ảnh chụp/log được chấp nhận chỉ khi giảng viên đồng ý.
- Báo cáo architecture/data flow, technology rationale, data volume, topology, performance, evaluation, limitations, reproducibility steps.
- Không đưa dữ liệu MovieLens vào repo nếu license không cho redistribution.

**Gate 5:** demo từ dữ liệu đã persist; hướng dẫn chạy sạch; deliverables khớp rubric.

## Thứ tự ưu tiên khi thời gian thiếu

1. Hadoop/HDFS job thật + cross-check.
2. Spark ALS + MostPopular fallback, top-N cho user.
3. MongoDB persist + truy vấn/CLI.
4. Offline evaluation tối thiểu.
5. UI Streamlit.
6. ItemKNN, reranking, SOTA, dashboard nâng cao.

Không thêm thuật toán trước khi pipeline end-to-end chạy.

## Rủi ro và ứng phó

| Rủi ro | Ứng phó |
|---|---|
| Local Spark bị gọi nhầm là distributed | Ghi `local[4]` rõ; phân định Hadoop cluster và Spark local. |
| OOM khi tạo recommendations toàn catalog | Không materialize user×item matrix; chia batch user, score top-K theo chunk; smoke test trước. |
| RAM/laptop nóng | Một job tại một thời điểm; profile cố định; ghi nhiệt/runtime khi đo được. |
| ALS cold-start/drop rows | Popularity fallback; báo coverage và số user được ALS phục vụ. |
| Leakage trong offline evaluation | Temporal split; fit train-only; loại seen items; test không tuning. |
| Cohort/denominator lệch | Dùng chung user cohort cho model comparison hoặc báo cohort riêng và không so trực tiếp. |
| UI chưa xong | CLI query + persisted output; xin xác nhận với giảng viên. |
| Rubric yêu cầu Spark cluster/SOTA khác | Xác minh ngay Phase 0; điều chỉnh topology/mô hình trước full run. |

## Definition of Done

- [ ] Rubric xác nhận và scope được khóa.
- [ ] HDFS ingest và Hadoop batch job chạy thành công, output cross-check.
- [ ] Spark ETL và ALS chạy trên data được khai báo.
- [ ] MostPopular fallback trả kết quả cho user cold-start.
- [ ] Top-10 không trùng, không chứa train-seen items, title resolve được.
- [ ] Recommendations và run metadata lưu/đọc được từ MongoDB.
- [ ] Có temporal offline metrics với denominator/cohort rõ.
- [ ] Có runtime/data-volume/topology manifest, logs, command và limitations.
- [ ] Demo UI hoặc CLI được giảng viên chấp nhận.

## Sau khi MVP đạt

Tối ưu riêng từng tầng, mỗi thay đổi có baseline runtime/metric trước-sau: partitioning, caching, ALS hyperparameters, ItemKNN, hybrid/reranking, Spark cluster execution, incremental update, monitoring. Tối ưu không thay thế MVP acceptance.
