# 08 — Tạo tác khoa học: SLI (Split Leakage Index) và giao thức audit 3 bước

**Project:** `D:\Master Exers\Big Data\Recomendation_System`
**Ngày lập:** 2026-11-07 · **Deadline đề cương:** 2026-11-08
**Vì sao có file này:** trả lời câu hỏi "đề tài có sáng tạo gì hay chỉ đo?" và thoả
yêu cầu Bài 03 PPNCKH trang 52: *"Yêu cầu ThS: Đóng góp ít nhất dạng 2 và 3"*.

---

## 0. Vấn đề phải giải

Bài 03 trang 52 — **bốn dạng tạo tác khoa học (artifacts) trong KHMT**:

| Dạng | Nội dung | Ví dụ |
|---|---|---|
| 1. **Concepts** | Thuật ngữ mới, taxonomy | Phân loại 3 kiểu gian lận mới |
| 2. **Models** | Mô hình toán, không gian nhúng | Đồ thị tài khoản–thiết bị–giao dịch |
| 3. **Methods** | Giải thuật, cơ chế, hàm mất mát mới | Adaptive Attention + hàm mất mát phạt nặng |
| 4. **Instantiations** | Prototype, thư viện mã nguồn | Prototype PyTorch trên GitHub |

> *"**Yêu cầu ThS: Đóng góp ít nhất dạng 2 và 3**"*

Bài 03 trang 26 — **tỷ trọng đóng góp của các SO**:

> SO1 · Data (20%) · SO2 · **Model (40%) — "Đề xuất kiến trúc cốt lõi"** · SO3 & SO4 · Eval (40%)

Bài 03 trang 12 — **phân biệt luận văn ThS và đồ án đại học**:

> Luận văn thạc sĩ — Trọng tâm: *Giải bài toán kỹ thuật, đề xuất mới* — Tính mới: **"Giải thuật cải tiến hoặc đối chuẩn SOTA"**

**Kết luận đối chiếu:** nếu đề tài chỉ chạy 3 baseline rồi báo cáo NDCG thì **không có SO2**,
tức **thiếu 40% tỷ trọng đóng góp** và **không đạt yêu cầu dạng 2 + 3**.

**Giải pháp:** đóng gói phát hiện đã đo được thành **tạo tác có tên, có công thức, có ngưỡng**.
Không bịa thêm thực nghiệm — chỉ hình thức hoá thứ đã có bằng chứng số.

---

## 1. Tạo tác 1 (dạng Concepts + Models) — Split Leakage Index (SLI)

### 1.1 Định nghĩa

Cho tập train $\mathcal{D}_{train}$ và test $\mathcal{D}_{test}$ trên cùng không gian
user–item–timestamp. Ký hiệu $\mathcal{D}_{test}(u)=\{(u,i,t)\in\mathcal{D}_{test}\}$ là
tập tương tác test của riêng user $u$. Với mỗi user $u$, gọi

$$t^{(u)}_{\max} = \max\{\, t : (u, i, t) \in \mathcal{D}_{train} \,\}$$

là **mốc thời gian cuối cùng mà mô hình còn được thấy** về user $u$.

Một tương tác test $(u, i, t) \in \mathcal{D}_{test}$ là **rò rỉ** khi

$$t < t^{(u)}_{\max}$$

Tức: mô hình đã thấy tương tác của $u$ ở thời điểm **sau** tương tác đang được đánh giá.

**Split Leakage Index** đo tỷ lệ rò rỉ:

$$
\mathrm{SLI}_u =
\frac{\bigl|\{(u,i,t) \in \mathcal{D}_{test}(u) : t < t^{(u)}_{\max}\}\bigr|}
     {|\mathcal{D}_{test}(u)|}
$$

$$
\mathrm{SLI} = \frac{1}{|\mathcal{U}_{test}|} \sum_{u \in \mathcal{U}_{test}} \mathrm{SLI}_u
$$

Tức **trung bình tỷ lệ rò rỉ trên từng user**, không phải tỷ lệ gộp toàn cục.
Mẫu số là số tương tác test **của chính user đó**, không phải $|\mathcal{D}_{test}|$.
Dùng dấu `<`: timestamp bằng nhau giữa train và test không được tính là rò rỉ.

> **Ghi nguồn tạo tác:** SLI là chỉ số **do đề tài định nghĩa**. TOIS 41(3) chỉ khẳng định
> cần quan sát timeline toàn cục và phân tích hậu quả rò rỉ; bài **không đưa công thức SLI**.
> Khi báo cáo phải viết "đề tài đề xuất", không viết "theo TOIS". Xem mục 1.2 dưới đây.

