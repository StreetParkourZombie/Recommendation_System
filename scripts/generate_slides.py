# -*- coding: utf-8 -*-
"""
Sinh 20 slide chinh + 4 slide phu luc cho de cuong PPNCKH.

Nguyen tac:
- Noi dung viet lai theo cach noi doi thuong, khong gom nhieu thuat ngu.
- So lieu doc tu runs/ co san; KHONG chay lai notebook.
- Cac so cu 0,2584 / 0,0474 / 158.688 / 6.219 / 96.003 bi cam.
- Bang dai chuyen het sang phu luc A1-A4.
"""
import argparse
import json
import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

BASE = r"D:\Master Exers\Big Data\Recomendation_System"
FIGS = os.path.join(BASE, "docs", "Project", "Main", "Presentation",
                    "Slides", "figures")
REPORT = os.path.join(BASE, "docs", "Project", "Main", "Presentation",
                      "Slides", "audit_report.json")
OUT = os.path.join(BASE, "docs", "Project", "Main", "Presentation",
                   "Slides", "PPNCKH_DeCuong_20slides.pptx")
N_SLIDES = 20
REPO_URL = "https://github.com/StreetParkourZombie/Recommendation_System"

DARK = RGBColor(0x1F, 0x29, 0x37)
ACCENT = RGBColor(0x1A, 0x56, 0xDB)
GREY = RGBColor(0x4B, 0x55, 0x63)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
NAVY = RGBColor(0x00, 0x33, 0x66)
TITLE_RED = RGBColor(0xC0, 0x00, 0x00)
NAVY_TXT = RGBColor(0x1E, 0x39, 0x89)
BLUE_PALE = RGBColor(0xEC, 0xF3, 0xFF)
TEAL = RGBColor(0x1E, 0x8A, 0x5A)
TEAL_PALE = RGBColor(0xE9, 0xF7, 0xF0)
ORANGE = RGBColor(0xBE, 0x6A, 0x18)
ORANGE_PALE = RGBColor(0xFF, 0xF3, 0xE6)
PAPER = RGBColor(0xF4, 0xF7, 0xFC)
RED = RGBColor(0xB9, 0x1C, 0x1C)

BAD_LITERALS = ["0,2584", "0,1364", "0,0474",
                "158.688", "6.219", "96.003"]


def set_round_rect_adjustments(shape, radius_in):
    try:
        avLst = shape._element.spPr.prstGeom.avLst
        for child in list(avLst):
            avLst.remove(child)
        val = int(max(0, min(0.5, radius_in / min(shape.width,
                                                 shape.height))) * 100000)
        from pptx.oxml.xmlchemy import OxmlElement
        gd = OxmlElement("a:gd")
        gd.set("name", "adj")
        gd.set("fmla", "val %d" % val)
        avLst.append(gd)
    except Exception:
        pass


def add_panel(slide, left, top, width, height, fill, line=None,
              radius_in=0.14, name="decor_panel", line_width=1.0):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left),
                                Inches(top), Inches(width), Inches(height))
    set_round_rect_adjustments(sh, radius_in)
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(line_width)
    sh.shadow.inherit = False
    sh.name = name
    return sh


def add_card(slide, left, top, width, height, accent, pale,
             kicker, title, lines, body_size=18, title_size=23,
             kicker_size=11, name="decor_card", head_h=0.72,
             body_gap=0.16, body_bottom=0.10, body_space_after=5.0):
    add_panel(slide, left, top, width, height, pale, accent,
              radius_in=0.16, name=name + "_bg", line_width=1.25)
    head = add_panel(slide, left + 0.10, top + 0.10, width - 0.20, head_h,
                     accent, None, radius_in=0.12, name=name + "_head")
    tf = head.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.vertical_anchor = 3
    tf.margin_left = tf.margin_right = Inches(0.08)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = kicker
    r.font.size = Pt(kicker_size)
    r.font.bold = True
    r.font.name = "Tahoma"
    r.font.color.rgb = WHITE
    p = tf.add_paragraph()
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = title
    r.font.size = Pt(title_size)
    r.font.bold = True
    r.font.name = "Tahoma"
    r.font.color.rgb = WHITE

    body = slide.shapes.add_textbox(
        Inches(left + 0.14), Inches(top + head_h + body_gap),
        Inches(width - 0.28),
        Inches(height - head_h - body_gap - body_bottom))
    body.name = name + "_body"
    tf = body.text_frame
    tf.clear()
    tf.word_wrap = True
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(body_space_after)
        p.line_spacing = 1.0
        r = p.add_run()
        r.text = line
        r.font.size = Pt(body_size)
        r.font.name = "Tahoma"
        r.font.color.rgb = DARK
    return body


def add_banner(slide, left, top, width, height, text, fill=None, size=15,
               color=None, bold=False, name="decor_banner",
               align=PP_ALIGN.CENTER):
    if fill is None:
        fill = NAVY
    if color is None:
        color = WHITE
    sh = add_panel(slide, left, top, width, height, fill, None,
                   radius_in=0.14, name=name)
    tf = sh.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.vertical_anchor = 3
    tf.margin_left = tf.margin_right = Inches(0.16)
    tf.margin_top = tf.margin_bottom = Inches(0.04)
    for i, line in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(2)
        p.line_spacing = 1.0
        r = p.add_run()
        r.text = line
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.name = "Tahoma"
        r.font.color.rgb = color
    return sh


def add_stat_card(slide, left, top, width, height, big, label, accent, pale,
                  name="decor_stat", big_size=26, label_size=15):
    add_panel(slide, left, top, width, height, pale, accent,
              radius_in=0.12, name=name + "_bg", line_width=1.0)
    tb = slide.shapes.add_textbox(Inches(left + 0.08), Inches(top + 0.05),
                                  Inches(width - 0.16), Inches(height - 0.10))
    tb.name = name + "_text"
    tf = tb.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.vertical_anchor = 3
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = big
    r.font.size = Pt(big_size)
    r.font.bold = True
    r.font.name = "Tahoma"
    r.font.color.rgb = accent
    p = tf.add_paragraph()
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    r.font.size = Pt(label_size)
    r.font.name = "Tahoma"
    r.font.color.rgb = DARK
    return tb


def add_thinking_card(slide, left, top, width, height, accent, pale,
                      badge, title, steps, examples):
    add_panel(slide, left, top, width, height, pale, accent,
              radius_in=0.20, name="decor_think_bg", line_width=1.5)
    head = add_panel(slide, left + 0.12, top + 0.12, width - 0.24, 0.80,
                     accent, None, radius_in=0.14, name="decor_think_head")
    tf = head.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.vertical_anchor = 3
    tf.margin_left = tf.margin_right = Inches(0.08)
    tf.margin_top = tf.margin_bottom = Inches(0.04)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = badge
    r.font.size = Pt(12)
    r.font.bold = True
    r.font.name = "Tahoma"
    r.font.color.rgb = WHITE
    p = tf.add_paragraph()
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = title
    r.font.size = Pt(22)
    r.font.bold = True
    r.font.name = "Tahoma"
    r.font.color.rgb = WHITE

    for i, step in enumerate(steps):
        chip = add_panel(slide, left + 0.18, top + 1.04 + i * 0.72,
                         width - 0.36, 0.62, WHITE, accent,
                         radius_in=0.12, name="decor_step_chip",
                         line_width=0.75)
        tf = chip.text_frame
        tf.clear()
        tf.word_wrap = True
        tf.vertical_anchor = 3
        tf.margin_left = Inches(0.14)
        tf.margin_right = Inches(0.08)
        tf.margin_top = tf.margin_bottom = Inches(0.03)
        p = tf.paragraphs[0]
        r = p.add_run()
        r.text = "%d. %s" % (i + 1, step)
        r.font.size = Pt(17)
        r.font.bold = True
        r.font.name = "Tahoma"
        r.font.color.rgb = DARK

    ex = add_panel(slide, left + 0.18, top + 3.26, width - 0.36, 1.16,
                   WHITE, accent, radius_in=0.12,
                   name="decor_example_box", line_width=0.75)
    tf = ex.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.vertical_anchor = 1
    tf.margin_left = Inches(0.14)
    tf.margin_right = Inches(0.10)
    tf.margin_top = Inches(0.08)
    tf.margin_bottom = Inches(0.05)
    p = tf.paragraphs[0]
    p.space_after = Pt(2)
    r = p.add_run()
    r.text = "Số thật từ đề tài"
    r.font.size = Pt(12)
    r.font.bold = True
    r.font.name = "Tahoma"
    r.font.color.rgb = accent
    for line in examples:
        p = tf.add_paragraph()
        p.space_after = Pt(1)
        p.line_spacing = 1.0
        r = p.add_run()
        r.text = line
        r.font.size = Pt(15)
        r.font.name = "Tahoma"
        r.font.color.rgb = DARK
    return ex


