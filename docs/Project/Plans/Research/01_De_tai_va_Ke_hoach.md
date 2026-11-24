# 01 — Đề tài và Kế hoạch nghiên cứu

**Project:** `D:\Master Exers\Big Data\Recomendation_System`
**Phục vụ đồng thời:** IT252BIDA (Xử lý dữ liệu lớn) + IT252STRM (Phương pháp nghiên cứu khoa học)
**Ngày lập:** 2026-11-03 · **Deadline đề cương:** 2026-11-08
**Trạng thái (04/11/2026 02:10):** Dataset chốt · **PoC Spark 3 split chạy xong** · MapReduce + G3 cross-check **PASS** · R analysis xong (7 figures) · MongoDB có dữ liệu · novelty đã có bằng chứng định lượng thật

---

## 1. Tên đề tài

> **Phân tích rò rỉ, thiên lệch phổ biến trong hệ thống gợi ý bằng kiểm toán chiến lược chia tập trên Spark**
>
> *Evaluating the Impact of Data Splitting Strategies on Evaluation Metrics and Popularity Bias in Recommender Systems on a Big Data Platform*

**Tên tiếng Việt rút gọn (dùng trong slide):** *Ảnh hưởng của chiến lược split đến đánh giá RS trên Big Data*

**Lý do chọn tên này:** đề tài nằm ở **giao điểm của ba yêu cầu bắt buộc**:

- Môn Big Data: xử lý 25M tương tác bằng Spark/HDFS/MapReduce, đo quy mô và chi phí.
- Môn PPNCKH: một **khoảng trống nghiên cứu có bằng chứng định lượng** (không phải "áp dụng ALS vào dữ liệu mới").
- Không trùng đồ án Deep Learning (ConvNeXt/ảnh y tế) và không trùng dự án cũ (Prompt Injection).

---

## 2. Bối cảnh và khoảng trống nghiên cứu

### 2.1 Bài toán thực tế

Ngành gợi ý (recommendation) đã dùng **hàng trăm triệu** lượt tương tác để huấn luyện mô hình. Tuy nhiên, phần lớn các bài báo đánh giá mô hình trên tập dữ liệu ngẫu nhiên 80/20 — một **thói quen không được kiểm chứng**. Khi cùng một mô hình được đánh giá bằng các chiến lược chia tập khác nhau (ngẫu nhiên, theo thời gian toàn cục, leave-one-out theo người dùng), **thứ hạng mô hình có thể đảo chiều**, và **thiên lệch phổ biến (popularity bias)** — vấn đề đạo đức thuật toán hàng đầu — có thể **hoàn toàn biến mất** khỏi báo cáo kết quả.

Hệ quả: một công ty có thể đưa ra quyết định triển khai sai dựa trên kết quả đánh giá không đáng tin cậy, và các bài báo học thuật dùng kết luận sai.

### 2.2 Ba bằng chứng định lượng

| #            | Bằng chứng                                                                                                                             | Nguồn                                                                                                                                                                                                  | Con số                                                                                                                                       |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **B1** | Chia tập ngẫu nhiên tạo ra **rò rỉ dữ liệu (data leakage)** trong đánh giá offline RS                                   | *A Critical Study on Data Leakage in Recommender System Offline Evaluation*, ACM TOIS 2022 — DOI `10.1145/3569930`                                                                                 | Rủi ro rò rỉ tồn tại trong cấu hình chia tập phổ biến nhất, gây sai lệch thứ hạng mô hình                                    |
| **B2** | Thiên lệch phổ biến **không lộ ra** dưới split ngẫu nhiên; kết quả khác nhau giữa các miền khác nhau              | *Reproducing Popularity Bias in Recommendation: The Effect of Evaluation Strategies*, ACM TOIS 2023 — DOI `10.1145/3637066`                                                                        | Cùng 1 thuật toán, 2 chiến lược split → **kết luận đảo chiều** về popularity bias                                          |
| **B3** | Chiến lược split tác động tới **thứ hạng mô hình**; thiết kế đánh giá offline thiếu **convergent validity** | *Time to Split*, RecSys 2025 — DOI `10.1145/3705328.3748164`; *On the Convergent Validity of Offline Evaluation Designs for Recommender Systems*, RecSys 2026 — DOI `10.1145/3773078.3831818` | Chưa có nghiên cứu nào đo **mức độ đảo chiều thứ hạng** dưới quy mô lớn, kèm đo coverage/popularity bias cùng lúc |

