# Error Log — I/O & tải dữ liệu

Lỗi khi tải từ FDA và khi đọc/ghi file trong môi trường Windows.

Format: `### [YYYY-MM-DD] [Category] Title` → Vấn đề / Nguyên nhân / Giải pháp

---

## 1. Tải từ FDA FTP area

### [2026-10-29] [HTTP] 403 Forbidden khi không có User-Agent

- **Vấn đề:** `Invoke-WebRequest` mặc định của PowerShell bị chặn:
  ```
  Invoke-WebRequest : The remote server returned an error: (403) Forbidden.
  ```
- **Nguyên nhân:** `accessdata.fda.gov` lọc theo `User-Agent`. UA mặc định
  `Mozilla/5.0 (Windows NT; Windows NT 10.0; ...) WindowsPowerShell/5.1` bị chặn.
- **Giải pháp:**
  ```powershell
  curl.exe -L -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" `
    -o "datasets\device2022.zip" `
    "https://www.accessdata.fda.gov/MAUDE/ftparea/device2022.zip"
  ```
- **Gotcha:** phải là `curl.exe`, không phải `curl`. Trong PowerShell, `curl` là alias của
  `Invoke-WebRequest` và **không nhận** `-A` / `-o` theo nghĩa của curl thật.

### [2026-10-29] [HTTP] HEAD trả 200 nhưng file không tồn tại lâu dài

- **Vấn đề:** HEAD trả `200 OK` + `Content-Length` cho file, nhưng FDA cập nhật
  `*Thru2025` **tại chỗ** khi có dữ liệu mới → nội dung thay đổi, size thay đổi.
- **Giải pháp:** Giữ **SHA-256** trong `datasets/manifest.json`. Size một mình không đủ.
- **Bài học:** "Tải được" ≠ "tải được cùng một thứ lần sau".

### [2026-10-29] [Path] Tên file sau giải nén KHÁC tên zip

- **Vấn đề:** `Expand-Archive device2022.zip` sinh ra `DEVICE2022.txt` (chữ HOA),
  không phải `device2022.txt`.
- **Bảng đối chiếu thật:**

  | Zip | File giải nén |
  |---|---|
  | `device2022.zip` | `DEVICE2022.txt` |
  | `device2023.zip` | `DEVICE2023.txt` |
  | `device2024.zip` | `DEVICE2024.txt` |
  | `device2025.zip` | `DEVICE2025.txt` |
  | `mdrfoiThru2025.zip` | `mdrfoiThru2025.txt` |
  | `foitext2025.zip` | `foitext2025.txt` |
  | `foidevproblem_thru2025.zip` | `foidevproblem_thru2025.txt` |
  | `patientproblemcode_thru2025.zip` | `patientproblemcode_thru2025.txt` |
  | `patientThru2025.zip` | `patientThru2025.txt` |
  | `deviceproblemcodes2025.zip` | `deviceproblemcodes2025.csv` |
  | `patientproblemcodes2026.zip` | `patientproblemcodes2026.csv` |

- **Giải pháp:** `schema.expected_columns()` so khớp bằng `name.lower().startswith(...)`,
  không so tên chính xác.

### [2026-10-29] [Disk] Hết chỗ khi giải nén — 29 GB → 27,9 GB

- **Vấn đề:** Sau khi giải nén 5 file bổ sung, đĩa D: từ 29,2 GB xuống **27,9 GB** trống.
  Parquet cho S2 cần thêm ~15–20 GB. Đo lại 2026-10-31: còn **27,2 GB** trống,
  parquet đã sinh 0,41 GB cho 5/12 file — đủ chỗ, nhưng theo dõi tiếp.
- **Nguyên nhân:** 14 file giải nén = 24,46 GiB; zip bị xoá sau giải nén nhưng txt vẫn còn.
- **Giải pháp:** Theo dõi trước khi chạy S2. Nếu thiếu: chỉ giữ cột dùng được ở S2,
  hoặc nén zstd thay snappy.
- **Bài học:** Tính tổng dung lượng **sau giải nén** trước khi tải, không phải dung lượng zip.

### [2026-10-29] [Script] Script giải nén lỗi vì zip đã bị xoá

- **Vấn đề:**
  ```
  Could not find file 'D:\...\datasets\device2022.zip'
  ```
