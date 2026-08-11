# Agent onboarding — two-clocks

Read this before touching anything. It is written for an AI agent picking the
project up cold. `README.md` explains *what the research is*; this file explains
*how not to break it*, and *what has already been tried and refuted*.

---

## 1. Where the project actually stands

Phase-0 is closed except the 40-pair manual review. **E1–E6 are complete.** The
core claim now has empirical support across six retrieval systems.

**The method line is closed.** Five distinct angles were attempted and each was
refuted by evidence (section 7). Do not re-propose them.

The paper is **benchmark + theory + a documented negative result**. It does not
propose a method, and that is a finding rather than a gap.

---

## 2. Three disciplines that override convenience

**① Never relax a pre-registered threshold.**

```
relative-only ∈ [0.50, 0.62]
   0.50 = zero positional information (Phase-0 items 2/4/6)
   0.62 = value-channel ceiling, measured ON THE SHIPPED CORPUS (v3, n=165,731):
            GroupKFold by concept  0.6249   <- the red line
            GroupKFold by ticker   0.6257
```

Exceeding the line is **not** a good result — it means an undiscovered leak.
Stop and investigate. It has already caught one real bug: an early E1 run hit
0.712 because the pool was tie-broken on `avail_time`, handing over the answer.

Always measure the ceiling on the exact set the experiment will run on. It was
once measured on a larger set (0.627 on 25,574 pairs) than the corpus shipped
(20,392); the bound survived by luck.

**② `dual-clock` is a reference upper bound, NOT our method.** It reaches
0.94–1.00 by being handed the availability ordering, i.e. half the answer. The
moment it is written as a contribution, "why not just add the filing date?"
becomes fatal — and the honest answer is "you can, easily".

**③ Distinguish three epistemic states, never collapse them.**

| state | meaning |
|---|---|
| **confirmed** | read the code / measured the data |
| **unfalsified** | searched, found no near neighbour, did not exhaust |
| **owed** | not checked at all |

`docs/design.md` labels every claim. The project has already had one incident
where "searches returned nothing" was treated as "novel".

---

## 3. Environment

Everything runs on **luyao4** (lab server, via jump host), CPU only. A rented
RTX 4090 was used once for E1 (vast.ai instance 47421359, stopped, disk
preserved: `vastai start instance 47421359` restores it with the rebuilt Q-RAG
encoder and corpus in `/root/tc`).

```bash
# MUST use the Windows OpenSSH binary, not Git Bash's
C:/Windows/System32/OpenSSH/ssh.exe luyao4 "command"

# Python: reuse alphagap's venv (torch, transformers, sklearn, pandas)
~/workspace/projects/alphagap/.venv/bin/python

~/workspace/projects/two-clocks/
```

`src/position.py` self-inserts `vendor/deps` and `vendor/qrag` into `sys.path`.

**Server constraints**: disk at 88% (105 GB free). Timezone WIB (Beijing −1).

---

## 4. File map

```
src/pull_companyfacts.py      SEC XBRL puller, arbitrary ticker list, resumable
src/fetch_acceptance.py       availability map, sharded per company, resumable
src/build_bench.py            corpus generator, self-contained, ~10 s
src/position.py               standalone Q-RAG position encoding + closed form
src/qrag_encoder.py           rebuild Q-RAG's trained action tower from checkpoint
src/audit/                    Phase-0 items, ceiling, distribution parameters
experiments/e1_full.py        six systems x two orderings x five time inputs
experiments/e2_collision.py   closed form vs measured collision rate
experiments/e3_ordering.py    no single ordering supports both axes
experiments/e4_extrapolation.py   probe fitted at L=200, applied to L=1000
experiments/e5_capacity.py    capacity split sweep
experiments/e6_abstention.py  collision predicate as an abstention gate
experiments/RESULTS.md        every result, every failure, with diagnosis
data/manual_review.md         40-pair sample awaiting HUMAN review (Phase-0 ①)
docs/design.md                validation record with epistemic labels
```

---

## 5. Traps already paid for — do not re-pay

