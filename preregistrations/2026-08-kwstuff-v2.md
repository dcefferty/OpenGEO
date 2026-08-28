# OpenGEO Keyword-Stuffing Intervention Pre-Registration — v2 — 2026-08

Committed before any row is written to a results file for this corpus. Per
`preregistrations/README.md`, the git timestamp on this file is the evidence; a
pre-registration committed after collection starts is not a pre-registration.

## Why a v2

`preregistrations/2026-08-kwstuff.md` (v1) pre-registered H6 on `corpus_kwstuff_v1.json`
and ran to completion cleanly (18,432 calls, 0 errors) — but the result was
uninformative, not a clean null. v1's `control` arm reused corpus v0.4's `treatment`
variant *wholesale*, on the (stated, and wrong) assumption that content already proven
not to have a ceiling problem in the claim-density experiment carried that property
into this one. It didn't: that text sits at ~98.5% pooled CPR, leaving no headroom for
stuffing to move citation in either direction. Symptoms: pooled H6 delta -0.001 (p=0.57),
5 of 8 models with zero variance in the control cell, H1 reliability undefined for
those models, H2 PSI collapsed to 0.007, H5 format eta² collapsed to 0.000. Full
diagnosis lives in the (unpublished — see below) v1 results; this file documents the
redesign, not a rerun of the same design.

**Decision:** redesign with a genuine mid-range baseline and rerun (not: publish v1 as
a negative-space finding). `results/runs_kwstuff_v1.jsonl` and its pre-registration
stay in the repo history as the documented false start that motivated this redesign —
science that doesn't work the first time is still reported, per this project's own
"publish nulls" rule, just not as the answer to H6.

## Redesign

