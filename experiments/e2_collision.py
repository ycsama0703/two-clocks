# -*- coding: utf-8 -*-
"""E2 — does the closed form predict the collision rate on the real corpus?

Not a model experiment. The closed form predicts a property of the POSITION
ENCODING, so measure that directly:

    P_collide(delta_i) = max(0, 1 - 18*delta_i/(L-1))

For each query we build a pool of L chunks from the same ticker, order it by
event time with a neutral tie-break, compute Q-RAG's rho_t, truncate to int32
exactly as its RoPE does, and ask whether gold and distractor land in the same
bin. delta_i is measured, not assumed -- other chunks sharing the event time can
fall between them after the shuffle.

Task accuracy is NOT the quantity here: gold and distractor share an event time
exactly, so under a neutral tie-break their order is random whether they collide
or not. Accuracy is flat in L by construction; the collision rate is not.
"""
import json
import os
import sys
from collections import Counter

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from position import relative_positions, collision_rate  # noqa: E402

N_PAIRS, SEED = 500, 0
LS = (50, 200, 1000)
rng = np.random.default_rng(SEED)

C = {c["id"]: c for c in map(json.loads, open(os.path.join(ROOT, "data/chunks.jsonl"), encoding="utf-8"))}
Q = [json.loads(l) for l in open(os.path.join(ROOT, "data/queries.jsonl"), encoding="utf-8")]
by_ticker = {}
for c in C.values():
    by_ticker.setdefault(c["ticker"], []).append(c)

sel = [Q[i] for i in rng.choice(len(Q), N_PAIRS, replace=False)]
print("pairs: %d   ordering: by event time, neutral tie-break" % len(sel))
print()
print("%6s %8s %14s %16s %14s %10s" %
      ("L", "usable", "median delta_i", "predicted(d=1)", "predicted(d^)", "measured"))

for L in LS:
    hits, preds1, predsd, deltas = [], [], [], []
    for q in sel:
        pool = [c for c in by_ticker[q["ticker"]]
                if c["id"] not in (q["gold_id"], q["distractor_id"])]
        if len(pool) < L - 2:
            continue
        pool = [pool[i] for i in rng.choice(len(pool), L - 2, replace=False)]
        items = pool + [C[q["gold_id"]], C[q["distractor_id"]]]
        rng.shuffle(items)
        items.sort(key=lambda c: c["event_time"])
        n = len(items)
        ig = next(i for i, c in enumerate(items) if c["id"] == q["gold_id"])
        idd = next(i for i, c in enumerate(items) if c["id"] == q["distractor_id"])
        rho = relative_positions(n).astype(np.int32)      # == t.type(torch.int32)
        d = abs(ig - idd)
        deltas.append(d)
        hits.append(int(rho[ig] == rho[idd]))
        preds1.append(collision_rate(n, 1))
        predsd.append(collision_rate(n, d))
    if not hits:
        print("%6d %8s  (no ticker has enough chunks)" % (L, "-"))
        continue
    print("%6d %8d %14.1f %16.3f %14.3f %10.3f"
          % (L, len(hits), np.median(deltas), np.mean(preds1), np.mean(predsd), np.mean(hits)))

print()
print("delta_i distribution at L=200 (how many chunks fall between the pair):")
pool_ok = 0
dd = Counter()
for q in sel:
    pool = [c for c in by_ticker[q["ticker"]]
            if c["id"] not in (q["gold_id"], q["distractor_id"])]
    if len(pool) < 198:
        continue
    pool_ok += 1
    pool = [pool[i] for i in rng.choice(len(pool), 198, replace=False)]
    items = pool + [C[q["gold_id"]], C[q["distractor_id"]]]
    rng.shuffle(items)
    items.sort(key=lambda c: c["event_time"])
    ig = next(i for i, c in enumerate(items) if c["id"] == q["gold_id"])
    idd = next(i for i, c in enumerate(items) if c["id"] == q["distractor_id"])
    dd[abs(ig - idd)] += 1
for k in sorted(dd)[:8]:
    print("   delta_i=%-3d %4d  (%.1f%%)" % (k, dd[k], 100.0 * dd[k] / pool_ok))
print("   ...  max delta_i = %d" % max(dd))