def add_arrow(slide, left, top, size=22, color=None):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(0.24),
                                  Inches(0.40))
    tb.name = "decor_arrow"
    tf = tb.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = "→"
    r.font.size = Pt(size)
    r.font.bold = True
    r.font.name = "Tahoma"
    r.font.color.rgb = color or ACCENT
    return tb


def add_table(slide, data, left, top, width, height, col_widths=None,
              header_size=14, body_size=14, name="decor_table"):
    rows, cols = len(data), len(data[0])
    shape = slide.shapes.add_table(rows, cols, Inches(left), Inches(top),
                                   Inches(width), Inches(height))
    shape.name = name
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
                                        PAPER if ri % 2 == 0 else WHITE)
            cell.text = str(val)
            cell.margin_top = Pt(2)
            cell.margin_bottom = Pt(2)
            cell.margin_left = Pt(4)
            cell.margin_right = Pt(4)
            for p in cell.text_frame.paragraphs:
                p.space_after = Pt(0)
                p.line_spacing = 1.0
                for r in p.runs:
                    r.font.size = Pt(header_size if ri == 0 else body_size)
                    r.font.name = "Tahoma"
                    r.font.bold = ri == 0
                    r.font.color.rgb = WHITE if ri == 0 else DARK
    return shape


def add_pic(slide, png, left, top, width_in):
    if not os.path.exists(png):
        raise SystemExit("Thiếu ảnh: " + png)
    sh = slide.shapes.add_picture(png, Inches(left), Inches(top),
                                  width=Inches(width_in))
    sh.name = "decor_pic"
    return sh


def add_caption(slide, text, left, top, width_in, size=13):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top),
                                  Inches(width_in), Inches(0.34))
    tb.name = "decor_caption"
    p = tb.text_frame.paragraphs[0]
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.italic = True
    r.font.color.rgb = GREY
    return tb


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
SW, SH = prs.slide_width, prs.slide_height


def add_slide(title=None, section=None, number=True, footer_label=None):
    s = prs.slides.add_slide(BLANK)
    idx = len(prs.slides._sldIdLst)

    strip = s.shapes.add_shape(1, Inches(0), Inches(0), SW, Inches(0.92))
    strip.name = "decor_header_strip"
    strip.fill.solid()
    strip.fill.fore_color.rgb = NAVY
    strip.line.fill.background()
    strip.shadow.inherit = False
    sp = s.shapes._spTree
    sp.remove(strip._element)
    sp.insert(2, strip._element)

    accent_line = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0),
                                     Inches(0.92), SW, Inches(0.035))
    accent_line.name = "decor_header_accent"
    accent_line.fill.solid()
    accent_line.fill.fore_color.rgb = ACCENT
    accent_line.line.fill.background()
    accent_line.shadow.inherit = False

    rail = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(7.46),
                              SW, Inches(0.04))
    rail.name = "decor_footer_rail"
    rail.fill.solid()
    rail.fill.fore_color.rgb = RGBColor(0xE3, 0xE9, 0xF2)
    rail.line.fill.background()
    rail.shadow.inherit = False

    if number:
        add_panel(s, 12.10, 6.98, 1.08, 0.42,
                  RGBColor(0xEC, 0xF0, 0xF7), None,
                  radius_in=0.12, name="decor_number_chip")
    if section:
        pill_w = min(6.0, max(2.4, 0.17 * len(section) + 0.9))
        add_panel(s, 0.42, 0.97, pill_w, 0.40, BLUE_PALE, None,
                  radius_in=0.12, name="decor_section_pill")
    if title:
        tb = s.shapes.add_textbox(Inches(0.38), Inches(0.08), Inches(12.4),
                                  Inches(0.66))
        tb.name = "decor_title"
        tf = tb.text_frame
        tf.word_wrap = False
        p = tf.paragraphs[0]
        r = p.add_run()
        r.text = title
        r.font.size = Pt(30)
        r.font.bold = True
        r.font.name = "Tahoma"
        r.font.color.rgb = WHITE
    if section:
        sb = s.shapes.add_textbox(Inches(0.55), Inches(1.00), Inches(12.2),
                                  Inches(0.34))
        sb.name = "decor_section"
        p = sb.text_frame.paragraphs[0]
        r = p.add_run()
        r.text = section
        r.font.size = Pt(13)
        r.font.italic = True
        r.font.color.rgb = GREY
    if number:
        nb = s.shapes.add_textbox(Inches(12.30), Inches(7.04), Inches(0.88),
                                  Inches(0.34))
        nb.name = "decor_number"
        p = nb.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.RIGHT
        r = p.add_run()
        r.text = footer_label or "%d / %d" % (idx, N_SLIDES)
        r.font.size = Pt(11)
        r.font.color.rgb = GREY
    return s


# =====================================================
# 20 SLIDE CHINH
# =====================================================

# ---- S1 ----
s = add_slide()
add_panel(s, 1.05, 1.15, 11.25, 0.10, ACCENT, None, radius_in=0.05,
          name="decor_top_line")
add_panel(s, 4.85, 3.92, 3.65, 0.08, TITLE_RED, None, radius_in=0.04,
          name="decor_mid_line")
tb = s.shapes.add_textbox(Inches(1.39), Inches(1.28), Inches(10.12),
                          Inches(0.70))
tb.name = "decor_course"
p = tb.text_frame.paragraphs[0]
p.alignment = PP_ALIGN.CENTER
r = p.add_run()
r.text = "HỌC PHẦN: PHƯƠNG PHÁP NGHIÊN CỨU KHOA HỌC TRONG CNTT"
r.font.size = Pt(19)
r.font.color.rgb = RGBColor(0x1D, 0x4E, 0xD7)

tb = s.shapes.add_textbox(Inches(0.79), Inches(2.42), Inches(11.69),
                          Inches(1.43))
tb.name = "decor_title_big"
p = tb.text_frame.paragraphs[0]
p.alignment = PP_ALIGN.CENTER
r = p.add_run()
r.text = ("Rò rỉ và thiên lệch trong hệ thống gợi ý:\n"
          "kiểm tra cách chia dữ liệu bằng Spark")
r.font.size = Pt(28)
r.font.bold = True
r.font.name = "Tahoma"
r.font.color.rgb = TITLE_RED

for x, label in ((1.55, "Cách chia dữ liệu"), (5.35, "Thước đo rò rỉ"),
                 (9.15, "Spark · MovieLens 25M")):
    add_banner(s, x, 4.16, 2.65, 0.46, label, fill=BLUE_PALE,
               size=14, color=ACCENT, bold=True, name="decor_topic_chip")

tb = s.shapes.add_textbox(Inches(1.39), Inches(5.02), Inches(10.5),
                          Inches(0.70))
tb.name = "decor_teacher"
p = tb.text_frame.paragraphs[0]
p.alignment = PP_ALIGN.CENTER
r = p.add_run()
r.text = "Giảng viên: TS. Trần Minh Thái · Khoa CNTT · HUFLIT"
r.font.size = Pt(17)
r.font.bold = True
r.font.name = "Arial"
r.font.color.rgb = NAVY_TXT

tb = s.shapes.add_textbox(Inches(1.39), Inches(5.72), Inches(10.5),
                          Inches(0.86))
tb.name = "decor_meta"
p = tb.text_frame.paragraphs[0]
p.alignment = PP_ALIGN.CENTER
r = p.add_run()
r.text = ("Vào: bảng chấm 25.000.095 dòng · Ra: phiếu chẩn đoán cho từng "
          "cách chia\nSinh viên: Trần Khôi Nguyên (MIT26004) · HUFLIT · 11/2026")
r.font.size = Pt(15)
r.font.italic = True
r.font.color.rgb = GREY

add_banner(s, 0.85, 6.68, 11.1, 0.40,
           "Trọng tâm: quy trình kiểm tra, không phải demo hạ tầng.",
           fill=PAPER, size=13, color=GREY, name="decor_scope_chip")
notes(s, "Chào hội đồng. Đề tài nhận vào một bảng chấm phim, trả ra một phiếu "
         "chẩn đoán cho mỗi cách chia dữ liệu. Tiêu đề gồm phương pháp + mục "
         "tiêu + phạm vi. Không nhận mô hình gợi ý mới; mô hình chỉ là công cụ "
         "để kiểm tra cách chia.")

# ---- S2 ----
s = add_slide("Bố cục trình bày")
parts = [
    ("CHƯƠNG 1", "20%", "Hiểu dữ liệu", ["Dữ liệu và cách tư duy"], ACCENT, BLUE_PALE),
    ("CHƯƠNG 2", "30%", "Câu hỏi & tài liệu", ["6 câu hỏi, 13 bài"], TEAL, TEAL_PALE),
    ("CHƯƠNG 3", "45%", "Đề cương", ["Mục tiêu, kết quả, kế hoạch"], ORANGE, ORANGE_PALE),
    ("KẾT LUẬN", "5%", "Tự đánh giá", ["Giới hạn và hướng thêm"], NAVY, PAPER),
]
for i, (chapter, pct, name, lines, accent, pale) in enumerate(parts):
    x = 0.55 + i * 3.10
    add_stat_card(s, x, 1.48, 2.90, 0.92, pct, chapter, accent, pale,
                  name="decor_part_%d" % i)
    add_card(s, x, 2.54, 2.90, 2.85, accent, pale, chapter, name, lines,
             body_size=18, title_size=20, name="decor_part_card_%d" % i)
    if i < 3:
        add_arrow(s, x + 2.88, 3.70, size=20, color=GREY)
