# 04 — Ma trận tổng quan tài liệu (Synthesis Matrix 5 cột)

**Project:** `D:\Master Exers\Big Data\Recomendation_System`
**Mục đích:** cột 5 = **hạn chế cốt lõi** → trực tiếp sinh ra phần **Critical Gap** (theo `02_Tong Quan Tai Lieu.pdf`).
**Cập nhật 2026-11-07:** toàn bộ tài liệu là **bản nhà xuất bản** (ACM / Springer / Elsevier). Đã loại tài liệu arXiv-only. Thêm nhánh "Big Data platform" (S13, S14) để bảng đối chiếu công bằng.

---

## Bảng chính

| # | Tài liệu | Bối cảnh / vấn đề | Phương pháp | Kết quả chính | **Hạn chế cốt lõi (cột 5)** |
|---|---|---|---|---|---|
| **S1** | *Bias and Debias in Recommender System: A Survey and Future Directions* (ACM TOIS 41(3) Art.67, 2023, `10.1145/3564284`) | Popularity bias & các bias khác là vấn đề đã được công nhận | Tổng quan hệ thống, taxonomy bias + debias | Phân loại 6 nhóm bias (popularity, exposure, conformity, position…), 4 nhóm hướng debias | **Tổng quan định tính**, không đo trên dataset + pipeline cố định → không có số để trích cho gap |
| **S2** | *A survey on popularity bias in recommender systems* (Springer UMAI 34(5):1777–1834, 2024, `10.1007/s11257-024-09406-0`) | Popularity bias ảnh hưởng nhà sản xuất nội dung & người dùng | Tổng quan + định nghĩa metric | Chuẩn hoá catalog coverage, Gini, exposure disparity | **Không đánh giá ảnh hưởng của chiến lược split** → thiếu tương tác split×metric |
| **S3** | *A Critical Study on Data Leakage in Recommender System Offline Evaluation* (ACM TOIS 41(3) Art.75, 2023, `10.1145/3569930`) | Offline eval rò rỉ dữ liệu → thứ hạng mô hình sai | Phân tích định lượng nhiều dataset, định nghĩa rò rỉ theo timestamp | Split ngẫu nhiên gây rò rỉ; đề xuất split theo thời gian | **Không đo popularity bias, không đo chi phí.** Dataset vừa phải → chưa rõ hiệu ứng cộng hưởng với bias |
| **S4** | *Reproducing Popularity Bias in Recommendation: The Effect of Evaluation Strategies* (ACM TORS 2(1) Art.5, 2024, `10.1145/3637066`) | Popularity bias tái tạo được hay không phụ thuộc chiến lược đánh giá | Thực nghiệm nhiều chiến lược split × nhiều dataset | Cùng thuật toán cho **kết luận đảo chiều** về popularity bias | **Không đo ảnh hưởng tới thứ hạng mô hình.** Không đo chi phí Big Data |
| **S5** | *Time to Split: Exploring Data Splitting Strategies for Offline Evaluation of Sequential Recommenders* (RecSys '25, pp.874–883, `10.1145/3705328.3748164`) | Split ảnh hưởng tới kết luận về mô hình | Thực nghiệm on sequential RS, nhiều split | **Thứ hạng mô hình thay đổi** theo chiến lược split | **Chỉ sequential recommenders.** Không đo bias định lượng, không đo chi phí |
| **S6** | *On the Convergent Validity of Offline Evaluation Designs for Recommender Systems* (RecSys '26, pp.410–418, `10.1145/3773078.3831818`) | Thiết kế đánh giá offline có hội tụ không | Nghiên cứu convergent validity | Nhiều thiết kế cho **kết luận không nhất quán** | **Mới (2026), 0 trích dẫn.** Không có thực nghiệm quy mô lớn kèm bias metric; không gắn Big Data platform |
| **S7** | *On Challenges of Evaluating Recommender Systems in an Offline Setting* (RecSys '23 tutorial, 2 pp, `10.1145/3604915.3609495`) | Offline eval có nhiều thách thức | Taxonomy thách thức | Liệt kê: metric ≠ mục tiêu, thiếu counterfactual, thiếu ổn định | **Mô tả định tính**, không có thực nghiệm định lượng |
| **S8** | *Take a Fresh Look at Recommender Systems from an Evaluation Standpoint* (SIGIR '23, pp.2629–2638, `10.1145/3539618.3591931`) | Cách đánh giá RS cần xem lại | Position paper + thực nghiệm | Nhiều kết luận cũ dựa trên thiết kế đánh giá không phù hợp | **Không gắn Big Data pipeline**; không đo bias chi tiết |
| **S9** | *On Inherited Popularity Bias in Cold-Start Item Recommendation* (RecSys '25, 6 pp, `10.1145/3705328.3748035`) | Bias thừa hưởng ở item cold-start | 3 dataset multimedia × 3 mô hình generative + bước giảm bias | Giảm bias item với thiệt hại nhỏ về accuracy | Chỉ **cold-start item**, không xét chiến lược split; không Big Data |
| **S10** | *Relieving Popularity Bias in Interactive Recommendation* (ACM TOIS 42(2) Art.52, 2024, `10.1145/3618107`) | Debias popularity bias trong interactive RS | RL đa dạng–mới lạ + thực nghiệm | Cải thiện fairness mà không giảm accuracy nhiều | **Giải quyết hậu quả**, không chẩn đoán nguyên nhân (cách đo); không Big Data |
| **S11** | *Quality Metrics in Recommender Systems: Do We Calculate Metrics Consistently?* (RecSys '21, pp.708–713, `10.1145/3460231.3478848`) | Cùng tên metric nhưng mỗi codebase tính khác nhau | Khảo sát implementation + tái lập | Cùng metric, cùng dataset → kết quả khác nhau giữa thư viện | **Chỉ nói metric không nhất quán**, không nối với chiến lược split; không Big Data |
| **S12** | *Exploring Data Splitting Strategies for the Evaluation of Recommendation Models* (RecSys '20, pp.681–686, `10.1145/3383313.3418479`) | 4 chiến lược split phổ biến cho kết quả khác nhau | Thực nghiệm 4 split × nhiều model | Metric thay đổi theo split; khuyến nghị split nhất quán | **Không đo popularity bias**; tiền thân của S5 nhưng thiếu bias + chi phí |
| **S13** | *Large-scale e-learning recommender system based on Spark and Hadoop* (Springer J. Big Data 6(1):2, 2019, `10.1186/s40537-019-0169-4`) | RS quy mô lớn cho e-learning | Association rules trên **Spark + HDFS + MapReduce** thật | Pipeline phân tán chạy được ở quy mô lớn | **Không đo popularity bias, không đo split sensitivity**, không so sánh nhiều chiến lược đánh giá |
| **S14** | *A novel evaluation framework for recommender systems in big data environments* (Elsevier ESWA 231:120659, 2023, `10.1016/j.eswa.2023.120659`) | Thiếu metric đánh giá phù hợp cho RS trong môi trường big data | Đề xuất metric hướng lợi nhuận/kinh doanh + khung đánh giá | Metric mới phù hợp big data hơn MAP/NDCG thuần | **Không xét ảnh hưởng của chiến lược split**; không đo popularity bias; không dùng MovieLens quy mô 25M |

> **Đã loại:** *Do Offline Metrics Predict Online Performance in Recommender Systems?* (`10.48550/arxiv.2011.07931`) — **chỉ là preprint arXiv**, không có bản tạp chí/hội nghị → không được trích theo yêu cầu giảng viên. Vai trò "offline metric ↔ online" được thay bằng S6 (convergent validity) + S11 (metric không nhất quán).

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
| S9 | ❌ | ⚠️ | ❌ | ❌ | ❌ | ❌ |
| S10 | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| S11 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| S12 | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| S13 | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| S14 | ❌ | ❌ | ⚠️ | ⚠️ | ❌ | ❌ |
| **Đề tài này** | **✅** | **✅** | **✅** | **✅** | **✅ (25M)** | **✅** |

**Đọc bảng:** không bài nào có ✅ đồng thời ở cột 1, 2, 3. S13 có cột 4 nhưng thiếu 1–2; S14 chạm cột 3/4 nhưng không đo split sensitivity và không đo popularity bias. Đây là **Critical Gap có cấu trúc** (không phải lập luận cảm tính) cho phần gap 200–250 từ.

---

## Cách dùng bảng này để viết Research Gap

1. **Known:** S1 + S2 (bias đã biết, có metric chuẩn) + S3 + S4 + S12 + S5 (split ảnh hưởng kết quả, thứ hạng đảo chiều) + S11 (metric không nhất quán) + S6 (thiếu convergent validity).
2. **Critical Gap:** chỉ vào bảng 6 cột — "chưa nghiên cứu nào đo **đồng thời** (i) đảo chiều thứ hạng, (ii) mức biến mất của popularity bias, (iii) chi phí vận hành, trên **một** pipeline Big Data cố định với **một** dataset ở quy mô ≥ 10M tương tác". Kèm bằng chứng PoC (mục 7.3 file `01`). Nêu rõ S13/S14 làm được lớp kiến trúc nhưng **không** làm lớp đo lường.
3. **Proposed:** audit framework 3 split × 4 baseline đã đăng kí (Random, MostPopular, ALS, ItemKNN) × 6+ chỉ số, MovieLens ml-25m, Spark/HDFS/MapReduce Java, MongoDB, R, Streamlit + tầng kiểm định thống kê (bootstrap, Wilcoxon, Cohen's dz).

---

## Tiêu chí sàng lọc tài liệu

| Tiêu chí | Nội dung | Áp dụng |
|---|---|---|
| **Thời gian** | 2019–2026 | S1–S14 đều thỏa |
| **Chủ đề** | offline evaluation / data leakage / popularity bias / splitting strategy / Big Data RS | S1–S14 đều thỏa |
| **Loại bài** | **chỉ bài đã publish bởi ACM / IEEE / Springer / Elsevier** — loại preprint arXiv chưa bình duyệt | 14/14 đạt |
| **Ngôn ngữ** | tiếng Anh | ✅ |
| **Truy cập** | open access hoặc qua thư viện | S14 cần thư viện |

---

## Việc còn lại

- [ ] **Tải PDF S14** (ScienceDirect chặn CAPTCHA) — anh tải tay hoặc qua thư viện HUFLIT.
- [ ] **PRISMA flow** với số bản ghi mỗi bước (Crossref + OpenAlex + Scopus) — script có sẵn `scripts/13_prisma_flow.py`, chỉ cần điền số.
- [x] **Bổ sung nhánh Big Data** — đã có S13, S14.
- [ ] **4 ảnh Zotero** minh hoạ phần gap.
- [ ] Ma trận này **đưa vào đề cương** dưới dạng bảng.
