# Chương 2 — Phương pháp (kiến trúc & công nghệ)

**Môn:** IT252BIDA — Xử lý dữ liệu lớn · **GV:** PhD. Võ Thị Hồng Tuyết
**Người thực hiện:** Trần Khôi Nguyên (MIT26004) — nhóm 4

---

## 2.1 Yêu cầu đề cương và cách ánh xạ

Đề cương môn yêu cầu chuỗi công nghệ cụ thể. Bảng dưới ánh xạ từng yêu cầu
→ thành phần đã triển khai → bằng chứng đo được.

| Yêu cầu đề cương | Thành phần | File | Bằng chứng |
|---|---|---|---|
| *Connect and query by PySpark* | EDA + MLlib trên PySpark 4.2.0 | `src/eda_spark.py`, `src/train_spark_ml.py` | Phân bố khớp pandas 100%; F1 0.8702 |
| *Database with MongoDB* | MongoDB 8.0.12, 5 index, aggregation | `src/mongo_store.py` | 141,725 doc · 6,917 docs/s · agg 0.72s |
| *Statistical with R Language* | Kiểm định Mann-Whitney, AUC (pROC) | `r/analysis.R` | p = 0 · AUC(độ dài) 0.8032 · 5 biểu đồ |
| *Build prototype and repair data* | App Streamlit đọc MongoDB | `app/streamlit_app.py` | 5 tab, 0 exception, metric khớp Spark |
| *Build source code and evaluation* | Baseline sklearn + ablation + LOSO | `src/train_baseline.py`, `src/loso_eval.py` | F1 0.9521, ablation −2.13 điểm |
| *Experiments and results* | Đo chi phí scale + benchmark 1M | `src/benchmark_scale.py` | 827,422 dòng, ~970k dòng train |
| *Final project = document + source code* | Repo + báo cáo này | — | 40 file Python, 16 tài liệu |

---

## 2.2 Kiến trúc tổng thể — 2 đường dữ liệu

```
                    ┌──────────────────────────────────────────┐
                    │         NGUỒN GỐC (HuggingFace)         │
                    │  wildguardmix · SPML · S-Labs · xTRam1   │
                    │  toxic-chat · guychuk · wildjailbreak    │
                    │  deepset · WildChat-1M · lmsys-chat-1m   │
                    └───────────────┬──────────────────────────┘
                                    │ 10 loader (src/prepare_data.py)
                                    ▼
                    ┌──────────────────────────────────────────┐
                    │  CHUỖI XỬ LÝ: dedupe → chống leakage   │
                    │  → split theo nhóm → 4 parquet            │
                    └───────┬──────────────────────┬───────────┘
                            │                      │
              BATCH PATH    │                      │   OPERATIONAL PATH
              (đào dữ liệu, │                      │   (truy vấn tương tác,
               huấn luyện)  │                      │    dashboard, ghi log)
                            ▼                      ▼
        ┌───────────────────────────┐   ┌────────────────────────────┐
        │  all/train/val/test      │   │  MongoDB 8.0.12            │
        │  .parquet  (columnar)    │   │  prompt_injection.prompts  │
        └────────┬──────────────────┘   │  5 index                   │
                 │                      │  141,725 doc                │
                 ▼                      └──────┬─────────────────────┘
   ┌──────────────────────────────┐               │
   │  PySpark 4.2.0 (local[4])   │◄──────────────┘  đọc lại bằng PySpark
   │  ├─ EDA: Spark SQL           │
   │  ├─ MLlib pipeline           │
   │  └─ Đo chi phí scale         │
   └────────┬─────────────────────┘
            │
     ┌──────┴───────┬──────────────┐
     ▼              ▼              ▼
┌─────────┐  ┌──────────┐  ┌──────────────────┐
│  R 4.6.1│  │ Streamlit│  │  sklearn baseline│
│ thống kê │  │ 1.66.0  │  │  (đối chứng)    │
│ + 5 PNG  │  │ 5 tab   │  │  F1 0.9521       │
└─────────┘  └──────────┘  └──────────────────┘
```

### 2.2.1 Vì sao tách 2 đường — đây là luận điểm chính

Nếu chỉ dùng MongoDB thì không train được (không có Spark ML trên Mongo).
Nếu chỉ dùng parquet thì mất khả năng truy vấn tương tác, không có prototype,
và không đáp ứng yêu cầu *"Database with MongoDB"* của đề cương.

