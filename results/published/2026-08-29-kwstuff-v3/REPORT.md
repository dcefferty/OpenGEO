# OpenGEO — Keyword-Stuffing Intervention (H6), Round kwstuff-v3

**Published 2026-08-29. PRE-REGISTERED before collection** —
`preregistrations/2026-08-kwstuff-v3.md`, committed 2026-08-28, before any row in
`results/runs_kwstuff_v3.jsonl` existed. This is a citable finding under this
project's own standard, not exploratory evidence.

## What this tests

Does keyword stuffing — awkwardly repeating a document's core topic phrase, without
adding any new facts — change the odds that an AI answer engine cites it, holding
retrieval constant? Conventional SEO wisdom treats stuffing as either useless or
actively penalized; `METRICS.md` flags self-promotional tone as a hypothesized
negative signal. No public GEO benchmark has tested this against real 2026 models.

**H6 (falsifiable, stated before collection): keyword stuffing does not increase
citation, and plausibly decreases it,** relative to equally fact-complete natural
prose. Falsified if the paired effect is positive and its 95% CI excludes zero.

## It took three tries to get a real answer

This round is the third corpus design for this intervention, and the story of why the
first two failed is part of the result:

- **v1** reused corpus v0.4's `treatment` variant (the claim-density experiment's
  fully-specific text) wholesale as its "natural" baseline. That text sits at ~98.5%
  pooled CPR — no headroom for stuffing to move citation in either direction. Result:
  an uninformative null (pooled delta −0.001, p=0.57), with 5 of 8 models showing zero
  variance in the baseline cell.
- **v2** tried a "half-specific" baseline — one of a question's two target facts
  stated concretely, the other left topically orthogonal — on the theory that partial
  completeness would land midway between v0.4's real orthogonal control (pooled CPR
  0.503) and its full-answer treatment (pooled CPR 0.985). A real-model spot check
  (2,304 calls, pre-committed before the full round) falsified that theory before any
  money was spent on the full run: the half-specific baseline hit **0.911–0.984 CPR on
  every spot-checked prompt** — the same ceiling as v1. These models, it turns out,
  don't discriminate on *completeness* of an answer, only on whether a document
  contains *any* specific, on-topic fact versus none. Half an answer behaves like a
  whole one.
- **v3** (this round) abandoned the "partial answer" axis and went back to the one
  baseline this project had *already measured against real models*: corpus v0.4's
  actual orthogonal control text (zero specific facts on either target fact, pooled
  CPR 0.503, individually confirmed non-ceiling per model). Stuffing was layered onto
  that unmodified text, with no new facts added — arguably a truer test of textbook
  SEO keyword stuffing than v1 or v2 attempted, since real stuffing pads without
  adding value. A pre-committed spot check confirmed real headroom (per-prompt CPR
  0.17–0.87, no cell pinned at 0% or 100%) before the full round ran.

