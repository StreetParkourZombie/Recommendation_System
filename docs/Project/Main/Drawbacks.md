# Hạn Chế & Thách Thức Dự Án (Project Drawbacks & Limitations)

**Dự án:** Phân tích rò rỉ, thiên lệch phổ biến trong hệ thống gợi ý bằng kiểm toán chiến lược chia tập trên Spark.
**Cập nhật:** 2026-11-20 (bổ sung giới hạn Novelty/Diversity/Friedman từ Bài 04)

---

## 1. Giới Hạn Về Hạ Tầng & Quy Mô Xử Lý

### 1.1. Spark Local, Không Phải Cụm Phân Tán

- PySpark chạy `local[4]` — 4 luồng trên **một máy đơn**, không có executor trên node khác.
- **Hạn chế:** mọi số wall-clock phản ánh CPU/RAM/SSD của laptop, **không** nói gì về khả năng scale-out. Không được suy ra "chạy trên cụm sẽ nhanh gấp N lần".
- **Ràng buộc báo cáo:** phải phân định rành mạch giữa kiểm toán thuật toán trên Spark Local và năng lực phân tán của Hadoop/HDFS (MapReduce chạy trong container — đó mới là phần phân tán thật).

### 1.2. Trạng Thái Dịch Vụ Nền (đã cập nhật 2026-11-15)

| Dịch vụ | Trạng thái | Ghi chú |
|---|---|---|
| MongoDB 8.0.12 | ✅ chạy được | `recsys.audit_metrics` 6 docs / 42 field; `item_profile` 62.423 docs |
| Hadoop 3.2.1 (container) | ✅ chạy được khi bật thủ công | MapReduce job `JOB_STATUS=SUCCESS`, G3 pass 100% |
| Docker engine | ⚠️ cần bật thủ công | Không tự khởi động trong phiên tự động |

- **Hạn chế:** pipeline không tự phục hồi khi container tắt. Mọi bước phụ thuộc HDFS/MongoDB phải smoke-test lại sau khi khởi động máy.

### 1.3. ALS Fit Toàn Bộ 162.541 User (khác phục từ 2026-11-17)

- **Trước đây (run 2026-11-15):** `recommendForAllUsers` OOM (162.541 × 59.047 ≈ 9,6 tỷ cặp) → ALS chỉ fit trên **30.000 user đầu theo `userId`**. NDCG của ALS không đại diện cho toàn bộ 162.541 user; 30.000 user đầu nghiêng về user đăng ký sớm.
- **Đã khác phục (run FULL 2026-11-17, `20261117_185700_08_als_implicit_7be22080`):** bỏ subsample, fit toàn bộ 162.541 user trên ~20–25M dòng/split bằng đường top-K numpy chunked (`topk_numpy`), fit ~35–38s/split, RUN_FINISH COMPLETED, mọi gate PASS. NDCG chênh ≤ 1% so subsample (0,2556 → 0,2581 random80_20) — subsample trước đủ đại diện.
- **Hạn chế còn lại:** 1 seed (§1.4); khuyến nghị ghi `fit_scope` trong summary để truy vết hai giai đoạn.
- Lịch sử subsample giữ lại ở đường B (`Metrics.md` §4.5) để truy vết.

### 1.4. Chỉ Một Seed (42)

- Toàn bộ kết quả đo trên **một seed duy nhất**.
- **Hạn chế:** không có bằng chứng về độ ổn định qua seed. Ma trận seed × 3 split × 5 model **không chạy** — đây là quyết định có chủ đích (được ghi trong `TEMP.md` §0: chạy thêm mâu thuẫn với giới hạn đã khai báo trong đề cương), không phải thiếu sót do quên.
- **Ràng buộc báo cáo:** không được nói "kết quả ổn định" hay "không phụ thuộc seed". Chỉ được nói "với seed 42".

---

## 2. Thách Thức Về Bản Chất Dữ Liệu & Rò Rỉ Thời Gian

### 2.1. Trùng Mốc Thời Gian (Timestamp Ties)

