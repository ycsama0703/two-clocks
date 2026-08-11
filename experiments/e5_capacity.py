# -*- coding: utf-8 -*-
"""E5 — capacity allocation between a lattice axis and a dense axis.

E3 showed dual-clock scoring 0.87 on task A but only 0.63 on task B. The cause
is suspected to be the naive split: the embedding is halved, giving each clock
384 dimensions. But the closed form says the two axes carry very different
amounts of information:

    availability   lattice; must separate "which version precedes as_of".
                   k=2 in 76% of series, k=3 in 21%  ->  about 1 bit
    event          dense; must separate L positions in the pool
                   L=200  ->  log2(200) ~ 7.6 bits

If that is right, a 1:1 split wastes 384 dimensions encoding ~1 bit while
starving the axis that needs 7.6.

Sweep the split and see. Pre-registered expectation, written before running:

    task A stays flat as the availability band shrinks (1 bit needs few dims)
    task B rises as the event band grows
    -> capacity should be allocated by information content, and the closed form
       says how much each axis needs

If both tasks are flat across the sweep, the allocation rule is worthless and
this angle closes like the previous three.
"""
import json
import os
import sys
from collections import defaultdict, Counter
from datetime import date

import numpy as np
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N_PAIRS = int(os.environ.get("N_PAIRS", 600))
L, SEED = 200, 0
rng = np.random.default_rng(SEED)
D = lambda s: date(*map(int, s.split("-")))

C = {}
for line in open(os.path.join(ROOT, "data/chunks.jsonl"), encoding="utf-8"):
    c = json.loads(line)
    C[c["id"]] = c
Q = [json.loads(l) for l in open(os.path.join(ROOT, "data/queries.jsonl"), encoding="utf-8")]
by_tick = defaultdict(list)
for c in C.values():
    by_tick[c["ticker"]].append(c)

# ---- task A: same event_time, different avail_time -------------------------
selA = [Q[i] for i in rng.choice(len(Q), N_PAIRS, replace=False)]
A = []
for q in selA:
    f = rng.random() < 0.5
    a, b = (q["distractor_id"], q["gold_id"]) if f else (q["gold_id"], q["distractor_id"])
    A.append({"a": a, "b": b, "y": 0 if f else 1, "concept": q["concept"], "ticker": q["ticker"]})

# ---- task B: same avail_time (same filing), different event_time ------------
byfiling = defaultdict(list)
for c in C.values():
    byfiling[(c["ticker"], c["concept"], c["avail_time"])].append(c)
B = []
for key, rows in byfiling.items():
    if len(B) >= N_PAIRS:
        break
    ends = {}
    for r in rows:
        ends.setdefault(r["event_time"], r)
    if len(ends) < 2:
        continue
    (e1, r1), (e2, r2) = sorted(ends.items())[:2]
    if r1["value"] == r2["value"]:
        continue
    d = max(abs(r1["value"]), abs(r2["value"]))
    if d == 0 or abs(r2["value"] - r1["value"]) / d < 0.01:
        continue
    f = rng.random() < 0.5
    a, b = (r2["id"], r1["id"]) if f else (r1["id"], r2["id"])
    B.append({"a": a, "b": b, "y": 0 if f else 1, "concept": key[1], "ticker": key[0]})
print("task A %d   task B %d" % (len(A), len(B)), flush=True)

need = sorted({i["a"] for i in A + B} | {i["b"] for i in A + B})
from transformers import AutoTokenizer, AutoModel
tok = AutoTokenizer.from_pretrained("thenlper/gte-base")
mdl = AutoModel.from_pretrained("thenlper/gte-base").eval()
CACHE = os.path.join(ROOT, "experiments", "emb_cache_e5.npz")
emb = None
if os.path.exists(CACHE):
    z = np.load(CACHE, allow_pickle=True)
    e = {str(k): v for k, v in zip(z["ids"], z["vecs"])}
    if set(e) == set(need):
        emb = e
