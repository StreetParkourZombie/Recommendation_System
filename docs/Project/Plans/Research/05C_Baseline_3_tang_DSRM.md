# 05C — Ba tầng baseline (yêu cầu Bài 03 PPNCKH) + khả năng tái lập

- Cả 3 nhóm phải **so sánh công bằng**: cùng dữ liệu, cùng split, cùng ngân sách tinh chỉnh và cùng hardware profile.
- **Seed phải truy xuất được**: dùng seed cụ thể từ paper/repository khi tuyên bố tái lập bài báo; nếu bài chỉ nói nhiều lần chạy mà không công bố số seed, ghi rõ `seed value not reported`.
- Project dùng **1 seed cố định (42)** — giới hạn đã khai báo trong đề cương và slide 14; ma trận nhiều seed là mở rộng, không chạy. Đây là protocol của project, không mặc định là seed của bài báo.
---

## 1. Ba tầng baseline đề xuất

| Tầng | Mô hình | Nguồn code | Có trong bài tham khảo nào | Tái lập trên máy anh | Tái lập trên Colab |
|---|---|---|---|---|---|
| **Sàn (truyền thống)** | **MostPopular** + **Random** | PySpark 4.2.0 `pyspark.ml.recommendation` (không cần cài thêm) | Không bài nào code riêng — nhưng [A] TOIS 2023 và [C] RecSys'25 đều dùng làm mốc so sánh | ✅ KHÔNG cần tải gì | ✅ |
| **Kinh điển** | **ItemKNN (cosine)** và **ALS (matrix factorization)** | `pyspark.ml.recommendation.ALS` + ItemKNN tự viết bằng RDD (`cartesian` + `topByKey`) | [12] RecSys'20 dùng **BPR + NMF** (cùng họ MF) · [13] dùng **FP-growth / association rules** | ✅ đã chạy 04/11 (ALS rank 16, maxIter 8, regParam 0.05) | ✅ |
| **SOTA (≤2 năm)** | **SASRec + cross-entropy** (softmax toàn catalog) — đã triển khai `src/audit/sasrec.py` + notebook 13, **GPU local RTX 4050 6 GB** | `github.com/pmixer/SASRec.pytorch` (repo gốc dùng BCEWithLogitsLoss 1-negative → bản này đổi sang CE, khai báo rõ) · `github.com/antklen/sasrec-bert4rec-recsys23` | [3] RecSys'25 — baseline chính thức, có repo riêng `github.com/monkey0head/time-to-split` | ⚠️ CPU chạy được nhưng chậm (ml-25m: ước tính 6-10h/lần) | ⚠️ cần GPU runtime T4 |

---

## 2. Bằng chứng tái lập — trích từ chính các bài Q1/CORE A

### [3] RecSys'25 Time to Split (CORE A) — nguồn SOTA chuẩn nhất

Trích nguyên văn:

> *"We conduct our experiments using three popular sequential recommender system baselines: **SASRec+** [30], an adaptation of the original PyTorch implementation that employs full cross-entropy loss (CE) over the entire item catalog; **BERT4Rec** [56], an efficient implementation using the Transformers library; and **GRU4Rec** [24] implementation with full CE loss."*

> *"We compute metrics using **RePlay framework**: https://github.com/sb-ai-lab/RePlay"*

> *"4https://github.com/pmixer/SASRec.pytorch   5https://github.com/antklen/sasrec-bert4rec-recsys23"*

> *"All experiments are conducted on NVIDIA H100 GPUs with 80GB HBM3 memory."*

Chú thích footnote 1: `https://github.com/monkey0head/time-to-split` — **toàn bộ code + 8 dataset của bài này đều công khai**.

**Siêu tham số họ công bố đầy đủ** (dùng để mình đối chuẩn cùng ngân sách):

