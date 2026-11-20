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


def add_panel(slide, left, top, width, height, fill, line=None,
              radius_in=0.14, name="decor_panel", line_width=1.0):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top),
                                Inches(width), Inches(height))
    set_round_rect_adjustments(sh, radius_in)
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line; sh.line.width = Pt(line_width)
    sh.shadow.inherit = False
    sh.name = name
    return sh


def add_card(slide, left, top, width, height, accent, pale,
             kicker, title, lines, body_size=11.0, title_size=15.0,
             kicker_size=9.5, name="decor_card"):
    add_panel(slide, left, top, width, height, pale, accent,
              radius_in=0.16, name=name + "_bg", line_width=1.25)
    head_h = 0.74
    head = add_panel(slide, left + 0.10, top + 0.10, width - 0.20, head_h,
                     accent, None, radius_in=0.12, name=name + "_head")
    tf = head.text_frame; tf.clear(); tf.word_wrap = True
    tf.vertical_anchor = 3
    tf.margin_left = tf.margin_right = Inches(0.08)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = kicker
    r.font.size = Pt(kicker_size); r.font.bold = True; r.font.name = "Tahoma"; r.font.color.rgb = WHITE
    p = tf.add_paragraph(); p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = title
    r.font.size = Pt(title_size); r.font.bold = True; r.font.name = "Tahoma"; r.font.color.rgb = WHITE
    body = slide.shapes.add_textbox(Inches(left + 0.14), Inches(top + head_h + 0.22),
                                    Inches(width - 0.28), Inches(height - head_h - 0.34))
    body.name = name + "_body"
    tf = body.text_frame; tf.clear(); tf.word_wrap = True
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(4); p.line_spacing = 1.0
        r = p.add_run(); r.text = line
        r.font.size = Pt(body_size); r.font.name = "Tahoma"; r.font.color.rgb = DARK
    return body


def add_banner(slide, left, top, width, height, text, fill=None, size=11.0,
               color=None, bold=False, name="decor_banner", align=PP_ALIGN.CENTER):
    if fill is None:
        fill = NAVY
    if color is None:
        color = WHITE
    sh = add_panel(slide, left, top, width, height, fill, None,
                   radius_in=0.14, name=name)
    tf = sh.text_frame; tf.clear(); tf.word_wrap = True
    tf.vertical_anchor = 3
    tf.margin_left = tf.margin_right = Inches(0.14)
    tf.margin_top = tf.margin_bottom = Inches(0.04)
    for i, line in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align; p.space_after = Pt(1); p.line_spacing = 1.0
        r = p.add_run(); r.text = line
        r.font.size = Pt(size); r.font.bold = bold; r.font.name = "Tahoma"; r.font.color.rgb = color
    return sh


def add_stat_card(slide, left, top, width, height, big, label, accent, pale,
                  name="decor_stat"):
    add_panel(slide, left, top, width, height, pale, accent,
              radius_in=0.12, name=name + "_bg", line_width=1.0)
    tb = slide.shapes.add_textbox(Inches(left + 0.08), Inches(top + 0.06),
                                  Inches(width - 0.16), Inches(height - 0.12))
    tb.name = name + "_text"
    tf = tb.text_frame; tf.clear(); tf.word_wrap = True
    tf.vertical_anchor = 3
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = big
    r.font.size = Pt(20); r.font.bold = True; r.font.name = "Tahoma"; r.font.color.rgb = accent
    p = tf.add_paragraph(); p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = label
    r.font.size = Pt(10); r.font.name = "Tahoma"; r.font.color.rgb = DARK
    return tb


def add_arrow(slide, left, top, size=20, color=None):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(0.22), Inches(0.38))
    tb.name = "decor_arrow"
    tf = tb.text_frame; tf.word_wrap = False
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = "→"
    r.font.size = Pt(size); r.font.bold = True; r.font.name = "Tahoma"
    r.font.color.rgb = color or ACCENT
    return tb

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
BLUE = RGBColor(0x1A, 0x56, 0xDB)
BLUE_PALE = RGBColor(0xEC, 0xF3, 0xFF)
TEAL = RGBColor(0x1E, 0x8A, 0x5A)
TEAL_PALE = RGBColor(0xE9, 0xF7, 0xF0)
ORANGE = RGBColor(0xBE, 0x6A, 0x18)
ORANGE_PALE = RGBColor(0xFF, 0xF3, 0xE6)

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
            cell.fill.solid()
            cell.fill.fore_color.rgb = (NAVY if ri == 0 else
                                        RGBColor(0xF4, 0xF7, 0xFC) if ri % 2 == 0 else WHITE)
            cell.text = str(val)
            cell.margin_top = Pt(2); cell.margin_bottom = Pt(2)
            cell.margin_left = Pt(4); cell.margin_right = Pt(4)
            for p in cell.text_frame.paragraphs:
                p.space_after = Pt(0)
                for r in p.runs:
                    r.font.size = Pt(header_size if ri == 0 else body_size)
                    r.font.name = "Tahoma"
                    r.font.name = "Tahoma"
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
add_panel(s, 1.05, 1.15, 11.25, 0.10, ACCENT, None, radius_in=0.05, name="decor_top_line")
add_panel(s, 4.85, 3.92, 3.65, 0.08, TITLE_RED, None, radius_in=0.04, name="decor_mid_line")
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
for x, label in ((1.55, "Cách chia dữ liệu"), (5.35, "Thước đo rò rỉ"), (9.15, "Spark · MovieLens 25M")):
    add_banner(s, x, 4.16, 2.65, 0.46, label, fill=RGBColor(0xEC, 0xF3, 0xFF),
               size=11.5, color=ACCENT, bold=True, name="decor_topic_chip")
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
add_banner(s, 0.85, 6.72, 11.1, 0.40, "Trọng tâm: quy trình nghiên cứu, không phải demo hạ tầng.",
           fill=RGBColor(0xF4, 0xF7, 0xFC), size=10.5, color=GREY, name="decor_scope_chip")
