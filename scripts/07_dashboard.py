"""Streamlit dashboard - doc MongoDB recsys.audit_metrics
Chay: streamlit run scripts/07_dashboard.py
"""
import os, sys
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import streamlit as st
import pandas as pd
from pymongo import MongoClient

st.set_page_config(page_title="Audit chiến lược chia tập — Hệ thống gợi ý",
                   page_icon="🎬", layout="wide")

st.title("🎬 Đánh giá tác động của chiến lược chia tập dữ liệu")
st.caption("MovieLens ml-25m · 25.000.095 tương tác · Spark 4.2.0 · seed 42")

MONGO = "mongodb://localhost:27017"

@st.cache_resource
def get_conn():
    return MongoClient(MONGO, serverSelectionTimeoutMS=5000)

try:
    client = get_conn()
    client.server_info()
    db = client["recsys"]
    docs = list(db.audit_metrics.find({}, {"_id": 0}))
    if not docs:
        st.error("Chưa có dữ liệu trong MongoDB. Chạy `python scripts/05_store_mongodb.py` trước.")
        st.stop()
    df = pd.DataFrame(docs)
except Exception as e:
    st.error(f"Không kết nối được MongoDB: {e}")
    st.stop()

SPLIT_VN = {
    "random80_20": "Ngẫu nhiên 80/20",
    "temporal_global": "Theo thời gian toàn cục",
    "leave_one_out": "Leave-one-out (theo user)",
}
MODEL_VN = {"Popularity": "Popularity (baseline)", "ALS_implicit": "ALS (implicit)"}

if "split" in df.columns:
    df["split"] = df["split"].map(lambda x: SPLIT_VN.get(x, x))
if "model" in df.columns:
    df["model"] = df["model"].map(lambda x: MODEL_VN.get(x, x))

# ---------------- sidebar ----------------
st.sidebar.header("Bộ lọc")
split_sel = st.sidebar.multiselect("Chiến lược chia tập",
                                   options=sorted(df["split"].unique()),
                                   default=sorted(df["split"].unique()))
model_sel = st.sidebar.multiselect("Mô hình",
                                  options=sorted(df["model"].unique()),
                                  default=sorted(df["model"].unique()))
view = df[df["split"].isin(split_sel) & df["model"].isin(model_sel)].copy()

if view.empty:
    st.warning("Không có dòng dữ liệu khớp bộ lọc.")
    st.stop()

# ---------------- KPI ----------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Số tương tác", f"{int(view['train_rows'].iloc[0]) + int(view['test_rows'].iloc[0]):,}")
c1.caption("MovieLens ml-25m")

leak = view[view["split"] == "Ngẫu nhiên 80/20"]
if not leak.empty:
    c2.metric("Rò rỉ (ngẫu nhiên)", f"{leak['temporal_violation_global_pct'].iloc[0]:.1f}%",
              delta="toàn cục", delta_color="off")
    c3.metric("Rò rỉ tương đối user", f"{leak['temporal_violation_user_pct'].iloc[0]:.1f}%",
              delta="cùng người dùng", delta_color="off")
c4.metric("Số dòng kết quả", f"{len(view)}")

# ---------------- bảng ----------------
st.subheader("1. Chỉ số cấp dữ liệu — đo mức độ rò rỉ và dịch chuyển miền")
data_cols = ["split", "train_rows", "test_rows", "temporal_violation_global_pct",
             "temporal_violation_user_pct", "unseen_item_pct",
             "coldstart_user_rows", "eval_users", "eval_relevant_users"]
if "temporal_violation_global_pct" in view.columns:
    show = view[[c for c in data_cols if c in view.columns]].drop_duplicates(subset=["split"])
    show = show.rename(columns={
        "split": "Chiến lược", "train_rows": "Train", "test_rows": "Test",
        "temporal_violation_global_pct": "Vi phạm toàn cục (%)",
        "temporal_violation_user_pct": "Vi phạm tương đối user (%)",
        "unseen_item_pct": "Item chưa từng xuất hiện (%)",
        "coldstart_user_rows": "User lạnh",
        "eval_users": "User đánh giá", "eval_relevant_users": "User có relevant"})
    st.dataframe(show, use_container_width=True)

