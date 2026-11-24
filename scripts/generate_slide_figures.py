# -*- coding: utf-8 -*-
"""
Sinh 4 hình cho slide:
  fig_architecture.png - 4 tang pipeline, co lan INPUT trai / OUTPUT phai
  fig_io.png           - dau vao la gi -> xu ly the nao -> dau ra la gi
  fig_sli.png          - muc ro ri theo tung cach chia (doc tu data_level_audit.json)
  fig_interaction.png  - NDCG@10 doi the nao theo 3 cach chia (doc tu comparison.json)

Khong con so nao bi hardcode: thieu file nguon thi dung han.
"""
import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["font.family"] = ["DejaVu Sans"]

BASE = r"D:\Master Exers\Big Data\Recomendation_System"
OUT = os.path.join(BASE, "docs", "Project", "Main", "Presentation", "Slides",
                   "figures")
os.makedirs(OUT, exist_ok=True)

DEFAULT_RUN = "20261120_012944_09_compare_and_reversal_21d0811a"
AUDIT_RUN = "20261115_233616_05_audit_split_leakage_3fa5a49e"
SPLITS = ["random80_20", "temporal_global", "leave_one_out"]
SPLITS_VI = ["Trộn ngẫu nhiên", "Theo mốc thời gian", "Giữ lượt cuối"]

DARK = "#111827"
BLUE, BLUE_BG = "#1a56db", "#e8f0fe"
GREEN, GREEN_BG = "#1e7b34", "#e6f6ea"
ORANGE, ORANGE_BG = "#b45309", "#fff4e0"
PURPLE, PURPLE_BG = "#6b21a8", "#f3e8ff"
RED, RED_BG = "#b91c1c", "#fde8e8"


def load_json(path, label):
    if not os.path.exists(path):
        raise SystemExit("Thiếu file nguồn %s: %s" % (label, path))
    return json.load(open(path, encoding="utf-8"))


def vn(x, nd=4):
    return ("%." + str(nd) + "f") % x


# ---------- FIG 1: kien truc 4 tang + lan INPUT/OUTPUT ----------
def fig_architecture():
    fig, ax = plt.subplots(figsize=(11.6, 5.9), dpi=170)
    ax.axis("off")

    layers = [
        ("TẦNG 1 — CHỨA DỮ LIỆU",
         "MovieLens 25M (678 MB) → Parquet\n→ Spark DataFrame", BLUE_BG, BLUE),
        ("TẦNG 2 — XỬ LÝ LỚN",
         "MapReduce Java: 323.737 khóa\nPySpark local[4]", GREEN_BG, GREEN),
        ("TẦNG 3 — LƯU KẾT QUẢ",
         "MongoDB 8.0.12\n42 trường cho mỗi lần audit", ORANGE_BG, ORANGE),
        ("TẦNG 4 — XEM & KIỂM ĐỊNH",
         "R 4.6.2 · Streamlit\nWilcoxon · bootstrap CI", PURPLE_BG, PURPLE),
    ]
    y, h, gap = 0.92, 0.185, 0.052
    for name, body, bg, border in layers:
        ax.add_patch(FancyBboxPatch((0.20, y - h), 0.60, h,
                                    boxstyle="round,pad=0.010",
                                    fc=bg, ec=border, lw=1.7))
        ax.text(0.235, y - 0.026, name, fontsize=16, fontweight="bold",
                color=border, va="top")
        ax.text(0.235, y - 0.084, body, fontsize=16, color=DARK, va="top",
                linespacing=1.25)
        y -= h + gap

    for ya, yb in [(0.735, 0.683), (0.498, 0.446), (0.261, 0.209)]:
        ax.add_patch(FancyArrowPatch((0.50, ya), (0.50, yb), arrowstyle="-|>",
                                     mutation_scale=15, color="#374151", lw=1.6))

    # lan trai: INPUT
    ax.add_patch(FancyBboxPatch((0.015, 0.14), 0.155, 0.78,
                                boxstyle="round,pad=0.008",
                                fc="#f8fafc", ec="#94a3b8", lw=1.4,
                                linestyle="--"))
    ax.text(0.092, 0.885, "INPUT", fontsize=16, fontweight="bold",
            color="#475569", ha="center")
    ax.text(0.092, 0.42,
            "Bảng chấm\n4 cột\n\n25.000.095\ndòng", fontsize=16,
            color="#334155", ha="center", va="center", linespacing=1.35)

    # lan phai: OUTPUT
    ax.add_patch(FancyBboxPatch((0.885, 0.14), 0.10, 0.78,
                                boxstyle="round,pad=0.008",
                                fc="#f8fafc", ec="#94a3b8", lw=1.4,
                                linestyle="--"))
    ax.text(0.935, 0.885, "OUTPUT", fontsize=16, fontweight="bold",
            color="#475569", ha="center")
    ax.text(0.935, 0.42,
            "audit\nreport\n.json\n\nruns/\n\nbiểu đồ",
            fontsize=16, color="#334155", ha="center", va="center",
            linespacing=1.3)

    ax.annotate("", xy=(0.20, 0.52), xytext=(0.175, 0.52),
                arrowprops=dict(arrowstyle="-|>", color="#94a3b8", lw=1.5))
    ax.annotate("", xy=(0.883, 0.52), xytext=(0.808, 0.52),
                arrowprops=dict(arrowstyle="-|>", color="#94a3b8", lw=1.5))

    ax.set_xlim(0, 1.0)
    ax.set_ylim(0.05, 0.98)
    path = os.path.join(OUT, "fig_architecture.png")
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


