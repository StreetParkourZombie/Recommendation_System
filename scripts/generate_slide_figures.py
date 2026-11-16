# -*- coding: utf-8 -*-
"""Sinh 2 hình cho slide: kiến trúc pipeline (slide 10) và SLI (slide 12)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["font.family"] = ["DejaVu Sans"]
OUT = r"docs\Project\Main\Presentation\Slides\figures"

import os
os.makedirs(OUT, exist_ok=True)

# ---------- FIG 1: kiến trúc 4 tầng ----------
fig, ax = plt.subplots(figsize=(11, 5.6), dpi=160)
ax.axis("off")
layers = [
    ("TẦNG 1 — LƯU TRỮ", "MovieLens 25M (678 MB) → Parquet (pyarrow 26s)\n→ HDFS 3.2.1 · 5 container", "#e8f0fe", "#1a56db"),
    ("TẦNG 2 — XỬ LÝ LỚN", "MapReduce Java: 323.737 key · G3 PASS 100%\nPySpark local[4]: 3 split → 735 MB · audit · MostPopular · ALS implicit", "#e6f6ea", "#1e7b34"),
    ("TẦNG 3 — LƯU TRỮ METRIC", "MongoDB 8.0.12 · recsys.audit_metrics (42 field) · item_profile (62.423 docs)", "#fff4e0", "#b45309"),
    ("TẦNG 4 — TRỰC QUAN", "R 4.6.2 (7 figures) · Streamlit dashboard · Wilcoxon / bootstrap CI", "#f3e8ff", "#6b21a8"),
]
y = 0.95
h = 0.19
for name, body, bg, border in layers:
    box = FancyBboxPatch((0.03, y - h), 0.94, h, boxstyle="round,pad=0.012",
                         fc=bg, ec=border, lw=1.6)
    ax.add_patch(box)
    ax.text(0.06, y - 0.045, name, fontsize=12.5, fontweight="bold", color=border, va="top")
    ax.text(0.06, y - 0.085, body, fontsize=10.5, color="#111827", va="top", wrap=True)
    y -= h + 0.045
for ya, yb in [(0.76, 0.715), (0.525, 0.48), (0.29, 0.245)]:
    ax.add_patch(FancyArrowPatch((0.5, ya), (0.5, yb), arrowstyle="-|>",
                                 mutation_scale=16, color="#374151", lw=1.4))
ax.set_xlim(0, 1); ax.set_ylim(0.02, 1.0)
fig.savefig(f"{OUT}\\fig_architecture.png", bbox_inches="tight", facecolor="white")
plt.close(fig)

# ---------- FIG 2: SLI toàn cục vs tương đối ----------
fig, ax = plt.subplots(figsize=(9.6, 4.6), dpi=160)
splits = ["random80_20", "temporal_global", "leave_one_out"]
sli_global = [1.0000, 0.0000, 0.999988]
sli_user = [0.989084, 0.0000, 0.0000]
x = range(3)
w = 0.36
b1 = ax.bar([i - w / 2 for i in x], sli_global, w, label="SLI toàn cục (cách phổ biến)",
            color="#fca5a5", ec="#b91c1c", lw=1.2)
b2 = ax.bar([i + w / 2 for i in x], sli_user, w, label="SLI tương đối theo user (đề xuất)",
            color="#93c5fd", ec="#1e40af", lw=1.2)
for rect, v in zip(b1, sli_global):
    ax.text(rect.get_x() + rect.get_width() / 2, v + 0.015, f"{v*100:.4f}%".replace(".", ","),
            ha="center", fontsize=10.5, fontweight="bold", color="#b91c1c")
for rect, v in zip(b2, sli_user):
    ax.text(rect.get_x() + rect.get_width() / 2, v + 0.015, f"{v*100:.4f}%".replace(".", ","),
            ha="center", fontsize=10.5, fontweight="bold", color="#1e40af")
ax.annotate("Kết luận NGƯỢC hoàn toàn:\ntoàn cục 99,9988% ≠ tương đối 0%",
            xy=(2, 0.999988), xytext=(1.52, 0.72),
            fontsize=11.5, color="#7f1d1d", fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="#7f1d1d", lw=1.4))
ax.set_xticks(list(x)); ax.set_xticklabels(splits, fontsize=12)
ax.set_ylabel("Tỷ lệ rò rỉ", fontsize=12)
ax.set_ylim(0, 1.09)
ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=10.5)
ax.legend(fontsize=11, loc="upper center", framealpha=0.95)
ax.spines[["top", "right"]].set_visible(False)
ax.set_title("Split Leakage Index — hai cách đo, hai kết luận (MovieLens 25M, đo thật)",
             fontsize=13, fontweight="bold", pad=12)
fig.tight_layout()
fig.savefig(f"{OUT}\\fig_sli.png", bbox_inches="tight", facecolor="white")
plt.close(fig)
print("OK 2 figures")

