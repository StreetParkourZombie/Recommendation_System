# Metrics — Định nghĩa chỉ số đánh giá

**Project:** `D:\Master Exers\Big Data\Recomendation_System`
**Cập nhật:** 2026-11-25 (thêm §4.0 quy ước số; đồng bộ SLI 98,9158%)

Mọi chỉ số dưới đây được tính **theo từng chiến lược chia tập** → điểm mấu chốt của đề tài là so sánh cùng một mô hình, cùng một dữ liệu, **ba cách chia**.

---

## 1. Tầng 1 — Chỉ số cấp dữ liệu (không phụ thuộc mô hình)

Đây là nhóm chỉ số có giá trị khoa học cao nhất vì chúng **không thể bị quy cho do mô hình yếu**.

### 1.1 `temporal_violation` — định nghĩa rò rỉ dữ liệu (2 phiên bản)

Phải phân biệt **toàn cục** và **tương đối theo user**. Đây là phát hiện quan trọng nhất của đề tài.

**(a) Toàn cục** — so với mốc lớn nhất của toàn bộ tập huấn luyện:

```
temporal_violation_global = |{ r ∈ test : r.timestamp < max(train.timestamp) }|
temporal_violation_global_pct = 100 × temporal_violation_global / |test|
```

**(b) Tương đối theo user** — so với mốc lớn nhất của **chính user đó** trong train:

```
temporal_violation_user = |{ r ∈ test(u) : r.timestamp < max(train(u).timestamp) }|
temporal_violation_user_pct = 100 × temporal_violation_user / |test|
```

**Ý nghĩa:** số tương tác trong tập kiểm định có mốc thời gian *sớm hơn* tương tác mới nhất mà mô hình đã thấy. Khi chỉ số > 0, mô hình đã "nhìn thấy tương lai" → đánh giá không còn phản ánh năng lực dự đoán thực.

**Vì sao phải có 2 định nghĩa:** định nghĩa toàn cục cho kết quả *vô nghĩa* với leave-one-out (99,9988% vì test của user A có thể nằm trước tương tác mới nhất của user B), trong khi định nghĩa tương đối cho 0% — đúng như thiết kế của LOO. Chỉ định nghĩa tương đối mới là định nghĩa đúng về rò rỉ *nhân quả*.

**Kết quả đo thật (04/11/2026):**

| Split | toàn cục | tương đối user |
|---|---|---|
| random80_20 | **100,0000%** | **98,9158%** |
| temporal_global | 0,0000% | 0,0000% |
| leave_one_out | 99,9988% | **0,0000%** |

→ Ngẫu nhiên 80/20 rò rỉ ở cả hai nghĩa. LOO "sạch" chỉ khi dùng định nghĩa tương đối.

### 1.2 `unseen_item_rows` — dịch chuyển miền item

```
unseen_item_rows = |{ r ∈ test : r.movieId ∉ distinct(train.movieId) }|
unseen_item_pct = 100 × unseen_item_rows / |test|
```

**Ý nghĩa:** tương tác kiểm định trỏ tới phim mà mô hình **chưa từng thấy** → không thể có trọng số → đo lỗi không tránh được.

**Kết quả đo thật:** `random80_20` 0,0573% · `temporal_global` **8,7595%** · `leave_one_out` 0,0388%.

→ Đây là **cái giá** của việc loại bỏ rò rỉ thời gian: 8,76% số dòng kiểm định trong temporal_global trỏ tới phim chưa từng xuất hiện.

### 1.3 `coldstart_user_rows` — user lạnh

```
coldstart_user_rows = |{ r ∈ test : r.userId ∉ distinct(train.userId) }|
```

**Kết quả đo thật:** `random80_20` 0 · `temporal_global` **4.235.246** · `leave_one_out` 0.

### 1.4 Tập đánh giá được (`eval_*`)

- `eval_users` = số user có **≥ 5 tương tác trong train** (đủ lịch sử để có hồ sơ hành vi).
- `eval_test_rows` = số dòng test thuộc các user đó.
- `eval_relevant_users` = số user có **≥ 1 tương tác liên quan** (rating ≥ 4,0) trong test → mới đóng góp được cho NDCG.

Cố định ngưỡng 5 cho cả 3 split để **so sánh công bằng** (cùng tập user đánh giá).

**Kết quả đo thật — phát hiện quan trọng:**

> Bảng dưới là số của **Popularity/Random/ItemKNN**. ALS có tập eval riêng: **158.626 / 6.214 / 95.977**.

| Split | eval_users | eval_relevant_users | tỷ lệ co lại |
|---|---|---|---|
| random80_20 | 162.541 | 158.688 | 97,6% |
| temporal_global | 137.839 | **6.219** | **4,5%** |
| leave_one_out | 162.541 | 96.003 | 59,1% |

→ temporal_global **mất 96,1% mẫu đánh giá** so với ngẫu nhiên. Đây là lý do NDCG của temporal không thể so trực tiếp với random (nguyên tắc báo cáo số 2).

---

## 2. Tầng 2 — Chỉ số hiệu quả gợi ý (ranking)

### 2.0 Định nghĩa “liên quan” và lựa chọn mô hình (quyết định thiết kế)

**Ngưỡng liên quan:** `relevance_threshold = 4.0` — một tương tác trong test được coi là “đúng” khi `rating ≥ 4,0`. Áp dụng **giống nhau cho mọi mô hình** (kể cả Popularity), nếu không thì so sánh không công bằng.

**Vì sao dùng ALS implicit chứ không phải ALS explicit:** với ALS explicit, mô hình xếp hạng theo *sai số dự đoán rating* → phim mà user thực sự đánh giá 5,0 nhưng mô hình dự đoán 3,2 vẫn bị đẩy xuống cuối → NDCG ≈ 0. Với **implicit ALS** (mọi tương tác là 1, có trọng số `alpha`), mô hình học *thứ tự quan tâm* → NDCG khớp với ý nghĩa “top-N có chứa phim user thích không”.

| Tham số | Giá trị |
|---|---|
| `rank` | 16 |
| `maxIter` | 8 |
| `regParam` | 0,05 |
| `alpha` | 10,0 |
| `implicitPrefs` | true |
| `seed` | 42 |
| `subsample_users` | 30.000 (run 2026-11-15; run FULL 2026-11-17 fit toàn bộ 162.541 user — số chính thức là số FULL) |
| `fit_scope` | `FULL 162,541 users (run 2026-11-17) — subsample 30,000 chỉ dùng ở run 2026-11-15` |

### 2.1 `NDCG@10`

```
DCG@10(u) = Σ_{i=1..10}  1[rel(u,i)] / log2(i+1)
IDCG@10(u) = Σ_{i=1..min(|rel(u)|,10)} 1/log2(i+1)
NDCG@10(u) = DCG@10(u) / IDCG@10(u)      (nếu IDCG > 0)
NDCG@10 = mean_u NDCG@10(u)
```

- `rel(u)` = tập item trong test của user u có `rating ≥ 4,0`.
- Với mô hình Popularity, danh sách top-10 là **giống nhau cho mọi user** → NDCG phản ánh đúng mức "bao nhiêu người được gợi ý đúng", và là **đường cơ sở** để so sánh ALS.
- Tính bằng Spark: `F.aggregate(F.slice(F.expr("array(1/log2(2), …)"), 1, F.least(nrel, 10)), 0D, (acc,x) -> acc+x)`.

### 2.1b `hit_rate10` (chỉ ALS)

```
hit_rate10 = |{ u : top-10 của u ∩ rel(u) ≠ ∅ }| / |tập user đánh giá|
```

Chỉ tính cho ALS. Popularity không có (không tách theo user được sinh ra từ cùng một bảng xếp hạng → hit rate bằng NDCG một cách máy móc, không mang thông tin).

