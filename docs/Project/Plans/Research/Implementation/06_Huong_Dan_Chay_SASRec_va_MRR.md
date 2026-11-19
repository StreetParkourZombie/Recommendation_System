# 06 — Hướng dẫn chạy SASRec+CE (notebook 13) và MRR@10

> [!IMPORTANT]
> Tài liệu này dành để **bạn tự chạy**. Máy có GPU RTX 4050 Laptop 6 GB (xem `docs/About/Hardware_Resources.md`), nên SASRec — tầng SOTA đã đăng kí — chạy được **local**, không cần Colab.
> Mọi số liệu chỉ được lấy từ `runs/<run_id>/*.json` thật. Không nhập tay.

---

## Phần A — SASRec + cross-entropy (notebook 13)

### A.0 Ba thứ đã sẵn sàng

| Thành phần | Đường dẫn | Trạng thái |
|---|---|---|
| Module model | [`src/audit/sasrec.py`](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/src/audit/sasrec.py) | đã viết, `py_compile` OK, logic data-layer đã unit-test PASS (`logs/scratch/test_sasrec_logic.py`) |
| Generator notebook | [`scripts/generate_notebook_13.py`](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/scripts/generate_notebook_13.py) | chạy OK, sinh 11 cells, all code cells compile |
| Notebook | [`notebooks/jupyter/13_sasrec_ce.ipynb`](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/notebooks/jupyter/13_sasrec_ce.ipynb) | đã tồn tại, **đã regenerate 2026-11-18 14:34 sau sửa `attn_mask` bool**; smoke run PASS (`20261118_143029_13_sasrec_ce_29c68c40`), **full 3 split đã chạy** |

> [!NOTE]
> `torch` **đã cài xong** (`2.14.1+cu126`, CUDA 12.6). Nhánh `torch` (`make_model` / `train_model` / `evaluate_ndcg` / `recommend_topk`) **đã chạy smoke PASS**: module test `logs/scratch/smoke_sasrec.py` → `ALL SMOKE PASS` (hết warning `mismatched key_padding_mask and attn_mask`), smoke notebook run `20261118_143029_13_sasrec_ce_29c68c40` → 0 cell error, seen-exclusion 2.933/0 leak. nhưng **Full 3 split đã chạy xong** (`20261118_144646_13_sasrec_ce_8225755a`, 3/3 split COMPLETED). Số smoke không được đưa vào slide.

### A.1 Cài PyTorch bản CUDA

> [!IMPORTANT]
> **Wheel đã tải xong (2026-11-18): `D:\recsys_data\wheels\torch-2.14.1+cu126-cp314-cp314-win_amd64.whl` = 2.501,6 MB VÀ ĐÃ CÀI OFFLINE XONG 14:25** (`Successfully installed mpmath-1.3.0 networkx-3.7 setuptools-78.1.0 sympy-1.14.0 torch-2.14.1+cu126`; verify `TORCH_OK 2.14.1+cu126 12.6 True`). Lệnh bên dưới chỉ dùng khi cần cài lại — **không** chạy lại lệnh `pip install torch --index-url ...` (đã fail 2 lần do `ConnectionResetError [WinError 10054]`, pip không resume được trên Windows).

```powershell
.\.venv\Scripts\python.exe -m pip install --no-input --retries 10 --timeout 60 `
  "D:\recsys_data\wheels\torch-2.14.1+cu126-cp314-cp314-win_amd64.whl" `
  --index-url https://download.pytorch.org/whl/cu126
```

Index `cu126` vẫn cần để lấy dependencies nhỏ (`sympy`, `networkx`, `mpmath`, `setuptools`, `jinja2`, `fsspec`, `typing_extensions`) — wheel torch thì dùng file local, không tải lại 2,6 GB. Đặt `TMP`/`TEMP`/`PIP_CACHE_DIR` sang `D:\recsys_data\...` nếu ổ C còn ít chỗ (ổ C lúc cài còn 12,8 GB).

Python của venv là **3.14.5**; chỉ index `cu126` có wheel `cp314` + CUDA. **Không cần** `pytorch_lightning`: module tự viết thuần `torch` (`sasrec.py` không import lightning).

