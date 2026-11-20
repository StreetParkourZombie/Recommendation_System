# 05 — Benchmark chi phí vận hành (RQ3)

> Tổng hợp **từ các artifact đã có sẵn** (`runs/<run_id>/outputs/*_summary.json` + `manifest.json`). Không chạy lại notebook nào. Mọi số lấy nguyên văn từ JSON, chỉ đổi cách trình bày sang quy ước Việt (dấu `,` cho thập phân, `.` cho hàng nghìn).
>
> RQ3 (xem [`04_Research_Questions_Gaps_and_Action_Map.md`](04_Research_Questions_Gaps_and_Action_Map.md#L103)): *"Mỗi split và pipeline có runtime, memory, I/O và task cost thế nào trên Spark local/Colab simulation?"* → **phần runtime đã có số; phần memory / I/O / task chưa đo** (mục 4).

## 1. Điều kiện đo (chung cho mọi run)

| Hạng mục | Giá trị | Nguồn |
|---|---|---|
| Spark | 4.2.0 | checkpoint `spark_ready` trong `manifest.json` từng run |
| master | `local[4]` | `src/audit/spark_utils.py` (`get_spark`, mặc định) |
| driver memory | `6g` (ALS / Random / MostPopular) — `10g` (ItemKNN, truyền tham số riêng) | `spark_utils.py` mặc định; `11_itemknn_baseline.ipynb` CELL001 |
| CPU máy | 16 logical processor | `[Environment]::ProcessorCount` = 16 |
| protocol | `project_protocol_v1`, seed 42, `rating ≥ 4,0`, K=10 | `manifest.json` metadata từng run |
| fit scope | FULL 162.541 user (không subsample) | `fit_scope` trong summary ALS / Random |

## 2. Bảng runtime per model × per split

| model | split | ndcg@10 | fit (giây) | total (giây) | train rows | eval users | ghi chú |
|---|---|---:|---:|---:|---:|---:|---|
| ALS_implicit | `random80_20` | 0,2581 | 37,4 | 107,1 | 19.997.974 | 158.626 | seed 42, driver_memory 6g, Spark local[4], 16 logical CPU; `seen_exclusion` PASS |
| ALS_implicit | `temporal_global` | 0,1332 | 43,2 | 79,2 | 19.999.279 | 6.214 | như trên; fit chậm nhất trong 3 split dù eval chỉ 6.214 user |
| ALS_implicit | `leave_one_out` | 0,0469 | 38,4 | 100,4 | 24.837.554 | 95.977 | như trên; train rows lớn nhất (24,8M) |
| Random | `random80_20` | 0,0003 | 0,0 | 57,1 | 19.997.974 | 158.692 | không có bước fit → `fit_seconds = 0`; `seen_exclusion` PASS |
| Random | `temporal_global` | 0,0009 | 0,0 | 18,4 | 19.999.279 | 6.219 | như trên |
| Random | `leave_one_out` | 0,0001 | 0,0 | 35,6 | 24.837.554 | 96.003 | như trên |
| MostPopular | `random80_20` | 0,0852 | — | 9,3 * | — | 158.692 | seed 42, driver_memory 6g, Spark local[4]; chỉ có `elapsed_seconds` (xem mục 3) |
| MostPopular | `temporal_global` | 0,0455 | — | 2,4 * | — | 6.219 | như trên |
| MostPopular | `leave_one_out` | 0,0183 | — | 3,6 * | — | 96.003 | như trên |
| ItemKNN_cosine | `random80_20` | 0,2679 | 66,8 | 221,0 | 19.997.974 | 158.692 | k=100 cosine, seed 42, `driver_memory=10g`, scipy sparse chạy trên driver; `seen_exclusion` PASS |
| ItemKNN_cosine | `temporal_global` | 0,1409 | 58,5 | 94,2 | 19.999.279 | 6.219 | như trên |
| ItemKNN_cosine | `leave_one_out` | 0,0461 | 83,2 | 184,5 | 24.837.554 | 96.003 | như trên; fit lớn nhất trong 3 split của ItemKNN |

\* MostPopular: field trong JSON là `elapsed_seconds`, **không phải** `total_seconds`, và không tách fit/eval.

Nguồn run id:

| Model | Run id | File số |
|---|---|---|
| ALS_implicit | `20261117_234312_08_als_implicit_da15debf` | `outputs/als_summary.json` |
| Random | `20261118_144717_10_random_baseline_d8644ac1` | `outputs/random_summary.json` |
| MostPopular | `20261118_021147_06_mostpopular_baseline_6d59bb2c` | `outputs/mostpopular_summary.json` |
| ItemKNN | `20261118_150305_11_itemknn_baseline_0b7511ee` | `outputs/itemknn_summary.json` (+ 3 `itemknn_<split>.json`, 3 npz per-user) |
| Ghép đối chiếu (5 model) | `20261118_151159_09_compare_and_reversal_1e0f72fa` | `outputs/comparison.json` (bản 3 model cũ: `20261118_004106_..._e9779077`) |
| Kiểm định cặp (20 cặp) | `20261118_151202_12_paired_stats_9b864f59` | `outputs/paired_stats.json` (bản 6 cặp cũ: `20261118_021517_..._f77a212b`) |

## 3. Field phụ (test rows, positive train rows, gate)

| model | split | test rows | positive_train_rows | seen_exclusion |
|---|---|---:|---:|---|
| ALS_implicit | `random80_20` | 5.002.121 | 9.960.940 | PASS |
| ALS_implicit | `temporal_global` | 5.000.816 | 9.980.888 | PASS |
| ALS_implicit | `leave_one_out` | 162.541 | 12.356.808 | PASS |
| Random | `random80_20` | 5.002.121 | — | PASS |
| Random | `temporal_global` | 5.000.816 | — | PASS |
| Random | `leave_one_out` | 162.541 | — | PASS |
| MostPopular | `random80_20` | — | — | — (có `relevant_test_items` = 2.491.871; không ghi `seen_exclusion`) |
| MostPopular | `temporal_global` | — | — | — (có `relevant_test_items` = 290.588) |
| MostPopular | `leave_one_out` | — | — | — (có `relevant_test_items` = 96.003) |
| ItemKNN | `random80_20` | 5.002.121 | 9.960.940 | PASS |
| ItemKNN | `temporal_global` | 5.000.816 | 9.980.888 | PASS |
| ItemKNN | `leave_one_out` | 162.541 | 12.356.808 | PASS |

## 4. Thiếu / cần đo thêm

**Field thiếu trong JSON (không suy đoán số):**

| Model | Field thiếu | Ghi chú |
|---|---|---|
| MostPopular | `fit_seconds`, `total_seconds`, `train_rows`, `test_rows`, `positive_train_rows`, `seen_exclusion` | notebook 06 chỉ ghi `elapsed_seconds` + `relevant_test_items`. `elapsed_seconds` 3 split cộng lại = 15,3 s, khớp thời gian CELL003 trong `manifest.json` (15,305 s) → đây là **thời gian đánh giá**, không phải toàn pipeline. |
| Random | `positive_train_rows` | có `fit_seconds`, `total_seconds`, `train_rows`, `test_rows`, `seen_exclusion` |
| ItemKNN | `mrr_at_k` | đã có `fit_seconds`/`total_seconds`/`train_rows`/`test_rows`/`positive_train_rows`/`seen_exclusion` + đủ bộ bias; chỉ chưa có MRR (giống 3 model kia) |
| Mọi model | **memory (RSS / peak driver heap)**, `numTasks`, `shuffle bytes`, `I/O bytes` | pipeline không instrument — xem dưới |

**Memory chưa đo được.** Lý do: không notebook nào ghi RSS/peak heap vào summary; `get_spark()` chỉ set `spark.driver.memory` (6g / 10g) — đó là **cấu hình cấp phát**, không phải mức dùng thật. Nên **không** được trích 6g/10g vào cột "memory" của bảng đối chuẩn như một kết quả đo.

Cách đo rẻ, đề xuất (**chưa triển khai** — cần duyệt trước khi sửa pipeline):

1. **Metrics qua Spark**: sau mỗi lần fit/eval, đọc `spark.sparkContext().getConf()` + `statusTracker()` để lấy `numTasks`, `shuffleReadBytes`, `memoryBytesSpilled` per stage — vài dòng, không chạy lại model, chỉ bật ở run kế tiếp.
2. **Peak heap JVM**: `java.lang.management.ManagementFactory.getMemoryMXBean()` / `MemoryPoolMXBean("Heap")` lấy `used` + `max`, ghi thêm field `driver_peak_heap_mb` vào summary, đo tại 3–4 checkpoint (sau fit, sau top-K) — chi phí gần 0.
3. **RSS tiến trình**: `psutil.Process(os.getpid()).memory_info().rss` (kèm `peak_wset` qua `ctypes` trên Windows) lấy mỗi 5–10 s trong lúc cell chạy → field `driver_peak_rss_mb`.
4. **Executor memory**: trên `local[*]` executor nằm trong cùng JVM driver → RSS driver là xấp xỉ tổng; phải ghi rõ giới hạn này trong chú thích bảng, không trình bày như cluster multi-node.
5. **ItemKNN (đã làm xong)**: run `20261118_150305_11_itemknn_baseline_0b7511ee` hoàn tất sau 503 s (CELL002), `fit_seconds`/`total_seconds` lấy nguyên văn từ `itemknn_summary.json`. Lưu ý phương pháp: phần dựng ma trận đồng xuất hiện + top-K chạy `scipy.sparse` trên **driver** (`toPandas` ~20 triệu cặp) → chi phí này là **driver-bound**, không so sánh trực tiếp được với ALS trong môi trường phân tán thật. Khai báo giới hạn: `docs/Project/Main/Drawbacks.md` §3.5.

**Cần đo thêm cho đủ RQ3:** I/O bytes (đọc `data/processed/` + parquet splits), số task Spark per stage, thời gian cold-start (`get_spark` 6,8–8,1 s/cell theo `manifest.json`) — hiện chưa có field nào.

## 5. Nhận xét so sánh chi phí

1. **ItemKNN mới là model đắt nhất đã đo, không phải ALS**: tổng 3 split `total_seconds` = 221,0 + 94,2 + 184,5 = **499,7 s**, gấp **1,74×** ALS (107,1 + 79,2 + 100,4 = **286,7 s**, khớp CELL003 trong `manifest.json` 286,773 s). Tổng fit ItemKNN = 66,8 + 58,5 + 83,2 = **208,5 s** (42% pipeline) so với 119,0 s (41%) của ALS → tỉ lệ fit/eval gần nhau, chỉ khác độ lớn. Cả hai cặp số đều truy vết được từ summary + manifest.
2. **Fit chỉ chiếm chưa tới 1/3 chi phí ALS**: 37,4 + 43,2 + 38,4 = **119,0 s** fit, còn lại **167,7 s** là top-K + đánh giá. Nói "ALS đắt vì ALS" là chưa đủ — phải nói đắt ở khâu inference/eval. Với ItemKNN, fit chiếm tỉ trọng lớn hơn (208,5/499,7 = 42%) vì dựng ma trận đồng xuất hiện và tra k láng giềng đều là thao tác trên sparse matrix của toàn catalog.
3. **Random: `fit_seconds = 0` nhưng không rẻ**: tổng 3 split = **111,1 s** (CELL002 = 113,714 s). Chi phí nằm ở sinh 10 item/user và loại item đã thấy trên 162.541 user — bằng khoảng **39%** chi phí ALS dù không học gì. Sàn "rẻ" chỉ đúng về fit, không đúng về runtime.
4. **MostPopular rẻ nhất rõ rệt**: 15,3 s cho cả 3 split (≈ **5%** ALS, **14%** Random), vì chỉ cần một bảng đếm phổ biến và top-10 chung cho mọi user. Cặp đánh đổi cần nêu: rẻ nhất về compute, tệ nhất về độ phủ (catalog_coverage 0,00017–0,00029).
5. **Chi phí không tỷ lệ với số eval user**: `temporal_global` chỉ có 6.214 user eval (bằng 4% `random80_20`) nhưng ALS fit **43,2 s** — chậm nhất trong 3 split. Runtime chủ yếu theo **train_rows** (20,0M ở cả hai split), không theo eval_users.
6. **`leave_one_out` có train rows lớn nhất** (24.837.554, hơn 24% so với hai split còn lại) nhưng fit 38,4 s — thấp hơn `temporal_global` (43,2 s với 20,0M rows), nên chi phí fit **không đơn điệu theo train_rows**. Khác biệt 4,8 s nằm trong biên độ dao động của `local[4]` trên máy 16 logical CPU có tiến trình khác chạy — không diễn giải quá xa.
7. **Chi phí phần thống kê gần bằng 0**: run 09 bản 5 model (`20261118_151159_..._1e0f72fa`) tổng **0,88 s** (cộng `duration_seconds` mọi cell trong `manifest.json`: 0,008+0,007+0,006+0,831+0,017+0,009+0,003), run 12 bản 20 cặp (`20261118_151202_..._9b864f59`) **0,48 s** (0,418 + 0,064) — chỉ đọc `.npz`/ JSON đã lưu. Wilcoxon + 95% CI + rank-biserial r cho 20 cặp (lớn nhất 158.692 user ghép) không đáng kể so với 107,1 s của một split ALS → **kiểm định cặp không thể lý do bỏ qua**.
   *(Bản cũ đo trước khi có ItemKNN: run 09 3 model = 1,05 s, run 12 6 cặp = 0,22 s — cùng kết luận.)*
8. **Đối chiếu với số hiệu quả** (không trộn bảng): ALS/sàn = 860,3× / 148,0× / 469,0×; ItemKNN/sàn = 893,0× / 156,6× / 461,0×; MostPopular/sàn = 284,0× / 50,6× / 183,0×; `reversals_found = 0` (so với sàn) nhưng `best_model_reversals_found = 2` (ngôi đầu đổi chỗ giữa ALS và ItemKNN ở 2/3 split). Wilcoxon 20/20 cặp đều `n_paired >= 30`; các cặp ALS-vs-Pop, ALS-vs-Random, ItemKNN-vs-Pop: CI 95% không chứa 0, `rank_biserial_r` 0,5172–0,9987; cặp ALS-vs-ItemKNN: p = 2,84e-60 / 3,01e-03 / 0,153 với |r| = 0,005–0,030 (gần như không). Bảng này mới cung cấp **cột runtime**, chưa phải bảng đối chuẩn đầy đủ (thiếu memory + SASRec).

9. **Chi phí cao hơn không mua được hiệu quả ổn định**: ItemKNN đắt hơn ALS 1,74× nhưng chỉ hơn ALS +0,0098 / +0,0077 NDCG@10 ở `random80_20` và `temporal_global`, kém hơn 0,0008 ở `leave_one_out`, và effect size |r| = 0,005–0,030. Nói được: *trong đề tài này, thêm chi phí tính toán không đi kèm khác biệt thực chất về chất lượng*.
10. **Điều kiện so sánh công bằng đã thoả (bài giảng 04)**: cùng dữ liệu (MovieLens-25M, `project_protocol_v1`), cùng 3 split, cùng K=10, cùng ngưỡng `rating >= 4,0`, cùng seed 42, cùng phần cứng (1 máy, 16 logical CPU, Spark `local[4]`), cùng code công khai trong repo. Khác biệt duy nhất cần nêu khi nói về ItemKNN: `driver_memory` 10 g vs 6 g và đường tính toán driver-side.

## 6. Việc còn lại để bảng đạt chuẩn IEEE/ACM (Bài 04)

- [x] Điền dòng ItemKNN — đã xong (run `20261118_150305_11_itemknn_baseline_0b7511ee`, `itemknn_summary.json`, 503 s).
- [ ] Thêm cột **memory** — cần instrument theo mục 4 (chưa làm, chưa tự ý triển khai).
- [ ] MostPopular: để cùng bộ cột với ALS/Random/ItemKNN, notebook 06 phải ghi thêm `fit_seconds`/`total_seconds`/`train_rows`/`test_rows`/`seen_exclusion` — chi phí chạy lại thấp (~15 s) nên đáng làm, **chờ duyệt**.
- [x] `mrr_at_k` đã có trong `src/audit/metrics.py` và đã đo ở cả 5 model (xem `Metrics.md` §4.10).
- [ ] Bảng slide 12: bold tốt nhất, underline nhì, `(*)` p<0,05 — lấy nguồn dấu sao từ `paired_stats.json` (run `20261118_151202_..._9b864f59`).
- [x] Cột `fit_seconds`/`total_seconds` cho 5 model trên slide 12 (footer chi phí RQ3: ALS 286,7 s, ItemKNN 499,7 s, Random 111,1 s, MostPopular 15,3 s).

---

## 7. Cập nhật 2026-11-20 — re-run 5 notebook để lấy Novelty/Diversity (Bài 04 Phần 3)

Re-run cả 5 notebook baseline để thêm `novelty10` / `diversity10` vào từng `*_summary.json` nên runtime đo lại toàn bộ. Cùng máy, cùng `local[4]`, cùng seed 42, cùng protocol. Chênh lệch so với bảng §2 là **dao động I/O + tải máy**, không phải thay đổi thuật toán.

| Split | Model | fit (giây) | total (giây) |
|---|---|---:|---:|
| `random80_20` | MostPopular | — | 10,5 * |
| `random80_20` | Random | 0,0 | 48,1 |
| `random80_20` | ALS | 38,7 | 103,7 |
| `random80_20` | ItemKNN | 61,5 | 203,1 |
| `random80_20` | SASRec+CE | 491,9 | 558,2 |
| `temporal_global` | MostPopular | — | 2,5 * |
| `temporal_global` | Random | 0,0 | 17,1 |
| `temporal_global` | ALS | 36,2 | 65,9 |
| `temporal_global` | ItemKNN | 55,0 | 88,0 |
| `temporal_global` | SASRec+CE | 304,6 | 332,1 |
| `leave_one_out` | MostPopular | — | 3,8 * |
| `leave_one_out` | Random | 0,0 | 34,2 |
| `leave_one_out` | ALS | 35,2 | 91,6 |
| `leave_one_out` | ItemKNN | 77,4 | 172,3 |
| `leave_one_out` | SASRec+CE | 524,4 | 564,1 |

\* MostPopular chỉ ghi `elapsed_seconds`.

Tổng 3 split theo đợt run này: ALS **261,2 s**, ItemKNN **463,4 s**, Random **99,4 s**, MostPopular **16,8 s**, SASRec+CE **1.454,4 s** (GPU, không so trực tiếp với 4 baseline CPU).

**Chi phí đo thêm của novelty/diversity: gần 0.** Chỉ cộng thêm `diversity_metrics` một lần mỗi split: đọc `movies.csv` (62.423 phim, cache module-level 0,23 s lần đầu) + 5.000 user × 45 cặp Jaccard. Không đáng kể so với 91,6–564,1 s của một split. `total_seconds` không tăng vì đã nằm trong cùng cell đánh giá.

**Cảnh báo đọc cột total:** SASRec+CE chạy **GPU RTX 4050 6 GB**, 4 baseline còn lại chạy **CPU** Spark `local[4]`. Không được kết luận "SASRec đắt hơn 5×" — khác phần cứng.

Run id đợt này: `20261120_004801_06_..._cde8a34b` (MostPopular), `20261120_012429_08_..._73a9947b` (ALS), `20261120_004945_10_..._dc453187` (Random), `20261120_005139_11_..._979f28e2` (ItemKNN), `20261120_005943_13_..._f31d7945` (SASRec), ghép đối chiếu `20261120_012944_09_..._21d0811a`. Chi tiết chỉ số: `Metrics.md` §4.12.
