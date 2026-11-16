# -*- coding: utf-8 -*-
"""Sinh 15 slide thuyết trình PPNCKH theo docs/Project/Main/Presentation/Plans/00_Slide_Plan.md."""
import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

BASE = r"D:\Master Exers\Big Data\Recomendation_System"
FIGS = rf"{BASE}\docs\Project\Main\Presentation\Slides\figures"
OUT = rf"{BASE}\docs\Project\Main\Presentation\Slides\PPNCKH_DeCuong_15slides.pptx"
N_SLIDES = 15

DARK = RGBColor(0x1F, 0x29, 0x37)
ACCENT = RGBColor(0x1A, 0x56, 0xDB)
GREY = RGBColor(0x4B, 0x55, 0x63)
BG = RGBColor(0xFF, 0xFF, 0xFF)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
TITLE_ONLY = prs.slide_layouts[5]


def add_slide(title=None, section=None, number=True):
    s = prs.slides.add_slide(BLANK)
    idx = len(prs.slides._sldIdLst)
    if title:
        tb = s.shapes.add_textbox(Inches(0.55), Inches(0.28), Inches(12.2), Inches(0.85))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        r = p.add_run(); r.text = title
        r.font.size = Pt(30); r.font.bold = True; r.font.color.rgb = ACCENT
    if section:
        sb = s.shapes.add_textbox(Inches(0.55), Inches(0.92), Inches(12.2), Inches(0.4))
        p = sb.text_frame.paragraphs[0]
        r = p.add_run(); r.text = section
        r.font.size = Pt(15); r.font.italic = True; r.font.color.rgb = GREY
    if number:
        nb = s.shapes.add_textbox(Inches(12.35), Inches(7.05), Inches(0.85), Inches(0.35))
        p = nb.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.RIGHT
        r = p.add_run(); r.text = f"{idx} / {N_SLIDES}"
        r.font.size = Pt(12); r.font.color.rgb = GREY
    return s


def bullets(slide, items, left=0.55, top=1.45, width=12.25, height=5.3,
            size=20, line_spacing=1.0):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame; tf.word_wrap = True
    for i, (lvl, txt, bold) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.level = lvl
        p.space_after = Pt(6)
        p.line_spacing = line_spacing
        r = p.add_run(); r.text = txt
        r.font.size = Pt(size - lvl * 2)
        r.font.bold = bold
        r.font.color.rgb = DARK
    return tb


def add_table(slide, data, left, top, width, height, col_widths=None,
              header_size=15, body_size=14):
    rows, cols = len(data), len(data[0])
    shape = slide.shapes.add_table(rows, cols, Inches(left), Inches(top),
                                   Inches(width), Inches(height))
    tbl = shape.table
    if col_widths:
        total = sum(col_widths)
        for i, cw in enumerate(col_widths):
            tbl.columns[i].width = Emu(int(Inches(width) * cw / total))
    for ri, row in enumerate(data):
        for ci, val in enumerate(row):
            cell = tbl.cell(ri, ci)
            cell.text = str(val)
            cell.margin_top = Pt(2); cell.margin_bottom = Pt(2)
            for p in cell.text_frame.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(header_size if ri == 0 else body_size)
                    r.font.bold = ri == 0
                    r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF) if ri == 0 else DARK
    return shape


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def footer_note(slide, text, top=6.75):
    tb = slide.shapes.add_textbox(Inches(0.55), Inches(top), Inches(12.2), Inches(0.55))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = text
    r.font.size = Pt(14); r.font.italic = True; r.font.color.rgb = GREY


def di_table(slide, pairs, left=0.55, top=1.5, width=12.25, row_h=None):
    data = [["Tầng", "Áp dụng vào đề tài"]] + [[a, b] for a, b in pairs]
    add_table(slide, data, left, top, width, 4.9, col_widths=[1.6, 10.6],
              header_size=16, body_size=15)