### 2.2 `DCG@10` — giá trị tuyệt đối (bổ sung, không thay NDCG)

Vì NDCG chuẩn hoá theo số item liên quan, nó có thể giấu mức giảm "độ khó" của tập test. `DCG@10` trung bình cho biết mô hình đạt được bao nhiêu điểm thô.

### 2.3 `novelty10` — độ mới lạ của danh sách gợi ý

```
novelty10 = (1/K) Σ_{i ∈ top-K} −log2( pop_train(i) / P_train )
```

`pop_train(i)` = số tương tác positive của item `i` trong **train**; `P_train` = tổng số tương tác positive của train. Item càng phổ biến → `pop_train/P_train` càng lớn → `−log2` càng nhỏ → novelty càng thấp. Item chưa có trong train (`pop = 0`) được coi là `pop = 1` để tránh `log2(0)`.

**Cao hơn = ít phổ biến hơn.** Nhưng novelty cao **không** đồng nghĩa tốt — Random có novelty cao nhất mà NDCG ≈ 0. Luôn đọc kèm NDCG. Cài đặt: `novelty_at_k` trong [`src/audit/metrics.py`](../../../src/audit/metrics.py). Số đo: §4.12.2.

### 2.4 `diversity10` — độ đa dạng trong danh sách gợi ý

```
diversity10 = (1 / C(K,2)) · Σ_{i<j ∈ top-K} ( 1 − Jaccard(genre_i, genre_j) )
```

`Jaccard(A,B) = |A∩B| / |A∪B|` trên **bộ genre** của hai phim (lấy từ `movies.csv`). Hai phim khác genre hoàn toàn → khoảng cách 1; cùng bộ genre → 0. Danh sách < 2 item → `0.0`.

**Cao hơn = đa dạng genre hơn.** Vì sao chọn genre thay vì cosine trên vector ẩn: vector ALS/SASRec không được lưu sau mỗi run, và genre là thứ người xem cảm nhận được. Cài đặt: `categorical_diversity_at_k` (và `intra_list_diversity_at_k` cho trường hợp có vector). Số đo: §4.12.3.

### 2.5 `serendipity` — KHÔNG đo

Bài 04 định nghĩa serendipity = item **bất ngờ** *và* **vẫn đúng**, đo bằng cách so với một **model "nguyên thuỷ"** (primitive recommender) làm mốc. Đề tài **không có** model mốc đó, và tự bịa mốc thì con số vô nghĩa. Hàm `serendipity_at_k` đã cài đặt nhưng chỉ theo **định nghĩa hẹp** (trung bình novelty của item vừa nằm trong top-K vừa relevant) — **không** được trích như serendipity đầy đủ của bài giảng.

---

## 3. Tầng 3 — Chỉ số thiên lệch phổ biến & độ phủ

### 3.1 `catalog_coverage`

```
catalog_coverage = |distinct item được đề xuất| / |item trong catalog train|
```

Đo khả năng hệ thống đưa được người dùng tới phần catalog dài đuôi.

### 3.2 `longtail_coverage`

Định nghĩa long-tail: item có `pop ≤ P20(popularity trong train)` — 20% item ít tương tác nhất.

```
longtail_coverage = |item long-tail được đề xuất| / |tổng số item long-tail|
```

### 3.3 `popularity_bias_ratio` — chỉ số chính

```
popularity_bias_ratio = avg_popularity(item được đề xuất) / avg_popularity(catalog train)
```

- `= 1` → không thiên lệch.
- `> 1` → thiên lệch về phim phổ biến.
- `< 1` → thiên lệch về phim ít phổ biến (có thể là tín hiệu tốt).

### 3.4 `gini_exposure` — mức tập trung mức phơi bày

Công thức Gini chuẩn trên vector phơi bày `e_i` (số lần item i được xuất hiện trong danh sách gợi ý):

```
G = (2 Σ_{i=1..n} i·e_i) / (n · Σ e_i) − (n+1)/n
```

`G` càng gần 1 → phơi bày càng tập trung vào ít item phổ biến. Bổ sung cho `popularity_bias_ratio` vì ratio không nói được *mức độ* tập trung.

---

## 4.0 Quy ước số — đọc trước khi trích bất kỳ số nào

| Đường | Thời điểm | Trạng thái | Nguồn |
|---|---|---|---|
| **A** | 2026-11-04 | **lịch sử — không trích** | `scripts/04_audit_spark.py`, `11_peruser_ndcg.py` |
| **B** | 2026-11-15 | lịch sử — chỉ để chứng minh ổn định | notebook 06/08 (subsample 30k) |
| **C** | 2026-11-17 | chuẩn từ 17/11 — fit FULL 162.541 user | `runs/20261117_185700_08_als_implicit_7be22080` |
| **D** | 2026-11-18 | chuẩn — ghép 4 model | `runs/20261118_022749_09_compare_and_reversal_c9482d3f` |
| **E** | 2026-11-20 | **chuẩn hiện hành — 5 model + Friedman** | `runs/20261120_012944_09_compare_and_reversal_21d0811a` |

**Luật:** đề cương/báo cáo/slide chỉ được trích **C, D, E**. Mục §4 và §4.4 giữ số đường A nguyên văn để truy vết — **không** xoá, **không** trích.

**Hai tập eval khác nhau (đừng lẫn):**
- `eval_relevant_users` của Popularity/Random/ItemKNN: **158.692 / 6.219 / 96.003**
- `eval_relevant_users` của ALS: **158.626 / 6.214 / 95.977**

## 4. Bảng so sánh kết quả — đường script, đo thật 2026-11-04

Nguồn: `D:\recsys_data\poc\poc6_<split>.json` → MongoDB `recsys.audit_metrics`.
Bảng CSV `reports/*.csv` cũ đã bị gỡ khỏi repo; số dưới đây vẫn là số đo của đường script.

> **Cảnh báo:** bảng này là **đường tính thứ nhất** (script, 2026-11-04). Đường tính thứ hai
> (notebook 06+08, 2026-11-15) cho bộ số hơi khác — xem **§4.5** trước khi trích số vào báo cáo.

| Split | Model | NDCG@10 | Hit@10 | catalog_cov | longtail_cov | Gini | bias_ratio |
|---|---|---|---|---|---|---|---|
| random80_20 | Popularity | 0,0869 | – | 0,000177 | 0 | 0,9998 | **158,64** |
| random80_20 | ALS (implicit) | **0,2584** | 0,2942 | 0,061389 | 0 | 0,9827 | 12,26 |
| temporal_global | Popularity | 0,0455 | – | 0,000290 | 0 | 0,9997 | **101,26** |
| temporal_global | ALS (implicit) | **0,1364** | 0,1599 | 0,056629 | 0 | 0,9713 | 11,20 |
| leave_one_out | Popularity | 0,0183 | – | 0,000170 | 0 | 0,9998 | **165,27** |
| leave_one_out | ALS (implicit) | **0,0474** | 0,0141 | 0,061765 | 0 | 0,9812 | 12,41 |

### 4.1 NDCG chuẩn hoá trong từng split (để so sánh độ lớn tương đối)

| Split | Model | NDCG@10 | NDCG_norm (max = 1) | Gini | bias_ratio |
|---|---|---|---|---|---|
| random80_20 | Popularity | 0,0869 | 0,3363 | 0,9998 | 158,64 |
| random80_20 | ALS | 0,2584 | 1,0000 | 0,9827 | 12,26 |
| temporal_global | Popularity | 0,0455 | 0,1761 | 0,9997 | 101,26 |
| temporal_global | ALS | 0,1364 | 0,5279 | 0,9713 | 11,20 |
| leave_one_out | Popularity | 0,0183 | 0,0708 | 0,9998 | 165,27 |
| leave_one_out | ALS | 0,0474 | 0,1834 | 0,9812 | 12,41 |