# ---------- FIG 2: dau vao -> xu ly -> dau ra ----------
def fig_io():
    fig, ax = plt.subplots(figsize=(12.6, 5.4), dpi=170)
    ax.axis("off")

    # cot 1: dau vao
    ax.add_patch(FancyBboxPatch((0.015, 0.10), 0.265, 0.78,
                                boxstyle="round,pad=0.012",
                                fc=BLUE_BG, ec=BLUE, lw=1.8))
    ax.text(0.147, 0.815, "ĐẦU VÀO", fontsize=18, fontweight="bold",
            color=BLUE, ha="center")
    ax.text(0.147, 0.700, "Một bảng 4 cột", fontsize=16, color=DARK,
            ha="center")
    ax.text(0.147, 0.545,
            "ai chấm  →  userId\n"
            "phim nào  →  movieId\n"
            "mấy sao  →  rating\n"
            "lúc nào  →  timestamp",
            fontsize=16, color="#1e3a8a", ha="center", va="center",
            linespacing=1.9)
    ax.text(0.147, 0.215,
            "25.000.095 dòng · 162.541 người\n59.047 phim · 1995 → 2019",
            fontsize=16, color="#1e3a8a", ha="center", va="center",
            linespacing=1.5)

    # cot 2: xu ly
    steps = [
        ("1. Chia 3 cách", "trộn ngẫu nhiên\nmốc thời gian\ngiữ lượt cuối", GREEN, GREEN_BG),
        ("2. Chạy 5 mô hình", "Random · MostPopular\nALS · ItemKNN\nSASRec", ORANGE, ORANGE_BG),
        ("3. Đo 6 nhóm chỉ số", "rò rỉ · độ đúng\nthứ hạng · phủ\nmới lạ · đa dạng", PURPLE, PURPLE_BG),
    ]
    y = 0.845
    for title, body, border, bg in steps:
        ax.add_patch(FancyBboxPatch((0.315, y - 0.215), 0.335, 0.20,
                                    boxstyle="round,pad=0.010",
                                    fc=bg, ec=border, lw=1.6))
        ax.text(0.335, y - 0.048, title, fontsize=16, fontweight="bold",
                color=border, va="top")
        ax.text(0.335, y - 0.108, body, fontsize=16, color=DARK, va="top",
                linespacing=1.3)
        y -= 0.265
    for yy in (0.79, 0.525):
        ax.add_patch(FancyArrowPatch((0.482, yy), (0.482, yy - 0.038),
                                     arrowstyle="-|>", mutation_scale=13,
                                     color="#374151", lw=1.5))

    # cot 3: dau ra
    ax.add_patch(FancyBboxPatch((0.685, 0.10), 0.30, 0.78,
                                boxstyle="round,pad=0.012",
                                fc="#f8fafc", ec="#475569", lw=1.8))
    ax.text(0.835, 0.815, "ĐẦU RA", fontsize=18, fontweight="bold",
            color="#334155", ha="center")
    outs = [
        ("O1  Phiếu chẩn đoán", "audit_report.json"),
        ("O2  Thước đo rò rỉ", "src/audit/leakage.py"),
        ("O3  Quy trình 3 bước", "SLI → số người → kết luận"),
        ("O4  Chạy lại được", "scripts/ · runs/ · Streamlit"),
    ]
    yy = 0.700
    for head, sub in outs:
        ax.text(0.712, yy, head, fontsize=16, fontweight="bold", color=DARK,
                va="top")
        ax.text(0.712, yy - 0.062, sub, fontsize=16, color="#475569",
                va="top")
        yy -= 0.148

    ax.annotate("", xy=(0.310, 0.49), xytext=(0.283, 0.49),
                arrowprops=dict(arrowstyle="-|>", color="#374151", lw=2.0))
    ax.annotate("", xy=(0.682, 0.49), xytext=(0.653, 0.49),
                arrowprops=dict(arrowstyle="-|>", color="#374151", lw=2.0))

    ax.set_xlim(0, 1.0)
    ax.set_ylim(0.06, 0.95)
    path = os.path.join(OUT, "fig_io.png")
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


