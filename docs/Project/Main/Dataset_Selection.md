# Lựa Chọn & Đặc Tả Dữ Liệu — MovieLens-25M

**Dự án:** Phân tích rò rỉ, thiên lệch phổ biến trong hệ thống gợi ý bằng kiểm toán chiến lược chia tập trên Spark.  
**Cập nhật:** 2026-11-15  
**Trạng thái kiểm chứng:** Đã kiểm toán L1/L2/L3 từ GroupLens gốc (không tải lại, không phân phối lại).

---

## 1. Nguồn Gốc & Giấy Phép (Provenance & License)

- **Đơn vị phát hành:** GroupLens Research, University of Minnesota.
- **Trang dữ liệu chính thức:** `https://grouplens.org/datasets/movielens/25m/`
- **File nén chính thức:** `https://files.grouplens.org/datasets/movielens/ml-25m.zip`
- **Trích dẫn bắt buộc (DOI):**
  > F. Maxwell Harper and Joseph A. Konstan. 2015. The MovieLens Datasets: History and Context. *ACM Transactions on Interactive Intelligent Systems (TiiS)* 5, 4: 19:1–19:19. https://doi.org/10.1145/2827872
- **Điều khoản sử dụng:** Chỉ phục vụ nghiên cứu học thuật, **cấm tái phân phối (redistribution strictly prohibited)**. Toàn bộ file dữ liệu gốc và file trung gian lớn được lưu ngoài repository tại `D:\recsys_data\raw\ml-25m`.

---

## 2. Kiểm Toán Toàn Vẹn File (File Integrity Audit - L1)

Kết quả kiểm toán SHA-256 và kích thước từ Notebook 01 (`runs/20261114_152054_01_verify_dataset_111fd4ad`):

| File | Kích thước (bytes) | Ghi chú & Hash |
|---|---:|---|
| `ratings.csv` | 678,260,987 | SHA-256: `9c85525758597dca76e8d98cebb9c13e018c2317b09a0878b6d383179526e385` |
| `movies.csv` | 3,038,099 | Danh mục phim danh nghĩa (62,423 phim) |
| `genome-scores.csv` | 435,164,157 | Điểm tương đồng tag genome |
| `genome-tags.csv` | 18,103 | Tag IDs |
| `links.csv` | 1,368,578 | Ánh xạ sang IMDb, TMDb |
| `tags.csv` | 38,810,332 | Tags người dùng gán |
| `README.txt` | 10,460 | SHA-256: `3c3b3195c5bcff4950d0f4d7a127cf1b5a4e0dd5598e2641f58a743a79fdace1` |

---

## 3. Đặc Tính Phân Phối Dữ Liệu Thực Nghiệm (L2 & L3 Profile)

Các chỉ số được tính toán trực tiếp qua PySpark DataFrame trên 25,000,095 dòng `ratings.csv` (`runs/20261114_162433_03_understand_interactions_a85f2c2b`):

### 3.1. Thống kê cơ bản
- **Tổng số tương tác:** 25,000,095 dòng (0 giá trị null ở cả 4 cột `userId`, `movieId`, `rating`, `timestamp`).
- **Số lượng Users:** 162,541 users độc lập.
- **Số lượng Items có tương tác:** 59,047 phim (lưu ý: khác với tổng 62,423 phim trong `movies.csv`; 3,376 phim không có rating nào).
- **Thang điểm Rating:** từ 0.5 đến 5.0 (bước nhảy 0.5; tổng 10 mức điểm).
- **Khoảng thời gian (Unix timestamp):** `789652009` (09/01/1995) đến `1574327703` (21/11/2019).

### 3.2. Cặp (User, Movie) trùng lặp
- **Số cặp trùng:** 0 cặp lặp lại. Toàn bộ 25,000,095 dòng là các cặp `(userId, movieId)` duy nhất.

### 3.3. Phân phối điểm rating & Ngưỡng quan tâm (Relevance Threshold)
- `rating >= 3.5`: 15,630,129 dòng (~62.52% toàn bộ dữ liệu).
- `rating >= 4.0`: 12,452,811 dòng (~49.81% toàn bộ dữ liệu).
- *Lưu ý:* Cả hai ngưỡng này là khảo sát độ nhạy dữ liệu, việc lựa chọn ngưỡng nào làm nhãn tích cực (implicit positive) cần được khai báo tường minh trong giao thức thực nghiệm.

### 3.4. Hiện tượng trùng Timestamp (Timestamp Ties)
- **Trùng timestamp theo từng user:** 1,799,454 nhóm `(userId, timestamp)` có nhiều hơn 1 tương tác (ảnh hưởng 78,496 users, tổng cộng 6,121,555 tương tác). Nhóm lớn nhất có tới 255 tương tác trong cùng 1 giây.
- **Trùng timestamp toàn cục:** 2,225,836 mốc thời gian có từ 2 tương tác trở lên (chứa 7,110,664 tương tác).
- *Ý nghĩa:* Dấu mốc thời gian không thể đơn độc xác định thứ tự trước/sau cho các tương tác cùng giây. Giao thức chia tập theo chuỗi (sequential leave-one-out) bắt buộc phải có quy tắc xử lý hòa (tie-breaking policy) rõ ràng.

---

## 4. Dữ Liệu Dẫn Xuất (Derived Data) — bổ sung 2026-11-15

Ba split đã materialize từ dataset gốc. Không phải dataset mới, không commit vào git.

| Đường dẫn | Nội dung | Kích thước |
|---|---|---:|
| `D:\recsys_data\parquet\ratings\part-00000.parquet` | cache Parquet của `ratings.csv` | 175.961.682 B |
| `D:\recsys_data\splits\random80_20\{train,test}\` | 19.997.974 / 5.002.121 dòng | — |
| `D:\recsys_data\splits\temporal_global\{train,test}\` | 19.999.279 / 5.000.816 dòng | — |
| `D:\recsys_data\splits\leave_one_out\{train,test}\` | 24.837.554 / 162.541 dòng | — |
| **Tổng thư mục `splits\`** | 3 chiến lược × (8 partition train + 4 partition test) | **735.030.695 B** |

Tái lập bằng notebook `04_build_splits` (`src/audit/splits.py` → `materialize_split`). Mọi split đã verify `matches_expected=True` và `overlap=0` (không dòng nào nằm ở cả train lẫn test trong cùng split).

> **Lưu ý về `leave_one_out`:** tie-break theo `movieId` là tất định nhưng **không phải thứ tự thời gian thật** — 1.799.454 nhóm `(userId, timestamp)` có nhiều hơn 1 tương tác (§3.4). Xem `Drawbacks.md` §2.1.