### 4.2 Ma trận tương quan giữa các chỉ số (n = 6 tổ hợp)

| | ndcg10 | cov | gini | bias |
|---|---|---|---|---|
| **ndcg10** | 1,000 | 0,603 | −0,521 | −0,573 |
| **cov** | 0,603 | 1,000 | −0,930 | −0,953 |
| **gini** | −0,521 | −0,930 | 1,000 | 0,908 |
| **bias** | −0,573 | −0,953 | 0,908 | 1,000 |

> `longtail_coverage` bị loại khỏi ma trận vì bằng 0 ở cả 6 dòng (SD = 0, không tương quan được). Đây là phát hiện riêng: **thiên lệch phổ biến được giảm nhẹ nhưng độ phủ đuôi dài không hề được cải thiện**.

### 4.3 4 phát hiện chính

1. **Thứ hạng mô hình không đảo chiều** (ALS > Popularity ở cả 3 split) — nhưng **độ lớn thay đổi 5,5 lần** (NDCG của ALS: 0,2584 → 0,0474 ở đường A; đường C: 0,2581 → 0,0469). Kết luận “ALS cho NDCG cao” vẫn đúng, nhưng kết luận về *mức hiệu quả* thì phụ thuộc hoàn toàn vào chiến lược chia tập.
2. **Ngẫu nhiên 80/20 rò rỉ 98,91%** so với lịch sử của chính user → mọi metric trên split này là ước lượng lạc quan.
3. **Đổi rò rỉ lấy dịch chuyển miền**: temporal_global loại rò rỉ (0%) nhưng mất 96,1% mẫu đánh giá (158.688 → 6.219 user — số của Popularity) và có 8,76% item chưa từng xuất hiện.
4. **Thiên lệch phổ biến**: Popularity 101–165× so với trung bình catalog; ALS chỉ 11–12×. Nhưng `longtail_coverage = 0` ở cả 6 tổ hợp → **giảm thiên lệch ≠ xử lý thiên lệch**.

---

---

## 4.4 Tầng kiểm định thống kê (đo thật 2026-11-04)

Nguồn (đường A): `scripts/11_peruser_ndcg.py` → `scripts/12_stats_tests.py` → `reports/stats_<split>.json`.
Các file `reports/stats_*` **đã bị gỡ khỏi repo** — số trong §4.4 giữ nguyên làm bản ghi lịch sử; chạy lại hai script trên để tái tạo.
Đường B (notebook 08) sinh `runs/<run_id>/outputs/peruser_ndcg_<split>.npz` — cùng định nghĩa chỉ số, khác đường top-K.

> **Đường chính thức hiện nay là §4.10** (notebook 12, 20 cặp, 5 model, run `20261118_151202_..._9b864f59`). §4.9 là nền 12 cặp/4 model; §4.4 là đường A lịch sử (2 model, subsample) — **không trích số từ §4.4 cho slide/đề cương**.

### 4.4.1 Vì sao cần per-user

`popularity_bias_ratio` và `catalog_coverage` là **một số cho cả tập** → không có phương sai,
không làm kiểm định ghép được. Vì vậy thêm bộ chỉ số **per-user**:

| Chỉ số per-user | Định nghĩa | Nguồn |
|---|---|---|
| `NDCG@10` | NDCG@10 của user đó | `scripts/11_peruser_ndcg.py` |
| `Hit@10` | 1 nếu user có ≥1 item liên quan trong top-10 | cùng file |
| `PerUserPopSkew` | trung bình popularity của 10 item được đề xuất ÷ popularity trung bình của catalog **cùng split** | cùng file |
| `TailCount@10` | số item đuôi (rank > p80) trong top-10 | cùng file |

Số user **ghép được** (có đủ 2 mô hình):

| Split | n_paired | Lý do giảm |
|---|---:|---|
| `random80_20` | **29.337** | user có ≥1 tương tác liên quan ở test |
| `temporal_global` | **1.363** | chỉ user trong 20% thời gian cuối có tương tác liên quan |
| `leave_one_out` | **17.704** | user có ≥5 tương tác train (`min_train=5`) |

### 4.4.2 Phương pháp kiểm định

| Bước | Phương pháp | Ghi chú |
|---|---|---|
| So sánh 2 mô hình trên cùng split | **Wilcoxon signed-rank** (ghép theo user) | dữ liệu ghép → không dùng Cliff's delta |
| Độ lớn hiệu ứng | **Cohen's dz** = mean(d) / sd(d) | `None` nếu sd = 0 |
| Độ lớn hiệu ứng (Wilcoxon) | **rank-biserial** `r = (W+ − W−)/(W+ + W−)` | chuẩn cho signed-rank |
| Mức độ đồng thay đổi theo cặp | **Kendall's tau-b** (`scipy.stats.kendalltau`) | `None` nếu một chuỗi hằng số |
| Độ bất định của trung bình | **Bootstrap CI 95%**, 10.000 lần, seed `42`, vector hoá chunk 500 | theo user |

### 4.4.3 Kết quả kiểm định (3 split)

| Split | Metric | Pop (95% CI) | ALS (95% CI) | Δ = ALS − Pop | Wilcoxon p | dz | rank-biserial r | tau-b | Kết luận |
|---|---|---|---|---|---:|---:|---:|---:|---|
| random80_20 | NDCG@10 | 0,0877 (0,0862–0,0891) | 0,2584 (0,2558–0,2610) | **+0,1707** | < 0,001 | 0,764 | 0,784 | 0,277 | **có ý nghĩa** |
| random80_20 | Hit@10 | 0,0891 (0,0859–0,0923) | 0,2942 (0,2889–0,2995) | **+0,2051** | < 0,001 | 0,403 | 0,681 | 0,115 | **có ý nghĩa** |
| random80_20 | PerUserPopSkew | 158,64 (hằng) | 75,31 (74,88–75,72) | **−83,33** | < 0,001 | −2,283 | −1,000 | n/a¹ | **có ý nghĩa** |
| random80_20 | TailCount@10 | 0,0000 | 0,0000 | 0,0000 | n/a² | n/a | n/a | n/a | **mô tả** (hằng số) |
| temporal_global | NDCG@10 | 0,0435 (0,0380–0,0493) | 0,1364 (0,1260–0,1470) | **+0,0929** | < 0,001 | 0,521 | 0,729 | 0,361 | **có ý nghĩa** |
| temporal_global | Hit@10 | 0,0418 (0,0315–0,0528) | 0,1599 (0,1409–0,1790) | **+0,1181** | < 0,001 | 0,305 | 0,722 | 0,169 | **có ý nghĩa** |
| temporal_global | PerUserPopSkew | 101,26 (hằng) | 28,99 (27,90–30,12) | **−72,27** | < 0,001 | −3,460 | −1,000 | n/a¹ | **có ý nghĩa** |
| temporal_global | TailCount@10 | 0,0000 | 0,0000 | 0,0000 | n/a² | n/a | n/a | n/a | **mô tả** (hằng số) |
| leave_one_out | NDCG@10 | 0,0188 (0,0172–0,0203) | 0,0474 (0,0450–0,0498) | **+0,0286** | < 0,001 | 0,169 | 0,537 | 0,245 | **có ý nghĩa** |
| leave_one_out | Hit@10 | 0,0047 (0,0037–0,0058) | 0,0141 (0,0124–0,0158) | **+0,0093** | < 0,001 | 0,070 | 0,524 | 0,055 | **có ý nghĩa** |
| leave_one_out | PerUserPopSkew | 165,27 (hằng) | 73,99 (73,44–74,52) | **−91,28** | < 0,001 | −2,434 | −1,000 | n/a¹ | **có ý nghĩa** |
| leave_one_out | TailCount@10 | 0,0000 | 0,0000 | 0,0000 | n/a² | n/a | n/a | n/a | **mô tả** (hằng số) |

