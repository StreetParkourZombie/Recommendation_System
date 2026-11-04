# Chương 1 — Ứng dụng & dữ liệu

**Môn:** IT252BIDA — Xử lý dữ liệu lớn · **GV:** PhD. Võ Thị Hồng Tuyết
**Người thực hiện:** Trần Khôi Nguyên (MIT26004) — nhóm 4

---

## 1.1 Bài toán

**Phát hiện Prompt Injection** trong câu lệnh người dùng gửi tới chatbot/LLM.

Prompt Injection là kỹ thuật khiến mô hình ngôn ngữ bỏ qua chỉ dẫn hệ thống và
làm theo chỉ dẫn của kẻ tấn công — ví dụ ép bot bỏ qua filter, tiết lộ system
prompt, hoặc sinh nội dung độc hại.

Bài toán được hiểu là **phân loại nhị phân ở mức văn bản**:

| Nhãn | Ý nghĩa |
|---|---|
| `0` (benign) | Câu lệnh bình thường, không có ý đồ chiếm quyền chỉ dẫn |
| `1` (attack) | Có ý đồ chỉ đạt/lệch chỉ dẫn hệ thống |

Không chạy đua SOTA. Mục tiêu là **đo trung thực** khả năng tổng quát hóa trên
corpus đa nguồn, bằng công cụ Big Data theo đúng đề cương môn.

### Ba câu hỏi nghiên cứu

| Mã | Câu hỏi | Cách đo |
|---|---|---|
| **RQ1** | Khi train và test cùng phân bố, model phân biệt tốt đến đâu? | F1 trên test split (80/10/10 theo `source`) |
| **RQ2** | Đổi nguồn dữ liệu thì hiệu năng mất bao nhiêu? | F1/AUC theo từng nguồn + **LOSO** (bỏ hẳn nguồn khỏi train) |
| **RQ3** | Bao nhiêu phần hiệu năng đến từ **độ dài** thay vì **từ vựng**? | Ablation unigram + AUC của riêng độ dài (R, pROC) |

---

## 1.2 Nguồn dữ liệu — 10 nguồn, 3 họ nguồn

| # | Nguồn | Dòng (sau dedupe) | Họ | Vai trò |
|---|---|---:|---|---|
| 1 | `allenai/wildguardmix` | 47,547 | adversarial | Nguồn attack lớn nhất + benign đi kèm |
| 2 | `reshabhs/SPML_Chatbot_Prompt_Injection` | 16,012 | roleplay | Persona/instruction override |
| 3 | `allenai/WildChat-1M` | 15,382 | benign stream | Hội thoại thật, **chỉ benign** |
| 4 | `S-Labs/prompt-injection-dataset` | 15,108 | direct | Prompt injection trực tiếp |
| 5 | `xTRam1/safe-guard-prompt-injection` | 10,108 | mixed | An toàn + tấn công |
| 6 | `lmsys/toxic-chat` | 9,586 | jailbreak | Hội thoại thật có nội dung độc hại |
| 7 | `guychuk/open-prompt-injection` | 6,583 | indirect | Injection qua tài liệu, không trực tiếp |
| 8 | `lmsys/lmsys-chat-1m` | 18,531 | benign stream | Hội thoại thật, **chỉ benign** |
| 9 | `allenai/wildjailbreak` | 2,206 | jailbreak | Adversarial có nhãn mức độc hại |
| 10 | `deepset/prompt-injections` | 662 | classic | Template injection cổ điển |
| | **Tổng** | **141,725** | | |

**Điểm quan trọng:** 2 nguồn **chỉ có benign** (WildChat, lmsys) và 1 nguồn
**chỉ có attack** (wildjailbreak). Vì vậy *cross-dataset* phải đo FPR (tỉ lệ
bắt nhầm benign) chứ không chỉ F1.

### 1.2.1 Ba ca hiểu sai nhãn — cùng một dạng lỗi

Đây là phần em muốn nhấn mạnh nhất trong báo cáo, vì nó quyết định chất lượng
toàn bộ kết quả phía sau.

**Cách chung:** cột tên nghe như nhãn phân loại, nhưng thực chất đo một thứ khác.
Ba ca đều bị phát hiện bằng **kiểm tra bằng chứng**, không phải bằng cảm tính.

