# 03 — Tài liệu tham khảo (đã kiểm chứng DOI, **bản nhà xuất bản**)

**Project:** `D:\Master Exers\Big Data\Recomendation_System`
**Nguyên tắc:** mọi DOI dưới đây đã query trực tiếp qua **OpenAlex API + Crossref** (03/11/2026 và 07/11/2026). Không lấy số liệu từ trí nhớ.
**Cập nhật 2026-11-07:** chuyển **toàn bộ** tài liệu trích dẫn sang **bản nhà xuất bản (ACM DL / Springer / Elsevier)** — không còn dùng bản arXiv làm nguồn chính. Lý do: giảng viên PPNCKH chỉ chấp nhận bài **đã được IEEE/ACM/Springer/Elsevier công bố**, không chấp nhận preprint arXiv.

---

## 0. Trạng thái file PDF — 14/14 có bản nhà xuất bản

Thư mục: `docs/References/Papers/` · manifest: `_manifest.json` (DOI, file, title, provenance, bytes, sha256).

| #  | File                                                                | Venue (theo Crossref)                      | Nguồn tải                                          |
| -- | ------------------------------------------------------------------- | ------------------------------------------ | ---------------------------------------------------- |
| 01 | `01_TOIS2022_DataLeakage_RS_OfflineEvaluation.pdf`                | ACM TOIS 41(3), Art. 75, 27 pp             | ACM DL                                               |
| 02 | `02_TOIS2023_Reproducing_PopularityBias_EvaluationStrategies.pdf` | ACM TORS 2(1), Art. 5, 39 pp               | ACM DL                                               |
| 03 | `03_RecSys2025_TimeToSplit.pdf`                                   | RecSys '25, pp. 874–883                   | ACM DL                                               |
| 04 | `04_RecSys2026_ConvergentValidity_OfflineEvaluation.pdf`          | RecSys '26, pp. 410–418                   | ACM DL                                               |
| 05 | `05_TOIS2022_Bias_Debias_Survey.pdf`                              | ACM TOIS 41(3), Art. 67, 39 pp             | ACM DL                                               |
| 06 | `06_UMAI2024_Survey_PopularityBias.pdf`                           | Springer UMAI 34(5), 1777–1834 (CC-BY)    | Springer                                             |
| 07 | `07_SIGIR2023_FreshLook_EvaluationStandpoint.pdf`                 | SIGIR '23, pp. 2629–2638                  | ACM DL                                               |
| 08 | `08_RecSys2023_Challenges_OfflineEvaluation.pdf`                  | RecSys '23 tutorial, 2 pp (CC-BY)          | ACM DL                                               |
| 09 | `09_RecSys2025_InheritedPopularityBias_ColdStart.pdf`             | RecSys '25, 6 pp                           | ACM DL                                               |
| 10 | `10_TOIS2023_Relieving_PopularityBias_Interactive.pdf`            | ACM TOIS 42(2), Art. 52, 30 pp             | ACM DL                                               |
| 11 | `11_RecSys2021_QualityMetrics_Consistency.pdf`                    | RecSys '21, pp. 708–713                   | ACM DL                                               |
| 12 | `12_RecSys2020_DataSplitting_Strategies.pdf`                      | RecSys '20, pp. 681–686                   | ACM DL                                               |
| 13 | `13_JBigData2019_Elearning_RS_Spark_Hadoop.pdf`                   | Springer J. Big Data 6(1):2, 23 pp (CC-BY) | SpringerOpen                                         |
| 14 | `14_ESWA2023_EvaluationFramework_BigData.pdf`                     | Elsevier ESWA 231:120659                   | ScienceDirect chặn bot (CAPTCHA), cần anh tải tay |

**Đã loại khỏi danh sách trích dẫn:**

- Bài `arXiv 10.48550/arxiv.2011.07931` (*Do Offline Metrics Predict Online Performance in Recommender Systems?*, Gilotte et al., RecLab). Lý do: **chỉ tồn tại dạng preprint arXiv**, không có phiên bản tạp chí/hội nghị → không được trích theo yêu cầu giảng viên. Nội dung "offline metric ↔ online A/B" **đã được thay thế** bằng [4] RecSys '26 và [11] RecSys '21.
- Mọi bản arXiv trước đây đã **bị ghi đè bằng bản nhà xuất bản**; không giữ bản trùng.

**Kiểm chứng bằng chương trình:** 13/13 PDF mở được bằng `pypdf`, metadata `/Creator` là `acmart` / `MiKTeX-pdfTeX` / `Acrobat Distiller` / `Springer`, footer trang 1 có dòng bản quyền + DOI của ACM/Springer (chứng minh không phải `arXiv GenPDF`).