add_banner(s, 0.55, 5.78, 12.15, 0.66,
           "12 phút trình bày + 5–8 phút hỏi đáp. Chương 3 nhận nhiều thời gian nhất.",
           fill=PAPER, size=15, color=GREY, name="decor_time_banner")
notes(s, "Bố cục bám hướng dẫn: 20/30/45/5. Chương 3 dài nhất vì ở đó nói rõ "
         "input, output, cách đo và kết quả.")

# ---- S3 ----
s = add_slide("Từ dữ liệu đến quyết định",
              "Có gì → thấy gì → hiểu gì → làm gì")
steps = [
    ("Dữ liệu", "Có gì", [
        "25.000.095 lượt chấm.",
        "162.541 người · 59.047 phim.",
        "Ai · phim nào · mấy sao · lúc nào.",
    ], ACCENT, BLUE_PALE),
    ("Thông tin", "Thấy gì", [
        "0 dòng trùng.",
        "1.799.454 nhóm chấm cùng giây.",
        "8,76% dòng test là phim chưa từng có trong train.",
    ], TEAL, TEAL_PALE),
    ("Hiểu ra", "Hiểu gì", [
        "Cùng ALS, chỉ đổi cách chia:",
        "0,2581 → 0,0469.",
        "Thấp hơn 5,5 lần.",
    ], ORANGE, ORANGE_PALE),
    ("Quyết định", "Làm gì", [
        "Xem rò rỉ trước, điểm số sau.",
        "Rồi xem bao nhiêu người được chấm.",
        "Lệch > 1,20 thì cấm nói 'tốt hơn'.",
    ], NAVY, PAPER),
]
for i, (title, kicker, lines, accent, pale) in enumerate(steps):
    x = 0.55 + i * 3.10
    add_card(s, x, 1.48, 2.90, 4.42, accent, pale, kicker, title, lines,
             body_size=18, title_size=20, name="decor_diku_%d" % i)
    if i < 3:
        add_arrow(s, x + 2.88, 3.40, size=20, color=accent)
add_banner(s, 0.55, 6.06, 12.15, 0.66,
           "8,76% ở đây là dòng test trỏ tới phim chưa từng có trong train, "
           "không phải 'người dùng chưa chấm phim đó'.",
           fill=PAPER, size=14, color=GREY, name="decor_diku_footer")
notes(s, "Bốn bước DIKW. Con số 8,76% tính trên dòng test, so với toàn bộ "
         "train — gọi là phim mới hoàn toàn (item cold-start). Câu cũ 'người "
         "dùng chưa từng chấm' là sai: mọi cặp user-item trong test đều chưa "
         "từng được chấm, nếu hiểu vậy phải là 100%.")

# ---- S4 ----
s = add_slide("Cách tư duy áp dụng",
              "Có quy luật sẵn · nhìn nhiều lần · thấy lạ thì kiểm tra lại")
add_thinking_card(
    s, 0.55, 1.48, 3.85, 4.62, ACCENT, BLUE_PALE,
    "Cách 1", "Có quy luật sẵn",
    ["Bắt đầu từ điều đã biết", "Áp vào trường hợp trước mặt",
     "Thấy khác thì sửa cách hiểu"],
    ["Bài trước: so công bằng cần cùng mốc thời gian.",
     "Random lộ 98,92%; giữ cuối lộ 0%.",
     "Một trường hợp ngược đủ bác cách hiểu cũ."])
add_thinking_card(
    s, 4.74, 1.48, 3.85, 4.62, TEAL, TEAL_PALE,
    "Cách 2 · CHỦ ĐẠO", "Nhìn nhiều rồi kết luận",
    ["Thử nhiều trường hợp", "Rút ra quy luật chung",
     "Kết luận từ dữ liệu thật"],
    ["3 cách chia × 5 mô hình × 25 triệu dòng.",
     "Điểm đổi theo cách chia, không chỉ theo mô hình.",
     "Chọn cách làm này vì số liệu tự nói."])
add_thinking_card(
    s, 8.93, 1.48, 3.85, 4.62, ORANGE, ORANGE_PALE,
    "Cách 3", "Thấy lạ → đoán → đếm",
    ["Thấy điểm bất thường", "Đoán nguyên nhân", "Đếm lại để kiểm chứng"],
    ["Cùng ALS: 0,2581 rồi 0,0469.",
     "Đoán: trộn ngẫu nhiên để lộ tương lai.",
     "Đếm: 98,92% dòng test cũ hơn lượt mới nhất."])
for arrow_x in (4.47, 8.66):
    add_arrow(s, arrow_x, 3.45, size=22, color=ACCENT)
add_banner(s, 0.55, 6.20, 12.15, 0.56,
           "Cách 2 là cách làm chính. Cách 1 dùng lý thuyết có sẵn; "
           "cách 3 là bước kiểm chứng thêm.",
           fill=NAVY, size=14, color=WHITE, bold=True, name="decor_think_band")
notes(s, "Diễn dịch: bài TOIS 41(3) gợi ý cần cùng mốc thời gian; thử trên "
         "dữ liệu thì random có SLI theo người 98,9158%, giữ lượt cuối 0%. "
         "Một phản ví dụ đủ bác cách hiểu 'cứ giữ cuối là rò rỉ'. Quy nạp là "
         "chủ đạo vì kết luận rút từ 3 cách chia × 5 mô hình. Suy đoán: thấy "
         "ALS rơi từ 0,2581 xuống 0,0469, đoán do trộn ngẫu nhiên, rồi đếm "
         "98,9158% để xác nhận. Không đụng số cũ 0,2584/0,0474.")

# ---- S5 ----
s = add_slide("6 câu hỏi của bài toán", "Hỏi đúng thì làm đúng")
questions = [
    ("Cái gì?", "Chia dữ liệu", ["Trộn, cắt theo thời gian,", "giữ lượt cuối."], ACCENT, BLUE_PALE),
    ("Ai?", "Ai bị ảnh hưởng", ["Người đọc kết quả gợi ý.", "Người có ít phim dễ bị che."], TEAL, TEAL_PALE),
    ("Khi nào?", "Phạm vi", ["Phim 1995–2019, chạy Spark.", "Nghiên cứu 11/2026–06/2027."], ORANGE, ORANGE_PALE),
    ("Vì sao?", "Lý do", ["Chia sai thì điểm phóng đại.", "Chọn nhầm mô hình."], NAVY, PAPER),
    ("Bao nhiêu?", "Mức chênh", ["ALS 0,2581 → 0,0469.", "Giảm 5,5 lần."], ACCENT, BLUE_PALE),
    ("Làm sao?", "Cách kiểm tra", ["Rò rỉ → số người → điểm số.", "3 cách chia × 5 mô hình."], TEAL, TEAL_PALE),
]
for i, (title, kicker, lines, accent, pale) in enumerate(questions):
    col, row = i % 3, i // 3
    add_card(s, 0.55 + col * 4.17, 1.42 + row * 2.26, 3.85, 2.06,
             accent, pale, kicker, title, lines,
             body_size=18, title_size=21, name="decor_q_%d" % i)
add_banner(s, 0.55, 6.02, 12.15, 0.56,
           "Chuỗi câu chuyện: thực trạng → hậu quả → tài liệu chưa giải quyết "
           "→ đề tài làm gì.",
           fill=PAPER, size=15, color=GREY, name="decor_problem_banner")
notes(s, "W5H2. Thực trạng: đa số bài dùng random hoặc giữ cuối. Hậu quả: "
         "điểm phóng đại và thứ hạng có thể đảo. Giải pháp: phiếu chẩn đoán "
         "gồm SLI + số người + kết luận.")

# ---- S6 ----
s = add_slide("Đầu vào là gì", "Một bảng chấm phim, bốn cột, 25 triệu dòng")
for i, (big, lab, col, pale) in enumerate([
    ("25.000.095", "lượt chấm", ACCENT, BLUE_PALE),
    ("162.541", "người dùng", TEAL, TEAL_PALE),
    ("59.047", "phim", ORANGE, ORANGE_PALE),
    ("24,8 năm", "1995 → 2019", NAVY, PAPER),
]):
    add_stat_card(s, 0.60 + i * 3.10, 1.42, 2.90, 1.02, big, lab,
                  col, pale, name="decor_input_stat_%d" % i,
                  big_size=24, label_size=15)
