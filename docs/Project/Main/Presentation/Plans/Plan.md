# Kế hoạch tạo slide thuyết trình PPNCKH — bảo vệ đề cương

**Project:** `D:\Master Exers\Big Data\Recomendation_System`
**Cập nhật:** 2026-11-18
**Mục đích:** Bảo vệ đề cương PPNCKH. Slide khớp artifact cuối: 5 model, 20 cặp kiểm định, SASRec+CE GPU local, 1 seed, 3 split. 

**Căn cứ:**
- [HD Chuan bi thuyet trinh.pdf](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/docs/References/HUFLIT/Research_Methods/HD%20Chuan%20bi%20thuyet%20trinh.pdf) (TS. Trần Minh Thái — 12 slide mẫu, tỷ trọng C1 20% / C2 30% / C3 45% / KL 5% + Q&A)
- 14 paper Q1/CORE A*/A (docs/References/Papers/ + `_manifest.json`)
- Đề tài, W5H2, FINER, gap 3 phần, SLI — `docs/Project/Plans/Research/`
- Kết quả đo thật (PoC 2026-11-04 + notebook 04–09 2026-11-15) — dùng làm **kết quả sơ bộ chứng minh khả thi**, không phải deliverable chính

---

## 1. Định dạng đầu ra

| Hạng mục | Quyết định |
|---|---|
| Số slide | **15** (trong khoảng 10–20 cho phép) |
| Công cụ | `python-pptx` — script sinh slide (`scripts/generate_slides.py`) + dùng 1 slide mẫu của file HD làm reference layout (Title and Content / Two Content, footer `x / 15`) |
| Cỡ chữ | Title 30pt; thân slide 11–17pt; bảng dày 9–13pt. Chưa đạt mức ≥24pt của hướng dẫn. Muốn đạt: đẩy bảng dày sang phụ lục, thân slide chỉ giữ 3 số chính. |
| Nền | Sáng (trắng / trắng ngà), một accent màu; không animation |
| Ngôn ngữ | Tiếng Việt, cách nói dễ hiểu. Tên chỉ số/mô hình giữ nguyên khi cần tra cứu (SLI, NDCG@10, MRR@10, SASRec); giải thích bằng tiếng Việt ngay bên cạnh. |
| Trực quan | Sơ đồ + bảng thay đoạn văn; mỗi slide ≤ 2 khối thông tin |
| Speaker notes | Mỗi slide có notes (script nói + dự phòng Q&A), dù file mẫu không yêu cầu — vì người trình bày cần |

---

## 2. Cấu trúc 15 slide — khớp tỷ trọng HD

| # | Slide | Phần (tỷ trọng) | Nguồn nội dung |
|---|---|---|---|
| 1 | Tiêu đề đề tài + sinh viên + GVHD | — | `01_De_tai_va_Ke_hoach.md` §1 |
| 2 | Bố cục trình bày (C1 20% · C2 30% · C3 45% · KL 5%) | — | copy cấu trúc HD slide 2 |
| 3 | **DIKW áp dụng vào đề tài** | C1 20% | mục §4 dưới đây |
| 4 | **Phương pháp tư duy** (3 cách: diễn dịch – quy nạp – suy đoán; phản chứng là bước kiểm chứng thêm) | C1 20% | mục §5 |
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

> Phương pháp tư duy (slide 4): đúng 3 cách theo báo cáo/bài giảng — **diễn dịch** (lý thuyết chung → trường hợp cụ thể; TOIS 2022 → kiểm tra 3 split), **quy nạp** (nhiều quan sát → quy luật chung — **chủ đạo**, vì kết luận rút từ dữ liệu thật), **suy đoán** (dữ kiện lạ → giả thuyết rồi kiểm chứng). **Phản chứng không phải phương pháp thứ 4** — chỉ là bước kiểm chứng thêm: phản ví dụ LOO bác định nghĩa rò rỉ toàn cục.

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
> Ghi dưới sơ đồ: *đã chạy thật — MapReduce SUCCESS, G3 PASS 100%, 10/10 notebook gate PASS (04–12)*.

### Slide 11 — Chỉ số + Baseline

- **Chỉ số tầng dữ liệu:** SLI = (công thức, 1 dòng) + 3 ngưỡng phân loại (an toàn < 0,05 / nhẹ < 0,30 / nghiêm trọng ≥ 0,30)
- **Chỉ số ranking:** NDCG@10 = DCG/IDCG (công thức 2 dòng); Hit@10
- **Chỉ số công bằng:** catalog coverage, Gini exposure, popularity-bias ratio, longtail_coverage
- **Baseline 3 tầng (bắt buộc Bài 03):** sàn (MostPopular, Random) · kinh điển (ALS implicit, ItemKNN) · đối chuẩn mới (SASRec+CE GPU local). EASE không đăng ký nên không chạy.

### Slide 12 — Kết quả sơ bộ (chứng minh khả thi — KHÔNG phải kết quả cuối)