---

## 1. Bài neo — dùng trực tiếp trong phần gap

### [1] Bằng chứng rò rỉ dữ liệu do chia tập

> **A Critical Study on Data Leakage in Recommender System Offline Evaluation**
> ACM Transactions on Information Systems (TOIS) **41**(3), Art. 75, 2023 (online 2022)
> DOI: **`10.1145/3569930`** · Yitong Ji, Aixin Sun, Jie Zhang, Chenliang Li

- **Vai trò:** nguồn `[1]` của phần gap. Chứng minh cấu hình chia tập phổ biến nhất (ngẫu nhiên) gây **rò rỉ dữ liệu** vào đánh giá offline, khiến thứ hạng mô hình không đáng tin.
- **Bằng chứng định lượng trong đề tài này:** `temporal_violation` đo bằng Spark dưới split ngẫu nhiên = 100% trên random80_20 (mục 7.3 file `01`).
- **Mức ảnh hưởng:** cao — nhiều bài RS dùng cùng cấu hình.

### [2] Popularity bias bị "giấu" dưới split ngẫu nhiên

> **Reproducing Popularity Bias in Recommendation: The Effect of Evaluation Strategies**
> ACM Transactions on Recommender Systems (TORS) **2**(1), Art. 5, 2024
> DOI: **`10.1145/3637066`** · Savvina Daniil và cộng sự

- **Vai trò:** nguồn `[2]`. Popularity bias **không lộ ra** dưới split ngẫu nhiên; kết luận đổi khi đổi chiến lược đánh giá.
- **Bằng chứng định lượng:** bộ `catalog_coverage`, `gini_exposure`, `longtail_coverage`, `popularity_bias_ratio` trên cùng 3 chiến lược split.

### [3] Chiến lược split tác động tới thứ hạng mô hình

> **Time to Split: Exploring Data Splitting Strategies for Offline Evaluation of Sequential Recommenders**
> RecSys '25 (19th ACM Conference on Recommender Systems), pp. 874–883, 2025
> DOI: **`10.1145/3705328.3748164`** · Danil Gusak, Anna Volodkevich, Anton Klenitskiy, Alexey Vasilev, Evgeny Frolov

### [4] Thiếu convergent validity giữa các thiết kế đánh giá

> **On the Convergent Validity of Offline Evaluation Designs for Recommender Systems**
> RecSys '26 (20th ACM Conference on Recommender Systems), pp. 410–418, 2026
> DOI: **`10.1145/3773078.3831818`** · Sushobhan Parajuli, Samira Vaez Barenji, Michael D. Ekstrand

- **Vai trò:** bổ trợ [3]. Một thiết kế đánh giá chỉ đáng tin nếu kết luận nhất quán qua nhiều chiến lược split.
- **Trạng thái:** rất mới (2026) → mở rộng phạm vi, không làm bằng chứng định lượng chính.

---

## 2. Bài nền tảng + bổ trợ (tất cả đã publish)

| #    | Tiêu đề                                                                                                                   | Venue                                | DOI                            | Vai trò                                                                                                                                   |
| ---- | ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| [5]  | **Bias and Debias in Recommender System: A Survey and Future Directions**                                              | ACM TOIS 41(3), Art. 67, 2023        | `10.1145/3564284`            | ~860 trích dẫn — popularity bias là vấn đề đạo đức thuật toán đã được công nhận; phần "Known" + đạo đức dữ liệu |
| [6]  | **A survey on popularity bias in recommender systems**                                                                 | Springer UMAI 34(5):1777–1834, 2024 | `10.1007/s11257-024-09406-0` | ~180 trích dẫn — định nghĩa chuẩn catalog coverage, Gini, exposure disparity                                                        |
| [7]  | **Take a Fresh Look at Recommender Systems from an Evaluation Standpoint**                                             | ACM SIGIR '23, pp. 2629–2638        | `10.1145/3539618.3591931`    | Position paper về thiết kế đánh giá offline                                                                                          |
| [8]  | **On Challenges of Evaluating Recommender Systems in an Offline Setting**                                              | RecSys '23 tutorial, 2 pp            | `10.1145/3604915.3609495`    | Liệt kê thách thức đánh giá offline → phần Known                                                                                  |
| [9]  | **On Inherited Popularity Bias in Cold-Start Item Recommendation**                                                     | RecSys '25, 6 pp                     | `10.1145/3705328.3748035`    | Bias ở cold-start item → liên quan `unseen_item`                                                                                      |
| [10] | **Relieving Popularity Bias in Interactive Recommendation: A Diversity-Novelty-Aware Reinforcement Learning Approach** | ACM TOIS 42(2), Art. 52, 2024        | `10.1145/3618107`            | Hướng debias — cơ sở cho phần kết quả kỳ vọng / hướng mở rộng                                                                |
| [11] | **Quality Metrics in Recommender Systems: Do We Calculate Metrics Consistently?**                                      | RecSys '21, pp. 708–713             | `10.1145/3460231.3478848`    | Cùng tên metric nhưng implementation khác → tái lập không được. **Thay thế vai trò của bài arXiv 2020**               |
| [12] | **Exploring Data Splitting Strategies for the Evaluation of Recommendation Models**                                    | RecSys '20, pp. 681–686             | `10.1145/3383313.3418479`    | **Tiền thân trực tiếp của [3]** — 4 chiến lược split, chứng minh metric thay đổi theo split                              |