| Đường | Công nghệ | Dữ liệu | Phù hợp với |
|---|---|---|---|
| **Batch** | parquet → PySpark | 141,725 dòng, 9 cột | Huấn luyện, đào dữ liệu, thống kê toàn bảng |
| **Operational** | MongoDB | 141,725 doc, +`text_len`, +`inserted_at` | Truy vấn có index, dashboard, ghi log sự kiện |

**Bằng chứng phân định:** MongoDB nhanh hơn Spark ở phép aggregation *có index*
(0.72s vs 2.7s) vì quét index, không quét toàn bảng. Nhưng khi scan toàn bảng
thì Spark mạnh hơn (đọc song song + columnar). Hai engine **bổ trợ nhau**, không
thay thế.

---

## 2.3 Lớp PySpark (batch path)

### 2.3.1 EDA bằng Spark SQL — `src/eda_spark.py`

Dùng `groupBy` + `count` + `avg` + `length` + `crosstab` thuần Spark SQL.
Kết quả so với pandas:

| Phép | Spark | pandas |
|---|---:|---:|
| `groupBy(source)` | 5.89s | 0.144s |
| `groupBy(label)` | 2.02s | — |
| `crosstab(source, label)` | 2.74s | — |
| `length_by_label` | 3.88s | 0.447s |
| **Tổng** | **80.67s** | **2.69s** |

⇒ Spark **chậm hơn pandas ~30×** ở 141k dòng. **Đây là kết quả trung thực,
không phải lỗi** — ở quy mô này overhead khởi tạo session + JVM chiếm ưu thế.
Cùng bộ dữ liệu, **5 phân bố khớp 100%** → Spark đọc và tính đúng, chỉ chậm hơn.

Điểm này được ghi thẳng vào báo cáo, không tô đẹp. Nó cũng là lập luận cho
mục 2.7: **Spark chỉ bắt đầu thắng khi vượt ngưỡng dữ liệu**.

### 2.3.2 Pipeline MLlib — `src/train_spark_ml.py`

```
Tokenizer(text → words) → HashingTF(words → features, 2^18) → IDF → LogisticRegression(50 iter, regParam 0.1)
```

Chọn `HashingTF` thay vì `CountVectorizer` vì không cần vocabulary (tránh rò rỉ
từ vectorizer) và chịu được corpus lớn hơn.

**So sánh với baseline sklearn (TF-IDF word 1-2 + char_wb 3-5, 120k chiều):**

| Chỉ số | MLlib | sklearn | Δ |
|---|---:|---:|---:|
| F1 (test) | 0.8702 | **0.9521** | **−0.0819** |
| AUC | 0.9801 | **0.9922** | −0.0121 |
| Accuracy | 0.9270 | 0.9708 | −0.0438 |
| Precision | 0.9662 | 0.9614 | +0.0048 |
| Recall | 0.7915 | 0.9430 | **−0.1515** |

MLlib **thua về recall** (0.7915 vs 0.9430) — bỏ sót nhiều attack hơn.

### 2.3.3 Chi phí scale — đo, không đoán

**Cấu hình partition** (109,543 dòng train, `spark.sql.shuffle.partitions` thay đổi):

| Partition | Fit | s/100k dòng |
|---:|---:|---:|
| 2 | 201.59s | 184.0 |
| 8 | 211.60s | 193.2 |
| 32 | 263.70s | 240.7 |

⇒ Tăng partition **làm chậm hơn**. Ở 32 partition, mỗi task chỉ ~3,400 dòng
— thấp hơn nhiều so với ngưỡng 100k–200k dòng/task mà Spark khuyến nghị.
Overhead scheduler + mỗi task đọc lại vocabulary của HashingTF.

**Nhân bản dữ liệu** (`unionByName`):

| Bản sao | Dòng | Fit | s/100k dòng |
|---|---:|---:|---:|
| ×1 | 109,543 | 192.27s | 175.5 |
| **×2** | 219,086 | 166.91s | **76.2 (−57%)** |

⇒ Nhân bản ×2 **nhanh hơn 57%** vì tăng số partition → task nhỏ hơn → phân
song song hoá tốt hơn.

**Kết luận then chốt:** ở 141k dòng, pipeline chỉ có **1 job** — chưa tách được
song song. Bắt đầu tách từ 219k dòng. Đó là lý do phải đo trên corpus ~1M
(mục 2.7).

---

