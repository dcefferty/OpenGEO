# OpenGEO Competition Round Pre-Registration — v1 — 2026-10

Committed before any row is written to a results file for this corpus. Per
`preregistrations/README.md`, the git timestamp on this file is the evidence; a
pre-registration committed after collection starts is not a pre-registration.

## Why this round

H4 is the project's headline. Replacing vague claims with specific figures raised target
CPR by **+0.482, CI [+0.404, +0.563]** on corpus v0.4, and replicated at +0.473 on the
held-out split. Two facts about how that number was produced limit what it can tell a
practitioner:

- **The target is the only document that answers.** v0.4 was built that way on purpose
  (`METHODOLOGY.md` §9), so the treated target is the single answering document among six.
  Real pages almost always compete with other pages that also state the answer.
- **The treatment arm saturates.** Treatment CPR is 0.985, so the delta is mostly
  `1 − control` and reports headroom rather than efficacy (§9, "The ceiling discipline
  applies to the treatment arm too").

The README already says so in words: *"Against competitors that already state the answer,
expect a smaller gain. The direction is solid; the size is specific to the setup."* This
round measures the gain against such a competitor, instead of only saying that it differs.

Probe 3 of item 11 (`results/probes/2026-09-12-realtext-feasibility.md`) is the reason to
expect the competitor to bite. Raising the number of answering documents cost the
mid-range answerers 0.142 of citation rate, negative on all five engines, while
non-answering filler moved by 0.000. If a competitor takes citation slots from an
answering target, the treatment arm should come off the ceiling. The delta would then be
an estimate, where today it is a floor.

## Design

| | |
|---|---|
| Corpus | `corpus/corpus_competition.json`, sha `ae1a8844d11cb97f` |
| Built by | `corpus/build_corpus_competition.py` |
| Base | corpus v0.4, all 48 prompts; target `control` and `treatment` reused **verbatim** (loaded programmatically) |
| Prompts | 48, across 24 domains, 8 per target format — unchanged from v0.4 |
| Documents | 6 per prompt |
| Conditions | 4 — `control`, `treatment`, `control_comp`, `treatment_comp` |
| Models | the five-engine panel in `engine_weights.py`: `openai/gpt-5.4-mini`, `google/gemini-3-flash-preview`, `anthropic/claude-haiku-4.5`, `deepseek/deepseek-chat`, `x-ai/grok-4.3` (98.9% of measured gen-AI traffic) |
| Runs per cell | 24 |
| Temperature | 1.0 |
| Document order | randomized per run from a seeded hash, recorded every run |
| Total calls | 48 × 4 × 5 × 24 = **23,040**, about $25 from the length-only round's measured spend at the same call count |

### The conditions

A 2×2 within prompt: **target** (v0.4 control or treatment) × **competitor** (absent or
present).

- `control`, `treatment` — corpus v0.4 exactly. All six documents are byte-identical to
  v0.4.
- `control_comp`, `treatment_comp` — the same two targets, with one of the five distractors
  replaced by an **answering competitor**.

Within each pair the five non-target documents are byte-identical, so both contrasts are
paired. The competitor sits in the displaced distractor's doc_id, which
`run_pilot.py` requires because it takes the document set from `prompt["doc_ids"]` for
every condition. Each prompt records it as `competitor_doc_id`.

**The competitor** is an authored document in the displaced slot's register. It answers
the question with the **same figures** as the treatment target, in different words. Same
figures, because a competitor stating different ones would test conflict between sources,
which is a different hypothesis. Different words, because a near-copy would measure
duplication. The builder refuses to write the corpus unless every competitor passes four checks:

| check | rule | built corpus |
|---|---|---|
| no new figures | every digit run in the competitor appears in the treatment target | 48 / 48 |
| answers | at least one figure the treatment has and the control lacks | 48 / 48 |
| not a copy | content-word Jaccard with the treatment < 0.60 | max 0.48, median 0.28 |
| length | 50–110 words | 51–78, median 64 |

Competitor format is balanced: each of the six formats is the competitor in exactly 8
prompts and never the target's own format, across 27 distinct (target, competitor) format
pairs. Named products reuse the v0.4 target's own name, so a question about "this" product
is answered about the same product. Business names are fictional, as in the skill's eval
fixtures.

## Hypotheses

**H9 (primary). Stating the specific answer raises citation even when a competitor
already states it.**

> With an answering competitor present, replacing the target's vague claims with specific
> figures raises the target's Citation Presence Rate.

**Falsified if** the share-weighted pooled `treatment_comp − control_comp` delta has a 95%
bootstrap CI that includes zero.

### Replication

**H4r.** `treatment − control` on this panel, reported beside v0.4's +0.482. It is a
replication rather than a hypothesis under test. It runs in the same session as the
competition arms, so the interaction below is not confounded with model drift since
August.

### Secondary (Holm across the four)

- **H9a — interaction.** `(treatment_comp − control_comp) − (treatment − control)`.
  **Two-sided; direction not predicted.** A competitor can shrink the effect by sharing
  citations with the treated target. It can also grow it, by pulling the untreated
  target down further than the treated one. Both outcomes are anticipated here, so
  neither can be reported as a surprise.
- **H9b — displacement.** The competitor's CPR, `treatment_comp − control_comp`. This
  answers whether stating the answer takes citations away from a rival that already
  states it.
- **H9c — first citation (B1).** Target cited first, `treatment_comp − control_comp`.
- **H9d — selection share (A2).** Target citations over all citations in the run,
  `treatment_comp − control_comp`.

H9c and H9d are included because they keep discriminating when CPR saturates. If both
answering documents are cited in nearly every run, CPR cannot tell them apart, but which
one is cited first, and how much of the answer each carries, can.

## Analysis plan

Executed by `analyze_competition.py --runs results/runs_competition.jsonl`.

- **Primary metric:** target CPR (`METHODOLOGY.md` A1).
- **Pairing:** per (prompt, model). Deltas are taken within each cell, weighted across
  models within a prompt, and prompts are the resampling unit.
- **Inference:** bootstrap over prompts, 10,000 resamples, 95% percentile CIs; sign-flip
  permutation test on the per-prompt deltas. No distributional assumptions; no scipy.
- **Pooling:** share-weighted by `engine_weights.py` for the decision. The unweighted pool
  is printed beside it, because H7 showed that a pooled figure can turn on its weighting.
  **Per-engine results are primary**, with Holm across the five engines.
- **Saturation rule:** an engine whose `treatment_comp` CPR is ≥ 0.98 reports a **floor** on
  its H9 effect, not an estimate (§9). The analyser prints this per engine, and the report
  must carry it into any sentence quoting that engine's delta.
- **Model exclusion:** standing rule — any model above 10% no-cite is excluded from pooled
  figures and reported separately.
- **No prompt exclusions.** All 48 prompts are analysed, including the five whose v0.4
  control already sat at or above 0.96 on this panel (`cons_espresso`, `parent_recall`,
  `career_negotiate`, `fit_hrzones`, `sec_breach`). They carry little H4r headroom, and dropping them after
  seeing data would be a fitted choice.

### Verified before collection

`make_mock_competition.py` plants known effects for this design. On 23,040 mock runs the
analyser's share-weighted intervals contain every planted value:

| contrast | planted | recovered |
|---|---|---|
| H4r | +0.260 | +0.268 [+0.248, +0.289] |
| H9 | +0.182 | +0.184 [+0.161, +0.208] |
| H9a | −0.078 | −0.084 [−0.118, −0.050] |
| H9b | −0.098 | −0.103 [−0.126, −0.080] |

Under a planted null, 150 mock rounds at 12 runs per cell rejected H9 at 6.0% by the
bootstrap CI and 5.3% by permutation, against a nominal 5%.

### Power, stated honestly

H9 itself is not expected to be close. H4 was +0.48. For H9 to fail at 48 prompts,
the competitor would have to erase nearly all of that. **H9a is the
underpowered contrast.** On mock data its 95% CI half-width is about ±0.034, which puts
the smallest detectable interaction near 5 points. That is optimistic, because v0.4's
per-prompt control CPR spans 0.02–1.00 on this panel, a much wider spread than the mock
has. An interaction of a few points may come back as an interval that includes zero,
and it would be reported as that interval.

## Stopping rule

One full round. No interim analysis, no adding models or prompts after seeing results. A
round that fails on data health is rerun in full, and the failed attempt is archived,
not merged.

## Pre-committed spot check

Runs **after this file is committed and before the full round**. It covers 6 prompts, one
per target format, chosen here before any data: `saas_uptime` (blog), `local_movers`
(news), `local_hvac` (docs), `diy_kit` (product), `cons_shoes` (forum), and
`health_creatine` (reference). It runs **two conditions, `control` and
`control_comp`**, on 5 engines at 12 runs per cell, for **720 calls, about $1**.

The treatment arms are not run. The gate is about baseline placement, and running a
treatment arm would measure the effect that the round exists to report (item 10's
precedent).

**Gate, stated against the same six prompts it is checked on** (`ROADMAP.md`, "What the
failures changed"):

1. **Control replicates.** Pooled `control` CPR within ±0.10 of v0.4's control on these six
   prompts and these five engines, **0.565** (720 runs, 2026-08-25). This is a drift check:
   the text is byte-identical, so a gap is the engines changing.
2. **The competitor competes.** In `control_comp`, the competitor's pooled CPR is ≥ 0.50.
   A competitor the engines do not cite is not competing, and the round would measure
   nothing.
3. **No ceiling.** Pooled `control_comp` target CPR ≤ 0.90.

A floor on `control_comp` does not fail the gate. H9 asks whether the treated target
rises, and a low untreated baseline leaves that room.

If any condition fails, the full round is not run, and the failure is logged under
Deviations. A failed competitor is rebuilt from scratch and not nudged (§9: do not re-tune
against the same spot check twice). The spot check does not test H9, and its numbers are
not reported as evidence about it.

## Reporting

Published under `results/published/` whatever the outcome. The headline is H9's delta,
**with the control_comp baseline beside it**, because both together are what a
practitioner facing a competitor can use. If H9's treatment arm saturates on an engine,
that engine's figure is reported as a floor, and the B1/A2 contrasts carry its reading.

Every sentence carries the Tier 1 caveat: synthesis stage only, retrieval held constant.

## Limitations known in advance

- **One competitor, and it agrees with the target.** This does not measure two or more
  answering competitors (the dose question) or competitors that disagree. Both are named
  follow-ups, not folded in.
- **The competitor is authored**, like every v0.4 document. The real-text H4 design note
  (`results/probes/2026-09-23-realtext-h4-design.md`) is still the route to verbatim text.
- **Format is nested within prompt** (8 prompts per target format, 8 per competitor format),
  as in every v0.4-based round.

## Deviations

Logged here with a timestamp before analysis, not made silently.

**2026-10-24 — spot check run; all three gates PASS; full round cleared to run.**

Ran the pre-committed spot check exactly as specified above: the 6 named prompts, the 5
panel engines, `control` and `control_comp` only, 12 runs per cell = **720 calls, 0
errors, 0 `model_returned` mismatches** (`results/spot_competition.jsonl`). Corpus
rebuilt from `corpus/build_corpus_competition.py` at sha `ae1a8844d11cb97f` before the run.
Logged spend $0.71. No treatment arm was run.

| gate | rule | result | |
|---|---|---|---|
| 1. control replicates | pooled `control` CPR within ±0.10 of 0.565 | **0.572** [0.521, 0.622], n=360 (Δ +0.007) | PASS |
| 2. competitor competes | competitor CPR in `control_comp` ≥ 0.50 | **1.000** [0.989, 1.000], n=360 | PASS |
| 3. no ceiling | pooled `control_comp` target CPR ≤ 0.90 | **0.322** [0.276, 0.372], n=360 | PASS |

Pooling for the gates is unweighted, because the 0.565 reference is the unweighted pool
of `results/runs_v0.4.jsonl` on these six prompts and five engines (recomputed: 720 runs,
0.565). Share-weighted for reference: control 0.463 (v0.4 on the same subset: 0.476),
`control_comp` target 0.229, competitor 1.000.

Per engine (72 runs per cell, 95% Wilson):

| engine | no-cite | `control` target | `control_comp` target | competitor |
|---|---|---|---|---|
| openai/gpt-5.4-mini | 0.0% | 0.194 [0.12, 0.30] | 0.000 [0.00, 0.05] | 1.000 [0.95, 1.00] |
| google/gemini-3-flash-preview | 0.0% | 0.958 [0.88, 0.99] | 0.667 [0.55, 0.76] | 1.000 [0.95, 1.00] |
| anthropic/claude-haiku-4.5 | 0.0% | 0.444 [0.34, 0.56] | 0.139 [0.08, 0.24] | 1.000 [0.95, 1.00] |
| deepseek/deepseek-chat | 3.5% | 0.708 [0.59, 0.80] | 0.556 [0.44, 0.66] | 1.000 [0.95, 1.00] |
| x-ai/grok-4.3 | 0.7% | 0.556 [0.44, 0.66] | 0.250 [0.16, 0.36] | 1.000 [0.95, 1.00] |

v0.4 `control` on the same subset, per engine: 0.271, 0.889, 0.299, 0.806, 0.563. No engine
exceeds the 10% no-cite exclusion threshold.

**Observations, recorded so they cannot be reinterpreted later. None changes the design.**

- **The competitor is cited in every run on every engine.** It passes gate 2 at its ceiling.
  H9b (displacement) can therefore only move downward, which is the direction it asks
  about, but its `control_comp` baseline carries no variance to compare against.
- **`gpt-5.4-mini` puts the untreated target at a floor (0/72) once the competitor is
  present.** Per the gate's own text, a floor does not fail it. It does mean that engine's
  H9 delta runs from a baseline of zero, and since it carries 55.9% of the share weight,
  the share-weighted H9 figure will lean on it.

The spot check does not test H9 and these numbers are not evidence about it.

**Status:** the full 23,040-call round (~$25) may proceed as pre-registered, at the
owner's go-ahead.
