# -*- coding: utf-8 -*-
"""
Sinh 15 slide thuyết trình PPNCKH theo docs/Project/Main/Presentation/Plans/00_Slide_Plan.md.
Bản 2026-11-18: thêm checklist bài giảng, bớt thuật ngữ academic trên thân slide,
kiểm soát chữ/overlap bằng helper và kiểm tra geometry sau khi lưu.
"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE


def set_round_rect_adjustments(shape, radius_in):
    """Round only corners; PowerPoint default rounding looks pill-like on tall cards."""
    try:
        avLst = shape._element.spPr.prstGeom.avLst
        for child in list(avLst):
            avLst.remove(child)
        val = int(max(0, min(0.5, radius_in / min(shape.width, shape.height))) * 100000)
        from pptx.oxml.xmlchemy import OxmlElement
        gd = OxmlElement("a:gd")
        gd.set("name", "adj")
        gd.set("fmla", "val %d" % val)
        avLst.append(gd)
    except Exception:
        pass


def add_thinking_card(slide, left, top, width, height, accent, pale,
                      badge, title, steps, examples):
    """Build one visual card from native PPTX shapes; decorative parts are skipped by the overlap check."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top),
                                  Inches(width), Inches(height))
    set_round_rect_adjustments(card, radius_in=0.20)
    card.fill.solid(); card.fill.fore_color.rgb = pale
    card.line.color.rgb = accent; card.line.width = Pt(1.5)
    card.shadow.inherit = False
    card.name = "decor_card_bg"

    head = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                  Inches(left + 0.12), Inches(top + 0.12),
                                  Inches(width - 0.24), Inches(0.78))
    set_round_rect_adjustments(head, radius_in=0.14)
    head.fill.solid(); head.fill.fore_color.rgb = accent
    head.line.fill.background(); head.shadow.inherit = False
    head.name = "decor_card_head"
    htf = head.text_frame; htf.clear(); htf.word_wrap = True
    htf.vertical_anchor = 3  # MIDDLE
    htf.margin_left = htf.margin_right = Inches(0.08)
    htf.margin_top = htf.margin_bottom = Inches(0.04)
    p = htf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER; p.space_after = Pt(1)
    r = p.add_run(); r.text = badge
    r.font.size = Pt(10.5); r.font.bold = True; r.font.name = "Tahoma"; r.font.color.rgb = WHITE
    p = htf.add_paragraph(); p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = title
    r.font.size = Pt(17); r.font.bold = True; r.font.name = "Tahoma"; r.font.color.rgb = WHITE

    for i, step in enumerate(steps):
        chip = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                      Inches(left + 0.18), Inches(top + 1.02 + i * 0.72),
                                      Inches(width - 0.36), Inches(0.62))
        set_round_rect_adjustments(chip, radius_in=0.12)
        chip.fill.solid(); chip.fill.fore_color.rgb = WHITE
        chip.line.color.rgb = accent; chip.line.width = Pt(0.75)
        chip.shadow.inherit = False
        chip.name = "decor_step_chip"
        tf = chip.text_frame; tf.clear(); tf.word_wrap = True
        tf.vertical_anchor = 3
        tf.margin_left = Inches(0.14); tf.margin_right = Inches(0.08)
        tf.margin_top = tf.margin_bottom = Inches(0.03)
        p = tf.paragraphs[0]
        r = p.add_run(); r.text = str(i + 1) + ". " + step
        r.font.size = Pt(11.5); r.font.bold = True; r.font.name = "Tahoma"; r.font.color.rgb = DARK

    ex = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                Inches(left + 0.18), Inches(top + 3.22),
                                Inches(width - 0.36), Inches(1.16))
    set_round_rect_adjustments(ex, radius_in=0.12)
    ex.fill.solid(); ex.fill.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    ex.line.color.rgb = accent; ex.line.width = Pt(0.75)
    ex.shadow.inherit = False
    ex.name = "decor_example_box"
    tf = ex.text_frame; tf.clear(); tf.word_wrap = True
    tf.vertical_anchor = 1  # TOP
    tf.margin_left = Inches(0.14); tf.margin_right = Inches(0.10)
    tf.margin_top = Inches(0.08); tf.margin_bottom = Inches(0.06)
    p = tf.paragraphs[0]; p.space_after = Pt(2)
    r = p.add_run(); r.text = "Ví dụ thật"
    r.font.size = Pt(10.5); r.font.bold = True; r.font.name = "Tahoma"; r.font.color.rgb = accent
    for line in examples:
        p = tf.add_paragraph(); p.space_after = Pt(1); p.line_spacing = 1.0
        r = p.add_run(); r.text = line
        r.font.size = Pt(10.5); r.font.name = "Tahoma"; r.font.color.rgb = DARK
    return card


BASE = r"D:\Master Exers\Big Data\Recomendation_System"
FIGS = rf"{BASE}\docs\Project\Main\Presentation\Slides\figures"
OUT = rf"{BASE}\docs\Project\Main\Presentation\Slides\PPNCKH_DeCuong_15slides.pptx"
N_SLIDES = 15
REPO_URL = "https://github.com/StreetParkourZombie/Recommendation_System"

DARK = RGBColor(0x1F, 0x29, 0x37)
ACCENT = RGBColor(0x1A, 0x56, 0xDB)
GREY = RGBColor(0x4B, 0x55, 0x63)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
NAVY = RGBColor(0x00, 0x33, 0x66)
TITLE_RED = RGBColor(0xC0, 0x00, 0x00)
NAVY_TXT = RGBColor(0x1E, 0x39, 0x89)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
SW = prs.slide_width
SH = prs.slide_height


