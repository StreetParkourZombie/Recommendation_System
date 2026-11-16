# Kế hoạch tạo slide thuyết trình PPNCKH — bảo vệ đề cương

**Project:** `D:\Master Exers\Big Data\Recomendation_System`
**Cập nhật:** 2026-11-16
**Mục đích:** DỰ PHÒNG — giảng viên PPNCKH đã nói rõ môn thiên về **soạn tài liệu / lý thuyết / trình bày khoa học**, không bắt buộc chạy hết pipeline. Slide phải dựng được **kể cả khi thực nghiệm bị dừng ở trạng thái hiện tại** (đã có PoC + notebook flow 6/6 gate PASS).

**Căn cứ:**
- [HD Chuan bi thuyet trinh.pdf](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/docs/References/HUFLIT/Research_Methods/HD%20Chuan%20bi%20thuyet%20trinh.pdf) (TS. Trần Minh Thái — 12 slide mẫu, tỷ trọng C1 20% / C2 30% / C3 45% / KL 5% + Q&A)
- 14 paper Q1/CORE A*/A (docs/References/Papers/ + `_manifest.json`)
- Đề tài, W5H2, FINER, gap 3 phần, SLI — `docs/Project/Plans/Research/`
- Kết quả đo thật (PoC 2026-11-04 + notebook 04–09 2026-11-15) — dùng làm **kết quả sơ bộ chứng minh khả thi**, không phải deliverable chính

---

## 1. Định dạng đầu ra

| Hạng mục | Quyết định |
|---|---|
| Số slide | **14** (trong khoảng 10–20 cho phép) |
| Công cụ | `python-pptx` — script sinh slide (`scripts/generate_slides.py`) + dùng 1 slide mẫu của file HD làm reference layout (Title and Content / Two Content, footer `x / 15`) |
| Cỡ chữ | **≥ 24pt** toàn bộ body; title 32–40pt; bảng tối thiểu 20pt (ngoại lệ duy nhất, do bảng số) |
| Nền | Sáng (trắng / trắng ngà), một accent màu; không animation |
| Ngôn ngữ | Tiếng Việt; thuật ngữ kỹ thuật giữ tiếng Anh (SLI, NDCG@10, coverage…) |
| Trực quan | Sơ đồ + bảng thay đoạn văn; mỗi slide ≤ 2 khối thông tin |
| Speaker notes | Mỗi slide có notes (script nói + dự phòng Q&A), dù file mẫu không yêu cầu — vì người trình bày cần |

---

## 2. Cấu trúc 15 slide — khớp tỷ trọng HD

| # | Slide | Phần (tỷ trọng) | Nguồn nội dung |
|---|---|---|---|
| 1 | Tiêu đề đề tài + sinh viên + GVHD | — | `01_De_tai_va_Ke_hoach.md` §1 |
| 2 | Bố cục trình bày (C1 20% · C2 30% · C3 45% · KL 5%) | — | copy cấu trúc HD slide 2 |
| 3 | **DIKW áp dụng vào đề tài** | C1 20% | mục §4 dưới đây |
| 4 | **Phương pháp tư duy** (phân tích – tổng hợp – quy nạp – phản chứng) | C1 20% | mục §5 |
| 5 | **W5H2** — bài toán thực tiễn | C2 30% | `01_De_tai…` §4 |
| 6 | **Quản lý tài liệu — 14 bài đã thu thập + kiểm tra độ uy tín** (chụp trang PDF + SCImago/CORE) | C2 30% | `docs/References/Papers/_manifest.json` |
| 7 | **Ma trận tổng hợp tài liệu** (5 bài Q1/CORE A*) + khoảng trống | C2 30% | `04_Ma_tran_tong_quan_5_cot.md`, `07_Gap_3_phan…` |
| 8 | **Tiêu đề + GO/SO + RQ** (gắn kết) | C3 45% | `01` §1, §3; `08` §6 |
| 9 | **FINER** (5 ô, mỗi ô 1 bằng chứng thật) | C3 45% | `01` §5 |
| 10 | **Quy trình thực hiện** — kiến trúc 4 tầng pipeline | C3 45% | `01` §6, `Architecture.md` |
| 11 | **Chỉ số đánh giá + Baseline** (SLI, NDCG@10, coverage, Gini; 3 tầng baseline) | C3 45% | `08` §1, `05C` §1, `Metrics.md` |
| 12 | **Kết quả sơ bộ** (chứng minh khả thi — không phải kết quả cuối) | C3 45% | `01` §7.3–7.4 |
| 13 | **Hiệu quả + ROI + Kế hoạch 5 giai đoạn + rủi ro** | C3 45% | `06` §1, §4; `01` §9 |
| 14 | **Tự đánh giá khả thi & giới hạn** | KL 5% | `Drawbacks.md` |
| 15 | Trao đổi & Thảo luận (Q&A) + Tài liệu tham khảo (5 bài IEEE) | — | `_manifest.json` |

