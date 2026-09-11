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

Logged here with a timestamp before analysis, not made silently.

**2026-09-11 — spot check run; gate FAILED as written; full round NOT run pending a
decision on the gate itself.**

Ran the pre-committed spot check: 6 prompts (one per target format — `auto_evcharger`,
`edu_certification`, `career_negotiate`, `health_sleep`, `auto_dashcam`,
`career_resume`), all 8 models, all 4 conditions, 12 runs/cell = **2,304 calls, 0
errors, 0 `model_returned` mismatches** (`results/spot_lengthonly.jsonl`). Actual spend
$1.98.

**Gate as written fails.** This file committed the gate as "`control` must reproduce its
v0.4 mid-range CPR (roughly 0.38–0.60 per model)". Only 2 of 8 models land in that band:

| model | control CPR | 95% Wilson |
|---|---|---|
| anthropic/claude-haiku-4.5 | 0.597 | [0.482, 0.703] |
| deepseek/deepseek-chat | 0.694 | [0.580, 0.789] |
| google/gemini-3-flash-preview | 0.847 | [0.747, 0.912] |
| meta-llama/llama-4-maverick | 0.639 | [0.524, 0.740] |
| mistralai/mistral-medium-3 | 0.222 | [0.142, 0.331] |
| moonshotai/kimi-k2 | 0.500 | [0.387, 0.613] |
| openai/gpt-5.4-mini | 0.653 | [0.538, 0.752] |
| x-ai/grok-4.3 | 0.819 | [0.715, 0.891] |

Pooled control CPR 0.622 against the 0.503 reference this file cited.

**Diagnosis: the gate was mis-specified, and the error is in this pre-registration, not
in the corpus.** The 0.503 reference is v0.4's control pooled over all **48** prompts.
The spot check runs **6**. Those are different denominators, and per-prompt control CPR
on this corpus spans 0.219–0.896, so a 6-prompt subset cannot be expected to land on the
48-prompt mean.

The correct comparison is v0.4's own control restricted to these same 6 prompts, from
`results/runs_v0.4.jsonl`:

| | control CPR | n |
|---|---|---|
| v0.4 control, all 48 prompts | 0.503 | 9,216 |
| **v0.4 control, these 6 prompts** | **0.646** | 1,152 |
| **lengthonly control, these 6 prompts** | **0.622** | 576 |

Delta −0.024. The `control` variant is byte-identical to v0.4's by construction, and it
behaves identically in practice. Per-model agreement with v0.4 on the same 6 prompts is
within sampling noise for 7 of 8 models (−0.076 to +0.153).

**New data-health exclusion: `mistralai/mistral-medium-3`.** No-cite rate 17.7%, above
the standing 10% threshold, and its control CPR fell 0.590 → 0.222 versus v0.4 on
identical text. This is an instruction-following regression in the model since v0.4 ran,
not a corpus effect. It joins `kimi-k2` (20.5% here, 34.4% on v0.4) on the exclusion
list. v0.4's published round did not exclude mistral; any future round should.

**Residual limitation even under the corrected gate.** With both excluded models
removed, `gemini-3-flash-preview` (0.847) and `grok-4.3` (0.819) sit high enough that an
*increase* in CPR has compressed headroom on them. A *decrease* is detectable throughout.
Since H7 is two-sided and this file explicitly declines to predict a direction, this
weakens but does not void the design on 2 of 6 usable models.

**Disclosure.** Per-condition descriptive CPRs for all four conditions were computed and
seen before this entry was written. They are not reported here and played no part in the
diagnosis above, which rests entirely on `control`-vs-`control` comparisons. Recording
that they were seen, because amending a gate after any look at outcome data is exactly
what pre-registration exists to constrain.

**Status: the full 36,864-call round (~$32) is NOT run.** Proceeding requires amending
the gate after seeing data, which is a real methodological cost even when the diagnosis
is sound. That decision is the repo owner's, not the contributor's. Options, in the
order this contributor would rank them:

1. **Re-specify the gate against a subset-matched reference and re-run the spot check on
   a larger prompt sample** (e.g. 18 prompts, ~1,700 calls at 12 runs) — restores the
   gate's meaning without amending it on the basis of a run already seen.
2. **Amend the gate to the subset-matched form** (`control` within ±0.10 of v0.4's
   control on the same prompts) and proceed, with this entry standing as the record.
3. **Redesign** to raise headroom on gemini and grok, as kwstuff went through three
   times.

**2026-09-11 — model panel narrowed to answer-engine models; gate amended; full round
authorised by the repo owner.**

Two changes, both made at the owner's direction after the spot check above, and both
recorded here rather than applied silently.