# ============ SLIDE 1 — tiêu đề ============
s = add_slide(number=True)
tb = s.shapes.add_textbox(Inches(0.8), Inches(2.0), Inches(11.7), Inches(3.2))
tf = tb.text_frame; tf.word_wrap = True
p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
r = p.add_run()
r.text = ("Phân tích rò rỉ, thiên lệch phổ biến trong hệ thống gợi ý\n"
          "bằng kiểm toán chiến lược chia tập trên Spark")
r.font.size = Pt(34); r.font.bold = True; r.font.color.rgb = ACCENT
p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER; p2.space_before = Pt(24)
r2 = p2.add_run()
r2.text = ("*Kiểm toán chiến lược chia tập* → *đánh giá tín hiệu đo và thiên lệch phổ biến* → "
           "*hệ thống gợi ý trên Big Data Spark/HDFS, MovieLens 25M*")
r2.font.size = Pt(18); r2.font.italic = True; r2.font.color.rgb = GREY
p3 = tf.add_paragraph(); p3.alignment = PP_ALIGN.CENTER; p3.space_before = Pt(30)
r3 = p3.add_run()
r3.text = "Sinh viên: [tên]  ·  GVHD: TS. [tên]\nHUFLIT — Phương pháp nghiên cứu khoa học · 11/2026"
r3.font.size = Pt(17); r3.font.color.rgb = DARK
notes(s, "Chào hội đồng. Em trình bày đề cương đề tài: Phân tích rò rỉ, thiên lệch phổ biến "
         "trong hệ thống gợi ý bằng kiểm toán chiến lược chia tập trên Spark. "
         "Tiêu đề theo công thức [phương pháp] + [mục tiêu] + [phạm vi]. "
         "Đề tài phục vụ đồng thời môn Big Data và môn Phương pháp nghiên cứu khoa học.")

# ============ SLIDE 2 — bố cục ============
s = add_slide("Bố cục trình bày")
add_table(s, [
    ["Phần", "Nội dung", "Tỷ trọng"],
    ["CHƯƠNG 1 — Cơ sở lý thuyết", "DIKW & phương pháp tư duy áp dụng vào đề tài", "20%"],
    ["CHƯƠNG 2 — Bài toán & Tài liệu", "W5H2 · thu thập & độ uy tín 14 bài · ma trận tổng hợp + gap", "30%"],
    ["CHƯƠNG 3 — Đề cương chi tiết", "GO/SO-RQ · FINER · quy trình · chỉ số & baseline · kết quả sơ bộ · ROI & kế hoạch", "45%"],
    ["KẾT LUẬN", "Tự đánh giá khả thi & giới hạn", "5%"],
], 0.7, 1.55, 11.9, 3.4, col_widths=[2.6, 7.4, 1.4], header_size=16, body_size=15)
footer_note(s, "Thời lượng: ~12 phút trình bày + 5–8 phút Q&A.")
notes(s, "Bố cục bám đúng tỷ trọng của file hướng dẫn: C1 20%, C2 30%, C3 45%, KL 5%. "
         "Phần nặng nhất là Chương 3 — thiết kế nghiên cứu.")

# ============ SLIDE 3 — DIKW ============
s = add_slide("DIKW áp dụng vào đề tài", "Chương 1 — không nhắc lại định nghĩa, đi thẳng vào đóng góp")
di_table(s, [
    ("Data", "25.000.095 tương tác (userId, movieId, rating, timestamp) — MovieLens ml-25m, 1995–2019"),
    ("Information", "Thống kê đo thật: 0 cặp trùng · 1.799.454 nhóm timestamp ties · unseen-item 8,76% (temporal)"),
    ("Knowledge", "Quy luật: rò rỉ phải đo tương đối theo user — đo toàn cục cho kết luận NGƯỢC (LOO: 99,9988% vs 0%)"),
    ("Wisdom", "SLI + giao thức audit 3 bước — công cụ quyết định \"split này có tin được không\" trước khi đọc metric"),
])
footer_note(s, "Không chép định nghĩa lý thuyết — mỗi tầng gắn trực tiếp với dữ liệu/đo thật của đề tài.")
notes(s, "Dữ liệu thô là 25 triệu tương tác. Thông tin là thống kê đo được. Tri thức là quy luật "
         "chúng tôi rút ra: cách đo rò rỉ toàn cục cho kết luận ngược với thực tế với leave-one-out. "
         "Trí tuệ là đóng gói thành công cụ SLI + giao thức audit — người dùng cuối của công cụ là "
         "nhà nghiên cứu RS và doanh nghiệp quyết định triển khai mô hình.")

