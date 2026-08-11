# two-clocks

> A financial fact carries two clocks. Every retrieval system we tested encodes one.

## The gap

A financial fact has two independent timestamps:

| | | |
|---|---|---|
| **event time** | the period it is about | period ended 2009-09-26 |
| **availability time** | when it first became knowable | filed 2009-10-27 |

The same figure is restated in later filings under the **same event time** but a
**different availability time** — AAPL's FY2009 total assets were first disclosed
as 53.851 B and later restated to 47.501 B, 90 days apart. An `as-of` query at
2009-12-01 must return the first; at 2010-03-01, the second.

Synthetic benchmarks cannot exhibit this. BabiLong's loader keeps *"relative
order of facts intact"* while shuffling noise, so text order **is** story order
**is** availability order. TDBench describes itself as `uni-temporal`. TEMPO's
schema has no timestamp field at all — its documents are `{id, content}` and
temporal relevance is an LLM judgement.

The two failure modes are not equally severe:

- uni-temporal failure → retrieves temporally mismatched evidence → answer may be wrong
- **bitemporal failure → uses information not yet knowable → look-ahead bias → the entire conclusion is void**

## Contributions

**1. A structural blind spot in the evaluation paradigm.** Every existing
temporal retrieval benchmark encodes one clock. The assumption is an artifact of
synthetic corpus construction, and it hides a class of error that invalidates
conclusions rather than merely degrading them.

**2. An impossibility result with a closed form.** For any single linear order,
the 2-D `(event, availability)` state is many-to-one, so some candidate pair is
unresolvable. For Q-RAG's `rho_t`, `P_collide = 1 − 18·Δi/(L−1)`, verified
bit-exact against its RoPE layer and, with measured Δi, on the real corpus.
Version spacing follows `E|a_j − a_i| = (k+1)P/3` with `P = 364` days.

**3. The benchmark.** 165,731 real collision pairs from SEC EDGAR — statutory,
tamper-proof timestamps, `avail_time = max(filingDate, acceptanceDate)`.

**4. A negative result with evidence.** Five distinct method angles were
attempted and each was refuted. They converge on one diagnosis: the required
information is not in the input at all. This is reported as a finding, not
omitted — it explains why the paper is benchmark-and-theory rather than method.

## Results

Red line 0.6249 (value-channel ceiling, GroupKFold by concept). Chance 0.5000.

**E1 — six systems, all fail on the as-of axis** (ordered by event time):

| system | relative-only | absolute-event | absolute-avail | dual-clock |
|---|---|---|---|---|
| BM25 | 0.495 | 0.497 | 0.751 | 0.730 |
| GTE-base | 0.532 | 0.526 | 0.981 | 0.947 |
| E5-base | 0.561 | 0.536 | 0.989 | 0.949 |
| gte-multilingual | 0.535 | 0.543 | 0.991 | 0.953 |
| **Q-RAG (BabiLong QA3)** | **0.523** | 0.517 | **0.996** | 0.941 |
| **RoMem continuous phase** | **0.530** | — | **1.000** | 1.000 |

The last two rows carry the weight. Q-RAG's checkpoint is the only released one
with `positions_processor: relative`, i.e. the only one where `rho_t` was
actually trained; it is state-of-the-art on BabiLong QA3 (three-hop *temporal*
reasoning). On the as-of axis it scores 0.523 — indistinguishable from BM25,
which has no positional mechanism at all. The same model reaches 0.996 when
availability is supplied. **The failure is not capability; it is a missing axis.**

RoMem rotates by a **continuous** angle with a learnable frequency base, so the
19-slot truncation cannot apply — and it fails identically. **The failure is
dimensional, not a matter of resolution.**

**E3 — no single ordering supports both axes:**

| arm | ordering | task A (as-of) | task B (period) |
|---|---|---|---|
| relative-only | by event | **0.490** | 0.638 |
| relative-only | by filing | 0.850 | **0.486** |
| dual-clock | either | 0.84–0.87 | 0.63 |

