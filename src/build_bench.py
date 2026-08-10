# -*- coding: utf-8 -*-
"""Build the bitemporal retrieval benchmark corpus from SEC XBRL.  v2

v2 changes availability semantics:
    avail_time = max(filingDate, acceptanceDate)     (was: filingDate alone)

Phase-0 item 3 found EDGAR accepting a document 36 days AFTER its legal filing
date (ABT 0001104659-10-033097). Labelling by `filed` alone put look-ahead bias
into the gold labels -- precisely the error class this benchmark exists to
detect. 1,657 fact entries shift under max().

v2 is also self-contained: collision pairs are computed here from companyfacts
rather than read from revisions.csv, which was derived under the old semantics.

Design decisions (see docs/design.md):
  chunk    = one XBRL fact, templated text, carries ONLY period_end.
             fy / fp / form / accn are NEVER emitted (fy alone separates the two
             versions in 97.2% of pairs).
  ordering = not chosen here; both clocks are stored, the evaluator sorts.
  pool L   = not chosen here; an experimental variable.
"""
import glob
import json
import os
import re
from collections import defaultdict
from datetime import date, timedelta

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CF = os.path.join(OUT, "companyfacts", "*.json")
ACC = os.path.join(OUT, "acceptance.json")

MIN_WINDOW = 30          # days between the two disclosures
MIN_SRD = 0.01           # symmetric relative difference
REP_LAG = (0, 400)       # period end -> first disclosure
KS = (2, 3)              # closed form (k+1)P/3 holds here

acc = json.load(open(ACC))
print("acceptance map:", len(acc))

_DEPRECATED = re.compile(r"\s*\(\s*deprecated[^)]*\)", re.I)
_ISODATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_YEAR = re.compile(r"\b(?:19|20)\d{2}\b")
label_of = {}


def humanise(concept):
    """SEC label, scrubbed of dates. `(Deprecated 2018-01-31)` markers bound when
    a filing using the tag could exist, i.e. they leak the availability clock."""
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
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return "{:,}".format(v) if isinstance(v, int) else str(v)


UNIT_WORD = {"USD": "USD", "shares": "shares", "USD/shares": "USD per share",
             "pure": "", "Rate": ""}
D = lambda s: date(*map(int, s.split("-")))

# ---------------------------------------------------------------- collect
series = defaultdict(dict)          # (ticker, concept, unit, start, end) -> {avail: val}
shifted = 0
for path in sorted(glob.glob(CF)):
    ticker = os.path.basename(path)[:-5]
    try:
        doc = json.load(open(path, encoding="utf-8"))
    except Exception:
        continue
    for _, concepts in (doc.get("facts") or {}).items():
        for concept, cdata in concepts.items():
            lab = (cdata.get("label") or "").strip()
            if lab and concept not in label_of:
                label_of[concept] = lab
            for unit, entries in (cdata.get("units") or {}).items():
                for e in entries:
                    end, filed, val, an = (e.get("end"), e.get("filed"),
                                           e.get("val"), e.get("accn"))
                    if not end or not filed or val is None:
                        continue
                    eff = acc.get(an, filed)
                    if eff != filed:
                        shifted += 1
                    key = (ticker, concept, unit, e.get("start"), end)
                    series[key].setdefault(eff, val)     # first value at that date

print("series:", len(series), " entries shifted by max():", shifted)

# ---------------------------------------------------------------- pairs
chunks, queries = [], []
cid = 0
kept = defaultdict(int)
for (ticker, concept, unit, start, end), versions in series.items():
    if len(versions) < 2:
        continue
    items = sorted(versions.items())                     # by effective availability
    if len(items) not in KS:
        continue
    (a1, v1), (a2, v2) = items[0], items[1]
    if v1 == v2 or v1 == 0:
        continue
    den = max(abs(v1), abs(v2))
    if den == 0 or abs(v2 - v1) / den < MIN_SRD:
        continue
    rep_lag = (D(a1) - D(end)).days
    if not (REP_LAG[0] <= rep_lag <= REP_LAG[1]):
        continue
    window = (D(a2) - D(a1)).days
    if window < MIN_WINDOW:
        continue

    lab = humanise(concept)
    uw = UNIT_WORD.get(unit, unit or "")
    ids = []
    for val, av in ((v1, a1), (v2, a2)):
        cid += 1
        ids.append("c%07d" % cid)
        chunks.append({
            "id": ids[-1],
            "text": "%s reported %s of %s%s for the period ended %s." % (
                ticker, lab, fmt(val), (" " + uw) if uw else "", end),
            "ticker": ticker, "concept": concept,
            "event_time": end, "avail_time": av, "value": float(val),
        })
    as_of = (D(a1) + timedelta(days=window // 2)).isoformat()
    queries.append({
        "id": "q%07d" % (len(queries) + 1),
        "query": "What was %s's %s for the period ended %s?" % (ticker, lab, end),
        "as_of": as_of, "gold_id": ids[0], "distractor_id": ids[1],
        "ticker": ticker, "concept": concept, "event_time": end,
        "window_days": window, "n_versions": len(items),
    })
    kept[len(items)] += 1

os.makedirs(OUT, exist_ok=True)
for name, rows in (("chunks", chunks), ("queries", queries)):
    with open(os.path.join(OUT, name + ".jsonl"), "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

print()
print("chunks : %d    queries: %d" % (len(chunks), len(queries)))
print("by k   :", dict(kept))
print("tickers:", len({c["ticker"] for c in chunks}))

# ---------------------------------------------------------------- guards
FORM = re.compile(r"\b(?:10-K|10-Q|8-K|20-F|fiscal|FY|filed|accession|deprecated|"
                  r"restated|amended|as of)\b", re.I)
g = {c["id"]: c for c in chunks}
n_date = sum(1 for c in chunks if _ISODATE.findall(c["text"]) != [c["event_time"]])
n_self = sum(1 for c in chunks if c["avail_time"] in c["text"])
inv = [sum(1 for q in queries if g[q["gold_id"]]["event_time"] == g[q["distractor_id"]]["event_time"]),
       sum(1 for q in queries if g[q["gold_id"]]["avail_time"] != g[q["distractor_id"]]["avail_time"]),
       sum(1 for q in queries if g[q["gold_id"]]["avail_time"] <= q["as_of"] < g[q["distractor_id"]]["avail_time"]),
       sum(1 for q in queries if g[q["gold_id"]]["text"] != g[q["distractor_id"]]["text"])]
print()
print("LEAK GUARD   date!=event_time: %d   own avail_time: %d" % (n_date, n_self))
print("COLLISION INVARIANTS (all must equal %d): %s" % (len(queries), inv))
