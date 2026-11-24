# Script thuyết trình đề cương — 20 slide

**Bám theo:** `docs/Project/Main/Presentation/Slides/PPNCKH_DeCuong_20slides.pptx`
**Thời lượng:** ~20 phút. Mỗi slide: phần **Nói** đọc gần nguyên văn; phần **Khái niệm** để trả lời hội đồng.
**File cũ:** `PPNCKH_DeCuong_15slides_Self-Adjustion.pptx` lỗi thời, không dùng. `PPNCKH_DeCuong_15slides.pptx` giữ làm bản dự phòng.

## Nguyên tắc đọc chung

- Thứ tự luôn: **SLI → số người đánh giá → chỉ số**. Đây là giao thức audit 3 bước, đóng góp Methods của đề tài.
- Phân biệt: "điểm cao hơn trên mẫu khác" (cùng mô hình, đổi split) ≠ "tốt hơn" (cùng split/seed/ngân sách, có kiểm định) ≠ "khác biệt có ý nghĩa thống kê" (p<0,05 hoặc 95% CI không chứa 0).
- Mọi số kèm tên split + seed 42. Một đường số duy nhất: ALS `0,2581 → 0,1332 → 0,0469`. Không đọc `0,2584 / 0,0474`.
- `8,76%` = dòng test trỏ tới phim **chưa từng có trong train**, không phải "user chưa chấm phim đó".
- SLI là chỉ số **đề tài đề xuất**; TOIS 41(3) chỉ khuyến nghị quan sát timeline toàn cục, không đưa công thức SLI. Ngưỡng `<0,05 / 0,30` do đề tài chọn.

## Slide 1 — Tiêu đề

**Nói:** "Thưa thầy và các anh chị, em là Trần Khôi Nguyên, MIT26004. Đề cương: *Phân tích rò rỉ, thiên lệch phổ biến trong hệ thống gợi ý bằng kiểm toán chiến lược chia tập trên Spark*. GVHD: TS. Trần Minh Thái. Vào: một bảng chấm 25 triệu dòng. Ra: một phiếu chẩn đoán cho từng cách chia dữ liệu. Em trình bày 20 slide."

**Khái niệm:** Tiêu đề = [Phương pháp] + [Mục tiêu] + [Phạm vi]. Không đặt tên mô hình mới. Đóng góp là cách kiểm tra, không phải mô hình mới.

## Slide 2 — Bố cục

**Nói:** "Bốn phần. Phần 1: dữ liệu, DIKW và 3 cách tư duy, 20%. Phần 2: tài liệu, ma trận, khoảng trống, 30%. Phần 3: mục tiêu, quy trình, chỉ số, thực nghiệm, 45%. Kết luận 5%, rồi Q&A."

**Khái niệm:** 20/30/45/5 theo HD slide 2. Phần 3 chiếm nhiều thời gian nhất vì chứa kết quả sơ bộ.

## Slide 3 — DIKW

**Nói:** "**Data**: 25.000.095 lượt chấm, 162.541 người, 59.047 phim, 1995–2019. Mỗi dòng có userID, movieID, rating, timestamp. **Information**: 0 dòng trùng, nhưng 1.799.454 nhóm người chấm cùng 1 giây; 8,76% dòng test trỏ tới phim chưa từng có trong train. **Knowledge**: cùng ALS, đổi cách chia làm NDCG@10 rớt 0,2581 → 0,0469, khoảng 5,5 lần. **Wisdom**: đo SLI trước, báo số người và seed, rồi mới đọc điểm; lệch mẫu quá 1,20 lần thì nói 'điểm cao hơn', không nói 'tốt hơn'."

**Khái niệm:** Data = sự kiện thô. Information = dữ liệu có ngữ cảnh. Knowledge = quy luật lặp lại. Wisdom = quyết định có trách nhiệm. 1.799.454 nhóm cùng giây là độ chi tiết của timestamp, không phải trùng dòng. Số user ALS: 158.626 / 6.214 / 95.977; không dùng 158.688 / 6.219 / 96.003 (đó là của Popularity).

## Slide 4 — Cách tư duy áp dụng

