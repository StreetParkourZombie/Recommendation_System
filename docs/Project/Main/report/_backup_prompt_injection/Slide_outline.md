# Slide thuyết trình — IT252BIDA

**Tên đề tài:** Xây dựng pipeline Big Data phát hiện Prompt Injection
**SV:** Trần Khôi Nguyên (MIT26004) — nhóm 4
**GV:** PhD. Võ Thị Hồng Tuyết

> Gợi ý trình bày: 12–15 slide, mỗi slide 1 ý chính.
> Slide đánh dấu `🔴` là bắt buộc — đó là phần "đo được" khác biệt với bài nhóm khác.

---

## Slide 1 — Bìa

```
XÂY DỰNG PIPELINE BIG DATA PHÁT HIỆN PROMPT INJECTION
Trần Khôi Nguyên — MIT26004 — nhóm 4
IT252BIDA · Xử lý dữ liệu lớn · GV: PhD. Võ Thị Hồng Tuyết
```

---

## Slide 2 — Bài toán & 3 câu hỏi nghiên cứu

Prompt Injection = khiến LLM bỏ qua chỉ dẫn hệ thống, làm theo kẻ tấn công.

| RQ | Câu hỏi | Đo bằng |
|---|---|---|
| RQ1 | Phân biệt tốt đến đâu khi train/test cùng phân bố? | F1 test split |
| RQ2 | Đổi nguồn dữ liệu thì mất bao nhiêu? | F1 per-source + **LOSO** |
| RQ3 | Bao nhiêu phần hiệu năng đến từ **độ dài** vs **từ vựng**? | Ablation + AUC |

> Không chạy đua SOTA. Mục tiêu: **đo trung thực** khả năng tổng quát hóa.

---

## Slide 3 — Dữ liệu: 10 nguồn, 141,725 dòng

- 3 họ: adversarial · roleplay · **benign hữu cơ** (hội thoại thật)
- 188,366 dòng thô → dedupe → **141,725**
- 2 nguồn **chỉ benign** (WildChat, lmsys) · 1 nguồn **chỉ attack** (wildjailbreak)
- Split 80/10/10 **theo `source`**: train 109,543 · val 12,808 · test 19,374

📊 **Biểu đồ:** `out/r_plots/r02_label_by_source.png`

---

## Slide 4 — 🔴 Ba ca hiểu sai nhãn (phần em tự hào nhất)

Cột tên nghe như nhãn phân loại, nhưng thực chất đo thứ khác. **Phát hiện bằng bằng chứng, không phải cảm tính.**

| Dataset | Nghĩa thật | Hậu quả nếu dùng sai | Cách phát hiện |
|---|---|---|---|
| HackAPrompt | prompt **đã thắng** model | nhãn đảo nghĩa | 715 text có nhiều nhãn |
| WildJailbreak | **mức độc hại** | FPR = **1.0** | `data_type` = adversarial_harmful/benign |
| SPML | **mức gắn persona** | suy sai ý đồ | `Degree=10` ↔ roleplay lành mạnh |

→ HackAPrompt **loại khỏi corpus** (mất 227K dòng, tránh học sai bài toán)

> Quy tắc: **FPR = 1.0 là dấu hiệu nhãn sai, không phải model dở.**

---

## Slide 5 — Chống rò rỉ 3 lớp

| Lớp | Cơ chế | Kết quả |
|---|---|---|
| 1 | Dedupe toàn cục trên text chuẩn hoá | 0 trùng giữa split |
| 2 | Split **theo nhóm** (`crc32(task_type\|normal_input)`) | 1,397 nhóm guychuk |
| 3 | 1 benign + ≤4 attack mỗi nhóm | không cặp attack/benign cùng nhóm ở 2 split |

✅ Kiểm chứng: `verify_split.py` → **0 rò rỉ**

---

## Slide 6 — Kiến trúc: 2 đường dữ liệu

```
10 loader → dedupe → chống leakage → split
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
   BATCH PATH            OPERATIONAL PATH
   parquet               MongoDB 8.0.12
   → PySpark MLlib       → truy vấn, dashboard
   → R thống kê           → Streamlit
```

**Vì sao tách?** MongoDB không train được; chỉ parquet thì mất prototype + mất
yêu cầu *"Database with MongoDB"* của đề cương.

---

## Slide 7 — 🔴 So sánh 4 engine (số đo thật)

| Engine | Phép | Quy mô | Thời gian |
|---|---|---:|---:|
| pandas | groupBy + length | 141,725 | **2.69s** |
| Spark SQL | groupBy + length | 141,725 | **80.67s** |
| MongoDB | `$group` + `$percentile` | 141,725 | **0.72s** |
| R | Mann-Whitney + AUC | 141,725 | ~60s |

