# -*- coding: utf-8 -*-
"""Phase-0 items 2, 4, 5, 6 exactly as pre-registered in
briefs/2026-08-10-MECH-AI-2.md section 10. No post-hoc redefinition.

Task throughout: given (query, as_of) and the two candidates in random order,
say which one was available at as_of. Chance = 0.500.
"""
import json
import random

import numpy as np
from datetime import date

rng = np.random.default_rng(0)
D = lambda s: date(*map(int, s.split("-")))

C = {c["id"]: c for c in map(json.loads, open("chunks.jsonl", encoding="utf-8"))}
Q = [json.loads(l) for l in open("queries.jsonl", encoding="utf-8")]
print("queries: %d   chunks: %d" % (len(Q), len(C)))

flip = rng.random(len(Q)) < 0.5
A = [C[q["distractor_id"] if f else q["gold_id"]] for q, f in zip(Q, flip)]
B = [C[q["gold_id"] if f else q["distractor_id"]] for q, f in zip(Q, flip)]
y = (~flip).astype(int)                       # 1 => A is the available one
asof = [D(q["as_of"]) for q in Q]
print("label balance: %.3f" % y.mean())

# ---------------------------------------------------------------- item 4
# Causal lever: relative-only tuple must be many-to-one on the label,
# the (event, availability) tuple must separate it. Deterministic, no LLM.
rel_A = np.array([(t - D(a["event_time"])).days for t, a in zip(asof, A)])
rel_B = np.array([(t - D(b["event_time"])).days for t, b in zip(asof, B)])
identical_rel = (rel_A == rel_B).mean()

av_A = np.array([(t - D(a["avail_time"])).days for t, a in zip(asof, A)])
av_B = np.array([(t - D(b["avail_time"])).days for t, b in zip(asof, B)])
dual_correct = ((av_A >= 0) == (y == 1)).mean()

print()
print("=" * 66)
print("[4] CAUSAL LEVER  (deterministic, no model)")
print("=" * 66)
print("  relative-only feature identical for both candidates : %.4f" % identical_rel)
print("     -> many-to-one on the label, cannot separate     : %s" % (identical_rel == 1.0))
print("  dual-clock rule (as_of >= avail_time) accuracy      : %.4f" % dual_correct)

# ---------------------------------------------------------------- item 2
# Side channel: try to recover the availability label from relative-only
# features by rule. Must fail (~chance) or the collision definition is void.
print()
print("=" * 66)
print("[2] SIDE CHANNEL from relative-only features")
print("=" * 66)
for name, f in (("rel_A - rel_B", rel_A - rel_B),
                ("rel_A", rel_A.astype(float)),
                ("sign(rel_A - rel_B)", np.sign(rel_A - rel_B).astype(float))):
    nz = f != 0
    if nz.sum() < 50:
        print("  %-22s decides %5.1f%% of pairs  (degenerate)" % (name, 100 * nz.mean()))
        continue
    acc = ((f[nz] > 0) == (y[nz] == 1)).mean()
    print("  %-22s decides %5.1f%% of pairs, correct %.4f"
          % (name, 100 * nz.mean(), max(acc, 1 - acc)))

# ---------------------------------------------------------------- item 6
# Learnable floor: a model reading only standardised (dEvent, dAvail) should be
# far above chance, otherwise the signal is drowned by linkage noise.
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold, cross_val_score

groups = np.array([q["concept"] for q in Q])
X_dual = np.column_stack([rel_A, rel_B, av_A, av_B])
X_rel = np.column_stack([rel_A, rel_B])
gb = lambda: HistGradientBoostingClassifier(max_iter=200, random_state=0)
s_dual = cross_val_score(gb(), X_dual, y, cv=GroupKFold(5), groups=groups)
s_rel = cross_val_score(gb(), X_rel, y, cv=GroupKFold(5), groups=groups)
print()
print("=" * 66)
print("[6] LEARNABLE FLOOR  (GroupKFold by concept)")
print("=" * 66)
print("  (dEvent, dAvail)  dual-clock : %.4f  (+/- %.4f)" % (s_dual.mean(), s_dual.std()))
print("  (dEvent) only     relative   : %.4f  (+/- %.4f)" % (s_rel.mean(), s_rel.std()))

# ---------------------------------------------------------------- item 5
# Lexical shortcut: TF-IDF on raw vs date-masked text. Both should be near
# chance, since the two candidates differ only in the numeric value.
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
import re

MASK = re.compile(r"\d[\d,\.]*")
idx = rng.choice(len(Q), size=min(6000, len(Q)), replace=False)
raw = ["%s [SEP] %s" % (A[i]["text"], B[i]["text"]) for i in idx]
msk = [MASK.sub("<NUM>", r) for r in raw]
yy, gg = y[idx], groups[idx]
print()
print("=" * 66)
print("[5] LEXICAL SHORTCUT  (TF-IDF + logistic, n=%d)" % len(idx))
print("=" * 66)
for nm, corpus in (("raw text", raw), ("date/number masked", msk)):
    pipe = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_features=60000),
                         LogisticRegression(max_iter=1000))
    s = cross_val_score(pipe, corpus, yy, cv=GroupKFold(5), groups=gg)
    print("  %-20s %.4f  (+/- %.4f)" % (nm, s.mean(), s.std()))
