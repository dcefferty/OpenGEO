# OpenGEO Keyword-Stuffing Intervention Pre-Registration — v3 — 2026-08

Committed before any row is written to a results file for this corpus. Per
`preregistrations/README.md`, the git timestamp on this file is the evidence; a
pre-registration committed after collection starts is not a pre-registration.

## Why a v3

Two prior baselines failed the same way. v1 (`preregistrations/2026-08-kwstuff.md`)
reused corpus v0.4's `treatment` variant wholesale — pooled CPR ~0.985, no headroom.
v2 (`preregistrations/2026-08-kwstuff-v2.md`) tried a "half-specific" recombination
baseline (one target fact stated specifically, the other left orthogonal), on the
theory that partial completeness would land between v0.4's true orthogonal control
(pooled CPR 0.503) and its full-answer treatment (pooled CPR 0.985). A pre-committed
real-model spot check (2,304 calls, 6 prompts, 0 errors) falsified that theory:
`moderate`-condition CPR came back 0.911–0.984 on every spot-checked prompt — the same
ceiling as v1. See `preregistrations/2026-08-kwstuff-v2.md`'s Deviations section for
the full diagnosis: these models appear to discriminate on presence vs. absence of
*any* specific, on-topic content, not on completeness of the answer. A document that
states even one concrete fact behaves like a fully-specific one, not a midpoint.

## Redesign

v3 does not attempt a new partial-specificity baseline. It returns to the one baseline
this project has **directly measured against real models and confirmed sits at a
genuine mid-range CPR**: corpus v0.4's actual `control` variant — zero specific facts
on either target fact, pooled CPR 0.503 across 8 models, individually confirmed
non-ceiling per model (range 0.383–0.591, see
`results/published/2026-08-25-corpus-v0.4-exploratory/REPORT.md`).

- `orthogonal` (new baseline) — corpus v0.4's `control` text, reused **verbatim, byte-
  for-byte, loaded programmatically from `corpus_v0.4.json` at build time** (not
  hand-copied) by `build_corpus_kwstuff_v3.py`. No new prose, no recombination.