**Nói:** "**Diễn dịch**: nghiên cứu 2022 gợi ý cần cùng mốc thời gian → em áp xuống MovieLens → thấy random rò rỉ 98,91% theo từng người, giữ lượt cuối 0%, một trường hợp ngược đủ sửa cách hiểu cũ. **Quy nạp** là cách chính: 3 cách chia × 5 mô hình × 25 triệu dòng → rút ra quy luật 'hỏi cách đo trước, tin số sau'. **Suy đoán**: thấy điểm nhảy 0,2581 → 0,0469 → đoán có rò rỉ → đếm lại và thấy 98,91% dòng test cũ hơn lượt mới nhất của chính user đó."

**Khái niệm:** Diễn dịch = tổng quát → cá biệt. Quy nạp = nhiều quan sát → quy luật. Suy đoán = hiện tượng lạ → giả thuyết → kiểm chứng. Phản chứng là bước kiểm chứng thêm, **không phải phương pháp thứ 4**. 98,91% là SLI tương đối; tính gộp toàn cục là 100%. Giữ cuối: tương đối 0%, toàn cục 99,9988%.

## Slide 5 — Sáu câu hỏi W5H2

**Nói:** "**What**: 3 cách chia tác động đến tín hiệu đo và thiên lệch. **Who**: người đọc kết quả; user xem ít phim dễ bị che. **Where/When**: Spark trên máy cá nhân, phim 1995–2019. **Why**: chia sai → rò rỉ → kết luận sai → chọn sai mô hình. **How much**: ALS 0,2581 khi trộn ngẫu nhiên, 0,0469 khi giữ lượt cuối, chênh 5,5 lần. **How**: 3 cách chia × 5 mô hình × 6 nhóm chỉ số, đọc SLI → số người → điểm."

**Khái niệm:** W5H2 khóa phạm vi, tránh câu hỏi mồ côi. "6 nhóm chỉ số", không phải "6 chỉ số".

## Slide 6 — Đầu vào là gì

**Nói:** "Đầu vào có đúng một thứ: bảng chấm MovieLens 25M. Bốn cột: ai chấm, phim nào, mấy sao, lúc nào. 25.000.095 dòng, 162.541 người, 59.047 phim, từ 1995 đến 2019. Không dùng ảnh, không dùng text review, không thêm metadata ngoài bốn cột này. Ngưỡng liên quan: rating ≥ 4."

**Khái niệm:** Bắt buộc trích Harper & Konstan, TIST 5(4), 2015, DOI `10.1145/2827872` theo license GroupLens. Dữ liệu ẩn danh. timestamp là mốc để tính rò rỉ.

## Slide 7 — Đầu ra là gì

**Nói:** "Đề tài trả ra bốn vật thể, đều có tên. O1: `audit_report.json` — phiếu chẩn đoán, mỗi cách chia một dòng, có SAFE/WARN/BLOCK kèm lý do. O2: `src/audit/leakage.py` — thước đo SLI theo từng người. O3: giao thức 3 bước — SLI, số người, rồi mới kết luận. O4: pipeline chạy lại được gồm `scripts/`, `runs/` và Streamlit. Nói đơn giản: bài phân loại ảnh trả một nhãn cho mỗi ảnh; đề tài này trả một nhãn cho mỗi cách chia."

**Khái niệm:** `audit_report.json` nằm trong `docs/Project/Main/Presentation/Slides/`, sinh thật từ `runs/` bằng `scripts/19_audit_report.py`. Hiện cả 3 cách chia đều `BLOCK` khi đem so sánh chéo; riêng SLI: random BLOCK, temporal SAFE, giữ cuối SAFE.

## Slide 8 — Kiểm tra tài liệu

**Nói:** "Tải 14 bài, giữ 10 bài Nhóm A để làm phần gap: 9 bài CORE A/A*, 1 bài Q1. Không có bài arXiv làm trích dẫn chính. Thêm 3 bài Nhóm B là bài gốc của mô hình, đã verify DOI ngày 24/11/2026 trên Crossref: Sarwar WWW 2001, Hu ICDM 2008, Kang–McAuley ICDM 2018. Tổng 13 bài. Random và MostPopular không có bài gốc riêng, em khai báo là sàn tầm thường."

**Khái niệm:** CORE xếp hội nghị A*/A/B/C; SJR xếp tạp chí Q1–Q4. Không viết "A* = Q1". Mọi DOI tra `api.crossref.org` trước khi ghi; bản arXiv bị loại.

## Slide 9 — Mô hình đối chuẩn đi với bài nào