> 15 slide (trong khoảng 10–20 cho phép). Tỷ trọng: C1 = 2 slide · C2 = 3 (S5–S7) · C3 = 7 (S8–S13... gồm S8–S13) · KL = 1 · khung/Q&A = 3. Trọng tâm nội dung (thời gian nói) vẫn chênh về C3 như yêu cầu 45% — C1/C2 mỗi slide được nói kỹ, C3 nói qua bảng.
>
> **Đánh số:** mọi slide có footer `x / 15` (bắt buộc theo yêu cầu giảng viên).

---

## 3. Nội dung chi tiết từng slide

### Slide 3 — DIKW (bắt buộc KHÔNG chép định nghĩa)

| Tầng | Áp dụng vào đề tài |
|---|---|
| **Data** | 25.000.095 tương tác (userId, movieId, rating, timestamp) — MovieLens ml-25m, 1995–2019 |
| **Information** | Thống kê đo thật: 0 cặp trùng; 1.799.454 nhóm timestamp ties; SLI 98,91% / 0% / 0%; unseen-item 8,76% ở temporal |
| **Knowledge** | Quy luật: (i) rò rỉ phải đo **tương đối theo user**, đo toàn cục cho kết luận ngược (LOO: 99,9988% vs 0%); (ii) đổi rò rỉ lấy dịch chuyển miền (mất 96,1% mẫu); (iii) giảm thiên lệch ≠ xử lý thiên lệch (longtail_coverage = 0 cả 6 tổ hợp) |
| **Wisdom** | **SLI + giao thức audit 3 bước** — công cụ giúp nhà nghiên cứu/công ty ra quyết định "split này có tin được không" trước khi đọc số metric |

> Phương pháp tư duy (slide 4): **phân tích** (mổ xẻ 3 split × 6 metric) → **tổng hợp** (giao thức audit) → **quy nạp** (từ 25M tương tác về quy luật) → **phản chứng** (phản ví dụ LOO: định nghĩa toàn cục sai). Ghi chú khung: tư duy phản biện của Popper — một phản ví dụ đủ để bác một định nghĩa.

### Slide 5 — W5H2 (nén thành bảng 6 ô, mỗi ô 1 dòng)

| | Nội dung |
|---|---|
| **What** | Chiến lược chia tập (random 80/20 · temporal global · leave-one-out) tác động đến tín hiệu đo + thiên lệch phổ biến |
| **Who** | Nhà nghiên cứu RS dùng kết quả đánh giá offline; user long-tail bị che khuất |
| **Where/When** | Pipeline Spark/HDFS/MapReduce cục bộ; dữ liệu phim 1995–2019; nghiên cứu 11/2026–06/2027 |
| **Why** | Split sai → rò rỉ → kết luận sai → quyết định triển khai sai |
| **How much** | Chứng minh định lượng: ALS NDCG 0,2584 (random) → 0,0467 (LOO) = chênh **5,5×** trên cùng mô hình, cùng dữ liệu |
| **How** | Audit framework 3 split × 2+ model × 6 metric trên 25M tương tác |