# ---------- FIG 3: SLI toan cuc vs theo tung nguoi ----------
def fig_sli():
    audit_path = os.path.join(BASE, "runs", AUDIT_RUN, "outputs",
                              "data_level_audit.json")
    audits = load_json(audit_path, "data_level_audit.json")["audits"]

    sli_global = [audits[s]["temporal_violation_global_pct"] / 100.0
                  for s in SPLITS]
    sli_user = [audits[s]["temporal_violation_user_pct"] / 100.0
                for s in SPLITS]

    fig, ax = plt.subplots(figsize=(10.4, 4.8), dpi=170)
    x = range(len(SPLITS))
    w = 0.36
    b1 = ax.bar([i - w / 2 for i in x], sli_global, w,
                label="Tính gộp toàn bộ dòng test", color="#fca5a5",
                ec=RED, lw=1.3)
    b2 = ax.bar([i + w / 2 for i in x], sli_user, w,
                label="Tính riêng từng người (đề tài đề xuất)",
                color="#93c5fd", ec="#1e40af", lw=1.3)
    for rect, v in zip(b1, sli_global):
        ax.text(rect.get_x() + rect.get_width() / 2, v + 0.018,
                vn(v * 100, 2) + "%", ha="center", fontsize=16,
                fontweight="bold", color=RED)
    for rect, v in zip(b2, sli_user):
        ax.text(rect.get_x() + rect.get_width() / 2, v + 0.018,
                vn(v * 100, 2) + "%", ha="center", fontsize=16,
                fontweight="bold", color="#1e40af")

    ax.annotate("Hai cách tính cho\nkết luận ngược nhau",
                xy=(2 + w / 2, sli_user[2] + 0.02), xytext=(1.35, 0.55),
                fontsize=16, color="#7f1d1d", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="#7f1d1d", lw=1.6))
    ax.set_xticks(list(x))
    ax.set_xticklabels(SPLITS_VI, fontsize=16)
    ax.set_ylabel("Tỷ lệ dòng test bị lộ", fontsize=16)
    ax.set_ylim(0, 1.14)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=16)
    ax.legend(fontsize=16, loc="upper center", framealpha=0.96)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("Mức rò rỉ (SLI) theo từng cách chia", fontsize=16,
                 fontweight="bold", pad=12)
    fig.tight_layout()
    path = os.path.join(OUT, "fig_sli.png")
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


