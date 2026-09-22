# OpenGEO Public/Private Contamination Round — Pre-Registration — v1 — 2026-09-22

Committed before collection. The git timestamp on this file is the evidence that it
preceded its data.

## Why this round

Every number this project has published comes from a corpus that ships with the result.
That is the point — it is what makes a round checkable — and it is also a standing
liability: a fully public benchmark is eventually trained on, and an effect that survives
only on questions a model has already seen is not an effect.

ROADMAP item 10 is the defence. A held-out private split of twelve questions now exists
(`METHODOLOGY.md` §10.1), built under §9 and screened control-arm-only across three
batches. Its questions have never been published and never will be; only aggregates from
it are ever reported.

This round runs the public corpus and the private split **side by side, in one
collection**, and asks whether the project's strongest finding survives on questions that
were never published. It closes item 10's third acceptance clause.

The finding under test is **H4** — that replacing vague claims with specific figures raises
citation. It was measured at +0.493 on corpus v0.3 and +0.482 on v0.4, significant on every
model. If contamination is inflating anything, it is inflating this.

## Design

| | Public half | Private half |
|---|---|---|
| Corpus | `corpus/corpus_v0.4.json`, sha `f1d0672d1d295a66` | `private-v1`, sha `529939b6163befeb` |
| Built by | `corpus/build_corpus.py` | held out; not in this repository |
| Prompts | 48, 24 domains, 8 per target format | 12, 12 domains, 2 per target format |
| Documents | 6 per prompt; 5 non-target documents byte-identical across arms | same |
| Conditions | 2 — `control`, `treatment` | same |
| Models | 5-engine market panel | same |
| Runs per cell | 24 | same |
| Temperature | 1.0 | same |
| Document order | randomised per run from a seeded hash, recorded every run | same |
| Calls | 48 × 2 × 5 × 24 = 11,520 | 12 × 2 × 5 × 24 = 2,880 |

**Total 14,400 calls**, ~9.9M input and ~3.6M output tokens, estimated at $3.65 (low
pricing) to $10.36 (mid) from `run_pilot.py --dry-run` on both corpora. Both halves are
collected in the same session, against the same panel, with the same harness version, so a
divergence cannot be a difference of date, model routing or code.

The private half's **treatment arm has never been run**. Every private figure recorded
anywhere to date is control-only, because the §5.3 gate is about baseline placement and
running the treatment arm early would measure the very effect this round exists to report.

## Hypotheses

**H8. The H4 effect replicates on held-out questions.**

> Replacing vague claims with specific figures raises Citation Presence Rate on questions
> that have never been published.

**Falsified if** the private half's pooled `treatment` − `control` delta has a 95%
bootstrap CI that includes zero.

**H9. The effect is no larger on published questions than on held-out ones.**

> The public and private effects do not differ.

**Falsified if** the 95% bootstrap CI on the public − private difference excludes zero.

**Direction is predicted for H9, and only for H9.** Contamination inflates the *public*
side. A public effect significantly *larger* than the private one is the signature this
round is built to detect. A private effect larger than the public one would not indicate
contamination and would most likely mean the two corpora differ in difficulty; that
reading is recorded here so it cannot be presented afterwards as a subtle confirmation.

**H9 is stated as a null to be falsified, and failing to falsify it is not proof of
absence.** With twelve private questions the interval will be wide. The round reports the
divergence and its interval; it does not claim contamination is absent.

## The baseline confound, and how it is handled

The two halves do not start from the same place. Measured control-arm rates, both on the
current five-engine panel — public from the length-only round's control arm (v0.4 control
text, 5,760 runs), private from the three committed screening runs (1,440 runs):

| engine | public | private | difference |
|---|---|---|---|
| claude-haiku-4.5 | 0.385 | 0.229 | −0.156 |
| deepseek-chat | 0.652 | 0.465 | −0.187 |
| gemini-3-flash-preview | 0.646 | **0.806** | +0.160 |
| gpt-5.4-mini | 0.423 | 0.444 | +0.022 |
| grok-4.3 | 0.602 | 0.632 | +0.030 |
| **pooled** | 0.542 | 0.515 | −0.026 |

Pooled they are close. Per engine they are not, and that matters: **a risk difference is
bounded by its baseline.** A cell starting at 0.806 cannot rise by 0.48 whatever the
intervention does, so a naive public-minus-private comparison would report "contamination"
on gemini that is arithmetic rather than memorisation.

Three pre-committed consequences:

