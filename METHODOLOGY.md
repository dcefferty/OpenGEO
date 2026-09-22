# OpenGEO: An Open Measurement Standard for Generative Engine Optimization

**Measurement standard v0.2.** Status: implemented and in use. Updated September 2026.

This is the technical specification: what the benchmark measures, how it is sampled and
analysed, and what every published round must record. Why the project exists, what is
planned, and what has already run are in `ROADMAP.md`. Rules for agents and contributors
working in the repo are in `CLAUDE.md`.

Section numbers are stable. Published reports and pre-registrations cite them by number,
so §2, §3 and §5.2 keep their meaning even as their text is updated.

---

## 1. Scope and non-goals

**In scope**

- A frozen, versioned, openly published **prompt corpus** per vertical.
- A **controlled-intervention protocol** that isolates cause from correlation.
- A **statistical standard** for reporting, adopted from prior work and formalised.
- An **engine adapter contract** plus a mandatory provenance record per run (§8).
- Periodic published **benchmark rounds**, re-run as models change.

**Explicitly not in scope**

- Per-customer brand tracking dashboards. That layer is commoditised and well funded
  ([OneGlanse](https://github.com/aryamantodkar/oneglanse),
  [gego](https://github.com/AI2HU/gego), plus Profound, Peec and Semrush commercially).
- Recommendations, audits or "fix your site" tooling. Selling the fix destroys the
  credibility of the measurement.
- Claiming to replicate the consumer product experience exactly. See §3, and the
  calibration study that measures the gap instead of asserting it away.

---

## 2. The central design problem: two stages, two different experiments

A generative engine answer is produced by two stages, and the GEO literature routinely
conflates them:

| Stage | Question | What controls it |
|---|---|---|
| **Retrieval** | Does my page get into the candidate set at all? | Crawlability, index freshness, query fanout, domain authority |
| **Synthesis** | Given that it's in the set, does the model cite it in the answer? | Content structure, quotability, stats, phrasing, extractability |

Almost every published "GEO tactic" is a synthesis-stage claim ("add statistics", "use
expert quotes") sold as if it affects the whole pipeline. The largest real-world effects
are probably retrieval-stage and technical.

**Separating these two stages is the core scientific contribution of this project.** It
gives the benchmark a two-tier structure.

### Tier 1 — Synthesis benchmark (fast, cheap, fully reproducible)

Fix the retrieval set. Supply a frozen corpus of source documents directly in context,
pose the query, and measure which sources get cited. Apply the intervention to exactly
one source document; hold every other document constant.

- **Reproducible by construction** — the corpus ships with the benchmark, so anyone can
  re-run it and get comparable results. No live-web dependency.
- **Isolates the causal effect** of content properties on citation, with retrieval held
  constant by design.
- **Limitation, stated in every publication:** this measures the synthesis stage only. A
  Tier 1 result is a claim about *what a model does with content it already has*, not a
  claim about traffic.

This is GEO-bench's design, run against real frontier models rather than a GPT-3.5
stand-in, with proper statistics, and versioned as models change.

### Tier 2 — Live-web field experiment (slow, expensive, high external validity)

Real pages on real domains, randomised to treatment and control, published, then measured
after recrawl.

- **Timing is set by the retrieval loop.** Median time-to-first-citation is ~6.8 days,
  P90 ~37 days. A Tier 2 round is a two-month experiment.
- **Requires donated inventory** — many real pages across many domains, contributed under
  a standard protocol.
- **Randomisation is what makes it worth doing.** Pair pages within a site by topic and
  traffic, randomise treatment within pair, so site-level authority differences cancel.

Tier 1 makes the project exist. Tier 2 makes it matter.

---

## 3. Query plane

| | API with search | Browser automation (consumer UI) |
|---|---|---|
| Reproducibility | High — pinned model IDs, logged params | Low — UI changes silently, no version pin |
| Cost / speed | Cents per run, parallelisable | Slow, proxy costs, CAPTCHAs |
| ToS posture | Clean, intended use | Gray at best |
| Maintenance | Low | High and unpredictable |
| Fidelity to real users | **Imperfect and documented as such** | Higher, but not ground truth either |

**The API plane is the primary measurement plane.** It is the only one reproducible by a
third party, the only one whose maintenance burden is sustainable, and the only one that
stays clean legally as the project gains visibility.

**The fidelity gap is a measured quantity, not a disclaimer.** Graphite documented that
responses from APIs, logged-out accounts and logged-in accounts "can vary significantly"
and concluded that tracking tools "should not be used as ground truth" — but published no
magnitude. The **Calibration Study** measures it: a small prompt set executed across
planes, publishing a per-engine divergence coefficient. Manual or lightly-assisted
collection is acceptable because n is small and the study runs periodically.

**Engine panel.** Engines are selected and ordered by measured market share rather than
convenience, so the panel matches the engines readers actually use; the shares, their
source and their caveats live in `engine_weights.py`. Pooled figures for a round with an
uneven panel are reported share-weighted, with per-engine results remaining primary.

Two constraints discovered by running this:

- **Not all engines are testable in Tier 1.** An engine that performs live web search and
  ignores supplied sources cannot be measured under a held-constant retrieval set, and the
  failure is silent: out-of-range citation indices are dropped by the parser, so such an
  engine looks like a no-cite model rather than an incompatible one. Verify that an engine
  cites only the supplied set before adding it to a panel.
- **A model can regress between rounds.** Check per-model no-cite rate and control-arm CPR
  against the previous round on identical text before trusting a comparison.

---

## 4. Metrics

Every metric is an estimator with a stated denominator. **The unit of observation is the
run, not the report.** Every metric here is computable from a fixed candidate corpus — no
proprietary panel, no live-web dependency, no privileged API.

### 4.1 What the vendor literature gives us, and what it withholds

Adoptable, and adopted:

| Finding | Source | Use to us |
|---|---|---|
| Query fanout uniqueness: ChatGPT 91%, Copilot 47%, Perplexity 14% | [What AI engines actually search for](https://www.tryprofound.com/blog/what-ai-engines-actually-search-for) | Sets required sample size per engine |
| Prompt/fanout word overlap: ChatGPT 13%, Copilot 50%, Perplexity 88% | same | Retrieval and synthesis are differently coupled per engine — justifies the two-tier split |
| ~47% of response content is unsolicited "Editorial" | [The Parrot Problem](https://www.tryprofound.com/blog/the-parrot-problem) | Answers are mostly *not* about your content. Denominator matters |
| ~11% of claims about one brand were false or inaccurate | same | Fidelity is a measurable, unowned dimension |
| Top 50% of cited content is <13 weeks old | same | Freshness as a covariate |
| Social citation rate varies 3.6%–15.3% across models | [How query language reshapes AI citations](https://www.tryprofound.com/blog/how-query-language-reshapes-ai-citations) | Models are not interchangeable; never average across them |

What is asserted without an experiment, and is therefore available to test:

> "The use of generic terms like 'enterprise grade', 'best in class', or 'industry
> leading' mean nothing to an answer engine because there's no extractable claim. The
> content on the right side of the equation reads more like 'P95 latency at 38
> milliseconds'." — *The Parrot Problem*

That is a **causal claim about content, stated as fact, with no experiment behind it**,
and it is the single most repeated piece of GEO advice in the industry. It is directly
testable in a fixed-corpus design, and testing it was the first intervention (H4).

The **AEO Content Score** is a proprietary model "trained on millions of top-cited pages"
predicting citation likelihood from "hundreds of signals" — that is, a model trained on
*observational* data to predict *correlation* with being cited, sold as guidance for
*causing* citation. Top-cited pages differ from uncited pages in a thousand ways, domain
authority above all. An open benchmark can run the randomised version: same page, same
corpus, one property changed.

### 4.2 The metric set

#### Group A — Selection: does the source get used at all?

**A1. Citation Presence Rate (CPR)** — *primary metric*

> CPR(d) = runs in which document d is cited ÷ total runs

Binomial per run. Report with a Wilson 95% interval, always. This is the workhorse and
everything else is secondary to it.

**A2. Selection Share** — compositional.

> Share(d) = citations to d ÷ all citations in the run, averaged over runs

Power-law distributed; report bootstrap CIs, never a bare mean.

#### Group B — Prominence: how well is it used?

**B1. First-Citation Rate.** Share of runs where d is the first source cited.

**B2. Attributed Content Share.** Proportion of answer sentences attributed to d. This is
the honest replacement for GEO-bench's *position-adjusted word count*, whose power-law
decay was borrowed from search CTR curves and never validated for generative answers.
Attribution is measured directly; any positional weighting is a separate, explicit choice.

**Linked Mention Rate.** Proportion of runs where the mention carries a clickable URL.
Kept separate from CPR — this is the metric with traffic attached. Any series spanning a
product change in link behaviour must be split into two eras.

#### Group C — Fidelity: is the content represented correctly?

The clearest open space. GEO tooling measures *whether* you appear; almost nothing
measures whether what's said about you is *right*. There is a mature literature to borrow
from: [ALCE](https://arxiv.org/pdf/2305.14627) defines citation precision and recall via
entailment, validated against human judgment at Cohen's κ = 0.698 (recall) and 0.525
(precision).

**C1. Claim Fidelity Rate.** Of the claims the answer attributes to d, the share actually
entailed by d — ALCE's citation precision in the GEO setting. **Nobody in the GEO industry
reports this.**

**C2. Distortion Rate.** Share of runs containing at least one claim attributed to d that
d does not support. The measurable core of the Parrot Problem.

**C3. Verbatim Retention.** Does distinctive phrasing from d survive into the answer?
Cheap to compute, and a proxy for whether the model is quoting or paraphrasing.

Group C is judged by a model, which introduces its own measurement error. Requirements:
the judge must come from outside the panel under test; judgments truncated before a
conclusion are missing data, not a guess; and a second judge from a different vendor must
reproduce the result before it is published. Absolute C1/C2 levels are judge-relative —
report the contrast, and report both judges.

#### Group D — Confounds that must be measured, not assumed away

**D1. Position Sensitivity Index (PSI)**

> PSI(d) = max over positions of CPR(d, position) − min over positions of CPR(d, position)

Move the identical document to different slots and measure how much citation changes,
content held constant. If PSI exceeds the effect of any content intervention, the entire
content-optimisation premise is second-order to retrieval-set position.

**D2. Run Stability.** Within-condition reproducibility per model, reported as split-half
reliability with Spearman-Brown correction. Establishes the noise floor.

**D3. Cross-Model Agreement (Kendall's W).** Do models agree on which documents deserve
citation? **W must be read against a within-model split-half baseline** — a model at
finite runs does not agree with itself, so raw cross-model W is mostly noise floor. Only
the gap between the two is evidence.

**Rank Stability.** Consistency of ordering across repeated runs, via bootstrap CI. The
audit metric on all the others: if rank is unstable at a given sample size, no number from
that sample is trustworthy.

#### Group E — Content properties (independent variables, not metrics)

The hypothesised levers, coded per document: extractable-claim density (specific figures,
named quantities), quotability, structural markup, direct-answer proximity, hedging
density, self-promotional tone.

### 4.3 Deprecated by this standard

A single composite "visibility score." Unreproducible, no denominator, not comparable
across vendors. **A number without a denominator, an engine breakdown and an interval is
not a measurement.**

---

## 5. Sampling and statistics

### 5.1 Baseline: estimating a level

For a single (prompt, engine) estimate, prior work supports 10 runs as a floor
(MAE ~5.6%) and 40 runs for 94.9% of prompts under 5% MAE. Report a Wilson 95% interval
always. Be honest about how wide these are:

| runs | p̂=0.10 | p̂=0.30 | p̂=0.50 |
|---|---|---|---|
| 10 | 1.8–40.4% | 10.8–60.3% | 23.7–76.3% |
| 20 | 2.8–30.1% | 14.5–51.9% | 29.9–70.1% |
| 30 | 3.5–25.6% | 16.7–47.9% | 33.2–66.8% |
| 100 | 5.5–17.4% | 21.9–39.6% | 40.4–59.6% |

At 10 runs, a 30% visibility estimate is compatible with anything from 11% to 60%.

### 5.2 The design that matters: detecting a *difference*

Estimating a level and detecting an intervention effect are different problems. Use a
**paired design** — same prompt, treated vs control source — analysed with prompt as a
blocking factor.

**Analysis:** sign-flip permutation test on per-prompt differences for the headline test,
bootstrap CIs over prompts for intervals. Assumption-light and reproducible by anyone.

**Power**, simulated for this spec (paired design, per-prompt baseline ~ Beta(1.2, 3),
sign-flip permutation, α=0.05):

| prompts | runs/arm | OR 1.3 | OR 1.5 | OR 2.0 | calls |
|---|---|---|---|---|---|
| 25 | 20 | 0.35 | 0.68 | 0.99 | 1,000 |
| 50 | 20 | **0.66** | **0.95** | 1.00 | 2,000 |
| 50 | 30 | 0.84 | 1.00 | 1.00 | 3,000 |
| 100 | 20 | 0.91 | 1.00 | 1.00 | 4,000 |

**Anything below 25 prompts is underpowered for realistic effects and should not be
published as a finding.**

**Correction, from this project's own data.** That Beta(1.2, 3) prior (mean 0.288) was
wrong. The first pilot's real control CPR averaged 0.867, with 67% of (prompt, model)
cells at a literal 100% ceiling, which collapses achievable power — 0.34 rather than 0.87
for OR=1.3 at identical size. **Baseline placement dominates sample size.** A corpus whose
control arm sits in a sensitive 30–70% band is worth more than twice the calls. Size a
round with `size_round1.py`, which resamples measured cells rather than assuming a prior.

**Pairing is most of the power.** At identical budget (50 prompts × 20 runs, OR 1.5):
paired 0.95, unpaired 0.32. Any study comparing treated pages against a *different* set of
control pages throws away most of its sensitivity.

Two consequences the standard states explicitly: **more runs of a frozen prompt set beat
more prompts run once**, because the variance lives at the run level; and inference is at
the corpus level. "Adding statistics raised citation odds across this corpus" is
defensible; "adding statistics will get *your page* cited" is not.

### 5.3 Pre-registration

Each round publishes hypotheses, corpus hash, interventions, primary metric, analysis plan
and stopping rule **before collection**, as a timestamped file in `preregistrations/`. The
git timestamp is the evidence. It is the strongest credibility signal available in a field
where every published number comes from someone selling something, and it protects against
the garden of forking paths.

Three rules that follow from rounds that went wrong:

- **A pre-committed spot check runs after pre-registration and before the full round** —
  a few hundred calls confirming the baseline is not at a ceiling or floor. It is a go/no-go
  gate on the *design*, never a peek at the *result*, and its only permitted outcomes are
  "proceed as written" or "redesign and log the deviation."
- **A gate must compare like with like.** A gate stated against a figure pooled over the
  full corpus cannot be evaluated on a subset; per-prompt CPR varies far too much. State
  the gate against the same prompts it will be checked on.
- **Deviations are logged in the pre-registration, dated, before analysis.** Including the
  uncomfortable ones: if outcome data was seen before a decision was made, that is recorded
  too.

No interim analysis. A round runs to completion, or is rerun in full and the failed attempt
archived rather than merged.

---

## 6. Feasibility and cost

Compute cost is not the constraint. Measured on real rounds:

| Round | Calls | Cost |
|---|---|---|
| Spot check (6 prompts × 8 models × 2 conditions × 12 runs) | 2,304 | ~$2 |
| Full round (48 prompts × 8 models × 2 conditions × 24 runs) | 18,432 | ~$5–14 |
| Four-condition dose ladder (48 × 5 × 4 × 24) | 23,040 | ~$25 |
| Group C judging pass over one round | ~11,700 | ~$26 |

The real constraints are wall-clock time and maintenance, which is why the API plane and
Tier-1-first sequencing matter. Engines change underneath the benchmark: model
deprecations, retrieval changes and product shifts each invalidate comparisons across the
boundary. Treat each round as a dated, immutable release rather than a live dashboard.

---

## 7. Threats to validity

| Threat | Mitigation |
|---|---|
| **Contamination** — corpus leaks into training data, or vendors optimise to the public set | Public + held-out private split; publish only aggregate results from the private half; rotate a fraction of prompts each round |
| **Gaming** — parties tune content to benchmark specifics | Never publish a score a brand can chase. Publish intervention effects, not leaderboards of brands |
| **Engine drift** | Pin model IDs; date-stamp every round; refuse cross-round comparison across a known product change; log `model_returned` on every call |
| **Tier 1 over-generalisation** | Every Tier 1 result carries a fixed caveat: synthesis stage only, retrieval held constant |
| **Ceiling and floor effects** | Measure the control arm's CPR before running; see §5.2 and §9 |
| **Judge-model artifacts** (Group C) | Judge from outside the tested panel; truncated judgments treated as missing; a second different-vendor judge must reproduce the result |
| **Time-of-day / regional effects** | Randomise collection times; log region; never compare a business-hours sample to a round-the-clock one |
| **Multiple comparisons** | Pre-register the primary contrast; correct across the secondary family and say which correction |
| **Own incentives** | If the project ever monetises, the measurement layer and any advisory layer must be separated in public and in fact |

---

## 8. Provenance record (mandatory per run)

A run without a complete record does not count toward a published number. This schema is
the most reusable artifact in the project — it is what another tool would adopt if the
standard succeeds.

```
run_key, harness_version, timestamp_utc,
corpus_version, prompt_id, domain, condition, rep,
model (requested), model_returned (as served), temperature,
presentation_order[], target_doc_id, target_format, target_slot, n_docs,
response_text (raw), finish_reason, usage, latency_s,
cited_display_idx[], cited_doc_ids[], target_cited, target_cite_rank,
sentence_citations[]
```

Two notes. Store the **raw response**, not just extracted citations — extraction logic will
change and the derivation has to be repeatable. And version the **extractor** separately,
because a silent change in mention-detection is indistinguishable from an engine change.

---

## 9. Corpus construction

The corpus decides what a round can detect. These rules were each learned by a round that
failed first.

**Length is matched, not assumed irrelevant.** Target variants are held within ±3 words of
each other, so an effect cannot be word count in disguise. Whether length matters on its own
is itself an open question under test rather than an assumption.

**Versions are immutable once a round has run against them.** Changes get a new version
number; a changed denominator makes a trend line fiction.

**All document text lives in the builder**, never in generated JSON, and the built corpus
carries a hash that the pre-registration records.

**Avoid the ceiling.** If the control arm is cited almost always, no intervention can show
an effect. Three failure modes, in the order they were discovered, each caught only by
testing against real models — never by inspection or keyword scripts:

1. **Literal keyword echo.** A control that omits the specific fact but reuses a noun from
   the question gets quoted as justification anyway, even when the model says it cannot
   answer.
2. **Qualitative echo.** A control with zero keyword overlap still gets cited if any
   sentence reaches the same directional conclusion the question asks about, in different
   words.
3. **Presence, not completeness.** Answering *one* of a question's facts specifically is
   enough to saturate citation. Models discriminate on presence versus absence of any
   specific on-topic content, not on how completely the answer is given. A "half-specific"
   baseline does not land mid-range; it lands at the ceiling.

The consequence: a genuinely mid-range baseline is one that is topically adjacent but
answers none of the question's facts. Build the control that way, then confirm it with the
§5.3 spot check before committing to a full round.

**"Topically adjacent" is a distance, and it is steeper than it looks (2026-09-21).**
Withholding the facts is not sufficient. A control that answers none of a question's
facts, reuses none of its distinctive nouns and reaches no matching directional conclusion
will *still* saturate if it sits on the same **dimension** of the subject the question asks
about. Measured on a fresh six-question corpus whose controls were rewritten between two
spot checks:

| the control's relation to the question | observed control CPR |
|---|---|
| same dimension, facts withheld | 0.86 – 0.97 |
| one dimension away | 0.41 – 0.75 |
| two dimensions away — an unrelated aspect of the subject | 0.17 |

One dimension away is the target. Concretely: for a question about *when to replace* a
part, a control about *how to make it last* is the same dimension and pins near the
ceiling; a control about *how to choose between brands* is one away; a control about the
manufacturing history of the part is two away and pins near the floor.

Two practical consequences. Aim one dimension away from the start rather than withholding
facts and hoping. And **do not re-tune a control against the same spot check more than
once** — a second pass is already fitting that sample's noise, which is a different error
from the ceiling the gate exists to catch. A question that fails twice goes back to the
pool and is rebuilt from scratch, not nudged again.

Watch `cites/answer` alongside the target's rate. If the whole field is cited more
generously than a comparable corpus, the non-target documents are collectively too
on-topic. That cannot bias a paired contrast — the non-targets are identical across arms —
but it holds the target's baseline higher than it needs to be, so include one or two
clearly tangential documents per question.

---

## 10. Publication

**Publish nulls with equal prominence.** A standard that only publishes wins is a
marketing site. A round is published whatever direction it comes back, and the
pre-registration says so before the data exists.

**Rounds are immutable and dated.** Raw responses ship with the result; the raw data being
downloadable is the differentiator over every commercial competitor.

**The public findings page is generated from a ledger**, never hand-edited — see
`results/findings.json` and `build_findings.py`. Every figure on it cites the committed
report it comes from, and prose claims carry assertions the build checks against the data.

**Licence:** code MIT; data and results CC-BY-4.0, so vendors can cite the numbers with
attribution.

### 10.1 The held-out private split

A benchmark that is fully public is eventually trained on. The defence is a **private
split**: questions the public corpus does not contain, run alongside the public ones, with
**only aggregate results published**. A result that holds on both is not an artefact of the
public set having been seen; a result that holds only on the public half is evidence of
contamination or of the corpus having been fitted.

The split is a *check on* the public numbers, not a source of headline ones. Nothing is
ever claimed from the private half alone, because nobody can verify it.

**It lives outside the repository, under a gitignored `private/`.** This is not a
preference. Git history is permanent, and in this project the history *is* the
pre-registration evidence — the timestamp on a committed pre-registration is what proves it
preceded its data. A private question committed once cannot be made private again without
rewriting that history, and that evidence is not tradeable. So the rule is absolute:
material that has ever been committed to the public repository can never become part of
the split, no matter that the repository was private at the time.

Two consequences follow, and both are easy to get wrong:

- **A question leaks by being mentioned, not just by being committed.** A prompt_id in a
  roadmap note, a pre-registration, a probe write-up or a commit message burns that
  question as thoroughly as committing its corpus would. `check_private.py` checks tracked
  files *and* every commit message, and must pass before any publication and before the
  repository is made public.
- **The split must be sourced fresh.** It cannot be assembled by holding back part of an
  existing corpus after the fact.

**Size and rotation.** The split should be large enough that a divergence between halves is
detectable rather than noise — at the reliability established in §5.2, that means treating
it as a corpus in its own right, not a handful of spare questions. A fraction of public
questions rotates into retirement each round, so the public set ages out rather than
accumulating exposure indefinitely.

**What a round reports.** Public results in full, with raw responses. Private results as
aggregates only: the pooled effect, its interval, and whether it agrees with the public
half. If the two disagree, that disagreement is the finding and is published as such.

---

## Sources

- [GEO: Generative Engine Optimization](https://arxiv.org/abs/2311.09735) — Aggarwal et al., KDD 2024
- [Quantifying Uncertainty in AI Visibility](https://arxiv.org/abs/2603.08924) — Sielinski, 2026
- [Demystifying Randomness in AI](https://graphite.io/five-percent/demystifying-randomness-in-ai) — Graphite
- [ALCE: Enabling Large Language Models to Generate Text with Citations](https://arxiv.org/pdf/2305.14627) — Gao et al.
- [AI Visibility Metrics: Formulas, Benchmarks & Sample Sizes (2026)](https://nicklafferty.com/blog/ai-visibility-metrics-reference/) — Lafferty
- [OneGlanse](https://github.com/aryamantodkar/oneglanse), [gego](https://github.com/AI2HU/gego), [geo-aeo-tracker](https://github.com/danishashko/geo-aeo-tracker) — existing open-source trackers