> Phát biểu vấn đề 4 bước (dùng notes): Thực trạng (đa số đánh giá trên random 80/20) → Hậu quả (NDCG phóng đại ảo, thứ hạng có thể đảo) → Hạn chế của tài liệu (đo từng khía cạnh riêng lẻ) → Giải pháp (SLI + giao thức audit).

### Slide 6 — Quản lý tài liệu: 14 bài đã thu thập + kiểm tra độ uy tín

**Layout Two Content.** Trái: ảnh chụp (screenshot) trang PDF của từng bài từ trang nhà xuất bản — nhóm 5 bài chính + thumbnail 9 bài còn lại nhỏ hơn. Phải: bảng uy tín.

**Ảnh chụp bắt buộc** (lấy từ chính file PDF có trong `docs/References/Papers/` — các bản **published version**, đã verify `/Creator` là `acmart`/`Springer`/`Elsevier`, không phải arXiv):

| # | Bài | Ảnh chụp cần lấy | Nguồn verify |
|---|---|---|---|
| 1 | TOIS 2022 Data Leakage | trang đầu (header ACM + DOI) | `pypdf` `/Creator: acmart` |
| 2 | TOIS 2023 Popularity Bias | trang đầu | `acmart` |
| 3 | RecSys '25 Time to Split | trang đầu | `acmart` |
| 4 | RecSys '26 Convergent Validity | trang đầu | `acmart` |
| 5 | TOIS 2022 Bias/Debias Survey | trang đầu | `acmart` |
| 6–14 | 9 bài còn lại | thumbnail hàng đầu + logo journal | `_manifest.json` |

**Bảng độ uy tín (cột phải):**

| Bài | Tạp chí/Hội nghị | SCImago | CORE |
|---|---|---|---|
| TOIS 2022 (x2) | ACM Trans. on Information Systems | **Q1** | A |
| TOIS 2023 | ACM Trans. on Recommender Systems | Q1 | A |
| RecSys '25/'26/'23/'21/'20 | ACM RecSys | Q1 | **A*** |
| SIGIR '23 | ACM SIGIR | Q1 | **A*** |
| UMAI 2024 | Springer User Modeling & User-Adapted Interaction | Q1 | — |
| J. Big Data 2019 | SpringerOpen | Q1 | C |
| ESWA 2023 | Elsevier Expert Systems with Applications | **Q1** | B |

> **Yêu cầu Think–Check–Submit** (ghi dưới bảng): mọi bài đều là **bản nhà xuất bản** (không arXiv — đã loại `10.48550/arxiv.2011.07931`), DOI resolve được, có footer bản quyền ACM/Springer/Elsevier trên PDF. Đóng góp: 14/14 bài ≥ Q1 hoặc CORE B, trong đó **9 bài CORE A*/A**.
>
> **Nguồn số liệu SCImago/CORE:** tra web tại `scimagojr.com` + `coreportal.org` trước khi dựng slide; chụp màn hình kết quả tra, dán vào speaker notes làm bằng chứng.

### Slide 7 — Ma trận tổng hợp (5 dòng, đúng format HD)

| Tài liệu (uy tín) | Phương pháp | Kết quả | Hạn chế → gap |
|---|---|---|---|
| Wang et al. — **TOIS 2022 (Q1)** `10.1145/3569930` | So sánh protocol có/không global timeline; BPR, NeuMF, SASRec, LightGCN | Leakage thay đổi accuracy và thứ hạng | Chưa định nghĩa **chỉ số** đo rò rỉ |
| Abdollahpouri et al. — **TOIS 2023 (Q1)** `10.1145/3637066` | Tách 4 yếu tố: data/algorithm/user-group/eval-strategy | Eval strategy giải thích phần lớn mâu thuẫn bias | Chưa gắn với quy mô Big Data |
| Chen et al. — **RecSys '25 (CORE A*)** `10.1145/3705328.3748164` | SASRec+/BERT4Rec/GRU4Rec × 8 dataset, RePlay | Split strategy thay đổi thứ hạng sequential | Chỉ sequential RS; H100 GPU |
| RecSys '26 (CORE A*) `10.1145/3773078.3831818` | Convergent validity của các thiết kế offline | Sparse ranking ≠ dense judgment | Chưa đo coverage/bias kèm rank |
| RecSys '20 (CORE A*) `10.1145/3383313.3418479` | So sánh split strategies | Split là lựa chọn thiết kế | Tiền thân, quy mô vừa |