- MovieLens-25M có **1.799.454 nhóm** tương tác trùng cùng một giây ở cùng một user, phủ **78.496 user**, chiếm khoảng 6,12 triệu tương tác.
- **Hệ quả:** với `leave_one_out`, "tương tác cuối cùng" của một user không xác định được bằng timestamp. Phải có tie-break phụ.
- **Đã áp dụng:** tie-break theo `movieId` (deterministic, cài trong `src/audit/splits.py`).
- **Hạn chế còn lại:** tie-break theo `movieId` **tất định nhưng không phải thứ tự thời gian thật**. Không có cách nào biết user thực sự xem phim nào sau cùng trong cùng một giây. Mọi kết luận về "item cuối" phải kèm câu này.

### 2.2. Rò Rỉ Tương Lai Trong Chia Ngẫu Nhiên

- `random80_20`: **98,9158%** tương tác test sớm hơn tương tác mới nhất của chính user đó trong train (đo bằng notebook 05).
- **Hệ quả:** NDCG@10 trên split này là ước lượng **lạc quan**, không phản ánh năng lực triển khai thực tế.

### 2.3. Thiên Lệch Phổ Biến & Hiệu Ứng Matthew

- Phân phối đuôi dài cực mạnh: item nhiều rating nhất 81.491, trung vị khoảng 6.
- MostPopular `bias_ratio` 101–165× trung bình catalog; ALS 10,6–12,8×. Cả hai đều **trên 1** → đều thiên lệch về phim phổ biến.
- `longtail_coverage = 0` ở **cả 6 tổ hợp** → **không** được khẳng định "đã xử lý thiên lệch".

### 2.4. `leave_one_out` Báo 99,9988% Rò Rỉ Toàn Cục — Đây Là Artifact

- Định nghĩa **toàn cục** so test của mọi user với `max(train.timestamp)` của toàn bộ tập train. Với LOO, test của user A gần như luôn sớm hơn tương tác mới nhất của user B.
- **Không phải lỗi, không phải rò rỉ nhân quả.** Chỉ định nghĩa **tương đối theo user** (= 0,0000%) mới đúng cho LOO.
- **Ràng buộc báo cáo:** nếu trích 99,9988% mà không kèm 0,0000% và giải thích, đó là trình bày sai.

---

## 3. Ranh Giới Đánh Giá Offline

### 3.1. Thiếu Tương Tác Trực Tuyến

- Hệ thống hoàn toàn dựa trên offline replay trên tập test cố định.
- Không đo được: hài lòng thực tế, click-through thật, mỏi mệt khi thấy gợi ý lặp lại, tác động lên hành vi dài hạn.

### 3.2. Giả Định Đơn Giản Hoá Về Tương Tác Tích Cực

- Chuyển rating explicit (0,5–5,0) sang implicit bằng ngưỡng `rating ≥ 4,0` → mất sắc thái đánh giá và bỏ qua tương tác dưới ngưỡng (có thể là tín hiệu phủ định, không phải "thiếu dữ liệu").
- Ngưỡng 4,0 áp dụng giống nhau cho mọi mô hình — công bằng trong so sánh nhưng **không** phải lựa chọn tối ưu cho từng mô hình.

### 3.3. NDCG Không So Cặp Được Giữa Các Split

- Mỗi split có tập user đánh giá riêng: **158.692 / 6.219 / 96.003** user có ≥ 1 tương tác liên quan.
- **Hạn chế:** NDCG của `temporal_global` (0,1332) và `random80_20` (0,2581) được tính trên hai quần thể khác nhau → **không** so sánh trực tiếp được bằng test ghép cặp. (Số FULL run 2026-11-17; số subsample cũ 0,1311 / 0,2556.)
- Kiểm định Wilcoxon chỉ hợp lệ **trong** một split (so ALS với Popularity trên cùng user). So sánh **giữa** split chỉ được dùng để mô tả **độ lớn hiệu ứng co lại**, kèm chỉ số cấp dữ liệu giải thích nguyên nhân.

### 3.4. `temporal_global` Đổi Rò Rỉ Lấy Dịch Chuyển Miền

- Loại được rò rỉ (0,0000%) nhưng **mất 96,1% mẫu đánh giá** (158.692 → 6.219 user) và có **8,7595%** dòng test trỏ tới item chưa từng thấy trong train.
- **Hệ quả:** NDCG thấp ở split này một phần là do tập test khó hơn, không hoàn toàn do mô hình yếu.

