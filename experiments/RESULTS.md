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