### 2.3 Khoảng trống cụ thể (chỗ em sẽ khai thác)

Tổng hợp ba bằng chứng B1–B3 và các bài tổng quan:

> **Chưa có nghiên cứu nào audit đồng thời (i) tác động của chiến lược chia tập đến thứ hạng mô hình, (ii) mức độ biến mất của thiên lệch phổ biến, và (iii) chi phí vận hành thực tế trên một pipeline Big Data (Spark/HDFS/MapReduce) ở quy mô hàng chục triệu tương tác.**

Lý do khoảng trống này còn mở:

1. Các nghiên cứu B1–B3 dùng dataset **vừa phải** (đủ để chứng minh hiện tượng, không đủ để đo chi phí Big Data).
2. Nghiên cứu B1–B3 **không đo popularity bias bằng chỉ số định lượng** (coverage, Gini, tỷ lệ exposure của long-tail) — mà đây mới là hệ quả thực tiễn quan trọng nhất của việc split sai.
3. Yêu cầu môn Big Data của HUFLIT **bắt buộc** Spark + Hadoop + MapReduce + MongoDB + R + Streamlit → phần lớn bài RS trong chương trình không có pipeline vận hành để đo chi phí.

### 2.4 Ba phần gap bắt buộc (`02_Tong Quan Tai Lieu.pdf` yêu cầu)

| Phần                  | Nội dung                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Từ |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --- |
| **Known**        | Có một thân thể nghiên cứu lớn đã biết rằng split ảnh hưởng kết quả đánh giá RS, và rằng popularity bias là vấn đề thuật toán–đạo đức đã được biết rõ                                                                                                                                                                                                                                                                                                                                                                              | ~70 |
| **Critical Gap** | Tuy nhiên các nghiên cứu hiện có **chưa đồng thời** đo (i) đảo chiều thứ hạng mô hình, (ii) mức độ biến mất của popularity bias bằng chỉ số định lượng, và (iii) chi phí vận hành ở quy mô Big Data — trên cùng một pipeline và cùng bộ metric, nên chưa biết các hiệu ứng này **cộng hưởng hay triệt tiêu nhau**                                                                                                                                                                                     | ~90 |
| **Proposed**     | Đề tài này lấp khoảng trống đó: dựng một **audit framework** chạy trên PySpark 4.2.0 + HDFS + MapReduce (Python) + MongoDB, trên MovieLens ml-25m (25.000.095 tương tác, 162.541 người dùng, 59.047 mục), so sánh **3 chiến lược split** × **nhiều mô hình nền**, đo đồng thời NDCG/Recall, catalog coverage, Gini của exposure, tỷ lệ exposure long-tail, và chi phí vận hành; kết quả là **bằng chứng định lượng** cho một **giao thức đánh giá** (evaluation protocol) đề xuất | ~80 |

**Tổng: 200–250 từ.** Bằng chứng định lượng **đã có** từ pipeline notebook (10/10 gate PASS, 4 baseline × 3 split, run id trong `docs/Project/Main/Document_Indexing.md`), nguồn trích dẫn `[1]` = TOIS 2022, `[2]` = TOIS 2023, `[3]` = RecSys 2025.

---

## 3. Câu hỏi nghiên cứu

