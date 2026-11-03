# OpenGEO Conflicting-Figures Round Pre-Registration — v1 — 2026-11

Committed before any row is written to a results file for this corpus. Per
`preregistrations/README.md`, the git timestamp on this file is the evidence; a
pre-registration committed after collection starts is not a pre-registration.

## Why this round

H9 (`results/published/2026-10-25-competition/REPORT.md`) found that stating the specific
answer raises citation by **+0.764 [+0.713, +0.812]** even when a competitor already
states it. That competitor stated the *same* figures as the target. Its pre-registration
named the next case and left it out: a competitor that disagrees.

That case is the one a practitioner meets when a rival page quotes a different price, an
older limit or a different dose. Two questions follow, and nobody has measured either
causally:

- **What does disagreeing cost?** If two answering pages conflict, does the engine cite
  the one that disagrees with the other less often than it would cite the same page
  agreeing?
- **Which figure does the answer use?** When the engine cites through a conflict, does it
  repeat the competitor's figure or the target's?

H9 also suggests what to expect. On ChatGPT and Claude, stating the answer took citations
from the competitor, so those engines sometimes choose between two answering pages. A
conflict gives them a reason to choose.

## Design

| | |
|---|---|
| Corpus | `corpus/corpus_conflict.json`, sha `4d27315abb2f1a7a` |
| Built by | `corpus/build_corpus_conflict.py` |
| Base | competition-v1, all 48 prompts; `control_comp` and `treatment_comp` reused **verbatim** (loaded programmatically) |
| Prompts | 48, across 24 domains, 8 per target format |
| Documents | 6 per prompt, one of them the answering competitor from competition-v1 |
| Conditions | 3 — `control_comp`, `agree`, `conflict` |
| Models | the five-engine panel in `engine_weights.py`: `openai/gpt-5.4-mini`, `google/gemini-3-flash-preview`, `anthropic/claude-haiku-4.5`, `deepseek/deepseek-chat`, `x-ai/grok-4.3` |
| Runs per cell | 24 |
| Temperature | 1.0 |
| Document order | randomized per run from a seeded hash, recorded every run |
| Total calls | 48 × 3 × 5 × 24 = **17,280**, about $16 from H9's measured spend per call |

### The conditions

Only the target differs between conditions. The other five documents, the competitor
included, are byte-identical across all three, so every contrast is paired.

- `control_comp` — the vague v0.4 target. Identical to competition-v1 `control_comp`.
- `agree` — the target states the same figures as the competitor. Identical to
  competition-v1 `treatment_comp`.
- `conflict` — the `agree` target with its answer figures replaced by different, plausible
  ones. Nothing else in the text changes.

Both `control_comp` and `agree` were measured in H9. They are run again here, so all
three arms are collected in one session and no contrast mixes in model drift since
October.

### The conflicting target

Each prompt has a short list of exact phrase replacements on the `agree` target, written
in the builder. The builder refuses to write the corpus unless every prompt passes these
checks:

| check | rule |
|---|---|
| exact | every replaced phrase occurs exactly once in the `agree` target |
| length | word count unchanged |
| conflicts | no answer figure survives: none that the target shares with the competitor and the vague control lacks, except tokens that name something ("Level 2", "R-22", the "10+ years" in the question, a year) |
| unambiguous | no new figure appears in any of the prompt's six documents, in any condition |
| direction | each prompt's asked-for figure moves `up` or `down`: 24 of each, 4 of each within every target format |

The unambiguous check is what makes adoption measurable. Each new figure exists only in the
`conflict` target, so an answer that repeats it took it from there.

### What "correct" means

The competitor's figures are v0.4's treatment figures, written to be realistic. In
`conflict`, nothing in the six documents says which side is right. So the primary contrast
measures what **disagreeing with another answering source** costs, not what being wrong
costs.

Whether the engines reward the correct figure can only be read where they have outside
knowledge to judge by. Each prompt is classed in the builder, before any data:

- **`world` (33 prompts):** a general fact the engine may already know, such as a creatine
  dose, the FDIC limit, PMP exam length, or the age to turn a car seat forward.
- **`document` (15 prompts):** a fact about one fictional product or event, such as a
  dashcam's card size or a recall's unit count. Here neither side can be known to be right.

Several `world` conflicts use a figure that was once true or is commonly misquoted (a
$100,000 FDIC limit, a 200-question PMP exam, rear-facing to age 1). That is deliberate:
those are the errors that circulate.

## Hypotheses

**H13 (primary). Disagreeing with an answering competitor costs citation.**

> With the same answering competitor present, a target whose figures agree with it is
> cited more often than the same target stating different figures.

**Falsified if** the share-weighted pooled `agree − conflict` delta has a 95% bootstrap CI
that includes zero. The direction is predicted (positive) and stated here so that a
negative result is reported as the surprise it would be.