> **Khoảng trống (đọc nguyên văn gap 3 phần — 237 từ, rút gọn còn ~80 từ cho slide):** Chưa có nghiên cứu nào đo **đồng thời** (i) đảo chiều thứ hạng, (ii) mức biến mất của thiên lệch phổ biến, (iii) chi phí Big Data — trên **cùng một pipeline**. Đo riêng lẻ thì không biết các hiệu ứng **cộng hưởng hay triệt tiêu nhau**.

### Slide 8 — Tiêu đề, GO/SO, RQ

- **Tiêu đề theo công thức [Phương pháp] + [Mục tiêu] + [Phạm vi]:** *"Kiểm toán chiến lược chia tập (phương pháp) → đánh giá tác động đến tín hiệu đo và thiên lệch phổ biến (mục tiêu) → hệ thống gợi ý trên nền Big Data Spark/HDFS, MovieLens 25M (phạm vi)"*
- Bảng SO–RQ (từ `08` §6): SO1 Data 20% · **SO2 Model — SLI + giao thức 40%** · SO3 Đối chuẩn 20% · SO4 Ablation 20%; mỗi SO khớp 1 RQ.

### Slide 9 — FINER (5 ô, mỗi ô 1 bằng chứng thật)

| | Bằng chứng |
|---|---|
| **F** Khả thi | Dataset đã tải + đo; PoC chạy xong trước deadline; khung có sẵn |
| **I** Thú vị | "Cách đo có đúng không" quan trọng hơn "model nào tốt hơn" |
| **N** Mới | **SLI** — phát hiện khái niệm: LOO toàn cục 99,9988% vs tương đối 0% — chưa có trong TOIS 2022 |
| **E** Đạo đức | Dataset ẩn danh, license research-use, trích dẫn Harper & Konstan `10.1145/2827872`, không redistribute |
| **R** Thiết thực | Đóng góp là **giao thức đánh giá**, không phải model mới — dùng được cho mọi dataset có timestamp |

### Slide 10 — Quy trình thực hiện (sơ đồ 4 tầng, vẽ bằng shape trong pptx)

```
CSV 25M → Parquet (pyarrow 26s)
   → [TẦNG 1] HDFS + MapReduce Java: popularity 323.737 key, G3 cross-check 100%
   → [TẦNG 2] Spark local[4]: 3 split → materialize 735 MB → audit
              MostPopular top-K | ALS implicit (rank 16, alpha 10) → numpy top-K
   → [TẦNG 3] MongoDB: audit_metrics 42 field, item_profile 62.423 docs
   → [TẦNG 4] R (7 figures) + Streamlit dashboard + kiểm định Wilcoxon/bootstrap
```
> Ghi dưới sơ đồ: *đã chạy thật — MapReduce SUCCESS, G3 PASS 100%, 6/6 notebook gate PASS*.

### Slide 11 — Chỉ số + Baseline

- **Chỉ số tầng dữ liệu:** SLI = (công thức, 1 dòng) + 3 ngưỡng phân loại (an toàn < 0,05 / nhẹ < 0,30 / nghiêm trọng ≥ 0,30)
- **Chỉ số ranking:** NDCG@10 = DCG/IDCG (công thức 2 dòng); Hit@10
- **Chỉ số công bằng:** catalog coverage, Gini exposure, popularity-bias ratio, longtail_coverage
- **Baseline 3 tầng (bắt buộc Bài 03):** sàn (MostPopular, Random) · kinh điển (ALS implicit, ItemKNN) · SOTA (SASRec+ hoặc EASE CPU nếu thiếu GPU)