### 3.5. Năm Baseline Đã Chạy — SASRec Có Điều Kiện

- Baseline theo danh sách **đã đăng kí đề tài** (`docs/About/Reseach_Method_Submission.md`): Random, MostPopular (sàn); ALS, ItemKNN cosine (kinh điển); SASRec+CE (SOTA). **EASE không nằm trong danh sách đăng kí → không chạy** (đã ghi rõ trong kế hoạch G1).
- **Đã chạy đủ 5/5 (2026-11-18):**
  - Random — run cuối `20261118_144717_10_random_baseline_d8644ac1`: NDCG@10 0,0003 / 0,0009 / 0,0001, bias_ratio ≈ 1, seen exclusion PASS.
  - ItemKNN cosine — run cuối `20261118_150305_11_itemknn_baseline_0b7511ee`: NDCG@10 0,2679 / 0,1409 / 0,0461, bias_ratio 16,4–22,0, seen exclusion PASS 3/3.
  - ALS hơn sàn 860,3× / 148,0× / 469,0×; ItemKNN hơn sàn 893,0× / 156,6× / 461,0×; MostPopular hơn sàn 284,0× / 50,6× / 183,0× — mức "học được" thật của từng split.
- **Tầng SOTA đã chạy:** SASRec+CE trên GPU RTX 4050 Laptop 6 GB, run `20261118_144646_13_sasrec_ce_8225755a`, `COMPLETED`, 3 split, seed 42, `tuning_budget=0`. Fit FULL 162.541 user nhưng đánh giá subset (`val_fraction_users=0.1`); mọi cặp Wilcoxon có SASRec dùng giao user. Kết quả thua 4 baseline về NDCG/MRR — **không gọi là model thắng**, không so runtime GPU-vs-CPU, không suy ra "SOTA yếu hơn bản chất" khi chưa tuning.
- **Giới hạn kỹ thuật của ItemKNN đã triển khai:** co-count bằng scipy sparse trên driver (`toPandas` 20M cặp user–item), **không phân tán** — khác với ALS chạy trong Spark. Nghĩa là chi phí 499,7 s ở §4.7 (Metrics) là chi phí *driver-bound*; trên cụm thật con số này không so sánh được với ALS. Đã khai báo, không được diễn giải thành "ItemKNN đắt hơn ALS trong hệ thống phân tán".
- **Giới hạn phương pháp (mới, từ kiểm định cặp §4.9 Metrics):** đảo chiều ngôi đầu ALS↔ItemKNN **có ý nghĩa thống kê** ở 2/3 split nhưng **effect size gần không** (|r| = 0,005–0,030). Nói "ItemKNN tốt hơn ALS" mà không kèm r là phóng đại kết quả.
- **Hạn chế còn lại:** nếu chỉ so với sàn, kết luận sẽ là "không đảo chiều". Đảo chiều chỉ lộ ra khi so hai model ngang tầm — đề tài có cả hai tầng baseline nên thấy được, nhưng điều này cũng cho thấy **thiết kế thực nghiệm phải chọn cặp so sánh trước**, không phải chỉ chọn nhiều model.

---

## 4. Hạn Chế Truy Vết Số Liệu

### 4.1. Hai Đường Tính Cho Hai Bộ Số Hơi Khác Nhau

- Đường A (script, 2026-11-04): ALS NDCG 0,2584 / 0,1364 / 0,0474.
- Đường B (notebook subsample, 2026-11-15): ALS NDCG 0,2556 / 0,1311 / 0,0467.
- Đường C (notebook FULL, 2026-11-17): ALS NDCG **0,2581 / 0,1332 / 0,0469** — fit toàn bộ 162.541 user.
- Chênh lệch ≤ 0,0053 do khác đường chọn tập user + khác đường top-K; B vs C chênh ≤ 1%.
- Đường D (2026-11-18): thêm Random + ItemKNN + MostPopular rerun, **ghép 4 model** ở run `20261118_022749_09_compare_and_reversal_c9482d3f` + kiểm định 12 cặp ở `20261118_022320_12_paired_stats_077f538e`. Số ALS đường D **trùng khớp đường C** (0,2581 / 0,1332 / 0,0469).
- Đường E (2026-11-18, cuối): thêm SASRec GPU + MRR cho cả 5 model; `comparison.json` `20261118_151159_09_compare_and_reversal_1e0f72fa`, `paired_stats.json` `20261118_151202_12_paired_stats_9b864f59` (20 cặp, min n=6.214). NDCG/ALS giữ nguyên đường D — bằng chứng pipeline ổn định khi ghép model thứ 5.
- **Ràng buộc:** không trộn số A/B/C trong cùng một bảng. Xem `Metrics.md` §4.5. Kết luận định tính giống nhau ở cả ba đường.

