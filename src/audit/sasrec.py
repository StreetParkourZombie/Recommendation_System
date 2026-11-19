"""SASRec + cross-entropy (full-catalog softmax) — baseline SOTA da dang ki.

Danh sach baseline dang ki (docs/About/Reseach_Method_Submission.md):
  san         : Random, MostPopular
  kinh dien   : ALS, ItemKNN cosine
  SOTA        : SASRec ket hop cross-entropy

Khac voi 4 baseline tren (chay Spark/CPU), module nay dung PyTorch + CUDA
(RTX 4050 Laptop 6 GB — docs/About/Hardware_Resources.md). Vi vay khong
duoc so sanh runtime cua SASRec truc tiep voi runtime ALS/ItemKNN; chi so
sanh duoc la chat luong (NDCG@10, Hit@10, Recall@10) cung protocol.

Khac voi repo goc cua bai [03_RecSys2025_TimeToSplit]
(docs/References/Papers/Code/dataLeakageRec/SASRec/train.py):
  repo goc  : BCEWithLogitsLoss, 1 negative/ngoai vi tri (sampled)
  o day     : cross-entropy softmax tren TOAN BO catalog — dung ten
              "SASRec + cross-entropy" da dang ki, va la loss cho phep
              so sanh cong bang voi viec xep hang toan bo catalog luc eval.

Loss va eval deu loai item da thay (xem _mask_seen luc eval); train dung
chinh xac la item ke tiep trong chuoi positive (rating >= 4.0).

Sach/protocol tham chieu:
  Kang & McAuley, "Self-Attentive Sequential Recommendation" (ICDM 2018)
  [03] TimeToSplit (RecSys 2025) — giao thuc kiem dinh leak tren chuoi
"""
from __future__ import annotations

import copy
import time
from collections.abc import Iterable

import numpy as np


# ---------------------------------------------------------------- vocab / data
def build_vocab(item_ids) -> tuple[np.ndarray, dict[int, int]]:
    """Item id -> vi tri lien tuc 0..n-1 (tang dan theo movieId)."""
    uniq = np.unique(np.asarray(item_ids, dtype=np.int64))
    pos = {int(i): k for k, i in enumerate(uniq)}
    return uniq, pos


def build_sequences(
    user_ids, item_pos, timestamps, max_len: int = 50, min_len: int = 2
) -> dict[int, np.ndarray]:
    """Moi user -> mang vi tri item (0-based) theo timestamp tang dan, cat duoi max_len.

    Cat duoi (giu lan tuong tac MUON NHAT) vi SASRec duoc huan luyen de du doan
    item ke tiep; chuan nay giong het cach repo [03] dung maxlen.
    """
    u = np.asarray(user_ids, dtype=np.int64)
    p = np.asarray(item_pos, dtype=np.int64)
    t = np.asarray(timestamps, dtype=np.int64)
    order = np.lexsort((t, u))
    u_s, p_s = u[order], p[order]
    uniq_u, starts = np.unique(u_s, return_index=True)
    ends = np.append(starts[1:], len(u_s))
    seqs: dict[int, np.ndarray] = {}
    for uid, s, e in zip(uniq_u.tolist(), starts.tolist(), ends.tolist()):
        if e - s < min_len:
            continue
        seg = p_s[s:e]
        if seg.size > max_len:
            seg = seg[-max_len:]
        seqs[int(uid)] = seg.astype(np.int32)
    return seqs


