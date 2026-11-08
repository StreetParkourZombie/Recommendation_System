# 05B — Ma trận tuân thủ tiêu chí thiết kế nghiên cứu (Bài 03 PPNCKH)

**Mục đích:** đối chiếu 14 tài liệu tham khảo với 8 tiêu chí mà Bài 03 yêu cầu khi chọn bài đối chuẩn:
(1) chia 3 tập train/val/test tách biệt · (2) so sánh SOTA · (3) ý nghĩa thống kê (p-value / nhiều lần chạy)
(4) cùng dữ liệu + tiền xử lý · (5) cùng ngân sách tinh chỉnh · (6) khai báo GPU/CPU/RAM/thời gian chạy
(7) mã nguồn gốc (GitHub/Zenodo) · (8) random seed cố định (tái lập).

**Cứng (hard requirement của thầy):** (6) cấu hình phần cứng, (7) code, (8) seed — *bắt buộc phải kiểm tra được*.

| # | Tài liệu | Venue | 7. Mã nguồn | 8. Seed | Dataset (để đối sánh) | 6. Cấu hình HW |
|---|---|---|---|---|---|---|
| 01 | TOIS 2023 Data Leakage | ACM TOIS 41(3) Art.75 | Có | Có (7 lần lặp, seed khác nhau) | MovieLens-25M, Yelp, Amazon-music/electronic | Không nêu (chỉ hyperparameter) |
| 02 | TORS 2024 Reproducing Pop. Bias | ACM TORS 2(1) Art.5 | Có | Có (fix seed khi split) | MovieLens-1M, LastFM, Book-Crossing | Không nêu |
| 03 | RecSys'25 Time to Split | ACM RecSys '25 pp.874-883 | Có | Có (nhiều seed, báo mean/variance) | ML-1M, ML-20M, Amazon Beauty/Sports, BeerAdv, Diginetica, YooChoose, Zvuk | NVIDIA H100 80GB HBM3 |
| 04 | RecSys'26 Convergent Validity | ACM RecSys '26 pp.410-418 | Có (Zenodo 10.5281/zenodo.21549024) | Không nêu | MovieLens, KuaiRec | Không nêu |
| 05 | TOIS 2023 Bias/Debias Survey | ACM TOIS 41(3) Art.67 | Không (survey) | N/A | N/A (survey) | N/A |
| 06 | UMAI 2024 Pop. Bias Survey | Springer UMAI 34(5) | Không (survey) | N/A | N/A (survey) | N/A |
| 07 | SIGIR'23 Fresh Look | ACM SIGIR '23 pp.2629-2638 | Không (position paper) | N/A | N/A | N/A |
| 08 | RecSys'23 Challenges (tutorial) | ACM RecSys '23 tutorial, 2pp | Không (tutorial) | N/A | N/A | N/A |
| 09 | RecSys'25 Inherited Pop. Bias | ACM RecSys '25, 6pp | Có | Không nêu | Microlens, Amazon Clothing/Electronics | Không nêu |
| 10 | TOIS 2024 Relieving Pop. Bias | ACM TOIS 42(2) Art.52 | Cần kiểm tra lại (PDF scan, không trích được text) | ? | ? | ? |
| 11 | RecSys'21 Quality Metrics | ACM RecSys '21 pp.708-713 | Có (supplemental GitHub) | Không nêu | MovieLens-20M (EASE) | Không nêu |
| 12 | RecSys'20 Data Splitting | ACM RecSys '20 pp.681-686 | Có (github.com/mengzaiqiao/data_splits) | Không nêu | ML-1M, ML-20M, Tafeng, Dunnhumby, Gowalla, Instacart, Netflix, Amazon, Yelp, Pinterest | Không nêu |
| 13 | J.BigData 2019 e-Learning Spark | Springer J. Big Data 6(1):2 | Không có repo | Không nêu | Dữ liệu e-learning ESTenLigne (không public) | 3 VM VirtualBox, Ubuntu 18.04.1, 8 cores Core i5 7th Gen, 8 GB RAM, 32 GB disk/node |
| 14 | ESWA 2023 Evaluation Framework | Elsevier ESWA 231:120659 | Không có repo (dùng code SOTA công khai của Han 2021 / SASRec) | Không nêu | Aptoide private (74.209 users) + MovieLens, Netflix Prize, Steam | Train: NVIDIA Tesla K80 (FloydHub, 1.22 USD/h); Spark serve: AMD A4-5000 1.5GHz, 1 core, Ubuntu VM trên Win10; benchmark: Intel Core i7 / Win10 |

## Kết luận phân loại (theo 8 tiêu chí Bài 03)

