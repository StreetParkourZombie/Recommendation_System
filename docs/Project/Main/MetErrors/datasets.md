# Error Log — Dataset & nhãn

Lỗi liên quan hiểu sai dữ liệu, schema, và rò rỉ. Tất cả đều **do thật, đo thật** bằng
script trong `scripts/` hoặc `scratch/`.

Format: `### [YYYY-MM-DD] [Category] Title` → Vấn đề / Nguyên nhân / Bằng chứng / Giải pháp

---

## 1. Bốn ca hiểu sai dữ liệu — cùng một dạng lỗi

### [2026-10-29] [Scope] `foitext` chỉ có 2022–2025 — không phải toàn bộ corpus

- **Vấn đề:** Plan v1 ghi "26,5 triệu báo cáo MAUDE có narrative", dẫn từ openFDA API.
  Khi đếm trên đĩa: chỉ **10.800.548 / 23.633.176 = 45,70%** báo cáo có narrative.
  (Số đo lại 2026-10-30 sau khi sửa parser — xem §6.)

- **Nguyên nhân:** FDA cắt `foitext20XX.zip` theo **năm nhận báo cáo**. Trên FTP area
  chỉ tồn tại `foitext2022` … `foitext2025`. Trước 2022 **không có file narrative**.
  openFDA API thì trả narrative cho mọi bản ghi nó có — kể cả bản ghi mà narrative
  không nằm trong file tải về.

- **Bằng chứng đo được:**
  ```
  master hợp lệ                : 23.633.176
  DATE_RECEIVED ∈ 2022..2025   : 10.800.548  (45,70%)
  foitext union 4 năm          : 10.799.941 report
  ```

- **Giải pháp:** Cohort phân tích = **2022-01-01 → 2025-12-31, 10.800.548 báo cáo**.
  Toàn bộ 23,6M chỉ dùng làm *baseline structured-only*, không đưa vào phân tích bất nhất.
  Mọi con số trong báo cáo phải kèm ngày snapshot.

- **Bài học:** Con số API và con số trên đĩa là hai thứ khác nhau. **Đếm trên đĩa trước
  khi viết bất kỳ câu nào về dữ liệu.**

---

### [2026-10-29] [Schema] `foidevproblem_thru2025.txt` KHÔNG có header

- **Vấn đề:** File `foidevproblem_thru2025.txt` có 29.198.732 dòng, 2 cột, nhưng
  **dòng đầu tiên là dữ liệu**, không phải header.

- **Nguyên nhân:** FDA không nhất quán giữa các file. `patientproblemcode_thru2025.txt`
  (cùng khái niệm "mã vấn đề") **có** header 5 cột. `foidevproblem` thì không.

- **Bằng chứng:**
  ```
  foidevproblem_thru2025.txt        : 2 cột, KHÔNG header, 29.198.732 dòng
  patientproblemcode_thru2025.txt   : 5 cột, CÓ header,  29.077.432 dòng
  ```

- **Hậu quả nếu bỏ qua:** `pd.read_csv(header=0)` sẽ **mất bản ghi đầu tiên** và đặt tên
  cột là `1234567|1546` — sai hoàn toàn, và không có exception nào.

- **Giải pháp:** `src/data/schema.py:has_header()` trả `False` cho `foidevproblem*`;
  `src/data/io.py:read_device_problem()` đọc từ dòng 1, không bỏ dòng nào.

- **Bài học:** Hai file "cùng ý nghĩa" không có nghĩa là "cùng hình dạng".

---

### [2026-10-29] [Schema] `MANUFACTURER_NAME` trong master rỗng 100%

- **Vấn đề:** Plan v1 định chia train/test theo manufacturer bằng cột `MANUFACTURER_NAME`
  trong `mdrfoiThru2025.txt`. Cột này **rỗng cho toàn bộ 23,6M dòng**.

- **Nguyên nhân:** Trong schema MAUDE, `MANUFACTURER_NAME` là thông tin liên hệ của hãng
  (địa chỉ, người đại diện) — FDA bỏ trống ở bản public. Tên hãng thật nằm ở bảng DEVICE.