### 4.2. `percentile_approx` / `approxQuantile` Là Xấp Xỉ

- Spark trả giá trị **xấp xỉ** (relative error mặc định 0,01), không phải phân vị chính xác.
- **Hệ quả:** ranh giới split của `temporal_global` dịch chuyển nhẹ nếu đổi `relativeError`. Không được assert bằng `==` trên mốc này.

---

## 5. Tóm Tắt Những Điều KHÔNG Được Nói

| Không được nói | Vì sao |
|---|---|
| "Chạy trên cụm phân tán" | `local[4]`, một máy |
| "Kết quả ổn định qua seed" | chỉ seed 42 |
| ~~"ALS đại diện toàn bộ 162.541 user"~~ | **đã khác phục 2026-11-17** — fit FULL toàn bộ; số cũ 30k chỉ là lịch sử đường B |
| "ALS/ItemKNN đã xử lý thiên lệch phổ biến" | `longtail_coverage = 0` ở cả 3 split của ALS và MostPopular; ItemKNN chỉ 0,0000–0,0005 — về thực hành vẫn là 0. Random đạt 1,0 nhưng đó là sàn không học gì, không phải bằng chứng xử lý thiên lệch |
| "leave_one_out rò rỉ 99,9988%" (không kèm giải thích) | artifact của định nghĩa toàn cục |
| "NDCG của temporal thấp hơn random vì mô hình kém" | tập đánh giá khác nhau về bản chất |
| "ItemKNN tốt hơn ALS" (không kèm effect size) | p có ý nghĩa ở 2/3 split nhưng |rank-biserial r| = 0,005–0,030 = gần không; ở LOO p = 0,153 và CI chứa 0 |
| "Đã chạy ma trận seed" hoặc "kết quả là Mean ± Std" | chỉ 1 seed 42; bảng báo per-split + kiểm định cặp per-user |
| "Chi phí ItemKNN so sánh được với ALS trên cụm" | ItemKNN chạy scipy sparse trên driver (`toPandas` ~20M cặp) — driver-bound, không phân tán |
| "Đã tái lập Paper 01" | đây là `method_informed_implementation` |
| "Serendipity đã đo" | Bài 04 định nghĩa serendipity cần một model "nguyên thuỷ" làm mốc; đề tài không có. Hàm `serendipity_at_k` chỉ cài **định nghĩa hẹp** (novelty của item vừa top-K vừa relevant), KHÔNG phải serendipity đầy đủ — xem `Metrics.md` §2.5 |
| "Mô hình cá nhân hoá thì đa dạng hơn" | Số đo ngược lại: Diversity@10 của ALS (0,735–0,747) **thấp hơn** MostPopular (0,765–0,788) ở cả 3 split. Cá nhân hoá không tự động kéo theo đa dạng genre — xem `Metrics.md` §4.12.3 |
| "Mô hình mới lạ hơn là tốt hơn" | Random có Novelty@10 cao nhất (20,2–21,1) nhưng NDCG ≈ 0. Novelty phải đọc kèm NDCG — xem `Metrics.md` §4.12.2 |
| "Friedman chỉ ra cặp nào khác nhau" | Friedman (Demšar, JMLR 2006) chỉ bác bỏ "mọi model ngang nhau"; chỉ ra cặp cụ thể là việc của Wilcoxon (notebook 12) hoặc Nemenyi post-hoc — chưa chạy Nemenyi |
| "SASRec đắt hơn baseline 5×" | SASRec chạy GPU RTX 4050, 4 baseline chạy CPU. Khác phần cứng, không so runtime — xem `Metrics.md` §4.12.4 |
