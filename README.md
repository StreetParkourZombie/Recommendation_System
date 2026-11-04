# Recomendation System — Audit chiến lược chia tập dữ liệu

**Đề tài:** Đánh giá tác động của chiến lược chia tập dữ liệu đến tín hiệu đo và thiên lệch phổ biến trong hệ thống gợi ý trên nền tảng xử lý dữ liệu lớn.

**Môn:** IT252BIDA (Xử lý dữ liệu lớn) + IT252STRM (Phương pháp nghiên cứu khoa học)
**Dataset:** MovieLens ml-25m — 25.000.095 tương tác, 162.541 user, 59.047 phim, 1995-01-09 → 2019-11-21
**License:** research-use — bắt buộc cite Harper & Konstan (2015), DOI 10.1145/2827872
**Deadline đề cương:** 2026-11-08

---

## Chạy lại

```powershell
# 0. Chuẩn bị (1 lần)
python scripts\00_download_and_prepare.py       # CSV -> Parquet (26s)

# 1. Nạp HDFS
python scripts\01_ingest_hdfs.py                 # -> /recsys/ratings/part-00000.parquet (167,8 MB)

# 2. MapReduce (Java, chạy trong container Hadoop + YARN)
docker cp D:\recsys_data\raw\ml-25m\ratings.csv namenode:/tmp/ratings.csv
docker cp scripts\02_PopularityByYear.java namenode:/tmp/PopularityByYear.java
docker exec namenode bash /tmp/run_mr.sh         # JOB_STATUS=SUCCESS, 323.737 dong

# 3. Đối chiếu MapReduce vs Spark (gate G3)
python scripts\08_crosscheck_g3.py               # -> results/g3_crosscheck.json

# 4. Audit 3 chiến lược chia tập (mỗi split ~4 phút)
python scripts\04_audit_spark.py random80_20
python scripts\04_audit_spark.py temporal_global
python scripts\04_audit_spark.py leave_one_out

# 5. Nạp MongoDB (NGUỒN GHI DUY NHẤT cho recsys.audit_metrics)
python scripts\05_store_mongodb.py --reset

# 6. Phân tích R + biểu đồ (R chỉ ĐỌC recsys.audit_metrics)
& "C:\Program Files\R\R-4.6.2\bin\Rscript.exe" scripts\06_analysis_r.R

# 7. Dashboard
python -m streamlit run scripts\07_dashboard.py --server.headless true

# 8. Kiểm tra độ dài Gap 3 phần (PPNCKH: 200–250 từ)
python scripts\09_count_gap.py
```

**R library path:** `.libPaths(c('D:/R-library', .libPaths()))` — R không ghi được vào `C:\Program Files`.

**Lưu ý:** `streamlit` không có trong PATH → dùng `python -m streamlit`.

---

## Trạng thái pipeline (04/11/2026 02:20)

| Hạng mục | Trạng thái | Bằng chứng |
|---|---|---|
| Parquet (25.000.095 dòng) | ✅ | `data/interim/`, SHA-256 trong `data/ratings.parquet.sha256` |
| HDFS ingest | ✅ | `/recsys/ratings/` — 167,8 MB |
| MapReduce Java + YARN | ✅ | `JOB_STATUS=SUCCESS` · 323.737 dòng output |
| Gate G3 (MR vs Spark) | ✅ **100% khớp** | `results/g3_crosscheck.json` |
| PoC Spark — 3 split × 2 model | ✅ | `results/poc6_*.json` |
| MongoDB | ✅ | `recsys.audit_metrics` 6 docs (42 field) · `item_profile` 62.423 docs |
| R analysis + biểu đồ | ✅ | 7 PNG + 2 CSV trong `reports/` |
| Streamlit dashboard | ✅ | HTTP 200 · `/_stcore/health → ok` |
| Gap 3 phần 200–250 từ | ✅ 237 từ | `scripts/09_count_gap.py` |
| SparkR / sparklyr | ❌ chưa cài | ghi rõ giới hạn trong `docs/Project/Main/Architecture.md` §5.2 |

---

## Kết quả chính (đo thật 2026-11-04)

### Chỉ số cấp dữ liệu

| Chiến lược | Train | Test | Vi phạm toàn cục | Vi phạm tương đối user | Item chưa từng xuất hiện | User lạnh | User đánh giá | User có relevant |
|---|---|---|---|---|---|---|---|---|
| Ngẫu nhiên 80/20 | 19.997.972 | 5.002.123 | **100,00%** | **98,91%** | 0,0559% | 0 | 162.541 | 158.688 |
| Theo thời gian toàn cục | 19.999.206 | 5.000.889 | 0,00% | 0,00% | **8,7594%** | 4.235.246 | 137.839 | **6.219** |
| Leave-one-out | 24.837.554 | 162.541 | 99,9988% | **0,00%** | 0,0388% | 0 | 162.541 | 96.003 |

### Hiệu quả gợi ý và thiên lệch phổ biến