| Mã           | Câu hỏi                                                                                                                                                                                                             | Loại          |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- |
| **RQ1** | Chiến lược chia tập khác nhau có làm **đảo chiều thứ hạng mô hình** gợi ý không, và độ lớn đảo chiều là bao nhiêu?                                                                    | Định lượng |
| **RQ2** | Thiên lệch phổ biến đo bằng coverage / Gini / long-tail exposure thay đổi **bao nhiêu** giữa các chiến lược split?                                                                                | Định lượng |
| **RQ3** | Chi phí vận hành (thời gian, bộ nhớ, số task, I/O) của mỗi chiến lược trên pipeline Spark/HDFS ở quy mô 25M như thế nào?                                                                            | Định lượng |
| **RQ4** | Có **giao thức đánh giá** nào vừa bảo toàn tín hiệu đo (giữ nguyên thứ hạng mô hình) vừa phát hiện được thiên lệch phổ biến, mà vẫn chạy được trong ràng buộc tài nguyên? | Thiết kế     |
| **RQ5** | Kết luận có **giữ được** khi chuyển sang miền khác (cross-domain: Amazon 2023, Steam) không?                                                                                                         | Định lượng |

> **RQ5 là câu hỏi mở rộng.** Nếu không kịp deadline 08/11, RQ5 trở thành "hướng mở rộng" trong phần kết luận, không nằm trong phạm vi cam kết.

---

## 4. W5H2

|                    | Nội dung                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **What**     | Tác động của **chiến lược chia tập dữ liệu** (random 80/20 · temporal global · leave-one-out) đến (a) tín hiệu đo ranking, (b) thiên lệch phổ biến, (c) chi phí vận hành, trong hệ thống gợi ý                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| **Who**      | Người dùng cuối bị ảnh hưởng bởi hệ thống gợi ý có thiên lệch phổ biến (nhóm long-tail bị giảm mức độ phơi bày) + cộng đồng nghiên cứu RS (đánh giá offline sai dẫn tới kết luận sai)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **Where**    | Nền tảng xử lý dữ liệu lớn cục bộ: HDFS (5 container Hadoop 3.2.1) + PySpark 4.2.0 + MongoDB + R + Streamlit; dữ liệu MovieLens ml-25m (GroupLens, Đại học Minnesota)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| **When**     | Dữ liệu phim 1995-01-09 → 2019-11-21 (24,8 năm); thời gian nghiên cứu 11/2026 → 06/2027 (học kỳ 2, 2026–2027)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| **Why**      | Vì split sai tạo rò rỉ dữ liệu và **giấu** thiên lệch phổ biến, dẫn tới quyết định triển khai sai và bài báo với kết luận sai                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **How**      | Audit framework: 3 chiến lược split × **3 tầng baseline bắt buộc** × {NDCG@K, Recall@K, MRR} × {catalog coverage, Gini exposure, long-tail exposure, thời gian/bộ nhớ}. **Tầng baseline theo danh sách đăng kí:** sàn (Random, MostPopular) · kinh điển (ALS, ItemKNN cosine) · SOTA ≤2 năm (SASRec + cross-entropy) — chi tiết `05C_Baseline_3_tang_DSRM.md`. Kiến trúc: HDFS ingest (CSV→Parquet) → MapReduce (**Java**, đã chạy thật 323.737 key) tính popularity/coverage → PySpark ALS → MongoDB (item profile + metrics) → R (thống kê, kiểm định) → Streamlit (dashboard). So sánh công bằng: cùng dữ liệu, cùng phần cứng, seed cố định 42, code công khai; 5/5 baseline đã chạy đủ trên FULL 162.541 user |
| **How Much** | 25.000.095 tương tác · 162.541 user · 59.047 item · 3 chiến lược split · 5 model đã chạy (Random, MostPopular, ALS, ItemKNN) + 1 SOTA tham chiếu (SASRec+CE, GPU local RTX 4050 6 GB — notebook 13 đã chạy 3 split, run `20261118_144646_13_sasrec_ce_8225755a`) · 6+ chỉ số đo · kiểm định cặp Wilcoxon 20 cặp (p + 95% CI + rank-biserial r) · ngân sách tính toán: laptop MSI i7-13620H (10c/16t, 32 GB DDR5, **GPU RTX 4050 Laptop 6 GB**), 4 baseline chạy CPU, SASRec+CE chạy GPU local, không dùng cloud; 1 seed (42) là giới hạn đã khai báo |

