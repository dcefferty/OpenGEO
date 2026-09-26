# OpenGEO test — At what mileage should I replace my running shoes, and how much does rotating two pairs extend their life?

Run 2026-09-26T19:16:17+00:00 with `opengeo.py` 0.1.0. Corpus `opengeo-test-36c39450d56b`. 24 runs per version per engine, temperature 1.0, document order randomised per run.

Engines: ChatGPT, Gemini, Claude, DeepSeek, Grok — 98.9% of measured AI-assistant traffic.

## At what mileage should I replace my running shoes, and how much does rotating two pairs extend their life?

**Your edit raised citation from 40% to 100%** — +60 points, 95% CI +49 to +69, held on 4 of 5 engines.

| Engine | Before | After | Change | 95% CI | p | Note |
|---|---|---|---|---|---|---|
| ChatGPT | 21% | 100% | +79 | +62 to +96 | 0.000 | lower bound |
| Gemini | 88% | 100% | +12 | 0 to +25 | 0.229 | lower bound; no room |
| Claude | 4% | 100% | +96 | +88 to +100 | 0.000 | lower bound |
| DeepSeek | 75% | 100% | +25 | +8 to +42 | 0.024 | lower bound |
| Grok | 17% | 100% | +83 | +67 to +96 | 0.000 | lower bound |
| **All engines** (share-weighted) | 40% | 100% | **+60** | +49 to +69 | | |

What this means:

- For this question, against these competitors, your edit made AI answers more likely to cite your page.
- One question is one question. About 1 in 20 tests shows a change by chance alone, so test 3-5 questions your customers actually ask before rewriting your site.
- 5 engines cited your edited page in almost every run, so the true change there may be larger than shown.
- 1 engine already cited your current page almost every time, leaving little room to show an improvement.
- This measures what happens once an AI engine has your page. It does not tell you whether an engine will find your page in the first place.

## Method

A paired, controlled experiment. Your page appears twice — as it is and as edited — each time among the same excerpts of your competitors' pages. Only your excerpt differs between the two versions, so a difference in citation is caused by your edit. Intervals are percentile bootstraps over runs; p-values are permutation tests. No distributional assumptions.

Every default is argued for, with its evidence, in `design/opengeo-test.md`.

## Files

- `runs.jsonl` — every raw model response
- `corpus.json` — the exact text of every document tested
- `manifest.json` — versions, settings and flags, enough to re-run this test
- `chart*.svg` — before and after, per engine