- **Bằng chứng:**
  ```
  MANUFACTURER_NAME      (master)    : fill  0,00%   ❌
  MANUFACTURER_G1_NAME   (master)    : fill 34,15%   ⚠️
  MANUFACTURER_D_NAME    (DEVICE20XX) : fill 99,84–99,97%  ✅
  ```

- **Giải pháp:** Dùng `DEVICE20XX.txt:MANUFACTURER_D_NAME`. Nếu cần cột trong master thì
  `MANUFACTURER_G1_NAME` (34,15%) nhưng phải khai báo là thiếu 2/3.

- **Bài học:** Cột tồn tại ≠ cột có dữ liệu. **Đếm fill rate trước khi dùng cột nào để chia nhóm.**

---

### [2026-10-29] [Leakage] `REPORT_NUMBER` ≠ `MDR_REPORT_KEY`

- **Vấn đề:** Plan v1 chia train/test theo `MDR_REPORT_KEY`. Nhưng một *báo cáo* có thể
  sinh nhiều *bản ghi* — cùng `REPORT_NUMBER`, khác `MDR_REPORT_KEY`.

- **Nguyên nhân:** MAUDE lưu mỗi thiết bị / mỗi lần cập nhật thành một bản ghi riêng.
  `MDR_REPORT_KEY` là duy nhất theo bản ghi; `REPORT_NUMBER` là duy nhất theo báo cáo.

- **Bằng chứng:**
  ```
  dòng hợp lệ                    : 23.633.176
  REPORT_NUMBER phân biệt        : 23.126.307
  54.263 family >1 bản ghi        :    561.132  (2,37%)
  family lớn nhất                :         11
  family 10–11 bản ghi           :     53.404
  ```

- **Hậu quả nếu bỏ qua:** 2,37% dòng có bản ghi "anh em" ở phía bên kia split → model học
  thuộc báo cáo đó thay vì học bệnh lý. Metric tăng giả tạo.

- **Giải pháp:** Chia theo `REPORT_NUMBER`. `schema.GROUP_KEY = "REPORT_NUMBER"`.

- **Bài học:** Trước khi chia split, hỏi: "đơn vị phân tích là gì?" — không phải "khoá
  chính là gì?".

---

## 2. Ba ca mã không có trong từ điển

### [2026-10-29] [Codes] 294 mã device và 68 mã patient không có trong từ điển

- **Vấn đề:** Dữ liệu lịch sử dùng mã không còn trong từ điển hiện hành.

- **Bằng chứng:**
  ```
  device : 1.177 mã dùng thực tế, 884 trong từ điển  → 294 mã lạ,  32.228 dòng
  patient: 1.199 mã dùng thực tế, 1.172 trong từ điển →  68 mã lạ,     724 dòng
  từ điển có nhưng chưa bao giờ dùng: 1 device, 41 patient
  ```

- **Hậu quả nếu dùng INNER JOIN:** mất 32.228 + 724 = 32.952 dòng.

- **Giải pháp:** **LEFT JOIN**, giữ mã lạ, đánh cờ `in_dictionary = false`, và báo cáo
  con số. Trong báo cáo: mã lạ là bằng chứng từ điển FDA không đóng theo thời gian.

- **Bài học:** Từ điển là snapshot hiện tại, dữ liệu là lịch sử. Hai thứ không khớp nhau
  là bình thường — nhưng phải đếm.

### [2026-10-29] [Codes] Placeholder `"1" = "Old To Be Deactivated"` trong cả 2 từ điển

- **Vấn đề:** Đếm `distinct FDA_CODE` ra 885 (device) và 1.172 (patient), nhưng cả hai
  đều có dòng `1,Old To Be Deactivated,...` — đây là placeholder, không phải mã thật.

- **Giải pháp:** `read_codebook()` tự `pop("1")` → 884 và 1.171.

- **Bài học:** Đếm `distinct` trên file tham chiếu phải kiểm tra giá trị đặc biệt.

---

## 3. Hai ca "số liệu API vs số liệu đĩa"

### [2026-10-29] [Count] openFDA báo 26.557.775 — đĩa có 23.633.176