**Không engine nào thắng tuyệt đối** → đây là lý do kiến trúc 2 đường.
Và: **Spark chậm hơn pandas 30×** ở 141k dòng — ghi thẳng, không tô đẹp.

---

## Slide 8 — 🔴 Phát hiện quan trọng nhất: model học template, không học cơ chế

Cùng nguồn, cùng tập train:

| Nguồn | F1 sklearn (word 1-2 + char 3-5) | F1 MLlib (HashingTF unigram) | Δ |
|---|---:|---:|---:|
| **S-Labs** | **0.8624** | **0.2386** | **−0.6238** |
| xTRam1 | 0.9621 | 0.7418 | −0.2203 |
| guychuk | 0.9991 | 0.9916 | −0.0075 |

Recall MLlib ở S-Labs chỉ **0.1359** → bỏ sót **814/942** attack.

⇒ Prompt injection là **mệnh lệnh có cấu trúc** → cần n-gram, không chỉ unigram.
⇒ **char n-gram là thành phần bắt buộc**, không phải tuỳ chọn.

---

## Slide 9 — 🔴 RQ3: độ dài vs từ vựng

| Kiểm định | Kết quả | Kết luận |
|---|---|---|
| Ablation unigram | F1 0.9521 → 0.9308 (**−2.13 điểm**) | Phần lớn hiệu năng từ **từ vựng** |
| Mann-Whitney (R) | **W = 925,758,320, p = 0.0** | Độ dài **có** tín hiệu thật |
| AUC riêng độ dài (pROC) | **0.8032** | Nhưng **chưa đủ** phân loại |

Median benign 95 → attack 773 (×8.1).

⇒ Độ dài là **tín hiệu phụ trợ**, không phải đặc trưng quyết định.
⇒ Đây là lập luận chống lại **heuristic thuần** (dễ bypass, không học được gì).

---

## Slide 10 — 🔴 Chi phí scale — đo, không đoán

**Tăng partition → chậm hơn:**

| Partition | Fit | s/100k dòng |
|---:|---:|---:|
| 2 | 201.59s | 184.0 |
| 8 | 211.60s | 193.2 |
| 32 | 263.70s | 240.7 |

(ở 32 partition: ~3,400 dòng/task — thấp hơn nhiều ngưỡng 100k–200k/task)

**Nhân bản dữ liệu:**

| Bản sao | Dòng | Fit | s/100k dòng |
|---|---:|---:|---:|
| ×1 | 109,543 | 192.27s | 175.5 |
| **×2** | 219,086 | 166.91s | **76.2 (−57%)** |

⇒ Ở 141k dòng pipeline chỉ có **1 job** — chưa tách song song được.
⇒ **Đó là lý do phải đo ở ~1M dòng.**

---

## Slide 11 — 🔴 Benchmark corpus thật (~1M dòng)

- `allenai/WildChat-1M`: **14/14 shard** · 837,989 dòng · 3.36 GB
- `lmsys/lmsys-chat-1m`: 100,349 dòng
- **Tổng 827,422 dòng** (×5.84 corpus gốc)

**Kết quả train MLlib trên 969,147 dòng:**

| Quy mô | Tổng thời gian | s/100k dòng |
|---|---:|---:|
| 141k (giai đoạn 4) | 228.08s | 208.2 |
| **969k** | **550.4s** | **56.79** |

⇒ Chi phí mỗi 100k dòng **giảm 3.7×** khi scale.
Đây là câu trả lời định lượng cho "Spark thắng ở quy mô nào".

⚠️ **Bài học phát hiện được:** 9/12 shard bị tải **CẮT DỞ** — có header `PAR1`
nhưng footer hỏng. Script cũ dùng `curl -C -` + `--max-time`, timeout giữ lại
file dở và lần sau coi như "đã tải xong" → **file hỏng không bị phát hiện**.

⇒ Phải **verify magic bytes đầu + cuối**. Coi "file tồn tại" là "file đúng" là
lỗi âm thầm đắt nhất — nó làm hỏng mọi phép đo phía sau mà không báo lỗi.

---

## Slide 12 — 🔴 LOSO — zero-shot thật

**10 fold** · train trên 9 nguồn, test trên nguồn bị loại · 141,725 dòng

| Chỉ số (8 nguồn có attack) | Giá trị |
|---|---:|
| **Mean AUC** | **0.7511** |
| Mean F1 @ threshold 0.5 | 0.4198 |
| **Mean F1 @ threshold tối ưu** | **0.7617** |
| Min F1 (`S-Labs/prompt-injection-dataset`) | 0.0038 |
| Max F1 (`allenai/wildjailbreak`) | 0.9488 |