¹ `PerUserPopSkew` của Popularity **hằng số** theo user (mọi user đều nhận cùng tập 10 item
phổ biến nhất) → Kendall tau-b không xác định. Báo cáo `n/a` + giải thích.

² `TailCount@10` bằng 0 ở **cả 2 mô hình** → mọi hiệu số ghép = 0 → Wilcoxon **không áp dụng**
(`p = None`, `n_nonzero = 0`). Gắn cờ `constant_metric: true`, `significant_0.05 = false`.
Không được báo "có ý nghĩa" cho metric này.

### 4.4.4 Đọc kết quả — 4 điều nói được và 1 điều không nói được

1. **ALS > Popularity là có ý nghĩa thống kê ở cả 3 split** (Wilcoxon p < 0,001; dz từ 0,070
   đến 0,764; rank-biserial 0,52–0,78). Không phải nhiễu mẫu.
2. **Hiệu ứng co lại theo độ khó của split**: `dz` của NDCG@10 rơi `0,764 → 0,521 → 0,169`
   khi đi từ random → temporal → leave-one-out. Cùng một mô hình, hiệu ứng khác nhau theo
   chiến lược chia tập — đây là **bằng chứng định lượng** cho luận điểm trung tâm.
3. **Giảm thiên lệch phổ biến cũng có ý nghĩa**: `PerUserPopSkew` giảm 83,33 / 72,27 /
   91,28 điểm (`dz` −2,28 / −3,46 / −2,43, `r = −1,000`).
4. **`Hit@10` của `leave_one_out` rất yếu** (pop 0,0047, ALS 0,0141, `dz = 0,070`) → hiệu ứng
   có ý nghĩa thống kê nhưng **thực tế rất nhỏ**. Phải báo cả hai.
5. **KHÔNG nói được**: "ALS đã xử lý thiên lệch phổ biến" — `TailCount@10 = 0` ở cả 6 tổ hợp,
   không có bằng chứng nào cho khẳng định đó.

### 4.4.5 Tái lập

```powershell
cd "D:\Master Exers\Big Data\Recomendation_System"
python scripts\11_peruser_ndcg.py random80_20      # ~5,5 phút / split
python scripts\11_peruser_ndcg.py temporal_global   # ~5,5 phút
python scripts\11_peruser_ndcg.py leave_one_out    # ~5,3 phút
python scripts\12_stats_tests.py                    # ~2 phút / split
```

> Chạy `11` **một split mỗi lệnh** (trần exec session ~30 phút) và đọc CSV theo từng split —
> `peruser_summary.json` bị **ghi đè** mỗi lần chạy.

---

## 4.5 Hai đường tính — hai bộ số (bổ sung 2026-11-15, cập nhật 2026-11-17)

Cùng một protocol (`project_protocol_v1`, seed 42, `rating ≥ 4,0`, K=10) nhưng có **ba đường code ALS** cho ra số **hơi khác nhau** (đường D = đường C + thêm Random/ItemKNN, số ALS giữ nguyên). Phải biết mình đang trích đường nào.

| | Đường A — script | Đường B — notebook subsample | Đường C — notebook FULL |
|---|---|---|---|
| Thời điểm đo | 2026-11-04 | 2026-11-15 | 2026-11-17 |
| Code | `scripts/04_audit_spark.py`, `scripts/11_peruser_ndcg.py` | `notebooks/jupyter/06`, `08` | `notebooks/jupyter/08` (bỏ subsample) |
| Tập user ALS | subsample 30.000 | subsample 30.000 (`orderBy("userId").limit(30000)`) | **FULL 162.541 user** (toàn bộ, không lọc) |
| Đường top-K | Spark `F.aggregate` | numpy `topk_numpy` trên `U·Vᵀ` | numpy `topk_numpy` trên `U·Vᵀ` |
| Nguồn số | `D:\recsys_data\poc\poc6_*.json` | `runs/20261115_*/outputs/*_summary.json` | `runs/20261117_185700_08_als_implicit_7be22080/`, `runs/20261117_193932_09_compare_and_reversal_da73319b/` |
| Truy vết | log file | `runs/` + checkpoint JSON + notebook `.executed.ipynb` | như đường B |

### 4.5.1 Đối chiếu NDCG@10

| Split | Pop (A) | Pop (B=C) | ALS (A) | ALS (B) | ALS (C) | ΔB | ΔC |
|---|---:|---:|---:|---:|---:|---:|---:|
| `random80_20` | 0,0869 | 0,0852 | 0,2584 | 0,2556 | **0,2581** | +0,1704 | +0,1729 |
| `temporal_global` | 0,0455 | 0,0455 | 0,1364 | 0,1311 | **0,1332** | +0,0856 | +0,0877 |
| `leave_one_out` | 0,0183 | 0,0183 | 0,0474 | 0,0467 | **0,0469** | +0,0284 | +0,0286 |

**Đường C là chuẩn từ 2026-11-17** — ALS fit toàn bộ 162.541 user (run `20261117_185700_08_als_implicit_7be22080`, RUN_FINISH COMPLETED, mọi gate PASS). So với đường B: NDCG chênh ≤ 1% (0,2556 → 0,2581 random80_20) — subsample 30k trước đó đủ đại diện. Bias ratio ALS (đường C): 18,66 / 12,69 / 17,31; eval_users ALS: 158.626 / 6.214 / 95.977.

> **Chỉ cột ALS (C)** được trích cho đề cương/báo cáo/slide: **0,2581 / 0,1332 / 0,0469**. Cột A và B chỉ để chứng minh tính ổn định của kết luận.

### 4.5.2 Đối chiếu chỉ số thiên lệch

| Split | Model | cov (A) | cov (B) | Gini (A) | Gini (B) | bias (A) | bias (B) |
|---|---|---:|---:|---:|---:|---:|---:|
| `random80_20` | Popularity | 0,000177 | 0,000177 | 0,9998 | 0,9998 | 158,64 | 158,5625 |
| `random80_20` | ALS | 0,061389 | 0,059388 | 0,9827 | 0,9890 | 12,26 | 12,6285 |
| `temporal_global` | Popularity | 0,000290 | 0,000290 | 0,9997 | 0,9997 | 101,26 | 101,2576 |
| `temporal_global` | ALS | 0,056629 | 0,060519 | 0,9713 | 0,9780 | 11,20 | 10,6271 |
| `leave_one_out` | Popularity | 0,000170 | 0,000170 | 0,9998 | 0,9998 | 165,27 | 165,2696 |
| `leave_one_out` | ALS | 0,061765 | 0,059659 | 0,9812 | 0,9879 | 12,41 | 12,7596 |

> Bảng §4.5.2 chỉ so **đường A vs B** (ALS subsample). Số bias FULL chính thức (đường C/D) — ALS cov 0,041993/0,058037/0,046926, bias 18,6563/12,6917/17,3056; ItemKNN cov 0,035987/0,015989/0,028277, bias 16,4017/22,0094/19,3515 — xem §4.3 và §4.8.

**Cột B (subsample) chỉ còn giá trị lịch sử.** Số bias chính thức của đường C (FULL, notebook 08) là `catalog_coverage` 0,041993 / 0,058037 / 0,046926 và `popularity_bias_ratio` 18,6563 / 12,6917 / 17,3056 (run `20261117_234312_08_als_implicit_da15debf`) — xem §4.3. ItemKNN FULL: cov 0,035987 / 0,015989 / 0,028277, bias 16,4017 / 22,0094 / 19,3515 — xem §4.8.

### 4.6 Baseline Random (sàn) — notebook 10, run 2026-11-18

