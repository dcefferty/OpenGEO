# OpenGEO — Length-Only Intervention (H7), Round lengthonly-v1

**Published 2026-09-11. PRE-REGISTERED before collection** —
`preregistrations/2026-09-lengthonly.md`, committed 2026-09-11, before any row in
`results/runs_lengthonly.jsonl` existed. This is a citable finding under this
project's own standard, not exploratory evidence.

## What this tests

Every corpus version in this project is length-matched within ±3 words, because length
is assumed to be a confound. That assumption had never been measured here. This round
measures it.

It is the sibling of kwstuff-v3. That round isolated *repetition*, holding length and
facts constant. This one isolates *length*, holding facts constant: the same document,
padded with discourse filler that states no fact, names no entity, contains no numeral,
and shares no content word with its own prompt question.

The question matters beyond housekeeping. The Princeton GEO paper's headline figures —
quoted industry-wide as fact about ChatGPT — come from interventions that *add* material
to a document without holding length fixed. If padding alone moves citation, some
unknown share of every one of those numbers is word count.

**H7 (falsifiable, stated before collection): adding words without adding facts does not
increase citation.** Falsified if the pooled `pad200` − `control` delta has a 95%
bootstrap CI excluding zero. **Direction was not predicted** — a decrease was recorded
in advance as an anticipated outcome so it could not be reported as a surprise.

## Design

| | |
|---|---|
| Corpus | `corpus/corpus_lengthonly.json`, sha256 `91671f3b8a750cd2` |
| Base | corpus v0.4 `control` text, reused verbatim (loaded programmatically) |
| Prompts | 48, across 24 domains, 8 per target format |
| Documents | 6 per prompt; the 5 non-target documents byte-identical across conditions |
| Conditions | 4 — `control`, `pad125`, `pad150`, `pad200` (achieved medians 1.00×, 1.31×, 1.58×, 2.06×) |
| Engines | 5, selected and weighted by market share — 98.9% of measured gen-AI traffic |
| Runs per cell | 24 |
| Temperature | 1.0 |
| Total calls | 23,040 |
| Spend | $23.28 (projected ~$25) |

The panel was narrowed from v0.4's inherited 8 models to the 5 that back consumer answer
engines, ranked by Similarweb's August 2026 traffic share, at the repo owner's direction
after the spot check. Both the narrowing and the amendment of a mis-specified gate are
logged in the pre-registration's deviations section, with the reasoning and the cost.
`perplexity/sonar` was evaluated and is structurally unmeasurable in Tier 1 — it ignores
supplied sources and performs live web search.

## Headline result — H7: padding → citation

Paired per (prompt, model). Pooled share-weighted, as pre-registered.

| contrast | delta | 95% CI | p | p (Holm) |
|---|---|---|---|---|
| pad125 (1.31×) | +0.001 | [−0.027, +0.028] | 0.938 | 1.000 |
| pad150 (1.58×) | +0.015 | [−0.006, +0.036] | 0.185 | 0.556 |
| **pad200 (2.06×)** | **+0.004** | **[−0.023, +0.031]** | **0.764** | **1.000** |

95% CIs are bootstrap over prompts, 10,000 resamples. p-values are sign-flip permutation
over condition labels within (prompt, model), 20,000 permutations, which is the
exchangeability the paired design gives. Holm correction across the three padded
contrasts. Seeded (`seed=0`) so every figure here re-runs identically.

**H7 is not falsified.** The pad200 interval includes zero, and so does every other
contrast. Doubling a document's length without adding a single fact moved its pooled
citation rate by four tenths of a percentage point.

Unweighted descriptive CPR by condition, for reference: control 0.542 [0.529, 0.555],
pad125 0.536, pad150 0.538, pad200 0.519 [0.506, 0.532].

Condition is also invisible in the variance decomposition. Across 23,040 runs, η² for
condition is **0.0003**, against prompt identity 0.3328, target format 0.0622, model
0.0576 and target slot 0.0004. Length is not where citation variance lives.

## The pooled null hides a directional split — read this before citing the headline

Per-engine results are primary in this project; the pooled figure is computed from them.
Here they disagree with each other, and that disagreement is the most interesting thing
in the round.

`pad200` − `control`, per engine, Holm-corrected across the five engines:

| engine | weight | control CPR | pad200 delta | 95% CI | p | p (Holm) |
|---|---|---|---|---|---|---|
| DeepSeek | 3.7% | 0.652 | **−0.057** | [−0.098, −0.018] | 0.009 | **0.035** |
| Claude Haiku 4.5 | 9.4% | 0.385 | **−0.055** | [−0.092, −0.019] | 0.006 | **0.030** |
| Grok 4.3 | 2.6% | 0.602 | −0.038 | [−0.069, −0.006] | 0.028 | 0.085 |
| ChatGPT (gpt-5.4-mini) | 55.9% | 0.423 | +0.008 | [−0.030, +0.046] | 0.697 | 0.697 |
| Gemini 3 Flash | 28.4% | 0.646 | +0.029 | [−0.002, +0.058] | 0.070 | 0.140 |