def add_slide(title=None, section=None, number=True):
    s = prs.slides.add_slide(BLANK)
    idx = len(prs.slides._sldIdLst)
    # Navy header nằm trọn trong slide. Đẩy xuống dưới mọi textbox khác.
    strip = s.shapes.add_shape(1, Inches(0), Inches(0), prs.slide_width, Inches(0.92))
    strip.fill.solid(); strip.fill.fore_color.rgb = NAVY
    strip.line.fill.background()
    strip.shadow.inherit = False
    sp = s.shapes._spTree
    sp.remove(strip._element)
    sp.insert(2, strip._element)
    if title:
        tb = s.shapes.add_textbox(Inches(0.38), Inches(0.08), Inches(12.4), Inches(0.64))
        tf = tb.text_frame; tf.word_wrap = False
        p = tf.paragraphs[0]
        r = p.add_run(); r.text = title
        r.font.size = Pt(30); r.font.bold = True; r.font.name = "Tahoma"; r.font.color.rgb = WHITE
    if section:
        sb = s.shapes.add_textbox(Inches(0.55), Inches(1.00), Inches(12.2), Inches(0.34))
        p = sb.text_frame.paragraphs[0]
        r = p.add_run(); r.text = section
        r.font.size = Pt(13); r.font.italic = True; r.font.color.rgb = GREY
    if number:
        nb = s.shapes.add_textbox(Inches(12.35), Inches(7.05), Inches(0.85), Inches(0.35))
        p = nb.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.RIGHT
        r = p.add_run(); r.text = f"{idx} / {N_SLIDES}"
        r.font.size = Pt(11); r.font.color.rgb = GREY
    return s


def bullets(slide, items, left=0.55, top=1.42, width=12.25, height=5.28,
            size=17, line_spacing=1.0):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame; tf.word_wrap = True
    for i, (lvl, txt, bold) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.level = lvl
        p.space_after = Pt(5 if lvl == 0 else 4)
        p.line_spacing = line_spacing
        r = p.add_run(); r.text = txt
        r.font.size = Pt(max(11, size - lvl * 2))
        r.font.bold = bold
        r.font.color.rgb = DARK
    return tb


def add_table(slide, data, left, top, width, height, col_widths=None,
              header_size=13, body_size=12):
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
            cell.margin_left = Pt(4); cell.margin_right = Pt(4)
            for p in cell.text_frame.paragraphs:
                p.space_after = Pt(0)
                for r in p.runs:
                    r.font.size = Pt(header_size if ri == 0 else body_size)
                    r.font.bold = ri == 0
                    r.font.color.rgb = WHITE if ri == 0 else DARK
    return shape


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def footer_note(slide, text, top=6.72, size=11):
    tb = slide.shapes.add_textbox(Inches(0.55), Inches(top), Inches(12.2), Inches(0.52))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.italic = True; r.font.color.rgb = GREY


def add_pic_caption(slide, png, left, top, width_in, caption, caption_size=9):
    from PIL import Image
    w_px, h_px = Image.open(png).size
    h_in = width_in * h_px / w_px
    slide.shapes.add_picture(png, Inches(left), Inches(top), width=Inches(width_in))
    tb = slide.shapes.add_textbox(Inches(left), Inches(top + h_in + 0.02),
                                  Inches(width_in), Inches(0.30))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = caption
    r.font.size = Pt(caption_size); r.font.color.rgb = GREY
    return top + h_in + 0.34


# ============ SLIDE 1 — tiêu đề ============
s = add_slide(number=True)
tb = s.shapes.add_textbox(Inches(1.39), Inches(1.28), Inches(10.12), Inches(0.70))
tf = tb.text_frame; tf.word_wrap = True
p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
r = p.add_run(); r.text = "HỌC PHẦN: PHƯƠNG PHÁP NGHIÊN CỨU KHOA HỌC TRONG CNTT"
r.font.size = Pt(19); r.font.color.rgb = RGBColor(0x1D, 0x4E, 0xD7)
tb = s.shapes.add_textbox(Inches(0.79), Inches(2.42), Inches(11.69), Inches(1.43))
tf = tb.text_frame; tf.word_wrap = True
p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
r = p.add_run(); r.text = ("Rò rỉ và thiên lệch trong hệ thống gợi ý:\n"
                          "kiểm tra cách chia dữ liệu bằng Spark")
r.font.size = Pt(28); r.font.bold = True; r.font.name = "Tahoma"; r.font.color.rgb = TITLE_RED
tb = s.shapes.add_textbox(Inches(1.39), Inches(5.02), Inches(10.5), Inches(0.70))
tf = tb.text_frame; tf.word_wrap = True
p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
r = p.add_run(); r.text = "Giảng viên: TS. Trần Minh Thái · Khoa CNTT · HUFLIT"
r.font.size = Pt(17); r.font.bold = True; r.font.name = "Arial"; r.font.color.rgb = NAVY_TXT
tb = s.shapes.add_textbox(Inches(1.39), Inches(5.82), Inches(10.5), Inches(0.90))
tf = tb.text_frame; tf.word_wrap = True
p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
r = p.add_run(); r.text = ("Cách chia dữ liệu → thước đo rò rỉ → thiên lệch phổ biến → "
                          "hệ thống gợi ý trên Spark, MovieLens 25M\nSinh viên: Trần Khôi Nguyên (MIT26004) · HUFLIT · 11/2026")
