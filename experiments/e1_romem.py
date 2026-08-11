# -*- coding: utf-8 -*-
"""Add RoMem-style continuous phase rotation as a sixth arm.

RoMem (Tencent, arXiv 2604.11544) rotates embeddings by an angle derived from a
time scalar, with a LEARNABLE frequency base:

    inv_freq = 1 / base ** freq_indices        # base is nn.Parameter, init 10000
    theta    = t * inv_freq
    h_rot    = rotate(h, theta)

Two properties matter here and both differ from Q-RAG's rho_t:

  1. `t` stays CONTINUOUS. There is no int32 truncation, so the 19-slot collapse
     that the closed form describes does not apply. If anything defeats the
     collision, this should.
  2. `_theta` takes ONE time scalar. The mechanism is single-clock by
     construction: a learnable frequency for one axis, not two axes.

So this arm asks a sharp question: does a continuous, learnable-frequency phase
encoding escape the as-of failure, or is the failure about the NUMBER of clocks
rather than the resolution of one clock?

Arms added:
  romem-event    continuous phase on event time only     (what RoMem does today)
  romem-avail    continuous phase on availability only   (sanity: should solve it)
  romem-dual     two frequency bands, event + availability

Days are used as the time scalar, normalised to a 364-day period so the base
frequency matches the lattice measured in E2/dualclock_audit.
"""
import json
import os
from datetime import date

import numpy as np
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = "/root/tc"
N_PAIRS = int(os.environ.get("N_PAIRS", 1500))
L, SEED, RED = 200, 0, 0.6249
rng = np.random.default_rng(SEED)
D = lambda s: date(*map(int, s.split("-")))
EPOCH = date(2000, 1, 1)

C = {}
for line in open(os.path.join(ROOT, "data/chunks.jsonl"), encoding="utf-8"):
    c = json.loads(line)
    C[c["id"]] = c
Q = [json.loads(l) for l in open(os.path.join(ROOT, "data/queries.jsonl"), encoding="utf-8")]
sel = [Q[i] for i in rng.choice(len(Q), N_PAIRS, replace=False)]
by_tick = {}
for c in C.values():
    by_tick.setdefault(c["ticker"], []).append(c)

INST = []
for q in sel:
    f = rng.random() < 0.5
    a, b = (q["distractor_id"], q["gold_id"]) if f else (q["gold_id"], q["distractor_id"])
    INST.append({"a": a, "b": b, "y": 0 if f else 1, "concept": q["concept"]})
y = np.array([i["y"] for i in INST])
grp = np.array([i["concept"] for i in INST])
need = sorted({i["a"] for i in INST} | {i["b"] for i in INST})
print("instances %d   chunks %d   balance %.3f" % (len(INST), len(need), y.mean()), flush=True)

from transformers import AutoTokenizer, AutoModel
MODEL = "/root/tc/qrag_action_encoder"
tok = AutoTokenizer.from_pretrained(MODEL)
mdl = AutoModel.from_pretrained(MODEL).cuda().eval().half()
emb, bs = {}, 512
for i in range(0, len(need), bs):
    texts = [C[k]["text"] for k in need[i:i + bs]]
    b = tok(texts, padding=True, truncation=True, max_length=64, return_tensors="pt").to("cuda")
    with torch.no_grad():
        h = mdl(**b).last_hidden_state
        m = b["attention_mask"].unsqueeze(-1).half()
        e = torch.nn.functional.normalize((h * m).sum(1) / m.sum(1), dim=-1)
    for k, v in zip(need[i:i + bs], e.float().cpu().numpy()):
        emb[k] = v
DIM = len(emb[need[0]])
print("encoded, dim=%d" % DIM, flush=True)


def days(s):
    return (D(s) - EPOCH).days


def romem_rotate(vec, t_days, base=10000.0, period=364.0):
    """RoMem's rotation: theta = t * inv_freq, inv_freq = 1/base**idx.
    t is continuous — no int32 truncation anywhere."""
    d = vec.shape[-1]
    half = d // 2
    idx = np.arange(half, dtype=np.float64) / half
    inv = 1.0 / (base ** idx)
    theta = (t_days / period) * inv
    cos, sin = np.cos(theta), np.sin(theta)
    x1, x2 = vec[:half], vec[half:2 * half]
    return np.concatenate([x1 * cos - x2 * sin, x1 * sin + x2 * cos])


def build(arm):
    X = np.zeros((len(INST), DIM), dtype=np.float32)
    for r, inst in enumerate(INST):
        ca, cb = C[inst["a"]], C[inst["b"]]
        ea, eb = emb[inst["a"]], emb[inst["b"]]
        if arm == "romem-event":
            va = romem_rotate(ea, days(ca["event_time"]))
            vb = romem_rotate(eb, days(cb["event_time"]))
        elif arm == "romem-avail":
            va = romem_rotate(ea, days(ca["avail_time"]))
            vb = romem_rotate(eb, days(cb["avail_time"]))
        else:                                   # romem-dual
            h = (DIM // 2) - ((DIM // 2) % 2)
            va = np.concatenate([romem_rotate(ea[:h], days(ca["event_time"])),
                                 romem_rotate(ea[h:2 * h], days(ca["avail_time"]))])
            vb = np.concatenate([romem_rotate(eb[:h], days(cb["event_time"])),
                                 romem_rotate(eb[h:2 * h], days(cb["avail_time"]))])
        n = min(len(va), DIM)
        X[r, :n] = (va - vb)[:n]
    return np.nan_to_num(X)


print("\n" + "=" * 66)
print("RoMem-style continuous phase   red line %.4f   chance 0.5000" % RED)
print("=" * 66)
res = {}
for arm in ("romem-event", "romem-avail", "romem-dual"):
    X = build(arm)
    pipe = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, C=0.1))
    s = cross_val_score(pipe, X, y, cv=GroupKFold(5), groups=grp, n_jobs=5)
    res[arm] = s.mean()
    flag = "  <-- ABOVE RED LINE" if s.mean() > RED and arm != "romem-avail" else ""
    print("  %-14s %.4f (+/- %.4f)%s" % (arm, s.mean(), s.std(), flag), flush=True)
json.dump(res, open(os.path.join(ROOT, "romem_results.json"), "w"), indent=1)
print("\nwritten to romem_results.json")
