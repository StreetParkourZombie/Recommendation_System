# Error Log — Dataset MovieLens-25M & Schema

Nhật ký lỗi và các bẫy dữ liệu (gotchas) trong quá trình xử lý MovieLens-25M trên PySpark và Windows.

Format: `### [YYYY-MM-DD] [Category] Title` -> Vấn đề / Nguyên nhân / Bằng chứng / Giải pháp

---

## 1. Schema & Tính toàn vẹn MovieLens-25M

### [2026-11-03] [Integrity] Giả định có cặp (userId, movieId) trùng lặp

- **Vấn đề:** Kiểm tra xem MovieLens-25M có chứa các đánh giá trùng lặp cùng cặp `(userId, movieId)` hay không trước khi chia tập.
- **Nguyên nhân:** Một số dataset mở (như Amazon Reviews, GoodReads) thường xuyên có duplicate interactions do người dùng cập nhật đánh giá.
- **Bằng chứng đo được (Spark 4.2.0):**
  - Tổng số tương tác: 25.000.095 dòng.
  - Số cặp `(userId, movieId)` duy nhất: 25.000.095.
  - Số duplicate pairs: **0**.
- **Hậu quả code:** Khi tính tổng/max của các duplicate pairs bằng `df.groupBy("userId", "movieId").count().filter("count > 1")`, DataFrame rỗng khiến `.agg(sum("count"))` trả về `None` thay vì `0`.
- **Giải pháp:** Khi tính các chỉ số tổng hợp trên tập rỗng, luôn dùng `coalesce` hoặc ép mặc định `0` trong Python: `val = row[0] if row[0] is not None else 0`.
- **Bài học:** Schema sạch về ID không có nghĩa là aggregate queries không trả về `None` khi filter không khớp dòng nào.

---

## 2. Temporal Ties & Khung thời gian

### [2026-11-03] [Temporal] Xung đột nhãn thời gian (Timestamp Ties) trong Leave-One-Out

- **Vấn đề:** Chiến lược Leave-One-Out (LOO) yêu cầu lấy "tương tác mới nhất" của mỗi người dùng đưa vào tập test. Tuy nhiên, nhiều tương tác có cùng `timestamp` lớn nhất.
- **Nguyên nhân:** Người dùng đánh giá hàng loạt phim trong cùng một phiên đăng nhập (hoặc dữ liệu import đồng loạt) khiến nhiều bản ghi có cùng timestamp tính đến giây.
- **Bằng chứng đo được:**
  - 1.799.454 nhóm timestamp ties cục bộ xuất hiện trên 78.496 người dùng (48,29% tổng số người dùng).
  - Có 2.225.836 mốc timestamp trùng trên toàn cục.
- **Hậu quả:** Nếu chia tập bằng `row_number()` không có tie-breaker ổn định, các lần chạy khác nhau sẽ chọn ra các item test khác nhau, làm sai lệch tính tái lập (reproducibility) của NDCG/HitRate.
- **Giải pháp:** Sử dụng sắp xếp phụ cố định: `Window.partitionBy("userId").orderBy(col("timestamp").desc(), col("movieId").desc())` để đảm bảo phân tách đơn định (deterministic).
- **Cài đặt thực tế:** `src/audit/splits.py` → `build_split("leave_one_out")`. Đã verify ở notebook 04: 3 split ghi đĩa, `overlap=0`, `matches_expected=True` (test LOO = 162.541 dòng = đúng 1 dòng/user).
- **Giới hạn còn lại:** tie-break theo `movieId` là **tất định nhưng không phải thứ tự thời gian thật**. Trong cùng 1 giây không có cách nào biết user xem phim nào trước. Mọi kết luận về "item cuối" phải kèm câu này.

---

## 3. Catalog Shift & Cold-start trong Temporal Split

### [2026-11-03] [Leakage vs Cold-start] Cái giá của việc chia thời gian toàn cục

- **Vấn đề:** Khi chia theo mốc thời gian toàn cục (P80 timestamp), tập test xuất hiện lượng lớn item và user chưa từng có trong tập train.
- **Bằng chứng đo được:**
  - `unseen_item_rows`: 8,7594% số dòng test thuộc về phim chưa từng xuất hiện ở train.
  - `coldstart_user_rows`: 4.235.246 dòng test thuộc về user mới hoàn toàn.
- **Hậu quả:** Mô hình lọc cộng tác cổ điển (ALS / Matrix Factorization) hoàn toàn bất lực trước user/item cold-start này nếu không có fallback hoặc cơ chế hybrid.
- **Giải pháp:** Định nghĩa rõ tập `eval_users` (user có $\ge 5$ tương tác trong train và $\ge 1$ tương tác test có rating $\ge 4.0$) để đo lường công bằng trên cùng tập user hợp lệ giữa 3 phương pháp chia.
