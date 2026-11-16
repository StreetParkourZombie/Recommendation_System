# Hạn Chế & Thách Thức Dự Án (Project Drawbacks & Limitations)

**Dự án:** Phân tích rò rỉ, thiên lệch phổ biến trong hệ thống gợi ý bằng kiểm toán chiến lược chia tập trên Spark.
**Cập nhật:** 2026-11-15 (bổ sung hạn chế đo được từ run `04`–`09`)

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

### 1.3. ALS Chỉ Fit Trên 30.000 / 162.541 User

- `recommendForAllUsers` OOM (162.541 × 59.047 ≈ 9,6 tỷ cặp) → ALS chỉ fit trên **30.000 user đầu theo `userId`**.
- **Hạn chế:** con số NDCG của ALS **không** đại diện cho toàn bộ 162.541 user. 30.000 user đầu theo `userId` không phải mẫu ngẫu nhiên (userId được cấp theo thứ tự tham gia MovieLens → nghiêng về user đăng ký sớm).
- **Hạn chế kéo theo:** `n_paired` của ALS nhỏ hơn `eval_relevant_users` của Popularity (29.229 vs 158.692 ở `random80_20`). Không được trình bày hai số này như cùng một tập.
- **Không được** ngoại suy "ALS sẽ cho kết quả tương tự trên toàn bộ dữ liệu".

### 1.4. Chỉ Một Seed (42)

- Toàn bộ kết quả đo trên **một seed duy nhất**.
- **Hạn chế:** không có bằng chứng về độ ổn định qua seed. Ma trận 3 seed × 3 split × 2 model **chưa chạy**.
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
- **Hạn chế:** NDCG của `temporal_global` (0,1311) và `random80_20` (0,2556) được tính trên hai quần thể khác nhau → **không** so sánh trực tiếp được bằng test ghép cặp.
- Kiểm định Wilcoxon chỉ hợp lệ **trong** một split (so ALS với Popularity trên cùng user). So sánh **giữa** split chỉ được dùng để mô tả **độ lớn hiệu ứng co lại**, kèm chỉ số cấp dữ liệu giải thích nguyên nhân.

### 3.4. `temporal_global` Đổi Rò Rỉ Lấy Dịch Chuyển Miền

- Loại được rò rỉ (0,0000%) nhưng **mất 96,1% mẫu đánh giá** (158.692 → 6.219 user) và có **8,7595%** dòng test trỏ tới item chưa từng thấy trong train.
- **Hệ quả:** NDCG thấp ở split này một phần là do tập test khó hơn, không hoàn toàn do mô hình yếu.

### 3.5. Hai Baseline, Không Phải So Sánh State-of-the-Art

- Chỉ MostPopular + ALS implicit. Không có ItemKNN, BPR, NeuMF, SASRec, LightGCN.
- **Hạn chế:** kết luận "ALS > MostPopular" chỉ nói ALS hơn **đường cơ sở tầm thường**, không nói ALS tốt so với tiêu chuẩn ngành.

---

## 4. Hạn Chế Truy Vết Số Liệu

### 4.1. Hai Đường Tính Cho Hai Bộ Số Hơi Khác Nhau

- Đường A (script, 2026-11-04): ALS NDCG 0,2584 / 0,1364 / 0,0474.
- Đường B (notebook, 2026-11-15): ALS NDCG 0,2556 / 0,1311 / 0,0467.
- Chênh lệch ≤ 0,0053 do khác đường chọn tập user + khác đường top-K.
- **Ràng buộc:** không trộn số A và B trong cùng một bảng. Xem `Metrics.md` §4.5. Kết luận định tính giống nhau ở cả hai đường.

### 4.2. `percentile_approx` / `approxQuantile` Là Xấp Xỉ

- Spark trả giá trị **xấp xỉ** (relative error mặc định 0,01), không phải phân vị chính xác.
- **Hệ quả:** ranh giới split của `temporal_global` dịch chuyển nhẹ nếu đổi `relativeError`. Không được assert bằng `==` trên mốc này.

---

## 5. Tóm Tắt Những Điều KHÔNG Được Nói

| Không được nói | Vì sao |
|---|---|
| "Chạy trên cụm phân tán" | `local[4]`, một máy |
| "Kết quả ổn định qua seed" | chỉ seed 42 |
| "ALS đại diện toàn bộ 162.541 user" | fit trên 30.000 user đầu |
| "ALS đã xử lý thiên lệch phổ biến" | `longtail_coverage = 0` cả 6 tổ hợp |
| "leave_one_out rò rỉ 99,9988%" (không kèm giải thích) | artifact của định nghĩa toàn cục |
| "NDCG của temporal thấp hơn random vì mô hình kém" | tập đánh giá khác nhau về bản chất |
| "Đã tái lập Paper 01" | đây là `method_informed_implementation` |
