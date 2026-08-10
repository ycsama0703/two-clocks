# -*- coding: utf-8 -*-
"""Re-measure the value-channel ceiling with grouped CV.

The first pass used random 5-fold CV. Rows of the same concept land in both
train and test, so the model can memorise "this concept is usually revised
downward" -- that inflates the ceiling. The floor line drawn on the main
experiment's chart must not be inflated, so re-measure with the group held out.

Three splits, increasingly strict:
  random     -- what was reported before (63.2%)
  by concept -- concept unseen at test time
  by ticker  -- company unseen at test time (accounting habits held out too)
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import cross_val_score, GroupKFold, KFold
from sklearn.preprocessing import OrdinalEncoder

rng = np.random.default_rng(0)

df = pd.read_csv("results/revisions.csv")
for c in ("end", "first_filed", "first_revising_filed"):
    df[c] = pd.to_datetime(df[c], errors="coerce")
df["rep_lag"] = (df.first_filed - df.end).dt.days
den = np.maximum(df.first_val.abs(), df.final_val.abs())
df["srd"] = np.where(den > 0, (df.final_val - df.first_val).abs() / den, np.nan)
m = df[(df.first_val != 0) & (df.rep_lag.between(0, 400)) &
       (df.lag_days >= 30) & (df.srd >= 0.01)].reset_index(drop=True)

flip = rng.random(len(m)) < 0.5
va = np.where(flip, m.final_val, m.first_val).astype(float)
vb = np.where(flip, m.first_val, m.final_val).astype(float)
y = (~flip).astype(int)


def tz(x):
    out = np.zeros(len(x))
    for i, v in enumerate(x):
        try:
            s = str(int(abs(v)))
        except (ValueError, OverflowError):
            continue
        out[i] = len(s) - len(s.rstrip("0"))
    return out


def digits(x):
    with np.errstate(divide="ignore"):
        return np.where(np.abs(x) > 0, np.log10(np.abs(x) + 1e-12), 0.0)


X = np.nan_to_num(np.column_stack([
    digits(va) - digits(vb),
    np.abs(va) > np.abs(vb),
    tz(va) - tz(vb),
    (va > 0).astype(float) - (vb > 0).astype(float),
    (va == np.round(va)).astype(float) - (vb == np.round(vb)).astype(float),
    np.sign(va - vb),
    np.log1p(np.abs(va - vb)) - np.log1p(np.abs(va)),
    digits(va), digits(vb),
]).astype(np.float64), nan=0.0, posinf=0.0, neginf=0.0)

cid = OrdinalEncoder().fit_transform(m[["concept"]].astype(str))
Xc = np.column_stack([X, cid])

print("pairs: %d   concepts: %d   tickers: %d"
      % (len(m), m.concept.nunique(), m.ticker.nunique()))
print("label balance: %.3f" % y.mean())
print()
print("=" * 70)
print("VALUE-CHANNEL CEILING under three CV schemes   (chance = 0.500)")
print("=" * 70)


def run(name, cv, groups, feats, label):
    gb = HistGradientBoostingClassifier(max_iter=300, random_state=0)
    s = cross_val_score(gb, feats, y, cv=cv, groups=groups, scoring="accuracy")
    print("  %-28s %-18s %.3f  (+/- %.3f)" % (name, label, s.mean(), s.std()))
    return s.mean()


a = run("random 5-fold", KFold(5, shuffle=True, random_state=0), None, X, "numeric only")
b = run("random 5-fold", KFold(5, shuffle=True, random_state=0), None, Xc, "+ concept id")
print()
c = run("GroupKFold by concept", GroupKFold(5), m.concept.values, X, "numeric only")
d = run("GroupKFold by concept", GroupKFold(5), m.concept.values, Xc, "+ concept id")
print()
e = run("GroupKFold by ticker", GroupKFold(5), m.ticker.values, X, "numeric only")

print()
print("=" * 70)
print("VERDICT")
print("=" * 70)
print("  reported before (random CV, + concept id) : %.3f" % b)
print("  honest floor    (grouped by concept)      : %.3f" % c)
print("  strictest       (grouped by ticker)       : %.3f" % e)
print("  inflation from unblocked CV               : %+.3f" % (b - c))
