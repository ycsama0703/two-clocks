# -*- coding: utf-8 -*-
"""Level 0 — can a model tell the two versions apart WITHOUT the position code?

If yes, the relative-time collision is irrelevant: the model reads availability
off some other channel and the whole line dies. Cheapest possible kill test.

Channels checked, all from data already on disk:
  1. metadata   — do fy / fp / form / accn differ between versions?
  2. value sign — is the revision direction systematically biased (so the larger
                  or smaller value is guessably "the later one")?
  3. magnitude  — is the later value systematically rounder / longer / bigger?

No model, no download, no GPU.
"""
import glob
import json
import os
from collections import defaultdict, Counter

import numpy as np

FILES = sorted(glob.glob("data/edgar/companyfacts/*.json"))
print("companyfacts files:", len(FILES))

meta_diff = Counter()          # which metadata fields separate the pair
n_pairs = 0
dir_up = 0
dir_down = 0
first_rounder = 0
later_rounder = 0
abs_bigger_later = 0


def trailing_zeros(x):
    try:
        s = str(int(abs(x)))
    except (ValueError, OverflowError):
        return 0
    return len(s) - len(s.rstrip("0"))


for path in FILES:
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except Exception:
        continue

    for taxonomy, concepts in (doc.get("facts") or {}).items():
        for concept, cdata in concepts.items():
            for unit, entries in (cdata.get("units") or {}).items():
                by_period = defaultdict(dict)
                for e in entries:
                    end, filed, val = e.get("end"), e.get("filed"), e.get("val")
                    if not end or not filed or val is None:
                        continue
                    key = (e.get("start"), end)
                    if filed not in by_period[key]:
                        by_period[key][filed] = e

                for key, seen in by_period.items():
                    if len(seen) < 2:
                        continue
                    items = [seen[f] for f in sorted(seen)]
                    vals = [it.get("val") for it in items]
                    if len(set(vals)) < 2:
                        continue
                    a, b = items[0], items[-1]        # first vs last disclosure
                    if a.get("val") == b.get("val"):
                        continue
                    n_pairs += 1

                    for field in ("fy", "fp", "form", "accn", "frame"):
                        if a.get(field) != b.get(field):
                            meta_diff[field] += 1
                    if a.get("fy") == b.get("fy") and a.get("fp") == b.get("fp") \
                       and a.get("form") == b.get("form"):
                        meta_diff["NONE_of_fy_fp_form"] += 1

                    va, vb = a["val"], b["val"]
                    if vb > va:
                        dir_up += 1
                    else:
                        dir_down += 1
                    if abs(vb) > abs(va):
                        abs_bigger_later += 1
                    za, zb = trailing_zeros(va), trailing_zeros(vb)
                    if za > zb:
                        first_rounder += 1
                    elif zb > za:
                        later_rounder += 1

print("version pairs with a changed value:", n_pairs)
print()
print("=" * 68)
print("CHANNEL 1 — metadata that separates the two versions")
print("=" * 68)
for field in ("fy", "fp", "form", "accn", "frame"):
    c = meta_diff[field]
    print("   %-6s differs in %6d / %d pairs   (%5.1f%%)"
          % (field, c, n_pairs, 100.0 * c / max(n_pairs, 1)))
c = meta_diff["NONE_of_fy_fp_form"]
print()
print("   fy AND fp AND form all identical: %d pairs (%.1f%%)"
      % (c, 100.0 * c / max(n_pairs, 1)))
print("   -> those are the only pairs where metadata does NOT leak availability")

print()
print("=" * 68)
print("CHANNEL 2 — is the revision direction guessable?")
print("=" * 68)
tot = dir_up + dir_down
print("   later value LARGER : %6d (%.1f%%)" % (dir_up, 100.0 * dir_up / max(tot, 1)))
print("   later value SMALLER: %6d (%.1f%%)" % (dir_down, 100.0 * dir_down / max(tot, 1)))
print("   |later| > |first|  : %6d (%.1f%%)" % (abs_bigger_later,
                                                100.0 * abs_bigger_later / max(tot, 1)))
print("   (50/50 = no leak; a strong skew means the later version is guessable)")

print()
print("=" * 68)
print("CHANNEL 3 — is the later value systematically rounder?")
print("=" * 68)
t2 = first_rounder + later_rounder
print("   first  rounder: %6d (%.1f%%)" % (first_rounder, 100.0 * first_rounder / max(t2, 1)))
print("   later  rounder: %6d (%.1f%%)" % (later_rounder, 100.0 * later_rounder / max(t2, 1)))
print("   ties          : %6d" % (n_pairs - t2))
