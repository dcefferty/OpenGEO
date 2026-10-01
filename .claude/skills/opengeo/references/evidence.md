# Relaying the evidence

Read this when someone asks what works for getting cited by AI, what they should test, or
whether a tactic they've heard about is real.

## How to talk about it

The evidence is a set of measurements, each taken in a specific setting with a specific
amount of data. Relay it that way: what was measured, how strongly, and where it stops
applying. Then connect it to the user's own idea as **something worth testing on their
page** — never as a change their page needs.

The difference in practice:

- Relaying: *"In controlled tests, pages that stated the specific answer were cited far more
  often than pages that talked around it — about 48 points more, across 48 questions. Your
  page describes the service but doesn't state a price. If you have real prices you're happy
  to publish, that's the idea with the strongest evidence behind it, and you could test it
  on your page directly."*
- Prescribing (don't): *"You need to add pricing to your page to get cited by ChatGPT."*

The first gives them the evidence and the choice. The second turns a measurement into an
instruction the measurement doesn't support — it was taken on other pages, other questions,
and it says nothing certain about theirs. That gap is exactly what `opengeo test` closes.

## The findings

As of 2026-09-26. The authority is `results/findings.json` and the reports in
`results/published/` at the repository root; if they differ from this summary, they win.

"Points" are percentage points of citation rate: how much more often, out of every 100
answers, the page was cited.

### Strong evidence

48 questions each, and either pre-registered or independently replicated.

| What was changed | Effect on citation | Confidence |
|---|---|---|
| **Stated the specific answer** instead of talking around it | **+48 points**, 95% CI +40 to +56 | Strongest finding, and found three times. The +48 round itself was exploratory, not pre-registered — but the effect came out at +49 on an earlier corpus, and at +47 in a **pre-registered** round on twelve questions that were never published, which rules out an artefact of the public test set |
| **Repeated the keyword** from the question | **+4 points**, 95% CI +0.4 to +7.5 | Pre-registered. Real but small, and with no measurable cost to accuracy |
| **Padded the page with filler** to twice its length | **0 points**, 95% CI −2 to +3 | Pre-registered. Length alone does nothing; on a few engines padding cost citations |

The first row carries a caveat worth passing on: its direction is solid, but its size is
not a prediction. In those tests the vague version was written to answer none of the
question, and the edited page was usually the only document that did, so it was cited
almost every time. The +48 mostly reflects how rarely the vague version was cited. Against
competitors that also state the answer, expect less. Never present it as "at least +48".

A related pattern, seen while building the tests rather than measured as a formal result:
engines reward a page for answering at all, not for answering more completely. A page that
already gives some specific answer gained little from a fuller one.

### Preliminary evidence

Only three questions — a probe, below the 25-question threshold OpenGEO uses before calling
anything general. Treat these as "no effect detected so far", not as "proven not to work".

| What was changed | Effect | Confidence |
|---|---|---|
| Moved the answer to the top of the page | no detectable effect | Preliminary |
| Formatted it as a visible FAQ, with the question as a heading | no detectable effect | Preliminary |
| Attributed claims to their source by name | no detectable effect | Preliminary |
| Added a line citing the source | no detectable effect | Preliminary |

Pooled across all four: **+0.1 points, 95% CI −4 to +3.** The most likely reason these show
nothing is that they act on *whether a page is found* — retrieval — which this benchmark
holds constant by design. So "no effect" here means no effect once an engine already has
the page, not that the tactic is useless everywhere.

This is the most useful thing to tell someone who's been sold on answer-first or FAQ
formatting: the evidence doesn't show it helps at the stage we can measure, and whether it
helps a page get *found* is an open question nobody has tested causally.

**FAQ schema is a different thing, and was never tested.** Schema is structured-data markup
in the page's code. The engines here receive a page's visible text, and markup doesn't
survive into it, so neither the benchmark nor `opengeo test` can measure schema at all. Say
so plainly rather than letting the formatting result stand in for it.

### Context worth knowing

- **The engines largely agree** on which documents deserve a citation.
- **Engines sometimes credit a page with claims it doesn't make.** Being cited is not the
  same as being represented accurately.
- **Checking visibility through an engine's API may undercount you.** A calibration study
  found the API and the logged-out consumer interface diverged substantially (0.368, 95% CI
  0.139 to 0.625). On 3 of 12 questions, the API cited nothing where the interface cited
  real sources. This matters to anyone using a tracking tool built on APIs.

## Where the evidence stops

Say these whenever they bear on what the user is trying to decide:

- **It measures what an engine does once it has a page, not whether it finds the page.**
  For many small businesses, getting found is the bigger problem, and nothing here
  measures it.
- **The questions were informational** — how much, how often, how long. Local and commercial
  searches ("best plumber near me") were not tested. `opengeo test` lets the user test their
  own commercial questions, which is one of the best reasons to run it.
- **It used each engine's API**, which is not identical to what a person sees in the app.
  Each engine is one model standing in for its app: "ChatGPT" is OpenAI's gpt-5.4-mini,
  "Claude" is Claude Haiku 4.5, and so on (`engine_weights.py` at the repository root has
  the full panel). When someone cares about one engine specifically, name its model.
- **Five engines: ChatGPT, Gemini, Claude, DeepSeek and Grok**, together about 99% of
  measured AI-assistant traffic. **Perplexity is not among them and cannot be.** It runs its
  own live web search and ignores documents handed to it, so it can't be tested this way at
  all. When someone asks about Perplexity, say so rather than letting "AI engines" imply it
  was covered.
- **One engine panel, at one point in time.** Engines change; results can drift.
