# Environment — Môi trường đã verify

**Project:** `D:\Master Exers\Big Data\Recomendation_System`
**Verify:** 2026-11-04 00:20 GMT+7

---

## 1. Phần cứng / OS

| Hạng mục | Giá trị |
|---|---|
| OS | Windows_NT 10.0.26200 (x64) |
| RAM | 31.7 GB tổng (10.8 GB free tại lúc đo) |
| CPU | local[8] cho Spark |
| Disk C | 265.4 GB used / **12.8 GB free** |
| Disk D | 161.1 GB used / **15.5 GB free** |
| Shell | PowerShell |

> **Cảnh báo disk:** C đã từng xuống 4.2 GB vì cache HuggingFace 8.7 GB. Đã chuyển sang `D:\hf_cache\huggingface` + junction `C:\Users\PC\.cache\huggingface` → `D:\hf_cache\huggingface`.
> **Spark temp dir BẮT BUỘC nằm ở D** (`D:\recsys_data\spark_tmp`, đã dùng 1.5 GB).

---

## 2. Ngôn ngữ & thư viện

| Thành phần | Phiên bản / vị trí | Ghi chú |
|---|---|---|
| Python | 3.14 (`C:\Users\PC\AppData\Local\Python\pythoncore-3.14-64`) | |
| PySpark | **4.2.0** | ⚠️ API khác Spark 3.x — xem §5 |
| pyarrow | **26.0.0** | dùng để ghi Parquet (tránh winutils) |
| pandas | 3.0.3 | PySpark cảnh báo chưa hỗ trợ đầy đủ pandas ≥3 |
| numpy | có | dùng cho top-K chunk |
| pymongo | có | |
| streamlit | có | |
| plotly / scikit-learn | có | |
| Java | `jdk-24` tại `C:\Program Files\Java\jdk-24` (host) · **OpenJDK 1.8.0_232** trong container Hadoop | |
| **R** | ✅ **đã cài 04/11** — R 4.6.2 tại `C:\Program Files\R\R-4.6.2\bin\Rscript.exe` | user library `D:\R-library` (không ghi được vào `C:\Program Files`) |
| R packages | ✅ `jsonlite`, `dplyr`, `ggplot2`, `mongolite`, `corrplot` | `SparkR` / `sparklyr` chưa cài — chưa cần vì R đọc JSON + MongoDB |

---

## 3. Docker & Hadoop

| Thành phần | Trạng thái |
|---|---|
| Docker engine | ✅ 28.3.3, linux, mem ~15.5 GB |
| Hadoop cluster | ✅ **5 container đang chạy** — image `bde2020/hadoop-*:2.0.0-hadoop3.2.1-java8` |
| | `namenode`, `datanode`, `resourcemanager`, `nodemanager`, `historyserver` |
| Local `spark-submit` | ❌ không có → chạy qua `pyspark` local mode hoặc container |
| Local `hadoop`/`Rscript` | ❌ không có |

**Dùng lại được, không cần cài lại.** Cluster đã verify healthy 2026-11-03.

---

## 4. MongoDB

| Hạng mục | Trạng thái |
|---|---|
| Server | ✅ **8.0.12** đang chạy, truy cập `mongodb://localhost:27017` |
| Service Windows `MongoDB` | ⚠️ báo `Stopped` và `Start-Service` / `sc start` → **Access is denied** (không có quyền admin). **Không cần** — tiến trình `mongod` đã tự chạy và port 27017 listen bình thường. Kết nối bằng `mongodb://localhost:27017` vẫn OK |
| Database | `recsys` — collections: `audit_metrics` (6 docs), `item_profile` (62.423 docs) |
| Data dir | `D:\Master Exers\Big Data\Recomendation_System\data\mongodb\db` |

> Đây là lý do dùng `MongoClient` trực tiếp thay vì `mongod` service quản lý — hoạt động bình thường.

---

## 5. Khác biệt API PySpark 4.2 so với 3.x (đã vấp — ghi lại để không vấp lần nữa)