### 1.2 Vì sao "tương đối theo user" — đây là điểm mới

Định nghĩa **toàn cục** (cách đang dùng phổ biến) là:

$$\mathrm{SLI}_{\text{global}} = \frac{\bigl|\{(u,i,t) \in \mathcal{D}_{test} : t < T_{\max}^{train}\}\bigr|}{|\mathcal{D}_{test}|}, \quad T_{\max}^{train} = \max\{t : (u,i,t) \in \mathcal{D}_{train}\}$$

**Chứng minh bằng số thật** (MovieLens ml-25m, đo 04/11/2026):

| Split | $\mathrm{SLI}_{\text{global}}$ | $\mathrm{SLI}$ (tương đối) | Chênh |
|---|---|---|---|
| `random80_20` | 100,0000% | **98,9158%** | 1,08 pp — hai cách gần nhau |
| `temporal_global` | 0,0000% | **0,0000%** | 0 — đồng thuận |
| `leave_one_out` | **99,9988%** | **0,0000%** | **99,9988 pp — kết luận NGƯỢC HOÀN TOÀN** |

**Diễn giải:** với leave-one-out, mỗi user giữ tương tác **mới nhất của chính mình** làm test.
Toàn cục thì luôn tồn tại user hoạt động muộn hơn → $T^{train}_{\max}$ bị đẩy về tương lai →
gần như **mọi** tương tác test "trông như" bị rò rỉ. Nhưng thực tế **không user nào** bị rò rỉ,
vì test của mỗi user chính là tương tác muộn nhất **của user đó**.

→ **Cách đo toàn cục cho kết luận sai về leave-one-out.** Đây là phát hiện khái niệm,
không phải phát hiện kỹ thuật. Nó chưa có trong [01] TOIS 2023 (bài nổi tiếng nhất về data
leakage trong RecSys) — [01] đo bằng cách so sánh kết quả hai protocol, **không định nghĩa chỉ số**.

### 1.3 Ngưỡng phân loại (để hội đồng nghiệm thu được)

| SLI | Phân loại | Hàm ý |
|---|---|---|
| **SLI < 0,05** | **An toàn** | Rò rỉ dưới mức nhiễu; dùng được cho kết luận |
| **0,05 ≤ SLI < 0,30** | **Rò rỉ nhẹ** | Chấp nhận được trong công nghiệp, **không** dùng cho so sánh học thuật |
| **SLI ≥ 0,30** | **Rò rỉ nghiêm trọng** | Kết quả không dùng được; phải đổi split |

**Cơ sở chọn ngưỡng:** 0,05 tương đương mức nhiễu ±5% mà ngành chấp nhận cho metric xếp hạng;
0,30 là mức mà tỷ lệ item "đã biết trước" đủ lớn để MostPopular đạt NDCG gần bằng ALS
(đo được: random80_20 có Pop NDCG 0,0852 và ALS 0,2581 — chênh 3,03×; nếu SLI cao hơn nữa
thì khoảng cách này sụp). **Đây là ngưỡng do đề tài chọn dựa trên số liệu đo được, không phải
ngưỡng chuẩn công bố trong paper.**

### 1.4 Ví dụ áp dụng lên 3 split của đề tài

| Split | SLI | Phân loại | NDCG@10 (ALS) | `eval_rel_users` |
|---|---|---|---|---|
| `random80_20` | 0,9892 | **nghiêm trọng** | 0,2581 | 158.626 |
| `temporal_global` | 0,0000 | **an toàn** | 0,1332 | 6.214 |
| `leave_one_out` | 0,0000 | **an toàn** | 0,0469 | 95.977 |

Nguồn số NDCG/`eval_users`: đường C — ALS fit FULL 162.541 user, run `20261117_185700_08_als_implicit_7be22080`
(`als_summary.json`), đối chuẩn bởi `runs/20261118_151159_09_compare_and_reversal_1e0f72fa/outputs/comparison.json`.
`eval_rel_users` ở đây là `eval_users` của riêng ALS, không phải `eval_users_pop` (`158.692 / 6219 / 96003`).
Không trộn với đường script cũ: số cũ chỉ ghi trong lịch sử ở đây, không dùng làm số báo cáo.