> 2 nguồn còn lại (`allenai/WildChat-1M`, `lmsys/lmsys-chat-1m`) **chỉ có
> benign** → không có mẫu positive để dò, F1 = 0 và AUC = 0.5 là hiện tượng
> toán học, **không tính vào mean**.

**Bảng chi tiết 10 fold** (`Metrics.md` mục 14):

**Phát hiện quan trọng:** AUC cao (0.7511) nhưng F1@0.5 thấp (0.4198)
→ model **vẫn phân biệt được**, chỉ là **ngưỡng quyết định không di chuyển theo
phân bố dữ liệu**. Sửa threshold → F1 nhảy lên **0.7617**.

⇒ Bài học: so sánh ngoài phân bố phải dùng **AUC**; triển khai thật phải
**calibrate threshold** trên tập validation đa nguồn.

**Nguồn khó nhất:** `deepset/prompt-injections` (AUC 0.5725, F1 0.0038)
và `guychuk/open-prompt-injection` (AUC 0.6230, F1 0.0749) — ở đây **ngưỡng không
phải nguyên nhân chính** (AUC gần ngẫu nhiên). Trùng với per-source in-sample
(mục 3.4) → 2 phép đo độc lập, 1 kết luận: **model học template, không học cơ chế**.

Ngoại lệ: `S-Labs` AUC 0.8084, F1@0.05 = 0.7205 → model **hoàn toàn phân biệt
được** S-Labs, chỉ là điểm hoạt động nằm ở 0.05 thay vì 0.5.

---

## Slide 13 — Prototype: Streamlit + MongoDB

**1 process, không tách frontend/backend** — Streamlit đã gộp server+client
→ không cần FastAPI/Flask.

5 tab: Tổng quan · Tra cứu ($regex) · Phân bố độ dài · Benchmark scale · Dữ liệu thô

✅ Smoke test (`AppTest`): 0 exception · metric **141,725 / 88,655 / 53,070 / 37.45%**
→ khớp Spark SQL 100%, và đọc **trực tiếp từ MongoDB** (kiểm chéo độc lập)

---

## Slide 13b — 🟡 Detector streaming (rule + model)

**2 tầng, cùng một pipeline Spark:**

| Tầng | Cơ chế | Vai trò |
|---|---|---|
| **Rule** | 8 regex theo kỹ thuật tấn công, chạy bằng Spark SQL `rlike` | Bắt mẫu công khai, **giải thích được** (kèm kỹ thuật + đoạn text khớp) |
| **Model** | MLlib LR đã train | Bắt mẫu biến thiên, không giải thích được → bổ sung recall |

8 kỹ thuật: `override_instruction` · `role_reassignment` · `system_prompt_leak` ·
`guardrail_bypass` · `dan_injection` · `encoding_evasion` · `urgency_emotional` ·
`exfil_secret`

**Kết quả replay (12 dòng tự viết tay):**

| Chỉ số | Giá trị |
|---|---:|
| Attack phát hiện (rule) | **7 / 7 (recall 100%)** |
| Benign bị bắt nhầm (rule + model) | **0 / 5 (FPR 0%)** |
| Model layer flag attack | 4 / 7 (train 30k dòng) |
| Số lần kỹ thuật được ghi nhận | 13 |
| Ghi vào MongoDB | 12 doc (`prompt_injection.detections`) |

**Vì sao rule layer dùng Spark SQL native, không dùng Python UDF:** `addPyFile()`
trên Windows cần `HADOOP_HOME` (winutils.exe) → lỗi. `rlike`/`regexp_extract`
chạy thẳng trong JVM, không ship file, và **chạy được cả ở cluster mode**.

*(Ngược lại: cột `probability` của MLlib là VectorUDT — SQL không trích được,
phải dùng Python UDF. Nên model layer chỉ dùng được ở local mode, còn rule layer
thì portable.)*

---

## Slide 13c — Môi trường tái lập: cái gì tin được, cái gì không

**Ghim version (đã làm, `requirements.txt` pin toàn bộ 21 package):**

| Nhóm | Version |
|---|---|
| Runtime | Python **3.14.5** · Java **24.0.2** |
| Core | `pandas 3.0.3` · `numpy 2.5.1` · `scikit-learn 1.9.0` · `pyarrow 26.0.0` |
| Big Data | `pyspark 4.2.0` |
| NoSQL / App | `pymongo 4.19.0` · `streamlit 1.66.0` |

**Số liệu nào tái lập được:**