r.font.size = Pt(13); r.font.italic = True; r.font.color.rgb = GREY
notes(s, "Chào hội đồng. Em trình bày đề cương: Rò rỉ và thiên lệch trong hệ thống gợi ý: "
         "kiểm tra cách chia dữ liệu bằng Spark. Tiêu đề gồm phương pháp + mục tiêu + phạm vi. "
         "Đề tài phục vụ môn Phương pháp nghiên cứu khoa học.")

# ============ SLIDE 2 — bố cục ============
s = add_slide("Bố cục trình bày")
add_table(s, [
    ["Phần", "Nội dung", "Tỷ trọng"],
    ["CHƯƠNG 1 — Cơ sở", "Từ dữ liệu đến quyết định: DIKW + cách tư duy", "20%"],
    ["CHƯƠNG 2 — Bài toán & tài liệu", "W5H2 · kiểm tra 14 bài · bảng tổng hợp + khoảng trống", "30%"],
    ["CHƯƠNG 3 — Đề cương", "Mục tiêu · câu hỏi · khả thi · quy trình · chỉ số · kết quả sơ bộ · kế hoạch", "45%"],
    ["KẾT LUẬN", "Tự đánh giá và giới hạn", "5%"],
], 0.7, 1.45, 11.9, 3.05, col_widths=[2.5, 7.8, 1.3], header_size=13, body_size=12)
footer_note(s, "Thời lượng: khoảng 12 phút trình bày + 5–8 phút hỏi đáp.")
notes(s, "Bố cục bám tỷ trọng hướng dẫn: C1 20%, C2 30%, C3 45%, kết luận 5%. Phần nặng nhất là Chương 3.")

# ============ SLIDE 3 — DIKW ============
s = add_slide("Từ dữ liệu đến quyết định", "Chương 1 — có gì → thấy gì → hiểu gì → làm gì")
add_table(s, [
    ["Bước", "Áp dụng vào đề tài"],
    ["Dữ liệu", "25.000.095 lượt chấm phim của 162.541 người (MovieLens ml-25m, 1995–2019). Mỗi dòng: ai chấm, phim nào, mấy sao, lúc nào."],
    ["Thông tin", "Đếm thật: 0 dòng trùng · 1.799.454 nhóm chấm cùng giây · 8,76% phim ở tập kiểm tra là phim người đó chưa từng chấm."],
    ["Hiểu ra", "Cùng ALS, cùng dữ liệu, chỉ đổi cách chia: NDCG@10 từ 0,2581 xuống 0,0469 (thấp hơn 5,5 lần). Số đo phụ thuộc cách chia."],
    ["Quyết định", "Đóng gói thành thước đo rò rỉ SLI + kiểm tra 3 bước: coi SLI trước, đọc chỉ số sau; lệch quá 1,2 lần thì dừng so sánh."],
], 0.55, 1.40, 12.2, 4.42, col_widths=[1.7, 10.5], header_size=14, body_size=12)
footer_note(s, "Đây là ví dụ có số thật của đề tài, không phải ví dụ giả định trong bài giảng.", top=5.98)
notes(s, "Bốn bước: dữ liệu 25 triệu lượt; thông tin đếm được; hiểu ra số đo đổi 5,5 lần; quyết định dùng SLI và kiểm tra 3 bước.")

# ============ SLIDE 4 — phương pháp tư duy ============
s = add_slide("Cách tư duy áp dụng",
              "Chương 1 — cùng một dữ liệu, ba cách nhìn, một cách làm chính")

BLUE = RGBColor(0x1A, 0x56, 0xDB)
BLUE_PALE = RGBColor(0xEC, 0xF3, 0xFF)
TEAL = RGBColor(0x1E, 0x8A, 0x5A)
TEAL_PALE = RGBColor(0xE9, 0xF7, 0xF0)
ORANGE = RGBColor(0xBE, 0x6A, 0x18)
ORANGE_PALE = RGBColor(0xFF, 0xF3, 0xE6)

CARD_Y = 1.48
CARD_W = 3.85
CARD_H = 4.62

add_thinking_card(
    s, 0.55, CARD_Y, CARD_W, CARD_H, BLUE, BLUE_PALE,
    "Cách 1 · Có quy luật sẵn", "Diễn dịch",
    ["Bắt đầu từ điều đã biết", "Áp xuống trường hợp trước mặt", "Thấy khác → sửa cách hiểu"],
    ["Nghiên cứu 2022: cần cùng mốc thời gian.",
     "Trộn ngẫu nhiên lộ 98,91%; giữ lượt cuối: 0%.",
     "1 trường hợp ngược đủ bác cách hiểu cũ."])

add_thinking_card(
    s, 4.74, CARD_Y, CARD_W, CARD_H, TEAL, TEAL_PALE,
    "Cách 2 · CHỦ ĐẠO", "Quy nạp",
    ["Nhìn nhiều trường hợp", "Rút ra quy luật chung", "Kết luận từ dữ liệu thật"],
    ["3 cách chia · 2 mô hình · 6 cách đo",
     "trên 25 triệu lượt chấm.",
     "Quy luật: hỏi cách đo trước, tin số sau.",
     "Chủ đạo vì kết luận từ dữ liệu thật."])