## 2.4 Lớp MongoDB (operational path) — `src/mongo_store.py`

MongoDB 8.0.12, collection `prompts`, database `prompt_injection`.

### 2.4.1 Schema & index

9 cột gốc (chuẩn hoá từ parquet) + 2 cột dẫn xuất:

| Cột dẫn xuất | Kiểu | Ý nghĩa |
|---|---|---|
| `text_len` | int | độ dài ký tự — dùng bucket, không phải đo lại mỗi lần |
| `inserted_at` | datetime (UTC) | thời điểm nạp — truy vết batch |

5 index, **tạo trước khi insert** (đo được: `index_build_sec` 0.13s):

```
label_1_source_1   source_1_split_1   family_1_label_1   text_len_1   pair_id_1
```

Index phục vụ đúng 3 truy vấn dashboard: lọc theo nhãn+nguồn, theo nguồn+split,
theo family+nhãn, và duyệt theo độ dài.

### 2.4.2 Kết quả

| Chỉ số | Giá trị |
|---|---|
| Số doc nạp | 141,725 |
| Thời gian nạp | 20.49s (batch 5,000) |
| Tốc độ | **6,917 docs/s** |
| `dataSize` | 124,850,603 B (≈2.6× parquet 47.6 MB) |
| Aggregation `$group` source×label | **0.72s** (17 nhóm) |
| Đọc lại bằng PySpark | 50,000 doc / 23.29s, +groupBy = 32.86s (12 nhóm) |

**Kiểm chứng chéo:** `mongo_matches_parquet = true` — số dòng, số nhãn và
phân phối độ dài khớp 100%.

> **Ghi chú kỹ thuật:** `coll.drop()` xoá **cả index** → phải tạo lại index sau
> khi drop. Và `$percentile` ở MongoDB 8.0 **bắt buộc** có `method`
> (`"approximate"`) với `p` là số **0..1** (không phải 0..100).

---

## 2.5 Lớp R — thống kê — `r/analysis.R`

R không đọc parquet → `src/export_for_r.py` export từ MongoDB ra CSV:

| File | Dung lượng | Nội dung | Thời gian |
|---|---:|---|---:|
| `out/r_corpus.csv` | 102.6 MB | 141,725 dòng × 10 cột | 7.1s |
| `out/r_summary.csv` | 2,989 B | 47 dòng — source×label×family×split | 2.0s |
| `out/r_length_stats.csv` | 1,176 B | 17 dòng — phân phối độ dài | — |

R 4.6.1, package `jsonlite` + `pROC`.

### 2.5.1 Kiểm định giả thuyết

| Kiểm định | Giả thuyết | Kết quả | Quyết định |
|---|---|---|---|
| **Mann-Whitney U** (độ dài) | H₀: phân phối độ dài benign = attack | **W = 925,758,320, p = 0.0** | **Bác bỏ H₀** |
| **AUC (pROC)** của riêng độ dài | — | **0.8032** | Tín hiệu mạnh, **chưa đủ phân loại** |

> **Lỗi đã phát hiện và sửa:** công thức AUC viết tay bằng rank-sum ban đầu cho
> **0.3675** (sai). Công thức đúng là `1 − W/maxU`; đã **verify lại bằng pROC**
> → 0.8032 khớp. Đây là bài học: số "trông hợp lý" vẫn có thể sai, phải kiểm
> chứng bằng công cụ độc lập.

### 2.5.2 5 biểu đồ sinh ra

| File | Nội dung | Dùng ở |
|---|---|---|
| `r01_length_by_label.png` | Histogram độ dài benign vs attack (log y) | Chương 3, mục độ dài |
| `r02_label_by_source.png` | Stacked bar nhãn theo 10 nguồn | Chương 1, mục phân bố nguồn |
| `r03_boxplot_by_source.png` | Boxplot độ dài theo nguồn (log x) | Chương 3, mục độ dài |
| `r04_family_label.png` | Family × nhãn | Chương 3, mục family |
| `r05_attack_ratio.png` | Tỉ lệ % attack theo nguồn | Chương 1 |

---

## 2.6 Prototype — App Streamlit — `app/streamlit_app.py`

**Quyết định thiết kế quan trọng: 1 process, không tách frontend/backend.**
Streamlit đã gộp server + client → **không cần viết API FastAPI/Flask riêng**.
Viết full-stack sẽ tốn thời gian cho phần không mang giá trị nghiên cứu.

