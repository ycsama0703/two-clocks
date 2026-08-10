# Agent onboarding — bitemporal-bench

Read this before touching anything. It is written for an AI agent picking the
project up cold. `README.md` explains *what the research is*; this file explains
*how not to break it*.

---

## 1. Where the project actually stands

**Phase-0 is essentially closed. The main experiment has never been run.**
The core claim — that two-clock collision degrades as-of retrieval for real
systems — currently has **zero empirical support**. Everything verified so far
establishes that the *setup is sound*, not that the *hypothesis is true*.

Do not describe this project as having a finding. It has a benchmark and a
prediction.

---

## 2. Three disciplines that override convenience

**① Never relax a pre-registered threshold.**

```
relative-only  ∈ [0.50, 0.62]     ← written down BEFORE the experiment
   0.50 = zero positional information (Phase-0 items 2/4/6)
   0.62 = value-channel ceiling, measured ON THE ACTUAL CORPUS (v2, n=21,268):
            GroupKFold by concept  0.6128 (+/-0.0228)  <- the red line
            GroupKFold by ticker   0.5978 (+/-0.0266)  <- stricter variant
```

If a run exceeds 0.62, that is **not** a good result — it means an undiscovered
leak. Stop and investigate. Do not rationalise it.

> **Correction, logged 2026-08-10.** The ceiling was first measured as 0.627 on a
> *larger* set (25,574 pairs, no `n_filings` filter) than the corpus actually
> shipped (20,392 pairs, k∈{2,3}). Re-measured on the real corpus it is 0.6162.
> The pre-registered bound 0.62 happens to survive, but it survived by luck —
> always measure the ceiling on the exact set the experiment will run on.
> Use the *by-concept* number as the red line: it is the looser of the two, so
> exceeding it is unambiguous evidence of leakage rather than a grouping artefact.

**② `dual-clock ≈ 0.99` is a reference upper bound, NOT our method.**

It exists to prove the task is solvable and that failure comes from
representation rather than difficulty. The moment it is presented as a
contribution, the reviewer question "why not just add the filing date?" becomes
fatal — and the honest answer is "you can, easily".

**③ Distinguish three epistemic states, never collapse them.**

| state | meaning |
|---|---|
| **confirmed** | read the code / measured the data |
| **unfalsified** | searched, found no near neighbour, did not exhaust |
| **owed** | not checked at all |

`docs/design.md` labels every claim with one of these. Preserve the labels. The
project has already had one incident where "searches returned nothing" was
treated as "novel" — that is exactly the error this taxonomy prevents.

---

## 3. Environment

Everything runs on **luyao4** (lab server, via jump host). All of it is **CPU**;
no GPU is needed anywhere in Phase-0 or the main experiment.

```bash
# Connect — MUST use the Windows OpenSSH binary, not Git Bash's
C:/Windows/System32/OpenSSH/ssh.exe luyao4 "command"

# Python: reuse alphagap's venv (has torch, transformers, sklearn, pandas)
~/workspace/projects/alphagap/.venv/bin/python

# Project root
~/workspace/projects/bitemporal-bench/
```

`src/position.py` self-inserts `vendor/deps` and `vendor/qrag` into `sys.path`,
so it runs with no PYTHONPATH juggling.

**Server constraints**: disk is at 88% (107 GB free) — do not stage large
downloads. Timezone is WIB (Beijing −1) — log timestamps will look an hour off.

---

## 4. File map

