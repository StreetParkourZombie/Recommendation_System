# Kế hoạch tạo slide thuyết trình PPNCKH — bảo vệ đề cương

**Project:** `D:\Master Exers\Big Data\Recomendation_System`
**Cập nhật:** 2026-11-25
**Mục đích:** Bảo vệ đề cương PPNCKH. Slide khớp artifact cuối: 5 model, 20 cặp kiểm định, SASRec+CE GPU local, 1 seed, 3 split. 

**Căn cứ:**
- [HD Chuan bi thuyet trinh.pdf](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/docs/References/HUFLIT/Research_Methods/HD%20Chuan%20bi%20thuyet%20trinh.pdf) (TS. Trần Minh Thái — 12 slide mẫu, tỷ trọng C1 20% / C2 30% / C3 45% / KL 5% + Q&A)
- 10 paper Q1/CORE A*/A dung trong de cuong (14 PDF trong docs/References/Papers/, 4 bai archived)
- Đề tài, W5H2, FINER, gap 3 phần, SLI — `docs/Project/Plans/Research/`
- Kết quả đo thật (PoC 2026-11-04 + notebook 04–09 2026-11-15) — dùng làm **kết quả sơ bộ chứng minh khả thi**, không phải deliverable chính

---

## 1. Định dạng đầu ra

| Hạng mục | Quyết định |
|---|---|
| Số slide | **20 slide chính + 4 phụ lục** (trong khoảng 10–20 cho phép cho slide chính) |
| Công cụ | `python-pptx` — script sinh slide (`scripts/generate_slides.py`) + dùng 1 slide mẫu của file HD làm reference layout (Title and Content / Two Content, footer `x / 20`; phụ lục `A1/4`…`A4/4`) |
| Cỡ chữ | Title 28–30pt. Thân/thẻ slide chính 18–22pt (chủ yếu 20–22pt); bảng dày dời hết sang phụ lục A1–A4 (10,5–13pt). `verify_layout()` chặn thân slide chính <18pt. |
| Nền | Sáng (trắng / trắng ngà), một accent màu; không animation |
| Ngôn ngữ | Tiếng Việt, cách nói dễ hiểu. Tên chỉ số/mô hình giữ nguyên khi cần tra cứu (SLI, NDCG@10, MRR@10, SASRec); giải thích bằng tiếng Việt ngay bên cạnh. |
| Trực quan | Sơ đồ + bảng thay đoạn văn; mỗi slide ≤ 2 khối thông tin |
| Speaker notes | Mỗi slide có notes (script nói + dự phòng Q&A), dù file mẫu không yêu cầu — vì người trình bày cần |

---

## 2. Cấu trúc 20 slide chính — khớp tỷ trọng HD

| # | Slide | Phần (tỷ trọng) | Nguồn nội dung |
|---|---|---|---|
| 1 | Tiêu đề + một dòng "Vào: bảng chấm 25 triệu dòng · Ra: phiếu chẩn đoán" | — | §9.1 |
| 2 | Bố cục 20/30/45/5 | — | HD p2 |
| 3 | DIKW áp dụng vào đề tài | C1 20% | §3, §9.1 |
| 4 | Phương pháp tư duy (diễn dịch / quy nạp chủ đạo / suy đoán) | C1 20% | §3, §9.1 |
| 5 | W5H2 — sáu câu hỏi | C2 30% | §3, §9.1 |
| 6 | **ĐẦU VÀO là gì** — 4 cột + 4 số lớn | C2 30% | §8.3, §9.1 |
| 7 | **ĐẦU RA là gì** — 4 vật thể O1–O4 có tên file | C2 30% | §8.3, §9.1 |
| 8 | Kiểm tra tài liệu — 10 bài Nhóm A + 3 bài Nhóm B | C2 30% | `03` §0B/§0C |
| 9 | **Baseline ↔ bài báo** — 5 dòng, có bài gốc | C2 30% | §9.3 |
| 10 | Bài trước làm được gì, còn thiếu gì — số thật từ PDF | C2 30% | §9.2 |
| 11 | Khoảng trống — 3 thiếu + 1 cách làm | C2 30% | `07_Gap...md` |
| 12 | Mục tiêu và câu hỏi — GO/SO/RQ, MRQ, H0/H1 | C3 45% | `08` §6 |
| 13 | FINER — 5 ô, mỗi ô 1 bằng chứng | C3 45% | `01` §5 |
| 14 | Quy trình chạy thật — INPUT trái / OUTPUT phải | C3 45% | `Architecture.md`, `fig_architecture.png` |
| 15 | Cách đo rò rỉ và độ đúng — SLI + NDCG@10 | C3 45% | `08` §1, `Metrics.md` |
| 16 | Năm mô hình dùng để thử — 3 nhóm + tham số | C3 45% | `05C`, §9.3 |
| 17 | Kết quả: chia khác, điểm đổi + verdict | C3 45% | `comparison.json`, `audit_report.json` |
| 18 | Hiệu quả, rủi ro, kế hoạch | C3 45% | `06` §1/§4, `01` §9 |
| 19 | Tự đánh giá và giới hạn | KL 5% | `Drawbacks.md` |
| 20 | Hỏi và đáp + 13 tài liệu chia 2 nhóm | — | §9.3, `03` §0C |

**Phụ lục (không tính 20, footer `A1/4`…`A4/4`):** A1 bảng kết quả đầy đủ · A2 20 cặp kiểm định · A3 tham số/máy · A4 13 tài liệu.

> Tỷ trọng nói theo thời lượng: C1 = 2 slide · C2 = 7 slide (S5–S11) · C3 = 8 slide (S12–S18) · KL = 1 · khung/Q&A = 2. Trọng tâm vẫn nằm ở S12–S18.
> **Đánh số:** mọi slide chính có footer `x / 20`; phụ lục có footer `A1/4`…`A4/4`.