add_table(s, [
    ["userId", "movieId", "rating", "timestamp"],
    ["1", "31", "4,0", "1995-01-09 08:01:05"],
    ["1", "1029", "3,0", "1995-01-09 08:02:12"],
    ["2", "2957", "5,0", "1995-01-10 09:14:33"],
], 0.60, 2.72, 12.15, 1.88, col_widths=[2, 2, 2, 4],
    header_size=16, body_size=16, name="decor_input_table")
add_banner(s, 0.60, 4.86, 12.15, 0.82,
           "Mỗi dòng kể một chuyện: ai chấm · phim nào · mấy sao · lúc nào. "
           "Chỉ cần bốn cột này để tạo ba cách chia và chạy năm mô hình.",
           fill=BLUE_PALE, size=16, color=NAVY_TXT, name="decor_input_note")
add_banner(s, 0.60, 5.86, 12.15, 0.62,
           "Nguồn: MovieLens 25M · Harper & Konstan, TIST 5(4), 2015 · "
           "DOI 10.1145/2827872 · dữ liệu ẩn danh.",
           fill=PAPER, size=14, color=GREY, name="decor_input_src")
notes(s, "Đây là đầu vào duy nhất. Không thêm ảnh, text hay metadata ngoài "
         "bốn cột. rating dùng ngưỡng ≥4 để coi là 'phim liên quan'. timestamp "
         "là mốc thời gian để kiểm tra rò rỉ.")

# ---- S7 ----
s = add_slide("Đầu ra là gì", "Bốn vật thể có tên file, có thể cầm được")
add_pic(s, os.path.join(FIGS, "fig_io.png"), 0.55, 1.34, 12.15)
add_caption(s, "O1 = audit_report.json · O2 = src/audit/leakage.py · "
               "O3 = giao thức 3 bước · O4 = scripts/ + runs/ + Streamlit.",
            0.55, 6.62, 12.15, size=13)
notes(s, "O1 = docs/Project/Main/Presentation/Slides/audit_report.json: một "
         "phiếu cho mỗi cách chia, có SAFE/WARN/BLOCK kèm lý do. O2 = "
         "src/audit/leakage.py: công thức SLI. O3 = giao thức ba bước. O4 = "
         "pipeline chạy lại được gồm scripts/, runs/ và Streamlit. Nói với "
         "hội đồng: đề tài trả về một nhãn cho mỗi cách chia, giống như bài "
         "phân loại ảnh trả về một nhãn cho mỗi ảnh.")

# ---- S8 ----
s = add_slide("Kiểm tra tài liệu", "10 bài đánh giá/chia tập · 3 bài gốc mô hình")
add_stat_card(s, 0.60, 1.42, 3.90, 0.92, "10", "bài Nhóm A", ACCENT, BLUE_PALE,
              name="decor_doc_n")
add_stat_card(s, 4.70, 1.42, 3.90, 0.92, "9", "CORE A*/A", TEAL, TEAL_PALE,
              name="decor_doc_quality")
add_stat_card(s, 8.80, 1.42, 3.90, 0.92, "0", "bài chỉ có arXiv", ORANGE,
              ORANGE_PALE, name="decor_doc_arxiv")
add_table(s, [
    ["Nguồn", "Xếp hạng", "Số bài"],
    ["ACM TOIS / TORS", "Q1 · CORE A", "4"],
    ["ACM RecSys ('20, '21, '25, '26)", "Q1 · CORE A*", "5"],
    ["Springer UMAI 2024", "Q1", "1"],
], 0.60, 2.54, 7.20, 2.30, col_widths=[4.0, 2.0, 1.0],
    header_size=14, body_size=14, name="decor_doc_table")
add_card(s, 8.05, 2.54, 4.70, 2.90, ACCENT, BLUE_PALE,
         "Cách lọc", "Chỉ giữ bản có thật", [
             "Lấy bản ACM/IEEE/Springer có DOI.",
             "Bỏ bản arXiv chưa duyệt.",
             "Ghi sha256 cho từng PDF.",
             "Mỗi bài có mã đối chiếu trong _manifest.json.",
         ], body_size=18, title_size=21, name="decor_doc_check")
add_banner(s, 0.60, 5.66, 12.15, 0.70,
           "Nhóm B gồm 3 bài gốc mô hình, đã verify DOI trên Crossref ngày "
           "2026-11-24; chỉ trích, chưa tải PDF.",
           fill=PAPER, size=14, color=GREY, name="decor_doc_footer")
notes(s, "Quy trình: DOI từ Crossref/OpenAlex → chỉ lấy bản nhà xuất bản → "
         "kiểm tra /Creator bằng pypdf → tra SCImago/CORE → ghi sha256. "
         "Không viện dẫn arXiv. Ba bài Nhóm B có DOI nhưng chưa có PDF trên "
         "máy, ghi rõ trạng thái referenced-not-downloaded.")

# ---- S9 ----
s = add_slide("Mô hình đối chuẩn đi với bài nào",
              "Mỗi mô hình có bài gốc hoặc khai báo rõ là sàn tầm thường")
add_table(s, [
    ["Mô hình", "Tầng", "Bài gốc", "Bài trong corpus dùng nó"],
    ["Random", "Sàn", "Không có; khai báo là sàn tầm thường", "Không trích"],
    ["MostPopular", "Sàn", "Không có bài gốc riêng", "[2] Daniil, TORS 2(1)"],
    ["ItemKNN cosine", "Kinh điển", "Sarwar, WWW 2001", "[2] · [4]"],
    ["ALS implicit", "Kinh điển", "Hu et al., ICDM 2008", "[4] L246"],
    ["SASRec + CE", "Mới", "Kang & McAuley, ICDM 2018", "[1] · [3] dùng làm baseline"],
], 0.45, 1.42, 12.45, 3.62,
    col_widths=[2.0, 1.4, 3.6, 4.6], header_size=15, body_size=15,
    name="decor_baseline_table")
add_banner(s, 0.45, 5.24, 12.45, 1.02,
           "DOI đầy đủ nằm ở phụ lục A4.\n"
           "[1] và [3] dùng SASRec làm baseline: trích [3] cho cách huấn luyện "
           "CE, trích bài ICDM 2018 cho kiến trúc. Không nhầm 'tái lập bài báo' "
           "với 'dùng mô hình của bài báo'.",
           fill=BLUE_PALE, size=14, color=NAVY_TXT,
           name="decor_baseline_note")
notes(s, "Group B: Sarwar et al., Item-based collaborative filtering, WWW "
         "2001, DOI 10.1145/371920.372071. Hu, Koren, Volinsky, Collaborative "
         "Filtering for Implicit Feedback Datasets, ICDM 2008, DOI "
         "10.1109/ICDM.2008.22. Kang & McAuley, Self-Attentive Sequential "
         "Recommendation, ICDM 2018, DOI 10.1109/ICDM.2018.00035. Random và "
         "MostPopular không có bài gốc thì nói thẳng, không bịa DOI.")

# ---- S10 ----
s = add_slide("Bài trước làm được gì, còn thiếu gì",
              "Con số lấy trực tiếp từ bản nhà xuất bản")
add_table(s, [
    ["Bài", "Họ làm gì", "Con số thật", "Chỗ đề tài làm tiếp"],
    ["Ji, TOIS 41(3)", "Xem thêm dữ liệu tương lai",
     "SASRec NDCG@20 −5,4% … +16,8%; Yelp −29,0% … −0,6%",
     "Chưa đo riêng từng người"],
    ["Daniil, TORS 2(1)", "Thử 11 thuật toán, chia nhóm người",
     "NeuMF đẩy item niche gấp ~4 lần: %ΔGAP 399,1 / 399,6",
     "Chưa báo chi phí"],
    ["Gusak, RecSys '25", "Khảo sát 75 bài + thử 3 mô hình chuỗi",
     "77,3% dùng giữ cuối; Beauty 0,022 → 0,040 (+81,8%)",
     "Chưa đo thiên lệch"],
    ["Meng, RecSys '20", "Đổi cách chia, 230 mô hình",
     "NMF 0,0879 → 0,1811 (2,06×); NeuMF 1,91×",
     "Chưa so chi phí"],
    ["Parajuli, RecSys '26", "So đánh giá thưa và dày",
     "Kendall τ 0,03–0,28; nhiều CI chứa 0",
     "Chưa gắn dữ liệu lớn"],
], 0.45, 1.40, 12.45, 3.92,
    col_widths=[2.1, 2.8, 4.6, 2.9], header_size=14, body_size=14,
    name="decor_matrix_table")
add_banner(s, 0.45, 5.52, 12.45, 0.84,
           "Nhìn chung: đổi cách chia thì điểm đổi 1,9–2,1 lần (Meng) hoặc "
           "thứ hạng gần như không ăn khớp (Parajuli). Đề tài đo được 5,5 lần "
           "trên ALS.",
           fill=PAPER, size=15, color=DARK, name="decor_matrix_footer")