> [!NOTE]
> Nếu file wheel bị mất/bạn xoá, tải lại bằng `curl` có resume (nối tiếp được, không tải từ đầu):
> ```powershell
> curl.exe -L --retry 30 --retry-all-errors --retry-delay 3 -C - `
>   -o "D:\recsys_data\wheels\torch-2.14.1+cu126-cp314-cp314-win_amd64.whl" `
>   "https://download.pytorch.org/whl/cu126/torch-2.14.1%2Bcu126-cp314-cp314-win_amd64.whl"
> ```

### A.2 Xác nhận GPU nhìn thấy torch

```powershell
.\.venv\Scripts\python.exe -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

Kỳ vọng: `2.14.1+cu126 12.6 True NVIDIA GeForce RTX 4050 Laptop GPU`.
Nếu `False` → driver CUDA thấp hơn 12.6; driver hiện tại **610.78** là đủ, nên lỗi gần nhất thường là cài nhầm bản `cpu`. Kiểm tra bằng `pip show torch` (Version phải có hậu tố `+cu126`).

### A.3 Smoke test (làm trước, ~vài phút)

Mục đích: đi hết đường torch + Spark + metrics với chi phí nhỏ nhất, bắt bug trước khi đổ hàng giờ vào full run.

Mở notebook 13, sửa **cell config** (cell code ngay sau markdown giới thiệu):

```python
SMOKE_USERS = 3000                      # chi 3000 user dau tay
SPLITS_TO_RUN = ['random80_20']         # chi 1 split
```

Smoke này **đã chạy xong và PASS** tại run `20261118_143029_13_sasrec_ce_29c68c40` — số thật ở `TEMP.md` §8.7. Đoạn dưới là hướng dẫn nếu cần tự lặp lại. Ba điểm phải nhìn:

1. Cell GPU check in `cuda_available = True`, `device_name` = RTX 4050, và `run.checkpoint('gpu_check', 'PASS')`.
2. Cell train in `val_ndcg@10` **tăng** qua các epoch rồi early stop; `best_epoch` nằm trong `[1, 20]`.
3. Cell `check_seen_exclusion` in `status = PASS` (`users_with_leak = 0`) — đây là điều kiện tối thượng: model **không** được gợi ý item user đã xem.

> [!TIP]
> Muốn nhanh hơn nữa: `SMOKE_USERS = 500`. Chỉ cần chứng minh đường code chạy, không cần số có ý nghĩa. **Không** lấy số smoke vào slide.

### A.4 Chạy full (3 split, toàn bộ user)

Đặt lại trong cell config:

```python
SMOKE_USERS = None
SPLITS_TO_RUN = list(split_lib.STRATEGIES)   # random80_20, temporal_global, leave_one_out
```

Chạy từ CLI (tách terminal riêng, đừng ngồi chờ trong Jupyter):

```powershell
.\.venv\Scripts\python.exe scripts\generate_notebook_13.py
.\.venv\Scripts\python.exe scripts\run_notebook.py 13 --timeout 21600
```

> [!CAUTION]
> `run_notebook.py` **exit code 1 không đồng nghĩa thất bại**: nbclient in `RuntimeWarning` ở stderr → PowerShell biến thành `NativeCommandError`. Luôn xác minh bằng manifest:
> ```powershell
> Get-ChildItem runs | Sort-Object Name -Descending | Select-Object -First 1 | ForEach-Object { Get-Content "$($_.FullName)\manifest.json" -Raw }
> ```
> Phải thấy `"status": "COMPLETED"` và danh sách `checkpoints` đủ (`gpu_check`, `fit`, `eval`, `gates`).

### A.5 Ước lượng thời gian và cách hạ chi phí

| Hạng mục | Giá trị |
|---|---|
| Vocab | **38.328 item** (đo thực từ smoke run `20261118_143029_13_sasrec_ce_29c68c40`, item có trong train positive `rating >= 4.0` của ML-25M) — con số cũ 1.681 là sai, đã sửa |
| Logits full-catalog | `batch × seq × 38329 × 4 B`; `batch=32, maxlen=50` → ~245 MB/bước, vẫn an toàn trong 6 GB. Smoke chạy thật: VRAM free 5.024/6.140 MiB lúc bắt đầu |
| Effective batch | `32 × accum_steps 4 = 128` — **bằng** repo gốc, nhưng chia nhỏ để vừa VRAM |
| Epoch | `epochs=20`, early stop `patience=3` theo val NDCG (repo gốc dùng 200 epoch với BCE 1-negative) |
| Số user eval | 162.541 / split (do `collect_truth` lọc `rating >= 4.0`) |
| Thời gian | Smoke thật: 3.000 user / 1 split = **52,1 s** (fit 10,0 s), run `20261118_143029_13_sasrec_ce_29c68c40`. Ước thô full 162.541 user × 3 split ≈ **2,5 giờ** (xem `TEMP.md` §8.7) — chỉ để lên lịch, **không** đưa số này vào slide |

Nếu full quá lâu, **không** cắt số user. Thay vào đó chạy **từng split một** theo thứ tự ưu tiên slide:

```python
SPLITS_TO_RUN = ['random80_20']   # 1) split chính, đã có 4 baseline
# sau do: ['temporal_global']   # 2)
# sau do: ['leave_one_out']     # 3)
```

Mỗi lần chạy ghi `runs/<id>/sasrec_<split>.json` + `peruser_ndcg_sasrec_<split>.npz`; `sasrec_summary.json` của lần sau **chứa riêng split đó**. Khi gộp đủ 3 split, nói tôi gộp thành một `sasrec_summary.json` duy nhất (tôi viết script merge, không chạy lại model).

### A.6 Nếu gặp OOM (`torch.cuda.OutOfMemoryError`)

Sửa **đúng một** chỗ, giữ nguyên effective batch để không thành tinh chỉnh ẩn:

```python
'batch_size': 16,      # thay vi 32
'accum_steps': 8,      # thay vi 4  → van la 128
```

Vẫn OOM → `maxlen: 20`. Ghi chú vào docs: đây là **thay đổi do giới hạn phần cứng (VRAM 6 GB)**, không phải kết quả tìm siêu tham số. Nói tôi để cập nhật `Environment.md` + `Drawbacks.md` cho khớp.

Theo dõi VRAM lúc đang chạy:

```python
free, total = torch.cuda.mem_get_info()
print(f"VRAM free {free/2**20:.0f} MiB / {total/2**20:.0f} MiB")
```

### A.7 Điều cần khai báo (đã ghi sẵn trong notebook 13, đừng bỏ)

* Repo [03] `dataLeakageRec/SASRec` dùng **`BCEWithLogitsLoss` với 1 negative sampled / vị trí**. Bản này dùng **cross-entropy softmax trên toàn bộ catalog** (~38.328 negative/vị trí, đo thực) — đúng như đề tài đã đăng kí ("SASRec kết hợp cross-entropy"). Đây là **khác biệt có chủ đích**, phải nói rõ khi bị hỏi.
* `tuning_budget = 0`: **một** cấu hình cố định, không grid search — để công bằng với ALS (`rank=16, iter=8, reg=0.05, alpha=10`) và ItemKNN (`k=100, min_co=2`), theo yêu cầu "so sánh công bằng" của bài giảng 04.
* Validation split chia **theo user** (`VAL_FRACTION=0.1`, seed 42), early stop theo **val NDCG**; test set chỉ dùng **một lần** cuối. Không leak.
* **Không so sánh runtime** giữa SASRec (GPU) và 4 baseline (CPU Spark). `sasrec_summary.json` có field `hardware.note = 'KHONG so sanh runtime'`.

### A.8 Sản phẩm của lần chạy

```
runs/<run_id>/
  sasrec_random80_20.json          # per-user ndcg/hit/recall/mrr + bias + thoi gian
  sasrec_temporal_global.json
  sasrec_leave_one_out.json
  peruser_ndcg_sasrec_<split>.npz  # userId, ndcg (float32) — dung cho kiem dinh cap o notebook 12
  sasrec_summary.json              # tong hop 3 split + hardware + training history + tuning_budget