- **Vấn đề:** Hai con số chênh 2.924.599.
- **Nguyên nhân:** API tính cả bản ghi 2026 và bản ghi chưa vào `thru2025`.
- **Giải pháp:** `manifest.json` là nguồn duy nhất. API chỉ dùng để nói "đây là snapshot".

### [2026-10-29] [Count] "97,4% có narrative" là số của API, không phải của đĩa

- **Vấn đề:** Chênh 45,69% vs 97,4%.
- **Nguyên nhân:** Xem §1 ca đầu.
- **Giải pháp:** Đã sửa toàn bộ plan v2. Bất kỳ chỗ nào còn "97,4%" là lỗi.

---

## 4. Một ca chất lượng narrative

### [2026-10-29] [Text] Một ô FOI_TEXT dài 9.998.819 ký tự (~10 MB)

- **Vấn đề:** `foitext2025.txt` có một dòng với `FOI_TEXT` dài 9.998.819 ký tự.
- **Bằng chứng:**
  ```
  2022: max 32.419   |  >20k: 110
  2023: max 32.022   |  >20k:  83
  2024: max 923.350  |  >20k: 107
  2025: max 9.998.819|  >20k: 160
  ```
- **Nguyên nhân:** Bản ghi lỗi hệ thống — nội dung lặp lại hàng nghìn lần, không phải
  narrative dài thật.
- **Giải pháp:** Cắt ở 20.000 ký tự. Ảnh hưởng 460/24.740.279 dòng = 0,0019%.
- **Bài học:** Một ô 10 MB đủ làm nổ batch 200.000 dòng trong `pyarrow`. Luôn kiểm tra
  max length trước khi parse.

---

## 5. Ca trùng lặp giữa các năm foitext

### [2026-10-29] [Overlap] Tổng report foitext (10.799.941) khác cohort (10.800.548)

- **Vấn đề:** Union 4 năm foitext ra 10.799.941 report, nhưng cohort 10.800.548.
  Chênh **607** report (0,0056%) — cohort nhiều hơn union, tức có báo cáo trong
  cohort mà không có narrative, và ngược lại.
- **Nguyên nhân:** `foitext20XX` cắt theo năm **nhận báo cáo**, master lọc theo
  `DATE_RECEIVED`. Hai trường có thể khác nhau (báo cáo nhận 2022, `DATE_RECEIVED` 2021).
- **Giải pháp:** Join bằng `MDR_REPORT_KEY`, lấy giao. Không dùng union làm mẫu số.
- **Bài học:** Hai trường ngày trong MAUDE (`DATE_RECEIVED` vs `DATE_REPORT`) không đồng
  nhất. Luôn nói rõ dùng trường nào.

---

## 6. Ca lỗi lớn nhất: MAUDE **không** phải một bản ghi trên một dòng

### [2026-10-30] [Parse] Parser cũ vừa báo sai "malformed" vừa **âm thầm làm mất 3.503 bản ghi**

- **Vấn đề:** `verify_datasets.py` FAIL ở 4 file `DEVICE*` vì số dòng đọc được
  không khớp. Chẩn đoán ban đầu (2026-10-29) kết luận "bảng EXPECT sai, chỉ cần
  sửa số" — **kết luận đó sai**. Nếu làm theo, sẽ nuốt mất dữ liệu thật.

- **Nguyên nhân:** Một số bản ghi chứa **CR/LF nhúng bên trong** trường văn bản tự do
  (`BRAND_NAME`, `GENERIC_NAME`, `MANUFACTURER_D_ADDRESS_*`), nên một bản ghi logic trải
  trên 2–3 dòng vật lý. Code cũ `for line in f: parts = line.split("|")` coi mỗi dòng
  vật lý là một bản ghi, nên:
  1. mỗi **nửa** bản ghi có số cột sai → bị đếm là "malformed", và
  2. với `strict=False` (mà `verify`/`s2` đều dùng), bản ghi đó bị **bỏ qua im lặng**.