| trap | what happened | rule |
|---|---|---|
| `pgrep -f X` self-match | The waiting task's own command line contained `X`, so it matched itself and two processes waited on each other for **55 minutes**. Later `pkill -f "bash overnight.sh"` killed the shell running it (exit 127, zero output). Happened **twice in one night**, and it is documented in `luyao4-ops.md`. | Match by PID, or anchor the pattern so the querying command cannot match |
| hardcoded paths | `build_bench.py` still pointed at `~/repairable-experience/`, so it rebuilt from the OLD 63 companies while the acceptance map was new. **All steps returned EXIT=0 and produced a plausible 21,268 pairs.** Three scripts had the same defect. | Derive every path from `__file__` |
| inline heredoc over ssh | Quoting mangles `\n`, `+`, backticks. Cost two failed runs, the second immediately after quoting the rule forbidding it. | Write the patch locally, `scp`, then run it |
| smoke test passes, full run crashes | BM25 feature width = vocabulary size: even at 300 pairs, odd (2018) at 1500, breaking the RoPE half-split. Dense encoders are always 768 and could never surface it. | A smoke test validates the pipeline, not edge cases |
| `pip --target` without `--no-deps` | Pulled the entire CUDA tree, **4.6 GB** onto an 88%-full disk | Always `--no-deps` for the vendored packages |
| leak check by substring | `"fy"` matched inside `Qualifying` → 148 false positives, nearly masking 1,532 real ones | Word boundaries in every leak regex |
| `max_tokens` too small | The router's model emits reasoning tokens counted against `completion_tokens`; 800 was consumed entirely, empty content on 3 of 4 cards | Budget ≥ 3000 for any JSON-producing call |
| circular validation | `P=364` was read off the k=2 data, then "verified" against k=2 | Only k=3 (predicted 485.33, measured 485) is an independent check |
| ungrouped CV | Same concept in train and test inflated the ceiling by +0.039 | `GroupKFold` by concept |

**The meta-rule, which is worth more than any single entry above:** *too fast*
and *too quiet* are both alarms. A monitor silent for an hour on a 20-minute job,
and three steps finishing in 40 seconds when one had to read 2.1 GB, were the
only signals that anything was wrong. **Every exit code was zero.**

---

## 6. What an agent may and may not do

**May** — without asking, once a direction is set: literature search, reading
code, data audits, building corpora, deriving and verifying closed forms, writing
documentation. Run to a substantive conclusion before reporting.

**May not**:

- **Run the main experiment.** The owner runs TEST personally: most ideas die,
  and the value is in phenomena that surface *during* the run. Prepare data,
  environments and scaffolding; do not execute the comparison.
  (E1–E6 were run under an explicit instruction to proceed unattended.)
- **Create or push to remote repos**, send email, change production config
  (`alphagap` cron runs at 07:00 WIB off shared code), destroy rented instances,
  or force-push.

---

## 7. Five refuted method angles — do not re-propose

Each was attempted and killed by evidence. Re-proposing any of them without new
information wastes a cycle.

| # | angle | refuted by | reason |
|---|---|---|---|
| 1 | dual-clock phase decomposition | E3 | naive two-axis already 0.94; the oracle consumes the headroom |
| 2 | lattice-matched frequency design | literature | PeriodPatch / TimelyGPT / learnable-Fourier already pin bands to a known period |
| 3 | extrapolation irreparability | E4 | all arms flat to L=1000; the hypothesis conflated **sequence length** (Q-RAG's 1M→10M tokens) with **pool size** (candidate count) |
| 4 | capacity allocation | E5 | no Pareto improvement; confused **label entropy** (1 bit) with **representation capacity** (separating L positions) |
| 5 | abstention via collision predicate | E6 | gap −0.0065; the predicate selects an **always-true** condition, since E1 showed the positional channel is uninformative everywhere under event ordering |

**They converge on one diagnosis:** the information as-of eligibility requires is
not in the input at all. It cannot be recovered by better encoding (1, 2, 4),
exposed by extrapolation (3), or routed around by detecting its absence (5) —
because it is not sometimes missing, it is **always** missing. Any method
contribution must first put availability metadata back into the input, which is a
data-pipeline decision, not a modelling problem.

**Three of the five failed on a conceptual error rather than an experimental
surprise** (3, 4, 5). Before proposing a method angle, ask: *which variable does
this change, and was that variable previously a constant?*

---

## 8. Open items

- **Phase-0 ①**: `data/manual_review.md`, 40 pairs, needs human review
- **69 MB `acceptance.json` in git history**: no longer tracked, but `clone`
  still pulls it. Removing it needs `filter-repo` + force push (destructive)
- **`S2_API_KEY` empty** in alphagap's `.env` — the novelty probe ranks hits by a
  citation count that is always 0
- **RoMem is a mechanism reimplementation**, not the full KG system. Sufficient
  for the "can phase encoding escape" question; a reviewer wanting a full-system
  comparison would need more