class SeqData:
    """Nen chuoi thanh (flat, offsets) de lay batch khong copy nhieu lan."""

    def __init__(self, seqs: dict[int, np.ndarray]):
        self.users = np.array(sorted(seqs), dtype=np.int64)
        self._seqs = seqs
        if len(self.users) == 0:
            self.flat = np.zeros(0, dtype=np.int32)
            self.offsets = np.zeros(1, dtype=np.int64)
            self.lens = np.zeros(0, dtype=np.int32)
        else:
            self.lens = np.array([seqs[int(u)].size for u in self.users], dtype=np.int32)
            self.flat = np.concatenate([seqs[int(u)] for u in self.users]).astype(np.int32)
            self.offsets = np.zeros(len(self.users) + 1, dtype=np.int64)
            np.cumsum(self.lens, out=self.offsets[1:])

    def __len__(self) -> int:
        return int(self.users.size)

    def batch(self, rows: Iterable[int], torch, device):
        """rows = chi so user. Tra (x, y) voi x: 0=pad, item = pos+1; y: -100=pad."""
        rows = np.asarray(list(rows), dtype=np.int64)
        ln = self.lens[rows]
        width = int(ln.max())
        x = np.zeros((rows.size, width), dtype=np.int64)
        y = np.full((rows.size, width), -1, dtype=np.int64)
        for b, r in enumerate(rows.tolist()):
            s, e = int(self.offsets[r]), int(self.offsets[r + 1])
            seg = self.flat[s:e]
            n = seg.size
            x[b, width - n:] = seg + 1
            y[b, width - n:] = seg
        return (
            torch.from_numpy(x).to(device),
            torch.from_numpy(y).to(device),
        )


