# -*- coding: utf-8 -*-
"""Minimal go/no-go: does `relative-only` land inside the pre-registered [0.50, 0.62]?

Setup (fixed for this run; the full E1 sweeps these):
    encoder    GTE-base (Q-RAG's main config uses gte)
    pool       L = 200, ordered BY EVENT TIME (the natural way to organise filings)
    pairs      500
    probe      logistic on the A-vs-B embedding difference, GroupKFold by concept

Four time inputs:
    no-time        text embedding only
    relative-only  + Q-RAG rho_t through its RoPE  (the arm under test)
    absolute       + index in the pool through the same RoPE
    dual-clock     embedding split in half: event rho on one half,
                   availability rho on the other

Read the result against the red line, not against each other:
    relative-only > 0.62  =>  UNDISCOVERED LEAK, stop and investigate
    relative-only ~ 0.50-0.62  =>  positional channel carries no as-of information
"""
import json
import os
import sys

import numpy as np
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from position import relative_positions, make_rope, apply_positions  # noqa: E402

L, N_PAIRS, SEED = 200, 500, 0
rng = np.random.default_rng(SEED)

C = {c["id"]: c for c in map(json.loads, open(os.path.join(ROOT, "data/chunks.jsonl"), encoding="utf-8"))}
Q = [json.loads(l) for l in open(os.path.join(ROOT, "data/queries.jsonl"), encoding="utf-8")]
sel = [Q[i] for i in rng.choice(len(Q), N_PAIRS, replace=False)]
print("pairs: %d   pool L=%d   ordering: by event time" % (len(sel), L))

# ---- encode ---------------------------------------------------------------
from transformers import AutoTokenizer, AutoModel  # noqa: E402

MODEL = "thenlper/gte-base"
tok = AutoTokenizer.from_pretrained(MODEL)
mdl = AutoModel.from_pretrained(MODEL).eval()
DIM = mdl.config.hidden_size
print("encoder: %s  dim=%d  (CPU)" % (MODEL, DIM))


@torch.no_grad()
def encode(texts, bs=64):
    out = []
    for i in range(0, len(texts), bs):
        b = tok(texts[i:i + bs], padding=True, truncation=True, max_length=64,
                return_tensors="pt")
        h = mdl(**b).last_hidden_state
        m = b["attention_mask"].unsqueeze(-1).float()
        e = (h * m).sum(1) / m.sum(1)
        out.append(torch.nn.functional.normalize(e, dim=-1))
        if i % 640 == 0:
            print("   %d/%d" % (i, len(texts)), flush=True)
    return torch.cat(out)


ids = sorted({q["gold_id"] for q in sel} | {q["distractor_id"] for q in sel})
CACHE = os.path.join(ROOT, "experiments", "emb_cache.npz")
if os.path.exists(CACHE):
    z = np.load(CACHE, allow_pickle=True)
    emb = {str(k): torch.tensor(v) for k, v in zip(z["ids"], z["vecs"])}
    if set(emb) == set(ids):
        print("embeddings from cache: %d" % len(emb))
    else:
        emb = None
else:
    emb = None
if emb is None:
    emb = dict(zip(ids, encode([C[i]["text"] for i in ids])))
    np.savez(CACHE, ids=np.array(ids), vecs=np.stack([emb[i].numpy() for i in ids]))
    print("encoded %d chunks (cached)" % len(emb))