### Secondary (Holm across the four)

- **H13a — a disagreeing figure vs no figure.** `conflict − control_comp`, target CPR.
  **Two-sided; direction not predicted.** A page stating a contradicted figure may still
  beat a page that states none, as H9 suggests, or the conflict may cost it more than
  stating the figure gained.
- **H13b — the competitor's gain.** Competitor CPR, `conflict − agree`. Whether a rival
  gains citations when your page contradicts it.
- **H13c — adoption.** In `conflict` answers that state one side's figure and not the
  other's, the share that state the competitor's, tested against 0.5.
- **H13d — outside knowledge.** H13's delta in `world` prompts minus its delta in
  `document` prompts. If engines judge against what they already know, disagreeing should
  cost more where they know the answer. **Two-sided.**

## Analysis plan

Executed by `analyze_conflict.py --runs results/runs_conflict.jsonl`.

- **Primary metric:** target CPR (`METHODOLOGY.md` A1).
- **Pairing:** per (prompt, model). Deltas are taken within each cell, weighted across
  models within a prompt, and prompts are the resampling unit.
- **Inference:** bootstrap over prompts, 10,000 resamples, 95% percentile CIs; sign-flip
  permutation test on the per-prompt deltas. H13d compares two disjoint sets of prompts,
  so it bootstraps within each class and permutes the class labels. No distributional
  assumptions; no scipy.
- **Pooling:** share-weighted by `engine_weights.py` for the decision, with the unweighted
  pool printed beside it. **Per-engine results are primary**, with Holm across the five
  engines.
- **Saturation rule:** an engine whose `agree` CPR is ≥ 0.98 reports a **floor** on its H13
  effect, not an estimate (§9). H9 puts Gemini, DeepSeek and Grok there, so this rule is
  expected to apply to three of five engines.
- **Model exclusion:** standing rule. Any model above 10% no-cite is excluded from pooled
  figures and reported separately.
- **No prompt exclusions** from the CPR contrasts.

### Adoption, read mechanically

Adoption is read from the answer text by `analyze_conflict.py`, with no model judge. Each
answer's figures are extracted the way the corpus builder extracts them. A figure counts
for a side only if it is **distinctive**: not in the question and not a single-digit whole
number, which answers quote for other reasons. Every answer is classed `correct`
(competitor's figure only), `wrong` (target's only), `both` or `neither`, and H13c uses
`correct / (correct + wrong)`. All 48 prompts have a distinctive figure on both sides.

### Verified before collection

**The reader was run on H9's 11,520 real answers**
(`python3 analyze_conflict.py --validate-extractor results/runs_competition.jsonl`).
No conflicting figure exists in that round, so any `wrong` reading is a false positive:

| H9 condition | runs | correct | wrong or both | false-positive rate |
|---|---|---|---|---|
| `control_comp` | 5,760 | 5,584 | 0 | 0.00% [0.00%, 0.07%] |
| `treatment_comp` (= `agree`) | 5,760 | 5,595 | 1 | 0.02% [0.00%, 0.10%] |

The same run shows the reader finds the competitor's figure in 97% of `agree` answers.

**`make_mock_conflict.py` plants known effects for this design.** On 17,280 mock runs the
analyser's share-weighted intervals contain every planted value:

| contrast | planted | recovered |
|---|---|---|
| H13 | +0.239 | +0.240 [+0.212, +0.268] |
| H13a | +0.290 | +0.277 [+0.248, +0.306] |
| H13b | +0.056 | +0.058 [+0.042, +0.074] |
| H13c | +0.222 | +0.225 [+0.187, +0.262] |
| H13d | +0.080 | +0.071 [+0.011, +0.133] |

Under a planted null, 100 mock rounds at 12 runs per cell rejected H13 at 5.0% by the
bootstrap CI and 4.0% by permutation, against a nominal 5%.

### Power, stated honestly

H13 is likely to be detectable if disagreeing costs more than a few points on the engines
that choose between answering pages. The risk is saturation. On Gemini, DeepSeek and Grok,
H9's treated target was cited in nearly every run *alongside* the competitor, so those
engines may cite a conflicting page just as often, and H13 there could be a true null
rather than a missed effect. H13c (adoption) still discriminates in that case, because
which figure an answer repeats does not depend on whether the page was cited.

**H13d is the underpowered contrast.** It compares 33 prompts with 15, and the mock's 95%
interval is about ±0.06 wide on each side. An interaction smaller than that will come back
as an interval that includes zero, and it will be reported as that interval.

## Stopping rule

One full round. No interim analysis, no adding models or prompts after seeing results. A
round that fails on data health is rerun in full, and the failed attempt is archived, not
merged.