notes(s, "Số lấy từ Table 5 của Ji, L302/L518–522/L1223–1231 của Daniil, "
         "L279–281/L842/L992/L1856/L1864 của Gusak, Table 3 L594–641 của "
         "Meng, Table 2 L459–513 của Parajuli. Không bài nào báo thời gian "
         "chạy cạnh điểm số, không bài nào có SLI riêng theo từng người.")

# ---- S11 ----
s = add_slide("Khoảng trống đề tài lấp vào", "Ba cái còn thiếu, một cách làm")
gaps = [
    ("Thiếu người", "Chưa ai đo rò rỉ riêng từng người",
     "Ji tính gộp cả bảng test. Đề tài thêm SLI cho từng người.",
     ACCENT, BLUE_PALE),
    ("Thiếu chi phí", "Chưa ai báo thời gian cạnh điểm số",
     "Đề tài ghi giây cho từng mô hình trên cùng một máy.",
     TEAL, TEAL_PALE),
    ("Thiếu công bằng", "Chưa ai so số người trước khi so điểm",
     "Lệch hơn 1,20 lần thì dừng, không nói 'tốt hơn'.",
     ORANGE, ORANGE_PALE),
]
for i, (kicker, title, line, accent, pale) in enumerate(gaps):
    add_card(s, 0.55 + i * 4.17, 1.48, 3.85, 2.62, accent, pale,
             kicker, title, [line], body_size=18, title_size=21,
             name="decor_gap_%d" % i)
add_banner(s, 0.55, 4.42, 12.15, 1.12,
           "Cần một phiếu chẩn đoán cho mỗi cách chia:\n"
           "rò rỉ → bao nhiêu người được chấm → kết luận. Xong mới đọc điểm.",
           fill=NAVY, size=19, color=WHITE, bold=True, name="decor_gap_band")
add_banner(s, 0.55, 5.78, 12.15, 0.62,
           "Đề tài không nhận mô hình mới, không nhận miền dữ liệu mới. "
           "Đóng góp là cách kiểm tra.",
           fill=PAPER, size=15, color=GREY, name="decor_gap_scope")
notes(s, "Critical Gap = chưa có nghiên cứu nào đo cùng lúc rò rỉ theo từng "
         "người + thiên lệch + chi phí trên một pipeline dữ liệu lớn. Theo "
         "phân loại đóng góp của bài giảng: bài toán một phần, phương pháp "
         "chính, miền ứng dụng không, lý giải một phần.")

# ---- S12 ----
s = add_slide("Mục tiêu và câu hỏi", "Mỗi mục tiêu trả lời đúng một câu hỏi")
add_banner(s, 0.55, 1.34, 12.15, 1.06,
           "Mục tiêu chung: Đo và giải thích cách chia dữ liệu đổi tín hiệu "
           "đo và thiên lệch trên Spark, MovieLens 25M.\n"
           "Câu hỏi chính: Đổi cách chia thì điểm và độ thiên lệch đổi bao "
           "nhiêu, khi dữ liệu, seed 42 và ngân sách chỉnh giữ nguyên?",
           fill=BLUE_PALE, size=15, color=NAVY_TXT, bold=True,
           name="decor_goal_banner")
sos = [
    ("SO1 · Dữ liệu", "20%", ["Đối chuẩn 25.000.095 dòng.",
                             "Đếm 323.737 khóa phổ biến."], ACCENT, BLUE_PALE),
    ("SO2 · Thước đo", "40%", ["Đề xuất SLI theo từng người.",
                              "Viết giao thức 3 bước."], TEAL, TEAL_PALE),
    ("SO3 · Đối chuẩn", "20%", ["Chạy 5 mô hình × 3 cách chia.",
                               "Đo đổi thứ hạng."], ORANGE, ORANGE_PALE),
    ("SO4 · Độ nhạy", "20%", ["Đổi ngưỡng liên quan, subsample.",
                             "So sánh 2 cách tính SLI."], NAVY, PAPER),
]
for i, (title, kicker, lines, accent, pale) in enumerate(sos):
    add_card(s, 0.55 + i * 3.10, 2.56, 2.90, 2.24, accent, pale,
             kicker, title, lines, body_size=18, title_size=19,
             name="decor_so_%d" % i)
add_banner(s, 0.55, 4.98, 12.15, 1.32,
           "RQ1 ↔ SO3: thứ hạng đổi bao nhiêu? · RQ2 ↔ SO4: độ phủ và mới lạ "
           "đổi thế nào?\n"
           "RQ3 ↔ SO1: mỗi cách chia tốn bao nhiêu thời gian? · "
           "RQ4 ↔ SO2: giao thức 3 bước giữ tín hiệu đo ra sao?\n"
           "RQ5 (mở rộng, chưa cam kết): sang Amazon 2023 / Steam thì còn đúng "
           "không?",
           fill=PAPER, size=14, color=DARK, name="decor_rq_banner")
add_banner(s, 0.55, 6.44, 12.15, 0.44,
           "Kiểm định: Wilcoxon từng cặp · Friedman khi ≥3 mô hình · "
           "bác bỏ H0 khi p < 0,05.",
           fill=RGBColor(0xEC, 0xF0, 0xF7), size=13, color=NAVY,
           name="decor_hyp_banner")
notes(s, "Ánh xạ khép kín SO1↔RQ3, SO2↔RQ4, SO3↔RQ1, SO4↔RQ2. RQ5 để mở "
         "rộng, không gán SO. SO2 nặng 40% vì tạo ra SLI và giao thức. Mới "
         "1 seed 42; chạy 20 cặp Wilcoxon và Friedman trên 5.000 user chung.")

# ---- S13 ----
s = add_slide("Đề tài này có đáng làm không", "Năm câu tự kiểm, mỗi câu có bằng chứng")
finer = [
    ("Làm được", "Dữ liệu đã tải, thử nghiệm chạy xong trước hạn.", ACCENT, BLUE_PALE),
    ("Đáng hỏi", "Hỏi 'cách đo đúng chưa' quan trọng hơn 'ai cao hơn'.", TEAL, TEAL_PALE),
    ("Có mới", "Giữ cuối: gộp 99,9988%, riêng từng người 0%.", ORANGE, ORANGE_PALE),
    ("Đúng đạo đức", "Dữ liệu ẩn danh, có trích nguồn rõ.", NAVY, PAPER),
    ("Dùng được", "Phiếu chẩn đoán dùng cho tập có mốc thời gian.", TEAL, TEAL_PALE),
]
for i, (title, body, accent, pale) in enumerate(finer):
    add_card(s, 0.60 + i * 2.45, 1.48, 2.30, 4.30, accent, pale,
             "Tiêu chí %d" % (i + 1), title, [body],
             body_size=18, title_size=19, name="decor_finer_%d" % i)
add_banner(s, 0.60, 5.98, 12.10, 0.56,
           "FINER = Feasible · Interesting · Novel · Ethical · Relevant. "
           "Tên đầy đủ để trong ghi chú slide.",
           fill=PAPER, size=14, color=GREY, name="decor_finer_footer")
notes(s, "Feasible dữ liệu và máy đã có. Interesting câu hỏi đúng cách đo. "
         "Novel chính là hai cách tính SLI cho kết luận ngược nhau ở leave-one-"
         "out. Ethical dữ liệu MovieLens ẩn danh. Relevant phiếu chẩn đoán "
         "dùng được cho bất kỳ tập có timestamp.")

# ---- S14 ----
s = add_slide("Quy trình chạy thật", "Bốn tầng, có đầu vào trái và đầu ra phải")
add_pic(s, os.path.join(FIGS, "fig_architecture.png"), 0.45, 1.36, 8.10)
layers = [
    ("Chứa dữ liệu", "CSV 25M → Parquet, Spark đọc.", ACCENT, BLUE_PALE),
    ("Xử lý lớn", "MapReduce + Spark, 323.737 khóa.", TEAL, TEAL_PALE),
    ("Lưu kết quả", "MongoDB, 42 trường/phiếu.", ORANGE, ORANGE_PALE),
    ("Xem & kiểm định", "R + Streamlit + Wilcoxon.", NAVY, PAPER),
]
for i, (title, line, accent, pale) in enumerate(layers):
    add_card(s, 8.75, 1.36 + i * 1.27, 4.05, 1.15, accent, pale,
             "Tầng %d" % (i + 1), title, [line],
             body_size=18, title_size=19, kicker_size=10,
             head_h=0.42, body_gap=0.10, body_bottom=0.06,
             body_space_after=2, name="decor_layer_%d" % i)
add_banner(s, 0.45, 5.86, 12.35, 0.60,
           "MapReduce xong 2026-11-04; container đã gỡ nhưng dựng lại được. "
           "10/10 bước kiểm tra đạt; SASRec chạy GPU riêng.",
           fill=PAPER, size=14, color=GREY, name="decor_arch_footer")
notes(s, "Bốn tầng: lưu trữ Parquet + Spark; xử lý MapReduce Java và PySpark "
         "local[4]; lưu chỉ số MongoDB; xem bằng R và Streamlit. Không nhầm "
         "đây là đóng góp — đây là cách chạy để có phiếu chẩn đoán.")

