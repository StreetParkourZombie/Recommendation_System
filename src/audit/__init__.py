"""Audit toolkit cho pipeline chia tập RecSys.

Module con:
- splits      : sinh 3 chiến lược chia tập, ghi/đọc Parquet
- leakage     : audit tầng dữ liệu (rò rỉ thời gian, item/user lạnh)
- popularity  : baseline MostPopular + chỉ số thiên lệch
- metrics     : NDCG/DCG/Hit/Recall/Gini thuần Python, có fixture kiểm tra tay
- als_rec     : ALS implicit + top-K NumPy
- io          : ghi JSON, SHA-256, đọc lại kiểm tra
"""
from __future__ import annotations

__all__ = [
    "als_rec",
    "io",
    "leakage",
    "metrics",
    "popularity",
    "splits",
]

