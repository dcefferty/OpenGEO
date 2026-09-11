# OpenGEO Length-Only Intervention Pre-Registration — v1 — 2026-09

Committed before any row is written to a results file for this corpus. Per
`preregistrations/README.md`, the git timestamp on this file is the evidence; a
pre-registration committed after collection starts is not a pre-registration.

## Why this round

Every corpus version in this project is length-matched within ±3 words, because
length is assumed to be a confound. **That assumption has never been measured
here.** This round measures it.

It is the sibling of kwstuff-v3. That round isolated *repetition*, holding length
and facts constant. This one isolates *length*, holding facts constant. Both build
on the same baseline: corpus v0.4's `control` text, the one document set this
project has directly measured against real models and confirmed is not at a
ceiling (pooled CPR 0.503, per-model range 0.383–0.591).

The question matters beyond housekeeping. The Princeton GEO paper's headline
figures — quoted industry-wide as fact about ChatGPT — come from interventions that
*add* material to a document without holding length fixed. If padding alone moves
citation, some unknown share of every one of those numbers is word count. If
padding alone does nothing, CPR is robust to length in a way position-adjusted word
count is not, which turns `METRICS.md`'s principled rejection of PAWC into a
measured one.

### Prior evidence motivating it

Exploratory, not from this project, and not treated as a finding: an independent
16-arm replication run outside this repo (24 queries, 2 models, 5,080 observations)
included a pure-filler control arm and measured **+29% on a position-adjusted word
count share metric, statistically significant**, from padding alone — no
statistics, quotations, or citations added. That harness used PAWC as its primary
metric and a weaker length control (a ±10% instruction to the rewriting model,
which one arm violated at 1.89×), so it does not transfer here. It is cited only as
the reason to think this is worth 18,432 calls, not as a prediction.

## Design

| | |
|---|---|
| Corpus | `corpus/corpus_lengthonly.json`, sha `91671f3b8a750cd2` |
| Built by | `corpus/build_corpus_lengthonly.py` |
| Base | corpus v0.4, `control` variant, reused **verbatim** (loaded programmatically, not hand-copied) |
| Prompts | 48, across 24 domains, 8 per target format — unchanged from v0.4 |
| Documents | 6 per prompt; the 5 non-target documents are byte-identical across all conditions |
| Conditions | 4 — `control`, `pad125`, `pad150`, `pad200` |
| Models | 8, via OpenRouter, unchanged from v0.4 |
| Runs per cell | 24 |
| Temperature | 1.0 |
| Document order | randomized per run from a seeded hash, recorded every run |
| Total calls | 48 × 4 × 8 × 24 = 36,864 |

### The conditions

- `control` — corpus v0.4's `control` text, byte-for-byte. Keeps the JSON key
  `control` for harness compatibility (`run_pilot.py` reads it directly when
  estimating cost); referred to as the orthogonal baseline in prose.
- `pad125` / `pad150` / `pad200` — the same text with discourse filler appended to
  ≈1.25×, 1.50× and 2.00× its length. Achieved medians: 1.31×, 1.58×, 2.06×.

Filler sentences state no fact, name no entity, contain no numeral, and share no
content word with that document's own prompt question or its treatment-only
vocabulary. `corpus/build_corpus_lengthonly.py` enforces the last condition per
document at build time; `check_variants.py` re-verifies the built corpus
independently. All 48 target documents pass.

**Why a dose ladder rather than a binary contrast.** A single padded condition
answers "does padding move citation". A ladder answers "how much, and does it
scale" — and a monotone trend across three doses is much harder to explain away as
an artifact than one significant contrast. `run_pilot.py` already accepts arbitrary
`--conditions`, so this costs nothing in harness complexity.

## Hypothesis

**H7. Adding words without adding facts does not increase citation.**

> Padding a document with topic-neutral discourse filler, holding its factual
> content exactly constant, does not raise its Citation Presence Rate.

**Falsified if** the pooled `pad200` − `control` delta has a 95% bootstrap CI
excluding zero, under the standing model-exclusion rule.

**Direction is not predicted.** H7 is stated as a null to be falsified, not a
prediction of increase. A *decrease* would be just as informative — diluting a
document's content could plausibly make it a worse citation target — and is
recorded here as an anticipated outcome so it cannot be reported as a surprise.

### Secondary

- **H7a (dose-response).** If H7 is falsified, CPR increases monotonically across
  `control` → `pad125` → `pad150` → `pad200`. Tested by Spearman's ρ on the four
  condition means per model, with a permutation null over condition labels.
- **H7b (metric divergence).** B2 Attributed Content Share is more sensitive to
  padding than CPR is. Reported as the paired delta on each metric with bootstrap
  CIs; no significance test is pre-registered for the difference between them.

## Analysis plan

- **Primary metric:** target CPR, per `METRICS.md` Group A.
- **Pairing:** per (prompt, model), as in every round — only the target document
  differs between conditions.
- **Inference:** bootstrap over prompts, 10,000 resamples, 95% percentile CIs.
  Permutation test over condition labels within (prompt, model) for the pooled
  delta. No distributional assumptions; no scipy.
- **Multiplicity:** three conditions are compared against `control`. Holm
  correction across those three for the primary metric. H7 is falsified on the
  `pad200` contrast specifically, which is fixed in advance so it is not a
  multiplicity problem.
- **Model exclusion:** standing rule applies — any model whose no-cite rate exceeds
  10% is excluded from pooled figures and reported separately. On v0.4 this was
  `kimi-k2` (34.4%).
- **Variance components:** η² for condition, prompt identity, target format and
  target slot, as reported in every prior round. Relevant here because v0.4 found
  format (η²=0.483) and prompt (η²=0.484) dominate position (η²=0.003); if padding
  registers at all, its η² belongs in that comparison.

## Stopping rule

One full round. No interim analysis, no adding models or prompts after seeing
results. If the round fails on data health (no-cite rates, API errors), it is
rerun in full and the failed attempt is archived, not merged.

## Pre-committed spot check

Per the standing practice from kwstuff-v2, a real-model spot check runs **after
this pre-registration is committed and before the full round**: 6 prompts × 4
conditions × 8 models × 12 runs = 2,304 calls.

**The check is for headroom, not for the hypothesis.** `orthogonal` must reproduce
its v0.4 mid-range CPR (roughly 0.38–0.60 per model). If it comes back at a ceiling
or a floor on the spot-checked prompts, the full round is not run and the failure is
logged in this file's Deviations section, as with kwstuff-v1 and v2.

The spot check does not test H7 and its result is not reported as evidence about it.

## Reporting

Published under `results/published/` whatever the outcome, per the publish-nulls
rule. A null here is the more useful result: it would be the first direct evidence
that this project's primary metric is robust to the confound that its corpus
discipline has been spending effort to avoid.

## Deviations

None yet. Any deviation from the above gets appended here with its date and reason,
before the affected analysis is run.
