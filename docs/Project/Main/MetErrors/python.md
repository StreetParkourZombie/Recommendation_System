# Error Log — Python, Jupyter Kernel, PySpark & Thư viện

Nhật ký lỗi môi trường Python, xung đột kernel Jupyter và khác biệt API PySpark 4.2.

Format: `### [YYYY-MM-DD] [Category] Title` -> Vấn đề / Nguyên nhân / Giải pháp

---

## 1. Jupyter Kernel & Môi trường thực thi

### [2026-11-15] [Kernel] `AssertionError: PySpark missing in this kernel`

- **Vấn đề:** Khi mở notebook trên Jupyter Server (`http://localhost:8888/`), kernel mặc định báo lỗi:
  ```python
  assert packages["pyspark"] is not None, "PySpark missing in this kernel"
  # AssertionError: PySpark missing in this kernel
  ```
- **Nguyên nhân:**
  1. Jupyter Server ưu tiên tìm cấu hình kernel trong user AppData (`C:\Users\PC\AppData\Roaming\jupyter\kernels` và `Python\share\jupyter\kernels\python3`).
  2. File `kernel.json` mặc định của `python3` trỏ tới lệnh `python` không tường minh, vốn tự động phân giải về môi trường `.venv` của dự án khác (Deep Learning) thay vì môi trường chứa PySpark 4.2.0.
  3. Notebook được lưu dưới dạng file `.executed.ipynb` mang trạng thái lỗi cũ từ kernel trước đó.
- **Giải pháp:**
  - Khởi tạo virtual environment cô lập cho dự án tại `D:\Master Exers\Big Data\Recomendation_System\.venv` với cờ `--system-site-packages` (kế thừa PySpark 4.2.0 và JDK 24 từ host).
  - Đăng ký kernel tường minh: `python -m ipykernel install --prefix "d:\Master Exers\Big Data\Recomendation_System\.venv" --name "recsys-project-venv" --display-name "Python 3.14 (BigData RecSys .venv)"`.
  - Cập nhật file cấu hình `kernel.json` của user trỏ trực tiếp đến `python.exe` chuẩn của Python 3.14 host.
  - Xóa kernel rác `venv-dl` trong AppData.
  - Xóa các file trung gian `.executed.ipynb` và chọn đúng kernel `Python 3.14 (BigData RecSys .venv)` trong Jupyter UI.

---

## 2. Thay đổi API PySpark 4.2 so với 3.x

### [2026-11-03] [PySpark] `percentile_approx` nhận quantile dạng thập phân 0.0 - 1.0

- **Vấn đề:** Trong Spark 3.x, một số hàm chấp nhận phần trăm 0-100, nhưng trong Spark 4.2:
  ```python
  F.expr("percentile_approx(timestamp, 0.8)")  # Đúng
  F.expr("percentile_approx(timestamp, 80)")   # Báo lỗi ngoài phạm vi [0.0, 1.0]
  ```
- **Giải pháp:** Luôn sử dụng tỷ lệ chuẩn hóa `[0.0, 1.0]` cho mọi hàm tính quantile/percentile.

### [2026-11-03] [PySpark] Hàm `F.slice` trả về mảng thay vì số

- **Vấn đề:** Khi cần lấy tổng của top phần tử từ mảng trong PySpark:
  ```python
  # Trong PySpark 4.x:
  F.aggregate(F.slice(arr, 1, n), 0.0, lambda acc, x: acc + x)
  ```
- **Giải pháp:** Kết hợp `F.aggregate` với lambda function để cộng dồn mảng thay vì ép kiểu trực tiếp.

### [2026-11-03] [PySpark] pandas 3.0.3 cảnh báo tương thích

- **Vấn đề:** PySpark 4.2.0 phát cảnh báo khi làm việc cùng pandas phiên bản $\ge 3.0.0$:
  ```
  UserWarning: PySpark does not yet support pandas 3.0+.
  ```
- **Giải pháp:** Dùng PySpark thuần (`pyspark.sql.functions`) cho toàn bộ tác vụ aggregation và filtering trên 25M dòng. Chỉ chuyển sang pandas (`.toPandas()`) ở bước cuối cùng khi dữ liệu đã được tổng hợp thành bảng nhỏ (< 1.000 dòng).

---

## 3. Quản lý Bộ nhớ & Top-K RecSys

### [2026-11-15] [Spark] `Uncaught exception in thread executor-heartbeater` — `PartitionKeyedAccumulator.byPartition()` null

- **Vấn đề:** Khi chạy notebook 08 (fit ALS 3 split liên tiếp), log phát ra:
  ```
  ERROR Utils: Uncaught exception in thread executor-heartbeater
  java.lang.NullPointerException: Cannot invoke "java.util.concurrent.ConcurrentHashMap.isEmpty()"
    because the return value of "org.apache.spark.sql.util.PartitionKeyedAccumulator.byPartition()" is null
    at org.apache.spark.sql.util.PartitionKeyedAccumulator.isZero(...)
    at org.apache.spark.executor.Executor.$anonfun$reportHeartBeat$2(...)
  ```
- **Nguyên nhân:** bug ở tầng Spark 4.2.0 internal — accumulator được tạo trên driver nhưng chưa init trên executor khi heartbeat chạy. Liên quan việc mở/đóng nhiều SparkSession hay dùng `getActiveSession()` tái sử dụng session giữa các notebook trong cùng kernel.
- **Hậu quả thực tế: NONE.** Notebook vẫn `COMPLETED`, cả 5 checkpoint PASS, artifact đủ và NDCG khớp baseline từng con số. Đây là log ồn, không phải lỗi dữ liệu.
- **Cách xử lý:** Không cần sửa. Ghi lại vì (a) sẽ gặp lại, (b) nếu đọc log thấy dòng này thì **không** kết luận notebook hỏng — kiểm tra `manifest.json` `status` và `checkpoints` trước.
- **Giảm nhiễu (tùy chọn):** restart kernel giữa các notebook, hoặc chạy từng notebook bằng tiến trình riêng (`scripts/run_notebook.py 08` thay vì chạy nối trong một kernel).

---

### [2026-11-03] [OOM] Hàm `recommendForAllUsers` gây tràn bộ nhớ trên 162.541 users

- **Vấn đề:** Tính toán ma trận đầy đủ $162.541 \times 59.047 \approx 9,6 \times 10^9$ giá trị dự đoán khiến Spark driver/executor bị OOM.
- **Giải pháp:**
  - Trích xuất ma trận hệ số tiềm ẩn (latent factors): `userFactors` ($162.541 \times 16$) và `itemFactors` ($59.047 \times 16$).
  - Sử dụng NumPy chunking: Nhân ma trận theo từng khối 2.000 user (`U[start:end] @ V.T`) và dùng `np.argpartition` để trích xuất Top-10 trong bộ nhớ RAM cực nhanh, tránh tạo DataFrame khổng lồ trong Spark.