```
src/build_bench.py            corpus generator, ~10 s, reads ../repairable-experience/data/edgar/companyfacts
src/position.py               standalone driver for Q-RAG's relative position encoding
                              + relative_positions() + collision_rate() closed form
src/audit/
  phase0_preregistered.py     pre-registered Phase-0 items 2, 4, 5, 6
  phase0_item3.py             item 3 — SEC acceptanceDateTime cross-check (needs network)
  level1_grouped.py           the 0.62 floor (GroupKFold)
  level0_leakage.py           metadata leak channels
  level1_value_channel.py     value-channel ceiling, ungrouped
  rebuild_series.py           full a_i series from companyfacts, validates (k+1)P/3
  dualclock_audit2.py         distribution parameters (P=364, reporting lag, lifetime)
data/sample/                  500 pairs, committed — use for smoke tests
data/{chunks,queries}.jsonl   full corpus, gitignored, rebuild with build_bench.py
data/manual_review.md         40-pair sample awaiting HUMAN review (Phase-0 item ①)
docs/design.md                full validation record with epistemic labels
experiments/                  empty — the main experiment goes here
```

---

## 5. Traps already paid for — do not re-pay

| trap | what happened | rule |
|---|---|---|
| `pip install --target` without `--no-deps` | pulled the entire CUDA tree, **4.6 GB** onto an 88%-full disk | always `--no-deps` for the two vendored packages |
| leak check by substring | `"fy"` matched inside `Qualifying` → 148 false positives, nearly masked 1,532 real ones | **word boundaries** in every leak regex |
| `max_tokens` too small for JSON output | the router's model emits reasoning tokens counted against `completion_tokens`; 800 was consumed entirely, `finish_reason=length`, empty content on 3 of 4 cards | budget ≥ 3000 for any JSON-producing call |
| circular validation | `P=364` was read off the k=2 data, then "verified" against k=2 | only **k=3** (predicted 485.33, measured 485) is an independent check |
| ungrouped cross-validation | same concept in train and test → ceiling inflated by **+0.039** | `GroupKFold` by concept, or by ticker for the strict number |
| SEC label metadata | labels embed `(Deprecated YYYY-MM-DD)`; a deprecation date bounds when a filing could exist → leaks availability. 1,532 chunks affected, 5 printed their own `avail_time` | `humanise()` scrubs it; re-check after any label change |
| editing remote code inline | multi-level quoting through ssh rewrites `\n`, `\f`, `+` | write a `.py` patch locally → `scp` → run it remotely |

---

## 6. What an agent may and may not do

**May** — and should do without asking, once a direction is set: literature
search, reading code, data audits, building corpora, deriving and verifying
closed forms, writing documentation. Run to a substantive conclusion before
reporting; do not stop for approval at every step.

**May not**:

- **Run the main experiment.** The owner runs TEST personally. His stated reason:
  most ideas die, and the value is in phenomena that surface *during* the
  experiment — delegating it loses exactly that. Prepare data, environments and
  scaffolding; do not execute the comparison and do not report its outcome.
- **Create or push to remote repos**, send email, or change production config
  (`alphagap` cron runs at 07:00 WIB off shared code).

---

## 7. If you are asked "what's next"

1. Human review of `data/manual_review.md` (Phase-0 item ①) — the last open item
2. Minimal go/no-go: GTE-base × 4 time inputs × L=200 × 500 pairs, check whether
   `relative-only` lands inside `[0.50, 0.62]`
3. Only if it does: E1 baseline suite (BM25 / GTE / E5 / Q-RAG ρ_t / RoMem),
   E2 closed-form sweep over `L ∈ {50, 200, 1000}`, E3 ordering ablation
   (by event time vs by filing time)

E1 decides the paper's weight: **all four baselines degrade → a boundary of a
class of mechanisms; only Q-RAG degrades → one implementation's bug.**

---

## 8. Two debts still open

- **`S2_API_KEY` is empty** in alphagap's `.env`. The novelty probe therefore
  ranks hits by a citation count that is always 0 — literature checks are less
  reliable than they look. Only the owner can obtain the key.
- **`chunk` granularity is a first-version decision**, not a validated one. One
  XBRL fact = one chunk. Whether the two versions of a fact land close enough in
  a real chunking scheme to actually collide (small `Δi`) is **assumed, not
  verified** — it cannot be checked from XBRL data alone.