### Slide 12 — Kết quả sơ bộ (chứng minh khả thi — KHÔNG phải kết quả cuối)

Bảng 3 cột × 3 chỉ số chính (từ `01` §7.3 + notebook 09):

| | random 80/20 | temporal | leave-one-out |
|---|---|---|---|
| SLI (tương đối) | 98,91% | 0% | 0% |
| NDCG@10 ALS | 0,2556 | 0,1311 | 0,0467 |
| `eval_rel_users` | 158.692 | 6.219 | 96.003 |

> 3 nhận xét 1 dòng mỗi cái: (1) split đẹp nhất rò rỉ nặng nhất; (2) split sạch nhất mất 96,1% mẫu; (3) thứ hạng không đảo ở 2 mô hình nhưng độ lớn đổi **5,5×**. **Ghi rõ dòng disclaimer:** *"Số liệu sơ bộ, seed đơn (42), method-informed implementation — chứng minh khả thi, không phải kết luận cuối."*

### Slide 13 — Hiệu quả + ROI + Kế hoạch 5 giai đoạn + rủi ro

- **Hiệu quả dự kiến (định lượng):** giao thức audit chặn **3/3 cặp so sánh** không hợp lệ (tỷ lệ mẫu 25,5×/1,65×/15,4× > ngưỡng 1,2) → tránh kết luận sai trước khi công bố. SLI tính được trong ~2 phút cho split mới.
- **ROI:** chi phí = 1 laptop, không GPU; thời gian còn lại ≤ X ngày; đầu ra = 3 tạo tác (SLI dạng Concepts+Models, giao thức 3 bước dạng Methods, pipeline tái lập dạng Instantiations) — đạt yêu cầu Bài 03 "đóng góp dạng 2 + 3".
- **Kế hoạch 5 giai đoạn** (đến 06/2027): G1 hoàn thiện thực nghiệm (thêm 3 seed) → G2 phân tích thống kê mở rộng → G3 viết báo cáo + dashboard demo → G4 rà soát phản biện nội bộ → G5 bảo vệ cuối kỳ. Mỗi giai đoạn có mốc + output.
- **Rủi ro** (4 dòng từ `06` §4): thiếu SOTA → EASE; hạ tầng lỗi → giữ trục khoa học (PySpark local); thiếu thời gian → cắt cross-domain; seed đơn → khai báo giới hạn.

### Slide 14 — Tự đánh giá (KL 5%)

| | Trạng thái |
|---|---|
| Dữ liệu | ✅ hợp pháp, ẩn danh, đã verify SHA-256 |
| Năng lực | ✅ PySpark + Hadoop + MapReduce Java + MongoDB + R + Streamlit — tất cả đã chạy thật |
| Nguồn lực & thời gian | ✅ laptop, không GPU; khung PoC có sẵn |
| Giới hạn (nói thẳng) | `local[4]` không phải cluster; ALS subsample 30k/162.541 user; 1 seed; 2 baseline; NDCG không so cặp giữa split |
| Hướng mở rộng | Cross-domain (Amazon/Steam), thêm SOTA, ma trận 10 seed |

### Slide 15 — Q&A + Tài liệu tham khảo

5 bài IEEE format, đúng `_manifest.json` (đã verify DOI + venue): [1] Wang TOIS 2022 · [2] Abdollahpouri TOIS 2023 · [3] Chen RecSys'25 · [4] RecSys'26 · [5] Harper & Konstan TIST 2015.

---

## 4. Quy trình sản xuất (thứ tự làm)

