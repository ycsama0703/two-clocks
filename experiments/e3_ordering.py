# -*- coding: utf-8 -*-
"""E3 — no single ordering supports both axes.

Task A (as-of)  : two candidates share event_time, differ in avail_time.
                  Pick the one available at as_of.
Task B (period) : two candidates share avail_time (same filing), differ in
                  event_time. Pick the one matching the queried period.

Task B data comes free from comparative reporting: a 10-K reports the current
period and prior periods in the SAME filing, so avail_time is identical while
event_time differs.

Prediction (the impossibility result, empirically):
    ordered by event time  -> A fails, B works
    ordered by filing time -> A works, B fails
    dual-clock             -> both work
"""
import json
import os
import sys
import glob
from collections import defaultdict

import numpy as np
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from position import relative_positions, make_rope, apply_positions  # noqa: E402

L, N, SEED = 200, 400, 0
rng = np.random.default_rng(SEED)
acc = json.load(open(os.path.join(ROOT, "data/acceptance.json")))

# ---- task A (existing corpus) ---------------------------------------------
C = {c["id"]: c for c in map(json.loads, open(os.path.join(ROOT, "data/chunks.jsonl"), encoding="utf-8"))}
QA = [json.loads(l) for l in open(os.path.join(ROOT, "data/queries.jsonl"), encoding="utf-8")]
QA = [QA[i] for i in rng.choice(len(QA), N, replace=False)]

# ---- task B (same filing, different period) --------------------------------
CF = os.path.expanduser("~/repairable-experience/data/edgar/companyfacts/*.json")
taskB, cidB = [], 0
CB = {}
for path in sorted(glob.glob(CF)):
    if len(taskB) >= N:
        break
    ticker = os.path.basename(path)[:-5]
    try:
        doc = json.load(open(path, encoding="utf-8"))
    except Exception:
        continue
    for _, concepts in (doc.get("facts") or {}).items():
        for concept, cdata in concepts.items():
            lab = (cdata.get("label") or concept).split(" (Deprecated")[0]
            for unit, entries in (cdata.get("units") or {}).items():
                byfiling = defaultdict(list)
                for e in entries:
                    an, end, v, f = e.get("accn"), e.get("end"), e.get("val"), e.get("filed")
                    if an and end and v is not None and f:
                        byfiling[an].append((end, v, acc.get(an, f)))
                for an, rows in byfiling.items():
                    if len(taskB) >= N:
                        break
                    ends = {}
                    for end, v, av in rows:
                        ends.setdefault(end, (v, av))
                    if len(ends) < 2:
                        continue
                    (e1, (v1, av1)), (e2, (v2, av2)) = sorted(ends.items())[:2]
                    if v1 == v2 or av1 != av2:
                        continue
                    d = max(abs(v1), abs(v2))
                    if d == 0 or abs(v2 - v1) / d < 0.01:
                        continue
                    ids = []
                    for end, v in ((e1, v1), (e2, v2)):
                        cidB += 1
                        i = "b%07d" % cidB
                        CB[i] = {"id": i, "text": "%s reported %s of %s %s for the period ended %s."
                                 % (ticker, lab, "{:,}".format(int(v)) if float(v).is_integer() else v, unit, end),
                                 "ticker": ticker, "concept": concept,
                                 "event_time": end, "avail_time": av1, "value": float(v)}
                        ids.append(i)
                    tgt = rng.integers(2)
                    taskB.append({"query": "What was %s's %s for the period ended %s?"
                                  % (ticker, lab, (e1, e2)[tgt]),
                                  "gold_id": ids[tgt], "distractor_id": ids[1 - tgt],
                                  "ticker": ticker, "concept": concept,
                                  "anchor": (e1, e2)[tgt]})
print("task A pairs: %d   task B pairs: %d" % (len(QA), len(taskB)))

# ---- encode ---------------------------------------------------------------
from transformers import AutoTokenizer, AutoModel  # noqa: E402
tok = AutoTokenizer.from_pretrained("thenlper/gte-base")
mdl = AutoModel.from_pretrained("thenlper/gte-base").eval()
DIM = mdl.config.hidden_size