| Tab | Chức năng | Nguồn |
|---|---|---|
| Tổng quan | 4 metric + bảng source×nhãn + family×nhãn | MongoDB aggregation |
| Tra cứu | Lọc nguồn/family/nhãn + tìm regex trong text | MongoDB `find` + `$regex` |
| Phân bố độ dài | Bar chart 5 bucket × 2 nhãn | MongoDB `$switch` |
| Benchmark scale | Bảng partition/replication + MLlib vs sklearn | `out/*.json` |
| Dữ liệu thô | 1 document BSON mẫu + mô tả schema | MongoDB `find_one` |

**Kiểm chứng** (`streamlit.testing.v1.AppTest`): 0 exception, 5 tab, 5 dataframe,
metric **141,725 / 88,655 / 53,070 / 37.45%** → khớp Spark SQL 100%.

> Metric dashboard lấy **trực tiếp từ MongoDB**, không đọc file metric → nếu
> MongoDB lệch parquet thì dashboard hiện ngay. Đây là kiểm tra chéo độc lập.

> **Gotcha:** `st.cache_data` **không hash được** `pymongo Collection` → phải
> đặt tiều tố `_` cho tham số (`def agg_source_label(_coll)`).

---

## 2.7 Đo trên corpus thật (~1M dòng) — `src/benchmark_scale.py`

### 2.7.1 Vấn đề phát hiện được: 9/12 shard WildChat bị cắt dở

Script tải cũ dùng `curl -C -` với `--max-time`. Khi timeout, **file dở vẫn được
giữ lại** và lần chạy sau coi như "đã tải xong" → file hỏng **không bị phát hiện**.

Phát hiện bằng magic bytes (`PAR1` ở đầu **và** cuối file):

```python
pq.ParquetFile(p).metadata.num_rows   # ArrowInvalid: Parquet magic bytes not found in footer
```

| Shard | Local (trước) | Remote | Trạng thái |
|---|---:|---:|---|
| 00 | 35.2 MB | 230.8 MB | CẮT 15% |
| 02 | 106.6 MB | 205.7 MB | CẮT 52% |
| 04 | 114.5 MB | 208.3 MB | CẮT 55% |
| 05 | 17.6 MB | 200.9 MB | CẮT 9% |
| 06 | 19.6 MB | 189.5 MB | CẮT 10% |
| 07 | 4.6 MB | 188.4 MB | CẮT 2.5% |
| 09 | 105.9 MB | 269.0 MB | CẮT 39% |
| 10 | 57.5 MB | 336.5 MB | CẮT 17% |
| 01, 11, 12, 13 | 0 | 215–336 MB | THIẾU |
| 03, 08 | 216.9 / 181.0 MB | khớp | OK |

Sau khi sửa (HEAD Content-Length → `curl -C -` resume → **verify magic bytes** →
tối đa 10 lần thử): **14/14 shard đọc được, 837,989 dòng, 3.36 GB**.

> **Bài học chung:** script tải phải **verify magic bytes**. Coi "file tồn tại" là
> "file đúng" là lỗi âm thầm đắt nhất — nó làm hỏng mọi phép đo phía sau mà
> không có dấu hiệu nào báo lỗi.

### 2.7.2 Thiết kế benchmark

Lấy **first user turn** của mỗi hội thoại bằng **Spark SQL thuần** (không Python
UDF, để tránh bottleneck serialize):

```python
users  = F.filter(col, lambda m: m["role"] == "user")
text   = F.element_at(F.transform(users, lambda m: m["content"]), 1)
```

Lọc `length(text) > 20`, bỏ dòng `redacted`, gán `label=0`, `split=unassigned`,
`family=benign_stream` — vì đây là benign **hữu cơ**, không phải benign được
dán nhãn thủ công.

---

## 2.7b Detector streaming — `src/stream_detector.py`

Kiến trúc 2 tầng trong **một** pipeline Spark:

```
JSON files / thư mục
   └─> Spark Structured Streaming (foreachBatch)
         ├─> Rule layer  : 8 regex theo kỹ thuật tấn công  (Spark SQL `rlike`)
         └─> Model layer : MLlib LogisticRegression        (Python UDF cho probability)
               └─> hợp nhất: rule_score > 0 → attack, ngược lại model_pred
                     ├─> out/stream_out/detections.jsonl
                     └─> MongoDB `prompt_injection.detections`
```

**Vì sao tách 2 tầng:**