Bảng 5 model × 3 cách chia (từ artifact cuối):

| Model | NDCG random | NDCG thời gian | NDCG LOO |
|---|---|---|---|
| ItemKNN | 0,2679 | 0,1409 | 0,0461 |
| ALS | 0,2581 | 0,1332 | 0,0469 |
| SASRec+CE (GPU) | 0,0163 | 0,0188 | 0,0067 |
| MostPopular | 0,0852 | 0,0455 | 0,0183 |
| Random | 0,0003 | 0,0009 | 0,0001 |

> 3 nhận xét: (1) split đẹp nhất rò rỉ nặng nhất (98,91%); (2) split sạch nhất mất 96,1% mẫu đánh giá; (3) ItemKNN dẫn ở random/temporal, ALS dẫn ở LOO nhưng `p=0,153` → không kết luận. **Disclaimer bắt buộc:** *"1 seed (42), SASRec là đối chuẩn `tuning_budget=0`, không Mean±Std, không đo bộ nhớ; số liệu chứng minh khả thi, chưa phải kết luận cuối."*

### Slide 13 — Hiệu quả + ROI + Kế hoạch 5 giai đoạn + rủi ro

- **Hiệu quả dự kiến (định lượng):** giao thức audit chặn **3/3 cặp so sánh** không hợp lệ (tỷ lệ mẫu 25,5×/1,65×/15,4× > ngưỡng 1,2) → tránh kết luận sai trước khi công bố. SLI tính được trong ~2 phút cho split mới.
- **ROI:** chi phí = 1 laptop i7-13620H/32 GB/RTX 4050 6 GB, không cloud; đầu ra = 3 tạo tác (thước đo SLI, cách kiểm tra 3 bước, pipeline chạy lại được) — đạt yêu cầu Bài 03 "đóng góp dạng 2 + 3".
- **Kế hoạch 5 giai đoạn** (đến 06/2027): G1 xong SASRec GPU + bảng 3 split × 5 model → G2 xong Wilcoxon/CI/độ lớn, 20/20 cặp → G3 báo cáo + thử giao diện → G4 phản biện nội bộ → G5 bảo vệ. Không cam kết thêm seed trong kế hoạch hiện tại.
- **Rủi ro** (4 dòng từ `06` §4): thiếu SOTA → EASE; hạ tầng lỗi → giữ trục khoa học (PySpark local); thiếu thời gian → cắt cross-domain; seed đơn → khai báo giới hạn.

### Slide 14 — Tự đánh giá (KL 5%)

| | Trạng thái |
|---|---|
| Dữ liệu | Hợp pháp, ẩn danh, đã kiểm tra sha256, dùng cho nghiên cứu |
| Kỹ thuật | PySpark + MapReduce Java + MongoDB + R + Streamlit; MapReduce chạy thật 2026-11-04 |
| Thời gian & máy | Laptop RTX 4050 6 GB; G1–G5 đến 06/2027 |
| Giới hạn (nói thẳng) | `local[4]` không phải cụm; container đã gỡ; 5/5 model chạy (SASRec GPU, tập người con); không so CPU/GPU; 1 seed; không Mean±Std; không đo bộ nhớ; không so NDCG giữa split |
| Hướng mở rộng | Sang tập khác (Amazon/Steam); thêm seed; chỉnh SASRec; đo bộ nhớ; nếu có thời gian thêm Friedman/Nemenyi |

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
| Bố cục 4 phần đúng tỷ trọng | 2 | ✅ |
| DIKW áp dụng đề tài, không chép định nghĩa | 3 | ✅ |
| Phương pháp tư duy | 4 | ✅ |
| W5H2 + chuỗi phát biểu vấn đề | 5 | ✅ |
| ≥ 5 bài báo, IEEE, Q1/Q2 hoặc CORE A*/A/B + ảnh chụp + SCImago/CORE | 6, 15 | ✅ |
| Ma trận (Tài liệu/Phương pháp/Kết quả/Hạn chế) + gap | 7 | ✅ |
| Tiêu đề [cách làm]+[mục tiêu]+[phạm vi] | 8 | ✅ |
| Mục tiêu gắn câu hỏi; thêm biến và H0/H1 | 8 | ✅ |
| FINER (mỗi ô có bằng chứng) | 9 | ✅ |
| Quy trình 4 tầng + công thức độ đo + 5 baseline | 10, 11 | ✅ |
| Kiểm định Wilcoxon/CI/độ lớn; 20/20 cặp | 11, 12 | ✅ |
| Hiệu quả định lượng + chi phí + kế hoạch 5 giai đoạn + rủi ro | 13 | ✅ |
| Tự đánh giá: dữ liệu/năng lực/nguồn lực/giới hạn | 14 | ✅ |
| Q&A slide cuối + repo URL | 15 | ✅ |
| Nền sáng, sơ đồ/bảng thay văn dài, không tràn/overlap | toàn bộ | ✅ |
| Cỡ chữ ≥ 24pt | toàn bộ | ⚠️ Chưa; bảng 9–13pt để tránh tràn |
| Footer `x / 15` (đánh số mọi slide) | toàn bộ | ✅ |

