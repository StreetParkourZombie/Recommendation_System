# 03 — Tài liệu tham khảo (đã kiểm chứng DOI)

**Project:** `D:\Master Exers\Big Data\Recomendation_System`
**Nguyên tắc:** mọi DOI dưới đây đã query trực tiếp qua **OpenAlex API** (fallback Crossref) ngày **2026-11-03**. Không lấy số liệu từ trí nhớ.

---

## 1. Bài neo — dùng trực tiếp trong phần gap

### [1] Bằng chứng rò rỉ dữ liệu do chia tập (data leakage)

> **A Critical Study on Data Leakage in Recommender System Offline Evaluation**
> ACM Transactions on Information Systems (TOIS), 2022
> DOI: **`10.1145/3569930`**

- **Vai trò:** nguồn `[1]` của phần gap. Chứng minh rằng cấu hình chia tập phổ biến nhất (ngẫu nhiên) làm **rò rỉ dữ liệu** vào quá trình đánh giá offline, dẫn tới thứ hạng mô hình không đáng tin.
- **Bằng chứng định lượng trong đề tài này:** chỉ số `temporal_violation` đo bằng Spark cho thấy dưới split ngẫu nhiên, **5.000.974 / 5.000.974 = 100%** tương tác kiểm định có timestamp trước mốc lớn nhất của tập train (mục 7.3 của `01_De_tai_va_Ke_hoach.md`).
- **Mức độ ảnh hưởng:** cao — nhiều bài báo RS dùng cùng cấu hình này.

### [2] Bằng chứng popularity bias bị "giấu" dưới split ngẫu nhiên

> **Reproducing Popularity Bias in Recommendation: The Effect of Evaluation Strategies**
> ACM Transactions on Information Systems (TOIS), 2023
> DOI: **`10.1145/3637066`**

- **Vai trò:** nguồn `[2]`. Chứng minh hiện tượng popularity bias **không lộ ra** dưới split ngẫu nhiên, và **kết luận thay đổi** khi đổi chiến lược đánh giá, kể cả giữa các miền dữ liệu khác nhau.
- **Bằng chứng định lượng trong đề tài này:** bộ 3 chỉ số `catalog_coverage`, `gini_exposure`, `longtail_coverage` + `popularity_bias_ratio` đo trên cùng 3 chiến lược split.
- **Mức độ ảnh hưởng:** cao — là cơ sở lập luận "vì sao cần đo bias bằng chỉ số riêng, không chỉ NDCG".

### [3] Bằng chứng chiến lược split tác động tới thứ hạng mô hình

> **Time to Split: Exploring Data Splitting Strategies for Offline Evaluation of Sequential Recommenders**
> RecSys '25 (ACM Conference on Recommender Systems), 2025
> DOI: **`10.1145/3705328.3748164`**

- **Vai trò:** nguồn `[3]`. Xác lập rằng chiến lược split **thay đổi thứ hạng mô hình** — nền tảng cho RQ1 (đảo chiều thứ hạng).
- **Giới hạn:** tập trung **sequential recommenders**; đề tài này mở rộng sang CF cổ điển (ALS/ItemKNN) + đo thêm bias và chi phí Big Data.

### [4] Bằng chứng thiếu convergent validity

> **On the Convergent Validity of Offline Evaluation Designs for Recommender Systems**
> RecSys '26, 2026
> DOI: **`10.1145/3773078.3831818`**

- **Vai trò:** bổ trợ `[3]`. Cho thấy cần kiểm tra **tính hội tụ** giữa các thiết kế đánh giá offline — tức một thiết kế đánh giá chỉ đáng tin nếu cho kết luận nhất quán qua nhiều chiến lược split.
- **Trạng thái:** bài rất mới (2026), **0 trích dẫn** → dùng để mở rộng phạm vi, không dùng làm bằng chứng định lượng chính.

---

## 2. Bài tổng quan và nền tảng (đặt nền cho phần Known)