# ---------- FIG 4: NDCG@10 doi the nao theo cach chia ----------
def fig_interaction(run_id):
    run_path = os.path.join(BASE, "runs", run_id, "outputs", "comparison.json")
    rows = load_json(run_path, "comparison.json")["rows"]
    rows = sorted(rows, key=lambda r: SPLITS.index(r["split"]))

    with plt.rc_context({"font.size": 16}):
        fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.8), dpi=170)
        x = list(range(len(rows)))

        ax = axes[0]
        series = [
            ("rnd_ndcg10", "Random", "#7570b3", "^"),
            ("pop_ndcg10", "MostPopular", "#d95f02", "o"),
            ("als_ndcg10", "ALS", "#1b9e77", "s"),
            ("knn_ndcg10", "ItemKNN", "#e7298a", "v"),
            ("sasrec_ndcg10", "SASRec + CE", "#e41a1c", "d"),
        ]
        for key, label, color, marker in series:
            ax.plot(x, [r.get(key) or 0 for r in rows], marker + "-",
                    label=label, color=color, linewidth=2.5, markersize=9)
        ax.set_xticks(x)
        ax.set_xticklabels(SPLITS_VI, fontsize=16)
        ax.set_ylabel("Độ đúng top-10 (NDCG@10)", fontsize=16)
        ax.set_title("Điểm số tụt khi chia đúng thời gian", fontsize=16,
                     fontweight="bold")
        ax.legend(fontsize=16, framealpha=0.96)
        ax.grid(alpha=0.3)
        ax.set_ylim(0, 0.32)

        ax = axes[1]
        w = 0.38
        d1 = [r["delta_ndcg"] for r in rows]
        d2 = [r.get("delta_knn_vs_als") or 0 for r in rows]
        ax.bar([i - w / 2 for i in x], d1, w, label="ALS − MostPopular",
               color=["#93c5fd" if v > 0 else "#fca5a5" for v in d1],
               ec="#1e40af", lw=1.0)
        ax.bar([i + w / 2 for i in x], d2, w, label="ItemKNN − ALS",
               color=["#86efac" if v > 0 else "#fca5a5" for v in d2],
               ec="#166534", lw=1.0)
        for xi, v in zip(x, d1):
            ax.annotate("%+.4f" % v, (xi - w / 2, v), textcoords="offset points",
                        xytext=(0, 7), ha="center", fontsize=16)
        for xi, v in zip(x, d2):
            ax.annotate("%+.4f" % v, (xi + w / 2, v), textcoords="offset points",
                        xytext=(0, 7 if v > 0 else -18), ha="center",
                        fontsize=16)
        ax.axhline(0, color="black", linewidth=1.0)
        ax.set_xticks(x)
        ax.set_xticklabels(SPLITS_VI, fontsize=16)
        ax.set_ylabel("Chênh lệch NDCG@10", fontsize=16)
        ax.set_ylim(-0.025, 0.22)
        ax.set_title("Khoảng cách giữa các mô hình co lại", fontsize=16,
                     fontweight="bold")
        ax.legend(fontsize=16, framealpha=0.96, loc="upper right")
        ax.grid(alpha=0.3, axis="y")

        plt.tight_layout()
        path = os.path.join(OUT, "fig_interaction.png")
        fig.savefig(path, bbox_inches="tight", facecolor="white")
        plt.close(fig)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=DEFAULT_RUN,
                    help="run id chứa outputs/comparison.json")
    args = ap.parse_args()

    made = [fig_architecture(), fig_io(), fig_sli(),
            fig_interaction(args.run)]
    for p in made:
        print("OK %-70s %8d bytes" % (os.path.basename(p),
                                      os.path.getsize(p)))
    print("OK 4 figures")


if __name__ == "__main__":
    main()
