# -*- coding: utf-8 -*-
"""E4 — length extrapolation: does any single-axis code survive a larger pool?

This is the experiment that decides whether a method contribution exists at all.

Protocol. The probe is FITTED ONCE at L=200 and then applied unchanged at
L in {200, 500, 1000, 2000, 5000}. Refitting per L would measure in-distribution
fit, not extrapolation, and would answer a different question.

Pre-registered reading, written before running:
    absolute degrades and dual-clock holds  -> a method contribution exists, and
                                               the argument is "single-axis codes
                                               fail irrecoverably out of range"
    neither degrades                        -> no method contribution; write the
                                               benchmark + theory paper
    both degrade                            -> the second axis does not rescue
                                               extrapolation either; the problem
                                               is elsewhere

Why absolute is expected to degrade: its index range grows with L, so positions
at L=5000 lie far outside anything the probe saw at L=200. Phase-based codes are
periodic and in principle bounded, which is exactly Q-RAG's stated reason for
avoiding absolute positions.
"""
import json
import os
import sys
from datetime import date

import numpy as np
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

N_PAIRS = int(os.environ.get("N_PAIRS", 800))
LS = [200, 400, 700, 1000]   # >1000 leaves <10 companies: a different subset, not a bigger pool
FIT_L = 200
SEED = 0
rng = np.random.default_rng(SEED)
D = lambda s: date(*map(int, s.split("-")))

C = {}
for line in open(os.path.join(ROOT, "data/chunks.jsonl"), encoding="utf-8"):
    c = json.loads(line)
    C[c["id"]] = c
Q = [json.loads(l) for l in open(os.path.join(ROOT, "data/queries.jsonl"), encoding="utf-8")]
by_tick = {}
for c in C.values():
    by_tick.setdefault(c["ticker"], []).append(c)

# Only tickers with enough chunks to fill the largest pool, so the SAME instances
# are usable at every L. Otherwise the L=5000 row would silently be a different,
# easier subsample.
big = {t for t, v in by_tick.items() if len(v) >= max(LS) + 2}
cand = [q for q in Q if q["ticker"] in big]
print("tickers with >=%d chunks: %d   usable queries: %d" % (max(LS) + 2, len(big), len(cand)), flush=True)
if len(cand) < N_PAIRS:
    N_PAIRS = len(cand)
sel = [cand[i] for i in rng.choice(len(cand), N_PAIRS, replace=False)]

INST = []
for q in sel:
    f = rng.random() < 0.5
    a, b = (q["distractor_id"], q["gold_id"]) if f else (q["gold_id"], q["distractor_id"])
    INST.append({"a": a, "b": b, "y": 0 if f else 1,
                 "concept": q["concept"], "ticker": q["ticker"]})
y = np.array([i["y"] for i in INST])
grp = np.array([i["concept"] for i in INST])
need = sorted({i["a"] for i in INST} | {i["b"] for i in INST})
print("instances %d   chunks to encode %d   balance %.3f" % (len(INST), len(need), y.mean()), flush=True)

from transformers import AutoTokenizer, AutoModel
MODEL = "thenlper/gte-base"
tok = AutoTokenizer.from_pretrained(MODEL)
mdl = AutoModel.from_pretrained(MODEL).eval()
CACHE = os.path.join(ROOT, "experiments", "emb_cache_e4.npz")
if os.path.exists(CACHE):
    z = np.load(CACHE, allow_pickle=True)
    emb = {str(k): v for k, v in zip(z["ids"], z["vecs"])}
    if set(emb) != set(need):
        emb = None
else:
    emb = None
if emb is None:
    out, bs = [], 128
    for i in range(0, len(need), bs):
        b = tok([C[k]["text"] for k in need[i:i + bs]], padding=True, truncation=True,
                max_length=64, return_tensors="pt")
        with torch.no_grad():
            h = mdl(**b).last_hidden_state
            m = b["attention_mask"].unsqueeze(-1).float()
            e = torch.nn.functional.normalize((h * m).sum(1) / m.sum(1), dim=-1)
        out.append(e.numpy())
        if i % 1280 == 0:
            print("   encode %d/%d" % (i, len(need)), flush=True)
    emb = dict(zip(need, np.concatenate(out)))
    np.savez(CACHE, ids=np.array(need), vecs=np.stack([emb[k] for k in need]))
