# 06 — Phương án dự phòng và các phương án đã loại

**Project:** `D:\Master Exers\Big Data\Recomendation_System`
**Ngày:** 2026-11-03 · Deadline đề cương: **2026-11-08**

---

## 1. Phương án dự phòng chính: giữ trục đánh giá, giảm tầng hạ tầng

**Kích hoạt khi:** pipeline HDFS/MapReduce/MongoDB/R/Streamlit không hoàn thành trước 06/11.

| Tầng | Bình thường | Dự phòng | Mất gì |
|---|---|---|---|
| Tầng 1 (metrics cấp dữ liệu) | Spark + HDFS | **PySpark local đọc Parquet trên D** | Không mất gì về khoa học — đây là phần bằng chứng mạnh nhất |
| Tầng 2 (Popularity) | Spark | **Spark** | không |
| Tầng 3 (ALS) | Spark | **Spark, numpy top-K** | không |
| Tầng 4 (ItemKNN, re-rank) | Spark | **thay bằng BPR** (`beta-team/beta-recsys`) | vẫn đủ tầng kinh điển, không mất hàng bảng |
| **3 tầng baseline** | Sàn + Kinh điển + SOTA | **không được bỏ tầng nào** — đây là yêu cầu bắt buộc của Bài 03 | nếu thiếu 1 tầng → đề cương bị trả |
| SOTA (SASRec+) | PyTorch, cần GPU/thời gian | **EASE** (closed-form, CPU vài phút) — [11] RecSys'21 dùng đúng EASE trên ML-20M + global timestamp split | không mất gì: vẫn là SOTA có tiền lệ Q1/CORE A |
| Lưu trữ | MongoDB | **Parquet + JSON** | mất demo MongoDB → ghi rõ trong phụ lục |
| Phân tích | R + SparkR | **Python (scipy/pandas/matplotlib)** | mất seminar "R + Spark" → ghi rõ trong phụ lục |
| Trực quan | Streamlit | **bảng Markdown + biểu đồ tĩnh** | mất demo dashboard |

**Lý do dự phòng này hợp lý:** đề tài là về **đánh giá cách đánh giá**, không phải về hạ tầng. Nếu hạ tầng không kịp, giữ trục khoa học còn hơn làm hỏng cả hai.

### Ranh giới KHÔNG được vượt qua khi dự phòng

Bài 03 PPNCKH yêu cầu **3 tầng baseline** (truyền thống / kinh điển / SOTA) và **khai báo phần cứng + seed + code**.
Ba thứ này **không phải hạ tầng** — chúng là **thiết kế nghiên cứu**. Dự phòng hạ tầng được, dự phòng thiết kế thì không.

| Thứ được phép cắt | Thứ tuyệt đối không cắt |
|---|---|
| MongoDB → Parquet/JSON | 3 tầng baseline |
| R → Python (scipy/matplotlib) | 10 seed + Mean ± Std |
| Streamlit → bảng Markdown | Khai báo CPU/GPU/RAM + wall-clock |
| ItemKNN → BPR | Ngân sách tinh chỉnh bằng nhau |
| SASRec+ → EASE | File split công bố của [12] |

---

## 2. Phương án dự phòng phụ: giảm quy mô dữ liệu

**Kích hoạt khi:** thời gian chạy ALS vượt 30 phút/lần.

| Mức | Dữ liệu | Dùng cho |
|---|---|---|
| **M1** (mặc định) | 25.000.095 ratings, ALS subsample 30.000 user | kết quả chính |
| M2 | lọc `rating ≥ 3` (implicit positive) | kiểm tra độ nhạy với ngưỡng |
| M3 | lọc `timestamp ≥ 2010-01-01` | kiểm tra độ nhạy với kỷ nguyên dữ liệu |

**Không** dùng M2/M3 thay cho M1 trong báo cáo chính — chỉ là **phân tích độ nhạy** (robustness), trình bày ở phụ lục.

---

## 3. Các phương án đã cân nhắc và LOẠI