st.subheader("2. Hiệu quả gợi ý và thiên lệch phổ biến")
metric_cols = [c for c in ["split", "model", "ndcg10", "hit_rate10", "catalog_coverage",
                           "longtail_coverage", "gini_exposure", "popularity_bias_ratio"]
               if c in view.columns]
show2 = view[metric_cols].rename(columns={
    "split": "Chiến lược", "model": "Mô hình", "ndcg10": "NDCG@10",
    "hit_rate10": "Hit Rate@10", "catalog_coverage": "Độ phủ danh mục",
    "longtail_coverage": "Độ phủ đuôi dài", "gini_exposure": "Gini phơi bày",
    "popularity_bias_ratio": "Tỷ lệ thiên lệch phổ biến"})
st.dataframe(show2, use_container_width=True)

# ---------------- biểu đồ ----------------
st.subheader("3. Biểu đồ so sánh")
tab1, tab2, tab3 = st.tabs(["NDCG@10", "Thiên lệch phổ biến", "Rò rỉ thời gian"])

with tab1:
    if "ndcg10" in view.columns:
        piv = view.pivot_table(index="split", columns="model", values="ndcg10")
        st.bar_chart(piv)
        st.caption("NDCG@10: giá trị thấp = tín hiệu đo yếu. So sánh cột để thấy thứ hạng mô hình.")

with tab2:
    if "popularity_bias_ratio" in view.columns:
        piv2 = view.pivot_table(index="split", columns="model", values="popularity_bias_ratio")
        st.bar_chart(piv2)
        st.caption("Tỷ lệ = popularity(item được đề xuất) / popularity(catalog). > 1 = thiên lệch phổ biến.")
    if "gini_exposure" in view.columns:
        st.bar_chart(view.pivot_table(index="split", columns="model", values="gini_exposure"))
        st.caption("Gini mức phơi bày: gần 1 = tập trung vào ít item phổ biến.")

with tab3:
    if "temporal_violation_global_pct" in view.columns:
        d = view[["split", "temporal_violation_global_pct", "temporal_violation_user_pct"]].drop_duplicates("split")
        st.bar_chart(d.set_index("split"))
        st.caption("Toàn cục: test trước mốc lớn nhất của train. Tương đối user: test trước mốc lớn nhất train CỦA CHÍNH user.")

# ---------------- item profile ----------------
st.subheader("4. Hồ sơ phim (từ MongoDB)")
try:
    cnt = db.item_profile.count_documents({})
    if cnt:
        st.caption(f"{cnt:,} phim trong collection `item_profile`")
        ids = st.multiselect("Chọn movieId để xem hồ sơ", options=[], help="Nhập movieId")
        raw = st.text_input("movieId (ví dụ 318, 296, 260):")
        if raw:
            try:
                mid = int(raw)
                doc = db.item_profile.find_one({"movieId": mid}, {"_id": 0})
                if doc:
                    st.json(doc)
                else:
                    st.warning(f"Không tìm thấy movieId {mid}")
            except ValueError:
                st.warning("movieId phải là số nguyên.")
    else:
        st.info("Collection `item_profile` chưa có dữ liệu. Chạy `python scripts/05_store_mongodb.py`.")
except Exception as e:
    st.info(f"Không đọc được item_profile: {e}")

st.divider()
st.caption("Nguồn: `D:\\recsys_data\\poc\\poc6_<split>.json` → MongoDB `recsys.audit_metrics` · "
           "Đề tài: Đánh giá tác động của chiến lược chia tập dữ liệu đến tín hiệu đo và thiên lệch phổ biến")
