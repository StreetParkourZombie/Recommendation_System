# 04 — Ma trận tổng quan tài liệu (Synthesis Matrix 5 cột)

**Project:** `D:\Master Exers\Big Data\Recomendation_System`
**Mục đích:** cột 5 = **hạn chế cốt lõi** → trực tiếp sinh ra phần **Critical Gap** của đề cương (theo yêu cầu `02_Tong Quan Tai Lieu.pdf`).

---

## Bảng chính

| # | Tài liệu | Bối cảnh / vấn đề | Phương pháp | Kết quả chính | **Hạn chế cốt lõi (cột 5)** |
|---|---|---|---|---|---|
| **S1** | *Bias and Debias in Recommender System: A Survey and Future Directions* (TOIS 2022, `10.1145/3564284`, 760 cites) | Popularity bias & các dạng bias khác trong RS là vấn đề đã được công nhận | Tổng quan hệ thống, taxonomy bias + taxonomy debias | Phân loại 6 nhóm bias (popularity, exposure, conformity, position, …) và 4 nhóm hướng debias; định nghĩa metric đánh giá debias | **Tổng quan định tính.** Không đo lượng trên một dataset cụ thể với pipeline cố định → không có số để trích cho gap |
| **S2** | *A survey on popularity bias in recommender systems* (UMAI 2024, `10.1007/s11257-024-09406-0`, 159 cites) | Popularity bias ảnh hưởng nhà sản xuất nội dung & người dùng | Tổng quan + định nghĩa metric | Chuẩn hoá định nghĩa: catalog coverage, Gini coefficient, exposure disparity; đề xuất bộ metric | **Không đánh giá ảnh hưởng của chiến lược split.** Không nêu rõ metric nào bị "giấu" bởi split nào → thiếu tương tác split×metric |
| **S3** | *A Critical Study on Data Leakage in Recommender System Offline Evaluation* (TOIS 2022, `10.1145/3569930`) | Offline eval có thể bị rò rỉ dữ liệu → thứ hạng mô hình sai | Phân tích định lượng nhiều dataset, định nghĩa rò rỉ theo timestamp | Chứng minh split ngẫu nhiên gây rò rỉ; đề xuất split theo thời gian | **Không đo popularity bias.** Không đo chi phí. Dataset vừa phải → **chưa biết hiệu ứng có cộng hưởng với bias hay không** |
| **S4** | *Reproducing Popularity Bias in Recommendation: The Effect of Evaluation Strategies* (TOIS 2023, `10.1145/3637066`) | Popularity bias bị tái tạo hay không phụ thuộc chiến lược đánh giá | Thực nghiệm so sánh nhiều chiến lược split trên nhiều dataset | Cùng thuật toán cho **kết luận đảo chiều** về popularity bias giữa các chiến lược split | **Không đo ảnh hưởng tới thứ hạng mô hình.** Không đo chi phí vận hành trên Big Data platform |
| **S5** | *Time to Split: Exploring Data Splitting Strategies for Offline Evaluation of Sequential Recommenders* (RecSys 2025, `10.1145/3705328.3748164`) | Chiến lược split ảnh hưởng tới kết luận về mô hình | Thực nghiệm trên sequential RS, so sánh nhiều split | Chứng minh **thứ hạng mô hình thay đổi** theo chiến lược split | **Chỉ sequential recommenders.** Không đo popularity bias bằng metric định lượng. Không đo chi phí Big Data |
| **S6** | *On the Convergent Validity of Offline Evaluation Designs for Recommender Systems* (RecSys 2026, `10.1145/3773078.3831818`) | Thiết kế đánh giá offline có hội tụ giữa các thiết kế không | Nghiên cứu convergent validity | Chỉ ra nhiều thiết kế đánh giá cho **kết luận không nhất quán** | **Mới (2026), 0 trích dẫn.** Chưa có thực nghiệm quy mô lớn kèm bias metric. Chưa gắn Big Data platform |
| **S7** | *On Challenges of Evaluating Recommender Systems in an Offline Setting* (RecSys 2023, `10.1145/3604915.3609495`) | Offline eval có nhiều thách thức | Taxonomy các thách thức | Liệt kê: metric ≠ mục tiêu, thiếu counterfactual, thiếu độ ổn định | **Mô tả định tính**, không cung cấp thực nghiệm định lượng |
| **S8** | *Take a Fresh Look at Recommender Systems from an Evaluation Standpoint* (SIGIR 2023, `10.1145/3539618.3591931`) | Cách ta đánh giá RS cần xem lại | Position paper + thực nghiệm | Chỉ ra nhiều kết luận cũ dựa trên thiết kế đánh giá không phù hợp | **Không gắn với Big Data pipeline**; không đo bias chi tiết |
| **S9** | *Do Offline Metrics Predict Online Performance in Recommender Systems?* (arXiv 2020, `10.48550/arxiv.2011.07931`) | Metric offline có dự đoán được hiệu quả online? | Thực nghiệm offline↔online trên RecLab | Độ tương quan metric offline ↔ A/B online là **yếu** | Bối cảnh lý thuyết, không phải gap thực nghiệm |
| **S10** | *Relieving Popularity Bias in Interactive Recommender Systems* (TOIS 2023, `10.1145/3618107`) | Debias popularity bias trong interactive RS | Đề xuất thuật toán debias + thực nghiệm | Cải thiện fairness mà không giảm accuracy nhiều | **Giải quyết hậu quả**, không **chẩn đoán nguyên nhân** (nguyên nhân là cách đo). Không đánh giá trên Big Data platform |