| Tham số | Giá trị |
|---|---|
| hidden size | 32 – 256 |
| self-attention blocks | 1 – 3 |
| attention heads | 1 – 4 |
| masking prob (BERT4Rec) | 0.2 |
| GRU hidden size | 16 – 512 |
| GRU layers | 1 – 4 |
| dropout | 0.1 – 0.5 |
| batch size | 256 |
| max sequence length | 128 |
| optimizer | Adam, lr = 1e-3 |
| max epochs | 300 |
| early stopping patience | SASRec+/GRU4Rec = 10, BERT4Rec = 20 |

→ Đây là thứ thầy muốn: **cùng ngân sách tinh chỉnh**, không phải "baseline chạy default còn mình tinh chỉnh 30 lần".

### [12] RecSys'20 Data Splitting (CORE A) — nguồn kinh điển chuẩn nhất

> *"First, we include two classical models (i.e. **NMF** [8] and **BPR** [15]). Second, we select three state-of-the-art neural item recommendation models (**NeuMF** [5], **VAECF** [10] and **NGCF** [26]). Finally, we include two state-of-the-art neural grocery recommendation models (**Triple2vec** [24] and **VBCAR** [12]). **All models support all splitting strategies.**"*

> *"5The data splits used in this work can be downloaded from https://github.com/mengzaiqiao/data_splits. 6https://github.com/beta-team/beta-recsys"*

→ **Quan trọng nhất:** họ phát hành **file split sẵn**. Mình tải về, dùng đúng phép chia của họ → so sánh **cùng dữ liệu, cùng tiền xử lý** đúng tiêu chí (4).

### [1] TOIS 2023 Data Leakage (Q1) — nguồn rò rỉ

> *"Our codes and datasets are available online https://github.com/putatu/dataLeakageRec"*

> *"we repeat seven random trials with different seeds"*

→ Bài báo có **7 lần lặp với seed khác nhau**, nhưng bản PDF không công bố danh sách giá trị seed. Đây là bằng chứng cho việc báo cáo nhiều lần chạy; không đủ để khẳng định seed cụ thể dùng trong reproduction. Project dùng 10 seed cố định như protocol kiểm soát riêng.
---

## 3. Vì sao KHÔNG dùng [13] và [14] làm baseline

| # | Lý do | Bằng chứng |
|---|---|---|
| [13] J.BigData 2019 | **Dataset private, không public** | *"we have used an operational database of ESTenLigne platform ... This database contains 1218 learners ... 153 courses"* — DB Moodle nội bộ trường Fez, không có link tải |
| [13] | **Thuật toán khác lớp** (association rules, không phải rating prediction) | Dùng FP-growth / PFP, không tối ưu NDCG |
| [13] | **Không có repo, không nêu seed** | grep `github` = chỉ có code Scala trong bài, không link |
| [14] ESWA 2023 | **Dataset chính private** (Aptoide, 74.209 user) | *"We extracted the dataset we employed ... from Aptoide's big data lake running on Amazon Web Services (AWS)"* |
| [14] | **Không có repo** | Dùng code SOTA của Han 2021 / SASRec, không tự phát hành |
| [14] | **Spark chỉ để đo latency serving**, không train | *"A Spark script was executed directly on the PySpark command-line tool, which imports the TensorFlow graph from the local disk before applying it to each row of an RDD"* |

→ Cả hai chỉ dùng để chứng minh **lớp kiến trúc đã được publish**, không phải mốc so sánh số.

---

## 4. Ba tầng baseline — cụ thể trên MovieLens ml-25m

### Tầng 1 — Sàn (truyền thống), không cần code ngoài

| Mô hình | Định nghĩa | Tham số | Nguồn |
|---|---|---|---|
| **Random** | Gợi ý 10 item ngẫu nhiên từ catalog | seed = 42 | tự viết 5 dòng |
| **MostPopular** | Gợi ý 10 item có nhiều rating nhất trong train | đếm bằng MapReduce Java (đã chạy 04/11: 323.737 key) | `pyspark` hoặc MapReduce đã có |

→ **Đây là "mốc sàn" thầy yêu cầu.** Không mô hình nào được phép thua MostPopular; nếu thua là code sai.