| Chiến lược | Mô hình | NDCG@10 | Hit Rate@10 | Độ phủ danh mục | Gini phơi bày | Tỷ lệ thiên lệch phổ biến |
|---|---|---|---|---|---|---|
| Ngẫu nhiên 80/20 | Popularity | 0,0869 | – | 0,000177 | 0,9998 | **158,64** |
| Ngẫu nhiên 80/20 | ALS (implicit) | **0,2584** | 0,2942 | 0,061389 | 0,9827 | 12,26 |
| Theo thời gian toàn cục | Popularity | 0,0455 | – | 0,000290 | 0,9997 | **101,26** |
| Theo thời gian toàn cục | ALS (implicit) | **0,1364** | 0,1599 | 0,056629 | 0,9713 | 11,20 |
| Leave-one-out | Popularity | 0,0183 | – | 0,000170 | 0,9998 | **165,27** |
| Leave-one-out | ALS (implicit) | **0,0474** | 0,0141 | 0,061765 | 0,9812 | 12,41 |

**Ngưỡng liên quan:** rating ≥ 4,0. **ALS:** implicit feedback, rank 16, maxIter 8, regParam 0,05, alpha 10, seed 42, subsample 30.000 user.

### Chứng minh Big Data pipeline — gate G3 (ĐÃ PASS)

| Hạng mục | Kết quả |
|---|---|
| HDFS | `/recsys/ratings/part-00000.parquet` — 167,8 MB · 175.961.682 byte |
| MapReduce (Java, Hadoop 3.2.1, YARN) | `PopularityByYear` → `JOB_STATUS=SUCCESS` · 323.737 key (movieId, year) |
| Spark SQL cùng phép tính | 323.737 key |
| **Đối chiếu** | ✅ **100,0000% khớp** (323.737/323.737) · tổng 25.000.095 tương tác = kỳ vọng |
| Artifact | `results/g3_crosscheck.json` |

> Bẫy đã ghi nhận: MapReduce dùng UTC, Spark mặc định local (UTC+7) → phải set `spark.sql.session.timeZone=UTC`, nếu không G3 lệch 7,65%.

---

## 4 phát hiện chính

1. **Ngẫu nhiên 80/20 gây rò rỉ thời gian ở 98,91% tương tác kiểm định** — ngay cả khi so với lịch sử của chính người dùng đó, không chỉ so với mốc toàn cục.
2. **Không có chiến lược nào "miễn phí"**: đổi rò rỉ lấy dịch chuyển miền. Theo thời gian toàn cục loại bỏ rò rỉ (0%) nhưng 8,76% item kiểm định chưa từng xuất hiện và **chỉ còn 6.219 user có phản hồi tích cực** so với 158.688 — mẫu đánh giá co lại 25 lần.
3. **Metric rò rỉ phải tương đối theo user.** Định nghĩa toàn cục cho kết quả vô lý 99,9988% với leave-one-out, trong khi định nghĩa tương đối cho 0% — đúng như thiết kế.
4. **Thứ hạng mô hình không đảo chiều, nhưng độ lớn thay đổi 5,5 lần.** ALS > Popularity ở cả 3 chiến lược, nhưng NDCG@10 của ALS giảm từ 0,2584 (ngẫu nhiên) xuống 0,0474 (leave-one-out) — chênh lệch tuyệt đối có thể đủ để kết luận sai về mức hiệu quả.
5. **Thiên lệch phổ biến giảm mạnh khi dùng mô hình cá nhân hoá**: Popularity 101–165× so với trung bình catalog; ALS chỉ 11–12×. Nhưng độ phủ đuôi dài vẫn bằng 0 ở cả 6 tổ hợp → **thiên lệch phổ biến không được xử lý, chỉ được giảm nhẹ**.
6. **NDCG thấp không phải lỗi mô hình mà là lỗi thiết kế đo lường.** ALS explicit cho NDCG ≈ 0 vì xếp hạng theo sai số dự đoán rating → phim user đánh giá thấp bị đẩy xuống cuối. Phải dùng implicit ALS + ngưỡng liên quan.

---

## Cấu trúc

```
├── scripts/          # 00 prepare · 01 HDFS · 02 MR Java · 03 run MR · 04 audit
│                     # 05 mongo · 06 R · 07 dashboard · 08 G3 · 09 count gap
├── data/             # interim (parquet) · processed · CHECKSUMS
├── results/          # poc6_<split>.json · g3_crosscheck.json
├── reports/          # metrics_summary.csv · data_level_metrics.csv
├── docs/Project/Main/     # System_Context · Architecture · Metrics · Environment
├── docs/Project/Main/report/Big_Data/figures/  # 7 biểu đồ PNG
├── docs/Project/Plans/    # 00–07: đề tài, gap, tài liệu, ma trận, kế hoạch, dự phòng
└── logs/             # log thực nghiệm (UTF-8)
```

## Tài liệu

- `docs/Project/Plans/01_De_tai_va_Ke_hoach.md` — đề tài, RQ1–RQ5, W5H2, FINER, kiến trúc, timeline, kết quả đo thật
- `docs/Project/Plans/07_Gap_3_phan_Known_CriticalGap_Proposed.md` — gap 237 từ (đạt yêu cầu 200–250)
- `docs/Project/Plans/02_Nguon_du_lieu_va_URL.md` — URL, license, schema, checksum
- `docs/Project/Main/Metrics.md` — định nghĩa và công thức mọi chỉ số + bảng kết quả
- `docs/Project/Main/Architecture.md` — kiến trúc 4 tầng + 8 quality gate
- `docs/Project/Main/Environment.md` — môi trường đã verify + bảng lỗi đã vấp