| Vấn đề | Biểu hiện | Cách sửa đã áp dụng |
|---|---|---|
| `percentile_approx` | Spark 4.x nhận quantile **0.0–1.0** (3.x là 0–100) | `F.expr("percentile_approx(timestamp, 0.8)")` |
| `F.slice` | Trả **array**, không phải số | `F.aggregate(slice(arr, 1, n), 0D, (acc,x) -> acc+x)` |
| Ghi Parquet | `HADOOP_HOME and hadoop.home.dir are unset` (thiếu `winutils.exe`) | Ghi bằng **pyarrow**, không dùng `df.write.parquet` |
| Đọc Parquet (thư mục) | `UnsatisfiedLinkError: NativeIO$Windows.access0` | Đọc **file đơn** `…/part-00000.parquet` |
| Đọc Parquet (file) | ✅ OK 25.000.095 rows | dùng cách này |
| Đọc CSV | ✅ OK 25.000.095 rows | dùng khi cần |
| `recommendForAllUsers` | OOM (162.541 × 59.047) | numpy top-K chunk 2.000 user |
| **Timezone khi đối chiếu** | MapReduce dùng `SimpleDateFormat` + **UTC**, Spark `year(from_unixtime())` dùng **local (UTC+7)** → lệch 24.778/323.775 key (7,65%) | Set `.config("spark.sql.session.timeZone", "UTC")` cho Spark |
| MapReduce output value | `setOutputValueClass` phải khớp với **reducer input** | Cả map value + combiner + reducer đều dùng `IntWritable`; `setMapOutputValueClass(IntWritable.class)` |

---

## 6. Dữ liệu