# ============ SLIDE 4 — phương pháp tư duy ============
s = add_slide("Phương pháp tư duy áp dụng", "Chương 1")
bullets(s, [
    (0, "Phân tích — mổ xẻ 3 chiến lược split × 6 chỉ số trên cùng dữ liệu", True),
    (1, "mỗi split sinh ra bộ số khác nhau trên cùng mô hình, cùng dataset", False),
    (0, "Tổng hợp — chắt lọc quy luật chung thành GIAO THỨC AUDIT 3 bước", True),
    (1, "báo SLI trước metric · báo eval_rel_users song song · chặn so sánh khi mẫu lệch > 20%", False),
    (0, "Quy nạp — từ 25M tương tác về quy luật chung (không suy diễn từ 1 case)", True),
    (1, "khẳng định chỉ trên số đo thật, có manifest + checkpoint truy vết", False),
    (0, "Phản chứng — tư duy phản biện của Popper: 1 phản ví dụ đủ để bác 1 định nghĩa", True),
    (1, "phản ví dụ LOO: định nghĩa toàn cục gán 99,9988% rò rỉ trong khi thực tế là 0%", False),
])
notes(s, "Bốn phương pháp tư duy, mỗi cái gắn một sản phẩm cụ thể của đề tài. "
         "Phản chứng là điểm mạnh nhất: một phản ví dụ đủ để bác định nghĩa toàn cục — "
         "đây là tư duy Popper, không phải ý kiến chủ quan.")

# ============ SLIDE 5 — W5H2 ============
s = add_slide("Phân tích bài toán theo W5H2", "Chương 2")
add_table(s, [
    ["", "Nội dung"],
    ["WHAT", "Chiến lược chia tập (random 80/20 · temporal · leave-one-out) tác động đến tín hiệu đo + thiên lệch"],
    ["WHO", "Nhà nghiên cứu RS dùng đánh giá offline; user long-tail bị che khuất"],
    ["WHERE / WHEN", "Pipeline Spark/HDFS cục bộ; dữ liệu phim 1995–2019; nghiên cứu 11/2026–06/2027"],
    ["WHY", "Split sai → rò rỉ → kết luận sai → quyết định triển khai sai"],
    ["HOW MUCH", "ALS NDCG 0,2556 (random) → 0,0467 (LOO): chênh 5,5× trên cùng mô hình, cùng dữ liệu"],
    ["HOW", "Audit 3 split × 2+ model × 6 metric trên 25M tương tác"],
], 0.6, 1.4, 12.1, 4.6, col_widths=[2.0, 10.1], header_size=16, body_size=15)
notes(s, "Chuỗi phát biểu vấn đề: Thực trạng — đa số đánh giá trên random 80/20 chưa được kiểm chứng. "
         "Hậu quả — NDCG phóng đại ảo, thứ hạng có thể đảo chiều. Hạn chế tài liệu — đo từng khía cạnh "
         "riêng lẻ, không biết hiệu ứng cộng hưởng hay triệt tiêu. Giải pháp — SLI + giao thức audit.")

