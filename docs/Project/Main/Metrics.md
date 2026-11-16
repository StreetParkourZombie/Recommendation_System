# Metrics — Định nghĩa chỉ số đánh giá

**Project:** `D:\Master Exers\Big Data\Recomendation_System`
**Cập nhật:** 2026-11-15 (bổ sung §4.5 — hai đường tính, hai bộ số)

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
| random80_20 | **100,0000%** | **98,9084%** |
| temporal_global | 0,0000% | 0,0000% |
| leave_one_out | 99,9988% | **0,0000%** |

→ Ngẫu nhiên 80/20 rò rỉ ở cả hai nghĩa. LOO "sạch" chỉ khi dùng định nghĩa tương đối.

### 1.2 `unseen_item_rows` — dịch chuyển miền item

```
unseen_item_rows = |{ r ∈ test : r.movieId ∉ distinct(train.movieId) }|
unseen_item_pct = 100 × unseen_item_rows / |test|
```

**Ý nghĩa:** tương tác kiểm định trỏ tới phim mà mô hình **chưa từng thấy** → không thể có trọng số → đo lỗi không tránh được.

**Kết quả đo thật:** `random80_20` 0,0559% · `temporal_global` **8,7594%** · `leave_one_out` 0,0388%.

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
| `subsample_users` | 30.000 (để tránh OOM trên `recommendForAllUsers`) |

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

1. **Thứ hạng mô hình không đảo chiều** (ALS > Popularity ở cả 3 split) — nhưng **độ lớn thay đổi 5,5 lần** (NDCG của ALS: 0,2584 → 0,0474). Kết luận “ALS cho NDCG cao” vẫn đúng, nhưng kết luận về *mức hiệu quả* thì phụ thuộc hoàn toàn vào chiến lược chia tập.
2. **Ngẫu nhiên 80/20 rò rỉ 98,91%** so với lịch sử của chính user → mọi metric trên split này là ước lượng lạc quan.
3. **Đổi rò rỉ lấy dịch chuyển miền**: temporal_global loại rò rỉ (0%) nhưng mất 96,1% mẫu đánh giá (158.688 → 6.219 user) và có 8,76% item chưa từng xuất hiện.
4. **Thiên lệch phổ biến**: Popularity 101–165× so với trung bình catalog; ALS chỉ 11–12×. Nhưng `longtail_coverage = 0` ở cả 6 tổ hợp → **giảm thiên lệch ≠ xử lý thiên lệch**.

---

---

## 4.4 Tầng kiểm định thống kê (đo thật 2026-11-04)

Nguồn (đường A): `scripts/11_peruser_ndcg.py` → `scripts/12_stats_tests.py` → `reports/stats_<split>.json`.
Các file `reports/stats_*` **đã bị gỡ khỏi repo** — số trong §4.4 giữ nguyên làm bản ghi lịch sử; chạy lại hai script trên để tái tạo.
Đường B (notebook 08) sinh `runs/<run_id>/outputs/peruser_ndcg_<split>.npz` — cùng định nghĩa chỉ số, khác đường top-K.

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

## 4.5 Hai đường tính — hai bộ số (bổ sung 2026-11-15)

Cùng một protocol (`project_protocol_v1`, seed 42, `rating ≥ 4,0`, K=10) nhưng có **hai đường code** cho ra số **hơi khác nhau**. Phải biết mình đang trích đường nào.

| | Đường A — script | Đường B — notebook |
|---|---|---|
| Thời điểm đo | 2026-11-04 | 2026-11-15 |
| Code | `scripts/04_audit_spark.py`, `scripts/11_peruser_ndcg.py` | `notebooks/jupyter/06`, `08` → `src/audit/popularity.py`, `src/audit/als_rec.py` |
| Tập user ALS | subsample 30.000 | subsample 30.000 (`orderBy("userId").limit(30000)`) |
| Đường top-K | Spark `F.aggregate` | numpy `topk_numpy` trên `U·Vᵀ` |
| Nguồn số | `D:\recsys_data\poc\poc6_*.json` | `runs/<run_id>/outputs/*_summary.json` |
| Truy vết | log file | `runs/` + checkpoint JSON + notebook `.executed.ipynb` |

### 4.5.1 Đối chiếu NDCG@10

| Split | Pop (A) | Pop (B) | ALS (A) | ALS (B) | ΔA | ΔB |
|---|---:|---:|---:|---:|---:|---:|
| `random80_20` | 0,0869 | 0,0852 | 0,2584 | 0,2556 | +0,1715 | +0,1704 |
| `temporal_global` | 0,0455 | 0,0455 | 0,1364 | 0,1311 | +0,0909 | +0,0856 |
| `leave_one_out` | 0,0183 | 0,0183 | 0,0474 | 0,0467 | +0,0291 | +0,0284 |

### 4.5.2 Đối chiếu chỉ số thiên lệch

| Split | Model | cov (A) | cov (B) | Gini (A) | Gini (B) | bias (A) | bias (B) |
|---|---|---:|---:|---:|---:|---:|---:|
| `random80_20` | Popularity | 0,000177 | 0,000177 | 0,9998 | 0,9998 | 158,64 | 158,5625 |
| `random80_20` | ALS | 0,061389 | 0,059388 | 0,9827 | 0,9890 | 12,26 | 12,6285 |
| `temporal_global` | Popularity | 0,000290 | 0,000290 | 0,9997 | 0,9997 | 101,26 | 101,2576 |
| `temporal_global` | ALS | 0,056629 | 0,060519 | 0,9713 | 0,9780 | 11,20 | 10,6271 |
| `leave_one_out` | Popularity | 0,000170 | 0,000170 | 0,9998 | 0,9998 | 165,27 | 165,2696 |
| `leave_one_out` | ALS | 0,061765 | 0,059659 | 0,9812 | 0,9879 | 12,41 | 12,7596 |

### 4.5.3 Vì sao lệch — và đường nào là chuẩn

Lệch **tuyệt đối nhỏ** (NDCG ≤ 0,0053; bias ratio ≤ 0,57). Nguyên nhân: đường A tính NDCG bằng `F.aggregate` trên tập user đánh giá do Spark chọn; đường B chọn user bằng `orderBy("userId").limit(30000)` rồi tính top-K bằng numpy. Hai tập user khác nhau một chút → trung bình khác một chút.

**Đường B là chuẩn từ 2026-11-15** khi báo cáo, vì:
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

---

## 5. Nguyên tắc báo cáo

1. **Mọi số phải truy được** về `runs/<run_id>/manifest.json` + `runs/<run_id>/checkpoints/` + `logs/notebooks/<run_id>.log` (đường B), hoặc `D:\recsys_data\poc\poc6_<split>.json` + `logs/audit_<timestamp>.log` (đường A). Nêu rõ đường nào.
2. **Không so sánh chéo split bằng NDCG thuần** — tập test khác nhau về bản chất. Phải đi kèm chỉ số cấp dữ liệu (`unseen_item_pct`, `temporal_violation_pct`) để giải thích **tại sao** NDCG khác nhau.
3. **Độ lớn quan trọng hơn thứ hạng tuyệt đối**: kết luận chính là *thứ hạng mô hình có đảo chiều không* dưới 3 split, và *popularity bias có biến mất không*.