Full diagnosis for both failures, including the spot-check data, is in
`preregistrations/2026-08-kwstuff-v2.md` (v2's Deviations section) and
`preregistrations/2026-08-kwstuff-v3.md` (this round's Deviations section, including
the passing spot check and the final result below).

## Design

| | |
|---|---|
| Corpus | kwstuff-v3, `corpus/corpus_kwstuff_v3.json`, sha `c414f8fcae725096` |
| Base corpus | v0.4 (`corpus_v0.4.json`) — same 48 prompts, 24 domains, questions, and 5 non-target distractors per prompt, reused unchanged |
| Documents | 6 per prompt, one per format: blog, news, docs, product, forum, reference |
| Target format balance | exactly 8 prompts per format |
| Conditions | paired — `orthogonal` (v0.4's real control text, verbatim) vs. `stuffed` (same text, topic keyword repeated 4-8 times, no new facts); only the target document differs between arms, length-matched within ±3 words |
| Models | 8, via OpenRouter: `claude-haiku-4.5`, `gpt-5.4-mini`, `gemini-3-flash-preview`, `grok-4.3`, `kimi-k2`, `deepseek-chat`, `llama-4-maverick`, `mistral-medium-3` |
| Runs per cell | 24 |
| Temperature | 1.0 (the model's natural distribution, not lowered for stability) |
| Document order | randomized per run from a seeded hash, recorded every run |
| Total calls | 18,432, 0 errors, 0 `model_returned` mismatches |
| Raw data | `results/runs_kwstuff_v3.jsonl`, git commit `8546889` |

Retrieval is held constant by construction — documents are supplied directly in
context. This measures the synthesis stage only: what a model does with content it
already has, not whether that content gets retrieved in the first place.

## Headline result — H6: keyword stuffing → citation

**H6 is falsified.** Pooled across 7 models (`kimi-k2` excluded from pooled figures
per its known elevated no-cite rate — see Limitations): orthogonal CPR 0.517, stuffed
CPR 0.555, **delta +0.038, 95% bootstrap CI [+0.004, +0.075], sign-flip permutation
p=0.045.** The CI excludes zero on the positive side. Keyword stuffing did not
decrease citation as hypothesized — it measurably, if modestly, **increased** it.

| Model | Orthogonal CPR | Stuffed CPR | Delta | 95% CI | p |
|---|---|---|---|---|---|
| claude-haiku-4.5 | 0.378 | 0.385 | +0.008 | [-0.047,+0.064] | 0.807 |
| deepseek-chat | 0.564 | 0.623 | +0.059 | [+0.012,+0.115] | 0.027 |
| gemini-3-flash-preview | 0.661 | 0.706 | +0.044 | [-0.001,+0.092] | 0.078 |
| llama-4-maverick | 0.418 | 0.453 | +0.035 | [-0.023,+0.093] | 0.246 |
| mistral-medium-3 | 0.548 | 0.542 | -0.006 | [-0.055,+0.047] | 0.819 |
| kimi-k2 (excl. from pooled) | 0.417 | 0.464 | +0.048 | [+0.010,+0.086] | 0.019 |
| gpt-5.4-mini | 0.439 | 0.498 | +0.059 | [+0.019,+0.104] | 0.006 |
| grok-4.3 | 0.612 | 0.676 | +0.064 | [+0.004,+0.130] | 0.050 |
| **7-model pooled (excl. kimi-k2)** | **0.517** | **0.555** | **+0.038** | **[+0.004,+0.075]** | **0.045** |

4 of 7 pooled models are individually significant in the positive direction
(deepseek-chat, gpt-5.4-mini, grok-4.3, each p<0.05); gemini-3-flash-preview is
marginal (p=0.078); only mistral-medium-3 sits near zero, and it is not significantly
negative. `kimi-k2`, though excluded from the pooled figure, shows the same positive
direction (p=0.019) — its exclusion does not flip the result. **No model shows a
significant effect in the hypothesized negative direction.** This is a modest effect,
not a large one, and the pooled p-value is close to the conventional 0.05 threshold —
this is reported as a real but small positive effect, not a dramatic one.

## Why this might be true

This project has no stake in which direction H6 came back, but a plausible mechanism
is worth naming: these models appear to select citations largely on topical relevance
signals — does this document's language match the question's subject — rather than on
prose quality or restraint. A document that repeats "uptime monitoring" eight times is,
in a shallow lexical-overlap sense, more insistently *about* uptime monitoring than one
that mentions it twice gracefully. If citation selection leans on that kind of surface
signal, stuffing is not being penalized for reading badly; it is winning a relevance
contest it was never supposed to be able to enter. This is speculative and not
something this round's data can confirm mechanistically — it would take a
sentence-level attribution study (Group C metrics, not yet built — see
`METRICS.md`) to test directly.

## The other hypotheses — published with equal prominence

| H | Result | Verdict |
|---|---|---|
| H1 — reliability at n=24 | Spearman-Brown 0.923–0.963 for every model; pooled reliability usable from n=4 | Supported |
| H2 — position effect (PSI) is material | Mean PSI 0.109, p<0.05 for 5 of 8 models | Supported |
| H3 — cross-model agreement on citation-worthiness is low | Cross-model Kendall's W 0.798 [0.761,0.833] vs. within-model noise floor 0.766 [0.729,0.801] (gap −0.033) | **Not supported** — models agree with each other about as much as they agree with themselves, replicating the v0.4 finding on an independent corpus |
| H5 — format × model interaction dominates main effects | η²(interaction)=0.029, p=0.0005, vs. η²(format)=0.045, η²(model)=0.042 | Supported (interaction does not dominate) — see Limitations for two scale caveats carried over from v0.4 |

H3 replicating cleanly on a second, independent corpus (different intervention,
different baseline documents) is worth noting on its own: it's now been tested twice
and come back the same way both times, which is stronger evidence against the
"each engine is its own optimization problem" narrative than either round alone.

## Variance decomposition — where citation variance actually lives

| Factor | η² | Levels | Range |
|---|---|---|---|
| Prompt | **0.279** | 48 | 0.042–0.977 |
| Domain | 0.143 | 24 | 0.120–0.799 |
| Content format | 0.045 | 6 | 0.360–0.659 |
| Model | 0.042 | 8 | 0.382–0.684 |
| Condition (keyword stuffing) | 0.002 | 2 | 0.517–0.555 |
| Target slot (position) | 0.001 | 6 | 0.500–0.546 |

Keyword stuffing is real and statistically significant, but it explains very little of
the overall variance in citation — which fact/prompt is being asked about, and which
domain it's in, dominate by a wide margin. This is a genuine effect, not a lever with
much practical leverage relative to what content actually says.

## Limitations

- **Modest effect size, borderline pooled significance.** The 95% CI's lower bound
  (+0.004) is close to zero; this is a real but small effect, not a decisive one. A
  larger round (more prompts or more runs) would tighten this considerably.
- **Synthesis stage only.** Retrieval is held constant by design; this says nothing
  about whether a heavily keyword-stuffed page gets retrieved, ranked, or penalized
  upstream of the context window it never gets shown here. See `METHODOLOGY.md` §2.
- **`kimi-k2` has an elevated no-cite rate** (12.1% of runs produced no parseable
  citation this round, consistent with 13.3% on v0.4) — an instruction-following
  weakness, not a visibility signal. Excluded from pooled figures; its own per-model
  result is directionally consistent with the pooled finding and does not change the
  conclusion either way.
- **The mechanism is not measured directly here.** The "topical relevance via lexical
  overlap" explanation above is a plausible reading of the result, not something this
  round's data confirms at the sentence level.
- **Format is nested within prompt** (8 prompts per format) and the H5 interaction
  test operates on raw CPR rather than log-odds — same two caveats as v0.4's report;
  see the CAVEAT text printed by `analyze.py`'s H5 section for the exact statement.
- **The corpus was authored, not sampled from the wild** — the `orthogonal` baseline
  is reused verbatim from v0.4 rather than newly written, but `stuffed` was authored
  for this round following a documented method
  (`corpus/build_corpus_kwstuff_v3.py`).

## Reproducing this

```bash
python3 corpus/build_corpus_kwstuff_v3.py                              # regenerates corpus_kwstuff_v3.json; verify sha matches c414f8fcae725096
python3 analyze.py --runs results/runs_kwstuff_v3.jsonl --corpus corpus/corpus_kwstuff_v3.json
```

The pooled H6 figures above (kimi-k2 excluded) are computed directly from the raw
per-run records rather than `analyze.py`'s built-in "ALL MODELS POOLED" line, which
includes all 8 models — see `preregistrations/2026-08-kwstuff-v3.md` for the exact
recomputation.

Raw data (`results/runs_kwstuff_v3.jsonl`) and corpus (`corpus/corpus_kwstuff_v3.json`)
are committed at git commit `8546889` and after. Every run record carries full
provenance: model, `model_returned` (checked against silent OpenRouter reroutes),
presentation order, target slot, condition, and the raw response text — not just
extracted citations.

## License

Code MIT. This data and analysis are CC-BY-4.0 — cite it, quote it, build on it, with
attribution. See `LICENSE`.
