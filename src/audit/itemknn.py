"""ItemKNN cosine k=100 — co-count bang scipy sparse, khong dung Spark self-join.

Ly do doi phuong phap: ban dau dung self-join (user,item) x (user,item) tren Spark —
tao ~1,2 ty cap shuffle, chay >1h chua xong 1 split tren local[4] (timeout cell 3600s).
Cach chuan trong tai lieu RecSys (EASE/SASRec baseline repos dung): ma tran thua
R (users x items, implicit positive), S = R.T @ R la co-count bang sparse matmul
(scipy), chuan hoa cosine W_ij = S_ij / sqrt(pop_i * pop_j), giu top-k=100 neighbor
moi item.

Sach tham chieu: Sarwar et al., "Item-based Collaborative Filtering Recommendation
Algorithms" (WWW 2001) — cosine item-item.

Pruning khai bao: giu cap co-count co >= min_co (mac dinh 2) user chung — bien the
tien nghi cua ItemKNN (loc cap chi chung 1 user — nhieu nhieu); day la bien the co
khai bao trong notebook, khong phai ItemKNN nguyen ban khong loc.
"""
from __future__ import annotations

import time
from collections.abc import Iterable

import numpy as np
from scipy import sparse


def _load_matrix(train_positive):
    """(users x items) sparse binary tu DataFrame. Dung toPandas (Arrow) — collect()
    Row objects 20M dong se tran driver."""
    pairs = train_positive.select("userId", "movieId").distinct()
    pdf = pairs.toPandas()
    user_ids = pdf["userId"].to_numpy(dtype=np.int64)
    item_ids = pdf["movieId"].to_numpy(dtype=np.int64)

    uniq_items, item_col = np.unique(item_ids, return_inverse=True)
    uniq_users, user_row = np.unique(user_ids, return_inverse=True)
    r = sparse.csr_matrix(
        (np.ones(len(item_ids), dtype=np.float32), (user_row, item_col)),
        shape=(len(uniq_users), len(uniq_items)),
    )
    r.sum_duplicates()
    r.data[:] = 1.0
    return r, uniq_items


def fit(train_positive, k_neighbors: int = 100, min_co: int = 2):
    """Fit ItemKNN cosine tu DataFrame train_positive (userId, movieId).

    Tra (fit_seconds, model) voi model = dict:
      vi        : item ids (tang dan; index = cot cua R)
      nbr_idx   : (n_items, k_neighbors) int32 — top-k neighbor cua item i (-1 = het cho)
      nbr_w     : (n_items, k_neighbors) float32 — trong so cosine
      n_pairs   : nnz cua S sau pruning (so cap item co >= min_co user chung)
      n_items   : so item trong catalog cua split
      min_co    : nguong pruning da khai bao
    """
    started = time.perf_counter()

    r, uniq_items = _load_matrix(train_positive)
    n_items = int(r.shape[1])

    pop = np.asarray(r.sum(axis=0)).ravel()          # so user cua tung item (truoc pruning)
    inv_sqrt = 1.0 / np.sqrt(np.maximum(pop, 1.0))

    s = (r.T @ r).tocsr()
    del r
    s.data[s.data < min_co] = 0.0   # pruning khai bao
    s.setdiag(0.0)                  # loai self-similarity
    s.eliminate_zeros()

    w = s.multiply(inv_sqrt[:, None]).multiply(inv_sqrt[None, :]).tocsr()
    del s, pop, inv_sqrt

    coo = w.tocoo()
    del w
    src, dst, val = coo.row, coo.col, coo.data
    order = np.lexsort((-val, src))  # theo src tang dan, val giam dan
    src_s, dst_s, val_s = src[order], dst[order], val[order]
    starts = np.searchsorted(src_s, np.arange(n_items), side="left")
    ends = np.searchsorted(src_s, np.arange(n_items), side="right")

    nbr_idx = np.full((n_items, k_neighbors), -1, dtype=np.int32)
    nbr_w = np.zeros((n_items, k_neighbors), dtype=np.float32)
    for i in range(n_items):
        take = min(k_neighbors, int(ends[i] - starts[i]))
        if take > 0:
            sl = slice(int(starts[i]), int(starts[i]) + take)
            nbr_idx[i, :take] = dst_s[sl]
            nbr_w[i, :take] = val_s[sl]

    fit_seconds = time.perf_counter() - started
    model = {
        "vi": uniq_items,
        "nbr_idx": nbr_idx,
        "nbr_w": nbr_w,
        "n_pairs": int(len(val)),
        "n_items": n_items,
        "k_neighbors": int(k_neighbors),
        "min_co": int(min_co),
    }
    return fit_seconds, model


def score_users(
    model: dict,
    seen_by_user: dict[int, Iterable[int]],
    only_users: Iterable[int],
    k: int = 10,
    progress=None,
    chunk: int = 5000,
) -> dict[int, np.ndarray]:
    """Top-K item theo score = tong w_ij tren item user da thay, loai item da thay."""
    vi = model["vi"]
    nbr_idx = model["nbr_idx"]
    nbr_w = model["nbr_w"]
    item_position = {int(i): pos for pos, i in enumerate(vi)}

    targets = sorted(set(int(u) for u in only_users))
    out: dict[int, np.ndarray] = {}

    total = len(targets)
    for start in range(0, total, chunk):
        stop = min(start + chunk, total)
        for user in targets[start:stop]:
            seen = seen_by_user.get(user)
            if not seen:
                out[user] = np.array([], dtype=np.int64)
                continue
            cols = np.fromiter(
                (item_position[i] for i in seen if int(i) in item_position),
                dtype=np.int64,
            )
            if cols.size == 0:
                out[user] = np.array([], dtype=np.int64)
                continue
            idx_flat = nbr_idx[cols].ravel()
            w_flat = nbr_w[cols].ravel()
            valid = idx_flat >= 0
            if not valid.any():
                out[user] = np.array([], dtype=np.int64)
                continue
            uniq, inv = np.unique(idx_flat[valid], return_inverse=True)
            agg = np.bincount(inv, weights=w_flat[valid])

            keep = ~np.isin(uniq, cols)  # loai item da thay
            uniq, agg = uniq[keep], agg[keep]
            if uniq.size == 0:
                out[user] = np.array([], dtype=np.int64)
                continue

            kk = min(k, uniq.size)
            top = np.argpartition(-agg, kk - 1)[:kk] if uniq.size > kk else np.arange(uniq.size)
            top = top[np.argsort(-agg[top])]
            out[user] = vi[uniq[top]]
        if progress is not None:
            progress(stop, total)
    return out