| Tầng | Đặc điểm | Vai trò |
|---|---|---|
| Rule | Regex cố định theo kỹ thuật tấn công | Bắt mẫu công khai, **giải thích được** (kèm kỹ thuật + đoạn text khớp) → false positive thấp |
| Model | Học từ dữ liệu | Bắt mẫu biến thiên, không giải thích được → bổ sung recall |

Kết quả replay trên 12 dòng tự viết tay: **rule bắt 7/7 attack · 0/5 false
positive**, model layer flag 4/7 với 0 false positive.

**Ràng buộc kỹ thuật đã phát hiện:**
- Rule layer dùng **Spark SQL native** (`rlike`, `regexp_extract`) thay vì Python
  UDF, vì `sparkContext.addPyFile()` trên Windows cần `HADOOP_HOME`
  (winutils.exe). Native → chạy trong JVM, không ship file, chạy được ở cluster mode.
- Cột `probability` của MLlib là **VectorUDT** → SQL không trích được
  (`probability[1]`, `element_at`, `vector_to_array` đều fail) → model layer phải
  dùng Python UDF, chỉ chạy được khi driver và executor cùng môi trường.
- `PipelineModel.write().save()` cũng cần winutils → model được train **inline**
  trong bộ nhớ thay vì load từ đĩa.

---

## 2.8 Đánh giá — 3 mức

| Mức | Cách đo | Trả lời RQ nào |
|---|---|---|
| **In-domain** | Test split 19,374 dòng (80/10/10 theo `source`) | RQ1 |
| **Cross-dataset (in-train)** | F1 theo từng nguồn, nhưng nguồn **có trong train** | RQ2 (mức yếu) |
| **LOSO (zero-shot thật)** | Bỏ hẳn 1 nguồn khỏi train, đánh giá trên nguồn đó | RQ2 (mức mạnh) |

**Vì sao cần LOSO:** per-source breakdown ở Chương 3 **không** trả lời được
"model có tổng quát hóa không", vì cả 10 nguồn đều nằm trong tập train. LOSO
mới là đo zero-shot thật. Chi phí: 10 lần train.

**Ablation RQ3:** train lại chỉ với unigram → so sánh F1. Đo được: F1 tụt
**2.13 điểm** (0.9670 → 0.9308 trên validation). ⇒ phần lớn hiệu năng đến từ
**từ vựng**, không phải chỉ độ dài — nhưng độ dài vẫn đóng góp đáng kể, và
AUC(độ dài) = 0.8032 cho thấy nếu chỉ dùng độ dài thì vẫn có tín hiệu thật.

---

---

## 2.9 Môi trường tái lập — cái gì tái lập được, cái gì không

Yêu cầu chung khi chạy thí nghiệm là **thống nhất môi trường, ghim version, cùng
nền tảng**. Mục này ghi rõ đồ án đã làm được đến đâu và **phần nào không thể đồng
nhất** — vì che phần không đồng nhất đi sẽ là báo cáo sai.

### 2.9.1 Ghim version — đã làm

`requirements.txt` pin **toàn bộ** dependency (21 package), không dùng `>=`:

| Nhóm | Package |
|---|---|
| Core | `pandas==3.0.3` · `numpy==2.5.1` · `pyarrow==26.0.0` · `scikit-learn==1.9.0` · `scipy==1.18.0` |
| Big Data | `pyspark==4.2.0` |
| Tải dữ liệu | `datasets==5.1.0` · `huggingface-hub==2.2.0` · `duckdb==1.5.6` |
| NoSQL | `pymongo==4.19.0` |
| App + báo cáo | `streamlit==1.66.0` · `python-pptx==1.0.2` · `matplotlib==3.11.2` |

Runtime cũng được ghim: **Python 3.14.5**, **Java 24.0.2** (Spark cần Java 17+).
Toàn bộ giá trị trên được sinh tự động bằng `tools/capture_env.py` → `Environment.md`,
nên không phải gõ tay (gõ tay sẽ lệch sau mỗi lần `pip install`).

### 2.9.2 Số liệu nào tái lập được