---

## Bảng đối chiếu tính mới (6 cột)

| # | Đo **thứ hạng mô hình** đổi? | Đo **popularity bias** định lượng? | Đo **chi phí Big Data**? | Chạy trên **Spark/HDFS/MapReduce**? | Dữ liệu **≥ 10M tương tác**? | **Tập trung 1 dataset** (giảm nhiễu)? |
|---|---|---|---|---|---|---|
| S3 | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| S4 | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| S5 | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| S6 | ⚠️ | ❌ | ❌ | ❌ | ❌ | ✅ |
| S7 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| S8 | ⚠️ | ⚠️ | ❌ | ❌ | ❌ | ❌ |
| **Đề tài này** | **✅** | **✅** | **✅** | **✅** | **✅ (25M)** | **✅** |

**Đọc bảng:** Không bài nào đồng thời có ✅ ở cột 1, 2, 3. Đây chính là **Critical Gap** — và nó là **bằng chứng có cấu trúc** (không phải lập luận cảm tính) cho phần gap 200–250 từ.

---

## Cách dùng bảng này để viết Research Gap

1. **Known:** trích S1 + S2 (bias là vấn đề đã biết, có metric chuẩn) + S3 + S4 + S5 (split ảnh hưởng kết quả).
2. **Critical Gap:** chỉ vào bảng đối chiếu 6 cột — "chưa nghiên cứu nào đo **đồng thời** (i) đảo chiều thứ hạng, (ii) mức biến mất của popularity bias, (iii) chi phí vận hành, trên một pipeline Big Data cố định với một dataset duy nhất ở quy mô ≥ 10M tương tác". Kèm bằng chứng định lượng từ PoC (mục 7.3 của file 01).
3. **Proposed:** mô tả audit framework + kết quả kỳ vọng + cách kiểm chứng.

---

## Tiêu chí sàng lọc tài liệu (theo `02_Tong Quan Tai Lieu.pdf`)

| Tiêu chí | Nội dung | Áp dụng |
|---|---|---|
| **Thời gian** | 2020–2026 | S1–S10 đều thỏa (S9 = 2020) |
| **Chủ đề** | offline evaluation / data leakage / popularity bias / splitting strategy trong recommender systems | S1–S10 đều thỏa |
| **Bài báo** | peer-reviewed, có DOI | ✅ tất cả (S9 là preprint — đánh dấu rõ trong tài liệu tham khảo) |
| **Ngôn ngữ** | tiếng Anh | ✅ |
| **Truy cập** | open access hoặc qua thư viện | ghi rõ trong PRISMA |

---

## Việc còn lại

- [ ] **PRISMA flow diagram** với số bản ghi ở mỗi bước (Crossref + OpenAlex + Scopus), tiêu chí loại.
- [ ] **Bổ sung 2–3 bài** cho nhánh "đánh giá RS trên nền tảng Big Data / Spark" để làm rõ lớp kiến trúc (hiện cột 4 toàn ❌ → cần ít nhất 1–2 bài có ✅ để đối chiếu công bằng).
- [ ] **4 ảnh Zotero** theo yêu cầu `02_Tong Quan Tai Lieu.pdf` (4 ảnh chụp màn hình minh hoạ phần gap).
- [ ] Ma trận này phải được **đưa vào đề cương** dưới dạng bảng — đây là bằng chứng cho "Known / Critical Gap" mà thầy yêu cầu.