# ---- positions ------------------------------------------------------------
# Pool ordered by event time. Gold and distractor share an event time, so they
# are adjacent; the remaining L-2 slots are filler from the same ticker.
rope = make_rope(DIM)
rope_half = make_rope(DIM // 2)   # rotate_queries_or_keys halves again internally
by_ticker = {}
for c in C.values():
    by_ticker.setdefault(c["ticker"], []).append(c)

feats = {k: [] for k in ("no-time", "relative-only", "absolute", "dual-clock")}
y, grp = [], []
flip = rng.random(len(sel)) < 0.5

for q, f in zip(sel, flip):
    a, b = (q["distractor_id"], q["gold_id"]) if f else (q["gold_id"], q["distractor_id"])
    pool = [c for c in by_ticker[q["ticker"]] if c["id"] not in (a, b)]
    if len(pool) > L - 2:
        pool = [pool[i] for i in rng.choice(len(pool), L - 2, replace=False)]
    items = pool + [C[a], C[b]]
    # Tie-break NEUTRALLY inside an event_time. Using avail_time here leaked the
    # answer outright (gold always ahead of distractor -> relative-only hit 0.712,
    # above the 0.62 red line). `id` leaks too: ids are assigned in generation
    # order, gold before distractor. Shuffle first, then stable-sort.
    rng.shuffle(items)
    items.sort(key=lambda c: c["event_time"])
    n = len(items)
    ia = next(i for i, c in enumerate(items) if c["id"] == a)
    ib = next(i for i, c in enumerate(items) if c["id"] == b)

    rho = relative_positions(n)                       # Q-RAG rho_t, no discovered evidence
    av_order = np.argsort(np.argsort([c["avail_time"] for c in items]))
    rho_av = relative_positions(n)[av_order]          # same scheme on the availability axis

    ea, eb = emb[a].unsqueeze(0), emb[b].unsqueeze(0)
    feats["no-time"].append((ea - eb).squeeze(0).numpy())

    pa = apply_positions(rope, ea, np.array([rho[ia]], dtype=np.float32))
    pb = apply_positions(rope, eb, np.array([rho[ib]], dtype=np.float32))
    feats["relative-only"].append((pa - pb).squeeze(0).numpy())

    aa = apply_positions(rope, ea, np.array([float(ia)], dtype=np.float32))
    ab = apply_positions(rope, eb, np.array([float(ib)], dtype=np.float32))
    feats["absolute"].append((aa - ab).squeeze(0).numpy())

    H = DIM // 2
    da = np.concatenate([
        apply_positions(rope_half, ea[:, :H], np.array([rho[ia]], dtype=np.float32)).squeeze(0).numpy(),
        apply_positions(rope_half, ea[:, H:], np.array([rho_av[ia]], dtype=np.float32)).squeeze(0).numpy()])
    db = np.concatenate([
        apply_positions(rope_half, eb[:, :H], np.array([rho[ib]], dtype=np.float32)).squeeze(0).numpy(),
        apply_positions(rope_half, eb[:, H:], np.array([rho_av[ib]], dtype=np.float32)).squeeze(0).numpy()])
    feats["dual-clock"].append(da - db)

    y.append(0 if f else 1)
    grp.append(q["concept"])

y = np.array(y)
grp = np.array(grp)
print("label balance: %.3f" % y.mean())

print()
print("=" * 62)
print("E1 SMOKE   pre-registered: relative-only in [0.50, 0.62]")
print("=" * 62)
res = {}
for k in ("no-time", "relative-only", "absolute", "dual-clock"):
    X = np.nan_to_num(np.array(feats[k], dtype=np.float64))
    pipe = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, C=0.1))
    s = cross_val_score(pipe, X, y, cv=GroupKFold(5), groups=grp)
    res[k] = s.mean()
    print("  %-16s %.4f  (+/- %.4f)   dim=%d" % (k, s.mean(), s.std(), X.shape[1]))

r = res["relative-only"]
print()
print("  red line (ceiling, GroupKFold by concept) : 0.6128")
print("  chance                                    : 0.5000")
if r > 0.62:
    print("  VERDICT: relative-only = %.4f > 0.62  -> UNDISCOVERED LEAK, stop." % r)
elif r < 0.50 - 0.02:
    print("  VERDICT: relative-only = %.4f below chance -- inspect labelling." % r)
else:
    print("  VERDICT: relative-only = %.4f INSIDE [0.50, 0.62] as pre-registered." % r)
