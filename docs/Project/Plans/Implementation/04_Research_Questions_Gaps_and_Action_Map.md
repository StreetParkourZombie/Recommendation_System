# Bản đồ câu hỏi, gap và triển khai từ 14 bài báo

## Cách dùng

Vòng lặp: đọc câu hỏi/ý chính -> đọc phương pháp/kết quả trong PDF -> chạy smoke test code nếu có -> ghi reproduction report -> so sánh gap project -> thiết kế experiment riêng.

`Gap của bài` là giới hạn/câu hỏi còn bỏ ngỏ trong bài báo. `Gap project` là phần project có thể kiểm tra tiếp trên MovieLens-25M và pipeline Spark. Không gọi kết quả project là reproduction nếu dataset, preprocessing, split, model hoặc metric khác bài gốc.

## Định hướng

### Neo chính: Paper 01

Paper 01 đặt vấn đề: offline evaluation có thể vi phạm global timeline; train có thể chứa tương tác xảy ra sau test; leakage làm thay đổi accuracy và model ranking. Bài dùng BPR, NeuMF, SASRec, LightGCN trên MovieLens-25M và ba dataset khác; code: `https://github.com/putatu/dataLeakageRec`.

Project lấy Paper 01 làm neo về **data leakage và tính hợp lệ của offline evaluation**, nhưng không sao chép toàn bộ model deep-learning. Project kiểm tra ba split trên cùng protocol, trước hết với MostPopular và ALS để có controlled comparison chạy được.

### Neo phụ: Paper 02

Paper 02 kiểm tra vì sao nghiên cứu popularity bias có kết luận khác nhau. Bài tách data, algorithm, user-group division và evaluation strategy; code: `https://github.com/SavvinaDaniil/UnfairnessOfPopularityBias`.

Project dùng bài này mở rộng từ leakage sang popularity bias. Muốn gọi reproduction phải khớp popularity definition, user groups, evaluation strategy và `%DeltaGAP`; coverage/Gini/long-tail của project chỉ là controlled metrics nếu không khớp toàn bộ.

### Nền split: Paper 03 và 12

Dùng để hiểu split strategy. Paper 03 có code `https://github.com/monkey0head/time-to-split`; Paper 12 là nghiên cứu tiền thân. Nếu project chạy ALS/MostPopular thì gọi method-informed implementation, không gọi reproduction sequential recommender.

### Nền validity, metric và Big Data

- Paper 04: sparse offline ranking có thể khác dense judgments; dùng làm limitation nếu thiếu dense data.
- Paper 11: metric cần contract rõ; dùng để viết unit test.
- Paper 13-14: Spark/Hadoop, runtime và disclosure; không phải neo leakage/bias.
- Paper 05-10: taxonomy, bias, cold-start, evaluation critique và mitigation; dùng định nghĩa/discussion.

## Câu hỏi, ý chính và gap từng bài

### Paper 01 — Data Leakage

**Ý chính:** Global timeline là điều kiện của dự đoán tương lai. Random split và split không quan sát global timeline có thể để collaborative filtering học future interactions; leakage làm thay đổi accuracy và relative model order.

**Câu hỏi:** Vì sao leakage xảy ra? Model có recommend future items không? Leakage ảnh hưởng accuracy/ranking thế nào? Timeline scheme có thực tế hơn không?

**Gap:** Cần kiểm tra chính xác protocol, seed, hardware và preprocessing từ repository; kết quả phụ thuộc dataset/cutoff/model/metric. Bài chưa audit đồng thời leakage, popularity bias và runtime trong một protocol gọn. Project cần phân biệt global leakage với per-user/local timeline.

**Project:** RQ1, leakage diagnostics, `random80_20` vs `temporal_global` vs `leave_one_out`, ranking stability, MostPopular/ALS trước. **Code:** có, ưu tiên 1.

### Paper 02 — Popularity Bias Reproduction

**Ý chính:** Kết luận popularity bias khác nhau do data, algorithm, user-group division và evaluation strategy; evaluation strategy có thể giải thích nhiều khác biệt.

**Câu hỏi:** Có tái lập nghiên cứu trước không? Bốn yếu tố ảnh hưởng bao nhiêu? Vì sao kết luận mâu thuẫn?

**Gap:** Cần kiểm tra tuning, thư viện và domain khác. Metric phụ thuộc popularity/group definition; chưa trả lời trực tiếp split leakage trên protocol project.

**Project:** RQ2; giữ data/model/grouping cố định, đổi split. Chỉ báo `%DeltaGAP` khi khớp protocol; nếu không, báo metrics project riêng. **Code:** có, ưu tiên 2, environment riêng.

### Paper 03 — Time to Split

**Ý chính:** Sequential recommender evaluation nhạy với cách chia dữ liệu; split là thiết kế thực nghiệm quan trọng.