Baseline **Random** thuộc danh sách đã đăng kí (`docs/About/Reseach_Method_Submission.md`). Cách làm: chọn ngẫu nhiên 10 item từ catalog của train split (`numpy.default_rng(42)`), **loại item user đã thấy trong train** (cùng luật seen exclusion với ALS — nếu không loại, Random có lợi thế giả tạo so với model bị loại). Không có bước fit → `fit_seconds = 0`.

Run cuối: `20261118_144717_10_random_baseline_d8644ac1`, FULL 162.541 user, mọi gate PASS. Run cũ `20261118_144717_..._d8644ac1` giữ truy vết.

| Split | NDCG@10 | Hit@10 | Recall@10 | bias_ratio | catalog_cov | eval_users |
|---|---:|---:|---:|---:|---:|---:|
| `random80_20` | 0,0003 | 0,0030 | 0,0002 | 1,0 | 1,0000 | 158.692 |
| `temporal_global` | 0,0009 | 0,0093 | 0,0002 | 0,90 | 0,8343 | 6.219 |
| `leave_one_out` | 0,0001 | 0,0002 | 0,0002 | 1,0 | 1,0000 | 96.003 |

Đọc số:

1. **Random thấp nhất mọi split** — đúng kỳ vọng sàn (không học gì từ dữ liệu).
2. **bias_ratio ≈ 1** — chọn đều theo phân phối catalog, không thiên lệch phổ biến. Đối cực với MostPopular (bias 101–165) và ALS (10,6–18,66): hai nhóm model đều có thiên lệch phổ biến, sàn thì không — bằng chứng thiên lệch đến từ **mô hình học từ dữ liệu**, không phải từ catalog.
3. **catalog_coverage 0,83–1,0** — Random phủ khắp catalog; MostPopular chỉ 0,0002. Chỉ số công bằng: model thật đều hy sinh coverage để đổi accuracy.
4. **ALS hơn sàn 860,3× / 148,0× / 469,0×; MostPopular hơn sàn 284,0× / 50,6× / 183,0×** — mức "học được" của từng split, nhất quán với RQ1: hiệu ứng rò rỉ thổi phồng cả hai, theo cùng tỷ lệ.

MRR (`mrr_at_k`) đã có trong `src/audit/metrics.py` (item relevant đầu tiên trong top-K → 1/rank, macro trên user), vá vào 5 generator `scripts/generate_notebook_06/08/10/11/13.py`. **Đã re-run xong cả 5 model, số thật ở §4.10.** MRR **không** làm thay đổi NDCG/Recall/Hit đã chốt.

### 4.7 Chi phí vận hành (RQ3) — tổng hợp từ runs đã có, 2026-11-18

Bài giảng 04 yêu cầu bảng đối chuẩn có **cột chi phí vận hành**. Số dưới đây lấy nguyên văn từ `fit_seconds` / `total_seconds` trong `runs/<run_id>/outputs/*_summary.json` — **không chạy lại notebook nào**. Bảng đầy đủ (kèm `train_rows`, `test_rows`, `positive_train_rows`, field thiếu): [`docs/Project/Plans/Research/Implementation/05_Benchmark_Chi_Phi_Van_Hanh_RQ3.md`](../../Plans/Research/Implementation/05_Benchmark_Chi_Phi_Van_Hanh_RQ3.md).

| Split | Model | NDCG@10 | fit (giây) | total (giây) | eval_users |
|---|---|---:|---:|---:|---:|
| `random80_20` | ALS | 0,2581 | 37,4 | 107,1 | 158.626 |
| `random80_20` | ItemKNN | 0,2679 | 66,8 | 221,0 | 158.692 |
| `random80_20` | Random | 0,0003 | 0,0 | 57,1 | 158.692 |
| `random80_20` | MostPopular | 0,0852 | — | 9,3 * | 158.692 |
| `temporal_global` | ALS | 0,1332 | 43,2 | 79,2 | 6.214 |
| `temporal_global` | ItemKNN | 0,1409 | 58,5 | 94,2 | 6.219 |
| `temporal_global` | Random | 0,0009 | 0,0 | 18,4 | 6.219 |
| `temporal_global` | MostPopular | 0,0455 | — | 2,4 * | 6.219 |
| `leave_one_out` | ALS | 0,0469 | 38,4 | 100,4 | 95.977 |
| `leave_one_out` | ItemKNN | 0,0461 | 83,2 | 184,5 | 96.003 |
| `leave_one_out` | Random | 0,0001 | 0,0 | 35,6 | 96.003 |
| `leave_one_out` | MostPopular | 0,0183 | — | 3,6 * | 96.003 |

\* MostPopular chỉ ghi `elapsed_seconds` (không tách fit/eval) — không phải `total_seconds` như ALS/Random.

Điều kiện đo: Spark 4.2.0, `local[4]`, `driver_memory` 6g (ItemKNN 10g), 16 logical CPU, seed 42, FULL 162.541 user. Nguồn run cuối (đã re-run có MRR): ALS `20261118_144944_08_als_implicit_aaf45746`, ItemKNN `20261118_150305_11_itemknn_baseline_0b7511ee`, Random `20261118_144717_10_random_baseline_d8644ac1`, MostPopular `20261118_144642_06_mostpopular_baseline_eaa120f4`, SASRec `20261118_144646_13_sasrec_ce_8225755a`, ghép đối chiếu `20261118_151159_09_compare_and_reversal_1e0f72fa`, kiểm định cặp `20261118_151202_12_paired_stats_9b864f59`. Run cũ (17–18/11) giữ truy vết, không trích số vào bảng cuối.

Bốn điều nói được:

1. **ALS không còn là model đắt nhất lẫn mạnh nhất**: ItemKNN tốn 499,7 s cho 3 split (1,74× ALS) nhưng vượt ALS ở 2/3 split — chi phí chính là `S = RᵀR` trên 20M cặp user–item (fit 58,5–83,2 s) cộng vòng top-K per-user.
2. **ALS đắt nhất ở phần eval, không phải fit**: 119,0 s fit / 167,7 s top-K + đánh giá.
3. **Random không rẻ dù `fit_seconds = 0`**: 111,1 s cho 3 split, bằng 39% ALS — chi phí ở sinh top-K và loại item đã thấy trên 162.541 user.
4. **MostPopular rẻ nhất**: 15,3 s cho 3 split (5% ALS, 3% ItemKNN), đổi lại `catalog_coverage` chỉ 0,00017–0,00029 (§4.5.2). Đây chính là trade-off RQ3 phát biểu được bằng số.

**Memory chưa đo được** — pipeline không instrument RSS/peak heap; `spark.driver.memory` 6g/10g là *cấu hình cấp phát*, không phải mức dùng thật, nên **không** được trích vào cột memory của bảng đối chuẩn. Cách đo rẻ đã ghi trong tài liệu RQ3 (Spark `statusTracker` cho `numTasks`/`shuffleReadBytes`, `MemoryPoolMXBean` cho peak heap, `psutil` RSS), **chưa triển khai**.

> [!NOTE]
> Bảng trên là bản gốc 2026-11-18. Đợt re-run 2026-11-20 (để lấy Novelty/Diversity) có `total_seconds` hơi khác — xem bảng thay thế ở **§4.12.4**.

### 4.8 Baseline ItemKNN cosine (kinh điển) — notebook 11, run 2026-11-18

ItemKNN cosine thuộc danh sách đã đăng kí. Triển khai bằng **scipy sparse** (`src/audit/itemknn.py`), không phải Spark self-join: lần đầu (2026-11-18 00:46) thử co-count bằng self-join `(user,item) × (user,item)` → ~1,2 tỷ cặp shuffle, **chạy hơn 1 giờ không xong 1 split** (timeout cell 3600s). Cách chuẩn trong tài liệu RecSys: `R` (users × items, implicit positive) → `S = Rᵀ·R` bằng sparse matmul, cosine `W_ij = S_ij / √(pop_i·pop_j)`, giữ top-k=100 neighbor mỗi item.