- **Bằng chứng đo được** (`scratch/diag_multiline.py`, `scratch/check_cohort_delta.py`):

  | File | Bản ghi bị mất | Dòng bị báo sai "malformed" | Số dòng thật sau khi ghép |
  |---|---:|---:|---:|
  | `mdrfoiThru2025.txt` | **3.337** | 6.681 | 23.633.176 |
  | `DEVICE2022.txt` | 23 | 46 | 2.954.980 |
  | `DEVICE2023.txt` | 89 | 193 | 2.345.004 |
  | `DEVICE2024.txt` | 38 | 76 | 2.629.372 |
  | `DEVICE2025.txt` | 16 | 32 | 2.887.987 |
  | **Cộng** | **3.503** | **7.028** | |

  Số bản ghi **hỏng thật** của master là **3**, không phải 6.681.

- **Hậu quả nếu không phát hiện:** con số "0,03% malformed" trong báo cáo che
  **hai** lỗi cùng lúc — sai số tỷ lệ ~**2.200 lần** (3/23,6M = 0,0000127%), và việc
  mất 3.503 bản ghi. Con số "malformed" đọc như "chất lượng dữ liệu tốt" trong khi
  thực tế nó là **triệu chứng của mất dữ liệu**.

- **Giải pháp:** `src/data/io.py:_logical_records()` gom dòng vật lý cho tới khi số cột
  pipe khớp schema, rồi mới yield **một** bản ghi. `read_maude()`, `count_rows()` và
  `s2_parse._count_bad()` đều dùng nó.
  Bản ghi có số cột **vượt** schema được yield nguyên bản để caller đếm là
  hỏng — dùng `==` chứ không phải `>=` khi kiểm số cột, nếu không sẽ coi bản ghi
  hỏng là hợp lệ.

- **Bài học:** Khi một file "sạch" đột nhiên báo hàng nghìn dòng lỗi, **nghi ngờ parser
  trước, nghi ngờ dữ liệu sau**. Và: một bộ đếm "malformed" lớn bất thường có
  thể là dấu hiệu **mất dữ liệu**, không phải dấu hiệu dữ liệu bẩn. Luôn kiểm
  bằng: tổng số bản ghi đọc được + số bị bỏ có bằng số dòng vật lý không.

---

## 7. Bảng số đo lại sau khi sửa parser (2026-10-30)

Nguồn: `reports/tables/s4_audit.json` + `s4_cohort_coverage.json`.
Mọi con số ở các mục trên đều đã được cập nhật theo bảng này.

| Đại lượng | Trước sửa (sai) | **Sau sửa** |
|---|---:|---:|
| Master hợp lệ | 23.629.839 | **23.633.176** |
| Master malformed | 6.681 | **3** |
| `REPORT_NUMBER` phân biệt | 23.122.971 | **23.126.307** |
| Cohort 2022–2025 | 10.797.223 | **10.800.548** (45,7008%) |
| Năm 2022 / 2023 / 2024 / 2025 | 2.944.940 / 2.338.901 / 2.626.226 / 2.887.156 | **2.945.648 / 2.339.802 / 2.627.111 / 2.887.987** |
| Family >1 | 561.130 dòng | **54.263 family / 561.132 dòng** (max 11) |
| Device orphan codes | 293 (32.227 dòng) | **294 (32.228 dòng)** |
| Cohort không có mã nào | 121 | **122** |
| Cohort coverage device / patient / cả hai | 99,68 / 99,95 / 99,62% | **99,6758 / 99,9461 / 99,6230%** |

Điều **không** thay đổi: `MDR_REPORT_KEY` ≠ `REPORT_NUMBER` (vẫn là lý do chia split
theo `REPORT_NUMBER`), `foidevproblem` vẫn không có header, `MANUFACTURER_NAME` vẫn rỗng
100%, `foitext` vẫn chỉ có 2022–2025. Ca lỗi parser **không làm sai** bất kỳ quyết
định nào về thiết kế nghiên cứu — nó chỉ làm sai **số học**.

## 8. RecSys — định nghĩa "rò rỉ" và "tập đánh giá" sai (đo thật 2026-11-04)

Các mục dưới đây **thay thế** toàn bộ logic rò rỉ cũ của dự án MAUDE. Tất cả đều được
đo bằng pipeline thật (Parquet → HDFS → MapReduce Java → PySpark → MongoDB), seed `42`.