# ---- S15 ----
s = add_slide("Cách đo rò rỉ và độ đúng", "Công thức viết bằng lời, dễ nhớ")
metrics = [
    ("Công thức", "Rò rỉ (SLI)", [
        "Đếm dòng test cũ hơn lượt mới nhất của chính người đó.",
        "Chia cho tổng dòng test của người đó.",
        "Rồi lấy trung bình trên mọi người.",
    ], ACCENT, BLUE_PALE),
    ("Ngưỡng tự đặt", "3 mức", [
        "Dưới 0,05: sạch.",
        "0,05–0,30: còn lẫn.",
        "Từ 0,30: không dùng.",
    ], TEAL, TEAL_PALE),
    ("Độ đúng", "NDCG / MRR", [
        "NDCG@10: phim đứng càng cao càng có giá.",
        "MRR@10: phim đúng đầu tiên càng sớm càng tốt.",
        "Hit@10: có ít nhất 1 phim đúng trong top-10.",
    ], ORANGE, ORANGE_PALE),
    ("Độ phủ", "Coverage / Novelty", [
        "Coverage: bao nhiêu phim trong catalog được đề xuất.",
        "Novelty: phim ít người chấm thì điểm cao hơn.",
    ], NAVY, PAPER),
]
for i, (kicker, title, lines, accent, pale) in enumerate(metrics):
    add_card(s, 0.55 + i * 3.10, 1.42, 2.90, 3.72, accent, pale,
             kicker, title, lines, body_size=18, title_size=20,
             name="decor_metric_%d" % i)
add_banner(s, 0.55, 5.38, 12.15, 1.00,
           "8,76% dòng test trỏ tới phim chưa từng có trong train — đây là "
           "phim mới hoàn toàn, không phải 'người dùng chưa chấm phim đó'.\n"
           "Ba ngưỡng 0,05 / 0,30 do đề tài tự đặt, không phải chuẩn có sẵn "
           "trên tạp chí.",
           fill=ORANGE_PALE, size=15, color=DARK, name="decor_metric_footer")
notes(s, "SLI_u = |{(u,i,t) trong test(u): t < t_max(u)}| / |test(u)|; "
         "SLI = trung bình trên user. SLI_global so với T_max(train), dấu "
         "< nghiêm ngặt; hai timestamp bằng nhau không tính rò rỉ. NDCG dùng "
         "log2(rank+1). Ngưỡng SAFE/WARN/BLOCK là do đề tài chọn, không phải "
         "từ TOIS 41(3). TOIS chỉ gợi ý nên quan sát mốc thời gian toàn cục "
         "và cũng thừa nhận giữ lượt cuối có nét tương tự.")

# ---- S16 ----
s = add_slide("Năm mô hình dùng để thử", "Ba nhóm rõ ràng, cùng seed, cùng top-10")
groups = [
    ("Sàn", "Random · MostPopular", [
        "Random chọn ngẫu nhiên trong catalog.",
        "MostPopular chọn phim nhiều chấm nhất.",
    ], ACCENT, BLUE_PALE),
    ("Kinh điển", "ItemKNN · ALS", [
        "ItemKNN tìm phim giống phim đã thích.",
        "ALS học từ lịch sử chấm ẩn.",
    ], TEAL, TEAL_PALE),
    ("Mới", "SASRec + CE", [
        "Đoán phim tiếp theo bằng self-attention.",
        "Chạy riêng trên GPU, không so thời gian CPU.",
    ], ORANGE, ORANGE_PALE),
]
for i, (kicker, title, lines, accent, pale) in enumerate(groups):
    add_card(s, 0.55 + i * 4.17, 1.42, 3.85, 2.72, accent, pale,
             kicker, title, lines, body_size=18, title_size=21,
             name="decor_group_%d" % i)
add_banner(s, 0.55, 4.42, 12.15, 1.18,
           "Cùng settings: k = 10 · seed 42 · rating ≥ 4 là liên quan.\n"
           "ALS rank 16, alpha 10 · ItemKNN 100 hàng xóm · SASRec độ dài 50, "
           "1 block, 1 head, lr 0,001.\n"
           "Bốn mô hình chạy Spark CPU local[4]; SASRec chạy RTX 4050 6 GB.",
           fill=PAPER, size=15, color=DARK, name="decor_param_banner")
add_banner(s, 0.55, 5.80, 12.15, 0.58,
           "Tham số chi tiết hơn ở phụ lục A3. Không dùng EASE, không so "
           "thời gian CPU với GPU.",
           fill=BLUE_PALE, size=14, color=NAVY_TXT, name="decor_param_note")
notes(s, "SASRec + CE là đối chuẩn SOTA chạy lại, không phải mô hình thắng. "
         "Tuning budget = 0 cho SASRec theo run; các baseline dùng cấu hình "
         "cố định. Không so runtime CPU/GPU vì phần cứng khác nhau.")

# ---- S17 ----
s = add_slide("Kết quả: chia khác, điểm đổi", "Số thật 20/11/2026 · NDCG@10")
add_pic(s, os.path.join(FIGS, "fig_sli.png"), 0.40, 1.34, 5.55)
add_pic(s, os.path.join(FIGS, "fig_interaction.png"), 6.15, 1.46, 6.75)
add_caption(s, "Giữ cuối: gộp 99,9988%, riêng từng người 0% — hai cách "
               "đếm cho kết luận ngược nhau.",
            0.40, 3.96, 5.55, size=12)
add_table(s, [
    ["Mô hình", "Trộn ngẫu nhiên", "Theo mốc thời gian", "Giữ lượt cuối"],
    ["ItemKNN", "0,2679", "0,1409", "0,0461"],
    ["ALS", "0,2581", "0,1332", "0,0469"],
    ["SASRec + CE", "0,0163", "0,0187", "0,0067"],
    ["MostPopular", "0,0852", "0,0455", "0,0183"],
    ["Random", "0,0003", "0,0009", "0,0001"],
], 0.40, 4.36, 12.50, 1.44,
    col_widths=[2.6, 3.0, 3.4, 3.0], header_size=14, body_size=14,
    name="decor_result_table")
add_banner(s, 0.40, 5.98, 12.50, 0.92,
           "Phiếu chẩn đoán: trộn ngẫu nhiên BLOCK (SLI 98,92%); "
           "theo mốc thời gian BLOCK (chỉ 6.214 người, ít hơn 25,5 lần); "
           "giữ cuối BLOCK khi so sánh (95.977 người, ít hơn 1,65 lần).",
           fill=ORANGE_PALE, size=14, color=DARK, name="decor_verdict_banner")
notes(s, "Số NDCG lấy từ runs/20261120_012944.../comparison.json. Mỗi split "
         "tính trên đúng tập người đủ điều kiện của split đó, nên không được "
         "coi là so sánh ghép cặp giữa các split. ItemKNN dẫn ở random và "
         "temporal; ALS dẫn ở LOO nhưng p = 0,153 với ItemKNN, CI chứa 0. "
         "Mới 1 seed, không báo Mean±Std. Bảng đầy đủ 10 cột ở A1; 20 cặp "
         "kiểm định ở A2.")

# ---- S18 ----
s = add_slide("Hiệu quả, rủi ro, kế hoạch", "Chặn sớm để khỏi kết luận sai")
add_card(s, 0.55, 1.42, 6.05, 2.10, ACCENT, BLUE_PALE,
         "Hiệu quả", "Cách làm chặn sai sớm", [
             "Một phiếu mất khoảng 2 phút.",
             "3/3 cặp chia lệch > 1,20 lần.",
             "Có 3 kết quả: SLI, giao thức, pipeline.",
             "Chỉ nói 'điểm cao hơn trên mẫu khác'.",
         ], body_size=18, title_size=20, name="decor_roi")
add_card(s, 0.55, 3.70, 6.05, 1.94, ORANGE, ORANGE_PALE,
         "Rủi ro", "Có phương án dự phòng", [
             "Mới 1 seed → nói rõ giới hạn.",
             "Hạ tầng lỗi → giữ Spark trên máy.",
             "Thiếu thời gian → bỏ RQ5.",
         ], body_size=18, title_size=20, name="decor_risk")
add_table(s, [
    ["Mốc", "Việc làm", "Kết quả"],
    ["11/2026", "Xong 5 mô hình, 3 cách chia", "Bảng NDCG"],
    ["01/2027", "Xong Wilcoxon + Friedman", "20 cặp kiểm định"],
    ["02/2027", "Viết báo cáo nháp", "Bản nháp"],
    ["03/2027", "Phản biện nội bộ", "Bản sửa"],
    ["06/2027", "Bảo vệ", "Slide + demo"],
], 6.85, 1.42, 5.95, 4.22,
    col_widths=[1.2, 3.0, 1.8], header_size=14, body_size=14,
    name="decor_plan_table")