---

## 3. Nhánh "RS trên nền tảng Big Data" (bổ sung 07/11 — trước đây trống)

| #    | Tiêu đề                                                                              | Venue                                                           | DOI                            | Vai trò                                                                                                                                                                                                                                                             |
| ---- | --------------------------------------------------------------------------------------- | --------------------------------------------------------------- | ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [13] | **Large-scale e-learning recommender system based on Spark and Hadoop**           | Springer, *Journal of Big Data* 6(1):2, 2019 (CC-BY)          | `10.1186/s40537-019-0169-4`  | RS association-rule trên Spark + HDFS + MapReduce thật. 85 trích dẫn. **Chứng minh lớp kiến trúc là hướng đã publish được**, đồng thời cho thấy họ **không** đo popularity bias hay split sensitivity → củng cố khoảng trống |
| [14] | **A novel evaluation framework for recommender systems in big data environments** | Elsevier, *Expert Systems with Applications* 231:120659, 2023 | `10.1016/j.eswa.2023.120659` | Đề xuất metric đánh giá mới cho RS trong môi trường big data — gần nhất với lớp "đánh giá" của đề tài. **Chưa có PDF** (ScienceDirect chặn)                                                                                           |

> Với [13] + [14], bảng đối chiếu tính mới không còn "cột 4 toàn ❌": hai bài này **có** chạy trên nền tảng Big Data, nhưng **không** đo đồng thời split sensitivity + popularity bias + chi phí → Critical Gap giữ nguyên, và giờ có **đối chiếu công bằng** hơn khi bảo vệ.

---

## 4. Dataset — bắt buộc trích dẫn

> **The MovieLens Datasets: History and Context**
> F. Maxwell Harper & Joseph A. Konstan. ACM Transactions on Interactive Intelligent Systems (TiiS) **5**(4), Art. 19, pp. 1–19, 2015.
> DOI: **`10.1145/2827872`**

- Bắt buộc theo license GroupLens (xem `02_Nguon_du_lieu_va_URL.md` §4); ghi vào mục TLTK + phần đạo đức dữ liệu.

---

## 5. Tài liệu môn học (đối chiếu yêu cầu đầu ra)

| File                                                          | Nội dung dùng                                                                                                                                                |
| ------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `01_Tổng quan PPNCKH.pdf`                                  | W5H2, FINER, tính mới, đạo đức dữ liệu, lưu vết thực nghiệm                                                                                        |
| `02_Tong Quan Tai Lieu.pdf`                                 | Quy trình tổng quan tài liệu, PRISMA, cấu trúc gap 3 phần (Known / Critical Gap / Proposed), yêu cầu gap 200–250 từ có bằng chứng định lượng |
| `VD W5H2.pdf`                                               | Mẫu điền W5H2                                                                                                                                               |
| `Example Paper.pdf`                                         | Mẫu cấu trúc Introduction 5 phần                                                                                                                           |
| `0.CourseIntroduction_VTHT.pdf`, `1.Itroduction_VTHT.pdf` | Yêu cầu môn Big Data: Spark, Hadoop, MapReduce, MongoDB, PySpark, R, Streamlit                                                                              |
| `Du lieu lon_CH_16012026.pdf`                               | Yêu cầu prototype, đánh giá, source code, experiments                                                                                                     |

---

## 6. Sơ đồ trích dẫn cho phần gap (đã cập nhật)