### [2026-11-04] [Leakage] Rò rỉ phải đo **tương đối theo user**, không đo toàn cục

- **Vấn đề:** Định nghĩa rò rỉ đầu tiên (toàn cục) cho kết quả vô nghĩa ở `leave_one_out`:

  | Split | viol toàn cục | viol user-relative |
  |---|---|---|
  | `random80_20` | 100,0000% | 98,9084% |
  | `temporal_global` | 0,0000% | 0,0000% |
  | `leave_one_out` | **99,9988%** | **0,0000%** |

- **Nguyên nhân:** Toàn cục đếm số dòng test mà **item** xuất hiện ở train với timestamp
  *bất kỳ*. Ở `leave_one_out`, mỗi user giữ đúng 1 tương tác mới nhất nên item gần như
  chắc chắn đã xuất hiện ở train (tương tác cũ hơn của user đó) → tỷ lệ ~100% **vô nghĩa**,
  không phản ánh rò rỉ thời gian.

- **Bằng chứng đo được:** `random80_20` user-relative = 98,9084% (rò rỉ thật, vì random
  split lấy tương tác tương lai); `leave_one_out` user-relative = 0,0000% (không rò rỉ thật).

- **Giải pháp:** Định nghĩa chuẩn hoá — với mỗi user, kiểm tra **tương tác test có
  timestamp lớn hơn tất cả timestamp train của chính user đó không**. Đây là định nghĩa
  "user-relative temporal leakage". Toàn cục giữ lại như chỉ số phụ để đối chiếu.

- **Bài học:** Một định nghĩa rò rỉ phải **có đối chiếu cơ sở**. Cùng một dữ liệu, hai
  định nghĩa → kết luận ngược nhau (`99,9988%` vs `0,0000%`).

---

### [2026-11-04] [Scope] Đổi split = đổi **dịch chuyển miền đánh giá**, mất 96,1% mẫu

- **Vấn đề:** `temporal_global` cho NDCG@10 thấp hơn `random80_20` (0,1364 vs 0,2584 cho
  ALS). Nếu kết luận "ALS kém hơn" thì sai — tập đánh giá đã khác.

- **Nguyên nhân:** Không phải mô hình đổi, mà là **tập đánh giá đổi**:

  | Split | eval_rel_users | Ghi chú |
  |---|---|---|
  | `random80_20` | 158.688 | user có ≥1 tương tác liên quan ở test |
  | `temporal_global` | **6.219** | mất **96,1%** mẫu so với random |
  | `leave_one_out` | 96.003 | |

- **Bằng chứng đo được:** Bảng trên là số user **thực sự được đánh giá** (có ít nhất 1
  item liên quan ở test). `temporal_global` chỉ còn 6.219 user.

- **Giải pháp:** Báo cáo **cả ba** giá trị cùng lúc với `eval_rel_users` đi kèm. Cấm
  so sánh NDCG giữa 2 split khác nhau mà không kèm số user đánh giá.

- **Bài học:** Đổi chiến lược chia tập = đổi *bài toán đánh giá*, không chỉ đổi *cách chia*.

---

### [2026-11-04] [Metric] `longtail_coverage = 0` ở cả 6 tổ hợp — giảm thiên lệch ≠ xử lý thiên lệch

- **Vấn đề:** Sau khi thay Popularity bằng ALS, `popularity_bias_ratio` giảm mạnh
  (158,64 → 12,26 với `random80_20`), nhưng `longtail_coverage` vẫn bằng **0** ở cả
  Popularity lẫn ALS, ở cả 3 split.

- **Nguyên nhân:** Định nghĩa long-tail dùng ngưỡng `p20` của **độ phủ item toàn catalog**,
  trong khi mô hình chỉ xuất top-10 item **phổ biến nhất trong tập train**. Item đuôi
  (phổ biến rank > p80) gần như không bao giờ lọt vào top-10 → coverage = 0 về mặt toán học.