---

## 3. Nội dung chi tiết từng slide

> Mục này giữ lại để đối chiếu ý nghĩa các slide. Bố cục và số liệu chốt lấy theo **§2** và **§9** (§9 thay §8.4–§8.7). Không dùng lại số `0,2584 / 0,0474 / 158.688 / 6.219 / 96.003`.

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
| **How much** | Chứng minh định lượng: ALS NDCG 0,2581 (random) → 0,0469 (LOO, notebook FULL 2026-11-17) = chênh **5,5×** trên cùng mô hình, cùng dữ liệu |
| **How** | Audit framework 3 split × 2+ model × 6 metric trên 25M tương tác |

> Phát biểu vấn đề 4 bước (dùng notes): Thực trạng (đa số đánh giá trên random 80/20) → Hậu quả (NDCG phóng đại ảo, thứ hạng có thể đảo) → Hạn chế của tài liệu (đo từng khía cạnh riêng lẻ) → Giải pháp (SLI + giao thức audit).

### Slide 6 — Quản lý tài liệu: 10 bài trích dẫn + kiểm tra độ uy tín

**Layout Two Content.** Trái: ảnh chụp (screenshot) trang PDF của từng bài từ trang nhà xuất bản — nhóm 5 bài chính + thumbnail 5 bài còn lại nhỏ hơn. Phải: bảng uy tín.

**Ảnh chụp bắt buộc** (lấy từ chính file PDF có trong `docs/References/Papers/` — các bản **published version**, đã verify `/Creator` là `acmart`/`Springer`/`Elsevier`, không phải arXiv):

| # | Bài | Ảnh chụp cần lấy | Nguồn verify |
|---|---|---|---|
| 1 | TOIS 2022 Data Leakage | trang đầu (header ACM + DOI) | `pypdf` `/Creator: acmart` |
| 2 | TOIS 2023 Popularity Bias | trang đầu | `acmart` |
| 3 | RecSys '25 Time to Split | trang đầu | `acmart` |
| 4 | RecSys '26 Convergent Validity | trang đầu | `acmart` |
| 5 | TOIS 2022 Bias/Debias Survey | trang đầu | `acmart` |
| 06–10 | 5 bài còn lại | thumbnail hàng đầu + logo journal | `_manifest.json` |

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

> **Yêu cầu Think–Check–Submit** (ghi dưới bảng): mọi bài đều là **bản nhà xuất bản** (không arXiv — đã loại `10.48550/arxiv.2011.07931`), DOI resolve được, có footer bản quyền ACM/Springer trên PDF. Đóng góp: **10/10 bài ≥ Q1**, trong đó **9 bài CORE A*/A**, 1 bài Q1 chưa xếp CORE (UMAI 2024).
>
> **Nguồn số liệu SCImago/CORE:** tra web tại `scimagojr.com` + `coreportal.org` trước khi dựng slide; chụp màn hình kết quả tra, dán vào speaker notes làm bằng chứng.

### Slide 7 — Ma trận tổng hợp (5 dòng, đúng format HD)

| Tài liệu (uy tín) | Phương pháp | Kết quả | Hạn chế → gap |
|---|---|---|---|
| Wang et al. — **TOIS 2022 (Q1)** `10.1145/3569930` | So sánh protocol có/không global timeline; BPR, NeuMF, SASRec, LightGCN | Leakage thay đổi accuracy và thứ hạng | Chưa định nghĩa **chỉ số** đo rò rỉ |
| Abdollahpouri et al. — **TOIS 2023 (Q1)** `10.1145/3637066` | Tách 4 yếu tố: data/algorithm/user-group/eval-strategy | Eval strategy giải thích phần lớn mâu thuẫn bias | Chưa gắn với quy mô Big Data |
| Gusak, …, Frolov — **RecSys '25 (CORE A*)** `10.1145/3705328.3748164` | SASRec+/BERT4Rec/GRU4Rec × 8 dataset, RePlay | Split strategy thay đổi thứ hạng sequential | Chỉ sequential RS; H100 GPU |
| Parajuli et al. — RecSys '26 (CORE A*) `10.1145/3773078.3831818` | Convergent validity của các thiết kế offline | Sparse ranking ≠ dense judgment | Chưa đo coverage/bias kèm rank |
| Meng et al. — RecSys '20 (CORE A*) `10.1145/3383313.3418479` | So sánh split strategies | Split là lựa chọn thiết kế | Tiền thân, quy mô vừa |

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
| 5 | Rà soát checklist §5; kiểm tra cỡ chữ 9–30pt, fit text | bản nộp | nửa phiên |
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
| Cỡ chữ thân ≥ 18–20pt | slide 1–20 | ✅ Thân/thẻ 18–22pt; bảng dày dời A1–A4; `verify_layout()` chặn run <18pt |
| Footer `x / 20`, phụ lục `A1/4`…`A4/4` | toàn bộ | ✅ |

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
- Ghi nhận cũ (đã thay bởi §9/§10): cỡ chữ thân/bảng 9–15pt. Bản chốt 20 slide dùng thân 18–22pt, bảng dày ở A1–A4.

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


## Chốt bản trang trí toàn deck (2026-11-19)

- Áp dụng component PowerPoint gốc (thẻ bo góc, badge, stat card, banner, mũi tên, thanh chú thích) cho mọi slide 1–15. Cách nói đời thường; tên kỹ thuật đầy đủ giữ trong speaker notes.
- Slide 4 giữ nguyên đúng 3 cách: `Diễn dịch`, `Quy nạp` (**CHỦ ĐẠO**), `Suy đoán`. `Phản chứng` là bước kiểm chứng thêm, không phải phương pháp thứ 4.
- Slide 10: 4 ô tầng đổi sang helper `add_compact_card` (mỗi ô một khung chữ + thanh màu) để hết tràn. Slide 11: thu nhỏ đầu thẻ đối chuẩn. Slide 13: tăng chiều cao thẻ rủi ro.
- Kiểm tra: `py_compile` OK; generator in `15 slides, layout checked`; `verify_final_slides.py` giữ nguyên các check đúng/sai; `check_text_fit.py` cho `TOTAL_FLAGS 0`.
- Extracted text làm mới: `docs/Project/Main/Presentation/Slides/PPNCKH_DeCuong_15slides.extracted.txt`.
- Không sửa `.tex`, không chạy lại notebook, không commit/push.