# ---------------------------------------------------------------- model
# Module nay KHONG import torch o cap top: may chua cai PyTorch van doc/
# import duoc cac module khac cua src.audit. torch duoc truyen vao tung ham.
def make_model(torch, n_items: int, hidden: int, max_len: int, num_blocks: int,
               num_heads: int, dropout: float, device):
    class _FF(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.c1 = torch.nn.Conv1d(hidden, hidden, kernel_size=1)
            self.d1 = torch.nn.Dropout(p=dropout)
            self.c2 = torch.nn.Conv1d(hidden, hidden, kernel_size=1)
            self.d2 = torch.nn.Dropout(p=dropout)

        def forward(self, x):
            h = self.d2(self.c2(torch.relu(self.d1(self.c1(x.transpose(-1, -2))))))
            return h.transpose(-1, -2) + x

    class _Net(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.item_emb = torch.nn.Embedding(n_items + 1, hidden, padding_idx=0)
            self.pos_emb = torch.nn.Embedding(max_len, hidden)
            self.emb_drop = torch.nn.Dropout(p=dropout)
            self.norms = torch.nn.ModuleList()
            self.attns = torch.nn.ModuleList()
            self.ffs = torch.nn.ModuleList()
            for _ in range(num_blocks):
                self.norms.append(torch.nn.LayerNorm(hidden, eps=1e-8))
                self.attns.append(torch.nn.MultiheadAttention(
                    embed_dim=hidden, num_heads=num_heads, dropout=dropout, batch_first=True))
                self.ffs.append(_FF())
            self.last_norm = torch.nn.LayerNorm(hidden, eps=1e-8)
            self._causal = {}

        def _causal_mask(self, L, dev, dtype):
            key = (L, str(dev), 'bool')
            m = self._causal.get(key)
            if m is None:
                # bool mask cho CAH attn_mask va key_padding_mask -> tranh canh bao
                # 'Support for mismatched key_padding_mask and attn_mask is deprecated'.
                # True = bi mask (o tren duong cheo) — tuong duong -inf ban dau.
                m = torch.ones((L, L), dtype=torch.bool, device=dev).triu(1)
                self._causal[key] = m
            return m

        def encode(self, x):
            """x: (B, L) long, 0 = pad. Tra (B, L, hidden)."""
            B, L = x.shape
            if L > max_len:
                x = x[:, -max_len:]
                L = max_len
            pos = torch.arange(L, device=x.device).unsqueeze(0).expand(B, L)
            h = self.item_emb(x) + self.pos_emb(pos)
            h = self.emb_drop(h)
            pad_mask = (x == 0)
            causal = self._causal_mask(L, x.device, h.dtype)
            for norm, attn, ff in zip(self.norms, self.attns, self.ffs):
                z = norm(h)
                a, _ = attn(z, z, z, attn_mask=causal, key_padding_mask=pad_mask,
                            need_weights=False)
                h = h + a
                h = h + ff(norm(h))
            return self.last_norm(h)

        def logits(self, h, temperature=None):
            """(…, hidden) -> (…, n_items): softmax tren TOAN BO catalog."""
            flat = h.reshape(-1, h.shape[-1])
            out = flat @ self.item_emb.weight[1:].transpose(0, 1)
            if temperature:
                out = out / temperature
            return out

    net = _Net().to(device)
    for name, param in net.named_parameters():
        if param.dim() > 1 and "attn" not in name:
            torch.nn.init.xavier_normal_(param.data)
    return net


# ---------------------------------------------------------------- train
def train_model(
    torch,
    net,
    data: "SeqData",
    val: "SeqData",
    n_items: int,
    device,
    epochs: int = 20,
    lr: float = 1e-3,
    batch_size: int = 32,
    accum_steps: int = 4,
    weight_decay: float = 0.0,
    patience: int = 3,
    seed: int = 42,
    k_eval: int = 10,
    progress=None,
):
    """Huan luyen cross-entropy full-catalog. Early stopping tren `val`.

    Tra (fit_seconds, history) — history: list dict per epoch.
    `net` duoc cap nhat truc tiep ve trong so tot nhat theo val NDCG@10.
    """
    ce = torch.nn.CrossEntropyLoss()
    opt = torch.optim.Adam(net.parameters(), lr=lr, betas=(0.9, 0.98), weight_decay=weight_decay)
    g = torch.Generator(device="cpu").manual_seed(seed)
    history = []
    best = -1.0
    best_state = None
    best_epoch = 0
    started = time.perf_counter()

    for epoch in range(1, epochs + 1):
        net.train()
        order = torch.randperm(len(data), generator=g).tolist()
        opt.zero_grad(set_to_none=True)
        total_loss = 0.0
        n_batches = 0
        for i in range(0, len(order), batch_size):
            rows = order[i:i + batch_size]
            x, y = data.batch(rows, torch, device)
            h = net.encode(x)
            logits = net.logits(h)
            target = y.reshape(-1).to(device)
            valid = target >= 0
            loss = ce(logits[valid], target[valid]) / accum_steps
            loss.backward()
            total_loss += float(loss.item()) * accum_steps
            n_batches += 1
            if n_batches % accum_steps == 0 or i + batch_size >= len(order):
                opt.step()
                opt.zero_grad(set_to_none=True)
        epoch_loss = total_loss / max(n_batches, 1)

        val_ndcg = evaluate_ndcg(torch, net, val, n_items, device, k=k_eval, chunk=256)
        elapsed = time.perf_counter() - started
        history.append({
            "epoch": epoch,
            "loss": round(epoch_loss, 5),
            "val_ndcg10": round(val_ndcg, 5),
            "elapsed_seconds": round(elapsed, 1),
        })
        if progress is not None:
            progress(epoch, epochs, epoch_loss, val_ndcg, elapsed)

        if val_ndcg > best + 1e-6:
            best = val_ndcg
            best_epoch = epoch
            best_state = copy.deepcopy(net.state_dict())
        elif epoch - best_epoch >= patience:
            if progress is not None:
                progress("early_stop", epoch, epoch_loss, val_ndcg, elapsed)
            break

    if best_state is not None:
        net.load_state_dict(best_state)
    fit_seconds = time.perf_counter() - started
    meta = {
        "best_epoch": best_epoch,
        "best_val_ndcg10": round(best, 5),
        "epochs_run": len(history),
        "fit_seconds": round(fit_seconds, 1),
    }
    return fit_seconds, history, meta


# ---------------------------------------------------------------- eval
def _mask_seen(torch, logits, seen_rows, device):
    """Dat -inf tai vi tri item user da thay (loai khoi bang xep hang).

    Scatter mot lan: dung boolean mask (B, n_items) roi masked_fill — nhanh hon
    vong lap gan tung dong tren GPU (kernel launch per row).
    """
    n_rows = logits.shape[0]
    keep = torch.ones_like(logits, dtype=torch.bool)
    rows, cols = [], []
    for b, cs in enumerate(seen_rows):
        if cs:
            rows.extend([b] * len(cs))
            cols.extend(cs)
    if rows:
        r = torch.as_tensor(rows, dtype=torch.long, device=device)
        c = torch.as_tensor(cols, dtype=torch.long, device=device)
        keep[r, c] = False
    return logits.masked_fill(~keep, float("-inf"))


def evaluate_ndcg(torch, net, data: "SeqData", n_items: int, device, k: int = 10,
                  chunk: int = 256) -> float:
    """NDCG@k tren tap validation theo lech luu tru holdout-last.

    Voi moi chuoi cua `data`: dung TAT CA phan tu TRU phan tu cuoi lam dau vao,
    du doan chinh phan tu cuoi. Relevant = {phan tu cuoi} -> idcg = 1 nen
    NDCG@k = 1/log2(rank+1) neu vao top-k, nguoi lai 0. Cach nay khong "gian"
    dap an vi dap an bi an khoi dau vao.
    """
    if len(data) == 0:
        return 0.0
    discounts = 1.0 / np.log2(np.arange(2, k + 2))
    scores = []
    net.eval()
    with torch.no_grad():
        for start in range(0, len(data), chunk):
            rows = list(range(start, min(start + chunk, len(data))))
            x, _ = data.batch(rows, torch, device)
            if x.shape[1] < 2:
                continue
            truth_item = x[:, -1].cpu().numpy()
            xt = x[:, :-1].contiguous()
            h = net.encode(xt)
            logits = (h[:, -1, :] @ net.item_emb.weight[1:].transpose(0, 1)).float()
            top = torch.topk(logits, k=k, dim=1).indices.cpu().numpy() + 1
            for b, tgt in enumerate(truth_item):
                t = int(tgt)
                if t <= 0:
                    continue
                hit = np.where(top[b] == t)[0]
                scores.append(float(discounts[hit[0]]) if hit.size else 0.0)
    if not scores:
        return 0.0
    return float(np.mean(scores))


def recommend_topk(
    torch,
    net,
    seqs: dict[int, np.ndarray],
    users_to_score: Iterable[int],
    seen_by_user: dict[int, set[int]],
    vocab_pos: dict[int, int],
    n_items: int,
    device,
    k: int = 10,
    chunk: int = 128,
    progress=None,
) -> dict[int, np.ndarray]:
    """Top-k movieId cho tung user, da loai item da thay (train)."""
    targets = sorted(set(int(u) for u in users_to_score))
    out: dict[int, np.ndarray] = {}
    inv_vocab = {p: i for i, p in vocab_pos.items()}
    net.eval()
    total = len(targets)
    with torch.no_grad():
        for start in range(0, total, chunk):
            block = targets[start:start + chunk]
            seq_block = [seqs.get(u) for u in block]
            ln = [0 if s is None else s.size for s in seq_block]
            width = max(ln) if ln else 0
            if width == 0:
                for u in block:
                    out[u] = np.array([], dtype=np.int64)
                continue
            x = np.zeros((len(block), max(width, 1)), dtype=np.int64)
            keep_rows = []
            for b, s in enumerate(seq_block):
                if s is None or s.size == 0:
                    continue
                x[b, width - s.size:] = s + 1
                keep_rows.append(b)
            xt = torch.from_numpy(x).to(device)
            h = net.encode(xt)
            logits = (h[:, -1, :] @ net.item_emb.weight[1:].transpose(0, 1)).float()
            seen_rows = []
            for b, u in enumerate(block):
                cols = [vocab_pos[i] for i in seen_by_user.get(u, ()) if int(i) in vocab_pos]
                seen_rows.append(cols)
            logits = _mask_seen(torch, logits, seen_rows, device)
            kk = min(k, n_items)
            top = torch.topk(logits, k=kk, dim=1).indices.cpu().numpy()
            for b, u in enumerate(block):
                if b not in keep_rows:
                    out[u] = np.array([], dtype=np.int64)
                    continue
                out[u] = np.array([inv_vocab[int(p)] for p in top[b] if p >= 0], dtype=np.int64)
            if progress is not None:
                progress(min(start + chunk, total), total)
    return out


def cuda_report(torch):
    """Thong tin phan cung ghi vao summary (khai bao GPU khac 4 baseline CPU)."""
    rep = {
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "cuda_available": bool(torch.cuda.is_available()),
    }
    if rep["cuda_available"]:
        idx = 0
        rep["device_name"] = torch.cuda.get_device_name(idx)
        rep["device_total_memory_mib"] = round(torch.cuda.get_device_properties(idx).total_memory / 2**20, 1)
        free_b, total_b = torch.cuda.mem_get_info(idx)
        rep["device_free_memory_mib_at_start"] = round(free_b / 2**20, 1)
        rep["capability"] = ".".join(map(str, torch.cuda.get_device_capability(idx)))
    else:
        rep["device_name"] = "cpu"
    return rep