| Loại | Tái lập? | Lý do |
|---|---|---|
| F1 / AUC / P / R / FPR (sklearn) | ✅ **Có** | `random_state=42` + `liblinear` deterministic |
| Số dòng corpus (141,725 …) | ✅ **Có** | dedupe hash + split seed cố định |
| F1 / AUC của MLlib | ⚠️ **Gần đúng** | lệch chữ số 4 do thứ tự aggregation phụ thuộc số core |
| Thời gian (s/100k, docs/s) | ❌ **Không** | phụ thuộc CPU/RAM/ổ — **số của một máy** |

**Phân biệt hai khái niệm dễ nhầm:**

- **Ghim version** → cùng thư viện → **hành vi code** giống nhau → F1/AUC phải khớp.
- **Cùng nền tảng** (Colab / VM / local) → **số giây** so sánh được.

⇒ Chạy lại trên Colab: **F1 0.9521 phải ra đúng**, còn 56.79s/100k **sẽ khác**.
Lệch F1 = lỗi version. Lệch giây = khác máy. **Đừng gộp hai nguyên nhân.**

**Vì sao chọn local, không Colab:** đề cương bắt buộc **MongoDB + R native**
(Colab không có service MongoDB), và benchmark 969k dòng cần `--driver-memory 10g`
(Colab free OOM). Báo cáo xử lý bằng cách **luôn ghi kèm cấu hình máy** —
chi tiết ở `Environment.md` do `tools/capture_env.py` sinh tự động.

---

## Slide 14 — Đóng góp của đồ án

| Yêu cầu đề cương | Hiện thực | Bằng chứng |
|---|---|---|
| Connect & query by PySpark | ✅ | 5 phân bố khớp pandas 100% |
| Database with MongoDB | ✅ | 141,725 doc, 6,917 docs/s |
| Statistical with R Language | ✅ | p = 0, AUC 0.8032, 5 biểu đồ |
| Build prototype & repair data | ✅ | Streamlit 5 tab, 0 exception |
| Source code & evaluation | ✅ | LOSO 10 fold (AUC 0.7511) + ablation + per-source |
| Experiments & results | ✅ | 141,725 dòng LOSO + 827k dòng benchmark |
| Document + source code | ✅ | 3 chương + 40 file Python |

---

## Slide 15 — Hạn chế & hướng mở rộng

**Hạn chế đã đo được:**

| Hạn chế | Bằng chứng | Hướng |
|---|---|---|
| Học template, không học cơ chế | S-Labs: 0.2386 vs 0.8624 | char n-gram + embedding |
| toxic-chat yếu | F1 0.5114, P 0.4206 | đặc trưng imperative + override verb |
| Spark chậm hơn pandas 30× | 80.67s vs 2.69s | đo ở ~1M dòng (đã làm) |
| per-source là in-train | cả 10 nguồn trong train | **LOSO (đã làm)** → AUC 0.7511 |
| threshold không portable | F1@0.5 0.4198 vs F1@thr tốt 0.7617 | calibrate threshold trên validation đa nguồn |

**Hướng mở rộng:** Sentence-BERT/embedding · đa nhãn (adversarial-but-harmless ≠
injection) · **streaming detection (`stream_detector.py` — đã làm)** · chi phí
cluster (YARN/K8s)

---

## Slide 16 — Kết luận

1. **Đo trung thực quan trọng hơn con số đẹp** — "Spark chậm hơn pandas 30×" và
   "FPR = 1.0 do nhãn sai" đều là kết quả đáng trình bày.
2. **Ba ca nhãn sai đáng giá hơn 100K dòng dữ liệu thêm** — loại HackAPrompt
   mất 227K dòng nhưng tránh học sai bài toán.
3. **Model học template, không học cơ chế** — bằng chứng mạnh nhất từ S-Labs.
4. **Kiến trúc 2 đường** (parquet↔Spark cho batch, MongoDB cho operational)
   là câu trả lời cho bài toán đa yêu cầu của đề cương.

---

## Phụ lục — Slide dự phòng

### A. Top feature: model học template

*(trích từ `Metrics.md` mục 6 — top feature theo hướng attack/benign)*

### B. MongoDB schema + 5 index

```
label_1_source_1   source_1_split_1   family_1_label_1   text_len_1   pair_id_1
```

### C. R's gotcha đã sửa

AUC viết tay bằng rank-sum cho **0.3675 — sai**. Công thức đúng `1 − W/maxU` →
**0.8032**, verify lại bằng **pROC** (package độc lập).

⇒ Số "trông hợp lý" vẫn có thể sai. Phải kiểm chứng bằng công cụ độc lập.
