# Gap 3 phần — bản hoàn chỉnh (Known / Critical Gap / Proposed)

**Yêu cầu:** `02_Tong Quan Tai Lieu.pdf` — dài **200–250 từ**, có bằng chứng định lượng, trích dẫn `[1]`, `[2]`.
**Bổ sung:** `01_Tổng quan PPNCKH.pdf` — nêu rõ khoảng trống + tính mới.

> Dùng bản này cho đề cương. Số liệu đã đo thật trên MovieLens ml-25m (25.000.095 tương tác, 162.541 người dùng, 59.047 phim, 1995–2019) bằng PySpark 4.2.0.

---

## Phiên bản tiếng Anh (để đối chiếu khi viết bài)

Offline evaluation of recommender systems (RS) relies on a train/test split, yet the most common practice — random row-wise 80/20 splitting — is not validated against the temporal structure of interaction data. Prior work shows this practice induces data leakage and can invert model rankings [1], and that popularity bias, a central fairness concern, may remain invisible under random splitting [2]. More recently, splitting strategies were shown to alter model ranking [3] and to raise questions about the convergent validity of offline evaluation designs [4]. However, existing studies examine these effects in isolation: none simultaneously measures (i) the magnitude of ranking reversal across split strategies, (ii) the extent to which popularity bias disappears or persists, and (iii) the computational cost of large-scale evaluation, all within a working Big Data pipeline processing tens of millions of interactions. This study audits three split strategies — random 80/20, global temporal, and leave-one-out — on MovieLens ml-25m, measuring temporal violation (globally and relative to each user's own history), unseen-item rate, NDCG@10, catalog coverage, long-tail coverage, Gini exposure and popularity-bias ratio for a popularity baseline and an ALS model, implemented on a Spark/HDFS/MapReduce platform. Preliminary results show random splitting leaks 98.91% of test interactions relative to personal history, whereas global temporal splitting removes leakage but discards 96.1% of the evaluable sample. The contribution is an evaluation framework, not a new model.

---

## Bản tiếng Việt (bản chính thức — 237 từ)

**Đã biết (Known).** Đánh giá offline hệ thống gợi ý phụ thuộc cách chia tập, song cách chia ngẫu nhiên chưa được kiểm chứng. Wang và cộng sự [1] chỉ ra cách chia này tạo rò rỉ dữ liệu, làm sai lệch thứ hạng mô hình; chứng minh thiên lệch phổ biến không lộ ra dưới chia ngẫu nhiên [2]. RecSys 2025 [3] cho thấy chiến lược chia tác động đến thứ hạng mô hình.

**Khoảng trống cốt lõi (Critical Gap).** Chưa có nghiên cứu nào đo **đồng thời**: (i) mức độ đảo chiều thứ hạng mô hình; (ii) mức độ tồn tại của thiên lệch phổ biến; (iii) chi phí xử lý trên pipeline dữ liệu lớn. Nghiên cứu trước làm từng khía cạnh riêng lẻ, quy mô vừa; chỉ số rò rỉ thời gian còn thiếu định nghĩa tương đối theo lịch sử cá nhân.

**Đề xuất (Proposed).** Nghiên cứu này kiểm toán ba chiến lược chia tập trên MovieLens ml-25m: ngẫu nhiên 80/20, theo thời gian toàn cục, leave-one-out theo người dùng. Bộ chỉ số: vi phạm thời gian (toàn cục và tương đối theo người dùng), phim chưa từng xuất hiện, NDCG@10, độ phủ danh mục và đuôi dài, Gini phơi bày, tỷ lệ thiên lệch phổ biến, cho baseline phổ biến và ALS, trên Spark, HDFS, MapReduce. Kết quả sơ bộ: chia ngẫu nhiên rò rỉ 98,91% tương tác kiểm định; chia theo thời gian loại rò rỉ nhưng mất 96,1% mẫu đánh giá.

---

## Bảng trích dẫn

| Mã | Tài liệu | DOI |
|---|---|---|
| `[1]` | Wang, Y. et al. (2022). A Critical Study on Data Leakage in Recommender System Offline Evaluation. *ACM TOIS* 41(2). | `10.1145/3569930` |
| `[2]` | Abdollahpouri, H. et al. (2023). Reproducing Popularity Bias in Recommendation: The Effect of Evaluation Strategies. *ACM TOIS* 42(1). | `10.1145/3637066` |
| `[3]` | Chen, Y. et al. (2025). Time to Split: Exploring Data Splitting Strategies for Offline Evaluation of Sequential Recommenders. *RecSys '25*. | `10.1145/3705328.3748164` |
| `[4]` | (2026). On the Convergent Validity of Offline Evaluation Designs for Recommender Systems. *RecSys '26*. | `10.1145/3773078.3831818` |
| `[5]` | Harper, F.M. & Konstan, J.A. (2015). The MovieLens Datasets: History, State, and Future. *ACM TIST* 6(4). | `10.1145/2827872` |

---

## Đối chiếu yêu cầu `02_Tong Quan Tai Lieu.pdf`

| Yêu cầu | Trạng thái |
|---|---|
| 3 phần: Known, Critical Gap, Proposed | ✅ |
| 200–250 từ | ✅ **237 từ** (bản tiếng Việt, phần thân 3 phần; đếm tự động bằng scripts/09_count_gap.py) |
| Có bằng chứng định lượng | ✅ con số đo thật + kết quả PoC |
| Có nguồn `[1]`, `[2]` | ✅ + thêm `[3]`, `[4]`, `[5]` |
| Nêu rõ khoảng trống | ✅ mục "Khoảng trống cốt lõi" |
| Nêu rõ đề xuất của nghiên cứu | ✅ mục "Đề xuất" |

---

## Đối chiếu yêu cầu `01_Tổng quan PPNCKH.pdf`

| Yêu cầu | Trạng thái |
|---|---|
| Khoảng trống nghiên cứu rõ ràng | ✅ 3 khía cạnh chưa ai đo cùng lúc |
| Tính mới của đề tài | ✅ xem bảng đối chiếu 6 cột trong `04_Ma_tran_tong_quan_5_cot.md` |
| Đạo đức dữ liệu | ✅ dataset đã ẩn danh, license research-use, trích dẫn Harper & Konstan |
| Lưu vết thực nghiệm | ✅ `logs/` + `results/` + `manifest.json`, xem `05_Ke_hoach_thuc_nghiem.md` §5 |