add_thinking_card(
    s, 8.93, CARD_Y, CARD_W, CARD_H, ORANGE, ORANGE_PALE,
    "Cách 3 · Thấy lạ → đoán → kiểm tra", "Suy đoán",
    ["Thấy điểm bất thường", "Đoán nguyên nhân hợp lý", "Đếm lại để kiểm chứng"],
    ["Cùng mô hình, đổi cách chia: 0,2584 → 0,0474.",
     "Đoán: dữ liệu bị lộ khi trộn ngẫu nhiên.",
     "Đếm: 98,91% mẫu kiểm tra cũ hơn lượt mới nhất."])

for arrow_x in (4.47, 8.66):
    ar = s.shapes.add_textbox(Inches(arrow_x), Inches(3.45), Inches(0.25), Inches(0.42))
    ar.text_frame.word_wrap = False
    p = ar.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = "→"
    r.font.size = Pt(22); r.font.bold = True; r.font.color.rgb = BLUE

band = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                          Inches(0.55), Inches(6.18), Inches(12.15), Inches(0.58))
set_round_rect_adjustments(band, radius_in=0.16)
band.fill.solid(); band.fill.fore_color.rgb = NAVY
band.line.fill.background(); band.shadow.inherit = False
band.name = "footer_band"
btf = band.text_frame; btf.clear(); btf.word_wrap = True
btf.vertical_anchor = 3
btf.margin_left = btf.margin_right = Inches(0.20)
btf.margin_top = btf.margin_bottom = Inches(0.04)
bp = btf.paragraphs[0]; bp.alignment = PP_ALIGN.CENTER
br = bp.add_run()
br.text = "Có quy luật sẵn → diễn dịch · Có nhiều quan sát → quy nạp · Thấy lạ → suy đoán"
br.font.size = Pt(12.5); br.font.bold = True; br.font.name = "Tahoma"; br.font.color.rgb = WHITE

notes(s, "Ba phương pháp tư duy theo báo cáo và bài giảng: diễn dịch, quy nạp, suy đoán. "
         "Chủ đạo là quy nạp vì kết luận chính rút từ nhiều quan sát trên dữ liệu thật. "
         "Diễn dịch: lý thuyết TOIS 2022 nói đánh giá offline cần mốc thời gian chung; đem kiểm định "
         "trên 3 split thì random 80/20 có SLI tương đối 98,91%, leave-one-out (LOO) là 0%. "
         "Một phản ví dụ LOO đủ bác định nghĩa rò rỉ toàn cục. Phản chứng ở đây là bước kiểm chứng thêm, "
         "không phải phương pháp thứ 4. "
         "Quy nạp: 3 split × 2 mô hình × 6 chỉ số trên 25.000.095 lượt chấm; giới hạn là mới 1 seed; "
         "ALS đã chạy đủ 162.541 người. "
         "Suy đoán: cùng ALS, NDCG@10 rơi 0,2584 → 0,0474 (đường chạy script 2026-11-04 / Metrics.md mục 4); "
         "đoán rò rỉ ở split random; đếm thì 98,91% mẫu test cũ hơn lượt mới nhất của chính người đó, "
         "giả thuyết thành bằng chứng. Không trộn số 0,2581 → 0,0469 của đường notebook/FULL vào slide này.")

# ============ SLIDE 5 — W5H2 ============
s = add_slide("Phân tích bài toán theo W5H2", "Chương 2")
add_table(s, [
    ["Câu hỏi", "Nội dung"],
    ["WHAT — cái gì", "Cách chia dữ liệu (random 80/20 · theo thời gian · leave-one-out) đổi thước đo và thiên lệch thế nào"],
    ["WHO — ai", "Người làm gợi ý dùng đánh giá offline; người dùng ít phim bị che khuất"],
    ["WHERE / WHEN", "Spark trên máy cá nhân; phim 1995–2019; nghiên cứu 11/2026–06/2027"],
    ["WHY — vì sao", "Chia sai → rò rỉ → kết luận sai → chọn sai mô hình"],
    ["HOW MUCH — bao nhiêu", "ALS NDCG 0,2581 (random) → 0,0469 (leave-one-out): chênh 5,5 lần"],
    ["HOW — làm sao", "Kiểm tra 3 cách chia × 5 mô hình × 6 chỉ số trên 25 triệu tương tác"],
], 0.6, 1.40, 12.1, 4.25, col_widths=[2.3, 9.8], header_size=13, body_size=12)
footer_note(s, "Chuỗi phát biểu vấn đề: thực trạng → hậu quả → hạn chế của tài liệu → giải pháp (SLI + kiểm tra 3 bước).", top=5.78)
notes(s, "Thực trạng: đa số dùng random 80/20. Hậu quả: chỉ số phóng đại, thứ hạng có thể đảo. "
         "Hạn chế: bài trước đo riêng từng mặt. Giải pháp: SLI + kiểm tra 3 bước.")