| Bước | Việc | Output | Ước lượng |
|---|---|---|---|
| 1 | Viết `scripts/generate_slides.py` — python-pptx, 15 slide, template tối giản (title + body + footer `x / 15`) | file `.pptx` nháp | 1 phiên |
| 2 | Nhồi nội dung theo §3; mỗi slide ≤ 6 dòng bullet + 1 bảng/sơ đồ | slide hoàn chỉnh nội dung | 1 phiên |
| 3 | Vẽ 2 hình riêng bằng matplotlib cho slide 10 (kiến trúc) và slide 12 (SLI 3 cột: toàn cục vs tương đối — chính là hình số 1 luận văn theo `08` §7.2) | 2 PNG | 1 phiên |
| 4 | Speaker notes cho từng slide: script nói + 3 câu hỏi dự phòng mỗi slide | notes | 1 phiên |
| 5 | Rà soát checklist §5; sửa cỡ chữ ≥ 24pt (bảng 20pt) | bản nộp | nửa phiên |
| 6 | (Tùy chọn) Export PDF dự phòng | `.pdf` | 5 phút |

> **Nguyên tắc an toàn:** nội dung slide **không phụ thuộc** kết quả chạy tiếp theo. Slide 12 dùng số đã đo + disclaimer. Nếu thực nghiệm có thêm số mới (3 seed, EASE) thì chỉ cần cập nhật bảng slide 12 — không phải dựng lại.

## 5. Checklist đối chiếu yêu cầu giảng viên

| Yêu cầu (HD slide) | Có ở slide | Trạng thái |
|---|---|---|
| Bố cục 4 phần đúng tỷ trọng | 2 | ⬜ |
| DIKW áp dụng đề tài, không chép định nghĩa | 3 | ⬜ |
| Phương pháp tư duy | 4 | ⬜ |
| W5H2 + chuỗi phát biểu vấn đề | 5 | ⬜ |
| ≥ 5 bài báo, IEEE, Q1/Q2 hoặc CORE A*/A/B + ảnh chụp + SCImago/CORE | 6, 15 | ⬜ |
| Ma trận (Tài liệu/Phương pháp/Kết quả/Hạn chế) + gap | 7 | ⬜ |
| Tiêu đề [Phương pháp]+[Mục tiêu]+[Phạm vi] | 8 | ⬜ |
| GO/SO gắn RQ | 8 | ⬜ |
| FINER (F/I/N/E/R từng ô có bằng chứng) | 9 | ⬜ |
| Quy trình 4 bước + công thức độ đo + Baseline | 10, 11 | ⬜ |
| Hiệu quả định lượng + ROI + kế hoạch 5 giai đoạn + rủi ro | 13 | ⬜ |
| Tự đánh giá: dữ liệu/năng lực/nguồn lực/giới hạn | 14 | ⬜ |
| Q&A slide cuối | 15 | ⬜ |
| Cỡ chữ ≥ 24pt, nền sáng, sơ đồ/bảng thay văn dài | toàn bộ | ⬜ |
| Footer `x / 15` (đánh số mọi slide) | toàn bộ | ⬜ |

## 6. Rủi ro khi dựng slide + ứng phó

| Rủi ro | Ứng phó |
|---|---|
| Bảng số nhiều → slide rối | Mỗi bảng ≤ 5 dòng; số chỉ giữ 4 chữ số có nghĩa; chi tiết để speaker notes |
| Đề tài có phần kỹ thuật nặng (SLI, pipeline) dễ bị hỏi sâu | Mỗi slide kỹ thuật có 3 câu hỏi dự phòng trong notes (SLI toàn cục vs tương đối? vì sao LOO không rò rỉ? 30k subsample có đại diện không?) |
| Người nghe không biết RecSys là gì | Slide 3 Data tầng mở đầu bằng 1 câu định nghĩa hệ thống gợi ý thực tế (Netflix/YouTube) |
| Đề tài nộp 2 môn (BIDA + STRM) dễ gây nhầm trọng tâm | Slide 1 ghi rõ: trình bày cho **PPNCKH** — trọng tâm quy trình nghiên cứu, không phải demo hạ tầng |