- **Bằng chứng đo được:**

  | Split | bias Pop | bias ALS | longtail Pop | longtail ALS |
  |---|---|---|---|---|
  | `random80_20` | 158,64 | 12,26 | 0 | 0 |
  | `temporal_global` | 101,26 | 11,20 | 0 | 0 |
  | `leave_one_out` | 165,27 | 12,41 | 0 | 0 |

- **Giải pháp (đã ghi trong `Metrics.md`):** Tách 2 khái niệm —
  1. **Giảm thiên lệch phổ biến** = `popularity_bias_ratio` giảm → đạt.
  2. **Xử lý thiên lệch phổ biến** = mô hình đưa được item đuôi vào top-K → **chưa đạt**,
     và `longtail_coverage = 0` là bằng chứng.

  Báo cáo phải nói rõ: kết quả hiện tại chứng minh *giảm được* thiên lệch, **không** chứng minh
  *giải quyết được* thiên lệch.

- **Bài học:** Đừng dùng một chỉ số để kết luận cho hai câu hỏi khác nhau.

---

### [2026-11-04] [Metric] `popularity_bias_ratio` cấp catalog không đo được thiên lệch cấp user

- **Vấn đề:** Chỉ số `popularity_bias_ratio` (độ lệch giữa popularity của item được đề xuất
  và popularity trung bình của catalog) là **một số duy nhất cho cả tập** → không có
  phương sai, không làm kiểm định ghép được.

- **Nguyên nhân:** Muốn làm Wilcoxon signed-rank (kiểm định ghép theo user) thì phải có
  **một giá trị cho mỗi user**.

- **Giải pháp:** Bổ sung `PerUserPopSkew` — với mỗi user, tính trung bình popularity của
  10 item được mô hình đề xuất chia cho popularity trung bình của catalog **cùng split**.
  Dùng chỉ số này cho kiểm định thống kê; giữ `popularity_bias_ratio` cho mô tả catalog.

- **Bài học:** Chỉ số cấp tập không dùng được cho kiểm định ghép. Tách rõ
  *chỉ số mô tả* và *chỉ số kiểm định*.

---

### [2026-11-04] [Model] ALS **explicit** cho NDCG ≈ 0 — phải dùng implicit

- **Vấn đề:** ALS explicit (dự đoán rating) đưa NDCG@10 xuống gần **0**.

- **Nguyên nhân:** ALS explicit xếp hạng theo **giá trị rating dự đoán**. User đánh giá
  1,0 bị đẩy xuống cuối danh sách → không bao giờ vào top-10 → NDCG ≈ 0. Đây là lỗi
  **phương pháp** (đánh giá top-N bằng mô hình rating), không phải lỗi code.

- **Giải pháp:** Chuẩn top-N là **implicit feedback**. Chỉ tính tương tác có `rating ≥ 4,0`
  là "liên quan", dùng **ALS implicit** (`implicitPrefs=True`, `alpha=10.0`), và áp dụng
  **cùng một ngưỡng liên quan + cùng cách xếp hạng** cho cả Popularity và ALS.

- **Cấu hình chốt:** rank `16`, `maxIter 8`, `regParam 0,05`, `alpha 10`, seed `42`,
  mẫu `30.000` user.

- **Bài học:** Trước khi sửa code, hỏi "phương pháp đúng chưa". Một con số ≈ 0 gần như
  luôn là lỗi phương pháp trước khi là lỗi kỹ thuật.

---

### [2026-11-04] [Timezone] MapReduce UTC vs Spark local → lệch 7,65% số key

- **Vấn đề:** Gate G3 cross-check MapReduce ↔ Spark lệch **24.778 / 323.775 key = 7,65%**.

- **Nguyên nhân:** MapReduce dùng `SimpleDateFormat` với **UTC**; Spark dùng
  `year(from_unixtime(timestamp))` theo **local time (UTC+7)**. Ranh giới năm dịch 7,65%
  số dòng (khớp đúng tỷ lệ 1 giờ / 24 giờ × số lần chạy quanh năm).

- **Giải pháp:** Spark bắt buộc `.config("spark.sql.session.timeZone", "UTC")`.
  Đã áp dụng và G3 pass: `323.737 / 323.737 = 100%`, tổng `25.000.095`.