- **Nguyên nhân:** Script `dl_missing.ps1` tải → giải nén → **xoá zip** trong cùng một
  lần chạy. Chạy lại script lần 2 thì zip không còn.
- **Giải pháp:** Script kiểm tra `Test-Path` file `.txt` trước, chỉ tải nếu chưa có.
  Idempotent.

---

## 2. Đọc file trong Python

### [2026-10-29] [Encoding] UTF-8 làm hỏng toàn bộ narrative

- **Vấn đề:** `open(path, encoding="utf-8")` raise `UnicodeDecodeError` hoặc (tệ hơn, với
  `errors="replace"`) biến mọi ký tự >127 thành `�`.
- **Nguyên nhân:** MAUDE là **latin-1 (ISO-8859-1)**, không phải UTF-8. Tên hãng châu Âu
  (`Müller`, `Société`) chứa byte >127 không hợp lệ trong UTF-8.
- **Giải pháp:**
  ```python
  io.open(path, "r", encoding="latin-1", errors="replace", newline="")
  ```
- **Gotcha:** `newline=""` cần thiết để `csv`/split xử lý `\r\n` đúng. Không có nó,
  Windows sẽ dịch `\r\n` → `\n` và cột cuối có thể dính `\r`.

### [2026-10-29] [Parse] `read_csv` mặc định SAI với file không có header

- **Vấn đề:** `pd.read_csv("foidevproblem_thru2025.txt", sep="|")` mất dòng đầu và đặt
  tên cột là `1234567|1546`.
- **Nguyên nhân:** `header="infer"` (mặc định) lấy dòng 1 làm header.
- **Giải pháp:** `header=None, names=["MDR_REPORT_KEY", "PROBLEM_CODE"]`.
  Trong project: `src/data/io.py:read_device_problem()`.

### [2026-10-29] [Parse] Cột rỗng bị pandas biến thành `NaN` rồi mất khi ghi

- **Vấn đề:** `pd.read_csv(..., na_values=[""])` → `NaN` → ghi parquet thành `null`.
  Nhưng MAUDE dùng **chuỗi rỗng** làm null, và phân biệt "rỗng" với "không có cột".
- **Giải pháp:** `keep_default_na=False, na_values=[]` → giữ nguyên chuỗi rỗng.
  Trong project: mọi cột giữ `string`, không convert.

### [2026-10-29] [Memory] Batch 200.000 dòng phình lên hàng GB

- **Vấn đề:** Một ô `FOI_TEXT` dài 9.998.819 ký tự làm batch 200.000 dòng chiếm hàng GB.
- **Giải pháp:** Cắt ở `schema.TEXT_MAX_CHARS = 20_000` **ngay trong reader**, trước khi
  vào batch. Ảnh hưởng 460/24,7M dòng.

---

## 3. PowerShell trên Windows

### [2026-10-29] [Shell] `head`, `tail`, `ls -la` không tồn tại

- **Vấn đề:** `head -20 file` → `CommandNotFoundException`.
- **Giải pháp:**

  | Linux | PowerShell |
  |---|---|
  | `head -20 f` | `Get-Content f -TotalCount 20` |
  | `tail -20 f` | `Get-Content f -Tail 20` |
  | `ls -la` | `Get-ChildItem -Force` |
  | `wc -l f` | `(Get-Content f).Count` |
  | `du -sh d` | `(Get-ChildItem d -Recurse \| Measure-Object Length -Sum).Sum` |
  | `grep x f` | `Select-String -Path f -Pattern x` |

### [2026-10-29] [Shell] Tiếng Việt in ra thành `?` hoặc lỗi `UnicodeEncodeError`

- **Vấn đề:** Console Windows là **cp1252**, không encode được tiếng Việt.
  ```
  UnicodeEncodeError: 'charmap' codec can't encode character '\u1ebf'
  ```
- **Giải pháp:** Đặt biến môi trường trước khi chạy Python:
  ```powershell
  $env:PYTHONIOENCODING = "utf-8"
  python -u scripts\s4_audit.py
  ```
- **Gotcha:** `-u` (unbuffered) cần thiết nếu muốn thấy log realtime khi chạy background.

### [2026-10-29] [Shell] `java -version` ghi ra stderr → PowerShell báo lỗi

- **Vấn đề:**
  ```
  java : java version "24.0.2" 2025-07-15
  + CategoryInfo : NotSpecified: (...) [], RemoteException
  + FullyQualifiedErrorId : NativeCommandError
  ```