if emb is None:
    out, bs = [], 128
    for i in range(0, len(need), bs):
        bb = tok([C[k]["text"] for k in need[i:i + bs]], padding=True, truncation=True,
                 max_length=64, return_tensors="pt")
        with torch.no_grad():
            h = mdl(**bb).last_hidden_state
            m = bb["attention_mask"].unsqueeze(-1).float()
            v = torch.nn.functional.normalize((h * m).sum(1) / m.sum(1), dim=-1)
        out.append(v.numpy())
        if i % 2560 == 0:
            print("   encode %d/%d" % (i, len(need)), flush=True)
    emb = dict(zip(need, np.concatenate(out)))
    np.savez(CACHE, ids=np.array(need), vecs=np.stack([emb[k] for k in need]))
DIM = len(emb[need[0]])
print("embeddings ready dim=%d" % DIM, flush=True)


def relpos(n, step=20):
    return np.linspace(0, int(0.9 * step), n).astype(np.float32)


def rope(vec, pos, theta=10000.0):
    d = vec.shape[-1]
    de = d - d % 2
    half = de // 2
    if half == 0:
        return vec.copy()
    inv = theta ** (-np.arange(half, dtype=np.float64) * 2.0 / half)
    ang = np.int32(pos) * inv
    cos, sin = np.cos(ang), np.sin(ang)
    x1, x2 = vec[:half], vec[half:de]
    r = np.concatenate([x1 * cos - x2 * sin, x1 * sin + x2 * cos])
    return r if de == d else np.concatenate([r, vec[de:]])


def build(inst_list, avail_dims):
    """avail_dims: dimensions given to the availability band; the rest go to event."""
    ev = DIM - avail_dims
    ev -= ev % 2
    av = avail_dims - (avail_dims % 2)
    X = np.zeros((len(inst_list), ev + av), dtype=np.float32)
    for i, inst in enumerate(inst_list):
        ea, eb = emb[inst["a"]], emb[inst["b"]]
        pool = [c for c in by_tick[inst["ticker"]] if c["id"] not in (inst["a"], inst["b"])]
        if len(pool) > L - 2:
            pool = [pool[j] for j in rng.choice(len(pool), L - 2, replace=False)]
        items = pool + [C[inst["a"]], C[inst["b"]]]
        items = [items[j] for j in rng.permutation(len(items))]
        items.sort(key=lambda c: c["event_time"])
        n = len(items)
        ia = next(j for j, c in enumerate(items) if c["id"] == inst["a"])
        ib = next(j for j, c in enumerate(items) if c["id"] == inst["b"])
        r = relpos(n)
        oe = np.argsort(np.argsort([c["event_time"] for c in items]))
        oa = np.argsort(np.argsort([c["avail_time"] for c in items]))
        re_, ra_ = r[oe], r[oa]
        va = np.concatenate([rope(ea[:ev], re_[ia]), rope(ea[ev:ev + av], ra_[ia])])
        vb = np.concatenate([rope(eb[:ev], re_[ib]), rope(eb[ev:ev + av], ra_[ib])])
        X[i] = va - vb
    return np.nan_to_num(X)


def score(X, inst_list):
    y = np.array([i["y"] for i in inst_list])
    g = np.array([i["concept"] for i in inst_list])
    pipe = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, C=0.1))
    return cross_val_score(pipe, X, y, cv=GroupKFold(5), groups=g).mean()


SPLITS = [384, 256, 128, 64, 32, 16, 8]
print("\n" + "=" * 62)
print("E5  capacity allocation (total dim %d)" % DIM)
print("=" * 62)
print("%-12s %-12s %9s %9s" % ("avail dims", "event dims", "task A", "task B"))
res = {}
for ad in SPLITS:
    ta = score(build(A, ad), A)
    tb = score(build(B, ad), B)
    res[ad] = (ta, tb)
    print("%-12d %-12d %9.4f %9.4f" % (ad, DIM - ad, ta, tb), flush=True)

print()
base = res[384]
best_b = max(res.items(), key=lambda kv: kv[1][1])
print("1:1 split (384/384)      task A %.4f  task B %.4f" % base)
print("best task B at %d dims   task A %.4f  task B %.4f  (delta B %+.4f)"
      % (best_b[0], best_b[1][0], best_b[1][1], best_b[1][1] - base[1]))
json.dump({str(k): v for k, v in res.items()},
          open(os.path.join(ROOT, "experiments", "e5_results.json"), "w"), indent=1)
