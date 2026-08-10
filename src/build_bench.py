# -*- coding: utf-8 -*-
"""Build the bitemporal retrieval benchmark corpus from SEC XBRL.

Design decisions baked in (see D:\\personal doc\\DARMO\\260726\\bitemporal-retrieval-bench.md):
  chunk    = one XBRL fact, templated text, carries ONLY period_end (event time).
             fy / fp / form / accn are NEVER emitted -- Level 0 measured fy alone
             separating the two versions in 97.2% of pairs.
  ordering = NOT chosen here. Each chunk stores both clocks so the evaluator can
             sort by either; ordering is an experimental variable.
  pool size= NOT chosen here. Chunks are emitted with both clocks and a company
             key so the evaluator can draw pools of any L.

Outputs (jsonl, into bench/):
  chunks.jsonl   every fact-version: id, text, event_time, avail_time, ticker, concept
  queries.jsonl  one per collision pair: query, as_of, gold_id, distractor_id
"""
import glob
import json
import os
import re
from collections import defaultdict
from datetime import date, timedelta

import pandas as pd

OUT = "bench"
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- concept labels
label_of = {}
series = defaultdict(list)          # (ticker, concept, unit, start, end) -> [(filed, val)]

for path in sorted(glob.glob("data/edgar/companyfacts/*.json")):
    ticker = os.path.basename(path)[:-5]
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except Exception:
        continue
    for _, concepts in (doc.get("facts") or {}).items():
        for concept, cdata in concepts.items():
            lab = (cdata.get("label") or "").strip()
            if lab and concept not in label_of:
                label_of[concept] = lab
            for unit, entries in (cdata.get("units") or {}).items():
                seen = {}
                for e in entries:
                    end, filed, val = e.get("end"), e.get("filed"), e.get("val")
                    if not end or not filed or val is None:
                        continue
                    seen.setdefault((filed,), (val, e.get("start")))
                    key = (ticker, concept, unit, e.get("start"), end)
                    series[key].append((filed, val))

print("concepts with labels:", len(label_of))
print("raw series:", len(series))


_DEPRECATED = re.compile(r"\s*\(\s*deprecated[^)]*\)", re.I)
_ISODATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_YEAR = re.compile(r"\b(?:19|20)\d{2}\b")


def humanise(concept):
    """SEC label if present, else split the CamelCase tag.

    The label is scrubbed of dates first. SEC tags carry "(Deprecated 2018-01-31)"
    markers, and a deprecation date bounds when a filing using that tag could have
    been made -- i.e. it leaks the availability clock. On the first build 1,532
    chunks (3.8%) carried such a date and 5 of them printed their own avail_time
    verbatim.
    """
    lab = label_of.get(concept)
    if lab:
        lab = _DEPRECATED.sub("", lab)
        lab = _ISODATE.sub("", lab)
        lab = _YEAR.sub("", lab)
        lab = re.sub(r"\(\s*\)", "", lab)
        lab = re.sub(r"\s{2,}", " ", lab).strip(" ,;:-")
        if len(lab) >= 3:
            return lab
    out, buf = [], ""
    for ch in concept:
        if ch.isupper() and buf:
            out.append(buf)
            buf = ch
        else:
            buf += ch
    out.append(buf)
    return " ".join(out).lower()


def fmt(v):
    if v is None:
        return "n/a"
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return "{:,}".format(v) if isinstance(v, int) else str(v)


UNIT_WORD = {"USD": "USD", "shares": "shares", "USD/shares": "USD per share",
             "pure": "", "Rate": ""}

# ---------------------------------------------------------------- collision pairs
df = pd.read_csv("results/revisions.csv")
for c in ("end", "first_filed", "first_revising_filed"):
    df[c] = pd.to_datetime(df[c], errors="coerce")
df["rep_lag"] = (df.first_filed - df.end).dt.days
den = df[["first_val", "final_val"]].abs().max(axis=1)
df["srd"] = (df.final_val - df.first_val).abs() / den.replace(0, pd.NA)
pairs = df[(df.first_val != 0) & df.rep_lag.between(0, 400) &
           (df.lag_days >= 30) & (df.srd >= 0.01) &
           df.n_filings.isin([2, 3])].reset_index(drop=True)