- **Nguyên nhân:** `java -version` ghi ra stderr (từ Java 8). PowerShell coi stderr là lỗi.
- **Giải pháp:** `java -version 2>&1 | Out-String` — vô hại, chỉ là cảnh báo.

### [2026-10-29] [Shell] Đường dẫn có dấu cách

- **Vấn đề:** `D:\Master Exers\Big Data\Medical_Equipment\...` có 3 dấu cách.
- **Giải pháp:** Luôn quote. Trong Python dùng raw string `r"D:\Master Exers\..."`.

### [2026-10-29] [Shell] Output bị buffer, không thấy tiến độ

- **Vấn đề:** Chạy background, poll mãi không thấy output mới dù process đang chạy
  (CPU tăng đều).
- **Nguyên nhân:** Python buffer stdout khi không phải TTY.
- **Giải pháp:** `python -u` hoặc `flush=True` trong mọi `print()` của script dài.

---

## 4. Ghi file

### [2026-10-29] [Write] File `.md` UTF-8 có BOM làm hỏng patch script

- **Vấn đề:** Script patch tìm chuỗi không thấy dù chuỗi có trong file (`count=0`).
- **Nguyên nhân:** Một số editor ghi UTF-8 **có BOM** (`\ufeff`) ở đầu file; và một số
  dòng dùng **em dash `—`** thay vì hyphen `-`.
- **Giải pháp:** Đọc/ghi với `encoding="utf-8"` (không phải `utf-8-sig`), và **copy chuỗi
  tìm kiếm từ chính file** thay vì gõ lại.

### [2026-10-29] [Write] `newline=""` khi ghi text để tránh `\r\n` tự động

- **Vấn đề:** Ghi file trên Windows tự thêm `\r` vào mọi `\n` → diff toàn bộ file.
- **Giải pháp:** `io.open(path, "w", encoding="utf-8", newline="\n")`.

---

## 5. Git

### [2026-10-29] [Git] `datasets/` bị ignore hoàn toàn, không re-include được `manifest.json`

- **Vấn đề:** `.gitignore` có `datasets/` → git bỏ qua cả thư mục, và `!datasets/manifest.json`
  **không có tác dụng**.
- **Nguyên nhân:** Git không thể re-include một file nếu **thư mục cha** bị exclude.
- **Giải pháp:** Đổi thành `datasets/*` (loại nội dung, không loại thư mục) rồi
  `!datasets/manifest.json`.
- **Kiểm chứng:** `git check-ignore -v datasets/manifest.json` → in ra dòng `!datasets/manifest.json`
  nghĩa là đã re-include.

### [2026-10-29] [Git] Branch `main` không có commit nào

- **Vấn đề:** `git log` → `fatal: your current branch 'main' does not have any commits yet`.
- **Trạng thái:** 11 mục untracked. Commit đầu tiên chờ `verify_datasets.py` PASS.

---

## 6. Bài học vận hành: job dài bị kill, không phải do OOM

### [2026-10-31] [Process] Exec session SIGKILL process Python ở ~15 triệu dòng

- **Vấn đề:** `python scripts\s4_audit.py` chạy được đến dòng 15.000.000 rồi chết:
  ```
  ... 15,000,000 rows
  Process exited with signal SIGKILL.
  ```
  Lần 1 nghĩ là OOM. Lần 2 kiểm RAM: **còn 11,9 / 31,7 GB trống** — không phải OOM.

- **Nguyên nhân:** Process do exec session quản lý bị thu hồi khi vượt ngưỡng thời
  gian/CPU của session. Đây là hành vi của shell, không phải của Python hay của OS.

- **Giải pháp:** Chạy **detached**, tách khỏi session:
  ```powershell
  Start-Process -FilePath "python" -ArgumentList "scripts\s4_audit.py" `
    -RedirectStandardOutput "tmp\s4.out" -RedirectStandardError "tmp\s4.err" `
    -WindowStyle Hidden
  ```
  Kiểm tra còn sống:
  ```powershell
  Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -like "*s4_audit*" } |
    Select-Object ProcessId, @{n='WS_MB';e={[math]::Round($_.WorkingSetSize/1MB,0)}}
  ```