# ============ SLIDE 6 — quản lý tài liệu + uy tín ============
s = add_slide("Quản lý tài liệu & đánh giá độ uy tín", "Chương 2 — 14 bài, bản nhà xuất bản (không arXiv)")
add_table(s, [
    ["Nhóm tạp chí / hội nghị", "SCImago", "CORE", "Số bài"],
    ["ACM TOIS / TORS (Trans. Information Systems, Rec. Systems)", "Q1", "A", "4"],
    ["ACM RecSys ('25, '26, '23, '21, '20)", "Q1", "A*", "5"],
    ["ACM SIGIR '23", "Q1", "A*", "1"],
    ["Springer UMAI 2024 / J. Big Data 2019", "Q1", "—/C", "2"],
    ["Elsevier ESWA 2023", "Q1", "B", "1"],
], 0.6, 1.5, 7.6, 3.3, col_widths=[4.4, 1.1, 1.0, 1.0], header_size=14, body_size=13)
# cột phải: minh chứng
tb = s.shapes.add_textbox(Inches(8.5), Inches(1.5), Inches(4.3), Inches(4.6))
tf = tb.text_frame; tf.word_wrap = True
for i, (h, t) in enumerate([
        ("Minh chứng kiểm tra", "• 14/14 PDF là bản nhà xuất bản (verify /Creator: acmart · Springer · Elsevier)"),
        (None, "• 10/14 có DOI ACM DL; 9 bài CORE A*/A"),
        (None, "• Đã loại arXiv-only: 10.48550/arxiv.2011.07931 (không có bản tạp chí)"),
        (None, "• Think–Check–Submit: DOI resolve được; footer bản quyền ACM/Springer/Elsevier trên PDF"),
        (None, "• Manifest truy vết: _manifest.json (sha256 từng file, provenance từng bài)"),
        (None, "• Zotero/Mendeley: phân nhóm thẻ — leakage (5), bias (6), split (2), Big Data (2)"),
]):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.space_after = Pt(5)
    r = p.add_run(); r.text = t
    r.font.size = Pt(13 if i > 0 else 15)
    r.font.bold = i == 0
    r.font.color.rgb = ACCENT if i == 0 else DARK
footer_note(s, "Ảnh chụp trang PDF từng bài (header ACM + DOI) có trong phần phụ lục / file nộp kèm.")
notes(s, "Quy trình: (1) thu thập qua DOI từ OpenAlex/Unpaywall; (2) chỉ lấy bản nhà xuất bản, "
         "không preprint arXiv; (3) verify /Creator bằng pypdf để chắc bản thật; (4) tra SCImago + CORE; "
         "(5) ghi manifest với sha256. Kết quả: 14 bài, tất cả ≥ Q1 hoặc CORE B, 9 bài A*/A. "
         "Hội đồng có thể yêu cầu xem ảnh chụp — đã chuẩn bị 14 thumbnail trang đầu trong phụ lục.")

# ============ SLIDE 7 — ma trận tổng hợp ============
s = add_slide("Ma trận tổng hợp & khoảng trống nghiên cứu", "Chương 2")
add_table(s, [
    ["Tài liệu", "Phương pháp", "Kết quả", "Hạn chế → gap"],
    ["Wang et al. TOIS 2022 (Q1)", "So sánh protocol có/không global timeline; 4 model DL", "Leakage đổi accuracy + thứ hạng", "Chưa định nghĩa CHỈ SỐ đo rò rỉ"],
    ["Abdollahpouri et al. TOIS 2023 (Q1)", "Tách 4 yếu tố: data/algorithm/group/eval", "Eval strategy giải thích mâu thuẫn bias", "Chưa gắn quy mô Big Data"],
    ["Chen et al. RecSys '25 (A*)", "SASRec+/BERT4Rec/GRU4Rec × 8 dataset", "Split đổi thứ hạng sequential", "Chỉ sequential RS; cần H100 GPU"],
    ["RecSys '26 (A*)", "Convergent validity của thiết kế offline", "Sparse ranking ≠ dense judgment", "Chưa đo coverage/bias kèm rank"],
    ["RecSys '20 (A*)", "So sánh split strategies", "Split là lựa chọn thiết kế", "Tiền thân, quy mô vừa"],
], 0.45, 1.45, 12.45, 3.5, col_widths=[2.6, 3.4, 3.0, 3.0], header_size=13, body_size=12)
footer_note(s, "Khoảng trống: CHƯA có nghiên cứu nào đo ĐỒNG THỜI (i) đảo chiều thứ hạng, "
               "(ii) mức biến mất của thiên lệch phổ biến, (iii) chi phí Big Data — trên CÙNG pipeline. "
               "Đo riêng lẻ thì không biết các hiệu ứng CỘNG HƯỞNG hay TRIỆT TIÊU nhau.")