### Tầng 2 — Kinh điển

| Mô hình | Tham số | Nguồn code | Đã chạy? |
|---|---|---|---|
| **ALS (MF)** | rank 16, maxIter 8, regParam 0.05, alpha 10, seed 42, implicit | `pyspark.ml.recommendation.ALS` | ✅ 04/11 — NDCG@10 = 0.2584 / 0.1364 / 0.0474 cho 3 split |
| **ItemKNN (cosine)** | k = 100 láng giềng, min_co = 2 | `src/audit/itemknn.py` — `scipy.sparse` co-count → cosine (bản RDD `cartesian`/self-join timeout 3600 s) | ✅ run `20261118_150305_..._0b7511ee`, 503 s, NDCG@10 0,2679 / 0,1409 / 0,0461 |

→ (Tham khảo, **không áp dụng**): [12] dùng BPR cho tầng kinh điển, nhưng danh sách baseline đã đăng kí của đề tài chỉ gồm ALS + ItemKNN → không chạy BPR.

### Tầng 3 — SOTA (≤ 2 năm, ACM)

| Mô hình | Venue | Nguồn code | Phần cứng |
|---|---|---|---|
| **SASRec+ (full CE)** | RecSys'25 baseline chính thức | `github.com/pmixer/SASRec.pytorch` (PyTorch) | CPU được / GPU tốt hơn |
| **BERT4Rec** | RecSys'25 baseline | `github.com/antklen/sasrec-bert4rec-recsys23` (Transformers) | CPU rất chậm → cần GPU |

**Ngân sách tinh chỉnh** (bắt chước đúng [3]): hidden 32-256, blocks 1-3, heads 1-4, dropout 0.1-0.5, batch 256, seq_len 128, Adam lr 1e-3, max 300 epoch, early stop patience 10.

**Nếu không đủ GPU (khuyến nghị của tài liệu tham khảo, KHÔNG áp dụng cho đề tài này):** [11] RecSys'21 dùng EASE — chính là mô hình mà bài đó dùng để tính metric. Trích nguyên văn:

> *"To calculate metrics, we used the **MovieLens-20m** dataset and **EASE recommender** [30] to get predictions, as it is an easy model that produces a **closed-form solution** for a given regularization term. Ratings less than 4.5 were treated as negative and were removed. The **global timestamp split** was used so that 20% of the latest ratings were in the test set."*

→ EASE chạy CPU vài phút, có công thức đóng, **và [11] dùng đúng global timestamp split như mình**. **Quyết định của đề tài: không dùng EASE** vì không có trong danh sách baseline đã đăng kí (`docs/About/Reseach_Method_Submission.md`); chỉ dùng làm **tham chiếu văn bản** khi đối chuẩn protocol. Nếu thiếu GPU → khai báo tầng SOTA đã reproduce 3 split trên GPU local (không tuning).

---

## 5. Bảng khai báo bắt buộc trong Chương 3 (đúng 3 dòng thầy yêu cầu)

| Trường | Mẫu khai (điền số thật) |
|---|---|
| **Mã nguồn** | `commit hash` của repo mình + link 3 repo baseline |
| **Seed** | `paper_replication`: seed cụ thể từ repo/paper, nếu có; `project_controlled_comparison`: `[42, 2024, 7, 1337, 2025, 11, 88, 99, 314, 2718]` |
| **CPU/GPU/RAM** | ví dụ: `Intel Core i5-XXXX, 16 GB RAM, no GPU, Spark 4.2.0 local[*], Java 17` |
| **Thời gian chạy** | wall-clock mỗi mô hình × mỗi split, ghi bằng `time.perf_counter()` |
| **Ngân sách tinh chỉnh** | số cấu hình thử cho **mỗi mô hình, gồm baseline** (vd 30) |