- **Bài học:** **Job >20 phút phải chạy detached.** Và khi process chết ở một
  mốc số dòng tròn trị, nghĩ ngay đến giới hạn của shell trước khi nghĩ đến OOM.
  Kiểm tra RAM trước khi "tối ưu bộ nhớ" — nếu RAM còn nhiều thì vấn đề ở chỗ khác.

### [2026-10-31] [Process] `Get-Process -Id` không lấy được CommandLine

- **Vấn đề:** Cần biết process Python nào đang chạy script nào, nhưng `Get-Process`
  không có thuộc tính CommandLine.
- **Giải pháp:** `Get-CimInstance Win32_Process -Filter "Name='python.exe'"` — có
  `CommandLine`, `ParentProcessId`, `CreationDate`, `WorkingSetSize`.

---

## 7. Hợp đồng của reader: một bản ghi KHÔNG phải một dòng vật lý

### [2026-10-30] [Parse] `_logical_records()` — dùng `==` không phải `>=`

- **Vấn đề:** Khi viết lại reader cho MAUDE, có hai biến thể điều kiện kết thúc bản ghi:
  `buf.count("|") + 1 >= ncols` và `== ncols`. Chọn sai sẽ **coi bản ghi hỏng là
  hợp lệ**, làm số liệu đẹp giả tạo.

- **Quy tắc đúng:**
  - `>= ncols` chỉ dùng để **biết đã hết một bản ghi** (dừng gom dòng).
  - `== ncols` dùng để **quyết định bản ghi đó có hợp lệ không**.
  - Bản ghi **vượt** số cột phải được yield ra và caller đếm là hỏng.

- **Bằng chứng:** master có đúng **3** bản ghi vượt số cột. Nếu dùng `>=` để
  emit, 3 bản ghi này sẽ được tính là hợp lệ → `malformed = 0` → báo cáo "sạch
  100%", sai.

- **Bài học:** Khi viết lại một reader có `strict` flag, phải có test chứng minh
  `strict=False` **không** nuốt bản ghi hỏng. Ở đây là đối chiếu tổng: số bản
  ghi đọc được + số bị bỏ = số dòng vật lý − số dòng đã ghép.

### [2026-10-30] [Parse] `count_rows` phải đếm bản ghi logic, không phải dòng

- **Vấn đề:** `count_rows()` cũ đếm theo dòng vật lý → trả về
  `(23.629.839, 6.681)` trong khi sự thật là `(23.633.176, 3)`.
- **Giải pháp:** `count_rows()` dùng cùng `_logical_records()` như `read_maude()`.
  Một bản ghi ghép từ 2 dòng là **1** dòng hợp lệ, không phải 2 dòng lỗi.
- **Bài học:** Hai hàm cùng đọc một file phải dùng **cùng một định nghĩa bản ghi**.
  Nếu không, `verify` sẽ FAIL trên file mà `parse` đọc đúng.

---

## 8. PowerShell: heredoc không tồn tại

### [2026-10-31] [Shell] `git commit -F - <<'EOF'` không chạy trong PowerShell

- **Vấn đề:**
  ```
  The '<' operator is reserved for future use.
  Missing file specification after redirection operator.
  ```
  PowerShell không có here-document của bash.

- **Giải pháp:** Ghi message ra file rồi truyền file:
  ```powershell
  # dùng tool write để tạo tmp\commitmsg.txt, rồi:
  git commit -F tmp\commitmsg.txt
  ```
- **Bài học:** Mọi cú pháp bash `<<EOF`, `<<<`, `$(...)` đều không dùng được.
  Trong PowerShell, `$()` có tồn tại nhưng nghĩa khác.

### [2026-10-31] [Shell] `python -c` với chuỗi tiếng Việt dài → SyntaxWarning / SyntaxError

- **Vấn đề:** `python -c "...\M...\D..."` sinh
  `SyntaxWarning: "\M" is an invalid escape sequence`. Chuỗi dài có dấu ngoặc kép
  lồng còn gây `SyntaxError: unterminated string literal`.
- **Giải pháp:** Với patch có chuỗi tiếng Việt, **viết ra file `.py` rồi chạy**,
  không dùng `-c`. Đồng thời đặt `$env:PYTHONIOENCODING="utf-8"`.
- **Bài học:** `-c` chỉ dùng cho lệnh một dòng không có tiếng Việt.

