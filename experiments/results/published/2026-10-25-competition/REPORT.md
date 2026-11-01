# OpenGEO — Specific Answer Against a Competitor (H9), Round competition-v1

**Published 2026-10-25. PRE-REGISTERED before collection** —
`preregistrations/2026-10-competition.md`, merged 2026-10-24 (PR #27), before any row in
`results/runs_competition.jsonl` existed. The pre-committed spot check passed all three
gates (logged in the pre-registration's Deviations section) before the full round ran.

## What this tests

H4 is the project's headline: replacing vague claims with specific figures raised target
CPR by +0.482 on corpus v0.4. In v0.4 the treated target is the only document that
answers the question, and the treatment arm saturates near 1.0. Real pages almost always
compete with another page that already states the answer.

This round adds that page. In two of four arms, one distractor is replaced by an
**answering competitor**: an authored document that states the same figures as the
treated target, in different words and a different format.

**H9 (falsifiable, stated before collection): with an answering competitor present,
stating the specific answer raises the target's citation rate.** Falsified if the
share-weighted `treatment_comp − control_comp` delta has a 95% bootstrap CI that
includes zero.

## Design

| | |
|---|---|
| Corpus | `corpus/corpus_competition.json`, sha `ae1a8844d11cb97f` |
| Base | corpus v0.4, all 48 prompts; target `control` and `treatment` reused verbatim |
| Documents | 6 per prompt; in the `_comp` arms one distractor is replaced by the competitor |
| Conditions | 4 — `control`, `treatment`, `control_comp`, `treatment_comp` (2×2 within prompt) |
| Engines | 5, share-weighted by `engine_weights.py` — 98.9% of measured gen-AI traffic |
| Runs per cell | 24 |
| Temperature | 1.0 |
| Total calls | 23,040, 0 errors, 0 `model_returned` mismatches |
| Collected | 2026-10-25 02:39–06:06 UTC (one interruption, see Deviations) |
| Spend | $21.42 logged (projected ~$25) |

No engine came near the 10% no-cite exclusion: Grok 1.0%, Claude 0.6%, ChatGPT 0.3%,
DeepSeek 0.3%, Gemini 0.0%. All five are included.

## Headline result — H9: the specific answer still wins against a competitor

Paired per (prompt, model), bootstrap over 48 prompts (10,000 resamples), sign-flip
permutation p (20,000). Share-weighted, as pre-registered.

| pool | `control_comp` | `treatment_comp` | delta | 95% CI | p |
|---|---|---|---|---|---|
| **share-weighted** | — | — | **+0.764** | **[+0.713, +0.812]** | <0.0001 |
| unweighted | 0.215 | 0.951 | +0.735 | [+0.684, +0.784] | <0.0001 |

**H9 is supported.** The interval is far from zero under either pooling, so unlike H7 the
conclusion does not turn on the weights.

The baseline belongs beside the delta. With a competitor that already answers, a page that
does not state the answer is cited in **0.215** of runs [0.205, 0.226]. Without the
competitor it was cited in 0.533. Stating the figures takes it to 0.951.

### Per engine (primary), Holm across five

| engine | weight | `control_comp` | `treatment_comp` | H9 delta | 95% CI | Holm p | reading |
|---|---|---|---|---|---|---|---|
| ChatGPT (gpt-5.4-mini) | 55.9% | 0.016 | 0.891 | **+0.875** | [+0.816, +0.926] | <0.0001 | estimate |
| Gemini 3 Flash | 28.4% | 0.450 | 1.000 | **+0.550** | [+0.448, +0.652] | <0.0001 | **floor** |
| Claude Haiku 4.5 | 9.4% | 0.095 | 0.865 | **+0.771** | [+0.699, +0.832] | <0.0001 | estimate |
| DeepSeek | 3.7% | 0.322 | 0.999 | **+0.677** | [+0.585, +0.764] | <0.0001 | **floor** |
| Grok 4.3 | 2.6% | 0.195 | 0.997 | **+0.802** | [+0.740, +0.859] | <0.0001 | **floor** |

Positive and significant on every engine. Per the saturation rule, the three engines whose
`treatment_comp` CPR is ≥ 0.98 (Gemini, DeepSeek, Grok) report a **floor** on their H9
effect, not an estimate: their treated target is cited in essentially every run, so the
true effect could be larger than the headroom allowed. ChatGPT and Claude are estimates.

ChatGPT carries the share-weighted figure. With the competitor present it almost never
cites the untreated target (0.016, 18 of 1,152 runs), so its delta is measured from close
to zero. That was flagged at the spot check (0/72) before the round ran.

## H4r — the replication without a competitor

| pool | delta | 95% CI | p |
|---|---|---|---|
| share-weighted | +0.499 | [+0.410, +0.587] | <0.0001 |
| unweighted | +0.464 | [+0.379, +0.549] | <0.0001 |

v0.4's figure (8 models, equal weight, August 2026) was +0.482 [+0.404, +0.563]. On this
five-engine panel, two months later, the H4 effect reproduces within its interval.
Per engine: Claude +0.598, ChatGPT +0.573, DeepSeek +0.431, Grok +0.378, Gemini +0.341,
every interval above zero. `treatment` CPR is 0.997 pooled, so H4r is still mostly
`1 − control`, as `METHODOLOGY.md` §9 says it would be.

## Secondary contrasts (Holm across the four, share-weighted)

| contrast | delta | 95% CI | Holm p |
|---|---|---|---|
| H9a interaction, (H9 − H4r) on target CPR | **+0.265** | [+0.181, +0.351] | <0.0001 |
| H9b competitor CPR, `treatment_comp − control_comp` | **−0.071** | [−0.106, −0.039] | <0.0001 |
| H9c target cited first (B1) | **+0.473** | [+0.445, +0.501] | <0.0001 |
| H9d target selection share (A2) | **+0.365** | [+0.336, +0.394] | <0.0001 |

**H9a: the competitor makes the effect bigger, not smaller.** This direction was
anticipated in the pre-registration as one of two outcomes and was not predicted. The
mechanism is visible in the arm means. The competitor barely touches a treated target
(0.997 → 0.951) and cuts an untreated one by more than half (0.533 → 0.215). Stating the
answer matters more when someone else already does.

Read H9a with the saturation caveat. Both treatment arms sit near the ceiling, so the
interaction is close to the difference between the two controls. It is positive on every
engine: Grok +0.424, ChatGPT +0.302, DeepSeek +0.247, Gemini +0.209, Claude +0.173, all
intervals above zero.

**H9b: stating the answer takes citations from the competitor, on two engines.** The
competitor is cited in 0.998 of `control_comp` runs, so it starts at the ceiling. When the
target is treated it drops on ChatGPT (1.000 → 0.896, −0.104 [−0.161, −0.054]) and
Claude (0.999 → 0.867, −0.132 [−0.191, −0.077]). On Gemini, DeepSeek and Grok it does not
move (all within ±0.005): those engines cite both answering documents. So on the two
engines that keep displacing, either the target or the competitor is left out about one
time in eight.

**H9c and H9d keep discriminating where CPR saturates.** With a competitor present,
treating the target raises the chance it is cited *first* by 0.473 and its share of the
answer's citations by 0.365. On the three saturated engines, these are the contrasts that
show the treated target winning the answer and not only appearing in it.

## Limitations

- **Synthesis stage only.** Retrieval is held constant: documents are supplied in context.
  This round says nothing about whether the treated page is retrieved in the first place.
- **One competitor, and it agrees with the target.** Two or more answering competitors
  (the dose question) and competitors stating different figures (H13) are not measured.
- **Three of five engines saturate.** Their H9 figures are floors, and the interaction is
  compressed toward the difference in controls.
- **The competitor is authored**, like every v0.4 document. Real-text replication remains
  the route to verbatim pages (`results/probes/2026-09-23-realtext-h4-design.md`).
- **Format is nested within prompt**, as in every v0.4-based round.
- **One corpus, one day.** 48 prompts across 24 domains, collected 2026-10-25.

## Reproduce

```bash
cd experiments
python3 corpus/build_corpus_competition.py         # sha ae1a8844d11cb97f
python3 analyze_competition.py --runs results/runs_competition.jsonl
```

All figures above come from that analyser's output (seeded). The per-engine H4r, H9a and
H9b figures use the same functions restricted to one engine.
