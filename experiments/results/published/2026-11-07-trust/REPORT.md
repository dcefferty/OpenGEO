# OpenGEO — Trust Signals (H10–H12), Round trust-v1

**Published 2026-11-07. PRE-REGISTERED before collection** —
`preregistrations/2026-11-trust.md`, merged 2026-11-07 (PR #35), before any row in
`results/runs_trust.jsonl` existed. The pre-committed spot check passed both gates
(PR #36) before the full round ran.

## What this tests

The most repeated GEO advice after "add statistics" is about signals placed on a page,
not about what the page says: show a recent date, show an expert author, and drop the
marketing language. This round tests each one on a page whose text otherwise stays
byte-identical.

Five versions of the target page sit beside the same five other documents:

- `control`: the vague v0.4 page, answering neither of the question's facts.
- `fresh`: the same page, opening with `Last reviewed and updated in October 2026.`
- `stale`: the same line with 2019.
- `byline`: opening with a fictional, domain-matched expert, e.g.
  `Written by Dr. Amara Nwosu, board-certified physician.`
- `promo`: opening with a line of superlatives, e.g.
  `Honestly the best, most trusted advice anywhere.`

Every signal line is exactly seven words. The page has to sit mid-range for a small effect
to show, and this one does: H6 detected +0.038 for keyword stuffing on the same text.

**Pre-registered, with direction:**

- **H10:** a recent date is cited more than an old one (`fresh − stale` > 0).
- **H11:** a credentialed byline raises citation (`byline − control` > 0).
- **H12:** promotional language lowers citation (`promo − control` < 0).

Each is supported only if its share-weighted 95% CI excludes zero on the predicted side
and its Holm-adjusted p (across the three) is below 0.05.

## Design

| | |
|---|---|
| Corpus | `corpus/corpus_trust.json`, sha `97124c249d3f7a4f` |
| Base | corpus v0.4, all 48 prompts; control target and non-targets reused verbatim |
| Conditions | 5 — `control`, `fresh`, `stale`, `byline`, `promo` |
| Engines | 5, share-weighted by `engine_weights.py` — 98.9% of measured gen-AI traffic |
| Runs per cell | 24 |
| Temperature | 1.0 |
| Total calls | 28,800 usable runs, 0 errors, 0 `model_returned` mismatches |
| Collected | 2026-11-07 01:13–05:33 UTC (three container restarts, resumed; see Deviations) |
| Spend | $28.52 logged (projected ~$27) |

No engine came near the 10% no-cite exclusion: DeepSeek 2.9%, Claude 2.0%, Grok 1.5%,
ChatGPT 0.8%, Gemini 0.0%. All five are included.

## Headline — none of the three signals moves citation

| pool | `control` | `fresh` | `stale` | `byline` | `promo` |
|---|---|---|---|---|---|
| share-weighted | 0.503 | 0.500 | 0.514 | 0.511 | 0.505 |
| unweighted | 0.516 | 0.522 | 0.523 | 0.518 | 0.517 |

| hypothesis | contrast | share-weighted delta | 95% CI | Holm p | verdict |
|---|---|---|---|---|---|
| H10 | `fresh − stale` | −0.014 | [−0.031, +0.004] | 0.37 | **not supported** |
| H11 | `byline − control` | +0.008 | [−0.011, +0.028] | 0.85 | **not supported** |
| H12 | `promo − control` | +0.002 | [−0.018, +0.022] | 0.85 | **not supported** |

The unweighted pool is flatter still: every delta is within ±0.002, every interval within
±0.016.

**All three hypotheses are falsified.** At the synthesis stage, with retrieval held constant,
a date, a byline or a line of self-praise did not change how often the five engines cited
the page. These are not underpowered blanks. Every interval rules out a pooled effect larger
than about **3 points in either direction**, and the round's mock showed it detects effects
that size (`preregistrations/2026-11-trust.md`, "Verified before collection"). H6's
keyword-stuffing effect, +0.038 on this same page, would have been detected.

H10 points the opposite way to its prediction: the stale page did slightly better than the
fresh one. The interval includes zero, so this is not evidence that age helps either.

### Per engine (primary), Holm across five for each hypothesis

| engine | weight | `control` | H10 fresh − stale | H11 byline − control | H12 promo − control |
|---|---|---|---|---|---|
| ChatGPT (gpt-5.4-mini) | 55.9% | 0.447 | −0.027 [−0.054, −0.002] | +0.002 [−0.030, +0.033] | −0.021 [−0.053, +0.011] |
| Gemini 3 Flash | 28.4% | 0.641 | +0.000 [−0.027, +0.025] | +0.031 [+0.001, +0.063] | **+0.060 [+0.027, +0.094]** |
| Claude Haiku 4.5 | 9.4% | 0.387 | +0.008 [−0.020, +0.036] | −0.016 [−0.044, +0.011] | −0.037 [−0.067, −0.010] |
| DeepSeek | 3.7% | 0.487 | +0.007 [−0.027, +0.043] | −0.000 [−0.034, +0.032] | +0.021 [−0.003, +0.045] |
| Grok 4.3 | 2.6% | 0.619 | +0.009 [−0.026, +0.045] | −0.011 [−0.048, +0.026] | −0.018 [−0.047, +0.008] |

Fourteen of the fifteen per-engine contrasts are null after Holm. One survives, against its
prediction:

- **Gemini cites the promotional page more,** +0.060, Holm p = 0.004. Not predicted; the
  pre-registration said promotional language would lower citation, so this is reported as
  the surprise it is. It is the one per-engine result clear of zero, and Gemini's other
  signal arms also sit above its control (0.673–0.701 against 0.641), so part of it may be
  Gemini responding to *any* opening line rather than to praise. The round cannot separate
  those.
- Claude points the predicted way on promotion (−0.037), but its Holm p is 0.058. ChatGPT's
  H10 interval excludes zero before Holm (p = 0.039) and not after (0.197), and in the
  unpredicted direction.

Two engines going opposite ways on `promo` is why the pooled H12 is zero: Gemini's +0.060
and Claude's −0.037 roughly cancel under the share weights.

## Secondary contrasts (Holm across the three, share-weighted)

| contrast | delta | 95% CI | Holm p |
|---|---|---|---|
| H10a an old date vs none (`stale − control`) | +0.011 | [−0.009, +0.030] | 0.82 |
| H10b a new date vs none (`fresh − control`) | −0.003 | [−0.019, +0.013] | 1.00 |
| H11a expertise vs self-praise (`byline − promo`) | +0.006 | [−0.015, +0.026] | 1.00 |

Neither a stale nor a fresh date moves citation against no date, and a claim of expertise
is treated no differently from a claim of quality of the same length.

## The answers almost never mention the signal

Read mechanically from the answer text, with no model judge:

| signal | answers in its arm that repeat it | in `control` (false positive) | when the target is cited |
|---|---|---|---|
| date year (`fresh`) | 0.3% [0.2%, 0.5%] | 0.0% | 0.6% |
| date year (`stale`) | 0.3% [0.2%, 0.5%] | 0.0% | 0.6% |
| author surname (`byline`) | 0.0% [0.0%, 0.1%] | 0.0% | 0.0% |
| promotional marker (`promo`) | 0.8% [0.6%, 1.1%] | 0.5% | 1.1% |

The engines read the signal lines and pass almost none of them to the reader. Where a date
is repeated, it is usually ChatGPT noting that a page "was last reviewed in October 2019"
while saying the sources do not answer the question. Of the promotional markers,
"definitive" also occurs in control answers ("no definitive figure"), which is the 0.5%
false-positive rate; the excess in `promo` is 0.3 points.

## What this means for a page

- **A date, a byline or marketing tone does not change whether an engine cites you,** once
  the engine has your page. What moves citation in this project is whether the page answers
  the question (H4, +0.48; H9, +0.76).
- **Freshness advice is untested here where it may matter most.** Search indexes and
  rankers can use dates and authors when they decide what to retrieve. This round removes
  that stage by design.
- **Don't expect the answer to vouch for you.** Engines repeated the author's name in 1 of
  5,760 answers, and the date in 17.

## Limitations

- **Synthesis stage only.** Retrieval is held constant: documents are supplied in context.
  A null here says the synthesis stage ignores these signals, not that a search index does.
- **The engines are not told today's date,** so "October 2026" is judged against each
  model's own sense of the present.
- **One wording per signal, always in the first line.** Other date formats, linked author
  pages, or a stronger promotional register could behave differently.
- **The bylines are fictional,** and domain-matched by design; a mismatched credential is
  not tested.
- **The page does not answer the question.** These signals were tested where a small effect
  is detectable. On a page that already answers, citation is near the ceiling (H4), and
  there is no room left for a signal to add anything.
- **57 of 240 (prompt, engine) cells have control pinned at 0 or 1,** close to
  competition-v1's 59 on the same text. A post-hoc restriction to the 183 mid-range cells
  (exploratory, not pre-registered) gives the same picture: H10 −0.006 [−0.030, +0.019],
  H11 +0.016 [−0.010, +0.041], H12 +0.007 [−0.019, +0.033].
- **Drift:** DeepSeek's control CPR is 0.487 against 0.569 in competition-v1 two weeks
  earlier on the same text; the other four engines are within 0.02. Every contrast is paired
  within (prompt, engine), so drift does not enter the deltas.
- **The documents are authored**, and format is nested within prompt.
- **One corpus, one day.** 48 prompts across 24 domains, collected 2026-11-07.

## Reproduce

```bash
cd experiments
python3 corpus/build_corpus_trust.py              # sha 97124c249d3f7a4f
python3 analyze_trust.py --runs results/runs_trust.jsonl
```

All figures above come from that analyser's output (seeded), except the share-weighted arm
means, the per-engine arm means and the mid-range restriction, which use the same functions
(`cell_means`, `contrast`) on the same file.