# ============ SLIDE 6 — tài liệu ============
s = add_slide("Kiểm tra tài liệu", "Chương 2 — 14 bài bản nhà xuất bản, không dùng arXiv")
add_table(s, [
    ["Nguồn", "Xếp hạng", "Số bài"],
    ["ACM TOIS / TORS", "Q1 · CORE A", "4"],
    ["ACM RecSys ('25, '26, '23, '21, '20)", "Q1 · CORE A*", "5"],
    ["ACM SIGIR '23", "Q1 · CORE A*", "1"],
    ["Springer UMAI 2024 / J. Big Data 2019", "Q1 · CORE —/C", "2"],
    ["Elsevier ESWA 2023", "Q1 · CORE B", "1"],
], 0.6, 1.42, 7.45, 2.75, col_widths=[4.6, 1.7, 0.8], header_size=12, body_size=11)
tb = s.shapes.add_textbox(Inches(8.35), Inches(1.42), Inches(4.45), Inches(4.70))
tf = tb.text_frame; tf.word_wrap = True
lines = [
    "Cách kiểm tra",
    "• 14/14 là bản nhà xuất bản; đã kiểm tra thông tin PDF",
    "• 10/14 có DOI ACM; 9 bài CORE A*/A",
    "• Loại bài chỉ có arXiv: 10.48550/arxiv.2011.07931",
    "• Kiểm tra: DOI mở được, có bản quyền ACM/Springer/Elsevier",
    "• Ghi rõ nguồn: _manifest.json có sha256 từng file",
    "• Zotero: nhóm thẻ rò rỉ (5), thiên lệch (6), chia tập (2), Big Data (2)",
    "• Mã nguồn bài đối chuẩn: github.com/putatu/dataLeakageRec",
]
for i, t in enumerate(lines):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.space_after = Pt(5)
    r = p.add_run(); r.text = t
    r.font.size = Pt(12 if i == 0 else 10)
    r.font.bold = i == 0
    r.font.color.rgb = ACCENT if i == 0 else DARK
footer_note(s, "Chụp trang đầu từng PDF có trong phụ lục. Tìm kiếm theo 3 trục: bài toán – cách làm – phạm vi.", top=6.18)
notes(s, "Quy trình tìm: DOI từ OpenAlex/Unpaywall → chỉ lấy bản nhà xuất bản → kiểm tra /Creator → tra SCImago/CORE → ghi manifest sha256. "
         "14 bài, 9 bài CORE A*/A. Mã nguồn bài đối chuẩn: github.com/putatu/dataLeakageRec.")

# ============ SLIDE 7 — ma trận + 4 loại đóng góp ============
s = add_slide("Bảng tổng hợp và khoảng trống", "Chương 2 — hạn chế trong bảng dẫn tới câu hỏi")
add_table(s, [
    ["Bài", "Cách làm", "Kết quả", "Hạn chế → chỗ đề tài vào"],
    ["Wang, TOIS 2022", "So sánh có/không dùng mốc thời gian chung", "Rò rỉ đổi độ đúng và thứ hạng", "Chưa có thước đo rò rỉ"],
    ["Abdollahpouri, TOIS 2023", "Tách dữ liệu / thuật toán / nhóm người / cách đánh giá", "Cách đánh giá giải thích mâu thuẫn", "Chưa gắn quy mô lớn"],
    ["Chen, RecSys '25", "SASRec+ / BERT4Rec / GRU4Rec trên 8 tập", "Cách chia đổi thứ hạng", "Chỉ mô hình chuỗi; cần GPU lớn"],
    ["RecSys '26", "Kiểm tra độ tin của đánh giá offline", "Xếp hạng thưa khác đánh giá dày", "Chưa đo độ phủ và thiên lệch"],
    ["RecSys '20", "So sánh cách chia tập", "Chia tập là lựa chọn thiết kế", "Quy mô vừa"],
], 0.45, 1.38, 12.45, 2.70, col_widths=[2.35, 3.45, 3.05, 3.60], header_size=11, body_size=10)
LIM = rf"{FIGS}\limitation"
add_pic_caption(s, rf"{LIM}\01_TOIS2022_Ji_scope.png", 0.45, 4.18, 6.05,
                "[1] TOIS 2022: đổi thứ hạng nhưng chưa đặt tên thước đo", caption_size=9)
add_pic_caption(s, rf"{LIM}\02_TOIS2023_Navarro_limitations.png", 6.85, 4.18, 6.05,
                "[2] TOIS 2023: chưa gắn quy mô dữ liệu lớn", caption_size=9)
add_pic_caption(s, rf"{LIM}\03_RecSys2025_TimeToSplit_limitation.png", 0.45, 5.02, 6.05,
                "[3] RecSys '25: chỉ mô hình chuỗi, tốn GPU lớn", caption_size=9)
add_pic_caption(s, rf"{LIM}\04_RecSys2026_Discussion_Limitations.png", 6.85, 5.02, 6.05,
                "[4] RecSys '26: xếp hạng thưa khác đánh giá dày", caption_size=9)
footer_note(s, "Khoảng trống: chưa bài nào đo cùng lúc đảo thứ hạng + thiên lệch + chi phí trên cùng một pipeline. "
              "Đóng góp của đề tài: hệ thống + thực nghiệm; KHÔNG nhận phương pháp mới hay miền mới.", top=6.32, size=10)
notes(s, "Bảng 5 bài. 4 ảnh là câu hạn chế cắt từ bản nhà xuất bản, có trang nguồn trong phụ lục. "
         "Gap 3 phần (đã biết / điểm nghẽn / cách làm đề xuất) nằm ở báo cáo; slide chỉ tóm tắt. "
         "Đóng góp theo 4 loại của bài giảng: bài toán (một phần), phương pháp (không), miền ứng dụng (không), lý giải (một phần).")

# ============ SLIDE 8 — tiêu đề, mục tiêu, câu hỏi ============
s = add_slide("Mục tiêu và câu hỏi", "Chương 3")
tb = s.shapes.add_textbox(Inches(0.55), Inches(1.40), Inches(12.2), Inches(0.68))
tf = tb.text_frame; tf.word_wrap = True
p = tf.paragraphs[0]
r = p.add_run(); r.text = ("Công thức tiêu đề: [cách làm] + [mục tiêu] + [phạm vi] — "
                           "kiểm tra cách chia tập → đo rò rỉ và thiên lệch → gợi ý trên Spark, MovieLens 25M")