- **Bài học:** Mọi engine trong cùng pipeline phải khai báo timezone **tường minh** và
  **giống nhau**. Kiểm chứng bằng con số tương đối, không bằng cảm giác.

---

### [2026-11-04] [Ownership] R ghi đè schema MongoDB do Python tạo

- **Vấn đề:** R script từng `drop()` + `insert()` vào `recsys.audit_metrics` → phá schema
  42 field mà Python tạo.

- **Giải pháp (đã áp dụng):**
  - Python (`scripts/05_store_mongodb.py`) là **nguồn ghi duy nhất** cho `recsys.audit_metrics`.
  - R **chỉ đọc**, và ghi kết quả riêng vào `recsys.audit_metrics_r`.

- **Bài học:** Một collection = một chủ sở duy nhất. Tách ngay khi phát hiện, đừng sửa
  "tạm" rồi quên.

---

### [2026-11-04] [Data] Amazon `All_Beauty` 5-core còn 4.240 dòng / 477 user — quá nhỏ

- **Vấn đề:** Bộ cross-domain dự phòng bị "thu nhỏ" mạnh sau khi lọc 5-core.

- **Bằng chứng đo được:** `All_Beauty` 5-core → **4.240 dòng / 477 user**.

- **Giải pháp:** Giữ làm cross-domain **dự phòng**, không dùng làm tập chính. Tập chính
  là MovieLens `ml-25m`. Phải ghi con số 4.240/477 vào tài liệu để không ai hiểu nhầm
  là toàn bộ dataset Amazon 2023.

- **Bài học:** Khi một tập dữ liệu được lọc, **ghi rõ bộ lọc và số trước/sau**.

---

## 9. RecSys — schema, nhãn và quy ước đo lường

### [2026-11-04] [Schema] Ba chiến lược chia tập — định nghĩa chính xác

| Tên | Định nghĩa (seed 42) | Train rows | Test rows |
|---|---|---|---|
| `random80_20` | `F.rand(42) > 0.8` → test | 20.000.076 | 5.000.019 |
| `temporal_global` | `timestamp ≥ P80(timestamp)` → test | 19.999.206 | 5.000.889 |
| `leave_one_out` | mỗi user giữ 1 tương tác **mới nhất** → test | 24.837.554 | 162.541 |

> Số liệu đo thật từ `scripts/11_peruser_ndcg.py` (log `D:\recsys_data\poc\peruser\peruser_run.log`).

### [2026-11-04] [Label] Ngưỡng liên quan `rating ≥ 4,0` — giống nhau cho MỌI mô hình

- **Vấn đề:** Nếu Popularity và ALS dùng hai ngưỡng khác nhau thì mọi so sánh vô nghĩa.

- **Giải pháp:** Một ngưỡng duy nhất `THRESH = 4.0` cho **cả 2 mô hình × cả 3 split**.
  Ghi rõ trong `Metrics.md` §2.0.

### [2026-11-04] [Metric] Per-user metric — thứ tự cột và nguồn

`scripts/11_peruser_ndcg.py` xuất `D:\recsys_data\poc\peruser\peruser_<split>.csv`:

| Cột | Ý nghĩa |
|---|---|
| `userId` | khóa user (khớp giữa 2 mô hình) |
| `ndcg_pop`, `ndcg_als` | NDCG@10 theo user |
| `hit_pop`, `hit_als` | Hit@10 theo user |
| `skew_pop`, `skew_als` | `PerUserPopSkew` theo user |
| `tail_pop`, `tail_als` | `TailCount@10` theo user (luôn 0 — xem §8 lỗi longtail) |

Số user có cặp đủ 2 mô hình (paired):
`random80_20` = **29.337**, `temporal_global` = **1.363**, `leave_one_out` = **17.704**.

> **Cảnh báo:** script ghi đè `peruser_summary.json` mỗi lần chạy. Nếu chạy 2 split
> trong 1 lệnh, mục `random80_20` trong summary sẽ mất. Đọc file CSV theo từng split,
> đừng dựa vào summary JSON làm nguồn duy nhất.
