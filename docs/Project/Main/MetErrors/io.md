# Error Log — I/O, Parquet & File System Windows

Nhật ký lỗi I/O và hệ thống tệp trong quá trình xử lý 25 triệu dòng trên Windows.

Format: `### [YYYY-MM-DD] [Category] Title` -> Vấn đề / Nguyên nhân / Giải pháp

---

## 1. Native I/O & Hadoop Winutils trên Windows

### [2026-11-03] [Winutils] Lỗi `HADOOP_HOME and hadoop.home.dir are unset` khi ghi Parquet

- **Vấn đề:** Khi gọi `df.write.parquet("path")` trong PySpark trên Windows, phát sinh lỗi NativeIO:
  ```
  java.lang.RuntimeException: java.io.FileNotFoundException:
    HADOOP_HOME and hadoop.home.dir are unset
  ```
- **Nguyên nhân:** Hadoop/Spark trên Windows phụ thuộc binary `winutils.exe` để mô phỏng phân quyền POSIX filesystem. Khi `HADOOP_HOME` chưa cấu hình, hàm native gọi thất bại.
- **Giải pháp đã verify 2026-11-15:** cần **đủ hai file**, không phải chỉ một:

  | File | Kích thước | Kết quả nếu thiếu |
  |---|---|---|
  | `D:\recsys_data\tools\hadoop\bin\winutils.exe` | 112.640 B | `FileNotFoundException: HADOOP_HOME ... unset` |
  | `D:\recsys_data\tools\hadoop\bin\hadoop.dll` | 85.504 B | `UnsatisfiedLinkError: NativeIO$Windows.access0` |

  Set `HADOOP_HOME=D:\recsys_data\tools\hadoop` và prepend `bin` vào `PATH`. Sau đó test thật:
  ```
  df.write.mode("overwrite").parquet(path)  ->  WRITE_OK rows=2
  ```
  Nguồn binary: `https://raw.githubusercontent.com/cdarlint/winutils/master/hadoop-3.2.1/bin/`.
  Hàm `src/utils/spark_utils.ensure_hadoop_home()` tự set và trả `True/False` để notebook log.

- **Chốt lại:** `df.write.parquet` **dùng được** khi có đủ 2 binary. Vẫn giữ `pyarrow` cho bước **ingest CSV → Parquet gốc** vì nhanh hơn (26s cho 25M dòng) và không cần JVM; dùng **Spark** cho bước **ghi split** vì cần partition + metadata Spark.

---

## 2. Checksum & Xác thực tính bất biến

### [2026-11-03] [Integrity] Xác thực dữ liệu thô và Parquet bằng SHA-256

- **Vấn đề:** Đảm bảo dữ liệu 25 triệu dòng không bị suy biến (data corruption) qua các bước nén/giải nén và chuyển đổi.
- **Giải pháp:**
  - Snapshot SHA-256 chính thức cho `D:\recsys_data\raw\ml-25m\ratings.csv`:
    `9c85525758597dca76e8d98cebb9c13e018c2317b09a0878b6d383179526e385` (678.260.987 bytes).
  - Snapshot SHA-256 của thư mục `D:\recsys_data\parquet\ratings\`:
    `379d0b2e4131fa62ea6c4d7301faf9aafd3ab5842038d3346fded66c2109657c`; file `part-00000.parquet` = 175.961.682 bytes.
  - Lưu trữ cố định mã băm tại file `.sha256` để kiểm định tự động trong các notebook.

---

## 3. Quản lý thư mục tạm Spark trên ổ đĩa

### [2026-11-03] [Disk] Phình to dung lượng thư mục `spark_tmp` khi shuffle

- **Vấn đề:** Các tác vụ shuffle diện rộng (tính ma trận tương quan, top-K full catalog, percentile_approx) ghi nhiều gigabyte dữ liệu tạm vào ổ đĩa.
- **Giải pháp:** Cấu hình thư mục scratch riêng biệt trên ổ có dung lượng lớn (`D:\recsys_data\spark_tmp\`) qua tham số `spark.local.dir`. Thường xuyên dọn dẹp sau khi phiên Spark kết thúc.