add_banner(s, 0.55, 5.92, 12.25, 0.58,
           "Máy: laptop i7-13620H · 32 GB · RTX 4050 6 GB · không dùng cloud. "
           "Mã: " + REPO_URL,
           fill=PAPER, size=13, color=GREY, name="decor_repo_banner")
notes(s, "ROI ở đây là tránh kết luận sai, không phải tối ưu điểm số. "
         "Kế hoạch 5 mốc đến 06/2027. RQ5 sang tập khác để mở rộng, không "
         "cam kết trong đề cương.")

# ---- S19 ----
s = add_slide("Tự đánh giá và giới hạn", "Nói thẳng điều đã làm và chưa làm")
status = [
    ("Dữ liệu", "Hợp lệ", ["Ẩn danh, có nguồn.", "Kiểm tra sha256."], ACCENT, BLUE_PALE),
    ("Kỹ thuật", "Chạy thật", ["PySpark + MapReduce.", "MongoDB + R + Streamlit."], TEAL, TEAL_PALE),
    ("Máy & thời gian", "Rõ ràng", ["RTX 4050 6 GB.", "G1–G5 đến 06/2027."], ORANGE, ORANGE_PALE),
    ("Hướng thêm", "Còn việc", ["Thêm seed, thêm tập.", "Độ bộ nhớ, chỉnh SASRec."], NAVY, PAPER),
]
for i, (title, kicker, lines, accent, pale) in enumerate(status):
    add_card(s, 0.55 + i * 3.10, 1.42, 2.90, 2.30, accent, pale,
             kicker, title, lines, body_size=18, title_size=20,
             name="decor_status_%d" % i)
add_banner(s, 0.55, 3.96, 12.15, 1.72,
           "Giới hạn nói thẳng: local[4] không phải cụm; container MapReduce "
           "đã gỡ; mới 1 seed; không báo Mean±Std.\n"
           "Không so thời gian CPU với GPU; không đo bộ nhớ; không chạy "
           "Nemenyi; chưa đo 'bất ngờ' vì thiếu mô hình mốc.\n"
           "Không nhận tái lập SOTA đầy đủ. Muốn chắc hơn thì thêm seed, thêm "
           "tập dữ liệu, đo thêm bộ nhớ.",
           fill=ORANGE_PALE, size=15, color=DARK, name="decor_limit_banner")
add_banner(s, 0.55, 5.90, 12.15, 0.58,
           "Bốn nhóm an toàn: dữ liệu · thiết kế · đo lường · thống kê — "
           "mới đáp ứng một phần, cách giảm rủi ro ghi ngay dòng trên.",
           fill=PAPER, size=14, color=GREY, name="decor_validity_banner")
notes(s, "Đưa giới hạn trước khi hội đồng hỏi. Không overclaim về ổn định, "
         "bộ nhớ hay SOTA replication.")

# ---- S20 ----
s = add_slide("Hỏi và đáp", "13 bài: 10 bài đánh giá + 3 bài gốc mô hình")
refs = [
    ("[A1]", "Ji, TOIS 41(3), 2023 · 10.1145/3569930"),
    ("[A2]", "Daniil, TORS 2(1), 2024 · 10.1145/3637066"),
    ("[A3]", "Gusak, RecSys '25 · 10.1145/3705328.3748164"),
    ("[A4]", "Parajuli, RecSys '26 · 10.1145/3773078.3831818"),
    ("[A5]", "Chen, TOIS 41(3), 2023 · 10.1145/3564284"),
    ("[A6]", "Klimashevskaia, UMAI 34(5), 2024 · 10.1007/s11257-024-09406-0"),
    ("[A7]", "Meehan & Pauwels, RecSys '25 · 10.1145/3705328.3748035"),
    ("[A8]", "Shi, TOIS 42(2), 2024 · 10.1145/3618107"),
    ("[A9]", "Tamm, RecSys '21 · 10.1145/3460231.3478848"),
    ("[A10]", "Meng, RecSys '20 · 10.1145/3383313.3418479"),
    ("[B1]", "Sarwar, WWW 2001 · 10.1145/371920.372071"),
    ("[B2]", "Hu et al., ICDM 2008 · 10.1109/ICDM.2008.22"),
    ("[B3]", "Kang & McAuley, ICDM 2018 · 10.1109/ICDM.2018.00035"),
]
add_table(s, [["#", "Tài liệu"]] + [list(x) for x in refs],
          0.45, 1.40, 8.85, 5.18, col_widths=[0.9, 7.95],
          header_size=13, body_size=12, name="decor_refs_table")
add_card(s, 9.50, 1.40, 3.35, 3.62, ACCENT, BLUE_PALE,
         "Câu hỏi dự phòng", "Trả lời ngắn", [
             "Giữ cuối vẫn rò rỉ 99,9988% nếu tính gộp.",
             "ALS chạy đủ 162.541 người.",
             "Mới 1 seed → chưa nói ổn định.",
             "SASRec là đối chuẩn, không phải mô hình thắng.",
         ], body_size=18, title_size=20, name="decor_qa_card")
add_banner(s, 9.50, 5.20, 3.35, 1.14,
           "Nguồn dữ liệu: Harper & Konstan, TIST 5(4), 2015 · "
           "DOI 10.1145/2827872.\nMã: " + REPO_URL,
           fill=PAPER, size=12, color=GREY, name="decor_qa_footer")
notes(s, "Nhóm B chỉ trích, chưa tải PDF; manifest ghi "
         "referenced-not-downloaded. Mọi DOI đã verify Crossref 2026-11-24. "
         "Không dùng arXiv cho cơ sở trích dẫn.")

# =====================================================
# 4 SLIDE PHU LUC
# =====================================================

def appendix_slide(title, tag):
    return add_slide(title, "Phụ lục " + tag, footer_label=tag + " / 4")


# ---- A1 ----
s = appendix_slide("Bảng kết quả đầy đủ", "A1")
add_table(s, [
    ["Mô hình", "NDCG t", "NDCG g", "NDCG c", "MRR t", "MRR g", "MRR c",
     "Đa dạng t", "Đa dạng g", "Đa dạng c"],
    ["ItemKNN", "0,2679", "0,1409", "0,0461", "0,4604", "0,2644", "0,0330", "0,7878", "0,7921", "0,7891"],
    ["ALS", "0,2581", "0,1332", "0,0469", "0,4342", "0,2491", "0,0328", "0,7440", "0,7351", "0,7472"],
    ["SASRec + CE", "0,0163", "0,0187", "0,0067", "0,0380", "0,0449", "0,0043", "0,8234", "0,8149", "0,8240"],
    ["MostPopular", "0,0852", "0,0455", "0,0183", "0,1751", "0,0964", "0,0123", "0,7648", "0,7883", "0,7648"],
    ["Random", "0,0003", "0,0009", "0,0001", "0,0009", "0,0023", "0,0001", "0,8410", "0,8296", "0,8400"],
    ["ItemKNN − ALS", "+0,0098", "+0,0077", "−0,0008", "+0,0262", "+0,0153", "+0,0002", "+0,0438", "+0,0570", "+0,0419"],
], 0.35, 1.42, 12.62, 3.42,
    col_widths=[1.7, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.3, 1.3, 1.3],
    header_size=12, body_size=12, name="decor_a1_table")
add_banner(s, 0.35, 5.10, 12.62, 0.92,
           "t = trộn ngẫu nhiên · g = theo mốc thời gian · c = giữ lượt cuối. "
           "Đa dạng@10 = trung bình 1 − Jaccard(bộ thể loại) trên 5.000 "
           "người.\nRandom có độ đa dạng cao nhất mà NDCG ≈ 0 → đa dạng "
           "không đồng nghĩa tốt. Bất ngờ (serendipity) chưa đo.",
           fill=PAPER, size=13, color=DARK, name="decor_a1_footer")
notes(s, "Nguồn runs/20261120_012944.../comparison.json và năm summary "
         "tương ứng. Mỗi split tính trên tập người đủ điều kiện riêng; không "
         "so chéo giữa các split như phép thử ghép cặp.")

