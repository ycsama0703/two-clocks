# -*- coding: utf-8 -*-
"""Phase-0 item 3 (pre-registered, [high]):

  "findata 的 publication/filing 时间可以解释为信息真实可得时间，而不是数据库
   ingestion/update 时间。 -- $0 check: 抽 30-50 条与 SEC accession/accepted
   timestamp 或原始文档发布日期交叉核对，统计偏差及缺失。"

companyfacts gives每个 fact 一个 `accn` + `filed`. SEC's submissions API gives the
same accession its `filingDate` (the legal date) and `acceptanceDateTime` (when
EDGAR actually accepted it, i.e. when it became visible).

Two failure modes to rule out:
  A. `filed` != `filingDate`      -> our avail_time is not the SEC filing date at all
  B. acceptance date > filingDate -> the document became visible AFTER the date we
     label as available => look-ahead bias baked into the gold labels
(acceptance date < filingDate is the benign direction: EDGAR accepts after 17:30 ET
 and rolls the legal date to the next business day, so we would be conservative.)
"""
import glob
import json
import os
import time
from collections import defaultdict

import requests

UA = {"User-Agent": "AlphaGap Research yuncongliu0703@gmail.com"}
N_COMPANIES = 6
PER_COMPANY = 10

# ---- collect (cik, accn, filed) from companyfacts, newest first --------------
want = {}
for path in sorted(glob.glob("../data/edgar/companyfacts/*.json"))[:40]:
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
    if seen:
        want[ticker] = (int(cik), sorted(seen.items(), key=lambda kv: kv[1], reverse=True))
    if len(want) >= N_COMPANIES:
        break

print("companies sampled:", list(want))

rows, missing = [], 0
for ticker, (cik, pairs) in want.items():
    url = "https://data.sec.gov/submissions/CIK%010d.json" % cik
    try:
        r = requests.get(url, headers=UA, timeout=30)
        r.raise_for_status()
        sub = r.json()
    except Exception as e:
        print("  FETCH FAIL %s: %s" % (ticker, str(e)[:70]))
        continue
    rec = sub.get("filings", {}).get("recent", {})
    idx = {an: i for i, an in enumerate(rec.get("accessionNumber", []))}
    hit = 0
    for accn, filed in pairs:
        if accn not in idx or hit >= PER_COMPANY:
            continue
        i = idx[accn]
        rows.append({
            "ticker": ticker, "accn": accn,
            "cf_filed": filed,
            "sec_filingDate": rec["filingDate"][i],
            "sec_acceptance": rec.get("acceptanceDateTime", [None] * (i + 1))[i],
            "form": rec.get("form", [None] * (i + 1))[i],
        })
        hit += 1
    missing += max(0, min(PER_COMPANY, len(pairs)) - hit)
    print("  %-6s cik=%-8d matched %d" % (ticker, cik, hit))
    time.sleep(0.2)

print()
print("=" * 70)
print("CROSS-CHECK  n = %d  (missing/unmatched: %d)" % (len(rows), missing))
print("=" * 70)
if not rows:
    raise SystemExit("no rows matched -- cannot conclude")

mismatch = [r for r in rows if r["cf_filed"] != r["sec_filingDate"]]
print("A. companyfacts.filed != SEC.filingDate : %d / %d" % (len(mismatch), len(rows)))
for r in mismatch[:5]:
    print("     %s %s  cf=%s sec=%s" % (r["ticker"], r["accn"], r["cf_filed"], r["sec_filingDate"]))

later = same = earlier = nodata = 0
for r in rows:
    acc = r["sec_acceptance"]
    if not acc:
        nodata += 1
        continue
    accd = acc[:10]
    if accd > r["sec_filingDate"]:
        later += 1
    elif accd == r["sec_filingDate"]:
        same += 1
    else:
        earlier += 1
print()
print("B. acceptance date vs filingDate")
print("     LATER   (visible after labelled date -- LOOK-AHEAD RISK) : %d" % later)
print("     same                                                    : %d" % same)
print("     earlier (accepted after 17:30 ET, legal date rolled fwd) : %d" % earlier)
print("     no acceptance timestamp                                  : %d" % nodata)

print()
print("sample rows:")
for r in rows[:8]:
    print("   %-6s %-22s form=%-6s cf_filed=%s sec=%s acc=%s"
          % (r["ticker"], r["accn"], r["form"], r["cf_filed"],
             r["sec_filingDate"], (r["sec_acceptance"] or "")[:16]))