---

## 5. FINER

|                       | Đánh giá         | Bằng chứng cụ thể                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| --------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Feasible**    | ✅ Khả thi         | Dataset đã tải và đo thật (25M dòng, 678 MB). PoC Spark 4.2.0 đã chạy được trên máy. Hadoop cluster 5 container đã chạy. MongoDB cần `Start-Service`. R cần cài. Deadline 08/11 còn 5 ngày — khả thi vì **khung nghiên cứu đã có sẵn từ PoC**                                                                                                                                                                                                                                                                                         |
| **Interesting** | ✅ Đáng quan tâm | Trả lời "model nào tốt hơn" không quan trọng bằng "cách đo của ta có đúng không" — đây là vấn đề ảnh hưởng mọi bài báo RS                                                                                                                                                                                                                                                                                                                                                                                                                          |
| **Novel**       | ✅ Có tính mới   | Novelty **ở bài toán đánh giá và thiết kế thực nghiệm**, không ở kiến trúc mô hình: đề xuất **Split Leakage Index (SLI)** — chỉ số rò rỉ dữ liệu **tương đối theo từng người dùng** thay vì toàn cục (chi tiết `08_Tao_tac_SLI_va_giao_thuc_audit.md`) — cùng **giao thức audit 3 bước** ràng buộc so sánh giữa các split. Bằng chứng: định nghĩa toàn cục gán **99,9988%** rò rỉ cho leave-one-out, định nghĩa tương đối cho **0%** — kết luận ngược hoàn toàn |
| **Ethical**     | ✅ Đạo đức      | Dữ liệu đã anonymize, không thuộc tính nhân khẩu học → không cần IRB. License GroupLens: research-use, **bắt buộc trích dẫn** Harper & Konstan (2015) DOI `10.1145/2827872`; không khẳng định endorsement; không redistribute dữ liệu. Phát hiện thiên lệch phổ biến là hướng **có lợi cho người dùng cuối và nhóm long-tail**                                                                                                                                                                                          |
| **Relevant**    | ✅ Liên quan       | Khớp trực tiếp đề cương IT252BIDA (Spark, Hadoop, MapReduce, MongoDB, PySpark, R, Streamlit, prototype, đánh giá, thực nghiệm) và IT252STRM (tổng quan tài liệu, PRISMA, gap, tính mới, W5H2, FINER, đạo đức dữ liệu, lưu vết thực nghiệm)                                                                                                                                                                                                                                                                                                         |

---

## 6. Kiến trúc Big Data

```
                    ┌──────────────────────────────────────┐
                    │  NGUỒN: MovieLens ml-25m (raw CSV)   │
                    │  25.000.095 ratings · 678 MB         │
                    └───────────────┬──────────────────────┘
                                    │  cp → HDFS (namenode:9000)
                    ┌───────────────▼──────────────────────┐
   LAYER 1  │  HDFS ingest: CSV → Parquet (Snappy)      │  container namenode/datanode
   (Lưu trữ)│  partition theo year(partitionBy)        │  bde2020/hadoop:3.2.1
                    └───────────────┬──────────────────────┘
                                    │
       ┌────────────────────────────┴────────────────────────────┐
       │                                                          │
┌──────▼───────────────────────────────────┐   ┌──────────────▼──────────────┐
│  LAYER 2a: MAPREDUCE (Python)            │   │  LAYER 2b: SPARK (PySpark)   │
│  wordcount-style trên ratings            │   │  ALS / ItemKNN / Popularity  │
│  → item popularity histogram theo năm    │   │  → recommendForAllUsers(10)  │
│  → coverage/Gini của exposure           │   │  → Spark ML RankingEvaluator │
│  (chứng minh MapReduce bằng Python)      │   │  spark.sql.shuffle.partitions│
└──────┬───────────────────────────────────┘   └──────────────┬──────────────┘
       └────────────────────────────┬────────────────────────────┘
                    ┌───────────────▼──────────────────────┐
                    │  LAYER 3: MONGODB (model registry)   │
                    │  items (profile), metrics,           │
                    │  experiments (lưu vết thực nghiệm)    │
                    └───────────────┬──────────────────────┘
                                    │
              ┌─────────────────────┴─────────────────────┐
    ┌─────────▼──────────┐                  ┌───────────▼──────────┐
    │  LAYER 4a: R       │                  │  LAYER 4b: STREAMLIT │
    │  SparkR, thống kê   │                  │  Dashboard đánh giá  │
    │  kiểm định, biểu đồ│                  │  split-strategy      │
    └────────────────────┘                  └──────────────────────┘
```

