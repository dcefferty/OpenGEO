# OpenGEO — Conflicting Figures (H13), Round conflict-v1

**Published 2026-11-03. PRE-REGISTERED before collection** —
`preregistrations/2026-11-conflict.md`, merged 2026-11-02 (PR #30), before any row in
`results/runs_conflict.jsonl` existed. The pre-committed spot check passed both gates
(PR #31) before the full round ran.

## What this tests

H9 found that stating the specific answer raises citation by +0.764 even when a competitor
already states it. That competitor stated the *same* figures. This round asks what happens
when your page states *different* ones.

Three versions of the target page sit beside the same answering competitor and four other
documents, which are byte-identical across versions:

- `control_comp`: the page is vague and states no figure.
- `agree`: the page states the competitor's figures.
- `conflict`: the same page states different, plausible figures. Nothing else changes.

**H13 (falsifiable, stated before collection): disagreeing with an answering competitor
costs citation.** Falsified if the share-weighted `agree − conflict` delta has a 95%
bootstrap CI that includes zero.

## Design

| | |
|---|---|
| Corpus | `corpus/corpus_conflict.json`, sha `4d27315abb2f1a7a` |
| Base | competition-v1, all 48 prompts; `control_comp` and `agree` reused verbatim |
| Conditions | 3 — `control_comp`, `agree`, `conflict` |
| Engines | 5, share-weighted by `engine_weights.py` — 98.9% of measured gen-AI traffic |
| Runs per cell | 24 |
| Temperature | 1.0 |
| Total calls | 17,280 usable runs, 0 `model_returned` mismatches (56 rate-limited calls retried, see Deviations) |
| Collected | 2026-11-03 02:42–05:57 UTC |
| Spend | $16.35 logged (projected ~$16) |

No engine came near the 10% no-cite exclusion: Grok 0.6%, Claude 0.3%, DeepSeek 0.1%,
ChatGPT 0.0%, Gemini 0.0%. All five are included.

## Headline — H13 is supported, and ChatGPT carries it

| pool | `agree` | `conflict` | delta | 95% CI | p |
|---|---|---|---|---|---|
| **share-weighted** | 0.932 | 0.730 | **+0.203** | **[+0.164, +0.241]** | <0.0001 |
| unweighted | 0.948 | 0.860 | +0.088 | [+0.061, +0.117] | <0.0001 |

**H13 is supported.** Both pools exclude zero. But the weighted figure is more than twice
the unweighted one, and the per-engine table shows why.

### Per engine (primary), Holm across five

| engine | weight | `agree` | `conflict` | H13 delta | 95% CI | Holm p | reading |
|---|---|---|---|---|---|---|---|
| ChatGPT (gpt-5.4-mini) | 55.9% | 0.905 | 0.555 | **+0.351** | [+0.289, +0.414] | <0.0001 | estimate |
| Gemini 3 Flash | 28.4% | 1.000 | 0.970 | **+0.030** | [+0.011, +0.057] | 0.0004 | **floor** |
| Claude Haiku 4.5 | 9.4% | 0.848 | 0.922 | **−0.074** | [−0.125, −0.020] | 0.021 | estimate |
| DeepSeek | 3.7% | 0.997 | 0.884 | **+0.113** | [+0.064, +0.166] | <0.0001 | **floor** |
| Grok 4.3 | 2.6% | 0.990 | 0.970 | +0.020 | [−0.005, +0.053] | 0.221 | **floor** |

The engines split three ways:

- **ChatGPT chooses.** A page that contradicts the competitor drops from 0.905 to 0.555.
  ChatGPT carries 55.9% of the share weight, so it accounts for most of the pooled figure.
- **Gemini, DeepSeek and Grok mostly keep citing both.** Their losses are small (Gemini,
  Grok) or moderate (DeepSeek). All three `agree` arms saturate, so these are floors.
- **Claude goes the other way.** It cites a contradicting page *more* often (0.848 →
  0.922), with an interval clear of zero after Holm. This was not predicted. The
  pre-registration stated a positive direction, so this is reported as the surprise it is.

"Disagreeing costs citation" is true of the traffic-weighted panel and of ChatGPT. It is
not true of every engine.

## What the answers do with a conflict: they mostly report it

Adoption was read mechanically from the answer text. The reader had a 0.02% false-positive
rate on H9's answers.

| engine | competitor's figure only | your figure only | both | neither | share correct, among those that pick |
|---|---|---|---|---|---|
| ChatGPT | 504 | 290 | 323 | 35 | 0.635 |
| Gemini | 38 | 24 | 1,074 | 16 | 0.613 |
| Claude | 102 | 78 | 947 | 25 | 0.567 |
| DeepSeek | 213 | 69 | 845 | 25 | 0.755 |
| Grok | 39 | 28 | 1,061 | 24 | 0.582 |

**74% of `conflict` answers (4,250 of 5,760) state both figures.** Typically they say the
sources disagree and attribute each figure to its source. Gemini, Grok and Claude do this
in over 80% of answers. That is why they keep citing the contradicting page, and why Claude
cites it more: to attribute the second figure, it has to cite the page that states it.
Claude cites both pages in 0.871 of `conflict` runs against 0.711 in `agree`.

ChatGPT does it in 28%, and usually picks one figure. When it picks, it cites one page.
Both pages are cited in 0.306 of its `conflict` runs against 0.813 in `agree`.

**When an answer does pick one figure, it picks the competitor's more often than yours.**
That is H13c: a share-weighted share of **0.656** (+0.156 over a coin flip
[+0.061, +0.246], Holm p = 0.004). In this design the competitor's figure is the original,
realistic one. On `world` prompts, where the engine may know the answer, the share is
0.713 [0.614, 0.805] across 32 prompts. On `document` prompts, about fictional products,
it is 0.534 [0.343, 0.715] across 15 prompts, an interval that includes a coin flip.
`travel_visa` drops out of the adoption share because no engine picked a single figure
there.

## Secondary contrasts (Holm across the four, share-weighted)

| contrast | delta | 95% CI | Holm p |
|---|---|---|---|
| H13a contradicted figure vs no figure (`conflict − control_comp`) | **+0.557** | [+0.499, +0.617] | <0.0001 |
| H13b competitor CPR, `conflict − agree` | **−0.082** | [−0.111, −0.055] | <0.0001 |
| H13c adoption, share picking the competitor's figure − 0.5 | **+0.156** | [+0.061, +0.246] | 0.004 |
| H13d H13 in `world` minus H13 in `document` prompts | −0.005 | [−0.090, +0.087] | 0.91 |

**H13a: a contradicted figure still beats no figure, by a wide margin, on every engine.**
Per engine: Claude +0.846, Grok +0.801, ChatGPT +0.530, DeepSeek +0.508, Gemini +0.499,
all intervals above zero. A page that states a figure the competitor disputes is cited far
more than a vague page. Being contradicted costs less than not answering.

**H13b: the competitor loses too, not gains.** The pre-registration asked whether a rival
gains when contradicted. Pooled, it loses 0.082. That is ChatGPT again (−0.158
[−0.207, −0.110]): when it picks one page, either side can lose. On Claude the competitor
*gains* (+0.086 [+0.046, +0.132]), for the same both-sides reason as the target. Gemini,
DeepSeek and Grok move it by 0.03 or less.

**H13d: no evidence that outside knowledge changes the citation cost.** Disagreeing cost
about the same on general facts as on facts about fictional products. The interval is wide
(±0.09), as the pre-registration warned. The adoption split above is suggestive in the
direction H13d asked about, but that comparison was not pre-registered as a test.

## What this means for a page

- **State the figure even if a competitor disputes it.** A disputed figure is cited far
  more than a vague page (H13a, every engine).
- **Agreeing is better than disagreeing on ChatGPT,** the engine with most of the traffic.
  It tends to pick one source when sources conflict, and it picks the other side's figure
  more often than yours.
- **On most other engines, a conflict gets reported, not resolved.** The answer states both
  figures and cites both pages. Your figure appears, but beside the competitor's.

## Limitations

- **Synthesis stage only.** Retrieval is held constant: documents are supplied in context.
- **The target is always the side that moves.** The competitor always holds the original,
  realistic figure. A design where the competitor is wrong would need a non-target document
  to change, which breaks this project's paired design. The adoption result could partly
  reflect "the original figure" as much as "the other page's figure."
- **"Correct" is only defined on `world` prompts**, and even there the engines were not
  asked what they know. On `document` prompts the round measures agreement with another
  source, not truth.
- **One conflicting competitor at one magnitude per prompt.** Corroboration (two sources
  against one) and graded discrepancies are untested.
- **Three of five engines saturate in `agree`**, so their H13 figures are floors.
- **The weighting carries the headline.** The share-weighted pool is the pre-registered
  decision. The unweighted pool is less than half its size, and one engine points the other
  way.
- **The documents are authored**, and format is nested within prompt.
- **One corpus, one day.** 48 prompts across 24 domains, collected 2026-11-03.

## Reproduce

```bash
cd experiments
python3 corpus/build_corpus_conflict.py            # sha 4d27315abb2f1a7a
python3 analyze_conflict.py --runs results/runs_conflict.jsonl
```

All figures above come from that analyser's output (seeded). The per-engine H13a and H13b
figures, the both-cited rates and the share-weighted arm means use the same functions
restricted to one engine.