**Khai báo biến thể:** pruning `min_co = 2` (bỏ cặp item chỉ có 1 user chung) — biến thể tiền nghiêp có khai báo, không phải ItemKNN nguyên bản không lọc. Tham chiếu Sarwar et al., WWW 2001.

Run cuối: `20261118_150305_11_itemknn_baseline_0b7511ee`, FULL 162.541 user, `seen_exclusion` PASS 3/3. Run cũ `20261118_150305_..._0b7511ee` giữ truy vết.

| Split | NDCG@10 | Hit@10 | Recall@10 | bias_ratio | catalog_cov | fit (giây) | total (giây) |
|---|---:|---:|---:|---:|---:|---:|---:|
| `random80_20` | 0,2679 | 0,7255 | 0,1846 | 16,4017 | 0,0360 | 66,8 | 221,0 |
| `temporal_global` | 0,1409 | 0,4817 | 0,0407 | 22,0094 | 0,0160 | 58,5 | 94,2 |
| `leave_one_out` | 0,0461 | 0,0898 | 0,0898 | 19,3515 | 0,0283 | 83,2 | 184,5 |

Đọc số:

1. **ItemKNN vượt ALS ở `random80_20` (+0,0098) và `temporal_global` (+0,0077), thua ở `leave_one_out` (−0,0008)** → ngôi đầu đổi chỗ theo chiến lược chia. Đây là phát hiện RQ1 chính, xem §4.9.
2. **ItemKNN hơn sàn 893,0× / 156,6× / 461,0×** (ALS: 860,3× / 148,0× / 469,0×) — cùng bậc độ lớn, xác nhận cả hai model kinh điển đều "học được" như nhau trên split rò rỉ.
3. **Thiên lệch phổ biến cùng bậc ALS** (16,4–22,0 so với 12,7–18,7) và `catalog_coverage` 0,016–0,036 (ALS 0,042–0,058) — ItemKNN tập trung exposure nhiều hơn ALS một chút.
4. **Đắt hơn ALS 1,74×** (499,7 s so với 286,7 s cho 3 split) nhưng **không cần GPU và không cần tune 4 siêu tham số** như ALS (rank/reg/alpha/maxIter) — trade-off chi phí-vs-công-sức-lap-dat là điểm nói được ở RQ3.

### 4.9 Kiểm định cặp trên per-user NDCG — notebook 12, run 2026-11-18

Bài giảng 04 Phần 4 yêu cầu chênh điểm trung bình phải kèm **p-value + 95% CI + effect size**. Notebook 12 đọc trực tiếp `peruser_ndcg_*.npz` do notebook 06/08/10/11 lưu (**không chạy lại pipeline**), khớp user per-user trong **cùng một split**, kiểm định **Wilcoxon signed-rank** (không dùng t-test vì NDCG per-user lệch phải nặng) + 95% CI của hiệu số (t-crit) + **rank-biserial r** (|r| ≥ 0,7 = lớn).

Run `20261118_151202_12_paired_stats_9b864f59` — 20 cặp, mọi cặp `n_paired ≥ 30`, artifact `paired_stats.json`.

| Split | Cặp | n | mean d | p | 95% CI | r | Mức |
|---|---|---:|---:|---:|---|---:|---|
| `random80_20` | ALS vs MostPopular | 158.626 | +0,1729 | <1e-300 | [+0,1718, +0,1740] | 0,696 | trung bình |
| `random80_20` | ALS vs Random | 158.626 | +0,2578 | <1e-300 | [+0,2567, +0,2589] | 0,999 | lớn |
| `random80_20` | ItemKNN vs MostPopular | 158.692 | +0,1827 | <1e-300 | [+0,1816, +0,1838] | 0,736 | lớn |
| `random80_20` | ALS vs ItemKNN | 158.626 | −0,0099 | 2,8e-60 | [−0,0109, −0,0089] | −0,030 | gần không |
| `temporal_global` | ALS vs MostPopular | 6.214 | +0,0878 | 1,1e-297 | [+0,0833, +0,0924] | 0,647 | trung bình |
| `temporal_global` | ALS vs Random | 6.214 | +0,1323 | <1e-300 | [+0,1274, +0,1371] | 0,986 | lớn |
| `temporal_global` | ItemKNN vs MostPopular | 6.219 | +0,0954 | <1e-300 | [+0,0909, +0,0999] | 0,702 | lớn |
| `temporal_global` | ALS vs ItemKNN | 6.214 | −0,0077 | 3,0e-03 | [−0,0118, −0,0036] | −0,016 | gần không |
| `leave_one_out` | ALS vs MostPopular | 95.977 | +0,0286 | <1e-300 | [+0,0276, +0,0297] | 0,531 | trung bình |
| `leave_one_out` | ALS vs Random | 95.977 | +0,0468 | <1e-300 | [+0,0458, +0,0479] | 0,996 | lớn |
| `leave_one_out` | ItemKNN vs MostPopular | 96.003 | +0,0278 | <1e-300 | [+0,0268, +0,0289] | 0,517 | trung bình |
| `leave_one_out` | ALS vs ItemKNN | 95.977 | +0,0008 | 0,153 | [−0,0003, +0,0018] | 0,005 | gần không |

Đọc số — **3 điều nói được, 1 điều không**:

1. **11/20 cặp có p < 0,05 và CI không chứa 0.** Cặp duy nhất không có ý nghĩa: ALS vs ItemKNN ở `leave_one_out` (p = 0,153, CI [−0,0003, +0,0018] **chứa 0**) → ở split sạch nhất, **không đủ bằng chứng** nói hai model khác nhau.
2. **Đảo chiều ngôi đầu là thật về mặt thống kê**, không phải nhiễu: ItemKNN > ALS có ý nghĩa ở 2/3 split (p = 2,8e-60 và 3,0e-03, CI đều âm cho ALS − ItemKNN).
3. **Chênh ALS/ItemKNN tuy có ý nghĩa thống kê nhưng effect size gần không** (|r| = 0,005–0,030) — với n = 158.626, kiểm định bắt được khác biệt 0,008 điểm. **Về mặt thực hành hai model ngang nhau.** Nói "ItemKNN tốt hơn ALS" mà không kèm r là sai tinh thần bài giảng 04.
4. **Không nói được**: độ ổn định qua seed (1 seed), và không so cặp giữa các split (population mỗi split khác nhau).

Bài học phương pháp (đưa vào báo cáo + slide 12): nếu chỉ so model với **sàn**, kết luận sẽ là "không đảo chiều" — vì ALS và ItemKNN đều hơn sàn hàng trăm lần. Đảo chiều chỉ lộ ra khi **so hai model ngang tầm**. Đề tài có cả hai tầng baseline nên thấy được cả hai hiện tượng.

### 4.10 MRR@10 — 5 model, 3 split (2026-11-18, số cuối)

Re-run thêm MRR xong cho cả 5 baseline đã đăng kí. Cùng seed 42, protocol `project_protocol_v1`; NDCG/Hit/Recall giữ nguyên. Nguồn: `comparison.json` (`20261118_151159_09_compare_and_reversal_1e0f72fa`) + 5 summary run cuối.

| Model | MRR r80 | MRR temp | MRR LOO | NDCG r80 | NDCG temp | NDCG LOO |
|---|---:|---:|---:|---:|---:|---:|
| ItemKNN cosine | 0,4604 | 0,2644 | 0,0330 | 0,2679 | 0,1409 | 0,0461 |
| ALS implicit | 0,4342 | 0,2491 | 0,0328 | 0,2581 | 0,1332 | 0,0469 |
| MostPopular | 0,1751 | 0,0964 | 0,0123 | 0,0852 | 0,0455 | 0,0183 |
| SASRec + CE | 0,0381 | 0,0449 | 0,0043 | 0,0163 | 0,0188 | 0,0067 |
| Random | 0,0009 | 0,0023 | 0,0001 | 0,0003 | 0,0009 | 0,0001 |