| Phương án | Lý do loại |
|---|---|
| **Medical Equipment / MAUDE (FDA)** | Bỏ theo quyết định 03/11. Đã dọn khỏi cây sống (chỉ còn `_backup_*`). Ngoài ra: narrative tiếng Anh, không có tín hiệu ranking tự nhiên → không phù hợp đề tài đánh giá RS |
| **Prompt Injection detection** | Bỏ. Đã có repo, giữ làm negative result. Không có ground truth ranking, không đo được NDCG/coverage |
| **Amazon Reviews 2023 — All_Beauty** | **Loại vai trò dataset chính.** PoC thật: 701.528 dòng gốc → 5-core chỉ còn **4.240 dòng / 477 user / 610 item**. Quá nhỏ để kết luận khoa học; tỷ lệ user/item chưa từng xuất hiện ở train quá lớn. Giữ làm cross-domain dự phòng |
| **Ảnh y tế (BreakHis, PCam, ISIC, Otoscopy)** | Lệch yêu cầu môn Big Data; trùng đồ án Deep Learning của anh (ConvNeXt-Tiny, otoscopy) |
| **Yelp full** | `yelp_business` bị **401 gated**; chỉ có `yelp_review_full` (không đủ metadata) |
| **Retailrocket** | Kaggle download endpoint **404**; chỉ còn mirror HF |
| **Zenodo API** | 403 Forbidden → không dùng được |
| **R (cài đặt)** | **Đã cài 04/11**: R 4.6.2 tại `C:\Program Files\R\R-4.6.2`, user library `D:\R-library`. Package: jsonlite, dplyr, ggplot2, mongolite, corrplot. Script `06_analysis_r.R` chạy thành công, sinh 7 figures + 2 CSV + nạp MongoDB |
| **Dataset Việt Nam** | Đã loại từ trước. Không còn nguồn mở, chất lượng thấp, và không có ground truth ranking đủ tin cậy |
| **Xây dựng "big data platform" thật (YARN, nhiều node)** | Quá tốn thời gian cho deadline 5 ngày; Hadoop cluster 5 container hiện có là đủ để chứng minh MapReduce + HDFS + Spark |
| **So sánh 5+ mô hình (NCF, LightGCN, SASRec…)** | Quá tốn thời gian train; đề tài không cần state-of-the-art accuracy mà cần **audit framework**. 4 mô hình (Popularity, ItemKNN, ALS, ALS+re-rank) đã đủ để RQ1 |
| **Cross-domain (Amazon, Steam) ngay bây giờ** | RQ5. Chưa loại — nhưng **không chặn** đề cương. Nếu xong sớm thì làm, không thì ghi "hướng mở rộng" |

---

## 4. Rủi ro còn lại + kế hoạch giảm thiểu

| # | Rủi ro | Xác suất | Hậu quả | Giảm thiểu | Người quyết định |
|---|---|---|---|---|---|
| R1 | Chưa cài được R → mất seminar "R + Spark" | Trung bình | Đề cương thiếu 1 yêu cầu | Dự phòng §1 (Python + ghi rõ phụ lục); **cố gắng cài R trong background từ 04/11** | Tự quyết |
| R2 | MongoDB không khởi động được (service) | Thấp | Mất demo MongoDB | `Start-Service MongoDB`; nếu lỗi → dùng `mongod` local như project `Multimodal_Social_Media_Analytics` đã làm | Tự quyết |
| R3 | MapReduce (Python) chạy lỗi trên Windows | Trung bình | Mất 1 yêu cầu seminar | Chạy MapReduce **trong container** `bde2020/hadoop` (đã có sẵn, đang healthy) → đúng đề cương hơn | Tự quyết |
| R4 | HDFS đọc từ PySpark local bị lỗi `winutils` | Trung bình | Không đọc được Parquet trên HDFS | Đặt `hadoop.home.dir` trỏ vào thư mục Hadoop trong container, hoặc đọc Parquet từ D (dữ liệu vẫn do MapReduce sinh ra từ HDFS) | Tự quyết |
| R5 | Không kịp 4 model × 3 split | Trung bình | Bảng kết quả thiếu ô | Dự phòng §1 + §6 stop criteria trong `05_Ke_hoach_thuc_nghiem.md` | Tự quyết |
| R6 | Thầy yêu cầu thêm đề tài mới (đổi hướng lần 3) | Thấp | Lãng phí | **Báo khả thi sớm** (trước 05/11) kèm số liệu PoC thật để thầy ra quyết định có căn cứ | Cần hỏi anh |
| R7 | Disk D đầy khi chạy nhiều thí nghiệm | Thấp | Crash | D có 8.4 GB free; Spark temp → `D:\recsys_data\spark_tmp`; xoá log cũ khi > 2 GB | Tự quyết |
| R8 | Ban đêm/em ngủ → không chạy được việc dài | Cao | Chậm tiến độ | Viết script **chạy nền** (background) + báo cáo khi xong; không chờ trong turn | Tự quyết |

---

## 5. Những gì KHÔNG được làm

- ❌ Đổi dataset giữa chừng (đã trả lời đề tài 2 lần rồi → giữ nguyên MovieLens ml-25m).
- ❌ Bắt đầu thêm hướng nghiên cứu mới trước 08/11.
- ❌ Mở rộng tìm kiếm tài liệu không dẫn tới gap — mục tiêu là **đối chiếu** tài liệu đã có, không phải sưu tầm.
- ❌ Xoá repo Prompt Injection (giữ làm negative result).
- ❌ Tải dataset > 2 GB thêm (D chỉ còn 8.4 GB).
- ❌ Bỏ qua yêu cầu đạo đức dữ liệu và trích dẫn license (GroupLens yêu cầu acknowledge).
