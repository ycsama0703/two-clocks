# -*- coding: utf-8 -*-
"""Corrected Phase-0 audit.

The first pass used `rel_change`, which is (final-first)/first and explodes to
1e20 when first_val == 0 (a concept first reported as 0 or absent). The
"|rel_change| >= 1%" filter therefore KEPT exactly the rows it should have
dropped. Use a symmetric relative difference instead, and drop impossible
reporting lags.
"""
import pandas as pd
import numpy as np

df = pd.read_csv("results/revisions.csv")
for c in ("end", "first_filed", "first_revising_filed"):
    df[c] = pd.to_datetime(df[c], errors="coerce")

df["rep_lag"] = (df.first_filed - df.end).dt.days

# Symmetric relative difference: bounded in [0, 2], undefined only if both are 0.
denom = np.maximum(df.first_val.abs(), df.final_val.abs())
df["srd"] = np.where(denom > 0, (df.final_val - df.first_val).abs() / denom, np.nan)
df["zero_start"] = df.first_val == 0

print("=" * 70)
print("DATA QUALITY")
print("=" * 70)
print("rows                          :", len(df))
print("first_val == 0 (rel_change bad):", int(df.zero_start.sum()),
      "(%.1f%%)" % (100.0 * df.zero_start.mean()))
print("reporting lag < 0 (impossible):", int((df.rep_lag < 0).sum()))
print("reporting lag > 400d          :", int((df.rep_lag > 400).sum()))
print()
print("symmetric rel diff (srd), zero-start rows excluded:")
print(df.loc[~df.zero_start, "srd"].describe(
    percentiles=[.25, .5, .75, .95]).round(4).to_string())

print()
print("=" * 70)
print("CLEAN COLLISION PAIRS")
print("=" * 70)
clean = df[(~df.zero_start) & (df.rep_lag >= 0) & (df.rep_lag <= 400) &
           (df.lag_days >= 30) & (df.n_distinct_vals >= 2)]
print("after dropping zero-start and impossible lags : %d" % len(clean))
for thr in (0.001, 0.005, 0.01, 0.05, 0.10):
    n = int((clean.srd >= thr).sum())
    print("   srd >= %5.1f%%  : %6d pairs   (%d tickers, %d concepts)"
          % (100 * thr, n,
             clean.loc[clean.srd >= thr, "ticker"].nunique(),
             clean.loc[clean.srd >= thr, "concept"].nunique()))

main = clean[clean.srd >= 0.01]
print()
print("=" * 70)
print("THE PARAMETERS THE CLOSED FORM NEEDS  (on srd >= 1%% set, n=%d)" % len(main))
print("=" * 70)
print("[reporting lag] period end -> first disclosure, days")
print(main.rep_lag.describe(percentiles=[.05, .25, .5, .75, .95]).round(1).to_string())
print()
print("[collision window] first disclosure -> first revision, days")
print(main.lag_days.describe(percentiles=[.05, .25, .5, .75, .95]).round(1).to_string())
print()
print("[revision multiplicity] how many filings restate the same (concept, period)")
print(main.n_filings.value_counts().sort_index().head(8).to_string())
print()
print("[quarterly clustering] share of collision windows within +-15d of a multiple of 91d:")
w = main.lag_days.values
near_q = np.min([np.abs(w - k * 91) for k in range(1, 9)], axis=0) <= 15
print("   %.1f%%" % (100.0 * near_q.mean()))
print("[annual clustering] within +-15d of a multiple of 365d:")
near_y = np.min([np.abs(w - k * 365) for k in range(1, 6)], axis=0) <= 15
print("   %.1f%%" % (100.0 * near_y.mean()))

print()
print("=" * 70)
print("SAMPLE CLEAN PAIRS (mid-range revisions, not outliers)")
print("=" * 70)
cols = ["ticker", "concept", "end", "first_filed", "first_revising_filed",
        "lag_days", "first_val", "final_val", "srd"]
mid = main[(main.srd > 0.05) & (main.srd < 0.5)]
print(mid.head(10)[cols].to_string(index=False))
print()
print("formal /A amendments in clean set:", int(main.has_amendment.sum()))
print("top form chains:")
print(main.forms_chain.value_counts().head(5).to_string())