**Nói:** "ItemKNN kinh điển đi với Sarwar, WWW 2001. ALS đi với Hu, Koren, Volinsky, ICDM 2008. SASRec đi với Kang và McAuley, ICDM 2018; phần huấn luyện full-catalog CE lấy từ bài RecSys '25. Daniil TORS 2024 dùng cả ItemKNN lẫn MostPopular làm baseline. Random và MostPopular: không viện dẫn, chỉ là sàn."

**Khái niệm:** `[1]` và `[3]` dùng SASRec làm baseline, nên trích `[3]` cho cấu hình CE, trích bài ICDM 2018 cho kiến trúc. Không nhầm "tái lập bài báo" với "dùng mô hình của bài báo". DOI đầy đủ ở phụ lục A4.

## Slide 10 — Bài trước làm được gì, còn thiếu gì

**Nói:** "Ji TOIS 41(3) cho SASRec NDCG@20 dao động −5,4% đến +16,8% khi đưa thêm dữ liệu tương lai; trên Yelp là −29,0% đến −0,6%. Daniil TORS 2(1) đo NeuMF đẩy item niche gấp khoảng 4 lần, %ΔGAP 399,1 và 399,6. Gusak RecSys '25 khảo sát 75 bài thì 77,3% dùng giữ lượt cuối; Beauty NDCG@10 đi từ 0,022 lên 0,040, tức +81,8%. Meng RecSys '20 đo NMF 0,0879 → 0,1811, gấp 2,06. Parajuli RecSys '26 cho Kendall τ chỉ 0,03–0,28, nhiều CI chứa 0. Đề tài đo được 5,5 lần trên ALS."

**Khái niệm:** Mọi bài đều dùng ≥ 3 mô hình, đề tài dùng 5 là hợp lệ. Con số cùng chiều: đổi cách chia thì điểm đổi 1,9–2,1 lần hoặc thứ hạng không khớp. Không bài nào báo chi phí vận hành hay SLI riêng từng người — đó là chỗ đề tài làm tiếp.

## Slide 11 — Khoảng trống

**Nói:** "Ba cái còn thiếu. Một: chưa ai đo rò rỉ riêng từng người; Ji tính gộp cả bảng test, đề tài thêm SLI cho từng người. Hai: chưa ai báo thời gian cạnh điểm số; đề tài ghi giây cho từng mô hình trên cùng máy. Ba: chưa ai so số người trước khi so điểm; lệch quá 1,20 lần thì dừng, không nói 'tốt hơn'. Cần một phiếu chẩn đoán cho mỗi cách chia: rò rỉ bao nhiêu, bao nhiêu người được chấm, rồi mới kết luận."

**Khái niệm:** Gap 3 phần Known / Critical Gap / Proposed, bản chính 237 từ trong `07_Gap...md`. Đề tài không nhận mô hình mới, không nhận miền dữ liệu mới.

## Slide 12 — Mục tiêu và câu hỏi

**Nói:** "Mục tiêu chung: đo và giải thích cách chia dữ liệu đổi tín hiệu đo và thiên lệch trên Spark, MovieLens 25M. Câu hỏi chính: đổi cách chia thì điểm và độ thiên lệch đổi bao nhiêu khi dữ liệu, seed 42 và ngân sách chỉnh giữ nguyên. Bốn mục tiêu: SO1 dữ liệu 20%, SO2 thước đo 40%, SO3 đối chuẩn 20%, SO4 độ nhạy 20%. SO2 nặng nhất vì chứa SLI và giao thức 3 bước. RQ1 hỏi thứ hạng, RQ2 hỏi độ phủ, RQ3 hỏi chi phí, RQ4 hỏi giao thức. RQ5 sang dataset khác để mở rộng, chưa cam kết."

**Khái niệm:** H0: phân bố NDCG@10 không khác nhau giữa các split. H1: có khác nhau. Bác bỏ khi p<0,05. Wilcoxon từng cặp, Friedman khi k≥3. Biến độc lập = chiến lược chia; biến phụ thuộc = NDCG@10, coverage, Gini; biến kiểm soát = seed 42, ngân sách chỉnh.

## Slide 13 — FINER

**Nói:** "**Làm được**: dữ liệu đã tải, thử nghiệm chạy xong trước hạn. **Đáng hỏi**: hỏi 'cách đo đúng chưa' quan trọng hơn 'ai cao hơn'. **Có mới**: giữ lượt cuối, tính gộp là 99,9988%, tính riêng từng người là 0%. **Đạo đức**: dữ liệu ẩn danh, trích Harper & Konstan. **Liên quan**: đóng góp là giao thức đánh giá, dùng được cho mọi dataset cótimestamp."

