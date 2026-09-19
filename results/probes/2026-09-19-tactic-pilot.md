# Tactic pilot — does a tactic move a screened target, and by how much?

**Committed before collection, 2026-09-19.** This is a probe, not a round. It carries no
hypothesis test and produces no published effect size. It exists to answer two design
questions before the remaining questions for ROADMAP item 11 are sourced against
assumptions nobody has checked.

This file is written and committed *before* the run so the tactic set cannot be chosen
after seeing which tactics worked. The git timestamp is the evidence, as it is for a
pre-registration.

## Why

Item 11 has built corpus machinery — sourcing, verbatim slicing, screening, an 8+
candidate rule, a power table — and fourteen kept questions. None of it tests the
intervention. No tactic variant has ever been written or run. Two assumptions sit under
the whole round:

1. **A tactic can be applied at all** to a screened target: fact-preserving, and at the
   length real federal excerpts come in.
2. **It moves citation** enough to be worth ranking.

Assumption 1 is already partly answered, and negatively. Of the fourteen kept targets,
**only seven have three or more sentences**; five are a single sentence of 16–44 words. A
one-sentence document cannot carry answer-first structure or an FAQ block, so half the
corpus as built cannot express two of the five tactics item 11 names. Fixing that means
re-anchoring targets to longer multi-block spans and re-screening — tracked separately,
and deliberately not on this pilot's critical path.

Assumption 2 also sizes the round. The question count in ROADMAP item 11 rests on H6's
+0.038 as a stand-in for tactic magnitude, and H6 was keyword stuffing, not a tactic this
round will rank. At OR 1.30 the round needs 25 questions; at OR 1.15 it needs 50. That is
the difference between ~11 and ~36 more questions to source.

## Design

Three questions × five conditions × five engines × 24 runs = **1,800 calls**.

Corpus `tactic-pilot-v1`, sha256 `831ad7108b1bdc31` (rebuilt after target re-flagging —
the build prints the current hash and it is recorded with the results). Built by
`corpus/build_corpus_tacticpilot.py`, which imports each question's candidate set
unchanged from the committed screen corpus and re-runs `screen.py` against the committed
screening runs, failing if the screen does not name the target below.

| question | target | baseline | headroom | screen excludes |
|---|---|---|---|---|
| `home_smokealarm` | `cpsc_blog` | 0.38 | 0.250 | gpt-5.4-mini |
| `health_bloodpressure` | `nhlbi_hbp` | 0.53 | 0.208 | grok-4.3 |
| `finance_housingshare` | `census_story22` | 0.47 | 0.208 | grok-4.3 |

Chosen as the highest-headroom members of the seven multi-sentence targets whose control
also has a **genuine buried lede** — an answer not already in the first sentence — so
answer-first is a real manipulation rather than a no-op. claude, gemini and deepseek rest
on all three questions, gpt on two, grok on one.

**These three questions are held out of the round.** The pilot reads effect sizes, which
is exactly what pre-registration constrains. Holding them out costs three of fourteen kept
questions and buys a round whose corpus has never been looked at.

## The tactics

All four are **fact-preserving**: no numeral appears in a variant that is not in the
control, verified by `check_variants.py`. The corpus already shows specific facts beat no
facts by +0.48 (H4); a tactic that adds a fact re-runs H4 and swamps everything else.
This is why "add statistics", named in the item 11 sketch, is not among them.

| tactic | what changes | length vs control |
|---|---|---|
| `answer_first` | the answering sentence moved to the front | +0% to +7% |
| `faq` | `answer_first` plus the question as a heading | +19% to +25% |
| `attributed` | same facts, attributed inline to the issuing agency | +19% to +38% |
| `citation` | control unchanged, plus a trailing source line | +11% to +34% |

Two properties are deliberate and both are verified mechanically:

- **`faq` nests `answer_first`.** Its body is byte-identical to the `answer_first` text,
  so `faq − answer_first` is the marginal effect of the heading alone.
- **`faq` cannot be separated from keyword insertion.** An FAQ heading necessarily
  introduces the question's own words; `check_variants.py` flags exactly that and nothing
  else on this arm. It is reported as heading-plus-keywords, never as formatting alone.
  H6's +0.038 is the reference point for the keyword component.

`attributed` is **weak by construction on two of three targets.** Federal pages name their
own agency, so `cpsc_blog` and `census_story22` already carry attribution in the control
and the variant only strengthens it. Only `nhlbi_hbp` is a clean un-attributed baseline.
A null on this arm most likely means the manipulation was small, not that attribution does
nothing, and the round should source un-attributed controls before ranking it.

On short documents `attributed` and `citation` cannot be applied without materially
increasing length — a source line has a floor of about ten words, which is a third of a
32-word document. That is a property of the tactic at this document length, not an
artefact of how these variants were written. H7 measured padding of 25–100% at +0.004
pooled, so length is not expected to carry these arms, but the analysis reports words per
variant rather than assuming it.

## What this pilot does and does not produce

**Produces:** per-tactic, per-engine citation rates against the control, with intervals;
an estimate of the largest and smallest tactic effect; a corpus-size recommendation for
the round.

**Does not produce:** a ranked table, a hypothesis test, a published effect size, or any
claim about tactics in general. n=3 questions is far below the 25-question floor
(`METHODOLOGY.md` §5.2). Every number here is an estimate with an interval, and it will be
reported as one.

## Pre-committed reading

Fixed before collection so the outcome cannot be reinterpreted afterwards:

- **Largest tactic ≥ OR 1.30** against control, pooled across the three questions → the
  round is sized at **25 questions**; ~11 more to source.
- **Largest tactic OR 1.15–1.30** → **50 questions**; ~36 more to source.
- **No tactic clears OR 1.15, and the interval excludes OR 1.30** → the tactics as
  written do not move a screened target at the length this corpus supports. Do not source
  36 more questions against them. Re-anchor targets to longer spans first, re-screen, and
  re-probe — the length finding above is then the main result, not a side note.

Recorded because the third outcome is the one that would otherwise get explained away.
