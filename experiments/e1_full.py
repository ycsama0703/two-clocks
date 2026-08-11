# -*- coding: utf-8 -*-
"""E1 full — do multiple retrieval systems all fail on the as-of axis?

The smoke run used one encoder, one ordering, one pool size, and folded
"absolute" into a pool index. This version:

  encoders   BM25 (lexical) / GTE-base / E5-base / gte-multilingual-base
             (the last is Q-RAG's own backbone, so its geometry is the one
              Q-RAG's rho_t was trained on top of)
  ordering   by event time  AND  by filing time
  time input no-time / relative-only / absolute-event / absolute-avail / dual-clock
  pool       L = 200
  probe      logistic on the A-vs-B difference, GroupKFold by concept

`absolute-avail` is NOT a fair baseline: ordering the pool by availability and
then handing over the absolute index is equivalent to revealing the label. It is
included as a sanity ceiling — if it does NOT approach 1.0, the harness is broken.

Read every number against the pre-registered red line 0.6249 (value-channel
ceiling, GroupKFold by concept, measured on this same v3 corpus). Anything above
it is a leak to investigate, not a result to celebrate.
"""
import json
import os
import sys
import time

import numpy as np
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = "/root/tc"
N_PAIRS = int(os.environ.get("N_PAIRS", 1500))
L = 200
SEED = 0
RED_LINE = 0.6249
rng = np.random.default_rng(SEED)
DEV = "cuda"

ENCODERS = [
    ("bm25", None),
    ("gte-base", "thenlper/gte-base"),
    ("e5-base", "intfloat/e5-base-v2"),
    ("gte-multilingual", "Alibaba-NLP/gte-multilingual-base"),
    ("qrag-babilong-qa3", "/root/tc/qrag_action_encoder"),
]
ARMS = ["no-time", "relative-only", "absolute-event", "absolute-avail", "dual-clock"]
ORDERINGS = [("event_time", "by event"), ("avail_time", "by filing")]

# ---------------------------------------------------------------- data
C = {}
with open(os.path.join(ROOT, "data/chunks.jsonl"), encoding="utf-8") as fh:
    for line in fh:
        c = json.loads(line)
        C[c["id"]] = c
Q = [json.loads(l) for l in open(os.path.join(ROOT, "data/queries.jsonl"), encoding="utf-8")]
sel = [Q[i] for i in rng.choice(len(Q), N_PAIRS, replace=False)]
by_tick = {}
for c in C.values():
    by_tick.setdefault(c["ticker"], []).append(c)
print("corpus %d chunks / %d queries; sampling %d pairs" % (len(C), len(Q), len(sel)), flush=True)

# Fix the pool, the A/B order and the filler ONCE, so every encoder and arm sees
# exactly the same instances. Otherwise differences between rows could come from
# resampling rather than from the representation.
INST = []
for q in sel:
    f = rng.random() < 0.5
    a, b = (q["distractor_id"], q["gold_id"]) if f else (q["gold_id"], q["distractor_id"])
    pool = [c for c in by_tick[q["ticker"]] if c["id"] not in (a, b)]
    if len(pool) > L - 2:
        pool = [pool[i] for i in rng.choice(len(pool), L - 2, replace=False)]
    INST.append({"a": a, "b": b, "y": 0 if f else 1, "concept": q["concept"],
                 "as_of": q["as_of"], "pool": [c["id"] for c in pool]})
print("instances fixed: %d (pool L=%d)" % (len(INST), L), flush=True)

need = sorted({i["a"] for i in INST} | {i["b"] for i in INST})
y = np.array([i["y"] for i in INST])
grp = np.array([i["concept"] for i in INST])
print("chunks to encode: %d   label balance %.3f" % (len(need), y.mean()), flush=True)


# ---------------------------------------------------------------- position
def relative_positions(n, step_size=20):
    """Verbatim port of Q-RAG envs/text_env.py:RelativePositionProcessor."""
    mv = int(0.9 * step_size)
    return np.linspace(0, mv, n).astype(np.float32)


def rope_freqs(dim, pos, theta=10000.0):
    """RoPE applied the way Q-RAG's PositionalRotaryEmbedding does: positions are
    truncated to int32 to index a cached table, which is what collapses a segment
    into at most 19 distinguishable slots."""
    half = dim // 2
    inv = theta ** (-np.arange(0, half, dtype=np.float64) * 2.0 / half)
    ang = np.int32(pos)[:, None] * inv[None, :]
    return np.cos(ang), np.sin(ang)


def apply_rope(vec, pos):
    """Rotate the largest even prefix; pass any odd leftover dimension through.

    BM25 feature width equals the vocabulary size and can be odd, in which case
    the two halves differ by one and the broadcast fails. One unrotated
    dimension carries no positional information, so the comparison stays fair.
    """
    d = vec.shape[-1]
    de = d - (d % 2)
    half = de // 2
    cos, sin = rope_freqs(de, pos)
    x1, x2 = vec[:, :half], vec[:, half:de]
    rot = np.concatenate([x1 * cos - x2 * sin, x1 * sin + x2 * cos], axis=-1)
    if de == d:
        return rot
    return np.concatenate([rot, vec[:, de:]], axis=-1)