**Ánh xạ sang yêu cầu seminar Big Data:**

| Yêu cầu seminar      | Thành phần kiến trúc                                                          |
| ---------------------- | --------------------------------------------------------------------------------- |
| HDFS + Jupyter         | LAYER 1 (Parquet trên HDFS) + notebook đọc `spark.read.parquet("hdfs://…")` |
| MapReduce + HDFS       | LAYER 2a — MapReduce bằng Python (`mrjob`/`hadoop-streaming`)               |
| MongoDB + Hadoop       | LAYER 3 — nạp output MapReduce vào MongoDB (`pymongo`)                       |
| MongoDB + Spark        | LAYER 2b→3 — `spark.read.format("mongodb")` và ghi metrics ngược lại      |
| R + Spark              | LAYER 4a — `SparkR::sparkR.session()` + `Rscript`                            |
| Streamlit + MongoDB    | LAYER 4b — `streamlit` đọc từ MongoDB                                       |
| MapReduce bằng Python | LAYER 2a                                                                          |

---

## 7. Kế hoạch thực nghiệm

### 7.1 Ma trận thực nghiệm

|                                     | random 80/20 | temporal global 80/20 | leave-one-out / user |
| ----------------------------------- | ------------ | --------------------- | -------------------- |
| **Popularity (MostPopular)**  | ☐           | ☐                    | ☐                   |
| **ItemKNN (cosine)**          | ☐           | ☐                    | ☐                   |
| **ALS (rank=16, maxIter=10)** | ☐           | ☐                    | ☐                   |
| **ALS + time-aware re-rank**  | ☐           | ☐                    | ☐                   |

Chỉ số (mỗi ô):

- **Ranking:** NDCG@10, Recall@10, MRR@10
- **Coverage:** catalog coverage, Gini của exposure, long-tail exposure rate
- **Bias:** popularity-bias ratio = popularity trung bình của item được đề xuất ÷ popularity trung bình toàn catalog
- **Vận hành:** wall-clock, số Spark task, shuffle bytes, peak memory

### 7.2 Quy trình đánh giá chuẩn (áp dụng cho mọi ô)

1. **Cold-start filter:** chỉ giữ test user có ≥5 tương tác train.
2. **Unseen-item report:** đếm số test interaction mà item chưa từng xuất hiện ở train (báo cáo, không loại — đây là hiện tượng cần đo).
3. **Temporal violation:** đếm số test interaction có timestamp **trước** timestamp lớn nhất của train → đây là **định nghĩa định lượng của data leakage** (B1). Với split ngẫu nhiên, giá trị này = toàn bộ tập test → chứng minh rò rỉ.
4. **Seed cố định** 42 cho mọi thành phần ngẫu nhiên.

### 7.3 Kết quả PoC — **ĐÃ ĐO THẬT 04/11/2026**

> **Quy ước số:** hai bảng dưới là **đường A (script, 04/11/2026)** — giữ để truy vết. Số chính thức dùng cho đề cương/báo cáo/slide là **đường C/D/E** ở **§7.3b**.

Nguồn: `results/poc6_<split>.json` → MongoDB `recsys.audit_metrics` → `reports/metrics_summary.csv`.
Ngưỡng liên quan `rating >= 4,0`; ALS implicit (rank 16, maxIter 8, regParam 0,05, alpha 10, seed 42, **FULL 162.541 user — run 2026-11-17**, subsample 30.000 chỉ là run lịch sử 15/11).

**Tầng 1 — chỉ số cấp dữ liệu**