DIM = len(emb[need[0]])
print("embeddings ready, dim=%d" % DIM, flush=True)


def relative_positions(n, step=20):
    return np.linspace(0, int(0.9 * step), n).astype(np.float32)


def apply_rope(vec, pos, theta=10000.0):
    d = vec.shape[-1]
    de = d - d % 2
    half = de // 2
    inv = theta ** (-np.arange(half, dtype=np.float64) * 2.0 / half)
    ang = np.int32(pos) * inv
    cos, sin = np.cos(ang), np.sin(ang)
    x1, x2 = vec[:half], vec[half:de]
    rot = np.concatenate([x1 * cos - x2 * sin, x1 * sin + x2 * cos])
    return rot if de == d else np.concatenate([rot, vec[de:]])


def build(arm, L, seed):
    r = np.random.default_rng(seed)
    X = np.zeros((len(INST), DIM), dtype=np.float32)
    for i, inst in enumerate(INST):
        ea, eb = emb[inst["a"]], emb[inst["b"]]
        pool = [c for c in by_tick[inst["ticker"]] if c["id"] not in (inst["a"], inst["b"])]
        pool = [pool[j] for j in r.choice(len(pool), L - 2, replace=False)]
        items = pool + [C[inst["a"]], C[inst["b"]]]
        items = [items[j] for j in r.permutation(len(items))]
        items.sort(key=lambda c: c["event_time"])
        n = len(items)
        ia = next(j for j, c in enumerate(items) if c["id"] == inst["a"])
        ib = next(j for j, c in enumerate(items) if c["id"] == inst["b"])
        if arm == "relative-only":
            rho = relative_positions(n)
            pa, pb = rho[ia], rho[ib]
            X[i] = apply_rope(ea, pa) - apply_rope(eb, pb)
        elif arm == "absolute":
            o = np.argsort(np.argsort([c["event_time"] for c in items]))
            X[i] = apply_rope(ea, float(o[ia])) - apply_rope(eb, float(o[ib]))
        else:                                            # dual-clock
            rho = relative_positions(n)
            oe = np.argsort(np.argsort([c["event_time"] for c in items]))
            oa = np.argsort(np.argsort([c["avail_time"] for c in items]))
            re_, ra_ = rho[oe], rho[oa]
            h = (DIM // 2) - ((DIM // 2) % 2)
            va = np.concatenate([apply_rope(ea[:h], re_[ia]), apply_rope(ea[h:2 * h], ra_[ia])])
            vb = np.concatenate([apply_rope(eb[:h], re_[ib]), apply_rope(eb[h:2 * h], ra_[ib])])
            X[i, :len(va)] = va - vb
    return np.nan_to_num(X)


print("\n" + "=" * 74)
print("E4  probe FITTED ONLY AT L=%d, applied unchanged at larger L" % FIT_L)
print("=" * 74)
print("%-14s " % "arm" + " ".join("%9s" % ("L=%d" % L) for L in LS))
res = {}
for arm in ("relative-only", "absolute", "dual-clock"):
    Xfit = build(arm, FIT_L, seed=100)
    row = []
    gkf = GroupKFold(5)
    for L in LS:
        Xte = build(arm, L, seed=200 + L)
        accs = []
        for tr, te in gkf.split(Xfit, y, groups=grp):
            pipe = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, C=0.1))
            pipe.fit(Xfit[tr], y[tr])              # fit at L=200
            accs.append(pipe.score(Xte[te], y[te]))  # score at L
        row.append(float(np.mean(accs)))
        res[(arm, L)] = row[-1]
    print("%-14s " % arm + " ".join("%9.4f" % v for v in row), flush=True)

print()
print("degradation from L=%d to L=%d:" % (FIT_L, LS[-1]))
for arm in ("relative-only", "absolute", "dual-clock"):
    d = res[(arm, LS[-1])] - res[(arm, FIT_L)]
    print("  %-14s %+.4f" % (arm, d))
json.dump({"%s|%d" % k: v for k, v in res.items()},
          open(os.path.join(ROOT, "experiments", "e4_results.json"), "w"), indent=1)
print("\nwritten to e4_results.json")
