# -*- coding: utf-8 -*-
"""Pull SEC XBRL companyfacts for an arbitrary ticker list, resumably.

Scaling from 63 to ~500 companies means ~2 GB over ~500 requests, so a run that
cannot resume is a run that will be repeated. Every download is atomic
(tmp + rename) and validated as JSON before being counted, so an interrupted
run never leaves a half-file that a later run would skip.

    python src/pull_companyfacts.py --tickers-file sp500.txt
    python src/pull_companyfacts.py --tickers AAPL,MSFT,NVDA
    python src/pull_companyfacts.py --tickers-file sp500.txt --retry-failed
    python src/pull_companyfacts.py --tickers-file sp500.txt --check   # audit only

Source: https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json
SEC asks for a descriptive User-Agent and <=10 req/s; both are honoured here.
"""
import argparse
import json
import os
import shutil
import sys
import time

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": os.environ.get("SEC_UA", "two-clocks research yuncongliu0703@gmail.com")}
TICKER_MAP = "https://www.sec.gov/files/company_tickers.json"
FACTS = "https://data.sec.gov/api/xbrl/companyfacts/CIK%010d.json"
SLEEP = 0.12                       # ~8 req/s, under SEC's 10


def load_tickers(a):
    if a.tickers_file:
        with open(a.tickers_file, encoding="utf-8") as fh:
            raw = [l.split("#")[0].split(",")[0].strip() for l in fh]
        return [t.upper() for t in raw if t]
    if a.tickers:
        return [t.strip().upper() for t in a.tickers.split(",") if t.strip()]
    sys.exit("give --tickers or --tickers-file")


def valid(path):
    """A file counts as done only if it parses and carries facts."""
    try:
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
        return bool(d.get("facts"))
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers")
    ap.add_argument("--tickers-file")
    ap.add_argument("--out", default=os.path.join(ROOT, "data", "companyfacts"))
    ap.add_argument("--retry-failed", action="store_true",
                    help="re-attempt only the tickers in failures.json")
    ap.add_argument("--check", action="store_true",
                    help="audit what is present, download nothing")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    fail_path = os.path.join(a.out, "_failures.json")
    tickers = load_tickers(a)
    if a.retry_failed:
        if not os.path.exists(fail_path):
            sys.exit("no _failures.json to retry")
        tickers = json.load(open(fail_path))
        print("retrying %d previously failed tickers" % len(tickers))

    done = [t for t in tickers if valid(os.path.join(a.out, t + ".json"))]
    todo = [t for t in tickers if t not in set(done)]
    free_gb = shutil.disk_usage(a.out).free / 2**30
    print("requested %d   already complete %d   to fetch %d   free disk %.1f GB"
          % (len(tickers), len(done), len(todo), free_gb))
    if a.check:
        stale = [t for t in tickers
                 if os.path.exists(os.path.join(a.out, t + ".json"))
                 and not valid(os.path.join(a.out, t + ".json"))]
        print("corrupt/partial files that will be re-fetched:", stale or "none")
        return
    if not todo:
        print("nothing to do")
        return
    if free_gb < 1 + 0.004 * len(todo):
        sys.exit("not enough free disk for ~%d files" % len(todo))

    print("fetching ticker->CIK map ...")
    m = requests.get(TICKER_MAP, headers=UA, timeout=60).json()
    t2c = {v["ticker"].upper(): int(v["cik_str"]) for v in m.values()}

    failures, t0 = [], time.time()
    for i, t in enumerate(todo, 1):
        cik = t2c.get(t)
        if cik is None:
            print("  [%4d/%d] %-6s no CIK in SEC map" % (i, len(todo), t))
            failures.append(t)
            continue
        dst = os.path.join(a.out, t + ".json")
        tmp = dst + ".tmp"
        ok = False
        for attempt in range(3):
            try:
                r = requests.get(FACTS % cik, headers=UA, timeout=120)
                if r.status_code == 404:
                    print("  [%4d/%d] %-6s 404 (no XBRL facts)" % (i, len(todo), t))
                    break
                r.raise_for_status()
                d = r.json()
                if not d.get("facts"):
                    break
                with open(tmp, "w", encoding="utf-8") as fh:
                    json.dump(d, fh)
                os.replace(tmp, dst)          # atomic: no half-files to skip later
                ok = True
                break
            except Exception as e:
                if attempt == 2:
                    print("  [%4d/%d] %-6s FAIL %s" % (i, len(todo), t, str(e)[:60]))
                time.sleep(2 * (attempt + 1))
        if not ok:
            failures.append(t)
            if os.path.exists(tmp):
                os.remove(tmp)
        elif i % 25 == 0 or i == len(todo):
            el = time.time() - t0
            mb = sum(os.path.getsize(os.path.join(a.out, f))
                     for f in os.listdir(a.out) if f.endswith(".json")) / 2**20
            print("  [%4d/%d] %.1f min elapsed, ~%.1f min left, %.0f MB on disk"
                  % (i, len(todo), el / 60, el / 60 * (len(todo) - i) / max(i, 1), mb))
        time.sleep(SLEEP)

    json.dump(failures, open(fail_path, "w"))
    print()
    print("fetched %d   failed %d" % (len(todo) - len(failures), len(failures)))
    if failures:
        print("failures written to %s -- rerun with --retry-failed" % fail_path)
        print("  ", failures[:15], "..." if len(failures) > 15 else "")


if __name__ == "__main__":
    main()
