# The headline effect holds on questions nobody has seen

**H4 replicates at +0.441 on twelve held-out questions. Which half a question came from
explains 0.01% of the variance in whether it gets cited.**

Published 2026-09-22. Pre-registered: `preregistrations/2026-09-contamination.md`,
committed before collection. 14,400 calls across two corpora in one session.

This round also broke two of its own methods, and those failures are reported here at the
same weight as the result, because both are load-bearing for how this project measures
things.

## What was asked

Every number this project publishes comes from a corpus that ships with the result. That
is what makes a round checkable, and it is also a standing liability: a benchmark that is
fully public is eventually trained on, and an effect that survives only on questions a
model has already seen is not an effect.

So a **held-out private split** was built — twelve questions, screened, never published,
and never to be published (`METHODOLOGY.md` §10.1). This round runs it beside corpus v0.4
in a single collection, same engines, same harness, and asks whether **H4** — that
replacing vague claims with specific figures raises citation, measured at +0.482 and
+0.493 on two earlier corpora — survives on questions that were never released.

**An important limit, logged mid-collection before any result was seen.** The
pre-registration framed this as a contamination test. It is not one: the repository has
never been public, so neither half has been exposed and there is no asymmetry to detect.
What it actually is:

1. the **pre-publication baseline** for a contamination test — a measurement that can only
   be taken before release, and after this it is gone;
2. a **corpus-equivalence check**, which is the precondition for the split working as a
   comparator at all.

The contamination test proper is a re-run of this design after publication, comparing the
public half against *itself* across two dates.

## H4 replicates

| engine | control | treatment | delta | 95% CI |
|---|---|---|---|---|
| deepseek-chat | 0.417 | 1.000 | **+0.583** | [+0.451, +0.701] |
| gpt-5.4-mini | 0.458 | 1.000 | **+0.542** | [+0.406, +0.674] |
| grok-4.3 | 0.656 | 0.997 | **+0.340** | [+0.229, +0.462] |
| gemini-3-flash | 0.767 | 1.000 | **+0.233** | [+0.125, +0.361] |
| **pooled, share-weighted** | | | **+0.441** | **[+0.324, +0.560]** |

Against +0.482 on v0.4 and +0.493 on v0.3. The interval excludes zero on every engine.

The per-engine spread tracks headroom exactly: gemini starts at 0.767 and gains 0.233,
deepseek starts at 0.417 and gains 0.583. Nothing can rise more than one minus where it
began, which is the whole of that pattern and is why the ordering should not be read as
engines differing in how much they reward specificity.

## The halves behave the same

Pooled difference in log odds ratios between halves: **+0.535, 95% CI [−0.316, +1.972]**,
which includes zero.

The variance decomposition says it more cleanly than any contrast can:

| term | η² |
|---|---|
| condition (vague vs specific) | **0.2795** |
| prompt identity | 0.1120 |
| target format | 0.0164 |
| model | 0.0102 |
| **half (public vs private)** | **0.0001** |

Which half a question came from explains one hundredth of one percent of the variance in
whether its document gets cited. The intervention explains a quarter.

## Two methods that broke

### 1. When an arm saturates, neither effect scale works

The pre-registration chose the **odds ratio** as H9's primary scale, for a stated and
correct reason: a risk difference is bounded by its baseline, and a cell starting at 0.767
cannot rise by 0.48 however good the intervention is.

The odds ratio has its own failure mode, which this data hits:

| engine | public treatment | private treatment |
|---|---|---|
| deepseek | 1152/1152 = 1.0000 | 288/288 = 1.0000 |
| gemini | 1152/1152 = 1.0000 | 288/288 = 1.0000 |

At exactly 100% the odds are undefined. The Haldane-Anscombe correction that makes them
computable sets them to `(n+0.5)/0.5`, which scales with the size of the cell — so **an
identical 100% in both halves produces odds ratios differing by 3.99×, from sample size
alone, with no effect whatever.** Public cells hold 1,152 runs, private cells 288.

Two engines flagged significant on the per-engine contrast after Holm correction. Both
decompose entirely into that artefact and the control-rate differences the pre-registration
had tabulated in advance:

- deepseek, +0.932 = ln(3.99 × 0.634) — the artefact supplies all of it, and the real
  control-rate difference pushes the other way and partly cancels it
- gemini, +1.965 = ln(3.99 × 1.788) — artefact plus a baseline gap pointing the same way

Neither says anything about the corpora, and they are not reported as though they do. The
pooled contrast and the variance decomposition are not distorted this way and both agree
the halves are equivalent.

**The general lesson:** `METHODOLOGY.md` §9's ceiling discipline has only ever been applied
to the *control* arm, because that is where a ceiling destroys an effect. This round shows
it is needed on the treatment arm too, for a different reason — not because the effect
disappears, but because **no effect scale remains interpretable.** The risk difference is
compressed by the ceiling and the odds ratio is inflated by the correction in proportion to
cell size.

### 2. The no-cite exclusion rule discarded the engine behaving most correctly

`claude-haiku-4.5` was excluded by the standing rule — any model above 10% no-cite is
dropped from pooled figures — on a 19.3% no-cite rate over the private half. Panel coverage
falls from 98.9% to 89.6%.

The rule exists to catch instruction-following failure: "a high no-cite rate is not a
visibility signal." Here it is precisely a visibility signal:

| half | condition | no-cite |
|---|---|---|
| public | control | 1.7% |
| public | treatment | 0.4% |
| private | control | **38.5%** |
| private | treatment | **0.0%** |

Claude cites nothing in 38.5% of private control runs and in none of the treatment runs. A
control document by construction answers none of the question's facts — so this is a model
**abstaining when nothing answers, then citing normally the moment something does.** It is
spread across the corpus rather than caused by one bad question: four questions under 10%,
four between 10 and 30%, four between 30 and 60%, none above 60%.

The exclusion stands for this round, because applying a pre-registered rule selectively
after seeing which way it cuts is the exact failure pre-registration prevents. But the rule
conflates *cannot follow the instruction* with *declines because nothing qualifies*, and on
this evidence it discarded the most defensible behaviour on the panel. Revising it is
follow-up work, not done retroactively here.

## Limits

- **Not a contamination test.** Logged before results were seen. It is the baseline for
  one.
- **Twelve private questions.** The interval on the half-to-half comparison is wide, and
  "no divergence detected" is not "no divergence exists."
- **Four engines in the pooled figures**, 89.6% of measured assistant traffic, after the
  claude exclusion above.
- **The treatment arm saturates**, so +0.441 is a floor on the effect, not an estimate of
  it. The true magnitude is not identified by this design at this baseline.
- **Synthetic documents.** Both corpora are authored text, not real-world pages. The
  verbatim-sourced corpora belong to ROADMAP item 11, closed separately
  (`../2026-09-20-tier1-scope/REPORT.md`).
- **One API plane.** The calibration study puts API/UI divergence at 0.368
  (`../2026-08-30-calibration-v1/REPORT.md`).

## Reproduction

```bash
python3 corpus/build_corpus.py
python3 analyze_contamination.py \
    --public results/runs_contamination_public.jsonl \
    --private private/results/runs_contamination_private.jsonl
```

The public half's 11,520 raw responses ship with this report. **The private half is
reported as aggregates only and always will be** — its per-prompt figures are never
published, because a per-prompt table would burn the split as surely as releasing the
corpus. `analyze_contamination.py` enforces that rather than leaving it to whoever runs it,
and `check_private.py` verifies no private identifier has reached a tracked file or a commit
message.