---

# 8. Kế hoạch chỉnh slide v2 — 2026-11-24

**Lý do:** hội đồng/người xem không nhận ra **đầu vào là gì, đầu ra là gì, sản phẩm cụ thể là gì**. Đề tài hiện được kể như "một chuỗi phân tích", không có vật thể bàn giao rõ như "phân loại ảnh nội soi → nhãn cho từng ảnh".

> [!WARNING]
> `Plans\Plan.md` và `Plans\00_Slide_Plan.md` là **cùng một file** (hardlink, cùng MD5 `F0F43A43…3244`). Sửa file này là sửa cả hai. `scripts\generate_slides.py` docstring trỏ tới `00_Slide_Plan.md` nên không có chuyện lệch bản.

---

## 8.1 Chẩn đoán — 5 lỗi cấu trúc đang có

| # | Lỗi | Bằng chứng | Hệ quả |
|---|---|---|---|
| D1 | **Không có slide "Đầu vào → Đầu ra"** | 15 slide hiện tại: S3 DIKW, S5 W5H2, S10 quy trình. Không slide nào phát biểu "nhận gì, trả ra cái gì" | Người nghe phải tự suy; đề tài bị coi là "phân tích trừu tượng" |
| D2 | **Đầu ra không phải vật thể** | S13 nói "3 kết quả: thước đo SLI · kiểm tra 3 bước · pipeline" nhưng không có tên file/định dạng | Không kiểm chứng được "đã xong hay chưa" |
| D3 | **Số liệu trộn 2 đường chạy** | `generate_slides.py` L455/L489: `0,2584 → 0,0474`; L500/L722: `0,2581 → 0,0469` | Cùng deck, cùng mô hình, 2 con số khác nhau |
| D4 | **Định nghĩa `8,76%` sai** | L401: "phim kiểm tra là phim **người đó** chưa chấm" | Sai bản chất: đó là item **chưa từng có trong train toàn cục**, không phải chưa chấm bởi user |
| D5 | **Baseline không có bài báo kèm** | S11 chỉ ghi tên 5 mô hình; TLTK S15 chỉ có 10 bài về split/bias | Thầy yêu cầu "mỗi baseline/kinh điển/SOTA phải có bài tương ứng" — hiện **không đáp ứng** |

Lỗi phụ: `158.688 / 6.219 / 96.003` (S3 L403, S13 L748) là **số user của Popularity**, không phải của ALS (ALS = `158.626 / 6.214 / 95.977`). Trộn 2 nguồn trong cùng một deck.

---

## 8.2 Trả lời câu hỏi: bài đang có nói gì về các mô hình đang dùng?