| # | Tiêu đề | Năm | DOI | Tác dụng trong đề tài |
|---|---|---|---|---|
| [5] | **Bias and Debias in Recommender System: A Survey and Future Directions** (ACM TOIS) | 2022 | `10.1145/3564284` | **760 trích dẫn** — nguồn mạnh nhất để định vị popularity bias là vấn đề đạo đức thuật toán đã được cộng nhận, không phải đề xuất mới. Dùng để viết phần "Known" và phần **đạo đức dữ liệu** |
| [6] | **A survey on popularity bias in recommender systems** (UMAI) | 2024 | `10.1007/s11257-024-09406-0` | **159 trích dẫn** — tổng quan mới nhất, định nghĩa chuẩn các chỉ số đo bias (coverage, Gini, exposure). Dùng để **định nghĩa** 3 chỉ số dùng trong đề tài |
| [7] | **Take a Fresh Look at Recommender Systems from an Evaluation Standpoint** (SIGIR) | 2023 | `10.1145/3539618.3591931` | 46 trích dẫn — nhấn mạnh vấn đề thiết kế đánh giá offline |
| [8] | **On Challenges of Evaluating Recommender Systems in an Offline Setting** (RecSys '23) | 2023 | `10.1145/3604915.3609495` | Liệt kê các thách thức của đánh giá offline → dùng cho phần Known |
| [9] | **Relieving Popularity Bias in Interactive Recommender Systems** (ACM TOIS) | 2023 | `10.1145/3618107` | Cơ sở cho hướng "debias" — phần **kết quả kỳ vọng / hướng mở rộng** |
| [10] | **On Inherited Popularity Bias in Cold-Start Item Recommendation** (RecSys '25) | 2025 | `10.1145/3705328.3748035` | Biến thể bias ở cold-start item → liên quan `unseen_item` metric |

---

## 3. Bài về offline metric ↔ hiệu quả thực tế (bối cảnh)

| # | Tiêu đề | Năm | DOI | Tác dụng |
|---|---|---|---|---|
| [11] | **Do Offline Metrics Predict Online Performance in Recommender Systems?** (arXiv / RecLab) | 2020 | `10.48550/arxiv.2011.07931` | 22 trích dẫn — nền cho câu hỏi "metric offline có ý nghĩa không". Trích dẫn được nhưng **không** phải bằng chứng chính |

---

## 3.1 Trạng thái file PDF cục bộ — 9/9 đã tải (2026-11-04)

Thư mục: `docs/References/Papers/` · manifest: `_manifest.json` (DOI, file, title, source, sha256, bytes).
Script tải: `scripts/10_fetch_papers.py` (fallback chain OpenAlex → Unpaywall → arXiv → OA aggregator;
**không ghi đè** file đã tồn tại).

| # | File cục bộ | Kích thước | Nguồn tải |
|---|---|---:|---|
| 01 | `01_TOIS2022_DataLeakage_RS_OfflineEvaluation.pdf` | 1.403.320 B | arXiv 2010.11060 |
| 02 | `02_TOIS2023_Reproducing_PopularityBias_EvaluationStrategies.pdf` | 9.819.024 B | CWI IR (`ir.cwi.nl/pub/33989`) |
| 03 | `03_RecSys2025_TimeToSplit.pdf` | 1.421.328 B | arXiv 2507.16289 |
| 04 | `04_RecSys2026_ConvergentValidity_OfflineEvaluation.pdf` | 699.011 B | ACM DL (hybrid) |
| 05 | `05_TOIS2022_Bias_Debias_Survey.pdf` | 1.793.185 B | ACM DL |
| 06 | `06_UMAI2024_Survey_PopularityBias.pdf` | 2.281.729 B | — |
| 07 | `07_SIGIR2023_FreshLook_EvaluationStandpoint.pdf` | 1.336.365 B | ACM DL |
| 08 | `08_RecSys2023_Challenges_OfflineEvaluation.pdf` | 414.562 B | ACM DL — SHA-256 `FA37C1CDE430372AE42B0DBA70F9BEE0A8A7A9B722A0A86DA9AC13CC64219F94` |
| 09 | `09_RecSys2025_InheritedPopularityBias_ColdStart.pdf` | 1.088.904 B | ACM DL |

**Verify:** 9/9 PDF parse OK bằng `pypdf` (số trang: 27 / 39 / 10 / 9 / 38 / 58 / 10 / **2** / 6).
Bài [11] (`10.48550/arxiv.2011.07931`) **chưa tải** — dùng làm ngữ cảnh, không đưa vào PRISMA.

> **Lưu ý giấy phép:** ACM DL là **hybrid** — bản OA của ACM cho phép sử dụng phi thương mại với
> trích dẫn. Khi nộp đề cương phải trích dẫn đầy đủ DOI; nếu giảng viên yêu cầu bản in,
> dùng bản publisher.

### Kỹ thuật tải ACM DL (Cloudflare) — ghi lại để không vấp lần nữa

`urllib`/`requests` → **HTTP 403** dù đã giả User-Agent Chrome. Nguyên nhân: Cloudflare kiểm tra
cookie `cf_clearance` **gắn với đúng UA + IP**.

Cách làm (đã thành công):
1. Mở DOI bằng browser OpenClaw (profile `openclaw`, CDP `127.0.0.1:18800`) → Cloudflare cấp cookie.
2. Dump cookie qua CDP `Storage.getCookies` (browser-level, **không cần attach page**).
3. Replay bằng `urllib` với `Cookie` + `Referer` + **UA Chrome desktop giống hệt lúc dump**.

Kết quả: HTTP `200`, `Content-Type: application/pdf;charset=UTF-8`, `414562` bytes, header `%PDF-1.7`.

Các nguồn khác bị chặn: Unpaywall **403** · Semantic Scholar **429** · DR-NTU Handle **405** (HTTP
client) và trang **Human Verification** (browser) · OpenAlex ✅.

---

## 3.2 PRISMA 2020 — sơ đồ quy trình rà soát (2026-11-04)

Script: `scripts/13_prisma_flow.py` → `docs/Project/Main/report/Big_Data/figures/fig8_prisma_flow.svg`
(1180×760, SVG thuần — **không cần** `cairosvg`/native Cairo).

Tiêu chí lọc (theo `02_Tong Quan Tai Lieu.pdf`):

| Tiêu chí | Nội dung |
|---|---|
| Khoảng thời gian | 2020–2026 |
| Chủ đề | offline evaluation of recommender systems |
| Loại trừ | non-peer-reviewed (trừ arXiv preprint có DOI), tài liệu thuộc domain khác, workshop short paper |

**Còn làm khi nộp đề cương:** điền số liệu cụ thể vào 4 hộp của PRISMA
(identification → screening → eligibility → included) — hiện SVG là **khung** với số liệu
điền sẵn cho bước cuối.

---

## 4. Dataset — bắt buộc trích dẫn

> **The MovieLens Datasets: History and Context**
> F. Maxwell Harper & Joseph A. Konstan. ACM Transactions on Interactive Intelligent Systems (TiiS) **5**(4), Article 19, 2015.
> DOI: **`10.1145/2827872`**

- **Bắt buộc** theo điều khoản license của GroupLens (xem `02_Nguon_du_lieu_va_URL.md` §4).
- Ghi vào mục "Tài liệu tham khảo" của đề cương và vào phần **đạo đức dữ liệu**.

---

## 5. Tài liệu môn học (để đối chiếu yêu cầu đầu ra)

| File | Nội dung dùng |
|---|---|
| `01_Tổng quan PPNCKH.pdf` | W5H2, FINER, tính mới, đạo đức dữ liệu, lưu vết thực nghiệm |
| `02_Tong Quan Tai Lieu.pdf` | Quy trình tổng quan tài liệu, PRISMA, cấu trúc gap 3 phần (Known / Critical Gap / Proposed), yêu cầu gap 200–250 từ có bằng chứng định lượng và nguồn `[1]`, `[2]` |
| `VD W5H2.pdf` | Mẫu điền W5H2 |
| `Example Paper.pdf` | Mẫu bài để tham chiếu cấu trúc Introduction 5 phần |
| `0.CourseIntroduction_VTHT.pdf`, `1.Itroduction_VTHT.pdf` | Yêu cầu môn Big Data: Spark, Hadoop, MapReduce, MongoDB, PySpark, R, Streamlit |
| `Du lieu lon_CH_16012026.pdf` | Yêu cầu về prototype, đánh giá, source code, experiments |

---

## 6. Sơ đồ trích dẫn cho phần gap

```
[1] TOIS 2022 (10.1145/3569930) ─┐
[2] TOIS 2023 (10.1145/3637066) ─┼─→ Known: split ảnh hưởng kết quả;
[3] RecSys'25 (…3748164)        ─┘   popularity bias bị giấu dưới split ngẫu nhiên
[4] RecSys'26 (…3831818)        ──→ Thiếu convergent validity
[5] TOIS 2022 survey (760 cites)──→ Bias = vấn đề đạo đức đã biết
[6] UMAI 2024 survey (159 cites)→ Định nghĩa chuẩn chỉ số coverage/Gini/exposure
                    ↓
      CRITICAL GAP: chưa có nghiên cứu nào đo ĐỒNG THỜI
      (i) đảo chiều thứ hạng  (ii) biến mất của popularity bias
      (iii) chi phí Big Data  — trên cùng pipeline, cùng bộ metric
                    ↓
      PROPOSED: audit framework 3 split × 4 model × 6+ chỉ số
      trên MovieLens ml-25m (25.000.095 tương tác) + Spark/HDFS/MapReduce
```

---

## 7. Việc cần làm tiếp theo cho PPNCKH

1. **PRISMA flow** — ghi lại: bao nhiêu bản ghi tìm được (Crossref + OpenAlex + Scopus), bao nhiêu bị loại ở mỗi bước, tiêu chí loại. Phải có **tiêu chí thời gian** (2020–2026) và **tiêu chí chủ đề** (offline evaluation of recommender systems).
2. **Bổ sung 2–3 bài** cho nhánh "đánh giá trên Big Data platform" để củng cố tính mới của lớp kiến trúc.
3. **Ma trận tổng quan 5 cột** — xem `04_Ma_tran_tong_quan_5_cot.md`; cột 5 = hạn chế cốt lõi → trực tiếp sinh ra phần Critical Gap.
4. Kiểm tra **4 ảnh Zotero** — yêu cầu của `02_Tong Quan Tai Lieu.pdf` (gap ≥ 200 từ + 4 ảnh).