### Nhóm A — Đủ điều kiện "bài đối chuẩn" (có code + seed + dataset rõ)
- **[01]** TOIS 2023 Data Leakage: code `github.com/putatu/dataLeakageRec`, 7 lần lặp seed khác nhau, 4 dataset public, hyperparameter search đầy đủ. **Thiếu:** GPU/CPU/RAM.
- **[02]** TORS 2024: code `github.com/SavvinaDaniil/UnfairnessOfPopularityBias`, fix seed khi split. **Thiếu:** HW.
- **[03]** RecSys'25: code `github.com/monkey0head/time-to-split`, nhiều seed + báo variance, 8 dataset, **có HW**: NVIDIA H100 80GB. → **mạnh nhất về tái lập**.
- **[12]** RecSys'20: code + **data splits tải được** (`github.com/mengzaiqiao/data_splits`), 10 dataset. **Thiếu:** seed, HW.
- **[11]** RecSys'21: supplemental code, ML-20M + EASE. **Thiếu:** seed, HW.
- **[04]** RecSys'26: code trên Zenodo (DOI cố định), MovieLens + KuaiRec. **Thiếu:** seed, HW.

### Nhóm B — Chỉ dùng làm nền lý thuyết / định nghĩa (survey, position, tutorial)
- **[05]**, **[06]**, **[07]**, **[08]** — không có thực nghiệm nên tiêu chí code/seed/HW không áp dụng. Dùng cho phần Known + định nghĩa metric (catalog coverage, Gini, exposure).

### Nhóm C — Có thực nghiệm nhưng thiếu khai báo tái lập
- **[09]** RecSys'25 Cold-Start: có code `github.com/gmeehan96/Cold-PopBias`, nhưng **không nêu seed, không nêu HW** → dùng để tham chiếu ý tưởng, không dùng làm mốc so sánh số.
- **[13]** J.BigData 2019: **không có repo**, **không nêu seed**; bù lại **có khai báo HW rất đầy đủ** (3 VM, i5 7th Gen, 8 cores, 8GB RAM, 32GB disk, Ubuntu 18.04.1). → Dùng để chứng minh lớp kiến trúc Spark+Hadoop đã được publish, **không** dùng để so sánh số liệu.
- **[14]** ESWA 2023: **không có repo**, **không nêu seed**; **có khai báo HW + giá thuê cloud rất chi tiết** (Tesla K80 1.22 USD/h; Spark serve AMD A4-5000 1.5GHz 1 core). Dataset Aptoide là **private**, chỉ 3 dataset public dùng để benchmark. → Dùng cho lớp "đánh giá trong big data", **không** tái lập được nguyên văn.

## Hệ quả cho đề cương (phải sửa)

1. **Không được** gọi [13] và [14] là "baseline để so sánh số". Chúng là *công trình cùng lớp kiến trúc* — dùng để chứng minh khoảng trống, không phải mốc so sánh.
2. **Baseline thật của đề tài** phải là mô hình có code + chạy được trên MovieLens ml-25m: chọn từ nhóm A.
3. Bảng đối chuẩn trong Chương 3/4 bắt buộc có 3 dòng khai báo: *phiên bản code + commit hash*, *seed list*, *CPU/GPU/RAM/thời gian chạy* — áp dụng cho cả mô hình của mình.
4. **[10] TOIS 2024** là PDF scan → phải OCR hoặc tải lại bản text trước khi trích dẫn chi tiết.
5. **Thiếu HW ở 10/14 bài** → đây chính là **cơ hội viết phần Critical Gap phụ**: *"ngay cả các nghiên cứu về split strategy cũng không công bố cấu hình phần cứng, khiến chi phí tính toán không thể so sánh"*.

---

## Bổ sung 08:45 — Có bài nào chạy Spark/MapReduce trên **1 máy (Colab/Jupyter)** không?

**Trả lời ngắn: KHÔNG có bài nào trong 14 bài dùng Colab/Google Cloud chạy Spark.** Nhưng có **2 bài chạy Spark trên đúng 1 máy** — đây là tiền lệ học thuật hợp lệ để biện luận với cô.

### Bằng chứng đọc trực tiếp từ PDF