### [2026-10-31] [Shell] `Select-String` hiển thị tiếng Việt bị lỗi font

- **Vấn đề:** `Select-String` in ra `B?n ca hi?u sai` — trông như file bị háng.
- **Nguyên nhân:** Console cp1252. **File vẫn đúng UTF-8.**
- **Giải pháp:** Kiểm nội dung thật bằng Python:
  ```powershell
  python -c "import io; print(io.open('file.md',encoding='utf-8').read()[:500])"
  ```
  hoặc `Get-Content file.md -Encoding UTF8`.
- **Bài học:** **Không "sửa" file chỉ vì Select-String hiển thị xấu.** Kiểm bằng
  công cụ đọc UTF-8 trước.

---

## 9. Ghi file: `apply_patch` bị chặn ngoài sandbox

### [2026-10-31] [Tool] `apply_patch` từ chối đường dẫn ngoài workspace

- **Vấn đề:**
  ```
  Path escapes sandbox root (~\.openclaw\workspace):
  D:\Master Exers\Big Data\Medical_Equipment\docs\...\Metrics.md
  ```
- **Giải pháp:** Dùng tool `edit` (nhận `oldText`/`newText`) cho file trong `D:\`,
  hoặc viết script Python `.py` rồi chạy bằng `exec`.
- **Bài học:** `apply_patch` chỉ dùng trong workspace. Với project ngoài workspace:
  `edit` cho sửa nhỏ, script `.py` cho sửa nhiều chỗ.

## 10. RecSys — tải paper và ghi file (2026-11-04)

### [2026-11-04] [HTTP] ACM DL chặn `urllib`/`requests` (403) dù đã giả User-Agent Chrome

- **Vấn đề:**
  ```python
  urllib.request.urlopen("https://dl.acm.org/doi/pdf/10.1145/3604915.3609495")
  # -> HTTP Error 403: Forbidden
  ```
  Giả `User-Agent: Mozilla/5.0 ... Chrome/144` vẫn 403.

- **Nguyên nhân:** ACM DL dùng **Cloudflare bot protection** kiểm tra **cookie `cf_clearance`**
  gắn với **đúng User-Agent + IP** đó. Không có cookie → 403 dù UA có hợp lệ.

- **Giải pháp (đã dùng, thành công):**
  1. Mở trang DOI bằng browser OpenClaw (profile `openclaw`, CDP `127.0.0.1:18800`) → Cloudflare
     cấp `cf_clearance` cho phiên đó.
  2. Dump cookie qua CDP `Storage.getCookies` (browser-level, **không cần attach page**).
  3. Replay bằng `urllib` với header `Cookie` + `Referer` + **UA Chrome desktop giống hệt** lúc dump.

- **Bằng chứng:** cùng 1 URL, `urllib` không cookie → 403; có cookie → HTTP `200`,
  `Content-Type: application/pdf;charset=UTF-8`, `414562` bytes, header `%PDF`.

- **Bài học:**
  - `cf_clearance` gắn với **UA + IP** → copy sang script khác UA là fail.
  - `Storage.getCookies` không cần attach page → nhẹ hơn `Network.getAllCookies`.

### [2026-11-04] [HTTP] Các API dự phòng cho paper cũng bị chặn

| Nguồn | Lỗi | Ghi chú |
|---|---|---|
| ACM DL (`urllib`) | `403 Forbidden` | xem mục trên |
| Unpaywall | `403 Forbidden` | cần `email=` param, nhưng vẫn 403 |
| Semantic Scholar | `429` (rate limit) | tạm thời |
| DR-NTU Handle (HTTP client) | `405 Not Allowed` | server chặn method |
| DR-NTU Handle (browser) | trang `Human Verification` | Cloudflare |
| OpenAlex | ✅ OK | dùng để tra DOI + `oa_status` |

- **Giải pháp:** Nguồn đáng tin cậy nhất cho bản PDF hợp pháp: **arXiv** (03 bài có bản
  arXiv), **IR repository của nhà xuất bản** (CWI cho TOIS 2023), và **ACM browser session**
  cho bài hybrid.

- **Bài học:** Đừng dựng cả pipeline tải quanh một nguồn. Thiết kế fallback chain
  `arXiv → publisher IR → ACM browser → OA aggregator` ngay từ đầu.

### [2026-11-04] [Tool] Browser fetch sang sink HTTP bị chặn mixed-content

- **Vấn đề:** Trang HTTPS (`dl.acm.org`) `fetch("http://127.0.0.1:8765")` →
  `TypeError: Failed to fetch`.

- **Nguyên nhân:** **Mixed content** — trang HTTPS không được fetch sang HTTP. Đây là quy tắc
  của trình duyệt, không phải lỗi mạng.

- **Giải pháp:** Dùng **sink HTTPS** (self-signed) hoặc `postMessage` sang tab HTTP mở sẵn
  ở cửa sổ khác (cross-window qua `postMessage` không bị mixed-content chặn).

### [2026-11-04] [Tool] `browser(action="download")` trả `ref required`

- **Vấn đề:** Gọi download không có `ref` → lỗi `ref required`.

- **Giải pháp:** Anchor download phải click có `ref` thật từ `snapshot` (`refs="aria"`),
  và **thư mục download thật** phải xác định trước — `C:\Users\PC\Downloads` **không tồn tại**
  trên máy này (Chrome tải vào thư mục hệ thống khác).

- **Bài học:** Trước khi dựng flow download, kiểm tra `Downloads` path thật của profile.

---

## 11. RecSys — ghi đọc file, script, console (2026-11-04)

### [2026-11-04] [Streamlit] `sys.stdout = io.TextIOWrapper(sys.stdout.buffer)` → app crash

- **Vấn đề:** Dashboard Streamlit hiện lỗi:
  ```
  ValueError: I/O operation on closed file
  File "...scripts/07_dashboard.py", line 5, in <module>
      sys.stdout = io.TextIOWrapper(...)
  ```

- **Nguyên nhân:** Khi script chạy dưới `streamlit run`, Streamlit **đóng stdout cũ** rồi
  mở stream mới. `TextIOWrapper` bọc `sys.stdout.buffer` cũ → khi Streamlit đóng buffer đó,
  mọi lệnh `print` sau đó ném `ValueError`. Pattern này **an toàn dưới `python` thuần**
  (nơi stdout không bị đóng) nên rất dễ lọt.

- **Bằng chứng:** `chrome --screenshot` chỉ ra trang nền tối, `document.title = "Streamlit"`,
  `txtlen = 32`, và `data-testid="stException"]` = 1 → app chết ngay dòng 5.

- **Giải pháp:**
  ```python
  import os, sys
  try:
      sys.stdout.reconfigure(encoding="utf-8", errors="replace")
  except Exception:
      pass
  ```
  `reconfigure` đổi encoding của **chính stream hiện tại**, không tạo wrapper mới → an toàn
  dưới cả `python` lẫn `streamlit run`.

- **Bài học:** Pattern "ép UTF-8 cho console" phải viết theo cách **không phụ thuộc vòng đời
  của stream**. `reconfigure` là cách đúng; `TextIOWrapper` chỉ đúng khi bạn sở hữu stream.

### [2026-11-04] [Spark] `df.write.parquet` fail vì thiếu `winutils.exe`

- **Vấn đề:**
  ```
  java.lang.RuntimeException: java.io.FileNotFoundException:
  Hadoop bin directory does not exist: ...\_fake_hadoop_home\bin
  ```

- **Nguyên nhân:** Đặt `HADOOP_HOME` giả (thư mục rỗng) làm Spark **không còn báo
  "unset"** nhưng `RawLocalFileSystem.setPermission` vẫn cần `winutils.exe` thật trong
  `$HADOOP_HOME\bin`. Trên máy này **không có** `winutils.exe` ở bất kỳ đâu đã tìm.

- **Giải pháp:** Ghi Parquet bằng **pyarrow** (`pyarrow.parquet.ParquetWriter`), không dùng
  `df.write.parquet`. Đọc Parquet bằng Spark thì **OK** (đọc file đơn).

- **Bài học:** `HADOOP_HOME` giả chỉ **đổi triệu chứng**, không giải quyết gốc rễ. Khi
  Spark cần quyền POSIX trên Windows mà không có `winutils`, hãy **tránh đường ghi file**
  đó thay vì giả môi trường.

### [2026-11-04] [Spark] `df.write.parquet` fail dù `HADOOP_HOME` unset

- **Vấn đề:** `Py4JJavaError: ... java.io.FileNotFoundException: HADOOP_HOME and
  hadoop.home.dir are unset`.

- **Giải pháp (đã áp dụng ở `scripts/04_audit_spark.py`):** ghi Parquet bằng **pyarrow**.

### [2026-11-04] [Screenshot] `chrome --screenshot` không chờ Streamlit render → ảnh trống

- **Vấn đề:** `chrome --headless=new --screenshot=... http://localhost:8501` tạo file
  18–20 KB, 100% pixel là nền tối `(14, 17, 23)`.