1. **The primary scale for H9 is the odds ratio**, which is not bounded by the baseline in
   the way a risk difference is. Risk differences are reported alongside, and where the two
   scales disagree the disagreement is the finding and is reported as such.
2. **These baselines are recorded here, before collection**, so that a per-engine
   divergence cannot be presented afterwards as a discovery when it was predictable from
   the starting rates.
3. **Per-engine results are primary**, as in every round since item 12. Any pooled figure
   states its weighting.

## Analysis plan

- **Primary metric:** target CPR (`METHODOLOGY.md` §4, Group A1).
- **Pairing:** per (prompt, model) — only the target document differs between arms.
- **Inference:** bootstrap over prompts, 10,000 resamples, 95% percentile CIs. Sign-flip
  permutation over condition labels within (prompt, model). No distributional assumptions,
  no scipy.
- **H9's contrast:** the difference of log odds ratios between halves, bootstrapped over
  prompts **within each half independently** and differenced, since the two halves share no
  prompts. Reported per engine and share-weighted-pooled.
- **Multiplicity:** Holm across the five engines for the per-engine H9 contrasts. H8 and
  the pooled H9 contrast are each single pre-specified tests and are not corrected.
- **Model exclusion:** the standing rule — any model above a 10% no-cite rate is excluded
  from pooled figures and reported separately.
- **Incomplete cells:** `analyze.incomplete_cells` reports any cell short of 24 runs and
  drops those below 80%. If any cell is dropped, the round is resumed to completion before
  analysis rather than analysed short.
- **Variance components:** η² for condition, half (public/private), prompt identity and
  target format. The half term is the one of interest and has not been estimated before.

## Stopping rule

One full round, both halves in one collection. No interim analysis. No adding prompts,
models or runs after seeing results. If the round fails on data health, it is rerun in full
and the failed attempt is archived, not merged.

## Spot check

**Already satisfied, and not re-run.** The standing §5.3 gate exists to confirm the control
arm is not at a ceiling or floor before a round is paid for. Both halves have that
evidence, on the current panel, from committed runs:

- Public: the length-only round's control arm, 5,760 runs, pooled 0.542 — v0.4 control
  text on this exact panel.
- Private: three screening runs, 1,440 runs, pooled 0.515, every question inside
  [0.25, 0.75].

Re-running the gate would spend roughly 2,000 calls to re-derive numbers already committed.
The gate's purpose is served; the evidence is cited rather than repeated.

## Reporting

Published under `results/published/` whatever the outcome.

**The public half is reported in full**, with raw responses shipped as in every round.
**The private half is reported as aggregates only** — pooled and per-engine effects with
intervals, and the H9 contrast. No private question, document, or per-prompt figure is
published, now or later. That restriction is what makes the split reusable; publishing a
per-prompt table would burn it as surely as publishing the corpus.

A null on H9 is the useful outcome and is reported with equal prominence: it would be the
first direct evidence that this project's headline number is not an artefact of its corpus
being public. A falsification of H9 is more useful still, and would mean the public
corpus's numbers need restating with a contamination caveat.

## Deviations

**2026-09-22 — H9 is mis-framed for the conditions this round runs under. Logged while
collection was still in progress and before any result was seen.**

H9 is stated above as a contamination test: "contamination inflates the *public* side. A
public effect significantly larger than the private one is the signature this round is
built to detect."

**That signature cannot appear, because the repository has never been public.** Corpus
v0.4 has never been published anywhere. Both halves of this round are equally unseen, so
there is no exposure asymmetry for H9 to detect, and a finding of "no divergence" would be
uninformative about contamination rather than evidence against it. The error is in this
pre-registration, not in the corpora or the collection.

**What the round does establish, and what it is now reported as:**

1. **A pre-publication baseline.** A contamination test is longitudinal by nature. Measured
   now, before the corpus is public, the public half's effect is the "before" against which
   a post-publication re-run is compared. Without it, a later measurement means nothing.
   This is the round's main value and it is time-critical in a way nothing else here is:
   once the repository is public, this measurement can never be taken.
2. **An equivalence check between the halves.** Whether the two corpora yield the same
   effect under conditions where no exposure asymmetry exists is a *precondition* for the
   contamination test, not the test itself. If they diverge now, the split needs fixing
   before it can serve as a comparator at all.
3. **Item 10's third acceptance clause**, which asks only that one round report public and
   private results side by side.

**H9 is therefore re-scoped, not abandoned.** Its statistic, contrast, scale and
multiplicity handling are unchanged — the odds-ratio primary, risk differences alongside,
Holm across five engines. Only its interpretation changes: it now reads as
**corpus equivalence**, and a CI on the difference that excludes zero means the halves are
not interchangeable, not that contamination has been found.