**Câu hỏi:** Split nào phù hợp? Split đổi metric/ranking thế nào? Chi phí và khả năng triển khai ra sao?

**Gap:** Sequential model/RePlay khác ALS/MostPopular; cần tách ảnh hưởng split khỏi ảnh hưởng sequence model.

**Project:** Giải thích split definitions và RQ1; reproduction chỉ khi khớp dataset/model/config. **Code:** có, ưu tiên 3 sau kiểm tra dependency.

### Paper 04 — Convergent Validity

**Ý chính:** Sparse offline ranking có thể không đồng thuận với dense relevance judgments; metric offline không tự động là ground truth.

**Câu hỏi:** Sparse/dense có cùng model ranking không? Setup và seed ảnh hưởng đồng thuận ra sao? Báo uncertainty thế nào?

**Gap:** Cần dense judgments và đúng MovieLens-32M/KuaiRec. Rating threshold project không thay thế dense judgments.

**Project:** Limitation và sensitivity discussion; không experiment chính. Code chỉ tải nếu Zenodo có đủ code và dense data.

### Paper 05-10 — Bias, validity, cold-start và mitigation

- **05:** Taxonomy bias/debias. Gap: taxonomy không trả lời split effect. Dùng định nghĩa, related work, limitation; không tải code.
- **06:** Popularity bias có nhiều definition/metric. Gap: thiếu protocol nối split, ranking, long-tail. Dùng chọn metric; không tải code.
- **07:** Offline metric có giả định ẩn, không đồng nghĩa online quality. Gap: cần diagnostics chạy được. Dùng rationale; không reproduction.
- **08:** Split, negative sampling, metric, data bias, external validity là rủi ro. Bài ngắn, dùng checklist; không tải code.
- **09:** Cold-start có thể kế thừa/khuếch đại popularity bias. Gap: project chưa có cold-start task/metadata/model. Dùng giới hạn diễn giải `unseen_item`; không tải phase hiện tại.
- **10:** Interactive/RL có thể giảm popularity bias. Gap: project static offline, không interaction/simulator. Dùng future work; không tải phase hiện tại.

### Paper 11-14 — Metric và Big Data

- **11:** Cùng tên metric vẫn khác do candidate set, relevance, cutoff, aggregation, user filtering. Gap: cần metric contract và fixture test. Dùng unit test; không reproduction toàn bài.
- **12:** Split là experimental design và có thể đổi kết luận model. Gap: nối split với leakage, popularity bias, runtime. Dùng cho RQ1; code chỉ tải nếu artifact phù hợp.
- **13:** Spark/Hadoop map được vào recommendation; cần báo data flow, distributed role, cluster, runtime. Gap: task e-learning khác MovieLens audit. Dùng cho RQ3 và environment disclosure; không cần code phase chính.
- **14:** Big Data evaluation gồm recommendation quality và execution/serving cost. Gap: cần xác minh artifact/topology/hardware. Dùng RQ3, hardware manifest, wall-clock, memory/I/O/task; không neo leakage/bias.

## Gap project nên giữ

1. **Split + leakage + ranking:** cùng MovieLens-25M, preprocessing, metric và seed set.
2. **Split + popularity bias:** giữ data/model/grouping cố định, đổi split, đo coverage/Gini/long-tail.
3. **Audit + Big Data cost:** báo runtime, memory, I/O, task và hardware.
4. **Leakage definition:** báo global và per-user/local diagnostics; không dùng SLI chưa unit-test làm claim chính.

## RQ lõi

- **RQ1:** Split strategy có thay đổi model ranking và ranking metrics không? Mức thay đổi đo bằng effect/rank stability thế nào?
- **RQ2:** Split strategy có thay đổi popularity-bias metrics không khi data/model/grouping giữ cố định?
- **RQ3:** Mỗi split và pipeline có runtime, memory, I/O và task cost thế nào trên Spark local/Colab simulation?
- **RQ4:** Protocol nào báo cáo đồng thời utility, leakage, popularity bias và cost mà vẫn tái lập được trong tài nguyên giới hạn?

**RQ5 cross-domain:** phase mở rộng, không chặn kết luận chính.

## Việc làm ngay

1. Clone/pin Paper 01, đọc README/environment, chạy smoke test, ghi reproduction report.
2. Lặp lại Paper 02 trong environment riêng.
3. Kiểm tra Paper 03 nếu dependency khả thi.
4. Lập bảng Paper protocol vs Project protocol.
5. Sau smoke test mới chạy MostPopular và ALS trên ba split.

## Phân loại kết quả

- `faithful_reproduction`: khớp protocol và artifact đủ.
- `partial_reproduction`: khớp phần chính nhưng còn sai khác đã ghi.
- `method_informed_implementation`: dùng ý tưởng bài, project tự triển khai.
- `blocked`: chưa chạy được do code/data/environment.
