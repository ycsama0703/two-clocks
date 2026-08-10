# -*- coding: utf-8 -*-
"""Phase-0 item 3, re-done without the recency bias.

The first pass sampled the newest filings and matched only against SEC's
`filings.recent` (last 1000), so all 59 cross-checks landed in 2024-2026 while
the corpus spans 2007-2026. This version:
  - pulls every historical shard listed in `filings.files`
  - samples STRATIFIED by era, so early EDGAR behaviour is actually tested

Checks, unchanged:
  A. companyfacts.filed == SEC.filingDate ?
  B. acceptance date > filingDate  =>  document visible AFTER the date we label
     as available  =>  look-ahead bias in the gold labels.
     (acceptance < filingDate is benign: accepted after 17:30 ET, legal date
      rolls forward, so our label is conservative.)
"""
import glob
import json
import os
import time
from collections import defaultdict

import requests

UA = {"User-Agent": "AlphaGap Research yuncongliu0703@gmail.com"}
ERAS = [(2007, 2012), (2013, 2018), (2019, 2026)]
PER_ERA = 8
N_COMPANIES = 6
BASE = "https://data.sec.gov/submissions/"


def get(url, tries=3):
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=40)
            if r.status_code == 200:
                return r.json()
            time.sleep(1 + i)
        except Exception:
            time.sleep(1 + i)
    return None


# ---- (cik, accn, filed) from companyfacts -----------------------------------
want = {}
CF_GLOB = os.path.expanduser("~/repairable-experience/data/edgar/companyfacts/*.json")
_files = sorted(glob.glob(CF_GLOB))
if not _files:
    raise SystemExit("no companyfacts found at %s -- fix the path, do not "
                     "silently report n=0" % CF_GLOB)
for path in _files[:40]:
    ticker = os.path.basename(path)[:-5]
    try:
        doc = json.load(open(path, encoding="utf-8"))
    except Exception:
        continue
    cik = doc.get("cik")
    if not cik:
        continue
    seen = {}
    for _, concepts in (doc.get("facts") or {}).items():
        for _, cdata in concepts.items():
            for _, entries in (cdata.get("units") or {}).items():
                for e in entries:
                    a, f = e.get("accn"), e.get("filed")
                    if a and f:
                        seen[a] = f
    if len(seen) > 50:
        want[ticker] = (int(cik), seen)
    if len(want) >= N_COMPANIES:
        break
print("companies:", list(want))

rows = []
for ticker, (cik, seen) in want.items():
    sub = get(BASE + "CIK%010d.json" % cik)
    if not sub:
        print("  %-6s submissions FAIL" % ticker)
        continue
    table = {}                                   # accn -> (filingDate, acceptance)

    def absorb(block):
        an = block.get("accessionNumber") or []
        fd = block.get("filingDate") or []
        ac = block.get("acceptanceDateTime") or [None] * len(an)
        for i, a in enumerate(an):
            table[a] = (fd[i] if i < len(fd) else None,
                        ac[i] if i < len(ac) else None)

    absorb(sub.get("filings", {}).get("recent", {}))
    shards = sub.get("filings", {}).get("files", []) or []
    for s in shards:
        j = get(BASE + s["name"])
        if j:
            absorb(j)
        time.sleep(0.15)
    print("  %-6s cik=%-8d shards=%d  accessions=%d" % (ticker, cik, len(shards), len(table)))

    # stratified sampling by era
    by_era = defaultdict(list)
    for accn, filed in seen.items():
        if accn not in table:
            continue
        yr = int(filed[:4])
        for lo, hi in ERAS:
            if lo <= yr <= hi:
                by_era[(lo, hi)].append((accn, filed))
                break
    for era, items in by_era.items():
        items.sort()
        step = max(1, len(items) // PER_ERA)
        for accn, filed in items[::step][:PER_ERA]:
            fd, ac = table[accn]
            rows.append({"ticker": ticker, "era": "%d-%d" % era, "accn": accn,
                         "cf_filed": filed, "sec_filingDate": fd, "sec_acceptance": ac})
    time.sleep(0.2)

print()
print("=" * 72)
print("CROSS-CHECK  n = %d" % len(rows))
print("=" * 72)
by_era = defaultdict(list)
for r in rows:
    by_era[r["era"]].append(r)

print("%-12s %6s %10s %10s %8s %8s %10s" %
      ("era", "n", "filed!=sec", "acc LATER", "same", "earlier", "no-acc"))
tot_mismatch = tot_later = 0
for era in sorted(by_era):
    rs = by_era[era]
    mm = sum(1 for r in rs if r["cf_filed"] != r["sec_filingDate"])
    later = same = earlier = noacc = 0
    for r in rs:
        if not r["sec_acceptance"]:
            noacc += 1
            continue
        d = r["sec_acceptance"][:10]
        if d > r["sec_filingDate"]:
            later += 1
        elif d == r["sec_filingDate"]:
            same += 1
        else:
            earlier += 1
    tot_mismatch += mm
    tot_later += later
    print("%-12s %6d %10d %10d %8d %8d %10d"
          % (era, len(rs), mm, later, same, earlier, noacc))

print()
print("TOTAL  filed != filingDate : %d / %d" % (tot_mismatch, len(rows)))
print("TOTAL  acceptance LATER    : %d / %d   <- look-ahead risk" % (tot_later, len(rows)))
for r in rows:
    if r["cf_filed"] != r["sec_filingDate"] or (
            r["sec_acceptance"] and r["sec_acceptance"][:10] > r["sec_filingDate"]):
        print("   OFFENDER", r)