**Khái niệm:** FINER = Feasible, Interesting, Novel, Ethical, Relevant. 99,9988% là **số đo của đề tài**, không phải trích TOIS. SLI và ngưỡng do đề tài đề xuất.

## Slide 14 — Quy trình chạy thật

**Nói:** "Bốn tầng. Tầng 1: CSV 25M sang Parquet, Spark đọc. Tầng 2: MapReduce Java đếm 323.737 khóa phổ biến; PySpark local[4] tạo 3 cách chia. Tầng 3: MongoDB lưu 42 trường cho mỗi lần audit. Tầng 4: R và Streamlit, Wilcoxon từng người. Bên trái sơ đồ là INPUT, bên phải là OUTPUT. MapReduce chạy SUCCESS, G3 đối chiếu đúng 100%, 10/10 gate PASS."

**Khái niệm:** Mỗi lần chạy ghi log + JSON + manifest: Spark 4.2.0, checksum, tham số, thời gian. Seed 42; không dùng hàm random không seed. SASRec chạy riêng trên GPU RTX 4050, không so thời gian với CPU.

## Slide 15 — Cách đo rò rỉ và độ đúng

**Nói:** "SLI tương đối lấy từng user: trong số dòng test của user đó, có bao nhiêu dòng cũ hơn lượt mới nhất mà mô hình từng thấy. Cùng timestamp thì không tính là rò rỉ; dùng dấu nhỏ hơn. Công thức: SLI_u = số dòng test rò rỉ của u chia số dòng test của u; SLI là trung bình trên mọi user. Ba ngưỡng: dưới 0,05 an toàn, 0,05 đến 0,30 nhẹ, từ 0,30 nặng. Độ đúng dùng NDCG@10 = DCG chia IDCG, chiết khấu log₂(rank+1)."

**Khái niệm:** Công thức toàn cục SLI_global lấy mốc T_max của toàn train, cho kết quả ngược ở giữ lượt cuối. Ngưỡng 0,05 / 0,30 do đề tài chọn từ số liệu đo được, không phải chuẩn công bố. TOIS 41(3) không đưa công thức SLI.

## Slide 16 — Năm mô hình dùng để thử

**Nói:** "Hai sàn: Random chọn ngẫu nhiên trong catalog, MostPopular chọn phim nhiều chấm nhất. Hai kinh điển: ItemKNN tìm phim giống phim đã thích, 100 hàng xóm cosine; ALS học từ lịch sử chấm ẩn, rank 16, alpha 10. Một đối chuẩn mới: SASRec + CE đoán phim tiếp theo bằng self-attention, độ dài 50, 1 block, 1 head, lr 0,001. Cùng k=10, seed 42, rating ≥4 là liên quan. Bốn mô hình chạy Spark CPU; SASRec chạy RTX 4050 6 GB."

**Khái niệm:** SASRec là tầng SOTA đối chuẩn, chạy lại với `tuning_budget=0`, **không phải mô hình thắng**. Không dùng EASE, không so thời gian CPU với GPU, không nhận tái lập SOTA đầy đủ.

## Slide 17 — Kết quả: chia khác, điểm đổi

**Nói:** "Số thật ngày 20/11/2026. ItemKNN 0,2679 / 0,1409 / 0,0461. ALS 0,2581 / 0,1332 / 0,0469. SASRec 0,0163 / 0,0187 / 0,0067. MostPopular 0,0852 / 0,0455 / 0,0183. Random 0,0003 / 0,0009 / 0,0001. Giữ lượt cuối: tính gộp 99,9988%, riêng từng người 0% — hai cách đếm cho kết luận ngược nhau. Phiếu chẩn đoán: trộn ngẫu nhiên BLOCK vì SLI 98,92%; theo mốc thời gian BLOCK vì chỉ 6.214 người, ít hơn 25,5 lần; giữ cuối BLOCK khi đem so sánh vì 95.977 người, ít hơn 1,65 lần."

**Khái niệm:** Cột SLI và số người đứng trước cột điểm. ItemKNN−ALS ở giữ lượt cuối: p=0,153, CI [−0,0003, 0,0018] chứa 0 → không kết luận khác biệt. SASRec thấp là điều kiện GPU local + 1 seed + tuning_budget=0, không phải bằng chứng SOTA yếu. Bảng đầy đủ ở A1, 20 cặp kiểm định ở A2.