@torch.no_grad()
def encode(texts, bs=64):
    out = []
    for i in range(0, len(texts), bs):
        b = tok(texts[i:i + bs], padding=True, truncation=True, max_length=64, return_tensors="pt")
        h = mdl(**b).last_hidden_state
        m = b["attention_mask"].unsqueeze(-1).float()
        out.append(torch.nn.functional.normalize((h * m).sum(1) / m.sum(1), dim=-1))
    return torch.cat(out)


ALL = {**C, **CB}
need = sorted({q["gold_id"] for q in QA + taskB} | {q["distractor_id"] for q in QA + taskB})
CACHE = os.path.join(ROOT, "experiments", "emb_cache_e3.npz")
if os.path.exists(CACHE):
    z = np.load(CACHE, allow_pickle=True)
    emb = {str(k): torch.tensor(v) for k, v in zip(z["ids"], z["vecs"])}
    if set(emb) != set(need):
        emb = None
else:
    emb = None
if emb is None:
    print("encoding %d chunks (CPU, a few minutes)" % len(need), flush=True)
    emb = dict(zip(need, encode([ALL[i]["text"] for i in need])))
    np.savez(CACHE, ids=np.array(need), vecs=np.stack([emb[i].numpy() for i in need]))
print("embeddings ready: %d" % len(emb))

rope, rope_half = make_rope(DIM), make_rope(DIM // 2)
by_tick = defaultdict(list)
for c in ALL.values():
    by_tick[c["ticker"]].append(c)


def run(queries, order_key, arm, anchor_key):
    """Candidate positions are given RELATIVE to the query's time anchor."""
    X, y, g = [], [], []
    for q in queries:
        a, b = q["gold_id"], q["distractor_id"]
        f = rng.random() < 0.5
        if f:
            a, b = b, a
        pool = [c for c in by_tick[q["ticker"]] if c["id"] not in (a, b)]
        if len(pool) > L - 2:
            pool = [pool[i] for i in rng.choice(len(pool), L - 2, replace=False)]
        items = pool + [ALL[a], ALL[b]]
        rng.shuffle(items)
        items.sort(key=lambda c: c[order_key])
        n = len(items)
        ia = next(i for i, c in enumerate(items) if c["id"] == a)
        ib = next(i for i, c in enumerate(items) if c["id"] == b)
        anchor = q[anchor_key]
        ea, eb = emb[a].unsqueeze(0), emb[b].unsqueeze(0)
        base = (ea - eb).squeeze(0).numpy()

        def axis(key):
            order = np.argsort(np.argsort([c[key] for c in items]))
            rho = relative_positions(n)
            r = rho[order]                      # r[i] = position of item i
            iq = min(sum(1 for c in items if c[key] <= anchor), n - 1)
            return r, rho[iq]                   # iq is the anchor's RANK, so rho[iq]

        def pair(r, rq):
            da, db = float(r[ia] - rq), float(r[ib] - rq)
            # sign terms for A-style rules, distance terms for B-style rules
            return [da, db, abs(da) - abs(db)]

        if arm == "relative-only":
            r, rq = axis(order_key)
            pos = np.array(pair(r, rq), dtype=np.float64)
        else:
            re, rqe = axis("event_time")
            ra, rqa = axis("avail_time")
            pos = np.array(pair(re, rqe) + pair(ra, rqa), dtype=np.float64)
        X.append(np.concatenate([base, pos]))
        y.append(0 if f else 1)
        g.append(q["concept"])
    X = np.nan_to_num(np.array(X, dtype=np.float64))
    pipe = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, C=0.1))
    return cross_val_score(pipe, X, np.array(y), cv=GroupKFold(5), groups=np.array(g)).mean()


print()
print("=" * 66)
print("E3   no single ordering supports both axes")
print("=" * 66)
print("%-16s %-18s %10s %10s" % ("arm", "ordering", "task A", "task B"))
for arm in ("relative-only", "dual-clock"):
    for key, nm in (("event_time", "by event time"), ("avail_time", "by filing time")):
        a = run(QA, key, arm, "as_of")
        b = run(taskB, key, arm, "anchor")
        print("%-16s %-18s %10.3f %10.3f" % (arm, nm, a, b))
print()
print("chance = 0.500;  A = as-of eligibility,  B = period matching")