print("collision pairs (k in {2,3}, closed form applies):", len(pairs))

# ---------------------------------------------------------------- emit
chunks, queries = [], []
cid = 0
skipped = 0

for i, r in pairs.iterrows():
    unit = UNIT_WORD.get(r.unit, r.unit or "")
    lab = humanise(r.concept)
    period = r.end.date().isoformat()

    ids = []
    for val, filed in ((r.first_val, r.first_filed), (r.final_val, r.first_revising_filed)):
        cid += 1
        text = "%s reported %s of %s%s for the period ended %s." % (
            r.ticker, lab, fmt(val), (" " + unit) if unit else "", period)
        chunks.append({
            "id": "c%07d" % cid,
            "text": text,                      # event time only, no filing metadata
            "ticker": r.ticker,
            "concept": r.concept,
            "event_time": period,              # clock 1  (valid time)
            "avail_time": filed.date().isoformat(),   # clock 2  (transaction time)
            "value": float(val),
        })
        ids.append("c%07d" % cid)

    # as-of at the midpoint of the collision window: gold is available, distractor is not
    a1, a2 = r.first_filed.date(), r.first_revising_filed.date()
    as_of = a1 + timedelta(days=int((a2 - a1).days / 2))
    if not (a1 <= as_of < a2):
        skipped += 1
        continue
    queries.append({
        "id": "q%07d" % (i + 1),
        "query": "What was %s's %s for the period ended %s?" % (r.ticker, lab, period),
        "as_of": as_of.isoformat(),
        "gold_id": ids[0],
        "distractor_id": ids[1],
        "ticker": r.ticker,
        "concept": r.concept,
        "event_time": period,
        "window_days": int(r.lag_days),
        "n_versions": int(r.n_filings),
    })

with open(os.path.join(OUT, "chunks.jsonl"), "w", encoding="utf-8") as fh:
    for c in chunks:
        fh.write(json.dumps(c, ensure_ascii=False) + "\n")
with open(os.path.join(OUT, "queries.jsonl"), "w", encoding="utf-8") as fh:
    for q in queries:
        fh.write(json.dumps(q, ensure_ascii=False) + "\n")

print()
print("chunks :", len(chunks))
print("queries:", len(queries), "(skipped %d)" % skipped)
print("tickers:", len({c["ticker"] for c in chunks}))

# ---------------------------------------------------------------- leak guard
# Word-boundary matching: a substring test flagged 148 false positives because
# "fy" matched inside "Qualifying".
FORM = re.compile(r"\b(?:10-K|10-Q|8-K|20-F|fiscal|FY|filed|accession|deprecated|"
                  r"restated|amended|as of)\b", re.I)
n_date = sum(1 for c in chunks if _ISODATE.findall(c["text"]) != [c["event_time"]])
n_year = sum(1 for c in chunks if _YEAR.search(_ISODATE.sub("", c["text"])))
n_form = sum(1 for c in chunks if FORM.search(c["text"]))
n_self = sum(1 for c in chunks if c["avail_time"] in c["text"])
print()
print("LEAK GUARD (all must be 0)")
print("   date other than event_time :", n_date)
print("   stray year                 :", n_year)
print("   filing/form vocabulary     :", n_form)
print("   own avail_time in text     :", n_self)
if max(n_date, n_year, n_form, n_self) > 0:
    print("   !! CORPUS IS CONTAMINATED -- do not run the experiment on it")
    for c in chunks:
        if _ISODATE.findall(c["text"]) != [c["event_time"]] or FORM.search(c["text"]):
            print("   e.g.", c["text"][:120])
            break

print()
print("=== sample ===")
for c in chunks[:2]:
    print(json.dumps(c, ensure_ascii=False, indent=1))
print(json.dumps(queries[0], ensure_ascii=False, indent=1))