Three engines have intervals entirely below zero; **none has an interval entirely above
zero.** Two of the three negatives survive Holm correction across the panel. And the three negatives are exactly the three
lowest-weighted engines — 15.7% of the panel's weight between them — while the two
flat-to-positive engines carry 84.3%.

So the pooled headline is doing real work, and it is worth showing what happens without
it:

| arm | share-weighted (pre-registered) | unweighted |
|---|---|---|
| pad125 | +0.001 [−0.027, +0.028] p=0.94 | −0.006 [−0.022, +0.010] p=0.51 |
| pad150 | +0.015 [−0.006, +0.036] p=0.19 | −0.003 [−0.019, +0.011] p=0.66 |
| **pad200** | **+0.004 [−0.023, +0.031] p=0.76** | **−0.023 [−0.041, −0.005] p=0.018** |

**An unweighted pool over the same five engines would have falsified H7, in the negative
direction.** The pre-registered analysis is the one that counts — that is what
pre-registration is for, and the weights were fixed in `engine_weights.py` before
collection, not chosen after seeing this. But a reader is entitled to know that the
conclusion turns on a documented parameter rather than on the data alone.

`engine_weights.py` says of itself that the weights are "a *parameter*, not a finding,"
and that per-engine results remain primary. This round is the first one where that
disclaimer has teeth. Treat the honest summary as: **padding does not help on any engine,
does nothing on the two that carry most traffic, and measurably hurts on three smaller
ones.**

Neither the direction split nor a heterogeneity test was pre-registered. The per-engine
contrasts were, and are reported above; the observation that they split by direction is
post-hoc and needs replication before anyone builds on it.

## Dose-response (H7a)

Pre-registered as conditional — "if H7 is falsified" — and as Spearman's ρ on the four
condition means **per engine**. H7 was not falsified, so this is descriptive. It is also
the clearest view of the split above.

| engine | ρ | control | pad125 | pad150 | pad200 |
|---|---|---|---|---|---|
| Claude Haiku 4.5 | **−1.000** | 0.385 | 0.367 | 0.350 | 0.331 |
| DeepSeek | **−1.000** | 0.652 | 0.635 | 0.622 | 0.595 |
| Grok 4.3 | −0.400 | 0.602 | 0.587 | 0.603 | 0.564 |
| Gemini 3 Flash | +0.400 | 0.646 | 0.680 | 0.672 | 0.674 |
| ChatGPT | +0.600 | 0.423 | 0.412 | 0.444 | 0.431 |

Mean ρ = −0.280; not monotone on every engine.

Two engines decline **perfectly monotonically** with dose — every filler step costs
Claude and DeepSeek citations, in order, with no reversal. That is a stronger pattern
than the pooled contrast suggests, and it is the main reason the directional split in
the previous section should be taken seriously enough to replicate rather than dismissed
as three noisy intervals. With four points ρ = ±1 is not itself significant evidence;
two engines landing on it in the same direction, consistent with their pad200 contrasts,
is what makes it worth reporting.

## Metric divergence (H7b)

Pre-registered as descriptive, with no test for the difference between metrics.

| metric | pad200 delta | 95% CI |
|---|---|---|
| CPR | +0.0043 | [−0.0220, +0.0304] |
| B2 Attributed Content Share | +0.0016 | [−0.0067, +0.0098] |

B2 was hypothesized to be *more* sensitive to padding than CPR. It is not — its interval
includes zero and is narrower than CPR's. Padding a
document does not win it a larger share of the answer's sentences either.

This is a small point against the position-adjusted word count family of metrics that
GEO-bench used. The independent 16-arm replication cited in the pre-registration measured
**+29% from padding alone on a PAWC-style share metric**. Measured directly, on attributed
sentence share rather than a decay-weighted word count, with length as the only thing
that varies: nothing.

## The other hypotheses — published with equal prominence

From `analyze.py` on the same 23,040 runs:

- **A1 target CPR, overall 0.534.** Per engine: Gemini 0.668, DeepSeek 0.626, Grok 0.589,
  ChatGPT 0.427, Claude 0.358.
- **H2 / D1 position sensitivity: SUPPORTED.** Mean PSI 0.080. Significant on three of
  five engines. The pooled slot profile is flat (0.524–0.554) — the position effect is
  real per-engine but does not share a common shape across them.