r.font.size = Pt(13); r.font.bold = True; r.font.color.rgb = DARK
add_table(s, [
    ["Việc cần làm", "Nội dung", "Tỷ trọng", "Câu hỏi"],
    ["SO1 Dữ liệu", "Chuẩn hóa MovieLens 25M; tạo 3 cách chia; đếm phổ biến bằng MapReduce", "20%", "—"],
    ["SO2 Thước đo", "Đề xuất SLI theo từng người, 3 mức + kiểm tra 3 bước", "40%", "RQ1, RQ2"],
    ["SO3 Đối chuẩn", "Chạy 5 mô hình trên 3 cách chia, 1 seed (đã khai báo giới hạn)", "20%", "RQ1"],
    ["SO4 Thử nghiệm thêm", "Đổi ngưỡng liên quan, lấy mẫu nhỏ, thử 2 định nghĩa SLI", "20%", "RQ2, RQ4"],
], 0.55, 2.12, 12.2, 3.10, col_widths=[1.9, 7.4, 1.2, 1.4], header_size=12, body_size=11)
footer_note(s, "RQ1: cách chia có làm đảo thứ hạng? · RQ2: thiên lệch đổi bao nhiêu? · RQ3: chi phí chạy? · "
              "RQ4: kiểm tra 3 bước có dùng được? · RQ5 (mở rộng): sang tập dữ liệu khác.", top=5.40, size=10)
footer_note(s, "Biến: độc lập = cách chia; phụ thuộc = NDCG/MRR/SLI; kiểm soát = dữ liệu, seed, ngân sách chỉnh. "
              "H0: không khác biệt giữa các cách chia; H1: có khác biệt; bác H0 khi p < 0,05.", top=5.92, size=10)
notes(s, "SO2 nặng nhất. S8 dùng 1 seed thay vì 3+ seed như bản cũ. Thêm bảng biến và H0/H1 theo bài giảng 03.")

# ============ SLIDE 9 — FINER ============
s = add_slide("Kiểm tra tính khả thi", "Chương 3 — mỗi ô có một bằng chứng thật")
add_table(s, [
    ["Tiêu chí", "Bằng chứng"],
    ["F — làm được", "Dữ liệu đã tải và đo; thử nghiệm chạy xong trước hạn"],
    ["I — đáng quan tâm", "Trả lời 'cách đo đúng chưa' quan trọng hơn 'mô hình nào cao hơn'"],
    ["N — mới", "SLI: leave-one-out tính toàn cục 99,9988% nhưng theo từng người là 0%"],
    ["E — đạo đức", "Dữ liệu ẩn danh, dùng cho nghiên cứu, có trích nguồn Harper & Konstan"],
    ["R — dùng được", "Đóng góp là cách kiểm tra, không phải mô hình mới; dùng cho tập có mốc thời gian"],
], 0.6, 1.42, 12.1, 4.25, col_widths=[2.1, 10.0], header_size=13, body_size=12)
footer_note(s, "Chữ trong slide dùng cách nói dễ hiểu; tên đầy đủ FINER nằm trong notes để hội đồng đối chiếu.", top=5.82)
notes(s, "FINER = Feasible, Interesting, Novel, Ethical, Relevant. Mỗi ô gắn một bằng chứng có số hoặc có nguồn.")

# ============ SLIDE 10 — quy trình ============
s = add_slide("Quy trình thực hiện", "Chương 3 — bốn tầng, đã chạy thật")
s.shapes.add_picture(rf"{FIGS}\fig_architecture.png", Inches(2.00), Inches(1.42), width=Inches(9.4))
footer_note(s, "MapReduce chạy xong 2026-11-04 (container đã gỡ, dựng lại được) · đối chiếu G3 đúng 100% · "
              "10/10 notebook đạt · 4 mô hình CPU, SASRec GPU local.", top=6.42, size=10)
notes(s, "Bốn tầng: lưu trữ Parquet + Spark; xử lý lớn MapReduce Java + PySpark local[4]; lưu chỉ số MongoDB; "
         "trình bày R + Streamlit. SASRec chạy GPU RTX 4050 6 GB.")

# ============ SLIDE 11 — chỉ số + baseline ============
s = add_slide("Chỉ số và mô hình đối chuẩn", "Chương 3")
bullets(s, [
    (0, "Chỉ số của đề tài", True),
    (1, "SLI = trung bình tỷ lệ rò rỉ theo từng người; không dùng tỷ lệ gộp cả tập", False),
    (1, "3 mức: an toàn < 0,05 · nhẹ 0,05–0,30 · nặng ≥ 0,30", False),
    (0, "Chỉ số xếp hạng", True),
    (1, "NDCG@10 = DCG/IDCG (5 ca tính tay, sai số 1e-12) · Hit@10 · Recall@10 · MRR@10", False),
    (0, "Chỉ số thiên lệch", True),
    (1, "độ phủ danh mục · Gini mức hiển thị · tỷ lệ phim phổ biến · độ phủ phim ít người xem", False),
    (0, "5/5 mô hình đã chạy: sàn (MostPopular, Random) · kinh điển (ALS, ItemKNN) · đối chuẩn mới (SASRec + CE)", True),
    (1, "SASRec + CE là mô hình đối chuẩn, KHÔNG phải mô hình thắng; GPU RTX 4050 6 GB, seed 42, không chỉnh thêm", False),
    (1, "4 mô hình chạy CPU, SASRec chạy GPU; KHÔNG so thời gian CPU với GPU", False),
    (0, "Kiểm định: Wilcoxon theo từng người + khoảng tin cậy 95% + độ lớn hiệu ứng", True),
    (1, "20/20 cặp có ít nhất 30 người; ít nhất 6.214 người", False),
], top=1.38, size=15)
notes(s, "Wilcoxon dùng vì NDCG theo từng người lệch phải. 20 cặp gồm 12 cặp baseline + 8 cặp SASRec. "
         "SASRec là SOTA reference/local reproduction, tuning_budget=0, không phải model thắng.")

