# -*- coding: utf-8 -*-
"""E6 — abstention: can the collision predicate tell us when NOT to answer?

Four attempts to repair the representation have failed (E3/E5 capacity, the
frequency-design angle to the literature, E4 extrapolation). This one accepts
that as-of eligibility is not recoverable from a single-axis code and asks a
different question: can a system at least KNOW when it cannot answer?

The collision predicate is deterministic and model-free:

    floor(rho_a) == floor(rho_b)   with rho from Q-RAG's relative_positions

So it can be evaluated BEFORE any model runs, as a gate on the retrieval result.

Pre-registered reading, written before the run:

    accuracy on non-colliding >> accuracy on colliding
        -> the predicate has selective power; abstention is a real mechanism,
           and the closed form gives the abstention-rate / residual-error curve
    the two are comparable
        -> the predicate does not predict failure; this angle closes like the
           other four

Also reported: the risk-coverage curve. For a deployment that must avoid
look-ahead bias, what residual error remains after abstaining on x% of queries.
"""
import json
import os
from collections import defaultdict

import numpy as np
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N_PAIRS = int(os.environ.get("N_PAIRS", 2000))
L, SEED = 200, 0
rng = np.random.default_rng(SEED)

C = {}
for line in open(os.path.join(ROOT, "data/chunks.jsonl"), encoding="utf-8"):
    c = json.loads(line)
    C[c["id"]] = c
Q = [json.loads(l) for l in open(os.path.join(ROOT, "data/queries.jsonl"), encoding="utf-8")]
by_tick = defaultdict(list)
for c in C.values():
    by_tick[c["ticker"]].append(c)

sel = [Q[i] for i in rng.choice(len(Q), N_PAIRS, replace=False)]
INST = []
for q in sel:
    f = rng.random() < 0.5
    a, b = (q["distractor_id"], q["gold_id"]) if f else (q["gold_id"], q["distractor_id"])
    INST.append({"a": a, "b": b, "y": 0 if f else 1,
                 "concept": q["concept"], "ticker": q["ticker"]})
y = np.array([i["y"] for i in INST])
grp = np.array([i["concept"] for i in INST])
need = sorted({i["a"] for i in INST} | {i["b"] for i in INST})
print("instances %d   chunks %d" % (len(INST), len(need)), flush=True)

from transformers import AutoTokenizer, AutoModel
tok = AutoTokenizer.from_pretrained("thenlper/gte-base")
mdl = AutoModel.from_pretrained("thenlper/gte-base").eval()
CACHE = os.path.join(ROOT, "experiments", "emb_cache_e6.npz")
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
print("embeddings dim=%d" % DIM, flush=True)


def relpos(n, step=20):
    return np.linspace(0, int(0.9 * step), n).astype(np.float32)


def rope(vec, pos, theta=10000.0):
    d = vec.shape[-1]
    half = d // 2
    inv = theta ** (-np.arange(half, dtype=np.float64) * 2.0 / half)
    ang = np.int32(pos) * inv
    cos, sin = np.cos(ang), np.sin(ang)
    x1, x2 = vec[:half], vec[half:2 * half]
    return np.concatenate([x1 * cos - x2 * sin, x1 * sin + x2 * cos])


# Build features under relative-only (ordered by event time) and, for every
# instance, record the deterministic collision predicate and delta_i.
X = np.zeros((len(INST), DIM), dtype=np.float32)
collide = np.zeros(len(INST), dtype=bool)
delta_i = np.zeros(len(INST), dtype=int)
for i, inst in enumerate(INST):
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
    qa, qb = np.int32(r[ia]), np.int32(r[ib])
    collide[i] = (qa == qb)
    delta_i[i] = abs(ia - ib)
    X[i] = rope(ea, r[ia]) - rope(eb, r[ib])

print("\ncollision rate: %.4f   (closed form 1-18/(L-1) at delta=1: %.4f)"
      % (collide.mean(), max(0.0, 1 - 18.0 / (L - 1))), flush=True)
print("median delta_i %d" % np.median(delta_i))

# Out-of-fold predictions so accuracy is measured on unseen instances
pred = np.zeros(len(INST), dtype=int)
for tr, te in GroupKFold(5).split(X, y, groups=grp):
    pipe = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, C=0.1))
    pipe.fit(X[tr], y[tr])
    pred[te] = pipe.predict(X[te])
correct = (pred == y)

print("\n" + "=" * 66)
print("E6  does the collision predicate select the failures?")
print("=" * 66)
for name, mask in (("colliding", collide), ("non-colliding", ~collide)):
    if mask.sum() == 0:
        print("  %-16s n=0" % name)
        continue
    print("  %-16s n=%-6d accuracy %.4f" % (name, mask.sum(), correct[mask].mean()))
gap = correct[~collide].mean() - correct[collide].mean() if collide.any() and (~collide).any() else float("nan")
print("  selective gap  %+.4f" % gap)

print("\n  by delta_i:")
for lo, hi in ((1, 1), (2, 3), (4, 8), (9, 10 ** 6)):
    m = (delta_i >= lo) & (delta_i <= hi)
    if m.sum() > 20:
        print("    delta_i %-6s n=%-6d collide %.2f  accuracy %.4f"
              % ("%d-%d" % (lo, hi) if lo != hi else str(lo), m.sum(),
                 collide[m].mean(), correct[m].mean()))

print("\n  risk-coverage (abstain on colliding first, then by smallest delta_i):")
order = np.lexsort((delta_i, ~collide))     # colliding first, then small delta_i
for frac in (0.0, 0.2, 0.4, 0.6, 0.7, 0.8):
    k = int(len(INST) * frac)
    keep = np.ones(len(INST), dtype=bool)
    keep[order[:k]] = False
    if keep.sum() > 20:
        print("    abstain %4.0f%%  answered n=%-6d accuracy %.4f"
              % (frac * 100, keep.sum(), correct[keep].mean()))

json.dump({"collision_rate": float(collide.mean()),
           "acc_colliding": float(correct[collide].mean()) if collide.any() else None,
           "acc_non_colliding": float(correct[~collide].mean()) if (~collide).any() else None,
           "selective_gap": float(gap)},
          open(os.path.join(ROOT, "experiments", "e6_results.json"), "w"), indent=1)
print("\nwritten to e6_results.json")
