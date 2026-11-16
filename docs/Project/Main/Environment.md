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
| Python Host | 3.14.5 (`C:\Users\PC\AppData\Local\Python\pythoncore-3.14-64`) | Môi trường hệ thống chứa PySpark |
| Python Project venv | 3.14.5 (`D:\Master Exers\Big Data\Recomendation_System\.venv`) | Môi trường cục bộ có link site-packages |
| Jupyter Kernel | `Python 3.14 (BigData RecSys .venv)` (`recsys-project-venv`) | Kernel chuẩn dành riêng cho notebook dự án |
| PySpark | **4.2.0** | Cấu hình chạy `local[4]` (hoặc `local[8]`), driver 6g |
| pyarrow | **26.0.0** | Ingest CSV → Parquet gốc (không cần JVM, 26s cho 25M dòng) |
| pandas | 3.0.3 | PySpark cảnh báo chưa hỗ trợ đầy đủ pandas ≥ 3.0.0 (vẫn hoạt động tốt cho profile) |
| numpy | có | Dùng cho chunking và tính top-K |
| pymongo | có | Kết nối lưu trữ kết quả MongoDB |
| streamlit | có | Web UI demo |
| Java | `jdk-24` tại `C:\Program Files\Java\jdk-24` (host) · **OpenJDK 1.8.0_232** trong container Hadoop | |
| **R** | R 4.6.2 tại `C:\Program Files\R\R-4.6.2\bin\Rscript.exe` | Thư viện người dùng `D:\R-library` cho thống kê bootstrap & paired tests |
| **winutils.exe** | `D:\recsys_data\tools\hadoop\bin\winutils.exe` (112.640 B) | Bắt buộc để Spark ghi/đọc Parquet trên Windows |
| **hadoop.dll** | `D:\recsys_data\tools\hadoop\bin\hadoop.dll` (85.504 B) | Bắt buộc kèm winutils; thiếu file này → `UnsatisfiedLinkError: NativeIO$Windows.access0` |
| `HADOOP_HOME` | `D:\recsys_data\tools\hadoop` | Set trong process bởi `src/utils/spark_utils.ensure_hadoop_home()` |

---

## 3. Docker, Hadoop & Môi trường thực thi cục bộ

| Thành phần | Trạng thái hiện tại | Ghi chú vận hành |
|---|---|---|
| Chế độ thực thi chính | **PySpark local (`local[4]`)** | Driver 6GB, chạy trực tiếp trên Windows host trong `.venv` |
| Local `.venv` | `d:\Master Exers\Big Data\Recomendation_System\.venv` | Khởi tạo với `--system-site-packages` để dùng PySpark 4.2.0 và Java 24 host |
| Jupyter Server | `http://localhost:8888/` | Root tại workspace; đã đăng ký kernel `Python 3.14 (BigData RecSys .venv)` |
| Docker engine | 28.3.3 (Linux container) | Dùng khi cần chạy Hadoop cluster hoặc MapReduce job container |
| Hadoop cluster | `bde2020/hadoop-*:2.0.0-hadoop3.2.1-java8` | Tùy chọn (đã kiểm định MapReduce Java). Khi chạy local notebook/pipeline, không bắt buộc giữ container bật |
| Local `spark-submit` | ❌ không có binary riêng | Sử dụng API `pyspark.sql.SparkSession` trực tiếp trong script Python/Jupyter |
| Local `hadoop.dll` / `winutils.exe` | ✅ **đã cài 2026-11-15** tại `D:\recsys_data\tools\hadoop\bin\` | `df.write.parquet` và đọc thư mục Parquet **đều chạy được**; cần **cả hai** file, thiếu một là fail |

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
| Ghi Parquet | `HADOOP_HOME and hadoop.home.dir are unset` (thiếu `winutils.exe`) | ✅ **ĐÃ SỬA** — `HADOOP_HOME` + `bin\winutils.exe` + `bin\hadoop.dll`; `df.write.parquet` OK |
| Đọc Parquet (thư mục) | `UnsatisfiedLinkError: NativeIO$Windows.access0` (có `winutils.exe` nhưng thiếu `hadoop.dll`) | ✅ **ĐÃ SỬA** — thêm `hadoop.dll` + prepend `bin` vào `PATH`; `spark.read.parquet(dir)` OK |
| Đọc Parquet (file) | ✅ OK 25.000.095 rows | vẫn dùng được nếu chỉ có 1 file |
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
| `D:\recsys_data\parquet\ratings\part-00000.parquet` | cache Parquet | 175.961.682 B, 31 row-groups |
| `D:\recsys_data\splits\<strategy>\{train,test}\` | 3 split đã materialize (notebook 04) | **735.030.695 B** tổng (8 partition train / 4 test mỗi split) |
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

## 11. Environment contract cho Paper 01 reproduction

- Repository: `https://github.com/putatu/dataLeakageRec`
- Clone riêng: `D:\recsys_papers\dataLeakageRec`; pin commit/tag trước khi chạy.
- Không cài dependency Paper 01 vào project Python hiện tại.
- Ghi Python, OS, Java, framework/library versions, CPU/RAM/GPU, dataset path/checksum.
- Nếu repository yêu cầu version khác Python 3.14/PySpark 4.2, ưu tiên environment tương thích repository; không sửa code trước smoke test.
- Không giả định Paper 01 dùng Spark/Hadoop. Chỉ ghi khi README hoặc methods xác nhận.