| Chỉ số                                          | random 80/20        | temporal global     | leave-one-out     |
| ------------------------------------------------- | ------------------- | ------------------- | ----------------- |
| Train rows                                        | 19.997.972          | 19.999.206          | 24.837.554        |
| Test rows                                         | 5.002.123           | 5.000.889           | 162.541           |
| **Temporal violation (toàn cục)**         | **100,0000%** | 0,0000%             | 99,9988%          |
| **Temporal violation (tương đối user)** | **98,9158%**  | 0,0000%             | **0,0000%** |
| Item chưa từng xuất hiện                      | 0,0573%             | **8,7595%**   | 0,0388%           |
| User lạnh (cold-start)                           | 0                   | **4.235.246** | 0                 |
| User đánh giá                                  | 162.541             | 137.839             | 162.541           |
| **User có phản hồi liên quan** (Pop/Random/ItemKNN) | 158.688 | **6.219** | 96.003 |
| **User có phản hồi liên quan** (ALS)    | 158.626             | 6.214         | 95.977            |

**Tầng 2-3 — hiệu quả gợi ý và thiên lệch phổ biến**

| Chỉ số                                      | random 80/20     | temporal global  | leave-one-out    |
| --------------------------------------------- | ---------------- | ---------------- | ---------------- |
| NDCG@10 — Popularity                         | 0,0869           | 0,0455           | 0,0183           |
| **NDCG@10 — ALS**                      | **0,2584** | **0,1364** | **0,0474** |
| Hit Rate@10 — ALS                            | 0,2942           | 0,1599           | 0,0141           |
| Catalog coverage — Popularity                | 0,000177         | 0,000290         | 0,000170         |
| Catalog coverage — ALS                       | 0,061389         | 0,056629         | 0,061765         |
| Long-tail coverage                            | 0                | 0                | 0                |
| Gini exposure — Popularity                   | 0,9998           | 0,9997           | 0,9998           |
| Gini exposure — ALS                          | 0,9827           | 0,9713           | 0,9812           |
| **Popularity-bias ratio — Popularity** | **158,64** | **101,26** | **165,27** |
| **Popularity-bias ratio — ALS**        | **12,26**  | **11,20**  | **12,41**  |

### 7.3b Số chính thức — đường C/D/E (2026-11-20, `runs/20261120_012944_09_compare_and_reversal_21d0811a`)

| Chỉ số | random 80/20 | temporal global | leave-one-out |
|---|---:|---:|---:|
| NDCG@10 — ItemKNN | 0,2679 | 0,1409 | 0,0461 |
| NDCG@10 — ALS | **0,2581** | **0,1332** | **0,0469** |
| NDCG@10 — MostPopular | 0,0852 | 0,0455 | 0,0183 |
| NDCG@10 — Random | 0,0003 | 0,0009 | 0,0001 |
| NDCG@10 — SASRec+CE | 0,0163 | 0,0187 | 0,0067 |
| eval_relevant_users (Pop/Random/ItemKNN) | 158.692 | 6.219 | 96.003 |
| eval_relevant_users (ALS) | 158.626 | 6.214 | 95.977 |

> Đọc bảng này: **thứ hạng giữa 5 model không đảo khi so với sàn**, nhưng ngôi đầu đổi chỗ ItemKNN ↔ ALS ở 2/3 split (`best_model_reversals_found = 2`) — khác biệt nhỏ hơn sai số thực hành.

### 7.4 Bằng chứng định lượng đã có (dùng được cho phần Gap)

**B1 — rò rỉ dữ liệu dưới split ngẫu nhiên:**

- Định nghĩa toàn cục: 100,0000% test trước mốc lớn nhất của train.
- **Định nghĩa tương đối theo user: 98,9158%** → rò rỉ không chỉ là hiện tượng toàn cục mà **xảy ra ở gần như từng người dùng**, kể cả khi so với lịch sử của chính họ.
- → Bằng chứng mạnh và **chi tiết hơn** các nghiên cứu B1 (vốn chỉ nêu rủi ro ở mức cấu hình).