```

Chạy xong → báo tôi. Tôi sẽ nối vào notebook 09 (so sánh 5 model) và 12 (Wilcoxon 20 cặp), rồi cập nhật slide + docs bằng số thật.

---

## Phần B — MRR@10

`metrics.mrr_at_k` **đã có sẵn** trong [`src/audit/metrics.py`](file:///d:/Master%20Exers/Big%20Data/Recomendation_System/src/audit/metrics.py) (dòng 82) — không cần viết gì mới. Đã vá vào **5 generator** (`generate_notebook_06/08/10/11/13.py`), mỗi file 3 điểm: tính `mrr_mean` cạnh `recall_mean`, thêm field `'mrr10'` vào summary, in `mrr@10=` trong dòng kết quả. Notebook `06/08/10/11` **đã regenerate xong** và compile sạch.

> [!NOTE]
> MRR **không** làm thay đổi NDCG@10 / Recall@10 / Hit@10 — chỉ thêm một cột. Số cũ vẫn đúng nguyên vẹn.

### B.1 Chi phí re-run để lấy MRR

| Notebook | Model | Thời gian đã đo | Lệnh |
|---|---|---|---|
| 06 | MostPopular | 15,3 s | `.\.venv\Scripts\python.exe scripts\run_notebook.py 06` |
| 10 | Random | 111,1 s | `.\.venv\Scripts\python.exe scripts\run_notebook.py 10` |
| 08 | ALS | 286,7 s | `.\.venv\Scripts\python.exe scripts\run_notebook.py 08` |
| 11 | ItemKNN | 499,7 s | `.\.venv\Scripts\python.exe scripts\run_notebook.py 11 --timeout 21600` |
| 13 | SASRec | đã đo 3 split, run `20261118_144646_13_sasrec_ce_8225755a` | xem A.4 |

Tổng 4 baseline ≈ **15 phút**. Chạy được cả 4 liên tục:

```powershell
.\.venv\Scripts\python.exe scripts\run_notebook.py 06 10 08 11 --timeout 21600
```

### B.2 Hệ quả phải biết trước khi chạy

> [!WARNING]
> Mỗi lần re-run sinh **`run_id` mới**. Các artifact sau trỏ vào run cũ và sẽ **lệch**, tôi phải cập nhật sau:
> * `comparison.json` (notebook 09 — so sánh 4/5 model)
> * `paired_stats.json` (notebook 12 — 12/20 cặp Wilcoxon)
> * `docs/Project/Main/Document_Indexing.md` (bảng run id)
> * `docs/Project/Main/Metrics.md`, `System_Context.md`, slide 11–12
>
> **NDCG không đổi** (cùng seed 42, cùng protocol id `project_protocol_v1`) → kết luận thống kê không đổi. Chỉ run id và cột MRR là mới. Nếu bạn muốn **tiết kiệm thời gian nhất**, chỉ cần MRR cho slide thì **chạy 06 + 10 + 08 + 11 một lượt duy nhất**, đừng chạy đi chạy lại.

### B.3 Quyết định nên chốt (chọn một)

1. **Lấy MRR cho cả 5 model** (≈15 phút CPU + phần GPU) → bảng đầy đủ, khớp bài giảng 04 (nêu cả MRR trong nhóm chỉ số xếp hạng). **Khuyên dùng.**
2. **MRR đã có ở cả 5 model** (notebook 13 đã có sẵn, không phải re-run gì thêm) → bảng đã có MRR cho cả 5 model, xem `Metrics.md` §4.10.
3. **Bỏ MRR khỏi slide** → giữ NDCG/Recall/Hit. Bài giảng 04 không bắt MRR, chỉ bắt "chỉ số đánh giá phải nêu rõ và có lý do chọn".

---

## Phần C — Việc còn nợ (tôi làm, không cần bạn chạy gì)

| # | Việc | Chờ gì |
|---|---|---|
| C.1 | Plan ưu tiên cho môn PPNCKH vào `TEMP.md` §7 | không chờ — làm ngay |
| C.2 | Sửa claim "pipeline không dùng GPU" trong `notebooks/jupyter/README.md`, `01_De_tai_va_Ke_hoach.md`, `Environment.md`, `Drawbacks.md` §1, `TEMP.md`, slide 13–14 | chờ bạn xác nhận sẽ chạy SASRec trên GPU |
| C.3 | Notebook 09 → 5 model; notebook 12 → 20 cặp; slide 11–12; docs `Metrics.md` §4.10, `System_Context.md` §12, `Architecture.md` gate L13, `Document_Indexing.md` nb13 | chờ `sasrec_summary.json` |
| C.4 | Không đụng `.tex` (báo cáo viết **sau** thuyết trình) | đã chốt |
| C.5 | Không làm memory instrumentation RQ3 | đã chốt — ưu tiên slide/đề cương |
