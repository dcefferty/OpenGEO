# Where synthesis-stage measurement stops

**Presentation tactics do not move citation at the synthesis stage, and the regime needed
to rank them is an artefact of how the documents were cut.**

Published 2026-09-20. **Probe-level evidence, not a round.** Three probes of three
questions each, 4,320 calls, below the 25-prompt floor (`METHODOLOGY.md` §5.2). Each
probe's design and reading were committed to git before its data existed; none is a
pre-registered round, and nothing here is published as an effect size. Read it as a
negative result about what this instrument can measure.

## The question

The benchmark's strongest finding is that specific facts beat no facts by +0.48 (H4). Its
weakest is that keyword stuffing helps by +0.038 (H6), and padding by +0.004 (H7). All
three vary *what a document says*. The open question — ROADMAP item 11, the largest on the
roadmap — was whether the things GEO practitioners actually sell can be ranked the same
way: answer-first structure, FAQ blocks, attributed quotations, source citations.

That needs a corpus where several documents answer the question, so citation measures
*preference* rather than *presence*. Building one took nine screening batches, 16
questions and a mechanical verbatim pipeline. The answer turned out not to depend on any
of that.

## Three probes

**1. Four tactics, screened targets** (`results/probes/2026-09-19-tactic-pilot.md`,
1,800 calls). Four fact-preserving tactics applied to targets the screen certified as
movable. Every arm null, every Holm-corrected p at 1.000:

| tactic | delta | OR | 95% CI |
|---|---|---|---|
| `answer_first` | −0.019 | 0.95 | [0.70, 1.29] |
| `faq` | −0.005 | 1.05 | [0.77, 1.43] |
| `attributed` | +0.017 | 1.02 | [0.85, 1.26] |
| `citation` | +0.010 | 0.95 | [0.72, 1.20] |

Per-cell movement sat at resampling noise — mean |delta| over its noise expectation ran
0.81 to 1.36, with `attributed` moving *less* than noise — so unlike H7's pooled null,
there was no directional split cancelling out. Restricting to cells with real headroom
collapsed every arm to about 0.00.

**2. A length ladder** (`results/probes/2026-09-19-length-ladder.md`, 2,160 calls). The
surviving explanation was that 28–55 word targets are too short for "first" to mean
anything. Targets were rebuilt at three nested lengths, up to 235 words with the answer as
far as 216 words from the top, each run with and without `answer_first`. The committed
rule fired **B SUPPORTED** on an interaction of +0.150 — and should not be read that way.
The rule named a bootstrap CI and did not say what to do when the two tests disagree: the
CI excluded zero while the sign-flip permutation gave p = 0.158, on six cells with one
carrying 56% of the panel weight. Leave-one-out moved the estimate between +0.076 and
+0.186. Worse, the contrast built specifically to separate burial depth from length
separated nothing — neither group was monotone, and the largest value in the table was the
*short* rung of the *fixed-position* question, which the hypothesis cannot explain.
Recorded as suggestive, not established.

**3. A page-length field** (`results/probes/2026-09-20-pagelength-screen.md`, 360 calls).
Both earlier probes lost cells to saturation, because a target containing the answer is
conspicuous against a field of snippets. So the field was changed instead: every document
rebuilt as a 252–345 word page section, closer to what an answer engine actually
synthesises from. **1 of 3 questions kept a usable target, against 3 of 3 as snippets.**

## What the third probe found

The hypothesised mechanism did not fire. Page length was meant to work by making engines
cite fewer documents per answer; cites per answer held at 4.68 → 4.84. Instead the
distributions polarised. Blood pressure, at page length:

| document | rate | | document | rate |
|---|---|---|---|---|
| `fda_bp` | 1.00 | | `nia_bp` | 0.07 |
| `cdc_hbp` | 0.95 | | `nhlbi_diag` | 0.03 |
| `nhlbi_sym` | 0.86 | | `niddk_bp` | 0.01 |
| `nhlbi_hbp` | 0.78 | | `nhlbi_causes` | 0.01 |

Four documents above 0.78, four below 0.08, nothing between. Smoke alarm collapsed
entirely — every document at 0.93–0.99.

**A short snippet is a partial answer and earns an intermediate citation rate. A full page
either contains the answer or it does not.** The gradeable middle that item 11 depends on
is not a property of the content. It is a property of how severely the content was
truncated.

That is worse for the item than a null. Measuring tactics in that regime would measure
something that does not correspond to how an engine sees a real page.

## The boundary

Tier 1 supplies documents in context, holding retrieval constant by construction. That is
what makes it reproducible, and it is also what bounds it.

What moves citation here is **whether a document answers the question** — +0.48, found
twice, significant on every model. What does not move it is how the answer is presented:
where it sits, whether it carries a heading, whether it names its source. Answer-first
structure and FAQ formatting are plausibly *retrieval*-stage tactics — they act on whether
a page is found and snippet-matched — and this design removes that stage.

So the negative result has a shape. It is not "these tactics don't work." It is: **if they
work, they do not work by changing what a model does with content it already has.** That
is a testable claim, and testing it needs a live-retrieval design (ROADMAP item 9), not a
bigger version of this one.

## Limits

- Three questions per probe, far below the 25-prompt floor. Every figure is an estimate
  with an interval, and the intervals are wide.
- One question (`finance_housingshare`) *improved* under page length — 40% → 48% unpinned,
  1 → 2 usable targets. The saturation effect is not uniform, and a corpus built from
  richer or more varied sources is not excluded by this evidence.
- `home_smokealarm` ran at 7 candidates rather than 8, logged as a deviation. It biases
  toward saturation, so it cannot explain a failure to saturate, but it does weaken that
  question.
- The tactic set was fact-preserving by design, so that H4 would not swamp it. Tactics that
  add facts were not tested and are already covered by H4.
- Five engines, one API plane. The calibration study puts API/UI divergence at 0.368
  (`../2026-08-30-calibration-v1/REPORT.md`), which bounds how far any of this generalises
  to what a person sees in a browser.

## Reproduction

```bash
python3 corpus/build_corpus_tacticpilot.py
python3 corpus/build_corpus_lengthladder.py
python3 corpus/build_corpus_pagelength.py

python3 analyze_tacticpilot.py  --runs results/tacticpilot.jsonl
python3 analyze_lengthladder.py --runs results/lengthladder.jsonl
python3 screen.py --corpus corpus/corpus_pagelength.json --runs results/pagelength_screen.jsonl
```

Raw responses for all 4,320 calls ship with this report. Each builder re-slices its text
from committed page snapshots and fails rather than warning if a source has drifted.
