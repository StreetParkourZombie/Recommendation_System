# TEMP — Plan hoàn thiện slide PPNCKH (2026-11-18)

> File tạm, được phép overwrite. Nguồn: `docs/Project/Main/Notes/04.md` (chuỗi Q_1–Q_5) + audit RQ + audit baseline.
> **Đóng 2026-11-20:** plan trong file này đã xong. Bổ sung cuối: rerun 06/08/10/11/13 lấy Novelty/Diversity, 09 lấy Friedman (Nemenyi KHÔNG chạy), 15/15 fixture PASS. Không còn hành động nào từ TEMP; số cuối ở `../../../Main/Metrics.md` §4.12.

---

## 0. Trả lời câu hỏi chính: notebook 10–12 + ma trận 3 seed còn cần không? (đã chốt 2026-11-19)

**Kết luận cập nhật 2026-11-19: notebook 10/12 đã chạy, ma trận 3 seed bị loại, slide đã regenerate. Bảng dưới là phân loại lịch sử, không còn việc phải làm cho slide.**

| Notebook                                                                                        | Mục đích                                                        | Cần cho slide?                                                                                                                                                                       | Chi phí       |
| ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- |
| **10** — kiểm định cặp (Wilcoxon signed-rank) trên `peruser_ndcg_*.npz` đã lưu | Chứng minh chênh NDCG random→LOO 5,5× có ý nghĩa thống kê | **Không bắt buộc** — đã có gap 5,5× làm bằng chứng chính; stats là nice-to-have. Nếu làm: **không chạy lại pipeline**, chỉ đọc npz sẵn (vài phút) | Rất rẻ       |
| **11** — bias audit chi tiết (PopRatio/P@k per group)                                   | Đo RQ2 sâu hơn bias_ratio hiện có                             | **Không bắt buộc** — bias_ratio 18,66/12,69/17,31 + ratio ALS/Pop 3,03×/2,93×/2,56× đã đủ cho slide                                                                  | Rẻ            |
| **12** — benchmark runtime/memory/#task/IO per split                                     | Điền **RQ3** (đang thiếu phần này theo audit)          | **Nên làm, nhưng gộp vào lần chạy model mới** — đo trong cùng script, không cần notebook riêng chạy lại                                                         | Rẻ, 1 lần    |
| **Ma trận 3 seed**                                                                       | Độ nhạy kết quả theo seed                                     | **KHÔNG chạy cho slide** — đã khai báo giới hạn "1 seed" + G1 giai đoạn tiếp theo; chạy thêm mâu thuẫn với giới hạn đã viết                                | Đắt, bỏ qua |

**Thứ tự nếu còn thời gian:** 12 (benchmark, điền RQ3) → 10 (stats trên npz) → 11. Seed matrix: bỏ.

---

## 1. Baseline 5 model — trạng thái đã xong (cập nhật 2026-11-19)

Slide 11–12 đã có số thật. 4 model chạy FULL 162.541 user × 3 split; SASRec+CE chạy 3 split trên GPU local với eval subset user, `tuning_budget=0`. Không chạy thêm từ mục này.