| Đường dẫn | Nội dung | Kích thước |
|---|---|---|
| `D:\recsys_data\raw\ml-25m\` | dataset gốc MovieLens | 1.664 MB… |
| `D:\recsys_data\raw\ml-25m\ratings.csv` | 25.000.095 dòng | 678.260.987 B |
| `D:\recsys_data\raw\ml-25m.zip` | file tải gốc | 261.978.986 B |
| `D:\recsys_data\parquet\ratings\part-00000.parquet` | cache Parquet | 176.0 MB, 31 row-groups |
| `D:\recsys_data\spark_tmp\` | Spark temp | ~1.5 GB (dọn khi > 2 GB) |
| `D:\recsys_data\poc\` | kết quả PoC (`poc3_results.json`) | |

**Checksum Parquet:** SHA-256 `379d0b2e4131fa62ea6c4d7301faf9aafd3ab5842038d3346fded66c2109657c`
(ghi tại `D:\recsys_data\parquet\ratings.parquet.sha256`)

---

## 7. Script hiện có (workspace)

| Script | Vai trò | Trạng thái |
|---|---|---|
| `_dl_ml.py` | tải ml-25m | ✅ đã chạy |
| `_ml_to_parquet.py` | CSV → Parquet (pyarrow streaming) | ✅ đã chạy (26s) |
| `_poc3_spark.py` | PoC audit framework 3 tầng × 3 split | 🔄 đang chạy |
| `_t_parquet_read.py` | test các cách đọc Parquet | ✅ đã chạy |
| `_deploy_plan.ps1` | deploy 7 file plan → `D:\...\Plans` | ✅ đã chạy |

---

## 8. Việc cần làm cho môi trường

| # | Việc | Lệnh | Ưu tiên |
|---|---|---|---|
| 1 | Bật MongoDB | `Start-Service MongoDB` | cao |
| 2 | Cài R + SparkR | winget / installer | trung bình (seminar) |
| 3 | Đặt `HADOOP_HOME` trỏ container Hadoop | biến môi trường | thấp (local mode chạy được) |
| 4 | Dọn `spark_tmp` khi > 2 GB | xoá thư mục con cũ | thấp |

---

## 9. Cảnh báo môi trường shell

- PowerShell: không `ls -la`, không `||`. Dùng `;` hoặc `if ($?)`.
- **PowerShell inline làm mất `$`** → viết `.ps1` rồi `powershell -ExecutionPolicy Bypass -File`.
- Console cp1252 → luôn bọc `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")`.
- Redirect ra file tạo **UTF-16** → script tự ghi UTF-8.
- `read`/`write` tool sandbox giới hạn `~/.openclaw/workspace` → file ở `D:\` phải ghi qua `exec`.
- `exec` bị **SIGKILL** khi đọc/tải file lớn vào RAM → dùng HTTP Range hoặc stream chunk.
- Path >260 ký tự → `robocopy` + `cmd /c rd /s /q "\\?\D:\…"`.
- `web_search` disabled → dùng OpenAlex, Crossref, API gốc.
- `memory_search` hỏng (403 `key_not_registered`) → đọc file memory trực tiếp.
- `openclaw status` bị treo → `openclaw gateway status`.

## 10. Cập nhật 2026-11-04 03:30 GMT+7 (sau khi tầng kiểm định thống kê)

### 10.1 Thư viện bổ sung

| Thành phần | Phiên bản | Ghi chú |
|---|---|---|
| **scipy** | **1.18.0** | `scipy.stats.kendalltau` — dùng cho Kendall tau-b thay vì tự viết |
| websocket-client | có | dùng cho CDP (`scripts/15_screenshot_dashboard.py`) |
| requests | có | dùng cho DevTools `/json/version` |
| Pillow | có | kiểm tra ảnh screenshot (kích thước, số màu) |

### 10.2 Trạng thái tiến trình (đo lúc 03:30)

| Tiến trình | Trạng thái |
|---|---|
| Docker containers Hadoop (5) | ✅ đang chạy |
| `mongod` (port 27017) | ✅ đang chạy (PID 22660) — **không** phải Windows service |
| Streamlit (port 8501) | ✅ đang chạy, `/_stcore/health → ok` |
| `_pdf_sink.py` (port 8765) | ⛔ **đã dừng** (đã lưu xong paper 08) |

> **MongoDB:** `Get-Service MongoDB` vẫn báo `Stopped` và `Start-Service` → *Access is denied*,
> nhưng tiến trình `mongod` chạy bình thường và port 27017 listen. **Không cần service.**

### 10.3 `winutils.exe` — KHÔNG có trên máy này

Đã tìm ở `C:\Program Files`, `C:\ProgramData`, `C:\Users\PC` (depth 5) → **không có**.

| Hệ quả | Xử lý |
|---|---|
| `df.write.parquet` (Spark) | ❌ không dùng — ghi bằng **pyarrow** |
| `df.write.csv` / `df.write.json` | ⚠️ cùng đường ghi → tránh |
| Đọc Parquet (file đơn) | ✅ OK |
| Đọc CSV từ HDFS | ✅ OK qua `hadoop fs` |

> Đặt `HADOOP_HOME` trỏ thư mục giả **không** giúp: lỗi đổi từ `HADOOP_HOME unset` sang
> `Hadoop bin directory does not exist: …\bin`. Xem `MetErrors/python.md` §9.

### 10.4 Thư mục dữ liệu sinh ra (2026-11-04)

| Đường dẫn | Nội dung |
|---|---|
| `D:\recsys_data\poc\peruser\peruser_random80_20.csv` | 29.337 user, 1.546.458 B |
| `D:\recsys_data\poc\peruser\peruser_temporal_global.csv` | 1.363 user, 68.846 B |
| `D:\recsys_data\poc\peruser\peruser_leave_one_out.csv` | 17.704 user |
| `D:\recsys_data\poc\peruser\peruser_run.log` | log 3 split, có `SUMMARY` JSON từng split |
| `…\Recomendation_System\reports\stats_<split>.json` | 3 file, ~4,5 KB mỗi file |
| `…\Recomendation_System\reports\stats_summary.csv` | 12 dòng (3 split × 4 metric) |
| `…\report\Big_Data\figures\fig8_prisma_flow.svg` | PRISMA flow, 4.619 B |
| `…\report\Big_Data\figures\fig9_dashboard.png` | dashboard, 152.694 B, 1920×1260 |
| `…\docs\References\Papers\*.pdf` | 9 paper + `_manifest.json` |

### 10.5 Cảnh báo mới (2026-11-04)

| Vấn đề | Xử lý |
|---|---|
| `sys.stdout = io.TextIOWrapper(sys.stdout.buffer)` → **Streamlit app crash** | dùng `sys.stdout.reconfigure(...)` |
| `chrome --screenshot` → ảnh trống (Streamlit render qua websocket) | dùng CDP (`scripts/15_screenshot_dashboard.py`) |
| PowerShell `>` ghi file **UTF-16** | script tự ghi `encoding="utf-8"` |
| `python -c` + chuỗi tiếng Việt + escape kép → `SyntaxError` | luôn viết file `.py` riêng |
| Job > 30 phút bị SIGKILL | chia theo split; vector hoá bootstrap |
| `read`/`edit` tool **không** truy cập được `D:\` | dùng `exec` + file `.py` trong workspace |
| `edit` tool fail trên file CRLF | patch bằng Python `str.replace` |