notes(s, "Chào hội đồng. Em trình bày đề cương: Rò rỉ và thiên lệch trong hệ thống gợi ý: "
         "kiểm tra cách chia dữ liệu bằng Spark. Tiêu đề gồm phương pháp + mục tiêu + phạm vi. "
         "Đề tài phục vụ môn Phương pháp nghiên cứu khoa học.")

# ============ SLIDE 2 — bố cục ============
s = add_slide("Bố cục trình bày")
parts = [
    ("CHƯƠNG 1", "20%", "Cơ sở", ["Hiểu dữ liệu", "3 cách tư duy"], BLUE, BLUE_PALE),
    ("CHƯƠNG 2", "30%", "Bài toán & tài liệu", ["6 câu hỏi", "10 bài + bảng tổng hợp"], TEAL, TEAL_PALE),
    ("CHƯƠNG 3", "45%", "Đề cương", ["Mục tiêu, chỉ số", "Kết quả, kế hoạch"], ORANGE, ORANGE_PALE),
    ("KẾT LUẬN", "5%", "Tự đánh giá", ["Giới hạn", "Hướng thêm"], NAVY, RGBColor(0xEC, 0xF0, 0xF7)),
]
for i, (chapter, pct, name, lines, accent, pale) in enumerate(parts):
    x = 0.55 + i * 3.10
    add_stat_card(s, x, 1.48, 2.90, 0.92, pct, chapter, accent, pale,
                  name="decor_part_%d" % i)
    add_card(s, x, 2.52, 2.90, 2.95, accent, pale, chapter, name, lines,
             body_size=11.0, title_size=14.0, name="decor_part_card_%d" % i)
    if i < 3:
        add_arrow(s, x + 2.88, 3.80, size=18, color=GREY)
add_banner(s, 0.55, 5.78, 12.15, 0.62,
           "Thời lượng: khoảng 12 phút trình bày + 5–8 phút hỏi đáp.\nChương 3 nhận nhiều thời gian nhất.",
           fill=RGBColor(0xF4, 0xF7, 0xFC), size=11, color=GREY, name="decor_time_banner")
notes(s, "Bố cục bám tỷ trọng hướng dẫn: C1 20%, C2 30%, C3 45%, kết luận 5%. Phần nặng nhất là Chương 3.")

# ============ SLIDE 3 — DIKW ============
s = add_slide("Từ dữ liệu đến quyết định", "Chương 1 — có gì → thấy gì → hiểu gì → làm gì")
steps = [
    ("Dữ liệu", "Có gì", ["25 triệu lượt chấm; 162.541 người.", "MovieLens 25M (1995–2019).", "Mỗi dòng: ai, phim nào, mấy sao, lúc nào."], BLUE, BLUE_PALE),
    ("Thông tin", "Thấy gì", ["0 dòng trùng.", "1.799.454 nhóm chấm cùng giây.", "8,76% phim kiểm tra là phim người đó chưa chấm."], TEAL, TEAL_PALE),
    ("Hiểu ra", "Hiểu gì", ["Cùng ALS, chỉ đổi cách chia:", "NDCG@10 0,2581 → 0,0469.", "Thấp hơn 5,5 lần."], ORANGE, ORANGE_PALE),
    ("Quyết định", "Làm gì", ["Đo rò rỉ trước (SLI), đọc chỉ số sau.", "Lệch quá 1,2 lần thì dừng so sánh.", "Ghi rõ điều kiện chia khi báo cáo."], NAVY, RGBColor(0xEC, 0xF0, 0xF7)),
]
for i, (title, kicker, lines, accent, pale) in enumerate(steps):
    x = 0.55 + i * 3.10
    add_card(s, x, 1.48, 2.90, 4.48, accent, pale, kicker, title, lines,
             body_size=10.5, title_size=15, name="decor_diku_%d" % i)
    if i < 3:
        add_arrow(s, x + 2.88, 3.40, size=18, color=accent)