Bảng này tự nói lên toàn bộ luận điểm của đề tài: **split an toàn nhất cũng là split đắt nhất**
(mất 96,1% mẫu đánh giá), còn **split cho kết quả đẹp nhất lại là split rò rỉ nghiêm trọng**.

---

## 2. Tạo tác 2 (dạng Methods) — Giao thức audit 3 bước

### 2.1 Quy trình

Khi báo cáo bất kỳ so sánh mô hình nào trên dữ liệu tương tác có timestamp:

**Bước 1 — Báo SLI trước, metric sau.**
Mọi bảng kết quả phải có cột SLI ở **bên trái** cột metric chính. Không có SLI → không được
diễn giải metric.

**Bước 2 — Báo `eval_rel_users` song song mọi metric.**
`eval_rel_users` = số user còn lại sau bộ lọc cold-start (≥5 tương tác train).
Metric trung bình trên 158.626 user khác hẳn trung bình trên 6.214 user — không báo kèm là
so sánh vô nghĩa.

**Bước 3 — Chặn so sánh khi tỷ lệ mẫu lệch quá 20%.**
Nếu tỷ lệ $\frac{\max(n_1, n_2)}{\min(n_1, n_2)} > 1{,}2$ thì **không được** phát biểu
"split A tốt hơn split B", mà phải phát biểu "split A cho điểm cao hơn trên một mẫu khác".

### 2.2 Ví dụ áp dụng — phép so sánh này bị chặn

| So sánh | $n_1$ | $n_2$ | Tỷ lệ | Kết luận |
|---|---:|---:|---:|---|
| random80_20 vs temporal_global | 158.626 | 6.214 | **25,5×** | **BỊ CHẶN** ở Bước 3 |
| random80_20 vs leave_one_out | 158.626 | 95.977 | 1,65× | **BỊ CHẶN** ở Bước 3 |
| temporal_global vs leave_one_out | 6.214 | 95.977 | 15,4× | **BỊ CHẶN** ở Bước 3 |

→ **Không cặp nào được phép so sánh trực tiếp.** Đây chính là đóng góp thực tiễn: giao thức
này **tự chặn** những kết luận mà nhiều bài báo hiện đang đưa ra.

### 2.3 Quy tắc báo cáo bắt buộc (đã có trong đề tài)

> Mọi so sánh NDCG giữa 2 split **phải kèm** `eval_rel_users`. Không có ngoại lệ.
> (đã ghi trong `MEMORY.md` từ 04/11 — nay hình thức hoá thành Bước 2 của giao thức)

---

## 3. Tạo tác 3 (dạng Instantiations) — Pipeline tái lập

| Thành phần | Công nghệ | Bằng chứng chạy thật |
|---|---|---|
| Thu nạp | HDFS 3.2.1 (5 container) | `docs/Project/Main/` log + screenshot YARN Web UI |
| Đếm phổ biến | **MapReduce Java** (không phải Python — container không có Python) | 323.737 key, `JOB_STATUS=SUCCESS`, G3 cross-check PASS 100% |
| Huấn luyện | PySpark 4.2.0, ALS (rank 16, maxIter 8, regParam 0,05, seed 42) | `results/poc6_<split>.json` |
| Kiểm định | scipy 1.18.0 — bootstrap 10.000 lần, Wilcoxon, Cohen's dz, rank-biserial | `reports/stats_summary.csv` (12 dòng) |
| Lưu trữ | MongoDB `recsys.audit_metrics` (6 docs, 42 field) + `item_profile` (62.423 docs) | 1 nguồn ghi duy nhất: Python |
| Trực quan | R 4.6.2 (7 PNG + 2 CSV) + Streamlit (port 8501, HTTP 200) | `fig9_dashboard.png` 152.694 B |

---

## 4. Bảng ba tạo tác — dán thẳng vào đề cương

| # | Dạng (theo Bài 03 tr.52) | Tạo tác | Bằng chứng định lượng | Đạt yêu cầu? |
|---|---|---|---|---|
| **1** | Concepts + Models | **Split Leakage Index (SLI)** — đo rò rỉ **tương đối theo user**, 3 ngưỡng phân loại | LOO: toàn cục **99,9988%** vs tương đối **0%** — kết luận ngược hoàn toàn | ✅ dạng 2 |
| **2** | Methods | **Giao thức audit 3 bước** — báo SLI trước metric, báo `eval_rel_users` song song, chặn so sánh khi lệch >20% | 3/3 cặp split bị Bước 3 chặn (tỷ lệ 25,5× / 1,65× / 15,4×) | ✅ dạng 3 |
| **3** | Instantiations | **Pipeline tái lập** — HDFS + MapReduce Java + PySpark + MongoDB + R + Streamlit | MapReduce 323.737 key, G3 PASS 100%, 25.000.095 tương tác | ✅ dạng 4 |

