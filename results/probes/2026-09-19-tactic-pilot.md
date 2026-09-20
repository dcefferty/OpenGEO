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

---

# Results — collected 2026-09-19

1,800 calls, **0 errors**, 0 `model_returned` mismatches, no model above the 10% no-cite
limit (grok 0.6%, the rest 0.0%). Panel covers 98.9% of measured assistant traffic.
Corpus `tactic-pilot-v1`, runs in `results/tacticpilot.jsonl`, analysis
`analyze_tacticpilot.py`.

Overall target citation rate across all 1,800 runs: **0.495** — mid-range, neither floor
nor ceiling, which is what the screen was for.

## Pre-committed reading: INCONCLUSIVE

| tactic | delta | 95% CI (cells) | OR | 95% CI | p | Holm |
|---|---|---|---|---|---|---|
| `answer_first` | −0.019 | [−0.106, +0.040] | 0.95 | [0.70, 1.29] | 0.71 | 1.000 |
| `faq` | −0.005 | [−0.106, +0.084] | 1.05 | [0.77, 1.43] | 0.83 | 1.000 |
| `attributed` | +0.017 | [−0.038, +0.069] | 1.02 | [0.85, 1.26] | 0.89 | 1.000 |
| `citation` | +0.010 | [−0.062, +0.063] | 0.95 | [0.72, 1.20] | 0.66 | 1.000 |

Largest tactic `faq` at OR 1.05, CI [0.77, 1.43]. The point estimate is below OR 1.15 and
the interval still reaches OR 1.30, which is the committed **inconclusive** branch:
*widen the pilot before sizing the round.* That instruction stands, and the diagnostics
below do not override it.

FAQ heading, marginal (`faq − answer_first`, bodies byte-identical): **+0.014**, CI
[−0.066, +0.081], p=0.43. No detectable effect from the heading, including the keyword
component it necessarily carries.

## Diagnostics — post-hoc, not pre-committed

Two questions the committed plan did not ask. Both were run after seeing the result and
are labelled as such; neither changes the reading above.

**Is the movement bigger than resampling noise?** Two independent 24-run rates differ by
E|d| ≈ 0.8·√(2p(1−p)/24) under the null. Individual cells did move a lot — `answer_first`
+0.375 on claude/housing, `citation` −0.333 on deepseek/housing — but that is what
sampling twice at n=24 produces:

| tactic | mean abs delta | noise expectation | ratio |
|---|---|---|---|
| `answer_first` | 0.086 | 0.082 | 1.05 |
| `faq` | 0.111 | 0.082 | 1.36 |
| `attributed` | 0.067 | 0.082 | **0.81** |
| `citation` | 0.092 | 0.082 | 1.12 |

`attributed` moves *less* than noise. So the pooled null is not a directional split
cancelling out, which is what H7 turned out to be — there is no consistent signal in the
cells to cancel.

**Was there room to move?** The screen certified these targets as movable, but headroom
measured once at 24 runs is itself an estimate: a rate of 0.21 has a Wilson interval of
roughly [0.09, 0.41]. By run time **6 of 15 cells sat at or beyond a boundary** — claude
went 0.21 → 0.04 on two questions, gemini 0.79 → 0.92. Restricting to the 9 cells with a
control rate in [0.125, 0.875] in this run:

| tactic | delta, all cells | delta, cells with real headroom | 95% CI |
|---|---|---|---|
| `answer_first` | −0.019 | **+0.003** | [−0.042, +0.027] |
| `faq` | −0.005 | **+0.001** | [−0.151, +0.110] |
| `attributed` | +0.017 | **+0.004** | [−0.074, +0.079] |
| `citation` | +0.010 | **+0.019** | [−0.079, +0.091] |

Every arm collapses to ~0.00. The null is not an artefact of cells having no room.

**Per engine** (primary; these do not depend on the weighting):

| engine | weight | `answer_first` | `attributed` | `citation` | `faq` |
|---|---|---|---|---|---|
| claude-haiku-4.5 | 0.094 | +0.056 | +0.014 | +0.083 | +0.097 |
| deepseek-chat | 0.037 | +0.028 | +0.028 | −0.139 | +0.056 |
| gemini-3-flash | 0.284 | −0.111 | −0.028 | −0.056 | −0.167 |
| gpt-5.4-mini | 0.559 | +0.014 | +0.042 | +0.042 | +0.056 |
| grok-4.3 | 0.026 | −0.056 | −0.028 | −0.000 | +0.014 |

gemini is negative on all four arms and claude positive on all four. At three questions
that is a hypothesis worth carrying into the round, not a finding.

## Validity checks

Run before trusting a null this clean:

- **The variants reached the models.** The five condition messages the runner builds for a
  question are five distinct strings (sha-checked, 1420–1503 chars). A bug sending control
  text under every label would produce exactly this result, and did not occur.
- **The metric is not broken.** The analyzer's citation call agrees with the
  harness-logged `target_cited` on 1,800 of 1,800 runs, and control rates span 0.00–0.96
  across cells, so the measurement clearly discriminates.
- **The corpus is the screened one.** The control arm reproduces the screening baseline on
  14 of 15 cells within 0.25; the one exception is gemini on `finance_housingshare`
  (+0.33). Differences are within the Wilson width of a 24-run rate.

## What this changes

**Do not source 36 more questions against these tactics yet.** The committed instruction
is to widen the pilot, and the binding constraint is not statistical power — it is that
the corpus can barely express the tactics being ranked:

- 7 of 14 targets have 3+ sentences; the rest cannot carry `answer_first` or `faq` at all.
- Of those 7, only **3** have a genuine buried lede, so `answer_first` is a real
  manipulation on roughly 3 of 14 targets — and those 3 are exactly this pilot.
- `attributed` is weak on 2 of 3 because federal pages name their own agency.

So widening by adding the four remaining multi-sentence questions would add cells where
the manipulation is near-degenerate, and would mostly buy tighter intervals around zero.

**A third finding, not anticipated:** screening certifies headroom from a single 24-run
estimate, and that estimate is noisy enough that 6 of 15 certified cells were unusable by
run time. The round's screening gate is weaker than its design assumes. This is the same
error class the project already caught once — treating a quantity measured at finite runs
as if it were exact, as raw cross-model Kendall's W did.

Sequenced consequence, in order:

1. **Re-anchor targets to longer multi-block spans** so a structural tactic is definable,
   then re-screen. Candidates stay short; only the target needs the length, and the tactic
   contrast is against that same target's control, so nothing is confounded.
2. **Certify headroom at more runs than 24, or require a wider margin**, so the screen
   stops passing cells that land on a boundary.
3. **Re-probe** before sourcing at scale.

The alternative, if that sequence proves too expensive, is to accept that item 11's
question is answered negatively for this class of tactic: at the document lengths real
federal sources come in, fact-preserving presentation changes do not move citation on a
screened target, and only adding facts does (H4, +0.48). That is a publishable result and
a genuinely useful one — it is the opposite of what the GEO advice market sells — but it
should be stated after step 1, not instead of it.