# ---- A2 ----
s = appendix_slide("20 cặp kiểm định", "A2")
pairs = [
    ["Cặp", "n", "p", "Khoảng 95%", "r"],
    ["random: ALS – Pop", "158.626", "< 1e-300", "0,1718 … 0,1740", "0,696"],
    ["random: ALS – Random", "158.626", "< 1e-300", "0,2567 … 0,2589", "0,999"],
    ["random: KNN – Pop", "158.692*", "< 1e-300", "0,1816 … 0,1838", "0,736"],
    ["random: ALS – KNN", "158.626", "2,84e-60", "−0,0109 … −0,0089", "−0,030"],
    ["random: SASRec – Pop", "158.472", "< 1e-300", "−0,0696 … −0,0683", "−0,739"],
    ["random: SASRec – ALS", "158.472", "< 1e-300", "−0,2431 … −0,2409", "−0,938"],
    ["random: SASRec – Random", "158.472", "< 1e-300", "0,0157 … 0,0162", "0,955"],
    ["random: SASRec – KNN", "158.472", "< 1e-300", "−0,2531 … −0,2507", "−0,942"],
    ["temporal: ALS – Pop", "6.214", "1,12e-297", "0,0833 … 0,0924", "0,646"],
    ["temporal: ALS – Random", "6.214", "< 1e-300", "0,1274 … 0,1371", "0,986"],
    ["temporal: KNN – Pop", "6219*", "< 1e-300", "0,0909 … 0,0999", "0,702"],
    ["temporal: ALS – KNN", "6.214", "0,00301", "−0,0118 … −0,0036", "−0,016"],
    ["LOO: ALS – Pop", "95.977", "< 1e-300", "0,0276 … 0,0297", "0,531"],
    ["LOO: ALS – Random", "95.977", "< 1e-300", "0,0458 … 0,0479", "0,996"],
    ["LOO: KNN – Pop", "96003*", "< 1e-300", "0,0268 … 0,0289", "0,517"],
    ["LOO: ALS – KNN", "95.977", "0,153", "−0,0003 … 0,0018", "0,005"],
    ["LOO: SASRec – Pop", "95.938", "2,47e-202", "−0,0123 … −0,0108", "−0,450"],
    ["LOO: SASRec – ALS", "95.938", "< 1e-300", "−0,0413 … −0,0391", "−0,767"],
    ["LOO: SASRec – Random", "95.938", "2,25e-225", "0,0062 … 0,0070", "0,972"],
    ["LOO: SASRec – KNN", "95.938", "< 1e-300", "−0,0405 … −0,0383", "−0,766"],
]
add_table(s, pairs, 0.35, 1.36, 12.62, 5.28,
          col_widths=[3.3, 1.5, 1.8, 3.8, 1.2],
          header_size=12, body_size=10.5, name="decor_a2_table")
add_caption(s, "Wilcoxon signed-rank hai phía + CI 95% + rank-biserial r. "
               "n có dấu * là số người của ItemKNN/MostPopular (viết không dấu chấm "
               "ngàn); các dòng khác là của ALS. ALS – KNN ở LOO: p = 0,153, CI chứa 0.",
            0.35, 6.66, 12.62, size=11)
notes(s, "Nguồn runs/20261118_151202_12_paired_stats_9b864f59/outputs/"
         "paired_stats.json. Friedman riêng: chi2 = 7017,283 / 4205,956 / "
         "773,127; Nemenyi chưa chạy.")

# ---- A3 ----
s = appendix_slide("Tham số và cấu hình máy", "A3")
add_table(s, [
    ["Mô hình", "Tham số chính", "Phạm vi fit", "Thời gian (t/g/c)"],
    ["Random", "seed 42; chọn đều từ catalog", "FULL 162.541 người", "48,1 / 17,1 / 34,2 s"],
    ["MostPopular", "xếp theo số lượt chấm", "FULL 162.541 người", "10,5 / 2,5 / 3,8 s"],
    ["ItemKNN", "100 hàng xóm; cosine", "FULL 162.541 người", "203,1 / 88,0 / 172,3 s"],
    ["ALS", "rank 16; maxIter 8; alpha 10; reg 0,05", "FULL 162.541 người", "103,7 / 65,9 / 91,6 s"],
    ["SASRec + CE", "maxlen 50; 1 block; 1 head; lr 0,001", "FULL 162.541 người", "558,2 / 332,1 / 564,1 s GPU"],
], 0.40, 1.42, 12.52, 2.82,
    col_widths=[1.9, 5.2, 2.4, 3.0], header_size=13, body_size=12.5,
    name="decor_a3_table")
add_table(s, [
    ["Hạng mục", "Giá trị"],
    ["Spark", "4.2.0 · local[4] · driver 6g · CPU"],
    ["SASRec CUDA", "torch 2.14.1+cu126 · CUDA 12.6 · RTX 4050 Laptop 6.140 MiB"],
    ["Ngưỡng liên quan", "rating ≥ 4,0"],
    ["Ngưỡng min_train", "5 lượt"],
    ["Seed", "42 · một seed duy nhất"],
    ["Tuning budget", "SASRec 0; baseline giữ cấu hình cố định"],
], 0.40, 4.48, 12.52, 2.14,
    col_widths=[3.0, 9.5], header_size=13, body_size=12.5,
    name="decor_a3_env")
notes(s, "t/g/c = trộn ngẫu nhiên / theo mốc thời gian / giữ lượt cuối. "
         "Không cộng dồn thời gian giữa CPU và GPU thành một bảng xếp hạng "
         "chung. Thời gian lấy từ tổng seconds trong từng summary.")

# ---- A4 ----
s = appendix_slide("13 tài liệu đầy đủ", "A4")
refs_full = [
    ["Nhóm", "Tên ngắn", "Nguồn", "DOI"],
    ["A1", "Ji — Data Leakage", "ACM TOIS 41(3), 2023", "10.1145/3569930"],
    ["A2", "Daniil — Popularity Bias", "ACM TORS 2(1), 2024", "10.1145/3637066"],
    ["A3", "Gusak — Time to Split", "ACM RecSys '25", "10.1145/3705328.3748164"],
    ["A4", "Parajuli — Convergent Validity", "ACM RecSys '26", "10.1145/3773078.3831818"],
    ["A5", "Chen — Bias and Debias", "ACM TOIS 41(3), 2023", "10.1145/3564284"],
    ["A6", "Klimashevskaia — Survey", "Springer UMAI 34(5), 2024", "10.1007/s11257-024-09406-0"],
    ["A7", "Meehan — Cold-Start Bias", "ACM RecSys '25", "10.1145/3705328.3748035"],
    ["A8", "Shi — Relieving Popularity Bias", "ACM TOIS 42(2), 2024", "10.1145/3618107"],
    ["A9", "Tamm — Quality Metrics", "ACM RecSys '21", "10.1145/3460231.3478848"],
    ["A10", "Meng — Data Splitting", "ACM RecSys '20", "10.1145/3383313.3418479"],
    ["B1", "Sarwar — Item-based CF", "ACM WWW 2001", "10.1145/371920.372071"],
    ["B2", "Hu — Implicit Feedback", "IEEE ICDM 2008", "10.1109/ICDM.2008.22"],
    ["B3", "Kang — SASRec", "IEEE ICDM 2018", "10.1109/ICDM.2018.00035"],
]
add_table(s, refs_full, 0.40, 1.40, 12.52, 5.12,
          col_widths=[1.0, 4.4, 3.4, 3.7],
          header_size=13, body_size=12.5, name="decor_a4_table")
add_caption(s, "Nhóm A = đánh giá/chia tập. Nhóm B = bài gốc mô hình. "
               "B1–B3 verify Crossref 2026-11-24; PDF chưa tải, trạng thái "
               "referenced-not-downloaded.",
            0.40, 6.62, 12.52, size=11)
notes(s, "Mọi DOI đều kiểm tra qua api.crossref.org trước khi ghi. Không "
         "dùng bản arXiv làm trích dẫn chính.")


def verify_layout():
    problems = []

    for si, slide in enumerate(prs.slides, 1):
        for sh in slide.shapes:
            if getattr(sh, "left", None) is None:
                continue
            if (sh.left < 0 or sh.top < 0 or
                    sh.left + sh.width > SW or sh.top + sh.height > SH):
                problems.append(
                    "slide %d: shape outside %s" % (si, sh.name))

            if not sh.has_text_frame:
                continue
            txt = sh.text_frame.text
            for bad in BAD_LITERALS:
                if bad in txt:
                    problems.append(
                        "slide %d: legacy literal %r" % (si, bad))
            if sh.has_table:
                for row in sh.table.rows:
                    for cell in row.cells:
                        for bad in BAD_LITERALS:
                            if bad in cell.text:
                                problems.append(
                                    "slide %d: legacy literal %r in table"
                                    % (si, bad))

            if si <= N_SLIDES and sh.name.endswith("_body"):
                for p in sh.text_frame.paragraphs:
                    for r in p.runs:
                        if r.font.size and r.font.size < Pt(18):
                            problems.append(
                                "slide %d: font %spt in %s"
                                % (si, r.font.size.pt, sh.name))
                            break
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-verify", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(REPORT):
        raise SystemExit("Chưa có audit_report.json. Chạy "
                         "scripts/19_audit_report.py trước.")
    if len(prs.slides._sldIdLst) != N_SLIDES + 4:
        raise SystemExit("Sai số slide: %d" % len(prs.slides._sldIdLst))

    if not args.no_verify:
        problems = verify_layout()
        if problems:
            raise SystemExit("LAYOUT FAIL:\n" + "\n".join(problems))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    prs.save(OUT)
    print("OK", OUT, os.path.getsize(OUT), "bytes,",
          len(prs.slides._sldIdLst), "slides (20 main + 4 appendix), checked")


if __name__ == "__main__":
    main()
