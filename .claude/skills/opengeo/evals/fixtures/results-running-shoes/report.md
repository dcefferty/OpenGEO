# OpenGEO test — How often should I replace my running shoes?

Run 2026-10-01T01:09:45+00:00 with `opengeo.py` 0.2.0. Corpus `opengeo-test-19520db4ec12`. 24 runs per version per engine, temperature 1.0, document order randomised per run. Cost $0.29, as billed.

Engines: ChatGPT, Gemini, Claude, DeepSeek, Grok — 98.9% of measured AI-assistant traffic.

## How often should I replace my running shoes?

**Your edit raised citation from 79% to 100%** — +21 points, 95% CI +9 to +31, held on 2 of 5 engines.

| Engine | Before | After | Change | 95% CI | p | Note |
|---|---|---|---|---|---|---|
| ChatGPT | 83% | 100% | +17 | 0 to +31 | 0.113 | ceiling |
| Gemini | 83% | 100% | +17 | 0 to +35 | 0.109 | ceiling |
| Claude | 38% | 100% | +62 | +38 to +77 | 0.000 | ceiling |
| DeepSeek | 67% | 100% | +33 | +12 to +50 | 0.004 | ceiling |
| Grok | 96% | 96% | 0 | −15 to +15 | 1.000 | ceiling; no room |
| **All engines** (share-weighted) | 79% | 100% | **+21** | +9 to +31 | 0.000 | |

What this means:

- For this question, against these competitors, your edit made AI answers more likely to cite your page.
- If your edit did nothing, a difference this large would turn up less than 1 time in 1,000, so chance is very unlikely to explain it.
- This is one question, against these competitors. Test 3-5 questions your customers actually ask before making the same kind of change elsewhere.
- 5 engines cited your edited page in almost every run, as high as this test can measure. That shows your edit got your page cited every time against these competitors, not how it would do against pages that also answer the question.
- 1 engine already cited your current page almost every time, leaving little room to show an improvement.
- This measures what happens once an AI engine has your page. It does not tell you whether an engine will find your page in the first place.

## What the engines saw

Your page's title, if it has one, and the part of the page around your edit -- not the whole page. Each competitor page was shown the same way: its title and its most relevant section (all in `corpus.json`). Anything else on the page was not part of the test.

**Before:**

> **Running Shoe Fitting | Kestrel Running Co.**
>
> From there we bring out three or four pairs that suit your gait and the running you do, from easy road miles to mountain trails. Take your time and jog the block in each pair before you decide. We carry Brooks, Hoka, Saucony, New Balance and On, in widths from narrow to extra wide. Not sure the new pair is right? Run in it for 30 days, and if it doesn't work out, bring it back for an exchange.

**After your edit:**

> **Running Shoe Fitting | Kestrel Running Co.**
>
> From there we bring out three or four pairs that suit your gait and the running you do, from easy road miles to mountain trails. Take your time and jog the block in each pair before you decide. Most pairs last 300 to 500 miles, roughly four to six months at 20 miles a week. Not sure the new pair is right? Run in it for 30 days, and if it doesn't work out, bring it back for an exchange.

## Method

A paired, controlled experiment. Your page appears twice — as it is and as edited — each time among the same excerpts of your competitors' pages. Only your excerpt differs between the two versions, so a difference in citation is caused by your edit. Intervals are percentile bootstraps over runs; p-values are permutation tests, stratified by engine for the pooled row. No distributional assumptions.

Every default is argued for, with its evidence, in `design/opengeo-test.md`.

## Files

- `runs.jsonl` — every raw model response
- `corpus.json` — the exact text of every document tested
- `manifest.json` — versions, settings and flags, enough to re-run this test
- `chart*.svg` — before and after, per engine