# ============ SLIDE 12 — kết quả ============
s = add_slide("Kết quả sơ bộ", "Chương 3 — số thật, chưa phải kết luận cuối")
s.shapes.add_picture(rf"{FIGS}\fig_sli.png", Inches(0.40), Inches(1.36), width=Inches(5.55))
s.shapes.add_picture(rf"{FIGS}\fig_interaction.png", Inches(6.28), Inches(1.48), width=Inches(6.55))
add_table(s, [
    ["Mô hình", "NDCG r80", "NDCG thời gian", "NDCG LOO", "MRR r80", "MRR thời gian", "MRR LOO"],
    ["ItemKNN", "0,2679", "0,1409", "0,0461", "0,4604", "0,2644", "0,0330"],
    ["ALS", "0,2581", "0,1332", "0,0469", "0,4342", "0,2491", "0,0328"],
    ["SASRec + CE (GPU)", "0,0163", "0,0188", "0,0067", "0,0381", "0,0449", "0,0043"],
    ["MostPopular", "0,0852", "0,0455", "0,0183", "0,1751", "0,0964", "0,0123"],
    ["Random", "0,0003", "0,0009", "0,0001", "0,0009", "0,0023", "0,0001"],
    ["ItemKNN − ALS", "+0,0098", "+0,0077", "−0,0008", "+0,0262", "+0,0153", "+0,0002"],
    ["Wilcoxon p", "2,8e-60", "3,0e-03", "0,153", "—", "—", "—"],
], 0.40, 4.06, 12.50, 2.32, col_widths=[2.45, 1.45, 1.70, 1.45, 1.45, 1.70, 1.45],
    header_size=9, body_size=9)
footer_note(s, "Seed 42 · 1 seed · SASRec đối chuẩn, tuning_budget=0 · KHÔNG Mean±Std · KHÔNG đo bộ nhớ · "
              "SASRec đánh giá trên tập người con nên so cặp trên giao người.", top=6.46, size=9)
notes(s, "ItemKNN dẫn ở random và temporal; ALS dẫn ở LOO nhưng p=0,153, CI chứa 0 → không kết luận. "
         "SASRec là đối chuẩn SOTA chạy lại trên máy, không phải model thắng. 1 seed, không Mean±Std, không memory.")

# ============ SLIDE 13 — ROI + kế hoạch ============
s = add_slide("Hiệu quả, chi phí và kế hoạch", "Chương 3")
tb = s.shapes.add_textbox(Inches(0.55), Inches(1.34), Inches(6.05), Inches(4.10))
tf = tb.text_frame; tf.word_wrap = True
left_lines = [
    "Hiệu quả và chi phí",
    "• Kiểm tra tự chặn 3/3 cặp so không hợp lệ (lệch 25,5× / 1,65× / 15,4× > 1,2)",
    "• Tính SLI khoảng 2 phút cho mỗi cách chia mới",
    "• 3 kết quả: thước đo SLI · cách kiểm tra 3 bước · pipeline chạy lại được",
    "• 1 laptop i7-13620H, 32 GB, RTX 4050 6 GB; không dùng cloud",
    "Rủi ro và cách xử lý",
    "• SASRec chạy được trên GPU 6 GB; chưa chỉnh thêm, chưa hết bộ nhớ",
    "• Hạ tầng lỗi → giữ Spark trên máy, vẫn đọc được Parquet",
    "• Thiếu thời gian → bỏ RQ5 (sang tập khác)",
    "• Mới 1 seed → nói rõ giới hạn",
]
for i, t in enumerate(left_lines):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.space_after = Pt(5)
    r = p.add_run(); r.text = t
    r.font.size = Pt(11 if i not in (0, 5) else 12)
    r.font.bold = i in (0, 5)
    r.font.color.rgb = ACCENT if i in (0, 5) else DARK
add_table(s, [
    ["Giai đoạn", "Nội dung", "Kết quả", "Mốc"],
    ["G1", "Xong SASRec trên GPU; EASE không đăng ký nên không chạy", "Bảng 3 cách chia × 5 mô hình", "11/2026"],
    ["G2", "Xong Wilcoxon + CI + độ lớn; 20/20 cặp", "Thêm biểu đồ nếu có thời gian", "01/2027"],
    ["G3", "Viết báo cáo + thử giao diện", "Báo cáo nháp", "02/2027"],
    ["G4", "Phản biện nội bộ + sửa", "Bản cuối", "03/2027"],
    ["G5", "Bảo vệ", "Slide + demo", "06/2027"],
], 6.85, 1.34, 5.95, 3.65, col_widths=[0.8, 2.8, 1.9, 0.9], header_size=10, body_size=9)
footer_note(s, "Mã nguồn và tham số: " + REPO_URL, top=5.55, size=10)
notes(s, "Giao thức chặn 3/3 cặp so sai. ROI: 1 laptop, 3 kết quả. Kế hoạch 5 giai đoạn đến 06/2027. "
         "Repo công khai: " + REPO_URL)