- `stuffed` (unchanged role from v1/v2) — the SAME orthogonal content, with the
  prompt's core topic keyword (identical mapping to v1/v2) awkwardly repeated 4-8
  times where natural writing wouldn't. **No new facts added** — this is deliberately
  pure repetition layered onto content that doesn't answer the question any better,
  which is arguably a truer test of textbook SEO keyword stuffing than v1's or v2's
  designs (both of which paired stuffing with genuinely more informative content).
  Length-matched to `orthogonal` within ±3 words (verified: min -3, max +3, mean +1.2,
  per `build_corpus_kwstuff_v3.py`'s balance check).
- The other 5 documents per prompt, and the questions themselves, are byte-identical to
  `corpus_v0.4.json` — unchanged from v1/v2.

**What changed about the intervention itself:** none of the above changes H6 or what
falsifies it. What changed is that `stuffed` no longer adds new facts on top of the
baseline — v1 and v2 both stuffed keywords into content that stated real facts; v3
stuffs keywords into content that states none. This is a stricter, cleaner isolation of
"does repetition alone move citation" from "does repetition plus more facts move
citation," and it is the version consistent with the everyday meaning of keyword
stuffing (padding without added value).

## Hypothesis

**H6 (unchanged since v1). Keyword stuffing does not increase citation, and plausibly
decreases it,** relative to equally fact-complete natural prose. Falsified if the
paired effect is positive and its 95% CI excludes zero.

## Corpus

| | |
|---|---|
| corpus_version | `kwstuff-v3` |
| corpus_sha256 (16-char prefix) | `c414f8fcae725096` |
| base_corpus_version | `0.4` |
| supersedes | `kwstuff-v2` |
| File | `corpus/corpus_kwstuff_v3.json` |
| Structure | 48 prompts × 6 documents (blog, news, docs, product, forum, reference) = 288 documents |
| Target format balance | exactly 8 prompts per format |

**What was checked before trusting this, without spending on real models:** every
`orthogonal`/`stuffed` pair verified programmatically for (a) length match within ±3
words (confirmed: -3 to +3, mean +1.2), (b) no duplicate sentences within a document,
(c) every document ending on complete, grammatical punctuation, (d) `orthogonal` text
loaded directly from `corpus_v0.4.json` at build time rather than hand-transcribed, to
rule out drift from the text this project has real-model data on.

## Validation plan

Both v1 and v2 skipped or under-weighted real-model validation before committing to a
full round, and both failed for reasons inspection alone did not catch. v3's
`orthogonal` baseline is the one piece of this design with direct prior real-model
evidence (v0.4's actual control CPR), but the **combination** with stuffing has not
been tested — v2 already showed that a "should be fine" assumption about a
recombination can be wrong. So: **a real-model spot check of a subset of prompts runs
after this pre-registration is committed but before the full 18,432-call round**,
checking that (a) `orthogonal`-condition CPR here reproduces something close to v0.4's
already-measured ~0.50 (confirming the corpus wiring is correct, not just the text),
and (b) `stuffed` isn't pinned near 0% or 100%. This does not reopen the hypothesis,
corpus content, or analysis plan to revision based on favorable-looking results — only
a genuine ceiling/floor failure or a `model_returned` problem triggers a documented
deviation or a v4 redesign; anything else, the round proceeds as specified below.
Logged as a dated entry in Deviations either way.

## Models

Same 8, via OpenRouter, unchanged from v1/v2: `anthropic/claude-haiku-4.5`,
`openai/gpt-5.4-mini`, `google/gemini-3-flash-preview`, `x-ai/grok-4.3`,
`moonshotai/kimi-k2`, `deepseek/deepseek-chat`, `meta-llama/llama-4-maverick`,
`mistralai/mistral-medium-3`.

`kimi-k2` has a known elevated no-cite rate (13.3% on v0.4) and is excluded from pooled
figures per the same rule as every prior round — reported individually, not averaged in.

## Design

- **Conditions:** `orthogonal` (new baseline, v0.4's real control, natural prose),
  `stuffed` (keyword-stuffed, no new facts) — paired within prompt; only the target
  document differs between arms.
- **Runs per cell:** 24, per the established reliability floor (`CLAUDE.md`).
- **Temperature:** 1.0, fixed.
- **Document order:** randomized per run, seeded deterministically from
  `(corpus_version, run_key)`.
- **Total calls:** 8 models × 48 prompts × 2 conditions × 24 runs = **18,432** for the
  full round (excludes the small validation-spot-check subset, run and reported
  separately).
- **Estimated cost:** comparable to v1/v2, ~$5-14, per `run_pilot.py --dry-run`.

## Primary metric

**Citation Presence Rate (CPR)** — A1 in `METRICS.md`. Proportion of runs in which the
target document is cited. Reported per model with a Wilson 95% interval.

## Analysis plan

Identical machinery to v1/v2, applied via `analyze.py --runs <results file> --corpus
corpus/corpus_kwstuff_v3.json`:

- Paired per-prompt (stuffed − orthogonal) CPR delta, sign-flip permutation test on
  per-prompt differences, bootstrap CI on the pooled delta. Reported per model and pooled.
- H1 (reliability), H2/D1 (PSI), H3 (cross-model agreement), H5 (format × model
  interaction) re-checked on this corpus as replication checks.
- All inference permutation- or bootstrap-based, no distributional assumptions, per
  `CLAUDE.md`'s stack constraints.
- `orthogonal`-condition CPR reported prominently, per model and pooled, before the H6
  delta — same discipline v2 introduced, kept here since it's what would have caught
  v2's problem earlier if applied at spot-check scale from the start.

## Reporting rules

- **Whatever direction H6 comes back — positive, negative, or null — gets published
  with equal prominence.** Unchanged from v1/v2.
- If `orthogonal`-condition CPR here diverges materially from v0.4's already-measured
  ~0.50 for the same prompts, that gets reported plainly — it would mean something
  about the corpus wiring or the 6-document context changed between rounds, not just
  sampling noise, and is worth flagging regardless of what it means for H6.
- `kimi-k2` excluded from pooled figures per its no-cite rate, same as every prior round.
- `model_returned` checked against the requested model on every run before cross-run
  comparison.

## Stopping rule

- Fixed-n, not sequential, for the full round. All 18,432 cells run to completion (or
  resumed via `--resume` after interruption); no early stopping based on interim effect
  sizes.
- The validation spot check is exempt from "no early stopping" on the same terms as
  v2's: a pre-committed go/no-go gate on the *design*, not a peek at the *result*. Its
  only allowed actions are: proceed as specified, or trigger a documented redesign. It
  cannot be used to tune the corpus toward a preferred H6 outcome.
- Round counts as complete when the results file has <2% error rate and
  `model_returned` has been checked for unexpected substitutions.
- A single model's error rate exceeding ~10% gets that model excluded and documented,
  not retried indefinitely — same rule as `2026-08-pilot.md`.

## Deviations

Logged here with a timestamp before analysis, not made silently.

*(none yet)*

---

Pre-registered: 2026-08-28
Corpus hash at pre-registration: `c414f8fcae725096`