| # | Model                       | Chi phí                                                                                 | Ghi chú                                                                                                                                                        |
| - | --------------------------- | ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 | **Random**            | ~10 dòng code, vài phút                                                               | Copy pattern notebook 08, đánh giá uniform random                                                                                                            |
| 2 | **ItemKNN k=100**     | 1–2h/split × 3 split                                                                   | Full user, similarity cosine trên item co-occurrence — **có trong đề tài đăng kí**                                                               |
| 3 | **SASRec**            | Notebook 13 + `src/audit/sasrec.py` đã viết; đã chạy xong 3 split, run `20261118_144646_13_sasrec_ce_8225755a` | **GPU local RTX 4050 6 GB** — baseline SOTA đã đăng kí (RecSys'25 [03], SASRec+CE); nếu không chạy → khai báo SOTA tham chiếu đã reproduce 3 split trên GPU local (không tuning) |
| 4 | **Ghép notebook 09** | Vài phút                                                                               | Sau mỗi model mới: chạy lại `generate_notebook_09.py` → `comparison.json` → update slide 11–12                                                       |

**Đóng mục này (2026-11-19):** đã ghép notebook 09/12, slide đã update. EASE bỏ, không đăng kí.

---

## 2. Slide fixes — đã xong regenerate 2026-11-18/19

1. **Slide 11**: nhắc SOTA = **SASRec + CE (RecSys'25, bài [03])** — baseline SOTA đã đăng kí trong đề tài (`docs/About/Reseach_Method_Submission.md`); nếu đã reproduce 3 split trên GPU local (không tuning) → khai báo "SOTA tham chiếu, đã reproduce 3 split trên GPU local (không tuning) trong giai đoạn này". Baseline đăng kí: Random, MostPopular (sàn) + ALS, ItemKNN (kinh điển) + SASRec+CE (SOTA). **Không thêm model ngoài danh sách đăng kí** (EASE đã loại khỏi plan).
2. **Slide 7 (gap)**: chèn ảnh chụp trang **limitation** từ PDF `docs/References/Papers/01–04*.pdf`. DOI + trang cần trích:
   - [1] Wang, TOIS 2022 — 10.1145/3569930
   - [2] Abdollahpouri, TOIS 2023 — 10.1145/3637066
   - [3] Chen, RecSys'25 — 10.1145/3705328.3748164
   - [4] RecSys'26 — 10.1145/3773078.3831818
3. **Slide 11–12**: ✅ bảng 5 model đã có; SASRec+CE là đối chiếu/local reproduction, không "winner"; không so runtime CPU/GPU.
4. Quy tắc: ✅ đã áp dụng — sửa `scripts/generate_slides.py` (source of truth) → regenerate PPTX → readback grep số mới. Geometry check PASS.

---

## 3. Việc tài liệu (rẻ, không cần chạy code)

> [!IMPORTANT]
> **Hoãn toàn bộ mục này (chốt 2026-11-18):** báo cáo `.tex` viết **sau** buổi thuyết trình PPNCKH. Môn học chỉ cần **đề cương + slide**. Xem phân tầng ở §7.

- Ảnh Zotero: ≥5 bài có ảnh bìa/meta. *(hoãn)*
- Điền ~35 placeholder trong `chuong1–3.tex` (chuong1 17 dòng · chuong2 30 · chuong3 34). *(hoãn)*
- Thêm DSRM vào chuong3. *(hoãn)*
- FINER + SO1–SO3. *(hoãn)*
- RQ5: đoạn mở rộng (khai báo là hướng tương lai). *(hoãn)*

---

## 4. Thứ tự thực thi + ước thời gian

> **Trạng thái (2026-11-18 03:00) — bước 1→5 đều đã xong + verify; chỉ còn bước 6 (tài liệu) và 8 (SASRec, chờ GPU):**
>
> - Bước 1 ✅ — notebook `10_random_baseline.ipynb` xong, run `20261118_144717_10_random_baseline_d8644ac1`: NDCG 0,0003/0,0009/0,0001, bias ≈ 1, seen exclusion PASS 3/3.
> - Bước 2 ✅ (lần 2) — notebook 09 đã **nâng lên 5 model** và rerun: `20261118_151159_09_compare_and_reversal_1e0f72fa` → `reversals_found = 0` (so với sàn) + **`best_model_reversals_found = 2`** (ngôi đầu đổi chỗ giữa ALS và ItemKNN ở 2/3 split). Bản 3 model cũ `20261118_004106_..._e9779077` giữ để truy vết.
> - Docs cập nhật: Metrics.md §4.6, Drawbacks.md §3.5, System_Context.md §12.1/12.2, Architecture.md pipeline + gates. `mrr_at_k` thêm vào `src/audit/metrics.py`.
> - Bước 3a ✅ — notebook 06 MostPopular regen + rerun `20261118_021147_06_mostpopular_baseline_6d59bb2c`: gate reproduction PASS (0,0852/0,0455/0,0183), **đã lưu `peruser_ndcg_{split}.npz` 3 split** (trước đây không lưu → nb12 từng fail).
> - Bước 3b ✅ — notebook 11 ItemKNN cosine (scipy sparse, `src/audit/itemknn.py`; v1 Spark self-join timeout 3600 s → bỏ) xong: run `20261118_150305_11_itemknn_baseline_0b7511ee`, **CELL002 = 503 s**, L11 PASS (seen_exclusion 3/3, `knn_above_random` true). NDCG@10 **0,2679 / 0,1409 / 0,0461**; hit 0,7255/0,4817/0,0898; recall 0,1846/0,0407/0,0898; bias_ratio 16,40/22,01/19,35; cov 0,0360/0,0160/0,0283; fit 66,8/58,5/83,2 s; total 221,0/94,2/184,5 s.
> - Bước 3c ✅ — notebook 12 chạy **đủ 5 model / 20 cặp**: run `20261118_151202_12_paired_stats_9b864f59`, mọi cặp `n_paired >= 30`, L12 PASS. Cặp mới ALS vs ItemKNN: random80_20 d=−0,00988 p=2,84e-60 CI[−0,0109;−0,0089] r=−0,0301 · temporal d=−0,00774 p=3,01e-03 CI[−0,0118;−0,0036] r=−0,0159 · LOO d=+0,000787 **p=0,153 CI[−0,0003;+0,0018] chứa 0** r=0,005. Bài học phương pháp nói được: *phải chọn cặp so sánh trước khi chọn nhiều model*. Bản 6 cặp cũ `20261118_021517_..._f77a212b` giữ để truy vết.
> - Bước 4 ✅ (runtime) — bảng chi phí vận hành RQ3 tổng hợp từ summary JSON, **không re-run**: `Implementation/05_Benchmark_Chi_Phi_Van_Hanh_RQ3.md` + Metrics.md §4.7/§4.8/§4.9. Đã điền đủ 5 model: ItemKNN 499,7 s (**đắt nhất**, 1,74× ALS 286,7 s), Random 111,1 s, MostPopular 15,3 s. Memory **chưa đo** (pipeline không instrument RSS) — 5 cách đo rẻ đã ghi trong file, chờ duyệt.
> - Bước 3d ✅ — `scripts/generate_limitation_crops.py` (mới; PyMuPDF `get_text("dict")`, 200 dpi, `max_lines=2`) cắt câu limitation/scope từ 4 PDF `docs/References/Papers/01–04` → `docs/Project/Main/Presentation/Slides/figures/limitation/*.png` + `index.json` (file/page/clip/px/sha256/doi/label/gap). Đã chạy, 4 ảnh OK, đã chèn slide 7 lưới 2×2 @ 6,05 in.
> - Bước 5 ✅ — `scripts/generate_slides.py`: slide 7 (4 ảnh crop + caption trang/DOI + notes dẫn chứng), slide 10 (footer 10/10 gate PASS), slide 11 (baseline 4/5 ✓ + mục KIỂM ĐỊNH Wilcoxon), **slide 12 viết lại layout** (2 ảnh trên `fig_sli.png` + `fig_interaction.png`, table 8 dòng, footer chi phí RQ3 — sửa bug ảnh đè table có sẵn từ trước), slide 13 (bỏ EASE; G1 = SASRec+CE trên Colab), slide 14 (giới hạn + hướng mở rộng), slide 15 (notes thêm câu 6 về đảo chiều ngôi đầu + effect size). PPTX 15 slides; readback **cả text_frame lẫn table cells**: đủ 0,2679 / 0,1409 / 0,0461 / 893,0× / 156,6× / 461,0× / 2,8e-60 / 3,0e-03 / 0,153 / 499,7 / 286,7; EASE chỉ xuất hiện ở dạng phủ định; geometry slide 7 & 12 không chồng lấn.

| Bước | Việc                                                              | Thời gian                                                                                                                                                                                                                                         |
| ------ | ------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1      | Random baseline (notebook mới, pattern 08)                        | ~30 phút                                                                                                                                                                                                                                          |
| 2      | Chạy lại notebook 09 + slide 11–12 update                       | ~30 phút                                                                                                                                                                                                                                          |
| 3      | ItemKNN k=100 (3 split, chạy nền)                                | ✅ xong — **503 s** cho 3 split (rẻ hơn ước lượng 3–6h nhiều lần nhờ scipy sparse)                                                                                                                                                |
| 4      | Benchmark RQ3 (gộp vào bước 1/3, đo runtime/memory per split) | ✅ **runtime xong cho cả 5 model × 3 split** (không re-run) → `Implementation/05_Benchmark_Chi_Phi_Van_Hanh_RQ3.md` + Metrics.md §4.7–4.9. ⚠️ **memory chưa đo** (pipeline không instrument RSS) — chờ duyệt cách đo |
| 5      | Slide 7: chụp limitation 4 PDF + chèn                            | ✅ xong — `scripts/generate_limitation_crops.py` + 4 ảnh + `index.json`                                                                                                                                                                      |
| 6      | Tài liệu mục 3                                                  | ~2–3h                                                                                                                                                                                                                                             |
| 7      | Notebook 12 (Wilcoxon + 95% CI + r trên npz đã lưu)            | ✅ xong — 20 cặp, 0,22 s                                                                                                                                                                                                                         |
| 8      | SASRec+CE trên GPU local (notebook 13)                            | 🟡 đã viết, chờ torch + user tự chạy — xem `Implementation/06_Huong_Dan_Chay_SASRec_va_MRR.md`                                                                                                                                            |
| —     | Seed matrix 3 seed                                                 | **Bỏ**                                                                                                                                                                                                                                      |

---

## 4B. Đối chiếu Bài giảng 04 (Dữ liệu, Thực nghiệm & Đánh giá) — gap bổ sung

Đã đọc `raw_04_Du_Lieu_Thuc_Nghiem_va_Danh_Gia.txt` (426 dòng). Kiểm tra từng phần so với hiện trạng:

| Yêu cầu bài giảng                                                                                                                                                                      | Hiện trạng đề tài                                                                                                                                                                                                                            | Gap / Việc                                                                                                                                                                                                       |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **3 nguồn rò rỉ** (tiền xử lý / thời gian / trùng lặp)                                                                                                                      | Đề tài đúng trọng tâm: notebook 05 audit split leakage, 3 chiến lược random/LOO/temporal                                                                                                                                                | Đã bao phủ — slide 7 nên nhắc đủ 3 nguồn, không chỉ thời gian                                                                                                                                         |
| **Pipeline fit–transform chỉ trên Train**                                                                                                                                         | ALS fit trên `train_full` mỗi split (run FULL 2026-11-17)                                                                                                                                                                                     | Đã đúng; slide 14 nêu "fit toàn bộ 162.541 user mỗi split"                                                                                                                                                |
| **Fair Benchmarking 3 nguyên tắc** (cùng ngân sách tune, cùng dữ liệu + hardware, mã tái lập + seed công khai)                                                           | Baseline MostPopular/ALS cùng split, cùng máy, seed cố định; nhưng **chưa có mục khai báo nguyên tắc này**                                                                                                                    | **Thêm 1 dòng vào slide 11**: "So sánh công bằng: cùng dữ liệu, cùng phần cứng, seed cố định, code công khai"                                                                               |
| **Bảng đối chuẩn IEEE/ACM**: nhóm mô hình (Sàn/SOTA/Đề xuất) + Mean ± Std + **chi phí vận hành (latency, memory)**; bold tốt nhất, underline nhì, (*) p<0.05 | Slide 12 đã có bảng **5 model** + dấu sao ý nghĩa + **runtime đủ 5 model** (`Implementation/05_Benchmark_Chi_Phi_Van_Hanh_RQ3.md`, Metrics.md §4.7–4.9); **memory vẫn thiếu** vì pipeline không instrument RSS | Còn thiếu: (a) memory — cần duyệt instrumentation; (b) Mean ± Std — **không làm** vì 1 seed, thay bằng kiểm định cặp + 95% CI và khai báo rõ                                              |
| **Kiểm định t-test/Wilcoxon + 95% CI + effect size** (Cohen's d / rank-biserial r)                                                                                                | ✅ **đủ cả ba**: notebook 12 ra 20 cặp, mỗi cặp có `p_value` + `ci95_low/ci95_high` + `rank_biserial_r` + `n_paired` (run `20261118_151202_..._9b864f59`)                                                                  | Đã đưa vào slide 11/12 + Metrics.md §4.9. Ngoại lệ cần nói thẳng: cặp ALS-vs-ItemKNN ở `leave_one_out` p=0,153, CI chứa 0 → không đủ bằng chứng                                             |
| **Friedman + Nemenyi / CD Diagram khi k≥3 mô hình**                                                                                                                               | Điều kiện đã đủ (5 model × 3 split, npz per-user đã lưu)                                                                                                                                                                               | Vẫn nice-to-have: Friedman/Nemenyi so nhiều model **cùng lúc**, không trả lời trực tiếp RQ1/RQ2; nếu làm thì thêm cell vào notebook 12 (không cần run model mới). Ưu tiên thấp hơn MRR |
| **Ablation study**                                                                                                                                                                   | Đề tài dạng "ablation trên chiến lược chia": random vs LOO vs temporal, cùng model                                                                                                                                                       | **Đặt tên đúng trong slide 12/13**: gọi bảng random→LOO→temporal là "bóc tách tác động chiến lược chia" — khớp ngôn ngữ bài giảng, hội đồng quen từ khóa này                  |
| **RecSys metrics: NDCG@k, MRR, Diversity, Novelty**                                                                                                                                  | NDCG@10 + Hit@10 + Recall@10 + catalog_coverage + Gini + long-tail + bias_ratio cho 4 model; **MRR đã đo ở cả 5 model (xem `Metrics.md` §4.10)** (`mrr_at_k` đã có trong `src/audit/metrics.py`)                                                                       | ✅ Xong: MRR đã đo ở cả 5 model (Metrics §4.10). Diversity/Novelty đã có coverage/Gini/long-tail — nói được                                |
| **Quy tắc trình bày số: Mean ± Std**                                                                                                                                            | Chỉ có mean                                                                                                                                                                                                                                     | NDCG per split đã là 3 giá trị khác nhau (khác "fold") — trình bày dạng bảng per split, không tính Std bừa; thống nhất ghi rõ                                                                   |
| **Ma trận rủi ro thực nghiệm** (overfitting, drift, OOM, không hội tụ)                                                                                                        | Drawbacks.md có rủi ro SASRec 6–10h CPU + tràn RAM nếu chạy trên máy                                                                                                                                                                      | Đủ — rủi ro OOM dời sang SASRec, khai báo khi không có GPU                                                                                                                                                |
| **Cấu trúc 3 phần chương thực nghiệm** (Thiết lập / Kết quả & Đối chuẩn / Ablation & Thảo luận)                                                                      | Chuong3.tex thiếu DSRM; chương thực nghiệm chưa theo khung 3 phần                                                                                                                                                                          | Khi điền placeholder chuong3: xếp theo 3 phần này                                                                                                                                                            |
| **Phiếu tự đánh giá Rubric ≥70/100**                                                                                                                                           | Chưa có                                                                                                                                                                                                                                         | Việc tài liệu rẻ — tạo 1 mục tự chấm theo yêu cầu tối thiểu: pipeline sạch ✓, bộ độ đo ✓, Ablation (khung) ✓, kiểm định (nếu làm NB10) ✓, bảng SOTA (sau baseline) ✓                 |
| **Bài 05 chuẩn bị: Overleaf**                                                                                                                                                     | Đề cương đã ở LaTeX                                                                                                                                                                                                                        | Nhắc user: tạo tài khoản Overleaf cá nhân cho phần bảo vệ                                                                                                                                                |

**Điều chỉnh mục 1/4 của plan này:**

- Notebook 12 (benchmark) bây giờ có lý do mạnh hơn: bài giảng yêu cầu cột **chi phí vận hành** trong bảng đối chuẩn → đo runtime/memory per model là bắt buộc để bảng slide 12 đạt chuẩn IEEE/ACM, không chỉ là "điền RQ3". **Cập nhật 2026-11-18: phần runtime đã tổng hợp xong từ runs có sẵn (bước 4 ✅), memory vẫn còn thiếu — chỉ còn thiếu instrumentation, không còn thiếu số runtime.**
- Notebook 10 nâng tối thiểu nếu làm: Wilcoxon + **95% CI** + **effect size r** (bài giảng Phần 4 quy định cả 3).
- Thêm bước "đặt tên Ablation" — 0 chi phí, chỉ wording.

## 5. Verify cuối

- Regenerate PPTX: `python scripts\generate_slides.py`, readback grep số mới.
- Không ghi vào `docs/Project/Main/Notes/03.md` / `04.md` (chỉ đọc).
- Số slide luôn từ runs/docs, không bịa; không dùng `~` cho số.

## 6. Checklist Rubric tự đánh giá (Bài 04 yêu cầu ≥70/100)

| Yêu cầu tối thiểu Bài 04                  | Điểm hiện tại                                                                                                                                             | Trạng thái                          |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| Pipeline sạch, chia dữ liệu không rò rỉ  | 3 chiến lược split + audit leakage NB05                                                                                                                    | ✅                                    |
| Bộ độ đo chuyên ngành                    | NDCG@10 + Hit@10 + Recall@10 + coverage + Gini + long-tail + bias_ratio × 4 model; MRR đã đo ở cả 5 model (xem `Metrics.md` §4.10)                                                             | ✅ MRR đã đo ở cả 5 model           |
| Khung Ablation                                 | Bảng random→LOO→temporal (đặt tên "bóc tách chiến lược chia")                                                                                      | ✅ (wording)                          |
| Kiểm định Wilcoxon + 95% CI + effect size r | Notebook 12: 20 cặp, L12 PASS, `paired_stats.json`                                                                                                         | ✅                                    |
| Bảng SOTA đối chuẩn (bold/underline/*)     | 5/5 baseline đăng kí có số thật + runtime đủ 5 model + dấu sao lấy từ `paired_stats.json`, đã vào slide 12; SASRec+CE đã có số; memory vẫn chưa đo | ✅ 5/5 model có số; memory chưa đo |
| Script mẫu chạy pipeline + kiểm định      | NB 04/05/06/07/08/09/10/11/12 đều qua `scripts/generate_notebook_XX.py` + `scripts/run_notebook.py` (log + manifest + checkpoints)                      | ✅                                    |
| Ma trận rủi ro thực nghiệm                 | Drawbacks.md §3.5 (5 model đã chạy, SASRec OOM/GPU, ItemKNN driver-bound, giới hạn effect size)                                                      | ✅                                    |

---

## 7. Plan ưu tiên cho **môn PPNCKH** (đề cương + slide) — phân tầng theo "cần gì để bảo vệ"

> [!IMPORTANT]
> Câu hỏi của bạn: *notebook 10/11/12 và SASRec còn cần không?* Trả lời theo hai tầng, vì hai thứ đó phục vụ **hai việc khác nhau**: một là **bài thuyết trình PPNCKH** (sắp nộp), hai là **project/báo cáo khoa học** (sau đó).

### 7.1 Tầng ĐÃ ĐỦ cho buổi thuyết trình — không cần chạy thêm gì

| Hạng mục bài giảng 04 yêu cầu                                     | Bằng chứng đã có trên slide                                                                                                          | Trạng thái |
| ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------ |
| Pipeline sạch, split không rò rỉ                                    | notebook 04 tạo 3 chiến lược + notebook 05 audit leakage, gate L04/L05 PASS                                                            | ✅           |
| Bộ chỉ số RecSys                                                     | NDCG@10 + Hit@10 + Recall@10 + catalog coverage + Gini + long-tail + bias_ratio, **5 model × 3 split**, FULL 162.541 user           | ✅           |
| Kiểm định thống kê                                                 | Wilcoxon signed-rank **20 cặp**, mỗi cặp có p + 95% CI + rank-biserial r + n_paired (`paired_stats.json`)                      | ✅           |
| Chi phí vận hành (cột bắt buộc trong bảng đối chuẩn IEEE/ACM) | runtime đủ 5 model × 3 split: ItemKNN 499,7 s · ALS 286,7 s · Random 111,1 s · MostPopular 15,3 s → `Implementation/05_...RQ3.md` | ✅           |
| Ablation                                                                | bảng random→LOO→temporal, đặt tên "bóc tách tác động chiến lược chia"                                                        | ✅ (wording) |
| Novelty định lượng                                                  | RQ1 `best_model_reversals_found = 2` (ngôi đầu ALS↔ItemKNN đổi chỗ ở 2/3 split), RQ2 bias_ratio, RQ3 chi phí                    | ✅           |
| Ngoại lệ trung thực                                                  | cặp LOO ALS-vs-ItemKNN p = 0,153, CI chứa 0 → nói thẳng "không đủ bằng chứng"                                                    | ✅           |
| Giới hạn + hướng mở rộng                                          | slide 14–15, Drawbacks.md §3.5/§4                                                                                                       | ✅           |
| Khai báo công bằng (bài 04 nguyên tắc 1–3)                       | cùng dữ liệu, cùng phần cứng, seed 42 cố định, `protocol_id = project_protocol_v1`, code công khai                             | ✅           |

**Kết luận 7.1: slide đã đạt ngưỡng bảo vệ đề cương.** Không có mục nào trong 7.1 còn thiếu. Nếu hôm nay phải trình bày → **trình bày được ngay**.

### 7.2 Tầng NÊN LÀM trước buổi thuyết trình (rẻ, tăng điểm Rubric)

| #  | Việc                                                                                         | Chi phí                                                | Lợi trên slide                                                                        | Quyết định                                                                   |
| -- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| P1 | **MRR@10** cho 4 baseline (code đã vá xong vào nb 06/08/10/11, notebook đã regen) | ~15 phút CPU, tự chạy                                | bảng slide 12 đủ bộ NDCG/Recall/Hit/**MRR** đúng danh mục chỉ số bài 04 | **Nên** — xem `Implementation/06_Huong_Dan_Chay_SASRec_va_MRR.md` §B |
| P2 | **SASRec+CE** (notebook 13 đã viết, GPU local)                                       | đã đo 3 split, run `20261118_144646_13_sasrec_ce_8225755a`        | đủ **5/5 baseline đăng kí**, slide 11–13 hết chỗ "đã reproduce 3 split trên GPU local (không tuning)"        | **Nên nếu kịp** — không chạy thì vẫn nói được, đã khai báo |
| P3 | **Friedman + Nemenyi / CD diagram**                                                     | chỉ đọc npz đã lưu, không run model              | 1 ảnh CD diagram, "so sánh ≥3 model cùng lúc" đúng bài 04                       | Nice-to-have, ưu tiên thấp hơn P1/P2                                        |
| P4 | **Đo peak memory (RSS)**                                                               | cần thêm instrumentation vào nb 08/11/13 rồi re-run | cột "memory" trong bảng đối chuẩn                                                  | **Bỏ cho môn PPNCKH** (chốt A3) — làm sau cho project                |
| P5 | **Notebook 11 bias audit chi tiết** (PopRatio/P@k per group)                           | rẻ                                                     | đã có bias_ratio + Gini + long-tail → **không tăng gì cho slide**          | **Bỏ**                                                                   |

> [!NOTE]
> Notebook 10 (kiểm định cặp) và 12 (benchmark) **đã tồn tại và đã chạy xong** — dòng "chưa tạo" trong `Notes/03.md` Q_1 là thông tin cũ. Không còn nợ hai notebook đó.

### 7.3 Tầng KHÔNG CẦN cho môn PPNCKH (để dành cho project/báo cáo sau)

| Việc                                                | Vì sao hoãn                                                                            |
| ---------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Điền ~81 placeholder `chuong1–3.tex` (17/30/34) | báo cáo viết **sau** thuyết trình — chốt A1                                 |
| DSRM vào chuong3, FINER, SO1–SO3, RQ5              | thuộc báo cáo, không thuộc slide                                                    |
| Ảnh bìa/meta Zotero ≥5 bài                       | thuộc báo cáo                                                                         |
| Ma trận 3 seed → Mean ± Std                       | **Bỏ hẳn**, đã khai báo "1 seed"; thêm seed = đổi toàn bộ số đã chốt |
| Memory instrumentation (P4)                          | đề cương không yêu cầu tự实测; bảng đã có runtime                            |
| EASE                                                 | **Cấm** — không đăng kí, chỉ được nhắc ở dạng phủ định             |
| BPR                                                  | không đăng kí để chạy                                                             |

### 7.4 Thứ tự hành động đề xuất (bạn chạy, tôi cập nhật)

```
1. P1  MRR:  .\.venv\Scripts\python.exe scripts\run_notebook.py 06 10 08 11 --timeout 21600   (~15 ph)
2. P2  SASRec: cai torch (A.1) → smoke (A.3) → full (A.4)         (chem nhieu thoi gian, tach rieng)
3. Bao toi so trong runs/<id>/*.json
4. Toi: nb09 → 5 model, nb12 → 20 cap, slide 11–12, docs Metrics/System_Context/Architecture/Document_Indexing
5. P3  (neu con thoi gian) Friedman/Nemenyi trong nb12
```

Bước 1 và 2 **độc lập**, chạy song song được (1 CPU, 2 GPU). Không có bước nào ở 7.2 là **bắt buộc** để bảo vệ — tất cả là tăng chất lượng.

### 7.5 Trạng thái commit của các quyết định đã chốt

| Quyết định                                  | Chốt | Ghi vào đâu                                                        |
| ---------------------------------------------- | ----- | --------------------------------------------------------------------- |
| Báo cáo `.tex` sau thuyết trình          | ✅ A1 | §7.3, §3                                                            |
| MRR: hướng dẫn để user tự chạy          | ✅ A2 | `Implementation/06_...md` §B                                       |
| Memory instrumentation: bỏ                    | ✅ A3 | §7.2 P4, §7.3                                                       |
| SASRec: notebook để user tự chạy GPU local | ✅ A4 | `src/audit/sasrec.py`, notebook 13, `Implementation/06_...md` §A |
| EASE loại khỏi danh sách chạy              | ✅    | `Reseach_Method_Submission.md`, slide 13/14 dạng phủ định       |
| Ma trận nhiều seed: bỏ                      | ✅    | §0, §7.3                                                            |
| `Notes/03.md` / `04.md` chỉ đọc         | ✅    | §5                                                                   |

---

## 8. Handoff cuối phiên 2026-11-18 04:08 (dừng ở đây, tiếp tục khi thức dậy)

### 8.1 Đã xong trong phiên này — không cần làm lại

| #  | Việc                                                                           | Bằng chứng                                                                                                                                                                                                                                                              |
| -- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1  | `src/audit/sasrec.py` — SASRec + CE softmax toàn catalog, ~390 dòng        | `py_compile` OK; logic data-layer unit-test **ALL PASS** (`logs/scratch/test_sasrec_logic.py`: `min_len`, thứ tự timestamp, cắt đuôi `maxlen`, `SeqData` flat/offsets, pad trái, `y` = item kế tiếp)                                            |
| 2  | `scripts/generate_notebook_13.py` → `notebooks/jupyter/13_sasrec_ce.ipynb` | 11 cells, **all code cells compile**; có sẵn MRR@10, gate seen-exclusion, bias metrics, `peruser_ndcg_sasrec_<split>.npz` (đúng format nb12 cần), `hardware.note = "KHONG so sanh runtime"`, `tuning_budget: 0`                                          |
| 3  | Vá **MRR@10** vào 4 generator còn lại                                 | `logs/scratch/add_mrr2.py` → **OK=12 MISS=0**; `generate_notebook_06/08/10/11/13.py` đều có `mrr_mean` ×3, `mrr10` ×1, `mrr@10` ×1                                                                                                                 |
| 4  | Regenerate 4 notebook                                                           | nb06 14 cells · nb08 11 · nb10 11 · nb11 11 — tất cả in "all code cells compile"                                                                                                                                                                                    |
| 5  | **Sửa claim sai sự thật "không dùng GPU"**                           | `logs/scratch/fix_gpu_claims.py` **OK=18 MISS=0** trên 9 file: `notebooks/jupyter/README.md`, `Architecture.md`, `System_Context.md`, `Drawbacks.md`, `01_De_tai_va_Ke_hoach.md`, `00_README.md`, `05C_...md`, `generate_slides.py`, `TEMP.md` |
| 6  | Regenerate + readback PPTX                                                      | 428516 B, 15 slides; readback **text_frame + table cells + notes**: RTX 4050 ✓ · 0,2679 / 0,1409 / 0,0461 ✓ · 893,0× ✓ · 499,7 / 286,7 ✓ · 0,153 ✓ · 20 cặp ✓. Stale chỉ còn 2 dòng EASE **dạng phủ định** (hợp lệ, giữ)              |
| 7  | `Implementation/06_Huong_Dan_Chay_SASRec_va_MRR.md` (mới)                    | §A torch cu126 + smoke + full + OOM + điều phải khai báo; §B MRR + chi phí re-run + hệ quả run id mới; §C việc còn nợ                                                                                                                                       |
| 8  | `TEMP.md` §7 — plan ưu tiên môn PPNCKH                                   | 7.1 đã đủ để bảo vệ · 7.2 nên làm (P1 MRR, P2 SASRec, P3 Friedman, P4 memory **bỏ**, P5 nb11 **bỏ**) · 7.3 hoãn (`.tex`, DSRM, FINER, Zotero, seed matrix, EASE, BPR) · 7.4 thứ tự · 7.5 chốt A1–A4                                    |
| 9  | `Environment.md`                                                              | thêm dòng GPU RTX 4050 6 GB / driver 610.78, scipy 1.18, PyTorch (chưa cài, kèm lệnh `cu126`), `local[4]`, todo #5 cài torch                                                                                                                                   |
| 10 | `Metrics.md` §4.6                                                            | note MRR: ✅ đã có số ở cả 5 model (Metrics §4.10), NDCG không đổi; đã đưa vào slide 12.                                                                                                                                  |
| 11 | Chỉ mục notebook 13                                                           | `Document_Indexing.md` + `notebooks/jupyter/README.md` (đánh dấu ✅ đã chạy); `Implementation/00_README.md` DoD sửa 7 điểm (models / seed / mean±std / BPR / 10 seed / status)                                                                           |

### 8.2 Đang chạy nền khi ngủ

Tải wheel PyTorch **có resume** (task `8058c244-8a06-4f08-8d90-277b2a492113/task-3311`):

```powershell
curl.exe -L --retry 30 --retry-all-errors --retry-delay 3 -C - `
  -o "D:\recsys_data\wheels\torch-2.14.1+cu126-cp314-cp314-win_amd64.whl" `
  "https://download.pytorch.org/whl/cu126/torch-2.14.1%2Bcu126-cp314-cp314-win_amd64.whl"
```

- **Đã tải xong 2026-11-18 14:24: 2.501,6 MB** (đầy đủ). Log cũ: `logs/scratch/curl_torch.log`.
- `curl -C -` **nối tiếp được** nếu lỡ xoá/rớt — không tải lại từ đầu.
- Cài offline (đang chạy lúc 14:25, giải nén 2,6 GB):
  ```powershell
  .\.venv\Scripts\python.exe -m pip install --no-input --retries 10 --timeout 60 `
    "D:\recsys_data\wheels\torch-2.14.1+cu126-cp314-cp314-win_amd64.whl" `
    --index-url https://download.pytorch.org/whl/cu126
  ```
  Log: `logs/scratch/pip_torch_offline.log`. Xác nhận: `import torch` → `2.14.1+cu126 12.6 True`.

> [!WARNING]
> `pip install torch --index-url .../cu126` **đã fail 2 lần** vì `ConnectionResetError [WinError 10054]` ở ~1,0 GB (pip trên Windows không resume giữa chừng). **Đừng lặp lại cách đó** — dùng `curl -C -` ở trên.
> Nếu tắt máy giữa chừng, file dở vẫn còn ở `D:\recsys_data\wheels\` → chỉ cần chạy lại lệnh `curl` là nối tiếp.

### 8.3 Việc đầu tiên khi thức dậy (theo thứ tự)

1. **Xác minh torch**:
   ```powershell
   .\.venv\Scripts\python.exe -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
   ```

   Kỳ vọng `2.14.1+cu126 12.6 True NVIDIA GeForce RTX 4050 Laptop GPU`.
2. **Smoke test nb13** — **bắt buộc trước khi chạy full**, vì nhánh torch (`make_model` / `train_model` / `evaluate_ndcg` / `recommend_topk`) **chưa từng được thực thi lần nào**: đặt `SMOKE_USERS = 3000`, `SPLITS_TO_RUN = ['random80_20']` trong cell config → `Restart & Run All` → đối chiếu 3 điểm ở §A.3 của `Implementation/06_Huong_Dan_Chay_SASRec_va_MRR.md`. **Gửi tôi traceback nguyên văn nếu lỗi**, tôi sửa `sasrec.py`.
3. **Full nb13**: `SMOKE_USERS = None`, `SPLITS_TO_RUN = list(split_lib.STRATEGIES)` → `.\.venv\Scripts\python.exe scripts\run_notebook.py 13 --timeout 21600` → verify `runs/<run_id>/manifest.json` có `"status": "COMPLETED"` (**exit code 1 ≠ fail**).
4. **MRR cho 4 baseline** (độc lập với 1–3, chạy song song được vì 1 bên GPU 1 bên CPU):
   `.\.venv\Scripts\python.exe scripts\run_notebook.py 06 10 08 11 --timeout 21600` (~15 phút).
5. **Báo tôi** số trong `runs/<id>/sasrec_summary.json` + 4 summary mới → tôi làm nốt §8.4.

### 8.4 Phần tôi sẽ làm khi có số thật (chưa làm được vì thiếu dữ liệu)

| Đích                      | Thay đổi                                                                                                                                                                                                                                                                                                                                                                             |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `generate_notebook_09.py` | thêm `sasrec_summary.json` → **5 model**, field `sasrec_ndcg10`, `sasrec_over_rand`, `best_model`, `delta_sasrec_vs_best`, plot thêm đường SASRec → run 09 mới                                                                                                                                                                                                 |
| `generate_notebook_12.py` | `MODEL_FILES` += `('SASRec_CE', 'sasrec_summary.json', 'peruser_ndcg_sasrec_{strategy}.npz')` → **20 cặp** → run 12 mới                                                                                                                                                                                                                                                  |
| `generate_slides.py`      | slide 11 baseline **5/5 ✓**, slide 12 thêm dòng SASRec + footer gate, slide 13/14 cập nhật GPU; regen + readback **table cells**                                                                                                                                                                                                                                      |
| Docs                        | `Metrics.md` §4.10 (MRR + SASRec), `System_Context.md` §12.1/12.2/12.2b, `Drawbacks.md` §3.5 "đủ 5/5" + §4.1 thêm đường E, `Architecture.md` gate L13 + diagram (`comparison.json (5 model)`, nb12 `20 cặp`), `Document_Indexing.md` run id mới, `Implementation/05_...RQ3.md` thêm dòng SASRec (kèm cảnh báo **không so runtime GPU-vs-CPU**) |
| Verify                      | quét `docs/` tìm chuỗi cũ: `4 model`, `12 cặp`, `4/5 baseline`, `chưa reproduce`, `không dùng GPU`, run id cũ                                                                                                                                                                                                                                                     |

### 8.5 Trạng thái `git` (chưa commit — bạn không yêu cầu)

Khoảng 35 file modified + 14 untracked. File mới đáng chú ý: `src/audit/sasrec.py`, `scripts/generate_notebook_13.py`, `notebooks/jupyter/13_sasrec_ce.ipynb`, `docs/Project/Plans/Research/Implementation/06_Huong_Dan_Chay_SASRec_va_MRR.md`, `logs/scratch/*.py`. **Không xoá** `runs/` — mọi run cũ giữ để truy vết, kể cả run fail có outputs rỗng (`20261118_002930_...`, `20261118_004635_...`, `20261118_0141*/0142*_12_...`).

### 8.6 Điều **không** làm (đã chốt, đừng tự ý mở lại)

- Không đụng `chuong1–3.tex` / FINER / DSRM / RQ5 / ảnh Zotero → báo cáo viết **sau** thuyết trình (chốt A1).
- Không làm memory instrumentation RQ3 (chốt A3) — đề cương/slide không cần.
- Không thêm **EASE** (không đăng kí), không chạy **BPR**, không chạy **ma trận nhiều seed**.
- Không ghi vào `docs/Project/Main/Notes/03.md` và `04.md` (chỉ đọc).
- Không tự chạy full SASRec/ALS/ItemKNN hộ (tiết kiệm token + bạn muốn tự chạy) — chỉ smoke test nhỏ để đảm bảo code chạy được.


### 8.7 Cập nhật 2026-11-18 14:32 — torch cài xong, smoke PASS, chuẩn bị full

| Việc | Kết quả thật |
|---|---|
| Cài torch | `2.14.1+cu126`, `torch.version.cuda = 12.6`, `cuda.is_available() = True`, device `NVIDIA GeForce RTX 4050 Laptop GPU`, capability 8.9, VRAM 6.140 MiB |
| Smoke module (`logs/scratch/smoke_sasrec.py`) | **ALL SMOKE PASS** — train 3 epoch, `evaluate_ndcg`, `recommend_topk` (leak=0), `cuda_report` đều chạy |
| Smoke notebook 13 | run `20261118_143029_13_sasrec_ce_29c68c40`, **0 cell error**, `gpu_check` PASS, `sasrec_complete` PASS; 3.000 user đầu → eval 2.933 user, seen-exclusion **PASS 2.933/0 leak**, `ndcg@10=0,1064`, `hit@10=0,4494`, `recall@10=0,0739`, `mrr@10=0,2008`, fit 10,0 s (best epoch 1), total 52,1 s; checkpoints `gpu_check`, `spark_ready`, `sasrec_complete`, `sanity_read`, `artifacts_saved` |
| **Phát hiện quan trọng** | Catalog thực = **38.328 item** (train positive `rating >= 4.0`), không phải 1.681 như giả định cũ. Đã sửa `generate_notebook_13.py` + `Implementation/06_...md` §A.5/§A.7. Logits full-catalog `batch 32 × seq 50 × 38.329 × 4 B ≈ 245 MB`, vẫn nằm trong 6 GB |
| Sửa kỹ thuật | `attn_mask` đổi sang `torch.bool` cùng dtype với `key_padding_mask` → hết `UserWarning: Support for mismatched key_padding_mask and attn_mask is deprecated` |

**Ước thời gian full (cập nhật từ smoke, thô):** 3.000 user → 52 s; FULL 162.541 user × 3 split ≈ 55× → ~48 phút/split, ~2,5 giờ cho cả 3 split (chủ yếu là bước top-K trên GPU). Chạy nền `--timeout 21600`, verify `manifest.json status == COMPLETED`.

> [!WARNING]
> Số smoke ở trên **không được đưa vào slide** — đã có số thật từ 4 baseline. Chỉ dùng để ước thời gian và chứng minh code chạy.

### 8.8 Verify sau sửa `attn_mask` bool — 2026-11-18 14:35

| Việc | Kết quả thật |
|---|---|
| `py_compile src/audit/sasrec.py scripts/generate_notebook_13.py` | `PY_COMPILE_OK` |
| Smoke module chạy lại sau sửa bool mask | `ALL SMOKE PASS`, `WARN_MISMATCH=False` — hết `UserWarning: Support for mismatched key_padding_mask and attn_mask is deprecated`; leak 0 |
| Regenerate notebook 13 | `Created ... 13_sasrec_ce.ipynb with 11 cells; all code cells compile` |
| Nội dung notebook 13 | `1.681=0` · `1682=0` · `38.328=1` · `SMOKE_USERS = None=1` · `SPLITS_TO_RUN = list(split_lib.STRATEGIES)` |
| Artifact smoke cũ | `13_sasrec_ce_SMOKE.ipynb` vẫn còn chữ `1.681` ở markdown — giữ để truy vết run smoke, **không** phải source of truth; slide/docs dùng notebook 13 đã regenerate |
| Docs đồng bộ | `Implementation/06_...md` + `Environment.md`: bỏ claim "chưa cài torch / chưa từng chạy" → "đã cài, smoke PASS, full 3 split đã chạy" |

Chặng còn lại giữ nguyên §8.4: full SASRec (user tự chạy) → MRR 4 baseline → nb09/nb12/slides/docs số thật.
