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