notes(s, "5 bài trung tâm. Điểm giao: gap là phép HOẶC của 3 hạn chế — không bài nào đo cả ba hiệu ứng "
         "trên cùng pipeline. Đây là chỗ đề tài chèn vào. Khoảng trống phát hiện từ 2 nguồn: "
         "thực tiễn doanh nghiệp (W5H2) và khảo sát tài liệu (hạn chế của từng bài).")

# ============ SLIDE 8 — tiêu đề, GO/SO, RQ ============
s = add_slide("Tiêu đề, mục tiêu và câu hỏi nghiên cứu", "Chương 3")
tb = s.shapes.add_textbox(Inches(0.55), Inches(1.35), Inches(12.2), Inches(1.0))
tf = tb.text_frame; tf.word_wrap = True
p = tf.paragraphs[0]
r = p.add_run()
r.text = ("Tiêu đề = [Phương pháp] + [Mục tiêu] + [Phạm vi]:  Kiểm toán chiến lược chia tập → "
          "đánh giá tác động đến tín hiệu đo & thiên lệch phổ biến → hệ thống gợi ý trên Big Data Spark/HDFS, MovieLens 25M")
r.font.size = Pt(15); r.font.bold = True; r.font.color.rgb = DARK
add_table(s, [
    ["SO", "Mục tiêu cụ thể", "Tỷ trọng", "RQ khớp"],
    ["SO1 Data", "Chuẩn hoá MovieLens 25M; sinh 3 split; MapReduce Java đếm phổ biến", "20%", "—"],
    ["SO2 Model", "Đề xuất SLI (tương đối theo user, 3 ngưỡng) + giao thức audit 3 bước", "40%", "RQ1, RQ2"],
    ["SO3 Đối chuẩn", "Chạy baseline 3 tầng trên 3 split, 3+ seed", "20%", "RQ1"],
    ["SO4 Ablation", "Độ nhạy: đổi ngưỡng relevant, subsample, 2 định nghĩa SLI", "20%", "RQ2, RQ4"],
], 0.55, 2.5, 12.2, 3.2, col_widths=[1.8, 7.6, 1.3, 1.4], header_size=15, body_size=14)
footer_note(s, "RQ1: chiến lược chia có làm đảo chiều thứ hạng mô hình? · RQ2: thiên lệch phổ biến thay đổi bao nhiêu? · "
               "RQ3: chi phí vận hành? · RQ4: có giao thức đánh giá khả thi không? · RQ5 (mở rộng): cross-domain.")
notes(s, "SO2 chiếm 40% — đây là đóng góp tạo tác dạng Model + Method, đáp ứng yêu cầu "
         "đóng góp dạng 2 + 3 của môn. 4 RQ chính + RQ5 là hướng mở rộng, không nằm trong cam kết.")

# ============ SLIDE 9 — FINER ============
s = add_slide("Kiểm tra tính khả thi — FINER", "Chương 3")
add_table(s, [
    ["", "Bằng chứng cụ thể"],
    ["F — Khả thi", "Dataset đã tải + đo; PoC chạy xong trước deadline; khung thực nghiệm có sẵn"],
    ["I — Thú vị", "Trả lời \"cách đo có đúng không\" quan trọng hơn \"model nào tốt hơn\" — ảnh hưởng mọi bài báo RS"],
    ["N — Mới", "SLI — phát hiện khái niệm: LOO toàn cục 99,9988% vs tương đối 0% — chưa có trong TOIS 2022"],
    ["E — Đạo đức", "Dataset ẩn danh, license research-use, trích dẫn Harper & Konstan (10.1145/2827872), không redistribute"],
    ["R — Thiết thực", "Đóng góp là GIAO THỨC đánh giá, không phải model mới — dùng được cho mọi dataset có timestamp"],
], 0.6, 1.45, 12.1, 4.3, col_widths=[1.8, 10.3], header_size=15, body_size=14)
notes(s, "Mỗi ô FINER không nói chung chung — mỗi ô có 1 bằng chứng thật. Điểm N là điểm mạnh nhất: "
         "phát hiện khái niệm chưa có trong bài nổi tiếng nhất về data leakage RecSys.")