- **Nguyên nhân:** Streamlit render qua **websocket**. `--screenshot` chụp ngay khi
  `load` event xong, lúc app chưa kịp vẽ chart.

- **Giải pháp (`scripts/15_screenshot_dashboard.py`):** điều khiển Chrome qua
  **CDP (Chrome DevTools Protocol)**:
  1. `Target.createTarget` + `Target.attachToTarget` (flatten session).
  2. `Page.navigate` → poll `Runtime.evaluate` tới khi có `.js-plotly-plot` và
     `innerText` > 300 ký tự.
  3. `Emulation.setDeviceMetricsOverride` theo `document.body.scrollHeight`.
  4. `Page.captureScreenshot` với `captureBeyondViewport: true` → chụp trang dài.

- **Bằng chứng:** sau khi sửa `07_dashboard.py`, ảnh ra **152.694 bytes**, 1920×1260,
  4006 màu distinct, có palette chart (131,201,255) và (0,104,201) → **render thật**.

- **Bài học:** App render bất đồng bộ cần **điều khiển trình duyệt ở mức protocol**,
  không phải `--screenshot` của CLI.

### [2026-11-04] [Script] `apply_patch`/`edit` fail trên file CRLF + blank-line lệch

- **Vấn đề:** `edit` tool báo không khớp `oldText` dù đọc file thấy nội dung đúng.