## Slide 18 — Hiệu quả, rủi ro, kế hoạch

**Nói:** "Cách làm chặn sai sớm: một phiếu mất khoảng 2 phút; 3/3 cặp chia lệch quá 1,20 lần; chỉ được nói 'điểm cao hơn trên mẫu khác'. Kết quả gồm SLI, giao thức 3 bước và pipeline chạy lại được. Rủi ro có dự phòng: mới 1 seed thì nói rõ giới hạn, hạ tầng lỗi thì giữ Spark trên máy, thiếu thời gian thì bỏ RQ5. Kế hoạch: 11/2026 xong 5 mô hình; 01/2027 xong kiểm định; 02/2027 nháp báo cáo; 03/2027 phản biện; 06/2027 bảo vệ."

**Khái niệm:** Ngưỡng 1,20 = max(n1,n2)/min(n1,n2) > 1,20 thì cấm so trực tiếp. ROI ở đây là lợi ích giải thích trên mỗi phút tính. Máy: i7-13620H, 32 GB, RTX 4050 6 GB, không cloud.

## Slide 19 — Tự đánh giá và giới hạn

**Nói:** "Hợp lệ: dữ liệu ẩn danh, có nguồn, kiểm tra sha256. Chạy thật: PySpark, MapReduce, MongoDB, R, Streamlit. Rõ ràng: RTX 4050 6 GB, G1–G5 đến 06/2027. Giới hạn nói thẳng: local[4] không phải cụm, container MapReduce đã gỡ, mới 1 seed, không báo Mean±Std, không so thời gian CPU với GPU, không đo bộ nhớ, không chạy Nemenyi, chưa đo 'bất ngờ' vì thiếu mô hình mốc."

**Khái niệm:** Bốn nhóm an toàn: dữ liệu, thiết kế, đo lường, thống kê — mới đáp ứng một phần. SASRec đã reproduce 3 split với 1 seed; không có bản nhiều seed.

## Slide 20 — Hỏi và đáp + tài liệu

**Nói:** "Em xin kết thúc phần trình bày, mời thầy và các anh chị đặt câu hỏi. Tài liệu gồm 13 bài: 10 bài Nhóm A về đánh giá/chia tập, 3 bài Nhóm B là bài gốc mô hình. Nguồn dữ liệu: Harper & Konstan 2015."

**5 câu chuẩn bị sẵn:**

| Hỏi | Trả lời |
|---|---|
| Tính mới là gì, có phải mô hình mới? | Không. Mới ở SLI tương đối + giao thức 3 bước. Giữ lượt cuối: gộp 99,9988%, riêng từng người 0%. |
| 1 seed đủ tin? | Chưa; em khai báo giới hạn. Mọi chênh có Wilcoxon + 95% CI + rank-biserial r, không báo Mean±Std bừa. |
| Sao Wilcoxon không dùng t-test? | Hiệu số NDCG cùng user không đảm bảo chuẩn; Wilcoxon xếp hạng \|d\|, chịu ngoại lai tốt hơn. k≥3 → Friedman. |
| SASRec thấp, SOTA hư à? | Không. GPU local, seed 42, tuning_budget=0; em gọi là đối chuẩn, không phải mô hình thắng. |
| Sao không so trực tiếp 3 split? | Giao thức Bước 3 chặn: 25,5× / 1,65× / 15,4× > 1,20. Chỉ nói "điểm cao hơn trên mẫu khác". |

## Nguồn đối chiếu

- `docs/Project/Main/Presentation/Plans/Plan.md` §9 — cấu trúc chốt 20 slide + 4 phụ lục.
- `docs/Project/Plans/Research/08_Tao_tac_SLI_va_giao_thuc_audit.md` — SLI, ngưỡng, giao thức 3 bước.
- `docs/Project/Plans/Research/05_Ke_hoach_thuc_nghiem.md` — ma trận, baseline, kiểm định.
- `docs/Project/Plans/Research/07_Gap_3_phan_Known_CriticalGap_Proposed.md` — Known/Gap/Proposed.
- `docs/Project/Plans/Research/03_Tai_lieu_tham_khao.md` — 10 bài Nhóm A + 3 bài Nhóm B.
- `docs/Project/Main/Presentation/Slides/audit_report.json` — phiếu chẩn đoán sinh thật.
