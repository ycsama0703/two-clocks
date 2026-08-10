# -*- coding: utf-8 -*-
"""Fetch accn -> effective-availability dates, resumably.

availability = max(filingDate, acceptanceDate)

companyfacts only carries `filed`, the LEGAL filing date. Phase-0 item 3 found
EDGAR accepting a document 36 days after it (ABT 0001104659-10-033097), so
labelling by `filed` alone bakes look-ahead bias into the gold labels.

At ~500 companies this is ~1,500 requests (submissions + historical shards).
v1 accumulated everything in memory and wrote once at the end, so a drop at
company 400 threw away all prior work. v2 shards per company and skips what is
already on disk.

    python src/fetch_acceptance.py                     # resume / continue
    python src/fetch_acceptance.py --check             # audit only
    python src/fetch_acceptance.py --merge-only        # rebuild acceptance.json
"""
import argparse
import glob
import json
import os
import time

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": os.environ.get("SEC_UA", "two-clocks research yuncongliu0703@gmail.com")}
BASE = "https://data.sec.gov/submissions/"


def get(url, tries=3):
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=45)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return None
            time.sleep(1.0 + i)
        except Exception:
            time.sleep(1.0 + i)
    return None


def valid(path):
    try:
        with open(path) as fh:
            return isinstance(json.load(fh), dict)
    except Exception:
        return False


def merge(shard_dir, out):
    acc = {}
    for p in sorted(glob.glob(os.path.join(shard_dir, "*.json"))):
        if os.path.basename(p).startswith("_"):
            continue
        try:
            acc.update(json.load(open(p)))
        except Exception:
            print("  skipping unreadable shard", os.path.basename(p))
    tmp = out + ".tmp"
    json.dump(acc, open(tmp, "w"), separators=(",", ":"))
    os.replace(tmp, out)
    print("merged %d shards -> %s (%d accessions, %.1f MB)"
          % (len(glob.glob(os.path.join(shard_dir, "*.json"))), out, len(acc),
             os.path.getsize(out) / 2**20))
    return acc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--facts-dir", default=os.path.join(ROOT, "data", "companyfacts"))
    ap.add_argument("--shard-dir", default=os.path.join(ROOT, "data", "acceptance"))
    ap.add_argument("--out", default=os.path.join(ROOT, "data", "acceptance.json"))
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--merge-only", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.shard_dir, exist_ok=True)

    if a.merge_only:
        merge(a.shard_dir, a.out)
        return

    need = {}
    for p in sorted(glob.glob(os.path.join(a.facts_dir, "*.json"))):
        t = os.path.basename(p)[:-5]
        try:
            cik = json.load(open(p, encoding="utf-8")).get("cik")
        except Exception:
            continue
        if cik:
            need[t] = int(cik)
    if not need:
        raise SystemExit("no companyfacts under %s" % a.facts_dir)

    done = [t for t in need if valid(os.path.join(a.shard_dir, t + ".json"))]
    todo = [t for t in need if t not in set(done)]
    print("companies %d   shards present %d   to fetch %d" % (len(need), len(done), len(todo)))
    if a.check:
        bad = [t for t in need
               if os.path.exists(os.path.join(a.shard_dir, t + ".json"))
               and not valid(os.path.join(a.shard_dir, t + ".json"))]
        print("corrupt shards to refetch:", bad or "none")
        return
    if not todo:
        merge(a.shard_dir, a.out)
        return

    failures, t0, shifted = [], time.time(), 0
    for i, t in enumerate(sorted(todo), 1):
        cik = need[t]
        sub = get(BASE + "CIK%010d.json" % cik)
        if not sub:
            failures.append(t)
            print("  [%3d/%d] %-6s FAIL" % (i, len(todo), t))
            continue
        table = {}

        def absorb(block):
            an = block.get("accessionNumber") or []
            fd = block.get("filingDate") or []
            ad = block.get("acceptanceDateTime") or []
            for j, k in enumerate(an):
                f = fd[j] if j < len(fd) else None
                d = (ad[j] or "")[:10] if j < len(ad) and ad[j] else None
                if f:
                    table[k] = max(f, d) if d else f

        absorb(sub.get("filings", {}).get("recent", {}))
        for s in sub.get("filings", {}).get("files", []) or []:
            j = get(BASE + s["name"])
            if j:
                absorb(j)
            time.sleep(0.15)
        dst = os.path.join(a.shard_dir, t + ".json")
        tmp = dst + ".tmp"
        json.dump(table, open(tmp, "w"), separators=(",", ":"))
        os.replace(tmp, dst)                      # atomic: partial shard never counts as done
        shifted += sum(1 for k, v in table.items() if v)
        if i % 20 == 0 or i == len(todo):
            el = time.time() - t0
            print("  [%3d/%d] %-6s %d accessions   %.1f min elapsed, ~%.1f min left"
                  % (i, len(todo), t, len(table), el / 60,
                     el / 60 * (len(todo) - i) / max(i, 1)))
        time.sleep(0.15)

    json.dump(failures, open(os.path.join(a.shard_dir, "_failures.json"), "w"))
    print()
    print("fetched %d   failed %d" % (len(todo) - len(failures), len(failures)))
    if failures:
        print("failed:", failures[:15])
    merge(a.shard_dir, a.out)


if __name__ == "__main__":
    main()