**B2 — thiên lệch phổ biến thay đổi theo chiến lược split:**

- Popularity: bias ratio **101-165x**; ALS: **11-12x** → giảm ~13 lần.
- Nhưng `longtail_coverage = 0` ở **cả 6 tổ hợp** → **giảm thiên lệch khác xử lý thiên lệch**. Đây là phát hiện bổ sung so với B2.
- Popularity bias **không biến mất**, chỉ giảm khi dùng mô hình cá nhân hoá.

**B3 — thứ hạng mô hình KHÔNG đảo chiều, nhưng độ lớn thay đổi mạnh:**

- ALS > Popularity ở cả 3 split.
- NDCG@10 của ALS: 0,2581 (random) → 0,1332 (temporal) → 0,0469 (LOO) = **chênh lệch 5,5 lần** (đường C).
- → Bổ sung (cập nhật 2026-11-18 sau khi có ItemKNN): B3 nói "thứ hạng có thể đảo chiều". Kết quả: **thứ hạng không đảo khi so với sàn** (ALS và ItemKNN đều hơn MostPopular/Random hàng trăm lần), **nhưng ngôi đầu đổi chỗ giữa hai model kinh điển ở 2/3 split** (ItemKNN dẫn `random80_20` +0,0098 và `temporal_global` +0,0077; ALS dẫn `leave_one_out` −0,0008) — `best_model_reversals_found = 2`. Effect size |r| = 0,005–0,030 nên khác biệt gần như không về thực hành.

**Phát hiện mới (đóng góp chính):**

1. **Định nghĩa rò rỉ phải tương đối theo user.** Toàn cục cho LOO = 99,9988% (vô nghĩa), tương đối = 0% (đúng thiết kế). Chỉ số phụ thuộc định nghĩa → cần chuẩn hoá.
2. **Đổi rò rỉ lấy dịch chuyển miền.** Temporal loại rò rỉ (0%) nhưng mất **96,1% mẫu đánh giá** (158.688 → 6.219 user — số của Popularity; ALS là 158.626 → 6.214) và có 8,76% item chưa từng xuất hiện. Không có chiến lược nào "miễn phí".
3. **NDCG thấp không phải lỗi mô hình mà lỗi thiết kế đo lường.** ALS explicit cho NDCG xấp xỉ 0 vì xếp hạng theo sai số dự đoán rating; phải dùng implicit ALS + ngưỡng liên quan >= 4,0.
4. **Hệ quả vận hành:** đổi chiến lược split làm thay đổi cả quy mô dữ liệu huấn luyện (20,0M → 24,8M rows) → khác biệt về thời gian chạy và chi phí tính toán, không chỉ về chất lượng đánh giá.

### 7.5 Chứng minh Big Data pipeline (G3 quality gate)

| Hạng mục                           | Kết quả                                                                                    |
| ------------------------------------ | -------------------------------------------------------------------------------------------- |
| HDFS ingest                          | `/recsys/ratings/part-00000.parquet` — 167,8 MB · 1 file                                 |
| MapReduce (Java, Hadoop 3.2.1, YARN) | `PopularityByYear` → **JOB_STATUS=SUCCESS** · 323.737 key (movieId, year)          |
| Spark SQL cùng phép tính          | 323.737 key                                                                                  |
| **Đối chiếu G3**            | ✅ **100,0000% khớp** (323.737/323.737) · tổng tương tác 25.000.095 = 25.000.095 |
| Artifact                             | `results/g3_crosscheck.json`                                                               |

> Lỗi đã ghi lại trong `Environment.md` §5: MapReduce dùng UTC, Spark mặc định local (UTC+7) → phải set `spark.sql.session.timeZone=UTC`. Không có bước này thì G3 lệch 7,65%.

---

## 8. Đóng góp kỳ vọng

