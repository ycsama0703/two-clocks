# -*- coding: utf-8 -*-
"""Level 1 — upper bound on how much a classifier can recover WITHOUT position.

Setup: each collision pair gives two values for the same (concept, period), one
disclosed first and one later. Present them in RANDOM order as (v_a, v_b) and
ask a model to say which one was disclosed first. Chance = 50%.

Level 0 measured single-rule channels (direction 54.9%, roundness ~58%). This
measures what a classifier with interactions can reach, i.e. the ceiling of the
"bypass the position code via the numbers themselves" channel.

If the ceiling stays near chance, collision pairs are genuinely unidentifiable
without the availability clock, and the main experiment is well posed.
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(0)

df = pd.read_csv("results/revisions.csv")
for c in ("end", "first_filed", "first_revising_filed"):
    df[c] = pd.to_datetime(df[c], errors="coerce")
df["rep_lag"] = (df.first_filed - df.end).dt.days
den = np.maximum(df.first_val.abs(), df.final_val.abs())
df["srd"] = np.where(den > 0, (df.final_val - df.first_val).abs() / den, np.nan)
m = df[(df.first_val != 0) & (df.rep_lag.between(0, 400)) &
       (df.lag_days >= 30) & (df.srd >= 0.01)].reset_index(drop=True)
print("collision pairs:", len(m))

# randomise which of the two is presented as A
flip = rng.random(len(m)) < 0.5
va = np.where(flip, m.final_val, m.first_val).astype(float)
vb = np.where(flip, m.first_val, m.final_val).astype(float)
y = (~flip).astype(int)          # 1 if v_a is the FIRST disclosure
print("label balance: %.3f" % y.mean())


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


X = np.column_stack([
    digits(va) - digits(vb),
    np.abs(va) > np.abs(vb),
    tz(va) - tz(vb),
    (va > 0).astype(float) - (vb > 0).astype(float),
    (va == np.round(va)).astype(float) - (vb == np.round(vb)).astype(float),
    np.sign(va - vb),
    np.log1p(np.abs(va - vb)) - np.log1p(np.abs(va)),
    digits(va), digits(vb),
]).astype(np.float64)
X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

try:
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.model_selection import cross_val_score
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline
    have_sk = True
except ImportError:
    have_sk = False

print()
print("=" * 66)
print("CEILING OF THE VALUE CHANNEL   (chance = 0.500)")
print("=" * 66)

if have_sk:
    lr = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
    s = cross_val_score(lr, X, y, cv=5, scoring="accuracy")
    print("logistic regression : %.3f  (+/- %.3f)" % (s.mean(), s.std()))

    gb = HistGradientBoostingClassifier(max_iter=300, random_state=0)
    s = cross_val_score(gb, X, y, cv=5, scoring="accuracy")
    print("gradient boosting   : %.3f  (+/- %.3f)" % (s.mean(), s.std()))
    s = cross_val_score(gb, X, y, cv=5, scoring="roc_auc")
    print("gradient boosting   : AUC %.3f  (+/- %.3f)" % (s.mean(), s.std()))

    # per-concept model: does knowing the concept help?
    from sklearn.preprocessing import OrdinalEncoder
    cid = OrdinalEncoder().fit_transform(m[["concept"]].astype(str))
    X2 = np.column_stack([X, cid])
    s = cross_val_score(HistGradientBoostingClassifier(max_iter=300, random_state=0),
                        X2, y, cv=5, scoring="accuracy")
    print("GB + concept id     : %.3f  (+/- %.3f)" % (s.mean(), s.std()))
else:
    print("(sklearn unavailable -- single-feature AUCs only)")

print()
print("=" * 66)
print("SINGLE-FEATURE SIGNAL  (share where the feature alone picks correctly)")
print("=" * 66)
names = ["log|v| diff", "|va|>|vb|", "trailing-zeros diff", "sign diff",
         "is-integer diff", "sign(va-vb)", "rel gap", "log|va|", "log|vb|"]
for j, nm in enumerate(names):
    f = X[:, j]
    nz = f != 0
    if nz.sum() < 50:
        print("   %-22s n/a (constant)" % nm)
        continue
    acc = ((f[nz] > 0) == (y[nz] == 1)).mean()
    acc = max(acc, 1 - acc)
    print("   %-22s decides %5.1f%% of pairs, correct %5.1f%% of those"
          % (nm, 100.0 * nz.mean(), 100.0 * acc))