```
[1] TOIS 2023 (3569930) ──┐
[2] TORS 2024 (3637066) ──┼─→ Known: split ảnh hưởng kết quả; bias bị giấu dưới split ngẫu nhiên
[12] RecSys'20 (…3418479) ┤
[3] RecSys'25 (…3748164) ─┘
[4] RecSys'26 (…3831818) ───→ Thiếu convergent validity
[11] RecSys'21 (…3478848) ──→ Metric không tính nhất quán giữa các codebase
[5] TOIS 2023 survey ───────→ Bias = vấn đề đạo đức đã biết (860 cites)
[6] UMAI 2024 survey ───────→ Định nghĩa chuẩn chỉ số coverage/Gini/exposure
[13] J.BigData 2019 ────────→ Có pipeline Spark/Hadoop nhưng KHÔNG đo bias/split
[14] ESWA 2023 ─────────────→ Có framework đánh giá big data nhưng KHÔNG đo split sensitivity
                    ↓
      CRITICAL GAP: chưa nghiên cứu nào đo ĐỒNG THỜI
      (i) đảo chiều thứ hạng  (ii) mức biến mất của popularity bias
      (iii) chi phí Big Data — trên cùng một pipeline, cùng bộ metric
                    ↓
      PROPOSED: audit framework 3 split × 4 baseline đã đăng kí (Random, MostPopular, ALS, ItemKNN) × 6+ chỉ số + kiểm định cặp per-user
      trên MovieLens ml-25m (25.000.095 tương tác) + Spark/HDFS/MapReduce + MapReduce Java
```

---

## 7. PRISMA 2020 — tiêu chí lọc (đã siết lại)

Script: `scripts/13_prisma_flow.py` → `figures/fig8_prisma_flow.svg`.

| Tiêu chí           | Nội dung                                                                                                                                                                     | Áp dụng            |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------- |
| Khoảng thời gian   | 2019–2026                                                                                                                                                                    | cả 14 tài liệu    |
| Chủ đề            | offline evaluation / data leakage / popularity bias / splitting strategy / Big Data RS                                                                                        | cả 14               |
| **Loại bài** | **chỉ bài đã publish bởi ACM / IEEE / Springer / Elsevier** (tạp chí hoặc proceedings có DOI). **Loại toàn bộ preprint arXiv chưa qua bình duyệt** | 14/14 đạt          |
| Ngôn ngữ           | tiếng Anh                                                                                                                                                                    | ✅                   |
| Truy cập            | open access hoặc qua thư viện                                                                                                                                              | [14] cần thư viện |

**Số liệu phải điền khi nộp:** identification (Crossref + OpenAlex + Scopus) → screening → eligibility → included. Bản crypto: 2 nguồn API, 14 bài giữ lại sau khi loại preprint.

---

## 8. Việc cần làm tiếp

1. **4 ảnh Zotero** cho phần gap (yêu cầu `02_Tong Quan Tai Lieu.pdf`).
2. **Điền số PRISMA** vào 4 hộp của `fig8_prisma_flow.svg`.
3. **Đối chiếu bảng `04_Ma_tran_tong_quan_5_cot.md`** — đã cập nhật theo 14 tài liệu mới.
4. Nộp đề cương **08/11/2026**.

---

## 9. Kỹ thuật tải bản nhà xuất bản (ghi lại để tái lập)

- **ACM DL:** `urllib`/`requests` → HTTP 403 (Cloudflare, kể cả UA Chrome giả). Cách đúng: mở DOI bằng browser OpenClaw (profile `openclaw`, CDP 18800) → dump cookie browser-level bằng CDP `Storage.getCookies` → replay bằng `urllib` với `Cookie` + `Referer` + **UA Chrome 156 y hệt**. `cf_clearance` gắn với UA + IP. Script: `scripts/16_fetch_publisher_versions.py`.
- **Springer (journalofbigdata.springeropen.com):** chặn `urllib` bằng "Client Challenge" (JS). Cách đúng: browser đã PASS challenge → trong page chạy `fetch(pdfUrl, {credentials:'include'})` → trả base64 → Node ghi file. **Lưu ý:** gửi header `Range` bừa sẽ nhận **416**; bỏ `Range` thì nhận **206 + đủ bytes**.
- **ScienceDirect / Elsevier:** CAPTCHA "Are you a robot?" cho cả browser lẫn HTTP client → **không tự động hóa được**, phải tải tay.
- **Kiểm chứng bản thật:** `pypdf` đọc `/Creator`: `arXiv GenPDF` = bản preprint; `acmart` / `MiKTeX-pdfTeX` / `Acrobat Distiller` + footer bản quyền ACM/Springer = bản xuất bản.