## Pre-committed spot check

Runs **after this file is committed and before the full round**. It covers 6 prompts, one
per target format, chosen here before any data and none of them in H9's spot check:
`game_pc_upgrade` (blog, down, world), `edu_certification` (docs, up, world), `diy_drill`
(forum, up, document), `loan_rate` (news, down, world), `auto_dashcam` (product, down,
document) and `fit_hrzones` (reference, up, world). It runs **two conditions, `control_comp`
and `agree`**, on 5 engines at 12 runs per cell, for **720 calls, about $1**.

The `conflict` arm is not run. Measuring it would measure the effect the round exists to
report.

**Gate, stated against the same six prompts it is checked on**, from
`results/runs_competition.jsonl`:

1. **`control_comp` replicates.** Pooled CPR within ±0.10 of competition-v1's on these six
   prompts and five engines, **0.214** (720 runs, 2026-10-25).
2. **`agree` replicates.** Pooled CPR within ±0.08 of competition-v1's `treatment_comp`,
   **0.925** (720 runs, 2026-10-25).

Both arms are byte-identical to text already measured, so a gap is the engines changing.
Pooling for both gates is unweighted, matching how the references were computed.

If either gate fails, the full round is not run and the failure is logged under
Deviations. The spot check does not test H13, and its numbers are not reported as
evidence about it.

## Reporting

Published under `results/published/` whatever the outcome. The headline is H13's delta
with both arm means beside it, and H13c's adoption share beside that, because a reader
facing a contradicting rival needs both: whether they are cited, and whose figure the
answer repeats. Engines whose `agree` arm saturates report a floor.

Every sentence carries the Tier 1 caveat: synthesis stage only, retrieval held constant.

## Limitations known in advance

- **"Correct" is only defined where the engine has outside knowledge.** In `document`
  prompts, the round measures agreement with another source, not truth.
- **One competitor, and the target is the side that moves.** This does not measure a page
  contradicted by two sources against one (the corroboration question), or the competitor
  being the wrong side. Both are named follow-ups. Moving the competitor would break the
  paired design, which holds every non-target document fixed.
- **One magnitude of disagreement per prompt.** Conflicts are plausible but not graded, so
  the round cannot say whether a small discrepancy costs less than a large one. Direction
  (`up`/`down`) is balanced and reported descriptively.
- **The documents are authored**, like every v0.4-based round.
- **Format is nested within prompt.**

## Deviations

Logged here with a timestamp before analysis, not made silently.

**2026-11-02 — spot check run; both gates PASS; full round cleared to run.**

Ran the pre-committed spot check exactly as specified above: the 6 named prompts, the 5
panel engines, `control_comp` and `agree` only, 12 runs per cell = **720 calls, 0 errors,
0 `model_returned` mismatches** (`results/spot_conflict.jsonl`). Corpus rebuilt from
`corpus/build_corpus_conflict.py` at sha `4d27315abb2f1a7a` before the run. Logged spend
$0.69. The `conflict` arm was not run.

| gate | rule | result | |
|---|---|---|---|
| 1. `control_comp` replicates | pooled CPR within ±0.10 of 0.214 | **0.239** [0.198, 0.286], n=360 (Δ +0.025) | PASS |
| 2. `agree` replicates | pooled CPR within ±0.08 of 0.925 | **0.914** [0.880, 0.939], n=360 (Δ −0.011) | PASS |

Per engine (72 runs per cell, 95% Wilson; competitor CPR pooled over both arms):

| engine | no-cite | `control_comp` target | `agree` target | competitor |
|---|---|---|---|---|
| openai/gpt-5.4-mini | 0.0% | 0.056 [0.02, 0.13] | 0.833 [0.73, 0.90] | 0.938 |
| google/gemini-3-flash-preview | 0.0% | 0.458 [0.35, 0.57] | 1.000 [0.95, 1.00] | 1.000 |
| anthropic/claude-haiku-4.5 | 2.1% | 0.097 [0.05, 0.19] | 0.764 [0.65, 0.85] | 0.903 |
| deepseek/deepseek-chat | 0.7% | 0.389 [0.28, 0.50] | 0.972 [0.90, 0.99] | 0.993 |
| x-ai/grok-4.3 | 0.7% | 0.194 [0.12, 0.30] | 1.000 [0.95, 1.00] | 0.993 |

No engine exceeds the 10% no-cite threshold. As expected from H9, `agree` sits at or near
the ceiling on Gemini, DeepSeek and Grok, so the saturation rule will likely make their H13
figures floors. ChatGPT and Claude have headroom.

The spot check does not test H13 and these numbers are not evidence about it.

**Status:** the full 17,280-call round (~$16) may proceed as pre-registered, at the
owner's go-ahead.