| # | Cách chạy | Trích nguyên văn |
|---|---|---|
| **[14]** ESWA 2023 | **PySpark trên 1 CPU core, 1 node** | *"Because this experiment is to be executed in a **single machine cluster**, we will simulate the typical industrial cluster configurations by estimating the V and Z components using Ψ sequential trials"* · *"We measured the Spark estimated serving latency separately on an **AMD quad-core Processor A4-5000 (1.5 GHz)** CPU machine executing a **Spark server on an Ubuntu VM through a Windows 10 host**. We used a **single CPU core** of this machine"* · Ψ = 12 (số node giả lập) |
| **[13]** J. Big Data 2019 | 3 VM VirtualBox, Hadoop 3.1.1 + Spark 2.3.1 | *"we created 3 virtual machines by installing Ubuntu 18.04.1 LTS ... we have unpacked and installed Hadoop 3.1.1 and Spark 2.3.1 in the cluster node"* · mỗi VM: 8 cores Core i5 7th Gen, 8GB RAM, 32GB disk |
| **[03]** RecSys'25 | GPU thuê, không Spark | *"All experiments are conducted on **NVIDIA H100 GPUs with 80GB HBM3 memory**"* |
| **[01][02][04][09][11][12]** | **Không chạy Spark/MapReduce/Hadoop** | grep `spark|mapreduce|hadoop|pyspark` = **0 hit** ở cả 6 bài |

### Vì sao [14] là tiền lệ mạnh nhất cho mình

[14] **không** thuê cluster thật. Họ chạy Spark local trên **1 core AMD A4-5000 1.5GHz** trong VM Ubuntu trên Windows 10, rồi **giả lập** cluster 12 node bằng cách chạy 12 lần tuần tự để lấy phân phối thời gian Z và V. Tức là:

- Công thức họ dùng: `JobTime = Z + V`, trong đó `Z = JobStartup + StageStartup + StageCleanup + JobCleanup`, `V = max over P cores of sum(TaskTime)`.
- Đo Z và V bằng Ψ = 12 lần chạy tuần tự → ước lượng cluster m5.12xlarge trên AWS EMR (2.958 USD/h).
- Kết quả vẫn **được Elsevier Q1 chấp nhận công bố**.

→ Nghĩa là: **chạy Spark trên 1 máy + suy ra chi phí cluster bằng mô hình giải tích là phương pháp đã được bình duyệt ở tạp chí Q1.** Mình dùng đúng cách này thì không ai bắt bẻ được.

### Nhưng có 1 điều phải cẩn thận

[14] vẫn **khai báo chi tiết** phần cứng (AMD A4-5000, 1.5GHz, 1 core, Ubuntu VM, Windows 10 host). Dùng Colab mà không khai báo cấu hình thì vi phạm tiêu chí (6) của Bài 03.

**Colab phải khai:** Runtime type (Python 3 / CPU), RAM, số vCPU, disk, phiên bản Spark, Java version — vì Colab đổi cấu hình theo thời gian. Ghi `!nproc`, `!free -h`, `!lscpu`, `spark.version`, `java -version` vào log.

### Phương án đề xuất cho đề tài (an toàn nhất)

Kết hợp 2 lớp, không phụ thuộc Colab:

| Lớp | Chạy ở đâu | Vai trò | Trạng thái |
|---|---|---|---|
| **A. Kiến trúc thật** | Máy anh: 5 container Hadoop 3.2.1 (namenode, datanode, resourcemanager, nodemanager, historyserver) + HDFS + MapReduce **Java** + PySpark | Chứng minh đúng kiến trúc đã nêu, đúng yêu cầu seminar | **ĐÃ CHẠY THẬT 30/09-01/10** (WordCount, HDFS commands) + 04/11 (MapReduce Java 323.737 key, G3 PASS) |
| **B. Tái lập 1 lệnh** | Colab / notebook | Người phản biện chạy lại được ngay, không cần Docker | Cần đóng gói notebook `spark.read.parquet()` → ALS → metric |

**Cách nói với cô:**
> "Kiến trúc của em là HDFS + YARN + MapReduce Java + PySpark, chạy thật trên cluster 5 container (có log, có screenshot YARN Web UI). Notebook Colab là **bản rút gọn để tái lập** — chạy cùng đoạn mã PySpark trên `local[*]`, cùng seed, cùng split, ra đúng con số trong báo cáo."

Như vậy:
- Đúng kiến trúc cô yêu cầu (không phải "Spark cho có").
- Có tái lập (tiêu chí 7 + 8 của Bài 03).
- Có khai báo phần cứng (tiêu chí 6).
- Có tiền lệ Q1 (bài [14]).

### Nếu Colab không đủ RAM (giới hạn 12.7 GB, ml-25m CSV 678 MB → Parquet 176 MB)

Vẫn OK: Parquet 176 MB nhỏ hơn nhiều so với 12.7 GB. Nhưng ALS map 162.541 × 59.047 (rank 16) sẽ cần ~1-2 GB cho item factors. Nên:
- Giữ `spark.driver.memory=8g`, `spark.sql.shuffle.partitions=8` (đã set trong script hiện tại).
- Lấy mẫu 30.000 user như PoC đã làm (đã ghi trong memory 04/11).
- Biến **cấu hình tài nguyên** thành một dòng trong bảng đối chuẩn, y như [14] làm với AMD A4-5000.