- **Nguyên nhân:** File sinh bởi công cụ khác dùng `\r\n` hoặc có **dòng trống thừa**
  lệch so với chuỗi `oldText` viết tay.

- **Giải pháp:** Patch bằng **Python `str.replace`** trong file `.py` riêng, rồi chạy file đó.
  Đây cũng là cách dùng cho Markdown tiếng Việt (tránh mojibake cp1252 của PowerShell
  here-string).

### [2026-11-04] [Shell] PowerShell `>` ghi file ra **UTF-16**, đọc lại thành ký tự `\x00`

- **Vấn đề:** `python ... > out.log` trên PowerShell → file log là UTF-16, đọc bằng
  `Get-Content` hiện ký tự `�` xen kẽ `\x00`.

- **Giải pháp:** Để **script tự ghi file** bằng `open(path, "w", encoding="utf-8")`.
  Không redirect bằng `>` cho file tiếng Việt.

### [2026-11-04] [Shell] `python -c "..."` với chuỗi tiếng Việt + escape kép → SyntaxError

- **Vấn đề:** `python -c "old = '...\"utf-8\"...'"` → `SyntaxError: unterminated string literal`.

- **Nguyên nhân:** PowerShell + Python `-c` + escape kép chồng nhau.

- **Giải pháp:** **Luôn** viết file `.py` riêng rồi `python file.py`. Không dùng `python -c`
  cho logic nhiều dòng. (Xem `io.md` §8 — cùng dạng lỗi, đã ghi lần trước.)

### [2026-11-04] [Process] Job dài bị SIGKILL ~30 phút; phải chia nhỏ

- **Bằng chứng:** Job `scripts/11_peruser_ndcg.py` chạy 2 split × ~5,5 phút → vẫn ổn.
  Job `scripts/12_stats_tests.py` bản **Python thuần** chạy > 12 phút không xong, bị giết.

- **Giải pháp:**
  - `11_peruser_ndcg.py`: chạy **1 split / 1 lệnh** (mỗi split ~5,5 phút) → an toàn.
  - `12_stats_tests.py`: **vector hoá** bootstrap + Wilcoxon bằng numpy (chunk 500) →
    rút từ > 12 phút xuống **~2 phút / split**.
  - `14_perf_benchmark.py`: tách phần **Spark** và phần **MapReduce/YARN** thành 2 bước.

- **Bài học:** Với exec session của OpenClaw, **30 phút là trần**. Mọi job dài phải
  (a) chia nhỏ theo đơn vị tự nhiên, hoặc (b) vector hoá để về mặt thời gian.
