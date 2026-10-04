# OpenGEO Keyword-Stuffing Intervention Pre-Registration — 2026-08

Committed before any row is written to a results file for this corpus. Per
`preregistrations/README.md`, the git timestamp on this file is the evidence; a
pre-registration committed after collection starts is not a pre-registration.

Unlike the claim-density corpus (v0.2–v0.4), which was validated prompt-by-prompt
against real models *as it was built* because the risk was "does the content answer
the question at all" (the ceiling problem), this corpus is authored and internally
audited *before* any real-model call. The thing under test here is a keyword-repetition
pattern layered on top of content that's already proven, on the v0.4 corpus, not to
have a ceiling problem — so there is no equivalent iterative-validation risk to guard
against before committing to a design.

## Hypothesis

**H6. Keyword stuffing does not increase citation, and plausibly decreases it,** relative
to equally fact-complete natural prose. Falsified if the paired effect is positive and
its 95% CI excludes zero.

This is a different bet than H4 (claim density). H4 tested whether *specificity* raises
citation odds — it does, decisively (see `results/published/2026-08-25-corpus-v0.4-exploratory/REPORT.md`).
H6 tests whether *unnatural repetition of a topic keyword*, independent of specificity,
helps, hurts, or does nothing. `METRICS.md` already flags self-promotional tone as a
hypothesized negative signal; no one in the GEO industry has tested keyword stuffing
against real 2026 models. A null, a negative result, or a positive result are all
publishable — this project has no stake in which one is true, only in reporting whichever
one the data supports.

## Corpus

| | |
|---|---|
| corpus_version | `kwstuff-v1` |
| corpus_sha256 (16-char prefix, as printed by `build_corpus_kwstuff.py`) | `4fb871f7bc0e8c19` |
| base_corpus_version | `0.4` (reuses v0.4's 48 prompts, domains, and 5 non-target distractors per prompt wholesale) |
| File | `corpus/corpus_kwstuff_v1.json` |
| Structure | 48 prompts × 6 documents (blog, news, docs, product, forum, reference) = 288 documents |
| Target format balance | exactly 8 prompts per format |

**Design of the intervention pair**, per target document:
- `control` — the *same* text as corpus v0.4's already-validated `treatment` variant:
  natural, fact-dense prose that states the specific fact the question asks for once.
- `treatment` (stuffed) — the same facts, with the prompt's core topic phrase (e.g.
  "uptime monitoring", "chef's knife") awkwardly repeated 4–8 times where natural
  writing would not repeat it — the textbook SEO keyword-stuffing pattern. Length-matched
  to control within ±3 words (target pair delta: mean −0.2, max |Δ| 3, verified by
  `build_corpus_kwstuff.py`'s own balance check), so any effect is attributable to
  repetition, not length.

The other 5 documents per prompt, and the questions themselves, are byte-identical to
`corpus_v0.4.json` — only the target's two variants differ from that corpus. This
reuses content already proven not to have a ceiling problem, rather than re-deriving it.

**What was checked before trusting this, without spending on real models:** every
control/stuffed pair was verified programmatically for (a) length match within ±3
words, (b) no duplicate sentences within a document, (c) every document ending on
complete, grammatical punctuation. This catches authoring bugs, not scientific risk —
it is not a substitute for real-model validation of the earlier corpora's ceiling
problem, because that problem doesn't apply here (see above).

## Models

Same 8, via OpenRouter, as `preregistrations/2026-08-pilot.md` and the v0.3/v0.4 runs:
`anthropic/claude-haiku-4.5`, `openai/gpt-5.4-mini`, `google/gemini-3-flash-preview`,
`x-ai/grok-4.3`, `moonshotai/kimi-k2`, `deepseek/deepseek-chat`,
`meta-llama/llama-4-maverick`, `mistralai/mistral-medium-3`.

`kimi-k2` has a known elevated no-cite rate (13.3% on v0.4) and is excluded from pooled
figures per the same rule as every prior round — reported individually, not averaged in.

## Design

- **Conditions:** `control` (natural), `treatment` (keyword-stuffed) — paired within
  prompt; only the target document differs between arms.
- **Runs per cell:** 24, per the established reliability floor (`CLAUDE.md`).
- **Temperature:** 1.0, fixed.
- **Document order:** randomized per run, seeded deterministically from
  `(corpus_version, run_key)`.
- **Total calls:** 8 models × 48 prompts × 2 conditions × 24 runs = **18,432**.
- **Estimated cost:** $4.79–$13.65 (low/mid tier), per `run_pilot.py --dry-run`.

## Primary metric

**Citation Presence Rate (CPR)** — A1 in `METRICS.md`. Proportion of runs in which the
target document is cited. Reported per model with a Wilson 95% interval.

## Analysis plan

Identical machinery to H4, applied to this corpus via `analyze.py --runs
<results file> --corpus corpus/corpus_kwstuff_v1.json`:

- Paired per-prompt (stuffed − control) CPR delta, sign-flip permutation test on
  per-prompt differences, bootstrap CI on the pooled delta. Reported per model and pooled.
- H1 (reliability), H2/D1 (PSI), H3 (cross-model agreement), H5 (format × model
  interaction) are re-checked on this corpus as replication checks, not because this
  round is designed to test them specifically — a divergence from their v0.4 verdicts
  here would itself be worth reporting.
- All inference permutation- or bootstrap-based, no distributional assumptions, per
  `CLAUDE.md`'s stack constraints.

## Reporting rules

- **Whatever direction H6 comes back — positive, negative, or null — gets published with
  equal prominence.** This is stated explicitly because H6 is, unlike H4, a hypothesis
  this project actively expects might go the "wrong" way (i.e., stuffing having no
  effect, which is the boring outcome), and the point of pre-registering is to remove
  any temptation to bury that.
- `kimi-k2` excluded from pooled figures per its no-cite rate, same as every prior round.
- `model_returned` checked against the requested model on every run before cross-run
  comparison.

## Stopping rule

- Fixed-n, not sequential. All 18,432 cells run to completion (or resumed via
  `--resume` after interruption); no early stopping based on interim effect sizes.
- Round counts as complete when the results file has <2% error rate and
  `model_returned` has been checked for unexpected substitutions.
- A single model's error rate exceeding ~10% gets that model excluded and documented,
  not retried indefinitely — same rule as `2026-08-pilot.md`.

## Deviations

Logged here with a timestamp before analysis, not made silently.

*(none yet)*

---

Pre-registered: 2026-08-26
Corpus hash at pre-registration: `4fb871f7bc0e8c19`