**Quy tắc ghi nhãn kết quả:**
- `paper_replication`: dùng đúng split/preprocessing/seed/config được bài báo hoặc repository công bố; thiếu seed thì ghi `not reported`, không tự đặt giá trị rồi gọi là tái lập nguyên văn.
- `project_controlled_comparison`: mọi mô hình dùng chung **seed 42**, 3 split, cùng ngân sách và hardware profile của project; vì chỉ 1 seed nên báo per-split + **kiểm định cặp per-user** (Wilcoxon, 95% CI, r) thay vì Mean ± Std.
---

## 6. Việc phải làm để có đủ 3 tầng trước khi nộp

1. **ItemKNN** — ✅ đã xong: `src/audit/itemknn.py` (scipy sparse cosine, k=100, min_co=2) + notebook 11; 503 s cho 3 split, FULL 162.541 user (run `20261118_150305_11_itemknn_baseline_0b7511ee`). Bản RDD `cartesian`+`topByKey` và bản Spark self-join đều **không dùng được** (self-join timeout 3600 s).
2. **Tải split của [12]** — `github.com/mengzaiqiao/data_splits` → dùng đúng phép chia để so sánh cùng dữ liệu.
3. **SASRec+CE** — chạy 1 cấu hình làm điểm SOTA trên **GPU local** (RTX 4050 Laptop 6 GB, CUDA 12.6): `src/audit/sasrec.py` + notebook 13, cross-entropy softmax toàn catalog. **Không cần Colab.** Không thay bằng EASE (không đăng kí). Đã chạy xong 3 split → khai báo giới hạn "đã reproduce 3 split trên GPU local (không tuning)".
4. **Script đo phần cứng** — `scripts/18_hardware_log.py` ghi `nproc`, `free -h`, `lscpu`, `java -version`, `spark.version` → `logs/hardware.txt`.
5. ~~Chạy 10 seed~~ **KHÔNG chạy** (giới hạn 1 seed đã khai báo) → thay bằng: 5 model × 3 split × seed 42 + 20 cặp kiểm định per-user → bảng đối chuẩn kèm cột chi phí vận hành (`Implementation/05_Benchmark_Chi_Phi_Van_Hanh_RQ3.md`).

---

## 7. Đóng góp so với baseline — phải nêu rõ trước hội đồng

Ba tầng baseline ở trên là **mốc đối chuẩn**, không phải đóng góp. Đóng góp của đề tài
được đóng gói thành **ba tạo tác** (chi tiết `08_Tao_tac_SLI_va_giao_thuc_audit.md`):

| # | Dạng tạo tác (Bài 03 tr.52) | Nội dung | Bằng chứng |
|---|---|---|---|
| 1 | **Concepts + Models** | **Split Leakage Index (SLI)** — rò rỉ đo **tương đối theo user**, 3 ngưỡng | LOO: toàn cục 99,9988% vs tương đối 0% |
| 2 | **Methods** | **Giao thức audit 3 bước** — SLI trước metric, `eval_rel_users` song song, chặn so sánh khi lệch >20% | 3/3 cặp split bị chặn (25,5× / 1,65× / 15,4×) |
| 3 | **Instantiations** | Pipeline HDFS + MapReduce Java + PySpark + MongoDB + R + Streamlit | 323.737 key, G3 PASS 100% |

**Đạt yêu cầu Bài 03 tr.52** — *"Đóng góp ít nhất dạng 2 và 3"*.

**Điền SO2 (40% tỷ trọng, hiện đang trống):**
> SO2 (Model) — **Đề xuất SLI (tương đối theo user, 3 ngưỡng) và giao thức audit 3 bước**.
> Nghiệm thu: SLI tính được cho cả 3 split; chênh lệch LOO 99,9988% vs 0%.

**Câu nói với hội đồng:**
> "Baseline của em là ba tầng đối chuẩn. Đóng góp của em không phải mô hình mới, mà là
> **một chỉ số đo mới (SLI) và một giao thức đánh giá mới**. Bằng chứng: cùng một split
> leave-one-out, cách đo toàn cục nói rò rỉ 99,9988% còn cách đo tương đối nói 0% —
> cách đo hiện hành đang cho kết luận ngược."
