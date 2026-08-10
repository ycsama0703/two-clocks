# E1 smoke — minimal go/no-go

`experiments/e1_smoke.py`, 2026-08-10. GTE-base, L=200, ordering by event time,
500 pairs, logistic probe on the A-vs-B embedding difference, GroupKFold by concept.

| time input | accuracy | |
|---|---|---|
| no-time | 0.5020 (±0.0431) | chance |
| **relative-only** | **0.4920** (±0.0204) | **inside pre-registered [0.50, 0.62]** |
| absolute (pool index) | 0.5020 (±0.0435) | chance |
| dual-clock | 0.9200 (±0.0245) | +43 pp |

Red line 0.6128 (value-channel ceiling). Chance 0.5000. **PASS.**

## The red line caught the experimenter first

The first run gave `relative-only = 0.7120`, above the line. Cause was not the
data: the pool was sorted `(event_time, avail_time)`, so availability was the
tie-break and gold always preceded distractor. `id` would have leaked equally —
ids are assigned in generation order. Fixed by shuffling before a stable sort on
event_time alone.

Without the pre-registered bound, 0.712 would have read as "the positional
channel carries some signal" and been accepted.

## Notes for the full E1

- `absolute` here is the **pool index**, not an absolute timestamp. The full run
  must split it into absolute-event-time and absolute-availability-time; the
  latter trivially solves the task and is not a fair comparison.
- `no-time` at 0.502 is well below the 0.6128 ceiling measured with hand-built
  numeric features. GTE embeddings do not encode magnitude well, so the real
  floor is lower than the theoretical one and the effect size is larger.
- Any representation encoding only the event axis fails regardless of whether it
  is relative or absolute — the two candidates share an event time exactly.


# E2 — closed form vs the real corpus

`experiments/e2_collision.py`. 500 queries, pool from the same ticker, ordered by
event time with a neutral tie-break, rho_t truncated to int32 as RoPE does.

| L | usable | median delta_i | predicted (delta_i=1) | predicted (measured delta_i) | measured |
|---|---|---|---|---|---|
| 50 | 499 | 1 | 0.633 | 0.453 | **0.455** |
| 200 | 480 | 2 | 0.910 | 0.688 | **0.704** |
| 1000 | 225 | 11 | 0.982 | 0.735 | **0.680** |

**The closed form holds when delta_i is measured rather than assumed** (error
0.002 at L=50, 0.016 at L=200). L=1000 deviates more (0.055) on only 225 usable
pools -- few tickers have 1000 chunks.

**Correction.** The repeatedly quoted "98.2% at L=1000" is the delta_i=1 special
case. Only 32.9% of pairs are actually adjacent; other chunks sharing the event
time fall between them after the shuffle (median delta_i = 2 at L=200, 11 at
L=1000, max 30). On the real corpus the collision rate is 0.455-0.704, not
0.633-0.982. Quote the measured numbers, not the adjacent-pair bound.

Note: task accuracy is deliberately not reported here. Gold and distractor share
an event time exactly, so under a neutral tie-break their order is random whether
they collide or not -- accuracy is flat in L by construction.


# E3 - no single ordering supports both axes

`experiments/e3_ordering.py`. GTE-base, L=200, 400 pairs per task.

- Task A (as-of): candidates share event_time, differ in avail_time.
- Task B (period): candidates share avail_time (same filing, comparative
  reporting), differ in event_time.
- The query carries a time anchor (as_of for A, target period for B), inserted
  into the same ordering; candidate positions are given relative to it.

| arm | ordering | task A | task B |
|---|---|---|---|
| relative-only | by event time | 0.497 | **0.679** |
| relative-only | by filing time | **0.910** | 0.440 |
| dual-clock | by event time | 0.905 | 0.684 |
| dual-clock | by filing time | 0.912 | 0.701 |

**Every single ordering is blind on one of the two tasks; the dual-clock
representation is not.** relative-only crosses over cleanly: ordering by event
time solves period matching and fails as-of; ordering by filing time does the
reverse. This is the impossibility result in empirical form.

## Three failed runs before this one, all methodological

1. **No query in the features.** The probe saw only the candidate embedding
   difference. Task A does not need the query (its rule is query-independent),
   task B does, since the target period is drawn at random. Task B sat at chance
   in all four cells.
2. **Anchor position double-indexed.** iq is the anchor's RANK on an axis, so its
   position is rho[iq]; the code used r[iq] where r = rho[order], which returns
   the position of an unrelated item.
