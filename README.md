# two-clocks

> A financial fact carries two clocks. Every retrieval system we tested encodes one.
>
> The first **bitemporal** retrieval benchmark. Existing long-context and temporal
> retrieval benchmarks are **uni-temporal**: they assume text order carries the
> complete temporal signal. Real corpora with version histories have two clocks
> that can diverge, and no single ordering can encode both.

## The gap

A financial fact carries two independent timestamps:

| | | |
|---|---|---|
| **event time** | when the fact is about | period ended 2009-09-26 |
| **availability time** | when it first became knowable | filed 2009-10-27 |

The same figure is restated in later filings under the **same event time** but a
**different availability time** — AAPL's total assets for FY2009 were first
disclosed as 53.851 B and later restated to 47.501 B, 90 days apart. An `as-of`
query at 2009-12-01 must return the first; at 2010-03-01, the second.

Synthetic benchmarks cannot exhibit this. In BabiLong the two clocks are forced
into alignment — its loader keeps *"relative order of facts intact"* while
shuffling noise, so text order **is** story order **is** availability order. TDBench
describes itself as `uni-temporal`. TEMPO's schema has no timestamp field at all;
its documents are `{id, content}` and temporal relevance is an LLM judgement.

The two failure modes are not equally severe:

- uni-temporal failure → retrieves temporally mismatched evidence → answer may be wrong
- **bitemporal failure → uses information that was not yet knowable → look-ahead bias → the entire conclusion is void**

## Contributions

1. **A structural blind spot in the evaluation paradigm.** Every existing temporal
   retrieval benchmark encodes one clock. We show the assumption is an artifact of
   synthetic corpus construction, and that it hides a class of error that
   invalidates conclusions rather than merely degrading them.
2. **An impossibility result with a closed-form degradation.** For any single linear
   order σ, the 2-D `(event, availability)` state is many-to-one under σ, so some
   candidate pair is unresolvable. For Q-RAG's `ρ_t` specifically,
   `P_collide = 1 − 18·Δi/(L−1)`, verified **bit-exact** against its RoPE layer.
   Version spacing follows `E|a_j − a_i| = (k+1)P/3` with `P = 364` days (52-week
   fiscal year); predicted 485.33 for k=3, measured 485.
3. **The benchmark.** 20,392 real collision pairs from SEC EDGAR — statutory,
   tamper-proof timestamps. Not reproducible elsewhere: Wikipedia edit history has
   no legally meaningful availability time, news has no revision chain for the same
   fact, synthetic data has no real distribution.

## Quick start

```bash
python src/build_bench.py                 # rebuild corpus from companyfacts, ~10 s
python src/position.py                    # verify the collision closed form
python src/audit/phase0_preregistered.py  # pre-registered Phase-0 items 2,4,5,6
```

`src/position.py` drives Q-RAG's relative position encoding **standalone** — the
`relative-only` arm needs no reproduction of its training:

```python
emb = your_encoder(chunk_texts)                    # any encoder
pos = relative_positions(len(chunks), discovered)
out = apply_positions(make_rope(dim), emb, pos)
```

Install the two vendored deps with `--no-deps`; without it pip pulls the entire
CUDA tree (4.6 GB measured, vs 876 KB).

## Data

```
data/chunks.jsonl    40,784   id / text / ticker / concept / event_time / avail_time / value
data/queries.jsonl   20,392   query / as_of / gold_id / distractor_id / window_days
data/sample/            500   committed subset for smoke tests
```

Full corpus is **gitignored** — it is L2 derived data, rebuilt in 10 s by
`build_bench.py` from SEC companyfacts. Only the generator and the sample ship.

Chunk text carries **event time only**:
`"{ticker} reported {label} of {value} {unit} for the period ended {period_end}."`

### Construction hazard worth knowing

SEC concept labels embed `(Deprecated YYYY-MM-DD)` markers. A deprecation date
bounds when a filing using that tag could exist — it leaks the availability clock.
The first build had 1,532 contaminated chunks (3.8%), 5 of which printed their own
`avail_time` verbatim. Scrubbed in `humanise()`. **Leak checks must use word
boundaries**: a substring test flagged 148 false positives (`fy` inside
`Qualifying`) and nearly masked the real problem.

## Phase-0 status (pre-registered)

| # | Precondition | Result |
|---|---|---|
| ① high | collisions exist in sufficient number | 20,392 pairs; 40-pair manual sample pending review |
| ② high | no side channel recovers availability | rule recovery 0.5031 |
| ③ high | filing time = true availability, not DB ingestion | n=59, `filed` ≡ SEC `filingDate`, **0 look-ahead** |
| ④ low | causal lever exists | relative-only degenerate (1.0000); dual-clock rule 1.0000 |
| ⑤ med | no lexical shortcut | TF-IDF raw 0.509 / masked 0.506 |
| ⑥ med | learnable floor exists | dual-clock 0.9987 vs relative 0.5014 |

**Pre-registered interval for the main experiment**: `relative-only ∈ [0.50, 0.62]`.
Lower bound = zero positional information. Upper bound = the value channel ceiling
(GroupKFold by concept). **Exceeding 0.62 means an undiscovered leak — stop and
investigate rather than proceed.**

`dual-clock ≈ 0.99` is a **reference upper bound, not a proposed method**. It exists
to show the task is solvable and that failure comes from representation, not difficulty.

## Provenance

- Corpus: SEC EDGAR XBRL companyfacts (63 companies cached, 50 in the benchmark)
- `vendor/qrag/`: snapshot of [griver/Q-RAG](https://github.com/griver/Q-RAG),
  *Q-RAG: Long Context Multi-step Retrieval via Value-based Embedder*
- Revision registry derived from `repairable-experience`

## Status

Phase-0 essentially closed. **The main experiment has not been run** — the core
claim (that collision degrades as-of retrieval for real systems) currently has
zero empirical support. See `docs/design.md` for the full validation record,
including what is confirmed, what is unfalsified, and what is still owed.