**E2 — the closed form predicts the corpus.** With measured Δi: predicted
0.398/0.623/0.732 against measured 0.455/0.704/0.688 at L=50/200/1000.

**E4/E5/E6 — the method line, refuted three ways.** No length-extrapolation gap
(all arms flat to L=1000); no Pareto improvement from capacity reallocation; the
collision predicate has no selective power (gap −0.0065). See `RESULTS.md`.

## Quick start

```bash
python src/pull_companyfacts.py --tickers-file data/top700.txt   # SEC XBRL, resumable
python src/fetch_acceptance.py                                   # availability map, resumable
python src/build_bench.py                                        # corpus, ~10 s
python src/position.py                                           # verify the closed form
python src/audit/phase0_preregistered.py                         # pre-registered Phase-0
```

`src/position.py` drives Q-RAG's relative position encoding **standalone** — the
`relative-only` arm needs no reproduction of its training. Install the two
vendored deps with `--no-deps`; without it pip pulls the entire CUDA tree
(4.6 GB measured, vs 876 KB).

## Data

```
data/chunks.jsonl    331,462   id / text / ticker / concept / event_time / avail_time / value
data/queries.jsonl   165,731   query / as_of / gold_id / distractor_id / window_days
data/sample/             500   committed subset for smoke tests
669 tickers, candidate pool = top 700 by market cap in SEC's company_tickers.json
```

Full corpus is gitignored — L2 derived data, rebuilt in seconds. Chunk text
carries **event time only**.

### Construction hazards worth knowing

**SEC labels embed `(Deprecated YYYY-MM-DD)`.** A deprecation date bounds when a
filing using that tag could exist — it leaks the availability clock. The first
build had 1,532 contaminated chunks, 5 printing their own `avail_time` verbatim.

**Leak checks must use word boundaries.** A substring test flagged 148 false
positives (`fy` inside `Qualifying`) and nearly masked the real problem.

**`filed` is not availability.** EDGAR accepted one document 36 days *after* its
legal filing date (ABT `0001104659-10-033097`). Labelling by `filed` alone bakes
look-ahead bias into the gold labels. Hence `max(filingDate, acceptanceDate)`.

## Phase-0 (pre-registered)

| # | precondition | result |
|---|---|---|
| ① | collisions exist in sufficient number | 165,731 pairs; 40-pair manual sample pending review |
| ② | no side channel recovers availability | 0.5017 |
| ③ | filing time = true availability | n=136 across 2007–2026, 1 look-ahead case → fixed by `max()` |
| ④ | causal lever exists | relative-only degenerate 1.0000; dual-clock rule 1.0000 |
| ⑤ | no lexical shortcut | TF-IDF raw 0.504 / masked 0.501 |
| ⑥ | learnable floor exists | dual-clock 0.9997 vs relative 0.4997 |

**Pre-registered interval**: `relative-only ∈ [0.50, 0.62]`. Held at 7.8× the
data. Exceeding it means an undiscovered leak — investigate, do not celebrate.

`dual-clock` is a **reference upper bound, not a proposed method**. It shows the
task is solvable and that failure comes from representation, not difficulty.

## Provenance

- Corpus: SEC EDGAR XBRL companyfacts + submissions (684 companies cached)
- `vendor/qrag/`: snapshot of [griver/Q-RAG](https://github.com/griver/Q-RAG)
- Q-RAG checkpoint: `Q-RAG/qrag-ft-contriever-on-babilong_qa3` (the only one with
  `positions_processor: relative`)
- RoMem mechanism reimplemented from `romem/kge/model/romem_chronor.py`
  ([Tencent/RoMem](https://github.com/Tencent/RoMem)) — the mechanism, not the
  full KG system

## Status

Phase-0 closed except the manual sample. E1–E6 complete. The method line is
closed with five documented refutations. Remaining: paper write-up.