| Loại số liệu | Tái lập? | Vì sao |
|---|---|---|
| F1 / AUC / precision / recall / FPR / confusion matrix (sklearn) | ✅ **Có** | `train_test_split(random_state=42)`, `LogisticRegression(solver="liblinear")` là **deterministic** (không random khởi tạo), TF-IDF không có yếu tố ngẫu nhiên. Lệch tối đa ở chữ số thập phân thứ 4 do thứ tự cộng dồn float của BLAS |
| Số dòng corpus (141,725 / 109,543 / 12,808 / 19,374) | ✅ **Có** | Dedupe bằng hash chuỗi, split bằng seed cố định |
| Phân bố EDA | ✅ **Có** | Spark SQL thuần, đã đối chiếu pandas **khớp 100%** |
| F1 / AUC của MLlib | ⚠️ **Gần đúng** | Kết quả Spark phụ thuộc **số partition + số core** (thứ tự aggregation khác nhau). Đã cố định `local[4]` + `spark.sql.shuffle.partitions=8` trong code, nhưng đổi số core vẫn lệch chữ số thứ 4 |
| Thời gian (fit_sec, s/100k dòng, docs/s, Spark 80.7s) | ❌ **Không** | Phụ thuộc CPU/RAM/ổ đĩa. Đây là **số của một máy**, không phải hằng số |

### 2.9.3 Ghim môi trường khác với ghim nền tảng

Đây là chỗ dễ hiểu sai nhất:

- **Ghim version** = cùng thư viện, cùng phiên bản → đảm bảo **hành vi code** giống nhau.
- **Cùng nền tảng** (Colab / VM / máy local) → đảm bảo **số đo thời gian** so sánh được.

Đồ án chạy **máy local** (Windows 11, i7-13620H, 32 GB, CPU only, Python 3.14.5,
Java 24.0.2, Spark 4.2.0). Điều này **không** ảnh hưởng tới tính đúng đắn của
F1/AUC — vì đó là phép tính số học trên cùng dữ liệu, cùng version thư viện.
Nó chỉ ảnh hưởng tới **số giây**, và báo cáo đã ghi rõ mọi số thời gian đều kèm
cấu hình máy đo.

Chạy lại trên Colab sẽ **không** cho ra 56.79s/100k dòng — có thể nhanh hoặc chậm
hơn 2–3× tuỳ GPU/CPU runtime. Nhưng **F1 0.9521 và AUC 0.9922 vẫn phải ra đúng**,
và đó chính là phép kiểm tra tái lập: nếu F1 lệch, là do version, không phải do máy.

### 2.9.4 Vì sao chọn máy local thay vì Colab

| Tiêu chí | Local (đã dùng) | Colab |
|---|---|---|
| Dung lượng | Ổ D: đủ cho 19 file / 1.19 GB dataset + 3.36 GB shard WildChat | Giới hạn ~100 GB, nhưng phiên bị ngắt sau 12h |
| Cài MongoDB | ✅ Server 8.0.12 native | ❌ Không có service, phải `apt install` mỗi phiên |
| Cài R | ✅ R 4.6.1 native | ✅ Có sẵn trong runtime |
| Driver memory | ✅ Set được `--driver-memory 10g` | ❌ RAM runtime cố định, OOM ở 969k dòng |
| Tái lập | ✅ Máy của người nộp, ghim được | ⚠️ Runtime Colab đổi version liên tục |

**Kết luận:** local là lựa chọn **đúng cho đồ án này** vì đề cương bắt buộc
MongoDB + R native, và benchmark 1M dòng cần >8 GB driver memory — Colab free
không đáp ứng. Rủi ro duy nhất là số thời gian không so sánh trực tiếp được với
nhóm chạy Colab, và báo cáo đã xử lý bằng cách **luôn ghi kèm cấu hình máy**.

### 2.9.5 Cách tái lập trên máy khác

```powershell
git clone <repo> ; cd Prompt_Injection
pip install -r requirements.txt          # ghim sẵn toàn bộ version
$env:PI_DATA_BASE = "D:\...\datasets\llm_security"
python tools\capture_env.py              # ghi lại môi trường THỰC TẾ của máy mới
python src\prepare_data.py               # phải ra đúng 141,725 dòng
python src\train_baseline.py             # phải ra F1 0.9521 / AUC 0.9922
```

Nếu `prepare_data.py` ra số dòng khác → **dữ liệu nguồn khác**, không phải môi trường.
Nếu số dòng đúng mà F1 lệch > 0.001 → **version thư viện khác**, so `Environment.md`
giữa 2 máy. Đây là 2 nguyên nhân tách biệt, đừng gộp.

---

*Chương 2 — xem Chương 3 (kết quả & đánh giá).*
