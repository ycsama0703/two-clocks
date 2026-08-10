# -*- coding: utf-8 -*-
"""Rebuild the full disclosure series a_1 < a_2 < ... < a_k from companyfacts.

revisions.csv only kept (a_1, a_2). The closed form
    E|a_j - a_i| = (P / C(k,2)) * sum_{i<j}(q_j - q_i)
needs every a_i to be tested beyond k=2. SEC companyfacts carries one entry per
(concept, unit, period, filing), each with its own `filed` date, so the series
is recoverable exactly.

Tests the equidistant-lattice prediction E|a_j-a_i| = (k+1)P/3 against the
measured mean pairwise gap, per k.
"""
import glob
import json
import os
from collections import defaultdict
from datetime import date

import numpy as np

P = 364.0
FILES = sorted(glob.glob("data/edgar/companyfacts/*.json"))
print("companyfacts files:", len(FILES))


def d(s):
    y, m, dd = s.split("-")
    return date(int(y), int(m), int(dd))


# k -> list of mean pairwise gaps (one per series); also collect first gaps
gaps_by_k = defaultdict(list)
first_gap_by_k = defaultdict(list)
span_by_k = defaultdict(list)
n_series = 0
n_files = 0

for path in FILES:
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except Exception as e:
        print("skip", os.path.basename(path), str(e)[:60])
        continue
    n_files += 1

    for taxonomy, concepts in (doc.get("facts") or {}).items():
        for concept, cdata in concepts.items():
            for unit, entries in (cdata.get("units") or {}).items():
                # bucket by reporting period
                by_period = defaultdict(list)
                for e in entries:
                    end, filed, val = e.get("end"), e.get("filed"), e.get("val")
                    if not end or not filed or val is None:
                        continue
                    # keep duration facts distinct from instant facts
                    by_period[(e.get("start"), end)].append((filed, val))

                for _, rows in by_period.items():
                    # one disclosure per filing date: take the first value seen
                    seen = {}
                    for filed, val in rows:
                        if filed not in seen:
                            seen[filed] = val
                    if len(seen) < 2:
                        continue
                    items = sorted(seen.items())          # by filed date
                    vals = [v for _, v in items]
                    if len(set(vals)) < 2:                # value never changed
                        continue
                    days = [d(f).toordinal() for f, _ in items]
                    k = len(days)
                    if k > 12:
                        continue
                    pair_gaps = [days[j] - days[i]
                                 for i in range(k) for j in range(i + 1, k)]
                    gaps_by_k[k].append(float(np.mean(pair_gaps)))
                    first_gap_by_k[k].append(days[1] - days[0])
                    span_by_k[k].append(days[-1] - days[0])
                    n_series += 1

print("files parsed :", n_files)
print("series with >=2 distinct values:", n_series)

print()
print("=" * 74)
print("CLOSED FORM  E|a_j - a_i| = (k+1)P/3   with P = %.0f" % P)
print("=" * 74)
print("%3s %8s %12s %12s %9s %12s" %
      ("k", "n", "predicted", "observed", "ratio", "first gap"))
for k in sorted(gaps_by_k):
    g = np.array(gaps_by_k[k])
    if len(g) < 30:
        continue
    pred = (k + 1) * P / 3.0
    obs = float(np.median(g))
    fg = float(np.median(first_gap_by_k[k]))
    print("%3d %8d %12.0f %12.0f %9.2f %12.0f" %
          (k, len(g), pred, obs, obs / pred, fg))

print()
print("=" * 74)
print("WHERE THE LATTICE ACTUALLY SITS  (first gap, share within +-7d)")
print("=" * 74)
for k in sorted(first_gap_by_k):
    fg = np.array(first_gap_by_k[k], dtype=float)
    if len(fg) < 30:
        continue
    on_364 = np.minimum(fg % 364, 364 - (fg % 364)) <= 7
    on_91 = np.minimum(fg % 91, 91 - (fg % 91)) <= 7
    print("k=%-3d n=%-7d median=%-6.0f  on 364-lattice: %5.1f%%   on 91-lattice: %5.1f%%"
          % (k, len(fg), np.median(fg), 100 * on_364.mean(), 100 * on_91.mean()))

print()
print("=" * 74)
print("SPAN  a_k - a_1   (how long a number stays revisable)")
print("=" * 74)
for k in sorted(span_by_k):
    s = np.array(span_by_k[k], dtype=float)
    if len(s) < 30:
        continue
    print("k=%-3d median span = %6.0f days   (%.1f years)   pred (k-1)P = %.0f"
          % (k, np.median(s), np.median(s) / 365.25, (k - 1) * P))