**1. Panel narrowed from 8 models to 5, selected and ranked by market share.** The
pre-registered panel was inherited from v0.4 and mixes models that back consumer answer
engines with models that do not. This benchmark exists to tell someone what to change
about their content, so the panel is the engines their readers actually use, ordered by
how much traffic each commands (Similarweb Gen AI worldwide traffic share, August 2026 —
see `engine_weights.py` for the numbers, the source, and the caveats):

| engine | share | model | in round |
|---|---|---|---|
| ChatGPT (incl. Copilot) | 54.7% | `openai/gpt-5.4-mini` | yes |
| Gemini | 27.8% | `google/gemini-3-flash-preview` | yes |
| Claude | 9.2% | `anthropic/claude-haiku-4.5` | yes |
| DeepSeek | 3.6% | `deepseek/deepseek-chat` | yes |
| Grok | 2.5% | `x-ai/grok-4.3` | yes |
| Perplexity | 1.1% | `perplexity/sonar` | **no — not measurable in Tier 1** |

The panel covers **98.9%** of measured gen-AI traffic across the engines this harness can
test.

Dropped, with reasons:

- `moonshotai/kimi-k2` (20.5% no-cite) and `mistralai/mistral-medium-3` (17.7%) —
  excluded by the standing data-health rule, independent of this change.
- `meta-llama/llama-4-maverick` — passes data health, but Meta AI does not appear as a
  named platform in the traffic series used here, and Llama's usage is overwhelmingly as
  a component in other products rather than as an answer engine people optimise for.

**A correction made in the course of this change, recorded because it was an error of
judgement and not of data.** An earlier version of this entry dropped
`deepseek/deepseek-chat` on the grounds that it does not back a consumer answer engine.
The traffic series contradicts that: DeepSeek holds 3.6% share, *above* Grok's 2.5%,
which the same entry retained. It is reinstated. The round had completed 223 calls under
the 4-model panel when this was caught; those rows are valid (same corpus, same
conditions) and were kept, with the round resumed rather than restarted. DeepSeek was
also one of the two best-headroom models in the spot check (control CPR 0.694), so the
correction improves the design as well as its rationale.

**Cost of the narrowing, stated plainly:** `gemini-3-flash-preview` (control CPR 0.847)
and `grok-4.3` (0.819) sit high enough that **detecting an *increase* in CPR is
compressed on two of the five engines**. A decrease remains detectable throughout. H7 is
two-sided and this file declines to predict a direction, so the round is still
informative, but it is better powered against one tail than the other. Reinstating
DeepSeek (0.694) mitigates this; it does not remove it. Recorded here so no later reader
has to infer it.

**Weighted pooling.** Because share is so uneven — ChatGPT alone is 55.9% of the panel's
normalised weight, Grok 2.6% — an unweighted pool over five engines would assert an equal
split that is false by more than an order of magnitude. Pooled figures for this round are
therefore reported **share-weighted**, with per-engine results remaining primary and
reproducible. The weights are a documented, swappable parameter in `engine_weights.py`,
not a finding; that file also states the tension in using vendor-panel numbers inside a
project that rejects vendor-panel numbers, and why they are still the best available.

**2. `perplexity/sonar` was evaluated and cannot be used.** Perplexity is the most
GEO-targeted engine in existence and its absence from this panel is a real gap, so it
was tested directly. Sonar **ignores supplied sources and performs live web search**: given
2 numbered sources and an instruction to use only those, it returned citations
`[2][4][9][10][12][15]` — indices drawn from its own web results, not the supplied set.

This is structurally incompatible with the Tier 1 constraint that retrieval is held
constant (`CLAUDE.md`), and the failure is silent rather than loud: `parse_citations`
bounds-checks against the document count, so out-of-range web citations are dropped and
Sonar would be recorded as a near-total no-cite model rather than an incompatible one. A
future round that adds it without this check would read the corruption as a finding.

**This is a limitation of the Tier 1 design, not of this corpus:** the engine most people
most want to optimise for is the one this harness structurally cannot measure. It belongs
in the Tier 2 line of work alongside the calibration study.

**3. Gate amended.** Per the diagnosis in the preceding entry, the gate is restated in
subset-matched form — `control` must fall within ±0.10 of v0.4's control CPR **on the
same prompts**, rather than against the 48-prompt pooled mean. On the spot check this is
0.622 vs 0.646, delta −0.024: **passes**. The original numeric band was an
operationalisation error (mismatched denominators); the gate's purpose — confirm the
baseline is not at a ceiling or floor — is served by the corrected form. Amended after
seeing spot-check data, at the owner's direction, with the preceding entry as the record.

**Round authorised:** 5 models × 48 prompts × 4 conditions × 24 runs = **23,040 calls**,
projected ~$25 from measured spot-check token spend.