# ============ SLIDE 10 — quy trình ============
s = add_slide("Quy trình thực hiện — kiến trúc 4 tầng", "Chương 3 — tất cả đã chạy thật")
s.shapes.add_picture(rf"{FIGS}\fig_architecture.png", Inches(0.9), Inches(1.35), width=Inches(11.5))
footer_note(s, "Đã chạy thật: MapReduce JOB_STATUS=SUCCESS · G3 cross-check PASS 100% (323.737/323.737 key) · "
               "6/6 notebook gate PASS (04–09) · không dùng GPU.")
notes(s, "Bốn tầng: lưu trữ (HDFS + Parquet), xử lý lớn (MapReduce Java + PySpark local[4]), "
         "lưu trữ metric (MongoDB), trực quan (R + Streamlit). Nhấn mạnh MapReduce viết bằng Java "
         "vì container không có Python — đúng yêu cầu seminar. Không dùng GPU — chạy CPU trên laptop.")

# ============ SLIDE 11 — chỉ số + baseline ============
s = add_slide("Chỉ số đánh giá & Baseline", "Chương 3")
bullets(s, [
    (0, "TẦNG DỮ LIỆU — chỉ số mới của đề tài", True),
    (1, "SLI (Split Leakage Index) = trung bình tỷ lệ rò rỉ THEO TỪNG USER, không phải tỷ lệ gộp toàn cục", False),
    (1, "3 ngưỡng: an toàn < 0,05 · rò rỉ nhẹ 0,05–0,30 · nghiêm trọng ≥ 0,30", False),
    (0, "TẦNG RANKING — chỉ số kinh điển", True),
    (1, "NDCG@10 = DCG/IDCG (bị chặn bởi fixture 5 ca tính tay, tolerance 1e-12) · Hit@10", False),
    (0, "TẦNG CÔNG BẰNG — chỉ số thiên lệch", True),
    (1, "catalog coverage · Gini exposure · popularity-bias ratio · longtail_coverage", False),
    (0, "BASELINE 3 TẦNG (bắt buộc) — sàn (MostPopular, Random) · kinh điển (ALS implicit, ItemKNN) · SOTA (SASRec+ hoặc EASE CPU)", True),
], top=1.35)
notes(s, "SLI là chỉ số đề tài đề xuất. NDCG có unit-test với fixture tính tay — bảo đảm công thức "
         "đúng không phụ thuộc code. Baseline 3 tầng là yêu cầu bắt buộc của môn, không được cắt.")

# ============ SLIDE 12 — kết quả sơ bộ ============
s = add_slide("Kết quả sơ bộ — chứng minh khả thi", "Chương 3 — số đo thật, KHÔNG phải kết quả cuối")
s.shapes.add_picture(rf"{FIGS}\fig_sli.png", Inches(1.4), Inches(1.25), width=Inches(10.5))
add_table(s, [
    ["", "random 80/20", "temporal_global", "leave_one_out"],
    ["SLI (tương đối)", "98,91%", "0%", "0%"],
    ["NDCG@10 — ALS", "0,2556", "0,1311", "0,0467"],
    ["eval_rel_users", "158.692", "6.219", "96.003"],
], 0.75, 4.85, 11.8, 1.5, col_widths=[2.6, 3.0, 3.0, 3.0], header_size=13, body_size=13)
notes(s, "3 nhận xét: (1) split cho kết quả đẹp nhất (random) rò rỉ nặng nhất — 98,91% tương tác test "
         "sớm hơn tương tác mới nhất của chính user đó; (2) split sạch nhất (temporal) mất 96,1% mẫu "
         "đánh giá — không có chiến lược miễn phí; (3) thứ hạng không đảo ở 2 mô hình này nhưng độ "
         "lớn hiệu ứng đổi 5,5×. DISCLAIMER bắt buộc đọc: số liệu sơ bộ, seed đơn (42), "
         "method-informed implementation — chứng minh khả thi, không phải kết luận cuối.")