| Dataset | Cột | Nghĩa thật | Hậu quả nếu dùng sai | Cách phát hiện |
|---|---|---|---|---|
| **HackAPrompt** | `labels` | *prompt đã thắng model mục tiêu* (đạt `PWNED`) | Toàn bộ nhãn đảo nghĩa | 715 text có nhiều nhãn khác nhau; 86.21% chứa `PWNED` |
| **WildJailbreak** | `label` | *mức độc hại* của prompt | FPR = **1.0** (17/17 benign bị bắt nhầm) | `data_type` = `adversarial_harmful` / `adversarial_benign` — cả hai đều adversarial |
| **SPML** | `Degree` | *mức gắn kết với persona* | Suy ra sai ý đồ tấn công | `Degree=10` ứng với roleplay lành mạnh ("You are a knowledgeable and reliable HealthAI…") |

→ **HackAPrompt bị loại khỏi corpus** (mất 227K dòng nhưng tránh được việc model
học "prompt đã thắng model khác" thay vì "prompt có ý đồ xấu").
→ **WildJailbreak**: đặt `label=1` cho toàn bộ, `label` cũ chuyển thành `severity`.
→ **SPML**: dùng cho hồi quy severity, không dùng làm nguồn nhãn phân loại.

> **Quy tắc rút ra:** trước khi tin một metric bất thường, kiểm tra nhãn trước.
> FPR = 1.0 là dấu hiệu chắc chắn nhãn bị hiểu sai, không phải model dở.

Chi tiết đầy đủ: `docs/Project/Main/MetErrors/datasets.md`.

---

## 1.3 Dựng corpus — 3 bước chống rò rỉ

### 1.3.1 Dedupe toàn cục

188,366 dòng thô → **141,725** dòng sau dedupe (loại 24.7%).
Khóa dedupe: chuẩn hoá whitespace + lowercase + hash nội dung.

### 1.3.2 Chống leakage — 3 lớp

| Lớp | Cơ chế | Kết quả |
|---|---|---|
| 1 | Dedupe toàn cục trên text chuẩn hoá | 0 trùng giữa train/val/test |
| 2 | Split theo **nhóm**, không theo dòng | `guychuk`: `crc32(task_type\|normal_input)` → 1,397 nhóm |
| 3 | Giới hạn 1 benign + tối đa 4 attack mỗi nhóm | Không còn "cặp attack/benign" cùng nhóm ở 2 split |

**Vì sao cần lớp 3:** nếu một benign và attack của cùng nhóm nằm ở 2 split khác
nhau, model có thể học "biết cặp này" thay vì học đặc trưng của injection.

**Kiểm chứng:** `verification/verify_split.py` → **0 rò rỉ** trên 3 lớp.

### 1.3.3 Quy tắc nhãn theo nguồn

| Nguồn | `split` | Lý do |
|---|---|---|
| `deepset/prompt-injections` | **`unassigned`** | 662 dòng → giữ ngoài mọi split để làm **hold-out ngoài** |
| `allenai/WildChat-1M`, `lmsys/lmsys-chat-1m` | `unassigned` | Chỉ benign → dùng đo FPR, không train |
| `allenai/wildjailbreak` | `unassigned` | Chỉ attack → dùng đo recall, không train |
| 7 nguồn còn lại | train/val/test 80/10/10 | Theo `source` |

Kết quả split: **train 109,543 · validation 12,808 · test 19,374**.

---

## 1.4 Đặc trưng phân bố — và bẫy độ dài

| Lớp | n | mean | median | IQR |
|---|---:|---:|---:|---|
| benign (`label=0`) | 88,655 | 406.2 | **95** | [50, 249] |
| attack (`label=1`) | 53,070 | 982.8 | **773** | [462, 1403] |

Attack dài hơn gấp **8.1×** ở median. Đây là điểm khởi đầu của RQ3, và cũng là
cảnh báo lớn nhất về phương pháp (xem Chương 2, mục đo lường).

Theo family: `jailbreak` dài **6.4×** benign, `direct` **3.0×**, `indirect` **1.7×**.
Family nào càng "bọc ngoài" (roleplay, kịch bản dài) thì càng dài — đây là lý do
mô hình bag-of-words dễ học "template" thay vì "cơ chế".

---

## 1.5 Kiểm chứng dữ liệu đầu vào

| Script kiểm chứng | Kết quả |
|---|---|
| `verification/verify_split.py` | 0 rò rỉ 3 lớp |
| `verification/verify_spml.py` | 16,012 dòng, 0 trùng |
| `verification/verify_hackaprompt.py` | 227,042 dòng — **loại** vì nhãn sai nghĩa |
| `verification/verify_attack_sets.py` | OK |
| `verification/list_wildjailbreak.py` | 2,206 dòng, `data_type` 2 giá trị |

Tổng 39 file Python trong repo đều pass **syntax + import** (`tools/patches/smoke_test.py`).

---

*Chương 1 — xem tiếp Chương 2 (phương pháp) và Chương 3 (kết quả).*
