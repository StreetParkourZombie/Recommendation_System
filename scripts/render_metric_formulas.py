# -*- coding: utf-8 -*-
"""Render metric LaTeX formulas as PNG, embed into slide 11."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(r"D:\Master Exers\Big Data\Recomendation_System")
OUT_DIR = ROOT / r"docs\Project\Main\Presentation\Slides\figures"
OUT_DIR.mkdir(exist_ok=True)

# Define formulas: (filename, latex_string, figsize)
formulas = [
    ("metric_sli.png", 
     r"$\text{SLI} = \frac{1}{|U_{\text{test}}|} \sum_u \frac{\left|\{r \in D_{\text{test}}(u): t_r < t_{\max}(u)\}\right|}{|D_{\text{test}}(u)|}$",
     (6, 1.2)),
    
    ("metric_ndcg.png",
     r"$\text{NDCG@10} = \text{mean}_u\left(\frac{\sum_{k=1}^{10} \frac{\text{rel}(u,k)}{\log_2(k+1)}}{\sum_{k=1}^{\min(|{\text{rel}(u)|,10})} \frac{1}{\log_2(k+1)}}\right)$",
     (7, 1.2)),
    
    ("metric_coverage.png",
     r"$\text{Coverage} = \frac{|I_{\text{rec}}|}{|I_{\text{train}}|}, \quad \text{LongTailCov} = \frac{|I_{\text{rec}} \cap L|}{|L|}$",
     (6.5, 1.2)),
    
    ("metric_novelty_div.png",
     r"$\text{Novelty@10} = \frac{1}{K}\sum_{i \in R_u} -\log_2\left(\frac{\text{pop}_i}{P_{\text{train}}}\right), \quad \text{Diversity@10} = \frac{1}{\binom{10}{2}} \sum_{i<j}(1 - \text{Jaccard}(G_i, G_j))$",
     (8.5, 1.2)),
]

for fname, latex, figsize in formulas:
    fig, ax = plt.subplots(figsize=figsize, dpi=150)
    ax.text(0.5, 0.5, latex, ha='center', va='center', fontsize=16, 
            transform=ax.transAxes, bbox=dict(boxstyle='round', facecolor='white', edgecolor='none'))
    ax.axis('off')
    fig.savefig(OUT_DIR / fname, bbox_inches='tight', facecolor='white', pad_inches=0.1)
    plt.close(fig)
    print(f"OK {fname}")

print(f"Saved {len(formulas)} formula images to {OUT_DIR}")