# ============ SLIDE 13 — hiệu quả, ROI, kế hoạch, rủi ro ============
s = add_slide("Hiệu quả, ROI và kế hoạch 5 giai đoạn", "Chương 3")
tb = s.shapes.add_textbox(Inches(0.55), Inches(1.3), Inches(6.1), Inches(5.2))
tf = tb.text_frame; tf.word_wrap = True
for i, (h, t) in enumerate([
        ("Hiệu quả + ROI (định lượng)", "• Giao thức audit tự chặn 3/3 cặp so sánh không hợp lệ (mẫu lệch 25,5× / 1,65× / 15,4× > ngưỡng 1,2)"),
        (None, "• SLI tính được trong ~2 phút cho mọi split mới"),
        (None, "• 3 tạo tác: SLI (Concepts+Models) · giao thức 3 bước (Methods) · pipeline tái lập (Instantiations)"),
        (None, "• Chi phí: 1 laptop, KHÔNG GPU; đầu ra ≥ yêu cầu \"đóng góp dạng 2 + 3\""),
        ("Rủi ro & ứng phó", "• Thiếu GPU cho SOTA → EASE (closed-form, CPU vài phút) — có tiền lệ RecSys '21"),
        (None, "• Hạ tầng lỗi → giữ trục khoa học (PySpark local đọc Parquet) — không mất gì về khoa học"),
        (None, "• Thiếu thời gian → cắt cross-domain (RQ5 thành hướng mở rộng)"),
        (None, "• Seed đơn → khai báo giới hạn rõ trong báo cáo"),
]):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.space_after = Pt(5)
    r = p.add_run(); r.text = t
    r.font.size = Pt(14 if i > 0 else 15)
    r.font.bold = i == 0 or i == 4
    r.font.color.rgb = ACCENT if i in (0, 4) else DARK
add_table(s, [
    ["Giai đoạn", "Nội dung", "Output", "Mốc"],
    ["G1", "Hoàn thiện thực nghiệm (thêm 3 seed, EASE)", "Bảng 3 split × 3 seed", "12/2026"],
    ["G2", "Kiểm định thống kê mở rộng", "CI + Wilcoxon cho mọi cặp", "01/2027"],
    ["G3", "Viết báo cáo + dashboard demo", "Báo cáo nháp + fig9", "02/2027"],
    ["G4", "Phản biện nội bộ + sửa", "Bản cuối", "03/2027"],
    ["G5", "Bảo vệ cuối kỳ", "Slide + demo", "06/2027"],
], 6.9, 1.3, 5.9, 4.0, col_widths=[0.8, 3.0, 2.1, 1.0], header_size=13, body_size=12)
notes(s, "Hiệu quả không nói định tính — có số: giao thức chặn 3/3 cặp so sánh sai. "
         "ROI: chi phí 1 laptop không GPU, đầu ra 3 tạo tác vượt yêu cầu tối thiểu. "
         "Kế hoạch 5 giai đoạn có mốc cụ thể đến 06/2027.")