# ============ SLIDE 14 — tự đánh giá ============
s = add_slide("Tự đánh giá và giới hạn", "Kết luận")
add_table(s, [
    ["Mặt", "Trạng thái"],
    ["Dữ liệu", "Hợp pháp, ẩn danh, đã kiểm tra sha256, dùng cho nghiên cứu"],
    ["Kỹ thuật", "PySpark + MapReduce Java + MongoDB + R + Streamlit; MapReduce chạy thật 2026-11-04"],
    ["Thời gian & máy", "Laptop RTX 4050 6 GB; các bước G1–G5 đến 06/2027"],
    ["Giới hạn nói thẳng", "local[4] không phải cụm; container đã gỡ; 5/5 mô hình chạy (SASRec GPU, tập người con); "
                          "không so CPU/GPU; 1 seed; không Mean±Std; không đo bộ nhớ; không so NDCG giữa các split"],
    ["Hướng thêm", "Sang tập khác (Amazon/Steam); thêm seed; chỉnh SASRec; đo bộ nhớ; nếu có thời gian thêm Friedman/Nemenyi"],
], 0.6, 1.40, 12.1, 4.10, col_widths=[2.3, 9.8], header_size=12, body_size=11)
footer_note(s, "Bốn nhóm an toàn của nghiên cứu: dữ liệu/thiết kế/đo lường/thống kê — mới đáp ứng một phần; "
              "cách giảm rủi ro được ghi ở dòng giới hạn.", top=5.72, size=10)
notes(s, "Nói thẳng giới hạn trước khi hội đồng hỏi. Chưa chứng minh ổn định qua seed, chưa đo memory, "
         "chưa so runtime CPU/GPU. Không nhận SOTA replication đầy đủ.")

# ============ SLIDE 15 — Q&A ============
s = add_slide("Hỏi và đáp", "Cảm ơn hội đồng")
add_table(s, [
    ["#", "Tài liệu tham khảo (IEEE)"],
    ["[1]", "Y. Wang et al., “A Critical Study on Data Leakage in Recommender System Offline Evaluation,” ACM TOIS, 41(3), 2022. DOI: 10.1145/3569930"],
    ["[2]", "H. Abdollahpouri et al., “Reproducing Popularity Bias in Recommendation,” ACM TORS, 2(1), 2023. DOI: 10.1145/3637066"],
    ["[3]", "Y. Chen et al., “Time to Split,” Proc. RecSys '25, 2025, pp. 874–883. DOI: 10.1145/3705328.3748164"],
    ["[4]", "“On the Convergent Validity of Offline Evaluation Designs,” Proc. RecSys '26, 2026. DOI: 10.1145/3773078.3831818"],
    ["[5]", "F. M. Harper and J. A. Konstan, “The MovieLens Datasets,” ACM TIST, 5(4), 2015. DOI: 10.1145/2827872"],
], 0.5, 1.42, 12.35, 3.90, col_widths=[0.7, 11.65], header_size=12, body_size=10)
tb = s.shapes.add_textbox(Inches(0.55), Inches(5.55), Inches(12.2), Inches(0.95))
tf = tb.text_frame; tf.word_wrap = True
for i, t in enumerate([
    "Mã nguồn và tham số: " + REPO_URL,
    "Câu hỏi dự phòng: vì sao LOO không rò rỉ? · ALS có chạy đủ 162.541 người không? · 1 seed có đủ chưa?",
]):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    r = p.add_run(); r.text = t
    r.font.size = Pt(10); r.font.italic = True; r.font.color.rgb = GREY
notes(s, "Giải thích ngắn: LOO lấy mốc là lượt muộn nhất của chính người đó; ALS chạy đủ 162.541 người; "
         "mới 1 seed nên chưa nói độ ổn định. SASRec là đối chuẩn, không phải mô hình thắng.")


def verify_layout():
    problems = []
    for si, slide in enumerate(prs.slides, 1):
        for sh in slide.shapes:
            if getattr(sh, "left", None) is None:
                continue
            if sh.left < 0 or sh.top < 0 or sh.left + sh.width > SW or sh.top + sh.height > SH:
                problems.append(f"slide {si}: shape outside {sh.name}")
        shapes = [sh for sh in slide.shapes
                  if getattr(sh, "left", None) is not None
                  and not str(getattr(sh, "name", "")).startswith("decor_")
                  and not (sh.top == 0 and sh.height == Inches(0.92)
                           and sh.width == prs.slide_width and sh.left == 0)]
        for i in range(len(shapes)):
            for j in range(i + 1, len(shapes)):
                a, b = shapes[i], shapes[j]
                ix = min(a.left + a.width, b.left + b.width) - max(a.left, b.left)
                iy = min(a.top + a.height, b.top + b.height) - max(a.top, b.top)
                area = (ix * iy) / (914400 ** 2) if ix > 0 and iy > 0 else 0
                if area > 0.08:
                    problems.append(f"slide {si}: overlap {a.name} | {b.name} = {area:.2f} in2")
    return problems


problems = verify_layout()
if problems:
    raise SystemExit("LAYOUT FAIL:\n" + "\n".join(problems))

prs.save(OUT)
print("OK", OUT, os.path.getsize(OUT), "bytes,", len(prs.slides._sldIdLst), "slides, layout checked")