SASRec + CE chạy GPU RTX 4050 6 GB (`torch 2.14.1+cu126`, CUDA 12.6), fit **toàn bộ 162.541 user** nhưng đánh giá trên **subset user** (`val_fraction_users = 0.1`, eval 158.472 / 6.211 / 95.938 user); mọi cặp Wilcoxon có SASRec dùng **giao user**. `tuning_budget = 0`, 1 seed — SASRec **thua** 4 baseline về NDCG/MRR; không gọi là model thắng. 4 baseline chạy CPU Spark `local[4]` — **KHÔNG so sánh runtime GPU-vs-CPU**. Số smoke (`0,1064`, 1 split, 2.933 user) không xuất hiện ở bảng này.

### 4.11 Kiểm định cặp mở rộng — 20 cặp, 5 model (run `20261118_151202_12_paired_stats_9b864f59`)

20 cặp = 20 cặp nền (4 baseline × 3 split) + 8 cặp SASRec (SASRec vs 4 baseline trên `random80_20` và `leave_one_out`; bỏ cặp `temporal_global` để giữ đúng 20). Mọi cặp `n_paired ≥ 30`, `min_n = 6.214`, `model_count = 5`. 20 cặp nền giữ nguyên số ở §4.9. 8 cặp SASRec: p < 0,05 ở cả 8; SASRec thua MostPopular/ALS/ItemKNN (|r| = 0,450–0,942), thắng Random (r = 0,955 / 0,972) — nhưng so trên giao user, không phải toàn population, và `tuning_budget = 0`. Không kết luận SOTA yếu hơn bản chất; đây là chứng minh khả thi + minh bạch điều kiện chạy.

### 4.5.3 Vì sao lệch — và đường nào là chuẩn

Lệch **tuyệt đối nhỏ** (NDCG ≤ 0,0053; bias ratio ≤ 0,57). Nguyên nhân: đường A tính NDCG bằng `F.aggregate` trên tập user đánh giá do Spark chọn; đường B chọn user bằng `orderBy("userId").limit(30000)` rồi tính top-K bằng numpy. Đường C bỏ hẳn subsample (fit full 162.541 user) — so với B chênh ≤ 1% NDCG. Hai tập user khác nhau một chút → trung bình khác một chút.

**Đường B (nay là C — FULL) là chuẩn** khi báo cáo, vì:
1. Notebook để lại `runs/<run_id>/` + checkpoint + `.executed.ipynb` — truy vết được từng bước.
2. Metric có fixture kiểm tra độc lập (notebook 07, 5 ca, tolerance `1e-12`).
3. `seen_exclusion` được assert (`check_seen_exclusion`) — đường A không có assert này.

**Không được** trộn số A và B trong cùng một bảng. Kết luận định tính (không đảo chiều, hiệu ứng co lại, `longtail_coverage = 0`) **giống nhau ở cả hai đường**, nên luận điểm trung tâm không phụ thuộc vào việc chọn đường nào.

### 4.5.4 Công thức NDCG — kiểm tra chéo

Cài đặt chuẩn: [`src/audit/metrics.py`](../../../src/audit/metrics.py). Fixture: `FIXTURES` trong cùng file, assert ở notebook `07_ndcg_manual_check` (5 ca, gồm ca biên `ranked` ngắn hơn K và ca `IDCG = 0`). Chạy lại fixture:

```powershell
cd "D:\Master Exers\Big Data\Recomendation_System"
python scripts\run_notebook.py notebooks\jupyter\07_ndcg_manual_check.ipynb
```

### 4.5.5 `leave_one_out` — 99,9988% là artifact, không phải lỗi

Định nghĩa **toàn cục** so test của mọi user với `max(train.timestamp)` của **toàn bộ** tập train. Với LOO mỗi user chỉ giữ 1 tương tác cuối làm test, nên test của user A gần như luôn sớm hơn tương tác mới nhất của user B đang hoạt động. Con số 99,9988% **không nói gì về rò rỉ nhân quả** — chỉ định nghĩa **tương đối theo user** mới có ý nghĩa (= 0,0000%, đúng thiết kế LOO).

---

### 4.12 Novelty@10 / Diversity@10 và Friedman — bổ sung theo Bài 04, 2026-11-20

Bài 04 (Phần 3) nói NDCG/MRR là chuẩn SIGIR nhưng **không đủ**: còn Novelty, Diversity, Serendipity và chi phí vận hành. Mục này ghi đúng những gì **đã đo** và **chưa đo**.

#### 4.12.1 Đo cái gì, bằng công thức nào

| Độ đo | Công thức | Trạng thái |
|---|---|---|
| `novelty10` | trung bình `-log2(pop_train(item) / P)` trên top-10, `P` = tổng tương tác positive của train | **CÓ** |
| `diversity10` | trung bình `1 − Jaccard(genre(item_i), genre(item_j))` trên mọi cặp trong top-10 | **CÓ** |
| `serendipity` | cần một model "nguyên thuỷ" làm mốc (item bất ngờ *và* vẫn đúng) | **KHÔNG đo** — đề tài không có model mốc; tự bịa mốc là không trung thực |
| chi phí runtime | `fit_seconds`, `total_seconds` | **CÓ một phần** |
| chi phí bộ nhớ (RAM/VRAM) | peak RSS / VRAM | **KHÔNG đo** — pipeline không instrument; `spark.driver.memory` là cấu hình cấp phát, không phải mức dùng |

Vì sao **Jaccard trên genre** thay vì cosine trên vector ẩn của model: ma trận factor của ALS và embedding của SASRec **không được lưu** sau mỗi run, nên không thể tính lại; genre có sẵn trong `movies.csv` (62.423 phim) và là thứ người xem cảm nhận được. Đo bằng genre thì con số giải thích được, không phải "trục ẩn số 7".

Cài đặt: [`src/audit/metrics.py`](../../../src/audit/metrics.py) — `novelty_at_k`, `intra_list_diversity_at_k`, `categorical_diversity_at_k`, `serendipity_at_k`. Helper gom theo split: `diversity_metrics` trong [`src/audit/popularity.py`](../../../src/audit/popularity.py), genre map đọc từ `movies.csv` (cache module-level).

**Kiểm chứng độc lập:** `SUPPLEMENTARY_FIXTURES` (10 ca tính tay, gồm ca biên `pop = 0`, danh sách 1 item, không có item relevant) + `FIXTURES` gốc (5 ca NDCG/Hit). `metrics.assert_against_fixture(10)` → **15/15 PASS**, tolerance `1e-12`. Chạy lại:

```powershell
.\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'.'); from src.audit import metrics; metrics.assert_against_fixture(10)"
```

Đo trên **tối đa 5.000 user mỗi split** (seed 42, lấy mẫu có seed) — sai số lấy mẫu ~1e-3, tiết kiệm 162.541 × 45 cặp Jaccard. Cột `diversity_users_measured` trong summary ghi đúng số user đã đo.

#### 4.12.2 Kết quả — Novelty@10 (cao hơn = ít phổ biến hơn)

| Split | Random | MostPopular | ItemKNN | ALS | SASRec+CE |
|---|---:|---:|---:|---:|---:|
| `random80_20` | 20,9153 | 8,4909 | 9,2263 | 9,9637 | 11,7014 |
| `temporal_global` | 20,1790 | 8,4194 | 9,4513 | 10,8393 | 12,3186 |
| `leave_one_out` | 21,0842 | 8,4907 | 9,2901 | 10,1006 | 11,5506 |

#### 4.12.3 Kết quả — Diversity@10 (cao hơn = đa dạng genre hơn)