**The contamination test proper is a re-run of this exact design after the repository has
been public long enough for a training cycle**, comparing the public half's effect then
against the public half's effect now. That round inherits this pre-registration's design
and will cite this file as its baseline.

**H8 is unaffected.** Whether H4 replicates on twelve never-published questions is a real
question under any conditions, and it is the first time the private split's treatment arm
has been run.

Nothing about the collection is changed by this entry: same corpora, same hashes, same
panel, same analysis plan. Only the claim the round is entitled to make is narrowed.

---

**2026-09-22 — collection complete; 4 calls lost to HTTP 429 and refilled.** 14,400 calls,
4 errors, all `429 Too Many Requests` on deepseek, 0.03% of the round. Per the analysis
plan the round was resumed to completion rather than analysed short; the refill ran clean
and every cell reached 24 runs before analysis.

---

**2026-09-22 — the pre-registered primary scale for H9 is compromised by a saturated
treatment arm. Recorded before drawing any conclusion from it.**

The odds ratio was chosen as H9's primary scale because a risk difference is bounded by its
baseline and the halves' baselines differ. The odds ratio has its own failure mode, which
this data hits and which was not anticipated: **the treatment arm saturates.**

| engine | public treatment | private treatment |
|---|---|---|
| deepseek | 1152/1152 = 1.0000 | 288/288 = 1.0000 |
| gemini | 1152/1152 = 1.0000 | 288/288 = 1.0000 |
| gpt | 1150/1152 = 0.9983 | 288/288 = 1.0000 |
| grok | 1148/1152 = 0.9965 | 287/288 = 0.9965 |

At exactly 100% the odds are undefined, and the Haldane-Anscombe correction this analysis
applies makes them scale with the cell's size: `(n+0.5)/0.5`. Public cells hold 1,152 runs
and private cells 288, so **an identical 100% in both halves yields odds ratios differing
by 3.99×, from sample size alone, with no effect whatever.** In log terms that is +1.38
before any real difference is considered.

Both engines that flag significant on the per-engine H9 contrast decompose entirely into
that artefact and the control-rate differences this pre-registration tabulated in advance:

- deepseek, lnOR difference +0.932 = ln(3.99 × 0.634). The sample-size artefact supplies
  all of it; the control-rate difference pushes the other way and partly cancels it.
- gemini, lnOR difference +1.965 = ln(3.99 × 1.788). Artefact plus a control-rate gap that
  happens to point the same way.

**Neither is evidence about the corpora.** The per-engine H9 contrasts are reported with
this decomposition attached and are not interpreted as corpus differences. The pooled H9
contrast and the variance decomposition are unaffected by the unequal-n artefact in the way
the per-engine contrasts are, and both point the same way: pooled lnOR difference +0.535,
CI [−0.316, +1.972], includes zero; and η² for the public/private term is **0.0001**
against 0.2795 for condition.

The general lesson, which belongs in the standard rather than only here: **when an arm
saturates, neither scale works.** A risk difference is compressed by the ceiling and an
odds ratio is inflated by the correction, in proportion to the cell size. The fix is to
avoid saturating arms, which is what `METHODOLOGY.md` §9's ceiling discipline exists for —
and which the *treatment* arm has never been held to, only the control arm.

---

**2026-09-22 — `claude-haiku-4.5` excluded by the standing rule, and the rule is
mis-firing.** Applied as written: 19.3% no-cite on the private half exceeds the 10% limit,
so claude is excluded from pooled figures. Panel coverage drops from 98.9% to 89.6%.

The diagnosis does not match what the rule is for. The standing rule treats a high no-cite
rate as instruction-following failure — "not a visibility signal". Here it is a visibility
signal, and a clean one:

| half | condition | no-cite |
|---|---|---|
| public | control | 1.7% |
| public | treatment | 0.4% |
| private | control | **38.5%** |
| private | treatment | **0.0%** |

Claude declines to cite anything in 38.5% of private *control* runs and never once in
private *treatment* runs. That is not a parser failing; it is a model abstaining when no
document answers the question, then citing normally as soon as one does. It is spread
across the corpus rather than caused by one bad question — four questions under 10%, four
between 10 and 30%, four between 30 and 60%, none above 60%.

The exclusion stands for this round because the rule was pre-registered and applying it
selectively after seeing which way it cuts is exactly what pre-registration prevents. But
the rule conflates two different things, and on this evidence it discards the engine
behaving most correctly. Revising it is filed as follow-up work, not done here.
