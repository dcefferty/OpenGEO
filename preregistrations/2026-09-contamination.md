# OpenGEO Public/Private Contamination Round — Pre-Registration — v1 — 2026-09-22

Committed before collection. The git timestamp on this file is the evidence that it
preceded its data.

## Why this round

Every number this project has published comes from a corpus that ships with the result.
That is the point — it is what makes a round checkable — and it is also a standing
liability: a fully public benchmark is eventually trained on, and an effect that survives
only on questions a model has already seen is not an effect.

ROADMAP item 10 is the defence. A held-out private split of twelve questions now exists
(`METHODOLOGY.md` §10.1), built under §9 and screened control-arm-only across three
batches. Its questions have never been published and never will be; only aggregates from
it are ever reported.

This round runs the public corpus and the private split **side by side, in one
collection**, and asks whether the project's strongest finding survives on questions that
were never published. It closes item 10's third acceptance clause.

The finding under test is **H4** — that replacing vague claims with specific figures raises
citation. It was measured at +0.493 on corpus v0.3 and +0.482 on v0.4, significant on every
model. If contamination is inflating anything, it is inflating this.

## Design

| | Public half | Private half |
|---|---|---|
| Corpus | `corpus/corpus_v0.4.json`, sha `f1d0672d1d295a66` | `private-v1`, sha `529939b6163befeb` |
| Built by | `corpus/build_corpus.py` | held out; not in this repository |
| Prompts | 48, 24 domains, 8 per target format | 12, 12 domains, 2 per target format |
| Documents | 6 per prompt; 5 non-target documents byte-identical across arms | same |
| Conditions | 2 — `control`, `treatment` | same |
| Models | 5-engine market panel | same |
| Runs per cell | 24 | same |
| Temperature | 1.0 | same |
| Document order | randomised per run from a seeded hash, recorded every run | same |
| Calls | 48 × 2 × 5 × 24 = 11,520 | 12 × 2 × 5 × 24 = 2,880 |

**Total 14,400 calls**, ~9.9M input and ~3.6M output tokens, estimated at $3.65 (low
pricing) to $10.36 (mid) from `run_pilot.py --dry-run` on both corpora. Both halves are
collected in the same session, against the same panel, with the same harness version, so a
divergence cannot be a difference of date, model routing or code.

The private half's **treatment arm has never been run**. Every private figure recorded
anywhere to date is control-only, because the §5.3 gate is about baseline placement and
running the treatment arm early would measure the very effect this round exists to report.

## Hypotheses

**H8. The H4 effect replicates on held-out questions.**

> Replacing vague claims with specific figures raises Citation Presence Rate on questions
> that have never been published.

**Falsified if** the private half's pooled `treatment` − `control` delta has a 95%
bootstrap CI that includes zero.

**H9. The effect is no larger on published questions than on held-out ones.**

> The public and private effects do not differ.

**Falsified if** the 95% bootstrap CI on the public − private difference excludes zero.

**Direction is predicted for H9, and only for H9.** Contamination inflates the *public*
side. A public effect significantly *larger* than the private one is the signature this
round is built to detect. A private effect larger than the public one would not indicate
contamination and would most likely mean the two corpora differ in difficulty; that
reading is recorded here so it cannot be presented afterwards as a subtle confirmation.

**H9 is stated as a null to be falsified, and failing to falsify it is not proof of
absence.** With twelve private questions the interval will be wide. The round reports the
divergence and its interval; it does not claim contamination is absent.

## The baseline confound, and how it is handled

The two halves do not start from the same place. Measured control-arm rates, both on the
current five-engine panel — public from the length-only round's control arm (v0.4 control
text, 5,760 runs), private from the three committed screening runs (1,440 runs):

| engine | public | private | difference |
|---|---|---|---|
| claude-haiku-4.5 | 0.385 | 0.229 | −0.156 |
| deepseek-chat | 0.652 | 0.465 | −0.187 |
| gemini-3-flash-preview | 0.646 | **0.806** | +0.160 |
| gpt-5.4-mini | 0.423 | 0.444 | +0.022 |
| grok-4.3 | 0.602 | 0.632 | +0.030 |
| **pooled** | 0.542 | 0.515 | −0.026 |

Pooled they are close. Per engine they are not, and that matters: **a risk difference is
bounded by its baseline.** A cell starting at 0.806 cannot rise by 0.48 whatever the
intervention does, so a naive public-minus-private comparison would report "contamination"
on gemini that is arithmetic rather than memorisation.

Three pre-committed consequences:

1. **The primary scale for H9 is the odds ratio**, which is not bounded by the baseline in
   the way a risk difference is. Risk differences are reported alongside, and where the two
   scales disagree the disagreement is the finding and is reported as such.
2. **These baselines are recorded here, before collection**, so that a per-engine
   divergence cannot be presented afterwards as a discovery when it was predictable from
   the starting rates.
3. **Per-engine results are primary**, as in every round since item 12. Any pooled figure
   states its weighting.

## Analysis plan

- **Primary metric:** target CPR (`METHODOLOGY.md` §4, Group A1).
- **Pairing:** per (prompt, model) — only the target document differs between arms.
- **Inference:** bootstrap over prompts, 10,000 resamples, 95% percentile CIs. Sign-flip
  permutation over condition labels within (prompt, model). No distributional assumptions,
  no scipy.
- **H9's contrast:** the difference of log odds ratios between halves, bootstrapped over
  prompts **within each half independently** and differenced, since the two halves share no
  prompts. Reported per engine and share-weighted-pooled.
- **Multiplicity:** Holm across the five engines for the per-engine H9 contrasts. H8 and
  the pooled H9 contrast are each single pre-specified tests and are not corrected.
- **Model exclusion:** the standing rule — any model above a 10% no-cite rate is excluded
  from pooled figures and reported separately.
- **Incomplete cells:** `analyze.incomplete_cells` reports any cell short of 24 runs and
  drops those below 80%. If any cell is dropped, the round is resumed to completion before
  analysis rather than analysed short.
- **Variance components:** η² for condition, half (public/private), prompt identity and
  target format. The half term is the one of interest and has not been estimated before.

## Stopping rule

One full round, both halves in one collection. No interim analysis. No adding prompts,
models or runs after seeing results. If the round fails on data health, it is rerun in full
and the failed attempt is archived, not merged.

## Spot check

**Already satisfied, and not re-run.** The standing §5.3 gate exists to confirm the control
arm is not at a ceiling or floor before a round is paid for. Both halves have that
evidence, on the current panel, from committed runs:

- Public: the length-only round's control arm, 5,760 runs, pooled 0.542 — v0.4 control
  text on this exact panel.
- Private: three screening runs, 1,440 runs, pooled 0.515, every question inside
  [0.25, 0.75].

Re-running the gate would spend roughly 2,000 calls to re-derive numbers already committed.
The gate's purpose is served; the evidence is cited rather than repeated.

## Reporting

Published under `results/published/` whatever the outcome.

**The public half is reported in full**, with raw responses shipped as in every round.
**The private half is reported as aggregates only** — pooled and per-engine effects with
intervals, and the H9 contrast. No private question, document, or per-prompt figure is
published, now or later. That restriction is what makes the split reusable; publishing a
per-prompt table would burn it as surely as publishing the corpus.

A null on H9 is the useful outcome and is reported with equal prominence: it would be the
first direct evidence that this project's headline number is not an artefact of its corpus
being public. A falsification of H9 is more useful still, and would mean the public
corpus's numbers need restating with a contamination caveat.

## Deviations

None yet. Every deviation is logged here, dated, before or as it happens.