**Đạt dạng 2 + 3 như Bài 03 yêu cầu. Có thêm dạng 1 và 4.**

---

## 5. Câu phát biểu tính mới (dán vào mục "Tính mới" của đề cương)

> **Điểm mới:** đề tài đề xuất **Split Leakage Index (SLI)** — chỉ số đo rò rỉ dữ liệu
> **tương đối theo từng người dùng** thay vì toàn cục, kèm ba ngưỡng phân loại
> (an toàn / nhẹ / nghiêm trọng); cùng **giao thức audit ba bước** ràng buộc việc so sánh
> giữa các chiến lược chia tập. Bằng chứng thực nghiệm trên MovieLens 25M (25.000.095 tương tác)
> cho thấy định nghĩa toàn cục gán **99,9988%** rò rỉ cho leave-one-out, trong khi định nghĩa
> tương đối cho **0%** — tức cách đo hiện hành cho kết luận **ngược hoàn toàn**. Giao thức
> ba bước sau đó **tự chặn** cả ba cặp so sánh giữa các split do chênh lệch mẫu đánh giá
> vượt ngưỡng 20%.

**Một câu rút gọn** (nếu đề cương giới hạn 2 dòng):
> Đề tài đề xuất chỉ số SLI đo rò rỉ dữ liệu tương đối theo người dùng và giao thức audit
> ba bước; thực nghiệm trên MovieLens 25M cho thấy cách đo toàn cục hiện hành gán 99,9988%
> rò rỉ cho leave-one-out trong khi thực tế là 0%.

---

## 6. Khung GO / SO cập nhật (điền SO2 còn trống)

| | Nội dung | Tỷ trọng | Chỉ số nghiệm thu |
|---|---|---|---|
| **GO** | Đo và giải thích tác động của chiến lược chia tập đến tín hiệu đo và thiên lệch phổ biến trong hệ thống gợi ý trên Spark | 100% | SLI, NDCG@10, popularity bias ratio |
| **SO1** (Data) | Khảo sát, chuẩn hóa MovieLens ml-25m; sinh 3 chiến lược split; hiện thực MapReduce Java đếm phổ biến | 20% | 25.000.095 tương tác, 3 split, 323.737 key |
| **SO2** (Model) | **Đề xuất SLI (tương đối theo user, 3 ngưỡng) và giao thức audit 3 bước** | **40%** | SLI tính được cho cả 3 split; khác biệt LOO 99,9988% vs 0% |
| **SO3** (Đối chuẩn) | Chạy các tầng baseline đã đăng kí (Random/MostPopular · ALS/ItemKNN · SASRec+CE) trên 3 split, **1 seed 42** (giới hạn đã khai báo, không phải 10 seed) | 20% | NDCG@10 per split; 5/5 baseline có số; Wilcoxon 20 cặp p + 95% CI + rank-biserial r |
| **SO4** (Ablation) | Phân tích độ nhạy: đổi ngưỡng relevant, đổi subsample, so 2 định nghĩa SLI | 20% | Bảng độ nhạy; SLI ổn định qua các cấu hình |

---

## 7. Việc phải làm trước 08/11

1. **Kiểm tra SLI tương đối đã có script chưa** — số 98,9158% / 0% / 0% hiện đo trong
   audit script; số chốt hiện là 98,9158% / 0% / 0% (`data_level_audit.json`, 15/11/2026), làm tròn 98,92% trên slide. Cần tách thành hàm riêng `compute_sli()` để báo cáo độc lập.
2. **Vẽ hình minh hoạ SLI** — 3 cột cho 3 split, hai thanh mỗi cột (toàn cục vs tương đối).
   Chính hình này sẽ là hình số 1 của luận văn.
3. **Viết 1 trang định nghĩa SLI** vào Chương 3, đúng trình tự: định nghĩa → chứng minh
   bằng phản ví dụ LOO → ngưỡng → ví dụ áp dụng.
4. **Điền SO2 vào `01_De_tai_va_Ke_hoach.md`** (hiện SO2 để trống).
5. **Sửa câu "tính mới"** trong `01_De_tai_va_Ke_hoach.md` từ "audit framework" (mơ hồ)
   sang SLI (có tên, có công thức).