- **H3 cross-model agreement: NOT SUPPORTED.** Cross-model W 0.836 [0.804, 0.864] against
  a within-model noise floor of 0.813 [0.780, 0.844] — gap −0.023. No evidence these
  engines rank sources differently from one another on this corpus.
- **H5 format universality: SUPPORTED.** Format η² 0.062 against interaction η² 0.012
  (p=0.0005, Freedman-Lane). Product (0.717) and news (0.640) documents are cited far
  more than blog (0.357), consistently in rank across engines. Both caveats in
  `analyze.py`'s output apply: format is nested within prompt in this design, and the
  interaction test runs on raw probability rather than log-odds, which manufactures
  apparent interaction from sigmoid position alone.

## Limitations

- **Synthesis stage only.** Retrieval is held constant; documents are supplied in
  context. This says nothing about whether a longer page gets retrieved in the first
  place — and length plausibly matters more there than here. A page that nobody
  retrieves cannot be cited regardless of what this round measured.
- **The weighting choice determines the headline.** Stated above rather than buried.
- **Filler is one kind of length.** These documents were padded with topic-neutral
  discourse filler. A document lengthened with *relevant but non-novel* prose is a
  different intervention and is not tested here. The result licenses "words alone don't
  help," not "length never matters."
- **Headroom was adequate but asymmetric.** The pre-registration warned that Gemini
  (spot-check control CPR 0.847) and Grok (0.819) had compressed headroom for detecting
  an *increase*. At full scale both came in far lower — 0.646 and 0.602 — so the warning
  did not materialize, but it was recorded before collection and is kept here.
- **One corpus, one day.** 48 prompts across 24 domains, collected 2026-09-11.
- **Two engines excluded by the standing data-health rule** before this round:
  `moonshotai/kimi-k2` and `mistralai/mistral-medium-3`. All five panel engines passed
  comfortably — no-cite rates 0.1%–2.1% against a 10% threshold.

## Data health

23,040 of 23,040 cells collected successfully. **0 `model_returned` mismatches** — no
silent OpenRouter reroutes. 258 runs (1.1%) cited nothing parseable, within normal range
and not concentrated in any condition.

The results file contains **455 error rows**. These are retry artifacts, not
observations: 410 HTTP 429 rate-limit responses and 17 HTTP 504 provider timeouts on
`deepseek/deepseek-chat`, plus earlier transients. Failed calls are not billed, are
retried by `--resume`, and are skipped by both analyzers. The 429s were self-inflicted —
concurrency was raised mid-run and DeepSeek's provider rate-limited; the fix was to run
that model in its own queue at concurrency 2. Every affected cell was subsequently
collected. No cell is missing and no partial cell is averaged in.

## Reproducing this

```bash
python3 corpus/build_corpus_lengthonly.py    # regenerate; verify sha256 starts 91671f3b8a750cd2
python3 check_variants.py                    # independent re-verification of the filler constraints

python3 analyze_lengthonly.py                # H7 primary, dose-response, B2, per-engine
python3 analyze.py --runs results/runs_lengthonly.jsonl --corpus corpus/corpus_lengthonly.json
```

`analyze.py`'s H4 block is hard-coded to a two-arm `control`/`treatment` design and
prints an empty table on this round's four-arm ladder. `analyze_lengthonly.py` implements
the pre-registered plan — share-weighted pooling, bootstrap over prompts, permutation
over condition labels within (prompt, model), Holm across the three padded contrasts —
and is the authoritative source for every H7 figure above.

**The null was verified two ways before it was reported.** A null produced by an
unexercised analyzer is indistinguishable from a bug, and this round's whole value is in
its null.

1. *Planted-effect recovery.* Injecting a known +0.08 shift into the `pad200` arm and
   re-running returned +0.090, 95% CI [+0.058, +0.122], p<0.0001, with the untouched
   `pad125` and `pad150` contrasts unchanged. The analyzer detects an effect of the size
   it is claiming is absent.
2. *Independent reimplementation.* The primary contrast was computed a second time from
   the raw records by a separate implementation written without reference to the first,
   differing in how it applies the share weights (within-prompt then equal-weight across
   prompts, versus a global weighted mean). The two agree to three decimal places on
   every contrast — pooled pad200 +0.004 against +0.004 — and on all five per-engine
   deltas. The committed script is the within-prompt version, which is the correct one
   when a cell is ever missing.

Raw data (`results/runs_lengthonly.jsonl`) and corpus (`corpus/corpus_lengthonly.json`)
are committed. Every run record carries full provenance: model, `model_returned`,
presentation order, target slot, condition, token usage and cost, and the raw response
text — not just extracted citations.

## License

Code MIT. This data and analysis are CC-BY-4.0 — cite it, quote it, build on it, with
attribution. See `LICENSE`.