## 6. Rủi ro khi dựng slide + ứng phó

| Rủi ro | Ứng phó |
|---|---|
| Bảng số nhiều → slide rối | Mỗi bảng ≤ 5 dòng; số chỉ giữ 4 chữ số có nghĩa; chi tiết để speaker notes |
| Đề tài có phần kỹ thuật nặng (SLI, pipeline) dễ bị hỏi sâu | Mỗi slide kỹ thuật có câu hỏi dự phòng trong notes (SLI toàn cục vs tương đối? vì sao LOO không rò rỉ? 1 seed có đủ không? SASRec có phải model thắng không?) |
| Người nghe không biết RecSys là gì | Slide 3 Data tầng mở đầu bằng 1 câu định nghĩa hệ thống gợi ý thực tế (Netflix/YouTube) |
| Đề tài nộp 2 môn (BIDA + STRM) dễ gây nhầm trọng tâm | Slide 1 ghi rõ: trình bày cho **PPNCKH** — trọng tâm quy trình nghiên cứu, không phải demo hạ tầng |


## 7. Ghi nhận chỉnh slide 2026-11-18

- Script sinh slide: `scripts/generate_slides.py`.
- File slide: `docs/Project/Main/Presentation/Slides/PPNCKH_DeCuong_15slides.pptx` (15 slide, đã kiểm tra geometry: không shape tràn slide, không overlap bỏ qua nền header).
- Text đối chiếu: `logs/scratch/slide_audit_20261118/PPNCKH_DeCuong_15slides_final.txt`.
- Thân slide dùng từ dễ hiểu; thuật ngữ đầy đủ nằm trong speaker notes.
- S8: bỏ `3+ seed`, ghi `1 seed (đã khai báo giới hạn)`; thêm biến độc lập/phụ thuộc/kiểm soát và H0/H1.
- S7: nêu rõ đóng góp là hệ thống + thực nghiệm; không nhận phương pháp mới hay miền mới.
- S11/S12: SASRec là đối chuẩn SOTA chạy lại, `tuning_budget=0`, không phải model thắng; disclaimer 1 seed, không Mean±Std, không đo bộ nhớ.
- S13/S15: thêm repo `https://github.com/StreetParkourZombie/Recommendation_System`.
- S14: thêm bốn nhóm an toàn dữ liệu/thiết kế/đo lường/thống kê ở mức tóm tắt.
- Deck `PPNCKH_DeCuong_15slides_Self-Adjustion.pptx` cũ, lỗi thời; không dùng làm bằng chứng.
- Hạn chế còn lại: cỡ chữ bảng dày 9–13pt, chưa đạt ≥24pt. Giữ để tránh tràn/overlap; nếu hội đồng bắt buộc ≥24pt, chuyển bảng sang phụ lục.

## Chốt slide 4 — bản thân thiện người xem (2026-11-19)

Slide 4 đã đổi từ dạng bullets sang **3 thẻ màu ngang hàng**, mỗi thẻ gồm: nhãn ngắn, tên cách, 3 bước suy nghĩ, ô «Ví dụ thật». Mũi tên nối 3 thẻ; thanh tóm tắt ở cuối slide.

- Thẻ 1 — `Diễn dịch`: «có quy luật sẵn → áp xuống trường hợp trước mặt → thấy khác thì sửa cách hiểu».
- Thẻ 2 — `Quy nạp` **CHỦ ĐẠO**: «nhìn nhiều trường hợp → rút quy luật chung → kết luận từ dữ liệu thật». Chủ đạo vì kết luận chính rút từ dữ liệu thật.
- Thẻ 3 — `Suy đoán`: «thấy điểm bất thường → đoán nguyên nhân hợp lý → đếm lại để kiểm chứng».
- `Phản chứng` vẫn là bước kiểm chứng thêm, không phải phương pháp thứ 4.
- Tên kỹ thuật (`TOIS`, `offline`, `random 80/20`, `leave-one-out`, `LOO`, `SLI`, `split`, `seed`, `ALS`, `NDCG`) chuyển hết vào ghi chú trình bày; thân slide dùng cách nói thường: «nghiên cứu 2022», «trộn ngẫu nhiên», «giữ lượt cuối», «cùng mốc thời gian», «mô hình gợi ý».
- Số liệu giữ nguyên nguồn: `98,91%`, `0%`, `0,2584 → 0,0474` (đường script 2026-11-04 / `Metrics.md` mục 4), `25 triệu lượt chấm`. Không trộn `0,2581 → 0,0469` của đường notebook/FULL.
- Generator: helper `add_thinking_card`, modifier excluded `decor_*` khỏi kiểm tra chồng chéo; chạy `scripts/generate_slides.py` cho kết quả `15 slides, layout checked`.
- Không sửa `.tex`, không chạy lại notebook.