3. **A linear probe cannot express a distance test.** Task A's rule is a sign
   test (is availability before as_of?), linear in the raw offsets. Task B's rule
   is "whichever offset is smaller in absolute value", which is not. Without an
   explicit absolute-offset feature, task B stayed at chance regardless of
   ordering.

Failure 3 is the dangerous one: it yields a plausible null that appears to
support an even stronger claim than the truth - "no ordering supports period
matching" - when in fact ordering by event time supports it fine.


# v3 rebuild at 669-company scale (2026-08-11)

Corpus rebuilt from 684 SEC companyfacts (candidate pool = top 700 by market cap
in SEC's `company_tickers.json`; 39 ADRs excluded automatically because they file
20-F and publish no XBRL companyfacts). Everything below was re-measured on the
new corpus; nothing was re-tuned.

|  | v2 (62 tickers) | v3 (669 tickers) |
|---|---|---|
| queries / chunks | 21,268 / 42,536 | **165,731 / 331,462** |
| ceiling by concept (red line) | 0.6128 | **0.6249** |
| ceiling by ticker | 0.5978 | 0.6257 |
| Phase-0 [4] causal lever | 1.0000 / 1.0000 | 1.0000 / 1.0000 |
| Phase-0 [2] side channel | 0.5031 | 0.5017 |
| Phase-0 [6] dual / relative | 1.0000 / 0.5065 | 0.9997 / 0.4997 |
| Phase-0 [5] raw / masked | 0.508 / 0.509 | 0.504 / 0.501 |
| collision window median | 364 | 364 |
| k=2 within +-7d of 364 | 91.8% | 89.0% (n=126,571) |
| reporting lag median | 34 | 37 |

## E1 smoke — pre-registered check PASSES at 7.8x the data

| time input | v2 | v3 |
|---|---|---|
| no-time | 0.5020 | 0.5320 |
| **relative-only** | 0.4920 | **0.5180** (inside [0.50, 0.62]) |
| absolute (pool index) | 0.5020 | 0.5960 |
| dual-clock | 0.9200 | 0.9460 |

Effect size dual-clock minus relative-only: 42.8 pp in v2, 42.8 pp in v3 -
unchanged. `absolute` rose from 0.502 to 0.596, but the ceiling rose too
(0.6128 -> 0.6249), so it stays below the red line and is still explainable by
the value channel rather than by positional information.

Phase-0 numbers all moved CLOSER to their theoretical values with 7.8x the
sample ([6] 0.5065 -> 0.4997, [5] 0.508 -> 0.504), which is what noise
convergence looks like.

## E2 — closed form still holds

| L | usable | median delta_i | predicted (measured delta_i) | measured |
|---|---|---|---|---|
| 50 | 499 | 1 | 0.398 | 0.429 |
| 200 | 474 | 3 | 0.623 | 0.639 |
| 1000 | 170 | 9 | 0.732 | 0.688 |

median delta_i rose (2 -> 3 at L=200, max 30 -> 68): with 669 companies a pool
drawn from one ticker holds more chunks sharing an event time, so more of them
fall between the pair.

## Two self-inflicted failures during this run, both logged as lessons

**A deadlock.** `overnight.sh` waited on `pgrep -f fetch_acceptance.py`, which
matched a *different* background task whose command line contained that string -
and that task was itself waiting for the fetch to end. They waited on each other
for 55 minutes. `luyao4-ops.md` documents exactly this trap ("pgrep -f matches
the querying command itself"); reading it was not enough to avoid it. Cleaning up
afterwards, `pkill -f "bash overnight.sh"` then killed the shell running it, for
the same reason.

**A silent wrong-data run.** `build_bench.py` still hardcoded
`CF = ~/repairable-experience/...`, so it rebuilt from the OLD 63 companies while
the acceptance map was the new 2,022,102 entries. All three steps returned
EXIT=0 and produced a plausible 21,268 pairs. Nothing failed. It was caught only
because two things looked wrong: E2's delta_i histogram was byte-identical to the
62-company run, and three steps finished in 40 seconds when one of them had to
read 2.1 GB.

**The transferable lesson is not the two specific traps.** It is that "too fast"
and "too quiet" are both alarms. A monitor that reported nothing for an hour on a
20-minute job, and a step that finished 30x faster than physically possible, were
the only signals that anything was wrong - the exit codes were all zero.