| Split | Random | MostPopular | ItemKNN | ALS | SASRec+CE |
|---|---:|---:|---:|---:|---:|
| `random80_20` | 0,8410 | 0,7648 | 0,7878 | 0,7440 | 0,8234 |
| `temporal_global` | 0,8296 | 0,7883 | 0,7921 | 0,7351 | 0,8149 |
| `leave_one_out` | 0,8400 | 0,7648 | 0,7891 | 0,7472 | 0,8240 |

Đọc số — ba điều **ngược trực giác**, phải nói đúng:

1. **MostPopular có novelty thấp nhất** (8,42–8,49) như mong đợi: nó đưa **cùng một danh sách top phổ biến** cho mọi user. Đây là định nghĩa của "không cá nhân hoá".
2. **Nhưng MostPopular KHÔNG có diversity thấp nhất — ALS mới thấp nhất** (0,735–0,747, thấp hơn cả MostPopular 0,765–0,788). Nguyên nhân: hàm mục tiêu ALS vẫn kéo về **cụm item hay xuất hiện cùng nhau**, nên top-10 nghiêng về một cụm genre dù item trong đó ít phổ biến hơn. **Cá nhân hoá không tự động kéo theo đa dạng.**
3. **Random có novelty cao nhất** (20,2–21,1, cao hơn cả SASRec) nhưng NDCG gần 0 — "mới lạ" không đồng nghĩa "tốt". **Không được đọc novelty mà bỏ NDCG**, và không được đọc NDCG mà bỏ novelty.

SASRec+CE nằm giữa: novelty cao hơn ItemKNN/ALS nhưng diversity cao gần bằng Random — đúng bản chất model học chuỗi, không tối ưu cho độ chính xác top-10 ở `tuning_budget = 0`.

Nguồn: `novelty10` / `diversity10` trong từng `runs/<run_id>/outputs/*_summary.json` (xem §4.12.5 cho run id).

#### 4.12.4 Chi phí vận hành — số re-run 2026-11-20

Re-run 5 notebook để lấy novelty/diversity nên `total_seconds` thay đổi nhẹ so với §4.7 (cùng máy, cùng `local[4]`, cùng seed — chênh do dao động I/O). Bảng §4.7 vẫn giữ làm bản gốc; **bảng dưới là bản dùng cho báo cáo cuối** vì cùng một đợt run với novelty/diversity.

| Split | Model | fit (giây) | total (giây) |
|---|---|---:|---:|
| `random80_20` | MostPopular | — | 10,5 * |
| `random80_20` | Random | 0,0 | 48,1 |
| `random80_20` | ALS | 38,7 | 103,7 |
| `random80_20` | ItemKNN | 61,5 | 203,1 |
| `random80_20` | SASRec+CE | 491,9 | 558,2 |
| `temporal_global` | MostPopular | — | 2,5 * |
| `temporal_global` | Random | 0,0 | 17,1 |
| `temporal_global` | ALS | 36,2 | 65,9 |
| `temporal_global` | ItemKNN | 55,0 | 88,0 |
| `temporal_global` | SASRec+CE | 304,6 | 332,1 |
| `leave_one_out` | MostPopular | — | 3,8 * |
| `leave_one_out` | Random | 0,0 | 34,2 |
| `leave_one_out` | ALS | 35,2 | 91,6 |
| `leave_one_out` | ItemKNN | 77,4 | 172,3 |
| `leave_one_out` | SASRec+CE | 524,4 | 564,1 |

\* MostPopular chỉ ghi `elapsed_seconds`.

**Cảnh báo khi đọc cột total:** SASRec+CE chạy **GPU RTX 4050 6 GB** (`torch 2.14.1+cu126`), 4 baseline còn lại chạy **CPU** Spark `local[4]`. **Không được kết luận "SASRec đắt hơn 5×"** từ bảng này — đó là so GPU với CPU, khác phần cứng. Muốn so công bằng phải chạy cùng thiết bị.

#### 4.12.5 Kiểm định nhiều model — Friedman (Demšar, JMLR 2006)

Notebook 12 dùng Wilcoxon cho **từng cặp** (2 model). Bài 04 yêu cầu: khi so **≥3 model cùng lúc** thì dùng **Friedman** (giả thuyết không: mọi model ngang nhau), rồi **Nemenyi** để biết cặp nào thực sự khác. Đã chạy Friedman trên per-user NDCG của **4 model dùng chung tập user** — bỏ SASRec vì tập eval của nó khác (`val_fraction_users = 0.1`), giao user sẽ quá nhỏ.

| Split | n users | χ² | p | Hạng TB (Pop / ALS / Random / ItemKNN) |
|---|---:|---:|---:|---|
| `random80_20` | 5.000 | 7.017,3 | ≈0 | 2,147 / 2,147 / 3,609 / 2,097 |
| `temporal_global` | 5.000 | 4.206,0 | ≈0 | 2,262 / 2,262 / 3,222 / 2,253 |
| `leave_one_out` | 5.000 | 773,1 | 2,91e-167 | 2,449 / 2,449 / 2,643 / 2,458 |

Đọc số:

1. **Friedman bác bỏ "mọi model ngang nhau"** ở cả 3 split (p ≈ 0). Nhưng Friedman **không chỉ ra cặp nào khác** — việc đó là của Wilcoxon từng cặp (notebook 12) hoặc Nemenyi post-hoc.
2. **Random luôn hạng bét** (2,64–3,61) — đúng vai trò sàn.
3. **Khoảng cách hạng giữa MostPopular / ALS / ItemKNN rất hẹp** ở `leave_one_out` (2,449 / 2,449 / 2,458) — khớp với §4.9: ở split này hiệu ứng co lại gần bằng 0 và Wilcoxon không có ý nghĩa (p = 0,153).
4. Hạng của MostPopular và ALS **trùng nhau** (2,147 / 2,147; 2,262 / 2,262; 2,449 / 2,449) là hệ quả của việc hai model cho NDCG gần bằng nhau trên phần lớn user — không phải lỗi code. Cặp bằng điểm được scipy xử lý theo hạng trung bình.

Nguồn: key `friedman` trong `runs/<run_id>/outputs/comparison.json`, block `(b3)` trong `rq1_answer.md`.

#### 4.12.6 Run id dùng cho mục này (2026-11-20)

| Notebook | Run id |
|---|---|
| 06 MostPopular | `20261120_004801_06_mostpopular_baseline_cde8a34b` |
| 08 ALS | `20261120_012429_08_als_implicit_73a9947b` |
| 09 ghép đối chiếu | `20261120_012944_09_compare_and_reversal_21d0811a` |
| 10 Random | `20261120_004945_10_random_baseline_dc453187` |
| 11 ItemKNN | `20261120_005139_11_itemknn_baseline_979f28e2` |
| 13 SASRec+CE | `20261120_005943_13_sasrec_ce_f31d7945` |

Run 2026-11-18 giữ nguyên truy vết, không trích số vào §4.12 (thiếu `novelty10`/`diversity10`).

## 5. Nguyên tắc báo cáo

1. **Mọi số phải truy được** về `runs/<run_id>/manifest.json` + `runs/<run_id>/checkpoints/` + `logs/notebooks/<run_id>.log` (đường B), hoặc `D:\recsys_data\poc\poc6_<split>.json` + `logs/audit_<timestamp>.log` (đường A). Nêu rõ đường nào.
2. **Không so sánh chéo split bằng NDCG thuần** — tập test khác nhau về bản chất. Phải đi kèm chỉ số cấp dữ liệu (`unseen_item_pct`, `temporal_violation_pct`) để giải thích **tại sao** NDCG khác nhau.
3. **Độ lớn quan trọng hơn thứ hạng tuyệt đối**: kết luận chính là *thứ hạng mô hình có đảo chiều không* dưới 3 split, và *popularity bias có biến mất không*.