1. **Audit framework** chạy lại được (mã nguồn + cấu hình + log thực nghiệm) trên bất kỳ dataset nào có cột timestamp. — *đã hiện thực: `scripts/04_audit_spark.py`*
2. **Bằng chứng định lượng** về mức độ đảo chiều thứ hạng mô hình và mức biến mất của popularity bias giữa các chiến lược split. — *đã đo §7.3-7.4*
3. **Giao thức đánh giá đề xuất** (RQ4): một quy trình đánh giá 3 bước mà vẫn khả thi về tính toán. — *đã rút ra từ kết quả thật: (i) định nghĩa rò rỉ tương đối theo user; (ii) báo cáo kèm `eval_relevant_users` khi so sánh NDCG giữa split; (iii) luôn báo `longtail_coverage` vì bias ratio có thể che mất độ phủ đuôi dài*
4. **Bảng đối chiếu** với kết luận của các nghiên cứu B1-B3 — cho thấy hiệu ứng có **cộng hưởng hay triệt tiêu** ở quy mô lớn. — *đã có bảng đối chiếu sơ bộ §7.4*

---

## 9. Timeline (đến deadline đề cương 21/11/2026)

| Ngày           | Việc                                                                                                             | Output                                                                                                 | Trạng thái            |
| --------------- | ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ | ----------------------- |
| 03/11           | Xác minh dataset, license, schema, số bản ghi; chạy PoC Spark                                                 | plan 00-03                                                                                             | ✅                      |
| **04/11** | **Hoàn tất PoC 3 split x 2 model; MapReduce + G3 cross-check; R analysis; MongoDB**                       | **`results/poc6_*.json`, `results/g3_crosscheck.json`, 7 figures, `recsys.audit_metrics`** | **✅ xong 02:10** |
| 05/11           | Ma trận thực nghiệm đầy đủ; kiểm định thống kê (bootstrap / Wilcoxon); mở rộng tham số             | Bảng kết quả + CI                                                                                   | ⏳                      |
| 06/11           | Streamlit dashboard chạy thật; R/SparkR bổ sung; số liệu vận hành (wall-clock, shuffle bytes)              | Dashboard                                                                                              | ⏳                      |
| 07/11           | Viết đề cương: Introduction (5 phần), W5H2, FINER, kiến trúc, tổng quan tài liệu (PRISMA), đạo đức | Đề cương nháp                                                                                     | ⏳                      |
| **08/11** | **Nộp đề cương**                                                                                       | ✅                                                                                                     | ⏳                      |

**Cắt giảm an toàn (nếu trượt):** bỏ R/SparkR bổ sung (đã có R analysis chạy thật), bỏ cross-domain (RQ5), giữ nguyên trục chính: 3 split x 2 model x 6 chỉ số trên MovieLens.

---

## 10. Rủi ro đã biết và cách xử lý

| Rủi ro                                  | Mức            | Xử lý                                                                                                           |
| ---------------------------------------- | --------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Disk C chỉ còn 4.2 GB**        | 🔴 Cao          | Đã dọn temp; dữ liệu lớn nằm ở `D:\recsys_data` (17.2 GB free). Spark temp dir → đặt trên D         |
| ALS trên 20M dòng chạy lâu           | 🟢 Đã xử lý | ALS implicit fit FULL 162.541 user ~35–38s/split (run 2026-11-17); `maxIter=8`, `rank=16` + `topk_numpy` chunked |
| **R chưa cài**                   | 🟢 Đã xử lý | R 4.6.2 đã cài 04/11 + 5 package; `06_analysis_r.R` chạy thành công                                       |
| **MongoDB service stopped**        | 🟢 Đã xử lý | `mongod` đang chạy, port 27017 listen — không cần quyền admin                                             |
| MapReduce timezone lệch Spark           | 🟢 Đã xử lý | Set `spark.sql.session.timeZone=UTC` — G3 pass 100%                                                            |
| Thiếu mô hình thứ 3-4 trong ma trận | 🟢 Đã xử lý | Đã đủ 5 model đăng kí: thêm Random (`20261118_144717_..._d8644ac1`) và ItemKNN (`20261118_150305_..._0b7511ee`); SASRec+CE đã chạy 3 split trên GPU local RTX 4050, run `20261118_144646_13_sasrec_ce_8225755a` |