add_banner(s, 0.55, 6.12, 12.15, 0.52,
           "Đây là ví dụ có số thật của đề tài, không phải ví dụ giả định trong bài giảng.",
           fill=RGBColor(0xF4, 0xF7, 0xFC), size=10.5, color=GREY, name="decor_diku_footer")
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
s = add_slide("6 câu hỏi của bài toán", "Chương 2 — hỏi đúng thì làm đúng")
questions = [
    ("Cái gì?", "Chia dữ liệu", ["Trộn ngẫu nhiên, theo thời gian,", "giữ lượt cuối của mỗi người.", "Cách chia đổi thước đo và thiên lệch."], BLUE, BLUE_PALE),
    ("Ai?", "Ai bị ảnh hưởng", ["Người làm gợi ý đọc kết quả.", "Người dùng ít phim dễ bị che khuất."], TEAL, TEAL_PALE),
    ("Ở đâu / khi nào?", "Phạm vi", ["Spark trên máy cá nhân.", "Phim 1995–2019; nghiên cứu 11/2026–06/2027."], ORANGE, ORANGE_PALE),
    ("Vì sao?", "Lý do", ["Chia sai → rò rỉ → kết luận sai", "→ chọn sai mô hình."], NAVY, RGBColor(0xEC, 0xF0, 0xF7)),
    ("Bao nhiêu?", "Mức chênh", ["ALS NDCG 0,2581 (trộn) → 0,0469", "(giữ lượt cuối): chênh 5,5 lần."], BLUE, BLUE_PALE),
    ("Làm sao?", "Cách kiểm tra", ["3 cách chia × 5 mô hình × 6 chỉ số", "trên 25 triệu tương tác."], TEAL, TEAL_PALE),
]
for i, (title, kicker, lines, accent, pale) in enumerate(questions):
    col, row = i % 3, i // 3
    x = 0.55 + col * 4.17
    y = 1.42 + row * 2.26
    add_card(s, x, y, 3.85, 2.06, accent, pale, kicker, title, lines,
             body_size=10.5, title_size=14.5, name="decor_q_%d" % i)
add_banner(s, 0.55, 6.02, 12.15, 0.56,
           "Chuỗi phát biểu vấn đề: thực trạng → hậu quả → hạn chế của tài liệu → giải pháp (SLI + kiểm tra 3 bước).",
           fill=RGBColor(0xF4, 0xF7, 0xFC), size=10.5, color=GREY, name="decor_problem_banner")
notes(s, "W5H2: What, Who, Where/When, Why, How much, How. Thực trạng: đa số dùng random 80/20. "
         "Hậu quả: chỉ số phóng đại, thứ hạng có thể đảo. Hạn chế: bài trước đo riêng từng mặt. Giải pháp: SLI + kiểm tra 3 bước.")

# ============ SLIDE 6 — tài liệu ============
s = add_slide("Kiểm tra tài liệu", "Chương 2 — 10 bài bản nhà xuất bản, không dùng arXiv")
add_stat_card(s, 0.60, 1.42, 3.90, 0.88, "10", "bài được giữ lại", ACCENT, BLUE_PALE, name="decor_doc_n")
add_stat_card(s, 4.70, 1.42, 3.90, 0.88, "9", "bài CORE A*/A", TEAL, TEAL_PALE, name="decor_doc_quality")
add_stat_card(s, 8.80, 1.42, 3.90, 0.88, "0", "bài chỉ có arXiv", ORANGE, ORANGE_PALE, name="decor_doc_arxiv")
add_table(s, [
    ["Nguồn", "Xếp hạng", "Số bài"],
    ["ACM TOIS / TORS", "Q1 · CORE A", "4"],
    ["ACM RecSys ('25, '26, '21, '20)", "Q1 · CORE A*", "5"],
    ["Springer UMAI 2024", "Q1 · CORE —", "1"],
], 0.60, 2.48, 7.45, 2.65, col_widths=[4.6, 1.7, 0.8], header_size=11, body_size=10)
add_card(s, 8.35, 2.48, 4.45, 2.65, ACCENT, BLUE_PALE, "Cách làm", "Kiểm tra từng bài", [
    "10/10 là bản nhà xuất bản.",
    "9/10 có DOI ACM.",
    "Loại bản chỉ có arXiv: 10.48550/arxiv.2011.07931",
    "DOI mở được, có bản quyền rõ.",
    "Ghi sha256 trong _manifest.json.",
    "Zotero: rò rỉ 1 · thiên lệch 5 · chia tập 4",
    "Mã đối chuẩn: github.com/putatu/dataLeakageRec",
], body_size=9.5, title_size=13.5, name="decor_check_card")
add_banner(s, 0.60, 5.38, 12.20, 0.68,
           "Chụp trang đầu từng PDF có trong phụ lục. Tìm theo 3 trục: bài toán – cách làm – phạm vi.",
           fill=RGBColor(0xF4, 0xF7, 0xFC), size=10.5, color=GREY, name="decor_doc_footer")