### Deadline execution profile

Project experiment chạy bằng environment đã verify của project: Python 3.14, PySpark 4.2.0, local mode, MovieLens-25M project dataset, MostPopular và ALS. Đây là `method-informed implementation`, không phải Paper 01 faithful reproduction.

Environment Paper 01 `paper01-tf114` chỉ dùng cho repository smoke test. BPR smoke test đã mất 489,40 giây cho 1 epoch và 10 user trên CPU; không chạy BPR 300 epoch trong critical path. Ghi kết quả này vào phụ lục runtime limitation.

Bảng chính deadline:

```text
3 split × 2 model × 3 seed
random80_20 | temporal_global | leave_one_out
MostPopular | ALS
seed: 42, 2024, 7
```

Mỗi run phải ghi: protocol ID, split, model, seed, HR/NDCG, leakage diagnostics, popularity metrics, wall-clock, CPU/RAM/Spark/Java và classification.

### Protocol checklist

| Thành phần | Paper 01 cần xác minh | Project không được thay thế bằng |
|---|---|---|
| Dataset | MovieLens subset và time interval | full 25M project dataset |
| Split | leave-last-one-out theo paper | `random80_20` project |
| Models | BPR, NeuMF, SASRec, LightGCN | ALS/MostPopular |
| Metrics | paper metric/cutoff | project metric nếu khác |
| Seed | paper/repository hoặc `not_reported` | project seed 42 |
| Runtime | paper/repository/hardware | local Spark runtime |

### Run stages

1. README/config inspection.
2. Dependency/environment setup.
3. Dataset/preprocessing smoke test.
4. One small model smoke test.
5. One paper-config run if smoke test passes.
6. Full run only after report has difference ledger.

### Output and stop conditions

Reports: `docs/Project/Plans/Research/Implementation/`. Temporary clone/data: `D:\recsys_papers\`. Logs: `logs/paper01\`. Do not mix with project `runs/`, `D:\recsys_data\poc\`, MongoDB `recsys`.

Stop and log `blocked` when dependency, dataset, GPU/RAM, repository link or license prevents faithful run. Command passing alone is only `smoke_test_pass`, not reproduction success.

## 12. Pre-run gate

Before cloning/running Paper 01, three docs must agree on two-track boundary, paper protocol, project protocol, isolated path, report path and classification rules. Inspect repository first; do not start full model training.

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