Đã grep toàn bộ 14 file text trong `docs\References\Papers\`.

| Mô hình dùng | Có trong bài nào (đếm hit) | Trích dẫn dùng được | Đủ để trích? |
|---|---|---|---|
| **SASRec / SASRec+** | `[1]` TOIS2022 (37 hit) · `[3]` RecSys'25 (13 hit) | `[1]` L199–200, L544–558: chọn BPR/NeuMF/SASRec/LightGCN làm baseline; `[3]` L601–605: "SASRec+ … full cross-entropy loss (CE) over the entire item catalog" + repo L609–610 | ✅ Có. `[3]` là nguồn chuẩn nhất vì project dùng đúng bản CE của họ |
| **ItemKNN** | `[2]` TORS2024 (**25 hit**) · `[4]` RecSys'26 (4 hit) | `[2]` L302, L317: "two baseline algorithms, MostPopular and ItemKNN"; L947: kết luận bias phụ thuộc ItemKNN; `[4]` L242–248: "ItemKNN (implicit)", "ItemKNN (explicit)" | ✅ Có |
| **ALS (MF)** | `[4]` RecSys'26 (2 hit) · `[13]` J.BigData2019 (2 hit, **đã bỏ khỏi TLTK**) | `[4]` L246: "Implicit MF (ALS)"; L248: "Biased MF (ALS)" | ⚠️ Có tên, nhưng `[4]` chỉ dùng như biến thể so sánh, không phải bài gốc ALS |
| **MostPopular** | `[2]` (2 hit) · `[6]` UMAI (3) · `[7]` SIGIR'23 (2) · `[14]` ESWA (1) | `[2]` L302/L343: dùng làm baseline sàn | ✅ Có (nhưng MostPopular vốn không có bài gốc) |
| **Random** | **0 hit** toàn bộ corpus | — | ❌ Không có. Đây là sàn tầm thường, không cần bài; phải **khai báo là "sàn tầm thường, không viện dẫn"** thay vì để trống |

**Kết luận:** 4/5 mô hình đã có bài trong corpus. Nhưng **thiếu bài gốc của từng mô hình** — thứ thầy thường đòi khi nói "mô hình kinh điển phải có bài báo tương ứng". Corpus hiện chỉ có bài *về đánh giá*, các bài đó *dùng* mô hình chứ không *đề xuất* mô hình.

Bài gốc cần bổ sung (đề xuất, **phải verify DOI qua Crossref/OpenAlex trước khi đưa vào slide**, không lấy từ trí nhớ):

| Mô hình | Bài gốc | Venue dự kiến |
|---|---|---|
| ItemKNN | Sarwar, Karypis, Konstan, Riedl — *Item-based collaborative filtering recommendation algorithms* | WWW 2001 |
| ALS (implicit MF) | Hu, Koren, Volinsky — *Collaborative Filtering for Implicit Feedback Datasets* | ICDM 2008 |
| SASRec | Kang, McAuley — *Self-Attentive Sequential Recommendation* | ICDM 2018 |
| (dự phòng) BPR | Rendle et al. — *BPR: Bayesian Personalized Ranking* | UAI 2009 |
| (dự phòng) LightGCN | He et al. — *LightGCN* | SIGIR 2020 |

Các bài này **đã nằm trong danh mục tham khảo của `[1]`** (`[19]` LightGCN, `[27]` SASRec, `[38]` BPR) → trích dẫn bậc hai hợp lệ, không phải bịa.

Quy tắc trình bày: tách rõ 2 nhóm trong TLTK —
- **Nhóm A — bài về bài toán/đánh giá** (10 bài hiện có): dùng cho gap.
- **Nhóm B — bài gốc của mô hình** (3–5 bài): dùng cho "baseline có nguồn".

---

## 8.3 Định nghĩa lại đầu vào / đầu ra (nội dung lõi cần đưa lên slide)

**Đầu vào (một câu, một dòng):**
> Bảng tương tác `(userId, movieId, rating, timestamp)` — MovieLens ml-25m, 25.000.095 dòng, 162.541 user, 59.047 phim, 1995-01-09 → 2019-11-21.

**Đầu ra (4 vật thể, mỗi vật thể có tên file):**

| # | Vật thể | Định dạng | Nội dung | Đã có? |
|---|---|---|---|---|
| O1 | **Phiếu chẩn đoán split** (`audit_report.json`) | JSON, 1 bản ghi / split | `sli_user_pct`, `sli_global_pct`, `eval_users`, `unseen_item_pct`, `verdict` (SAFE / WARN / BLOCK) | ⚠️ số đã có trong `Metrics.md`; **chưa đóng gói thành 1 file/1 thẻ** |
| O2 | **Thước đo SLI** | công thức + code `src/audit/leakage.py` | SLI tương đối theo user, 3 ngưỡng | ✅ có |
| O3 | **Giao thức audit 3 bước** | bảng 3 bước + ngưỡng 1,20 | SLI trước → số user → chặn so sánh | ✅ có |
| O4 | **Pipeline tái lập + dashboard** | `scripts/`, `runs/`, Streamlit | chạy lại 1 lệnh ra cùng số | ✅ có |

**Phép so sánh để người nghe hiểu ngay (dùng trong notes):**
> Đề tài phân loại ảnh nội soi trả ra **1 nhãn cho mỗi ảnh**.
> Đề tài này trả ra **1 nhãn cho mỗi cách chia dữ liệu**: `SAFE` / `WARN` / `BLOCK`, kèm con số SLI.
> Không huấn luyện mô hình mới; mô hình chỉ là **que thử** để lộ rò rỉ.

---

## 8.4 Cấu trúc slide mới — 17 slide (giới hạn cho phép 10–20)

| # | Slide | Thay đổi | Nguồn |
|---|---|---|---|
| 1 | Tiêu đề | Thêm 1 dòng: "Đầu vào: bảng chấm 25 triệu dòng · Đầu ra: phiếu chẩn đoán cho từng cách chia" | `01` §1 |
| 2 | Bố cục 20/30/45/5 | Giữ | HD p2 |
| 3 | DIKW | Sửa `8,76%`; đổi `158.688/6.219/96.003` → `158.626/6.214/95.977` (ALS) | `Metrics.md` L355–359 |
| 4 | Phương pháp tư duy | Đổi `0,2584 → 0,0474` thành `0,2581 → 0,0469` (một đường duy nhất) | `Metrics.md` |
| 5 | W5H2 | Thêm dòng **How much / Output** nêu 4 vật thể O1–O4 | §8.3 |
| **6** | **MỚI — Đầu vào → Đầu ra** | 1 khối input (4 trường + 25M) → 3 khối xử lý → 4 thẻ output O1–O4. Kèm phép so sánh "nhãn cho mỗi ảnh" vs "nhãn cho mỗi split" | §8.3 |
| 7 | Kiểm tra tài liệu (10 bài) | Giữ; ghi rõ "Nhóm A" | `03` §0B |
| **8** | **MỚI — Baseline ↔ bài báo** | Bảng 5 dòng: mô hình · tầng · bài gốc (DOI) · bài trong corpus dùng nó · đã chạy chưa | §8.2 |
| 9 | Ma trận tổng hợp + gap | Giữ (đổi số thứ tự) | `04`, `07` |
| 10 | Tiêu đề + GO/SO + RQ | Giữ | `08` §6 |
| 11 | FINER | Giữ | `01` §5 |
| 12 | Quy trình 4 tầng | Vẽ lại: thêm **làn Input bên trái, làn Output bên phải** trên `fig_architecture.png` | `Architecture.md` |
| 13 | Chỉ số + đối chuẩn | Giữ; thêm cột "bài gốc" tham chiếu slide 8 | `08` §1, `05C` §1 |
| 14 | Kết quả sơ bộ | Giữ số; thêm 1 thẻ verdict SAFE/WARN/BLOCK | `Metrics.md` |
| 15 | Hiệu quả / ROI / kế hoạch | Đổi `158.688/6.219/96.003` → ALS hoặc ghi rõ "số user của Popularity" | §8.1 |
| 16 | Tự đánh giá | Giữ | `Drawbacks.md` |
| 17 | Q&A + TLTK | Tách 2 nhóm A/B; thêm DOI 3 bài gốc | §8.2 |

**Phương án B nếu hội đồng bắt buộc 15 slide:** gộp S6 vào S5 (W5H2 thêm cột "Output"), gộp S8 vào S13. Mất ~40% độ rõ của D1/D5.

---

## 8.5 Sửa script — việc cụ thể

### `scripts/generate_slides.py`
1. **Số liệu:** tạo hằng số đầu file, không rải rác literal:
   ```python
   NDCG = {"random80_20": "0,2581", "temporal_global": "0,1332", "leave_one_out": "0,0469"}
   EVAL_USERS_ALS = {"random80_20": "158.626", "temporal_global": "6.214", "leave_one_out": "95.977"}
   EVAL_USERS_POP = {"random80_20": "158.692", "temporal_global": "6.219", "leave_one_out": "96.003"}
   ```
   Rồi thay L403, L416, L500, L514, L700, L722, L748 bằng biến. Chấm dứt D3 + lỗi phụ.
2. **L401:** `"8,76% phim kiểm tra là phim người đó chưa chấm."` → `"8,76% dòng test trỏ tới phim chưa từng có trong train (item cold-start)."`
3. **L455 / L489:** `0,2584 → 0,0474` → `0,2581 → 0,0469`; xoá câu "Không trộn số 0,2581 → 0,0469…" ở L491 (hết ý nghĩa sau khi hợp nhất).
4. **Thêm hàm** `slide_input_output()` (S6) và `slide_baseline_papers()` (S8); dùng lại `add_card`, `add_stat_card`, `add_table` sẵn có.
5. **`verify_layout()`:** thêm assert không còn literal `0,2584`, `0,1364`, `0,0474`, `158.688`, `6.219`, `96.003` trong text shape → chặn tái phát.
6. **Cỡ chữ:** xem §8.6.

### `scripts/generate_slide_figures.py`
1. `fig_sli.png` đang **hardcode** `sli_global = [1.0000, 0.0000, 0.999988]`, `sli_user = [0.989084, …]`. Đổi sang đọc từ `runs\…\outputs\comparison.json` / `audit_*.json`; nếu thiếu file thì **fail to**, không vẽ số cũ.
2. `fig_interaction.png` đã đọc từ `runs\20261120_012944_09_compare_and_reversal_21d0811a` — giữ, nhưng đổi hardcode path thành tham số `--run`.
3. **Thêm** `fig_io.png`: 1 làn vào (4 trường) → 3 khối → 1 làn ra (4 vật thể). Dùng cho S6.
4. **Sửa** `fig_architecture.png`: thêm nhãn `INPUT` / `OUTPUT` hai bên; hiện chỉ có 4 tầng, không có vào/ra.
5. Bỏ `plt.rcParams.update({"font.size": 15})` đặt giữa file (rò sang figure sau) → đặt trong `with plt.rc_context()`.

---

## 8.6 Hai quyết định cần chốt trước khi code

| # | Vấn đề | Lựa chọn A | Lựa chọn B |
|---|---|---|---|
| Q1 | **Cỡ chữ** — HD trang 3 ghi "≥ 24pt", deck hiện 9–15pt | Giữ 9–15pt, chấp nhận trừ điểm mỹ thuật, nội dung dày | Nâng ≥ 20–24pt: mỗi slide còn ≤ 3 dòng, **toàn bộ bảng số dời sang phụ lục** (thêm 3–4 slide phụ lục, không tính 17) |
| Q2 | **Số bài TLTK** | Giữ 10 bài nhóm A, thêm 3 bài gốc → **13 bài, 2 nhóm** | Chỉ thêm 3 bài gốc, cắt 3 bài nhóm A ít dùng (`[7]`, `[8]`, `[9]`) để giữ 10 |
| Q3 | **Đầu ra O1** (phiếu chẩn đoán JSON) | Sinh thật `audit_report.json` từ `runs/` bằng script nhỏ → có vật thể để demo | Chỉ mô tả trên slide, không sinh file |

Khuyến nghị: **Q1 = A** (nội dung trước, mỹ thuật sau; đã ghi hạn chế ở §5 checklist), **Q2 = A** (thầy đòi bài gốc cho từng mô hình, cắt bài sẽ hụt phần gap), **Q3 = A** (đây chính là thứ làm đề tài hết trừu tượng).

---

## 8.7 Thứ tự thực hiện (sau khi chốt Q1–Q3)

| Bước | Việc | Kiểm tra |
|---|---|---|
| 1 | Verify DOI 3 bài gốc qua Crossref; ghi vào `_manifest.json` + `03_Tai_lieu_tham_khao.md` §0C | DOI resolve, `/Creator` là nhà xuất bản |
| 2 | Tạo `audit_report.json` từ `runs/` (script `scripts/19_audit_report.py`) | 3 split × 5 field, verdict khớp ngưỡng |
| 3 | Sửa `generate_slide_figures.py`: đọc run, thêm `fig_io.png`, sửa `fig_architecture.png` | chạy lại sinh 4 PNG, không còn literal |
| 4 | Sửa `generate_slides.py`: hằng số, D3, D4, thêm S6 + S8, đánh số lại 1–17 | `verify_layout()` PASS, không literal cũ |
| 5 | Rebuild deck `PPNCKH_DeCuong_15slides.pptx` (đổi tên `…_17slides.pptx`) | 17 slide, footer `x / 17` |
| 6 | Cập nhật `Script_ThuyetTrinh_15Slides.md` → 17 slide | khớp số mới |
| 7 | Cập nhật `00_Slide_Plan.md` (= file này) mục 2, 3, 5 | footer, bảng cấu trúc |

> Không đụng `PPNCKH_DeCuong_15slides_Self-Adjustion.pptx` (deck cũ, đã đánh dấu lỗi thời ở §7).

---

# 9. Chốt phương án — 2026-11-24 (thay §8.4–8.7)

Ba quyết định đã chốt:

| Mã | Chốt | Hệ quả |
|---|---|---|
| Q1 | **Thêm slide để được cỡ chữ 20–24pt** | 15 → **20 slide chính + 4 phụ lục**; bảng dày dời hết sang phụ lục |
| Q2 | **13 bài, 2 nhóm A/B** | Nhóm A = 10 bài đánh giá/chia tập; Nhóm B = 3 bài gốc mô hình (DOI đã verify) |
| Q3 | **Sinh thật `audit_report.json`** | Thêm `scripts/19_audit_report.py`; là vật thể demo được |

> §8.4–§8.7 (bản 17 slide) **bị thay bởi mục này**.

---

## 9.1 Cấu trúc 20 slide chính — cỡ chữ 20–24pt

Quy tắc: title 30–32pt, thân card 20–24pt, **không quá 3 dòng/card, không quá 5 dòng/slide**. Mọi bảng > 5 dòng hoặc > 5 cột → phụ lục.

| # | Slide | Nội dung cốt lõi | Cỡ chữ thân |
|---|---|---|---|
| 1 | Tiêu đề | + 1 dòng: *Vào: bảng chấm 25.000.095 dòng · Ra: phiếu chẩn đoán cho từng cách chia* | 20 |
| 2 | Bố cục 20/30/45/5 | 4 thẻ | 22 |
| 3 | DIKW | 4 thẻ: Data → Info → Knowledge → Wisdom | 20 |
| 4 | Phương pháp tư duy | 3 thẻ: diễn dịch / quy nạp (chủ đạo) / suy đoán | 20 |
| 5 | W5H2 | 6 thẻ, mỗi thẻ 1 dòng | 20 |
| **6** | **ĐẦU VÀO là gì** | 1 ảnh bảng dữ liệu 4 cột + 4 số lớn (25.000.095 · 162.541 · 59.047 · 24,8 năm) | 22 |
| **7** | **ĐẦU RA là gì** | 4 thẻ O1–O4 kèm tên file: `audit_report.json` · `src/audit/leakage.py` · `GiaoThuc_3Buoc` · `runs/` + Streamlit | 20 |
| 8 | Tài liệu — Nhóm A | 3 số lớn: 10 bài · 9 CORE A*/A · 0 arXiv + bảng 3 dòng theo venue | 20 |
| **9** | **Baseline ↔ bài báo** | bảng 5 dòng: mô hình · tầng · bài gốc (DOI) · bài corpus dùng nó | 18–20 |
| 10 | Ma trận tài liệu | 5 dòng × 4 cột, **mỗi ô có số cụ thể** (xem §9.2) | 18 |
| 11 | Khoảng trống | 3 gạch đầu dòng + 1 câu Critical Gap | 22 |
| 12 | Tiêu đề + GO/SO/RQ | 4 thẻ SO + 5 dòng RQ→SO | 20 |
| 13 | FINER | 5 thẻ | 20 |
| 14 | Quy trình 4 tầng | ảnh có **làn INPUT trái / OUTPUT phải** | 20 |
| 15 | Chỉ số: SLI + NDCG | 2 thẻ công thức, 3 ngưỡng SLI | 22 |
| 16 | Baseline 3 tầng + tham số | 3 thẻ + 1 dòng repo/ngân sách tuning | 20 |
| 17 | Kết quả sơ bộ + verdict | bảng 5 dòng × 3 cột (NDCG 3 split) + 3 thẻ verdict SAFE/WARN/BLOCK | 20 |
| 18 | Hiệu quả · ROI · kế hoạch | 2 thẻ + bảng G1–G5 rút còn 3 cột | 20 |
| 19 | Tự đánh giá & giới hạn | 4 thẻ + 1 banner giới hạn | 20 |
| 20 | Q&A + TLTK | bảng 13 dòng chia 2 nhóm A/B (bảng nhỏ 14pt, chấp nhận) | 14 |

**Phụ lục (không tính 20, footer `A1/4`…):**
- **A1** — Bảng kết quả đầy đủ 5 mô hình × 3 split × 10 cột (NDCG/MRR/Đa dạng).
- **A2** — Bảng kiểm định 20 cặp: p, 95% CI, rank-biserial r.
- **A3** — Bảng tham số chi tiết từng mô hình + cấu hình máy.
- **A4** — Bảng 13 tài liệu đầy đủ: venue, năm, DOI, CORE/SCImago, vai trò.

Nếu slide 10 tràn khi để 20pt → tách thành 10a (S3, S4) và 10b (S5, S6, S12), tổng 21 slide.

---

## 9.2 Ma trận tài liệu — số cụ thể đã trích từ PDF (dùng cho slide 10)

Thầy yêu cầu "kết quả có con số rõ ràng chứ không trừu tượng". Đây là số **đọc trực tiếp từ bản nhà xuất bản**, kèm dòng để đối chiếu:

| Bài | Mô hình họ dùng | Phương pháp | Kết quả — SỐ CỤ THỂ | Dòng nguồn |
|---|---|---|---|---|
| **Ji, TOIS 41(3)** | BPR, NeuMF, SASRec, LightGCN | Thêm dần dữ liệu tương lai Y6→Y10, đo biến thiên HR@20/NDCG@20 | MovieLens-25M, test Y5→Y10: **SASRec NDCG@20 −5,4% … +16,8%**; **LightGCN −9,3% … +6,8%**; **BPR −6,3% … +5,5%**. Yelp: SASRec NDCG@20 **−29,0% … −0,6%**. Amazon-music: NeuMF NDCG@20 **+40,2% … +89,5%** | L999–1050 (Table 5) |
| **Daniil, TORS 2(1)** | ItemKNN, MostPopular, BPR, HPF, NeuMF, VAECF, SVD++ (11 thuật toán, Cornac) | 3 chiến lược chia × 4 cách chia nhóm user, đo %ΔGAP | NeuMF đẩy item cho nhóm Niche phổ biến gấp ~4 lần: **%ΔGAP = 399,1 và 399,6**. ItemKNN/MF cho **%ΔGAP âm** ở nhiều nhóm | L302, L518–522, L1223–1231 |
| **Gusak, RecSys '25** | SASRec+ (full CE), BERT4Rec, GRU4Rec | 8 dataset × LOO/GTS nhiều quantile, RePlay | Khảo sát 75 bài: **77,3% dùng LOO**, 16% GTS, 6,7% GTS cho next-item. GTS q0,9 chỉ phủ **10–44% user**; LOO phủ **100%**. Kendall τ giữa split **0,6–0,9**, Spearman **0,7–1,0**. NDCG@10 Beauty **0,022 → 0,040 (+81,8%)** | L279–281, L842, L992, L1864, L1856 |
| **Meng, RecSys '20** | NMF, BPR, NeuMF, VAECF, VBCAR, Triple2vec | 4 chiến lược chia, 230 mô hình, NDCG@10/Recall@10 | Tafeng NDCG@10: **NMF 0,0879 (LOO-item) → 0,1811 (temporal global) = 2,06×**; NeuMF **0,1738 → 0,3313 = 1,91×**; BPR **0,1347 → 0,2575**. Có hoán đổi hạng giữa các split | L594–641 (Table 3) |
| **Parajuli, RecSys '26** | ItemKNN (imp/exp), Implicit MF (ALS), Biased MF, fsSLIM | Kendall τ giữa xếp hạng mô hình của đánh giá thưa vs dày | τ chỉ **0,03–0,28**; nhiều ô CI chứa 0, ví dụ **τ=0,11 (−0,06; 0,28)**, **0,05 (−0,12; 0,21)** → không hội tụ | L459–513 (Table 2) |

Ba nhận xét in được lên slide:
1. Mọi bài đều **dùng ≥ 3 mô hình**; không bài nào chỉ 1 mô hình. Đề tài dùng 5 → hợp lệ.
2. Con số **cùng chiều**: chia khác nhau → chênh 1,9–2,1× (Meng), τ thấp (Parajuli). Đề tài đo được **5,5×** (0,2581→0,0469).
3. Không bài nào báo **chi phí vận hành** hay **SLI tương đối theo user** → cột hạn chế vẫn đứng.

---

## 9.3 Bảng Baseline ↔ bài báo (slide 9) — nội dung chính xác

| Mô hình | Tầng | Bài gốc (Nhóm B) | Bài trong corpus có dùng (Nhóm A) | Đã chạy |
|---|---|---|---|---|
| **Random** | Sàn | — (sàn tầm thường, **khai báo là không viện dẫn**) | — | ✅ |
| **MostPopular** | Sàn | — (không có bài gốc) | `[2]` Daniil TORS L302/L343 dùng làm baseline | ✅ |
| **ItemKNN (cosine)** | Kinh điển | Sarwar et al., WWW 2001, `10.1145/371920.372071` | `[2]` (25 lần) · `[4]` L242–248 | ✅ 503 s, 3 split |
| **ALS implicit** | Kinh điển | Hu, Koren, Volinsky, ICDM 2008, `10.1109/ICDM.2008.22` | `[4]` L246 "Implicit MF (ALS)" | ✅ rank 16, alpha 10 |
| **SASRec + CE** | SOTA | Kang & McAuley, ICDM 2018, `10.1109/ICDM.2018.00035` | `[1]` L199–200/L553 · `[3]` L601–605 + repo | ✅ GPU RTX 4050, 3 split |

Ghi chú phải nói trên slide: **`[1]` và `[3]` dùng SASRec làm baseline**, nên trích `[3]` cho *cấu hình CE* và bài gốc ICDM 2018 cho *kiến trúc*. Không nhập nhằng "tái lập bài báo" với "dùng mô hình của bài báo".

Nhóm B bổ sung 3 dòng vào `03_Tai_lieu_tham_khao.md` §0C; DOI đã verify Crossref ngày 2026-11-24.

---

## 9.4 Sửa `generate_slides.py` — danh sách việc

| # | Việc | Dòng hiện tại |
|---|---|---|
| 1 | Hằng số đầu file: `NDCG`, `EVAL_USERS_ALS`, `EVAL_USERS_POP`, `SLI` (dict theo split) | thêm sau L40 |
| 2 | Sửa định nghĩa `8,76%`: → "8,76% dòng test trỏ tới phim chưa từng có trong train (item cold-start)" | L401 |
| 3 | `0,2584 → 0,0474` → dùng `NDCG["random80_20"]` / `NDCG["leave_one_out"]` | L455, L489, L491 |
| 4 | `158.688/6.219/96.003` → `EVAL_USERS_ALS` (hoặc ghi rõ "số user của Popularity" nếu giữ Pop) | L403, L416, L514, L748 |
| 5 | Thêm `slide_input()` (S6), `slide_output()` (S7), `slide_baseline_papers()` (S9) | chen sau S5 |
| 6 | Thay bảng ma trận 5 dòng bằng nội dung §9.2 | S? hiện L543 |
| 7 | Tách bảng kết quả 10 cột → slide 17 chỉ 3 cột; bảng đầy đủ sang A1 | L718–730 |
| 8 | Tăng cỡ chữ: `body_size` 20–22, `title_size` 24–26 cho card; bảng chính 18–20 | toàn file |
| 9 | `verify_layout()`: thêm assert không còn literal `0,2584|0,1364|0,0474|158.688|6.219|96.003`; assert `body_size >= 18` cho shape trên slide chính 1–20 | L828 |
| 10 | Đổi tên output → `PPNCKH_DeCuong_20slides.pptx`, footer `x / 20` | L? footer |

## 9.5 Sửa `generate_slide_figures.py`

| # | Việc |
|---|---|
| 1 | `fig_sli.png`: bỏ hardcode `[1.0000, 0.0000, 0.999988]` / `[0.989084,…]`, đọc từ `runs\…\outputs\comparison.json`; thiếu file → raise |
| 2 | Thêm `--run` CLI, mặc định `20261120_012944_09_compare_and_reversal_21d0811a` |
| 3 | **Mới `fig_io.png`**: làn INPUT (4 trường + 25M) → 3 khối xử lý → làn OUTPUT (4 vật thể O1–O4) |
| 4 | `fig_architecture.png`: thêm nhãn INPUT trái / OUTPUT phải; 4 tầng giữ nguyên |
| 5 | `plt.rcParams.update({"font.size":15})` → đặt trong `plt.rc_context()` (đang rò sang figure sau) |
| 6 | Cỡ chữ hình ≥ 16pt để đọc được khi chiếu |

## 9.6 Sinh `audit_report.json`

Script mới `scripts/19_audit_report.py`:
- Đọc `runs/*/outputs/comparison.json` + `als_summary.json`.
- Xuất `docs/Project/Main/Presentation/Slides/audit_report.json`:
  ```json
  {"split":"temporal_global","sli_user_pct":0.0,"sli_global_pct":0.0,
   "eval_users":6214,"unseen_item_pct":8.76,"verdict":"SAFE",
   "reason":"SLI < 0,05 nhưng eval_users chỉ bằng 3,9% của random80_20 → BLOCK khi so sánh"}
  ```
- Ngưỡng lấy đúng `08_Tao_tac_SLI_va_giao_thuc_audit.md` §1: `<0,05` SAFE · `0,05–0,30` WARN · `≥0,30` BLOCK; cộng điều kiện tỷ lệ user `>1,20` → BLOCK.
- Verdict phải khớp số trong bảng slide 17.

## 9.7 Thứ tự thực hiện

| Bước | Việc | Kiểm tra |
|---|---|---|
| 1 | Thêm 3 bài Nhóm B vào `03_Tai_lieu_tham_khao.md` §0C + `_manifest.json` | 3 DOI resolve (đã verify) |
| 2 | Viết `scripts/19_audit_report.py`, sinh `audit_report.json` | 3 split × 6 field, verdict khớp §9.6 |
| 3 | Sửa `generate_slide_figures.py` (5 việc §9.5) | sinh 4 PNG, không còn literal |
| 4 | Sửa `generate_slides.py` (10 việc §9.4) | `py_compile` OK, `verify_layout()` PASS |
| 5 | Rebuild `PPNCKH_DeCuong_20slides.pptx` | 20 slide + 4 phụ lục, footer đúng, không tràn |
| 6 | Trích text ra `.extracted.txt`, đối chiếu số | grep không còn `0,2584/158.688` |
| 7 | Cập nhật `Script_ThuyetTrinh_15Slides.md` → 20 slide | khớp số mới |
| 8 | Cập nhật `Plan.md` §2/§3/§5 + `00_Slide_Plan.md` (cùng file) | checklist cỡ chữ đổi ⚠️ → ✅ |

> Không đụng `PPNCKH_DeCuong_15slides_Self-Adjustion.pptx`. Deck cũ `PPNCKH_DeCuong_15slides.pptx` giữ lại làm bản 15 slide dự phòng nếu hội đồng giới hạn số slide.

---

# 10. Trạng thái triển khai — 2026-11-25

## 10.1 Đã làm

| Việc | Kết quả |
|---|---|
| `scripts/19_audit_report.py` | Sinh `docs/Project/Main/Presentation/Slides/audit_report.json`, 3 split × 6 field. SLI_user: random 98,92% · temporal 0,00% · LOO 0,00%. `verdict` theo SLI: BLOCK / SAFE / SAFE; khi so chéo cả 3 đều BLOCK. `eval_users_ratio_max_over_min = 25,5272`. |
| `scripts/generate_slide_figures.py` | Đọc `data_level_audit.json` + `comparison.json`; có `--run`; sinh `fig_architecture.png`, `fig_io.png`, `fig_sli.png`, `fig_interaction.png`. Không còn mảng SLI hardcode. |
| `scripts/generate_slides.py` | Sinh `PPNCKH_DeCuong_20slides.pptx`: 20 slide chính + 4 phụ lục. `py_compile` OK; `verify_layout()` PASS; footer `x / 20`. Chặn literal `0,2584 / 0,1364 / 0,0474 / 158.688 / 6.219 / 96.003`. |
| `03_Tai_lieu_tham_khao.md` §0C + `_manifest.json` | Thêm 3 bài Nhóm B, DOI verify Crossref 2026-11-24. Manifest 17 entries; 3 bài mới `referenced-not-downloaded`. |
| `Script_ThuyetTrinh_15Slides.md` | Đổi nội dung sang 20 slide, kèm 5 câu Q&A đã cập nhật số liệu. Giữ tên file cũ để không gãy liên kết. |

## 10.2 Kiểm tra

```powershell
cd 'd:\Master Exers\Big Data\Recomendation_System'
python -m py_compile scripts\generate_slides.py
python scripts\generate_slide_figures.py
python scripts\generate_slides.py
python -c "import json; m=json.load(open(r'docs\References\Papers\_manifest.json',encoding='utf-8')); print(len(m))"
```

Kết quả chốt: `OK ... PPNCKH_DeCuong_20slides.pptx ... 24 slides (20 main + 4 appendix), checked`; manifest `17`. Text trích ở `docs/Project/Main/Presentation/Slides/PPNCKH_DeCuong_20slides.extracted.txt`.

## 10.3 Còn lại

- Chưa mở PPTX trong PowerPoint/LibreOffice để soi trực quan slide 6, 7, 9, 10, 17, A1, A2.
- Chưa đo bộ nhớ, chưa chạy thêm seed, chưa chạy Nemenyi — đã khai báo giới hạn ở slide 19.
- Không đụng `PPNCKH_DeCuong_15slides_Self-Adjustion.pptx`; bản 15 slide cũ giữ làm dự phòng.
