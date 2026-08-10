# -*- coding: utf-8 -*-
"""Build accn -> acceptance-date map for every company in the corpus.

Why: companyfacts gives only `filed` (the LEGAL filing date). Phase-0 item 3
found a case where EDGAR accepted the document 36 days AFTER that date
(ABT 0001104659-10-033097: filed 2010-05-04, accepted 2010-06-09). Labelling
availability by `filed` alone therefore bakes look-ahead bias into 0.7% of gold
labels -- the exact error this benchmark exists to detect.

Effective availability is max(filingDate, acceptanceDate).

Writes data/acceptance.json:  {accn: "YYYY-MM-DD"}
"""
import glob
import json
import os
import time

import requests

UA = {"User-Agent": "AlphaGap Research yuncongliu0703@gmail.com"}
BASE = "https://data.sec.gov/submissions/"
OUT = os.path.expanduser("~/workspace/projects/bitemporal-bench/data/acceptance.json")
CF = os.path.expanduser("~/repairable-experience/data/edgar/companyfacts/*.json")


def get(url, tries=3):
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=45)
            if r.status_code == 200:
                return r.json()
            time.sleep(1.0 + i)
        except Exception:
            time.sleep(1.0 + i)
    return None


files = sorted(glob.glob(CF))
if not files:
    raise SystemExit("no companyfacts at %s" % CF)
print("companyfacts files:", len(files))

need = {}                                   # cik -> ticker
for path in files:
    try:
        doc = json.load(open(path, encoding="utf-8"))
    except Exception:
        continue
    cik = doc.get("cik")
    if cik:
        need[int(cik)] = os.path.basename(path)[:-5]
print("companies:", len(need))

acc = {}
fail = []
for n, (cik, ticker) in enumerate(sorted(need.items()), 1):
    sub = get(BASE + "CIK%010d.json" % cik)
    if not sub:
        fail.append(ticker)
        print("  [%2d] %-6s FAIL" % (n, ticker))
        continue
    got = 0

    def absorb(block):
        global got
        an = block.get("accessionNumber") or []
        fd = block.get("filingDate") or []
        ad = block.get("acceptanceDateTime") or []
        for i, a in enumerate(an):
            f = fd[i] if i < len(fd) else None
            d = (ad[i] or "")[:10] if i < len(ad) and ad[i] else None
            if not f:
                continue
            acc[a] = max(f, d) if d else f          # effective availability
            got += 1

    absorb(sub.get("filings", {}).get("recent", {}))
    for s in sub.get("filings", {}).get("files", []) or []:
        j = get(BASE + s["name"])
        if j:
            absorb(j)
        time.sleep(0.15)
    print("  [%2d] %-6s cik=%-9d accessions=%d" % (n, ticker, cik, got))
    time.sleep(0.15)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(acc, open(OUT, "w"), separators=(",", ":"))
print()
print("wrote %s   accessions=%d   failed companies=%s" % (OUT, len(acc), fail or "none"))

# how often does acceptance actually move the date?
moved = 0
for path in files:
    try:
        doc = json.load(open(path, encoding="utf-8"))
    except Exception:
        continue
    for _, concepts in (doc.get("facts") or {}).items():
        for _, cdata in concepts.items():
            for _, entries in (cdata.get("units") or {}).items():
                for e in entries:
                    a, f = e.get("accn"), e.get("filed")
                    if a and f and a in acc and acc[a] != f:
                        moved += 1
print("fact entries whose availability shifts under max(): %d" % moved)
