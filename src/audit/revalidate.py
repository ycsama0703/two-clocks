# -*- coding: utf-8 -*-
"""Re-run every number that depends on avail_time, after the v2 rebuild.

avail_time changed from filingDate to max(filingDate, acceptanceDate), so the
pre-registered ceiling, the Phase-0 items and the distribution parameters all
have to be re-measured on the new corpus. Nothing here is new methodology --
it is the same measurements, repeated on the rebuilt data.
"""
import json
import os
from collections import Counter
from datetime import date

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import cross_val_score, GroupKFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
import re

ROOT = os.path.expanduser("~/workspace/projects/bitemporal-bench/data")
rng = np.random.default_rng(0)
D = lambda s: date(*map(int, s.split("-")))

C = {c["id"]: c for c in map(json.loads, open(os.path.join(ROOT, "chunks.jsonl"), encoding="utf-8"))}
Q = [json.loads(l) for l in open(os.path.join(ROOT, "queries.jsonl"), encoding="utf-8")]
print("corpus: %d queries / %d chunks / %d tickers"
      % (len(Q), len(C), len({c["ticker"] for c in C.values()})))

flip = rng.random(len(Q)) < 0.5
A = [C[q["distractor_id"] if f else q["gold_id"]] for q, f in zip(Q, flip)]
B = [C[q["gold_id"] if f else q["distractor_id"]] for q, f in zip(Q, flip)]
y = (~flip).astype(int)
asof = [D(q["as_of"]) for q in Q]
grp = np.array([q["concept"] for q in Q])
tik = np.array([q["ticker"] for q in Q])
print("label balance: %.3f" % y.mean())


def tz(x):
    o = np.zeros(len(x))
    for i, v in enumerate(x):
        try:
            s = str(int(abs(v)))
        except Exception:
            continue
        o[i] = len(s) - len(s.rstrip("0"))
    return o


def dg(x):
    with np.errstate(divide="ignore"):
        return np.where(np.abs(x) > 0, np.log10(np.abs(x) + 1e-12), 0.0)


va = np.array([a["value"] for a in A])
vb = np.array([b["value"] for b in B])
X = np.nan_to_num(np.column_stack([
    dg(va) - dg(vb), np.abs(va) > np.abs(vb), tz(va) - tz(vb),
    (va > 0).astype(float) - (vb > 0).astype(float),
    (va == np.round(va)).astype(float) - (vb == np.round(vb)).astype(float),
    np.sign(va - vb), np.log1p(np.abs(va - vb)) - np.log1p(np.abs(va)),
    dg(va), dg(vb)]), nan=0.0, posinf=0.0, neginf=0.0)

gb = lambda: HistGradientBoostingClassifier(max_iter=300, random_state=0)
print()
print("=" * 68)
print("PRE-REGISTERED CEILING (value channel) -- the red line")
print("=" * 68)
for nm, g in (("GroupKFold by concept", grp), ("GroupKFold by ticker", tik)):
    s = cross_val_score(gb(), X, y, cv=GroupKFold(5), groups=g)
    print("  %-24s %.4f  (+/- %.4f)" % (nm, s.mean(), s.std()))

rel_A = np.array([(t - D(a["event_time"])).days for t, a in zip(asof, A)])
rel_B = np.array([(t - D(b["event_time"])).days for t, b in zip(asof, B)])
av_A = np.array([(t - D(a["avail_time"])).days for t, a in zip(asof, A)])
av_B = np.array([(t - D(b["avail_time"])).days for t, b in zip(asof, B)])
print()
print("=" * 68)
print("PHASE-0 [4] causal lever   [2] side channel   [6] learnable floor")
print("=" * 68)
print("  [4] relative-only identical for both : %.4f" % (rel_A == rel_B).mean())
print("  [4] dual-clock rule accuracy         : %.4f" % ((av_A >= 0) == (y == 1)).mean())
nz = (rel_A - rel_B) != 0
print("  [2] rel_A-rel_B decides              : %.1f%% of pairs" % (100 * nz.mean()))
acc = ((rel_A > 0) == (y == 1)).mean()
print("  [2] rel_A alone                      : %.4f" % max(acc, 1 - acc))
s = cross_val_score(gb(), np.column_stack([rel_A, rel_B, av_A, av_B]), y,
                    cv=GroupKFold(5), groups=grp)
print("  [6] (dEvent, dAvail) dual-clock      : %.4f  (+/- %.4f)" % (s.mean(), s.std()))
s = cross_val_score(gb(), np.column_stack([rel_A, rel_B]), y, cv=GroupKFold(5), groups=grp)
print("  [6] (dEvent) relative only           : %.4f  (+/- %.4f)" % (s.mean(), s.std()))

MASK = re.compile(r"\d[\d,\.]*")
idx = rng.choice(len(Q), size=min(6000, len(Q)), replace=False)
raw = ["%s [SEP] %s" % (A[i]["text"], B[i]["text"]) for i in idx]
print()
print("=" * 68)
print("PHASE-0 [5] lexical shortcut (n=%d)" % len(idx))
print("=" * 68)
for nm, corpus in (("raw text", raw), ("masked", [MASK.sub("<NUM>", r) for r in raw])):
    pipe = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_features=60000),
                         LogisticRegression(max_iter=1000))
    s = cross_val_score(pipe, corpus, y[idx], cv=GroupKFold(5), groups=grp[idx])
    print("  %-12s %.4f  (+/- %.4f)" % (nm, s.mean(), s.std()))

w = np.array([q["window_days"] for q in Q], dtype=float)
print()
print("=" * 68)
print("DISTRIBUTION PARAMETERS")
print("=" * 68)
print("  collision window: median %.0f  q25 %.0f  q75 %.0f"
      % (np.median(w), np.percentile(w, 25), np.percentile(w, 75)))
for P in (364, 365):
    r = np.minimum(w % P, P - (w % P))
    print("  within +-7d of a multiple of %d : %.1f%%" % (P, 100 * (r <= 7).mean()))
k2 = w[np.array([q["n_versions"] for q in Q]) == 2]
print("  k=2 subset n=%d  median %.0f  within +-7d of 364: %.1f%%"
      % (len(k2), np.median(k2), 100 * (np.abs(k2 - 364) <= 7).mean()))
rep = np.array([(D(C[q["gold_id"]]["avail_time"]) - D(q["event_time"])).days for q in Q])
print("  reporting lag: median %.0f  (5%%-95%%: %.0f-%.0f)"
      % (np.median(rep), np.percentile(rep, 5), np.percentile(rep, 95)))