# ---------------------------------------------------------------- encoders
def encode_dense(model_name):
    from transformers import AutoTokenizer, AutoModel
    tok = AutoTokenizer.from_pretrained(model_name)
    mdl = AutoModel.from_pretrained(model_name, trust_remote_code=True).to(DEV).eval().half()
    out, bs = [], 512
    t0 = time.time()
    for i in range(0, len(need), bs):
        texts = [C[k]["text"] for k in need[i:i + bs]]
        b = tok(texts, padding=True, truncation=True, max_length=64, return_tensors="pt").to(DEV)
        with torch.no_grad():
            h = mdl(**b).last_hidden_state
            m = b["attention_mask"].unsqueeze(-1).half()
            e = (h * m).sum(1) / m.sum(1)
            e = torch.nn.functional.normalize(e, dim=-1)
        out.append(e.float().cpu().numpy())
    print("    encoded %d in %.1fs" % (len(need), time.time() - t0), flush=True)
    return dict(zip(need, np.concatenate(out)))


def encode_bm25():
    """A lexical vector per chunk: BM25 scores against a shared vocabulary.
    Gives the same interface as a dense encoder so the arms are comparable."""
    from rank_bm25 import BM25Okapi
    import re
    toks = {k: re.findall(r"[a-z0-9]+", C[k]["text"].lower()) for k in need}
    vocab = sorted({t for v in toks.values() for t in v})
    vi = {t: j for j, t in enumerate(vocab)}
    bm = BM25Okapi([toks[k] for k in need])
    idf = np.array([bm.idf.get(t, 0.0) for t in vocab], dtype=np.float32)
    out = {}
    for k in need:
        v = np.zeros(len(vocab), dtype=np.float32)
        for t in toks[k]:
            v[vi[t]] += 1.0
        v *= idf
        n = np.linalg.norm(v)
        out[k] = v / n if n > 0 else v
    print("    bm25 vocab %d" % len(vocab), flush=True)
    return out


# ---------------------------------------------------------------- features
def build(emb, order_key, arm):
    dim = len(next(iter(emb.values())))
    X = np.zeros((len(INST), dim), dtype=np.float32)
    for r, inst in enumerate(INST):
        ea, eb = emb[inst["a"]][None, :], emb[inst["b"]][None, :]
        if arm == "no-time":
            X[r] = (ea - eb)[0]
            continue
        items = [C[i] for i in inst["pool"]] + [C[inst["a"]], C[inst["b"]]]
        idx = rng.permutation(len(items))          # neutral tie-break
        items = [items[i] for i in idx]
        items.sort(key=lambda c: c[order_key])
        n = len(items)
        ia = next(i for i, c in enumerate(items) if c["id"] == inst["a"])
        ib = next(i for i, c in enumerate(items) if c["id"] == inst["b"])
        rho = relative_positions(n)
        if arm == "relative-only":
            pa, pb = rho[ia], rho[ib]
        elif arm == "absolute-event":
            o = np.argsort(np.argsort([c["event_time"] for c in items]))
            pa, pb = float(o[ia]), float(o[ib])
        elif arm == "absolute-avail":
            o = np.argsort(np.argsort([c["avail_time"] for c in items]))
            pa, pb = float(o[ia]), float(o[ib])
        else:                                       # dual-clock
            oe = np.argsort(np.argsort([c["event_time"] for c in items]))
            oa = np.argsort(np.argsort([c["avail_time"] for c in items]))
            re_, ra_ = rho[oe], rho[oa]
            h = (dim // 2) - ((dim // 2) % 2)   # keep both halves even
            va = np.concatenate([apply_rope(ea[:, :h], np.array([re_[ia]]))[0],
                                 apply_rope(ea[:, h:], np.array([ra_[ia]]))[0]])
            vb = np.concatenate([apply_rope(eb[:, :h], np.array([re_[ib]]))[0],
                                 apply_rope(eb[:, h:], np.array([ra_[ib]]))[0]])
            X[r] = va - vb
            continue
        X[r] = (apply_rope(ea, np.array([pa])) - apply_rope(eb, np.array([pb])))[0]
    return np.nan_to_num(X)


def probe(X):
    pipe = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, C=0.1))
    s = cross_val_score(pipe, X, y, cv=GroupKFold(5), groups=grp, n_jobs=5)
    return s.mean(), s.std()


# ---------------------------------------------------------------- run
print("\n" + "=" * 78)
print("E1 FULL   red line %.4f   chance 0.5000   n=%d" % (RED_LINE, len(INST)))
print("=" * 78, flush=True)
results = {}
for ename, mname in ENCODERS:
    print("\n[%s]" % ename, flush=True)
    emb = encode_bm25() if mname is None else encode_dense(mname)
    for okey, oname in ORDERINGS:
        row = []
        for arm in ARMS:
            m, sd = probe(build(emb, okey, arm))
            results[(ename, oname, arm)] = (m, sd)
            flag = "  <-- ABOVE RED LINE" if m > RED_LINE and arm not in ("absolute-avail", "dual-clock") else ""
            row.append("%s=%.3f" % (arm, m))
            print("    %-10s %-16s %.4f (+/-%.4f)%s" % (oname, arm, m, sd, flag), flush=True)
    del emb

print("\n" + "=" * 78)
print("SUMMARY")
print("=" * 78)
print("%-18s %-10s " % ("encoder", "ordering") + " ".join("%-16s" % a for a in ARMS))
for ename, _ in ENCODERS:
    for _, oname in ORDERINGS:
        cells = " ".join("%-16.4f" % results[(ename, oname, a)][0] for a in ARMS)
        print("%-18s %-10s %s" % (ename, oname, cells))
json.dump({"|".join(k): v for k, v in results.items()},
          open(os.path.join(ROOT, "e1_full_results.json"), "w"), indent=1)
print("\nwritten to e1_full_results.json")