# ============ SLIDE 14 — tự đánh giá ============
s = add_slide("Tự đánh giá khả thi & giới hạn", "Kết luận")
add_table(s, [
    ["", "Trạng thái"],
    ["Dữ liệu", "✅ hợp pháp, ẩn danh, đã verify SHA-256, license research-use"],
    ["Năng lực kỹ thuật", "✅ PySpark + Hadoop + MapReduce Java + MongoDB + R + Streamlit — tất cả đã chạy thật"],
    ["Nguồn lực & thời gian", "✅ laptop, không GPU; khung PoC có sẵn; G1–G5 đến 06/2027"],
    ["Giới hạn (nói thẳng)", "local[4] không phải cluster · ALS subsample 30k/162.541 user · 1 seed · 2 baseline · NDCG không so cặp giữa split"],
    ["Hướng mở rộng", "Cross-domain (Amazon/Steam) · thêm SOTA · ma trận 10 seed"],
], 0.6, 1.45, 12.1, 4.2, col_widths=[2.4, 9.7], header_size=15, body_size=14)
footer_note(s, "Nói thẳng giới hạn trước khi hội đồng hỏi — đây là phần thể hiện tư duy nghiên cứu nghiêm túc.")
notes(s, "Phần tự đánh giá chiếm 5% thời lượng nhưng quan trọng: nêu thẳng 5 giới hạn. "
         "local[4] là máy đơn, không phải cụm phân tán. ALS chỉ fit trên 30 nghìn user đầu theo userId, "
         "không phải toàn bộ 162 nghìn. Một seed. Hai baseline. NDCG giữa các split không so cặp được "
         "vì tập user khác nhau. Nói rõ trước — hội đồng không thể 'bắt lỗi' thứ đã được khai báo.")

# ============ SLIDE 15 — Q&A + tài liệu tham khảo ============
s = add_slide("Trao đổi và Thảo luận (Q&A)", "Cảm ơn hội đồng")
add_table(s, [
    ["#", "Tài liệu tham khảo (IEEE)"],
    ["[1]", "Y. Wang et al., \"A Critical Study on Data Leakage in Recommender System Offline Evaluation,\" ACM Trans. Inf. Syst., 41(3), Art. 75, 2022. DOI: 10.1145/3569930"],
    ["[2]", "H. Abdollahpouri et al., \"Reproducing Popularity Bias in Recommendation: The Effect of Evaluation Strategies,\" ACM Trans. Recomm. Syst., 2(1), Art. 5, 2023. DOI: 10.1145/3637066"],
    ["[3]", "Y. Chen et al., \"Time to Split: Exploring Data Splitting Strategies for Offline Evaluation of Sequential Recommenders,\" in Proc. RecSys '25, 2025, pp. 874–883. DOI: 10.1145/3705328.3748164"],
    ["[4]", "\"On the Convergent Validity of Offline Evaluation Designs for Recommender Systems,\" in Proc. RecSys '26, 2026. DOI: 10.1145/3773078.3831818"],
    ["[5]", "F. M. Harper and J. A. Konstan, \"The MovieLens Datasets: History and Context,\" ACM Trans. Interact. Intell. Syst., 5(4), Art. 19, 2015. DOI: 10.1145/2827872"],
], 0.5, 1.5, 12.35, 4.2, col_widths=[0.7, 11.6], header_size=14, body_size=12)
footer_note(s, "14 bài đã thu thập (9 bài CORE A*/A, 14 bài ≥ Q1) — manifest + ảnh chụp PDF trong phụ lục.")
notes(s, "Câu hỏi dự phòng hay gặp: "
         "(1) Vì sao LOO không rò rỉ? — vì test của mỗi user là tương tác muộn nhất CỦA USER ĐÓ, "
         "định nghĩa toàn cục lấy mốc của user B so với test của user A là vô nghĩa. "
         "(2) 30 nghìn user subsample có đại diện không? — không hoàn toàn, userId cấp theo thứ tự tham "
         "gia; đã khai báo là giới hạn, không ngoại suy. "
         "(3) local[4] có phải Big Data không? — xử lý 25M tương tác bằng Spark engine là đúng yêu cầu "
         "môn; phần phân tán thật là MapReduce trong Hadoop container (G3 PASS 100%). "
         "(4) Chỉ 2 baseline? — đúng yêu cầu tối thiểu; 3 tầng (sàn/kinh điển/SOTA) là phần G1 giai "
         "đoạn tiếp theo. "
         "(5) Số liệu có ổn định qua seed không? — chưa có bằng chứng; 1 seed đã khai báo giới hạn, "
         "3 seed là G1.")

prs.save(OUT)
print("OK", OUT, os.path.getsize(OUT), "bytes,", len(prs.slides._sldIdLst), "slides")