- `moderate` (new baseline, replaces v1's `control`) — for each prompt, the sentence(s)
  stating ONE of the question's two target facts, taken verbatim from
  `corpus_v0.4.json`'s `treatment` variant, combined with orthogonal filler content for
  the OTHER fact, taken verbatim from `corpus_v0.4.json`'s `control` variant. Genuinely
  specific about one fact, silent on the other — deliberately mid-range, not full
  answer and not off-topic distractor.
- `stuffed` (replaces v1's `treatment`) — the same `moderate` facts, with the prompt's
  core topic keyword (unchanged from v1's mapping) awkwardly repeated 4-8 times where
  natural writing wouldn't. Length-matched to `moderate` within ±3 words (verified:
  min -3, max +3, mean +1.0 words, per `build_corpus_kwstuff_v2.py`'s balance check).
- Both variants are **recombinations of text already validated against real models in
  corpus_v0.4.json** — no new prose authored from scratch, to limit the risk of
  reintroducing an undetected ceiling or keyword/directional-echo problem. This is a
  narrower bet than v1's (which also relied on "already validated" text, but reused it
  wholesale rather than recombined, and was wrong) — see Validation plan below for what
  this project is doing differently this time as a result.
- The other 5 documents per prompt, and the questions themselves, are byte-identical to
  `corpus_v0.4.json` — unchanged from v1.

## Hypothesis

**H6 (unchanged from v1). Keyword stuffing does not increase citation, and plausibly
decreases it,** relative to equally fact-complete natural prose. Falsified if the
paired effect is positive and its 95% CI excludes zero. This redesign changes the
*baseline*, not the hypothesis or what would falsify it.

## Corpus

| | |
|---|---|
| corpus_version | `kwstuff-v2` |
| corpus_sha256 (16-char prefix) | `742fda6efa4bf166` |
| base_corpus_version | `0.4` |
| supersedes | `kwstuff-v1` |
| File | `corpus/corpus_kwstuff_v2.json` |
| Structure | 48 prompts × 6 documents (blog, news, docs, product, forum, reference) = 288 documents |
| Target format balance | exactly 8 prompts per format |

**What was checked before trusting this, without spending on real models:** every
`moderate`/`stuffed` pair verified programmatically for (a) length match within ±3
words (confirmed: -3 to +3, mean +1.0), (b) no duplicate sentences within a document,
(c) every document ending on complete, grammatical punctuation. Same checks as v1 —
these catch authoring bugs, not the ceiling/echo risk, which is a different kind of
problem and is not fully catchable by inspection (established repeatedly across this
project's corpus-design history).

## Validation plan (the actual process change from v1)

v1 skipped real-model validation entirely, reasoning that reused-and-proven content
carried its properties forward. That reasoning failed. This time: **a real-model spot
check of a subset of prompts runs after this pre-registration is committed but before
the full 18,432-call round**, specifically to check the `moderate` baseline's CPR isn't
pinned near 0% or 100% and that `stuffed` isn't winning citations purely by keyword
echo unrelated to stuffing. This does not reopen the hypothesis, corpus content, or
analysis plan to revision based on favorable-looking results — only a genuine ceiling
or echo failure (CPR at or near 0/100% for most spot-checked prompts, or a
`model_returned` problem) triggers a documented deviation or a v3 redesign; anything
else, the round proceeds as specified below. Logged as a dated entry in Deviations
either way.

## Models

Same 8, via OpenRouter, unchanged from v1: `anthropic/claude-haiku-4.5`,
`openai/gpt-5.4-mini`, `google/gemini-3-flash-preview`, `x-ai/grok-4.3`,
`moonshotai/kimi-k2`, `deepseek/deepseek-chat`, `meta-llama/llama-4-maverick`,
`mistralai/mistral-medium-3`.

`kimi-k2` has a known elevated no-cite rate (13.3% on v0.4) and is excluded from pooled
figures per the same rule as every prior round — reported individually, not averaged in.

## Design

- **Conditions:** `moderate` (new baseline, natural prose), `stuffed` (keyword-stuffed)
  — paired within prompt; only the target document differs between arms.
- **Runs per cell:** 24, per the established reliability floor (`CLAUDE.md`).
- **Temperature:** 1.0, fixed.
- **Document order:** randomized per run, seeded deterministically from
  `(corpus_version, run_key)`.
- **Total calls:** 8 models × 48 prompts × 2 conditions × 24 runs = **18,432** for the
  full round (excludes the small validation-spot-check subset, run and reported
  separately).
- **Estimated cost:** comparable to v1, ~$5-14, per `run_pilot.py --dry-run`.

## Primary metric

**Citation Presence Rate (CPR)** — A1 in `METRICS.md`. Proportion of runs in which the
target document is cited. Reported per model with a Wilson 95% interval.

## Analysis plan

Identical machinery to v1, applied via `analyze.py --runs <results file> --corpus
corpus/corpus_kwstuff_v2.json`:

- Paired per-prompt (stuffed − moderate) CPR delta, sign-flip permutation test on
  per-prompt differences, bootstrap CI on the pooled delta. Reported per model and pooled.
- H1 (reliability), H2/D1 (PSI), H3 (cross-model agreement), H5 (format × model
  interaction) re-checked on this corpus as replication checks.
- All inference permutation- or bootstrap-based, no distributional assumptions, per
  `CLAUDE.md`'s stack constraints.
- **New for v2, given the v1 failure mode:** report `moderate`-condition CPR (the
  baseline itself) prominently and explicitly, per model and pooled, before reporting
  the H6 delta — so a ceiling or floor problem is visible on its own, not just inferred
  from a null delta after the fact.

## Reporting rules

- **Whatever direction H6 comes back — positive, negative, or null — gets published
  with equal prominence.** Unchanged from v1.
- If the `moderate` baseline shows a ceiling or floor problem analogous to v1's, that
  gets reported as plainly as v1's did — this project's credibility depends on that
  being routine, not exceptional.
- `kimi-k2` excluded from pooled figures per its no-cite rate, same as every prior round.
- `model_returned` checked against the requested model on every run before cross-run
  comparison.

## Stopping rule

- Fixed-n, not sequential, for the full round. All 18,432 cells run to completion (or
  resumed via `--resume` after interruption); no early stopping based on interim effect
  sizes.
- The validation spot check (see above) is explicitly exempt from "no early stopping" —
  it is a pre-committed go/no-go gate on the *design*, not a peek at the *result*, and
  its allowed actions are limited to: proceed as specified, or trigger a documented
  redesign. It cannot be used to tune the corpus toward a preferred H6 outcome.
- Round counts as complete when the results file has <2% error rate and
  `model_returned` has been checked for unexpected substitutions.
- A single model's error rate exceeding ~10% gets that model excluded and documented,
  not retried indefinitely — same rule as `2026-08-pilot.md`.

## Deviations

Logged here with a timestamp before analysis, not made silently.

*(none yet)*

---

Pre-registered: 2026-08-27
Corpus hash at pre-registration: `742fda6efa4bf166`