notes(s, "Quy trình tìm: DOI từ OpenAlex/Unpaywall → chỉ lấy bản nhà xuất bản → kiểm tra /Creator → tra SCImago/CORE → ghi manifest sha256. "
         "10 bài, 9 bài CORE A*/A. Mã nguồn bài đối chuẩn: github.com/putatu/dataLeakageRec.")

# ============ SLIDE 7 — ma trận + 4 loại đóng góp ============
s = add_slide("Bảng tổng hợp và khoảng trống", "Chương 2 — hạn chế trong bảng dẫn tới câu hỏi")
add_banner(s, 10.15, 1.00, 2.60, 0.30, "5 bài · 4 nhận xét", fill=BLUE_PALE,
           size=10, color=ACCENT, bold=True, name="decor_matrix_chip")
add_table(s, [
    ["Bài", "Cách làm", "Kết quả", "Hạn chế → chỗ đề tài vào"],
    ["Ji, TOIS 2023", "So sánh có/không dùng mốc thời gian chung", "Rò rỉ đổi độ đúng và thứ hạng", "Chưa có thước đo rò rỉ"],
    ["Daniil, TORS 2024", "Tách dữ liệu / thuật toán / nhóm người / cách đánh giá", "Cách đánh giá giải thích mâu thuẫn", "Chưa gắn quy mô lớn"],
    ["Frolov, RecSys '25", "SASRec+ / BERT4Rec / GRU4Rec trên 8 tập", "Cách chia đổi thứ hạng", "Chỉ mô hình chuỗi; cần GPU lớn"],
    ["Parajuli, RecSys '26", "Kiểm tra độ tin của đánh giá offline", "Xếp hạng thưa khác đánh giá dày", "Chưa đo độ phủ và thiên lệch"],
    ["Meng, RecSys '20", "So sánh cách chia tập", "Chia tập là lựa chọn thiết kế", "Quy mô vừa"],
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
add_panel(s, 0.45, 6.28, 12.45, 0.58, RGBColor(0xF4, 0xF7, 0xFC), None,
          radius_in=0.12, name="decor_gap_band")
footer_note(s, "Khoảng trống: chưa bài nào đo cùng lúc đảo thứ hạng + thiên lệch + chi phí trên cùng một pipeline. "
              "Đóng góp của đề tài: hệ thống + thực nghiệm; KHÔNG nhận phương pháp mới hay miền mới.", top=6.32, size=10)
notes(s, "Bảng 5 bài. 4 ảnh là câu hạn chế cắt từ bản nhà xuất bản, có trang nguồn trong phụ lục. "
         "Gap 3 phần (đã biết / điểm nghẽn / cách làm đề xuất) nằm ở báo cáo; slide chỉ tóm tắt. "
         "Đóng góp theo 4 loại của bài giảng: bài toán (một phần), phương pháp (không), miền ứng dụng (không), lý giải (một phần).")

# ============ SLIDE 8 — tiêu đề, mục tiêu, câu hỏi ============
s = add_slide("Mục tiêu và câu hỏi", "Chương 3 — việc cần làm gắn với câu hỏi")
add_banner(s, 0.55, 1.40, 12.15, 0.56,
           "Công thức tiêu đề: [cách làm] + [mục tiêu] + [phạm vi] — kiểm tra cách chia → đo rò rỉ và thiên lệch → Spark, MovieLens 25M",
           fill=RGBColor(0xEC, 0xF3, 0xFF), size=10.5, color=ACCENT, bold=True, name="decor_formula")
tasks = [
    ("Việc 1 · Dữ liệu", "20%", ["Chuẩn hóa MovieLens 25M.", "Tạo 3 cách chia; đếm phổ biến.", "Chưa gắn câu hỏi riêng."], BLUE, BLUE_PALE),
    ("Việc 2 · Thước đo", "40%", ["SLI theo từng người, 3 mức.", "Kiểm tra 3 bước.", "Trả lời câu hỏi 1, 2."], TEAL, TEAL_PALE),
    ("Việc 3 · Đối chuẩn", "20%", ["5 mô hình × 3 cách chia.", "1 seed (đã khai báo giới hạn).", "Trả lời câu hỏi 1."], ORANGE, ORANGE_PALE),
    ("Việc 4 · Thử thêm", "20%", ["Đổi ngưỡng; lấy mẫu nhỏ.", "Thử 2 cách tính SLI.", "Trả lời câu hỏi 2, 4."], NAVY, RGBColor(0xEC, 0xF0, 0xF7)),
]
for i, (title, pct, lines, accent, pale) in enumerate(tasks):
    x = 0.55 + i * 3.10
    add_card(s, x, 2.10, 2.90, 2.48, accent, pale, "Tỷ trọng " + pct, title, lines,
             body_size=10.0, title_size=13.0, name="decor_task_%d" % i)
add_banner(s, 0.55, 4.74, 12.15, 0.75,
           "Câu hỏi 1: chia tập có đảo thứ hạng? · 2: thiên lệch đổi bao nhiêu? · 3: chi phí chạy?\n"
           "Câu hỏi 4: kiểm tra 3 bước dùng được không? · 5 (mở rộng): sang tập dữ liệu khác.",
           fill=RGBColor(0xF4, 0xF7, 0xFC), size=10.5, color=DARK, name="decor_rq")
add_banner(s, 0.55, 5.66, 12.15, 0.82,
           "Biến: độc lập = cách chia; phụ thuộc = NDCG/MRR/SLI; kiểm soát = dữ liệu, seed, ngân sách chỉnh.\n"
           "H0: không khác biệt giữa các cách chia; H1: có khác biệt; bác H0 khi p < 0,05.",
           fill=RGBColor(0xEC, 0xF0, 0xF7), size=10.5, color=NAVY, name="decor_hyp")
notes(s, "SO2 nặng nhất. RQ1–RQ5 như slide. S8 dùng 1 seed thay vì 3+ seed như bản cũ. "
         "Bảng biến và H0/H1 theo bài giảng 03.")

# ============ SLIDE 9 — FINER ============
s = add_slide("Kiểm tra tính khả thi", "Chương 3 — mỗi ý có một bằng chứng thật")
criteria = [
    ("Làm được", "Dữ liệu đã tải và đo; thử nghiệm chạy xong trước hạn.", BLUE, BLUE_PALE),
    ("Đáng quan tâm", "Trả lời 'cách đo đúng chưa' quan trọng hơn 'mô hình nào cao hơn'.", TEAL, TEAL_PALE),
    ("Mới", "SLI: giữ lượt cuối tính toàn cục 99,9988% nhưng theo từng người là 0%.", ORANGE, ORANGE_PALE),
    ("Đạo đức", "Dữ liệu ẩn danh, dùng cho nghiên cứu, có trích nguồn Harper & Konstan.", NAVY, RGBColor(0xEC, 0xF0, 0xF7)),
    ("Dùng được", "Đóng góp là cách kiểm tra, không phải mô hình mới; dùng cho tập có mốc thời gian.", ACCENT, RGBColor(0xEC, 0xF3, 0xFF)),
]
for i, (title, body, accent, pale) in enumerate(criteria):
    add_card(s, 0.60 + i * 2.45, 1.42, 2.30, 4.25, accent, pale,
             "Tiêu chí %d" % (i + 1), title, [body],
             body_size=10.5, title_size=13.5, name="decor_finer_%d" % i)
add_banner(s, 0.60, 5.85, 12.10, 0.55,
           "Tên đầy đủ 5 tiêu chí nằm trong speaker notes để hội đồng đối chiếu.",
           fill=RGBColor(0xF4, 0xF7, 0xFC), size=10.5, color=GREY, name="decor_finer_footer")
notes(s, "FINER = Feasible, Interesting, Novel, Ethical, Relevant. Mỗi ô gắn một bằng chứng có số hoặc có nguồn.")

# ============ SLIDE 10 — quy trình ============
s = add_slide("Quy trình thực hiện", "Chương 3 — bốn tầng, đã chạy thật")
s.shapes.add_picture(rf"{FIGS}\fig_architecture.png", Inches(0.55), Inches(1.45), width=Inches(8.20))
layers = [
    ("1 · Chứa dữ liệu", ["CSV 25M → Parquet", "Spark đọc trực tiếp"], BLUE, BLUE_PALE),
    ("2 · Xử lý lớn", ["MapReduce + Spark", "323.737 khóa phổ biến"], TEAL, TEAL_PALE),
    ("3 · Lưu kết quả", ["MongoDB", "42 trường audit"], ORANGE, ORANGE_PALE),
    ("4 · Xem & kiểm định", ["R + Streamlit", "Wilcoxon theo từng người"], NAVY, RGBColor(0xEC, 0xF0, 0xF7)),
]
for i, (title, lines, accent, pale) in enumerate(layers):
    add_card(s, 9.00, 1.45 + i * 1.14, 3.75, 1.02, accent, pale,
             "Tầng %d" % (i + 1), title, lines,
             body_size=9.5, title_size=12.0, kicker_size=8.5, name="decor_layer_%d" % i)
add_banner(s, 0.55, 6.02, 12.20, 0.60,
           "MapReduce chạy xong 2026-11-04 (container đã gỡ, dựng lại được) · đối chiếu G3 đúng 100% · "
           "10/10 notebook đạt · 4 mô hình CPU, SASRec GPU local.",
           fill=RGBColor(0xF4, 0xF7, 0xFC), size=9.5, color=GREY, name="decor_arch_footer")
notes(s, "Bốn tầng: lưu trữ Parquet + Spark; xử lý lớn MapReduce Java + PySpark local[4]; lưu chỉ số MongoDB; "
         "trình bày R + Streamlit. SASRec chạy GPU RTX 4050 6 GB.")

# ============ SLIDE 11 — chỉ số + baseline ============
s = add_slide("Chỉ số và mô hình đối chuẩn", "Chương 3 — đo gì, so với ai")
metric_cards = [
    ("Chỉ số rò rỉ", "SLI", ["Trung bình tỷ lệ rò rỉ theo từng người.", "Không dùng tỷ lệ gộp cả tập.", "An toàn < 0,05 · nhẹ 0,05–0,30 · nặng ≥ 0,30"], BLUE, BLUE_PALE),
    ("Chỉ số xếp hạng", "NDCG / MRR", ["NDCG@10 = DCG/IDCG (5 ca tính tay).", "Hit@10 · Recall@10 · MRR@10."], TEAL, TEAL_PALE),
    ("Chỉ số thiên lệch", "Độ phủ", ["Độ phủ danh mục · Gini mức hiển thị.", "Tỷ lệ phim phổ biến · độ phủ phim ít xem."], ORANGE, ORANGE_PALE),
    ("Bài 04 yêu cầu thêm", "Mới lạ / Đa dạng", ["Mới lạ: phim ít người xem được đề xuất.", "Đa dạng: 10 phim không cùng một thể loại.", "Bất ngờ: CHƯA đo (cần mốc so sánh)."], NAVY, RGBColor(0xEC, 0xF0, 0xF7)),
]
for i, (kicker, title, lines, accent, pale) in enumerate(metric_cards):
    add_card(s, 0.55 + i * 3.10, 1.42, 2.90, 2.05, accent, pale, kicker, title, lines,
             body_size=9.0, title_size=13.0, kicker_size=8.5, name="decor_metric_%d" % i)
add_card(s, 0.55, 3.68, 12.15, 1.55, NAVY, RGBColor(0xEC, 0xF0, 0xF7),
         "5/5 mô hình đã chạy", "Ba nhóm đối chuẩn", [
             "Sàn: MostPopular, Random · Kinh điển: ALS, ItemKNN · Đối chuẩn mới: SASRec + CE.",
             "SASRec + CE là mô hình đối chuẩn, KHÔNG phải mô hình thắng; GPU RTX 4050 6 GB, seed 42, không chỉnh thêm.",
             "4 mô hình chạy CPU, SASRec chạy GPU; KHÔNG so thời gian CPU với GPU.",
         ], body_size=10.0, title_size=14.0, name="decor_baseline_card")
add_banner(s, 0.55, 5.45, 12.15, 1.05,
           "Kiểm định: Wilcoxon theo từng người + khoảng tin cậy 95% + độ lớn hiệu ứng.\n"
           "20/20 cặp có ít nhất 30 người; ít nhất 6.214 người. So ≥3 mô hình cùng lúc thì dùng Friedman — "
           "cả 3 cách chia đều bác bỏ \"mọi mô hình ngang nhau\".",
           fill=RGBColor(0xF4, 0xF7, 0xFC), size=10.5, color=DARK, name="decor_stat_banner")
notes(s, "Wilcoxon dùng vì NDCG theo từng người lệch phải. 20 cặp gồm 12 cặp baseline + 8 cặp SASRec. "
         "SASRec là SOTA reference/local reproduction, tuning_budget=0, không phải model thắng. "
         "Friedman chỉ nói 'không ngang nhau', không chỉ ra cặp nào — việc đó của Wilcoxon. "
         "Bài 04 yêu cầu thêm Mới lạ và Đa dạng: đã đo (giá trị nằm trong Metrics.md mục 4.12). "
         "Bất ngờ (serendipity) không đo vì cần một mô hình mốc mà đề tài không có.")

# ============ SLIDE 12 — kết quả ============
s = add_slide("Kết quả sơ bộ", "Chương 3 — số thật, chưa phải kết luận cuối")
s.shapes.add_picture(rf"{FIGS}\fig_sli.png", Inches(0.40), Inches(1.36), width=Inches(5.55))
s.shapes.add_picture(rf"{FIGS}\fig_interaction.png", Inches(6.28), Inches(1.48), width=Inches(6.55))
add_banner(s, 0.55, 1.44, 2.10, 0.34, "Rò rỉ theo từng người", fill=BLUE_PALE,
           size=9.5, color=ACCENT, bold=True, name="decor_sli_chip")
add_banner(s, 6.42, 1.56, 2.10, 0.34, "Thứ hạng đổi thế nào", fill=TEAL_PALE,
           size=9.5, color=TEAL, bold=True, name="decor_inter_chip")
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
add_panel(s, 0.40, 6.40, 12.50, 0.56, RGBColor(0xF4, 0xF7, 0xFC), None,
          radius_in=0.12, name="decor_result_band")
footer_note(s, "Seed 42 · 1 seed · SASRec đối chuẩn, tuning_budget=0 · KHÔNG Mean±Std · KHÔNG đo bộ nhớ · "
              "SASRec đánh giá trên tập người con nên so cặp trên giao người.", top=6.44, size=9)
notes(s, "ItemKNN dẫn ở random và temporal; ALS dẫn ở LOO nhưng p=0,153, CI chứa 0 → không kết luận. "
         "SASRec là đối chuẩn SOTA chạy lại trên máy, không phải model thắng. 1 seed, không Mean±Std, không memory. "
         "Mới lạ@10: MostPopular 8,49 thấp nhất, ALS 9,96, ItemKNN 9,23, SASRec 11,70, Random 20,92 — "
         "nhưng Random NDCG gần 0 nên 'mới lạ' không bằng 'tốt'. "
         "Đa dạng@10 ngược trực giác: ALS THẤP NHẤT (0,7440), thấp hơn cả MostPopular (0,7648), "
         "vì ALS vẫn kéo về cụm phim hay xuất hiện cùng nhau. Cá nhân hoá không tự động kéo theo đa dạng. "
         "Số đầy đủ: Metrics.md mục 4.12.")

# ============ SLIDE 13 — ROI + kế hoạch ============
s = add_slide("Hiệu quả, chi phí và kế hoạch", "Chương 3 — chặn sớm, làm tiếp theo lộ trình")
add_card(s, 0.55, 1.42, 6.05, 2.02, ACCENT, BLUE_PALE, "Hiệu quả", "Chạy nhanh, chặn sớm", [
    "Kiểm tra tự chặn 3/3 cặp so không hợp lệ.",
    "Lệch 25,5× / 1,65× / 15,4× > ngưỡng 1,2.",
    "Tính SLI khoảng 2 phút cho mỗi cách chia mới.",
    "3 kết quả: thước đo SLI · kiểm tra 3 bước · pipeline chạy lại được.",
], body_size=10.0, title_size=14.0, name="decor_roi")
add_card(s, 0.55, 3.62, 6.05, 1.82, ORANGE, ORANGE_PALE, "Rủi ro", "Có phương án dự phòng", [
    "SASRec chạy được trên GPU 6 GB; chưa chỉnh thêm.",
    "Hạ tầng lỗi → giữ Spark trên máy, vẫn đọc Parquet.",
    "Thiếu thời gian → bỏ câu hỏi 5 (sang tập khác).",
    "Mới 1 seed → nói rõ giới hạn.",
], body_size=10.0, title_size=14.0, name="decor_risk")
add_table(s, [
    ["Giai đoạn", "Nội dung", "Kết quả", "Mốc"],
    ["G1", "Xong SASRec trên GPU; EASE không đăng ký nên không chạy", "Bảng 3 cách chia × 5 mô hình", "11/2026"],
    ["G2", "Xong Wilcoxon + CI + độ lớn; 20/20 cặp", "Thêm biểu đồ nếu có thời gian", "01/2027"],
    ["G3", "Viết báo cáo + thử giao diện", "Báo cáo nháp", "02/2027"],
    ["G4", "Phản biện nội bộ + sửa", "Bản cuối", "03/2027"],
    ["G5", "Bảo vệ", "Slide + demo", "06/2027"],
], 6.85, 1.42, 5.95, 3.65, col_widths=[0.8, 2.8, 1.9, 0.9], header_size=10, body_size=9)
add_banner(s, 0.55, 5.65, 12.25, 0.62,
           "Chi phí: 1 laptop i7-13620H, 32 GB, RTX 4050 6 GB; không dùng cloud.\n"
           "Mã nguồn và tham số: " + REPO_URL,
           fill=RGBColor(0xF4, 0xF7, 0xFC), size=10, color=GREY, name="decor_repo_banner")
notes(s, "Giao thức chặn 3/3 cặp so sai. ROI: 1 laptop, 3 kết quả. Kế hoạch 5 giai đoạn đến 06/2027. "
         "Repo công khai: " + REPO_URL)

# ============ SLIDE 14 — tự đánh giá ============
s = add_slide("Tự đánh giá và giới hạn", "Kết luận — nói thẳng điều đã làm và chưa làm")
status_cards = [
    ("Dữ liệu", "Hợp lệ", ["Ẩn danh, dùng cho nghiên cứu.", "Đã kiểm tra sha256, trích nguồn."], BLUE, BLUE_PALE),
    ("Kỹ thuật", "Chạy thật", ["PySpark + MapReduce + MongoDB.", "R + Streamlit; MapReduce xong 2026-11-04."], TEAL, TEAL_PALE),
    ("Thời gian & máy", "Rõ ràng", ["Laptop RTX 4050 6 GB.", "G1–G5 đến 06/2027."], ORANGE, ORANGE_PALE),
    ("Hướng thêm", "Còn việc", ["Sang tập khác; thêm seed.", "Chỉnh SASRec; đo bộ nhớ."], NAVY, RGBColor(0xEC, 0xF0, 0xF7)),
]
for i, (title, kicker, lines, accent, pale) in enumerate(status_cards):
    add_card(s, 0.55 + i * 3.10, 1.42, 2.90, 2.35, accent, pale, kicker, title, lines,
             body_size=10.0, title_size=13.5, name="decor_status_%d" % i)
add_banner(s, 0.55, 3.98, 12.15, 1.62,
           "Giới hạn nói thẳng: local[4] không phải cụm; container đã gỡ; 5/5 mô hình chạy (SASRec GPU, tập người con);\n"
           "không so CPU/GPU; 1 seed; không Mean±Std; không đo bộ nhớ; không so NDCG giữa các split;\n"
           "chưa đo \"bất ngờ\" (serendipity) vì thiếu mô hình mốc — mới lạ và đa dạng thì đã đo.\n"
           "Chưa nhận bản sao SOTA đầy đủ; muốn chắc hơn thì thêm seed, thêm tập dữ liệu, đo thêm bộ nhớ.",
           fill=RGBColor(0xFF, 0xF3, 0xE6), size=10.0, color=DARK, name="decor_limit_banner")
add_banner(s, 0.55, 5.78, 12.15, 0.62,
           "Bốn nhóm an toàn của nghiên cứu: dữ liệu/thiết kế/đo lường/thống kê — mới đáp ứng một phần; "
           "cách giảm rủi ro được ghi ở dòng giới hạn.",
           fill=RGBColor(0xF4, 0xF7, 0xFC), size=10, color=GREY, name="decor_validity_banner")
notes(s, "Nói thẳng giới hạn trước khi hội đồng hỏi. Chưa chứng minh ổn định qua seed, chưa đo memory, "
         "chưa so runtime CPU/GPU. Không nhận SOTA replication đầy đủ.")

# ============ SLIDE 15 — Q&A ============
s = add_slide("Hỏi và đáp", "Cảm ơn hội đồng")
add_table(s, [
    ["#", "Tài liệu tham khảo (IEEE, rút gọn)"],
    ["[1]", "Y. Ji et al., TOIS 41(3), 2022 — Data Leakage. DOI: 10.1145/3569930"],
    ["[2]", "S. Daniil et al., TORS 2(1), 2024 — Popularity Bias. DOI: 10.1145/3637066"],
    ["[3]", "D. Gusak et al., RecSys '25, 2025 — Time to Split. DOI: 10.1145/3705328.3748164"],
    ["[4]", "S. Parajuli et al., RecSys '26, 2026 — Convergent Validity. DOI: 10.1145/3773078.3831818"],
    ["[5]", "J. Chen et al., TOIS 41(3), 2023 — Bias and Debias. DOI: 10.1145/3564284"],
    ["[6]", "A. Klimashevskaia et al., UMAI 34(5), 2024 — Popularity Bias Survey. DOI: 10.1007/s11257-024-09406-0"],
    ["[7]", "G. Meehan, J. Pauwels, RecSys '25, 2025 — Cold-Start Bias. DOI: 10.1145/3705328.3748035"],
    ["[8]", "X. Shi et al., TOIS 42(2), 2024 — Relieving Popularity Bias. DOI: 10.1145/3618107"],
    ["[9]", "Y.-M. Tamm et al., RecSys '21, 2021 — Quality Metrics. DOI: 10.1145/3460231.3478848"],
    ["[10]", "Z. Meng et al., RecSys '20, 2020 — Data Splitting. DOI: 10.1145/3383313.3418479"],
    ["[11]", "F. M. Harper, J. A. Konstan, TIST 5(4), 2015 — MovieLens. DOI: 10.1145/2827872"],
], 0.50, 1.42, 8.65, 3.90, col_widths=[0.72, 7.93], header_size=10.5, body_size=8.5)
add_card(s, 9.38, 1.42, 3.40, 3.90, ACCENT, BLUE_PALE, "Chuẩn bị", "Câu hỏi dự phòng", [
    "Vì sao giữ lượt cuối lại không rò rỉ?",
    "ALS có chạy đủ 162.541 người không?",
    "Mới 1 seed thì có đủ chưa?",
    "SASRec có phải mô hình thắng không?",
], body_size=10.5, title_size=14.0, name="decor_qa_card")
add_banner(s, 0.50, 5.55, 12.28, 0.66,
           "Mã nguồn và tham số: " + REPO_URL + "\n"
           "Giải thích ngắn nằm trong speaker notes của từng slide.",
           fill=RGBColor(0xF4, 0xF7, 0xFC), size=10, color=GREY, name="decor_qa_footer")
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
