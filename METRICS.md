# OpenGEO Metric Set v0.1

Candidate metrics for the open benchmark, with the hypothesis each is meant to test and the condition under which it gets dropped.

Design rule: **every metric here is computable from a fixed candidate corpus** — no proprietary panel, no live-web dependency, no privileged API. If a metric can only be computed by someone with a 27-billion-citation database, it does not belong in an open benchmark, however interesting it is.

---

## What the vendor literature gives us, and what it withholds

Reading Profound's research corpus, they have published a great deal — and the shape of what they publish is informative.

**Genuinely useful, and adoptable:**

| Finding | Source | Use to us |
|---|---|---|
| Query fanout uniqueness: ChatGPT 91%, Copilot 47%, Perplexity 14% | [What AI engines actually search for](https://www.tryprofound.com/blog/what-ai-engines-actually-search-for) (10k prompts, 14 days) | Sets required sample size per engine. High-fanout engines need more runs. |
| Word overlap between prompt and fanout query: ChatGPT 13%, Copilot 50%, Perplexity 88% | same | Retrieval and synthesis are differently coupled per engine — justifies our two-tier split |
| ~47% of response content is unsolicited "Editorial" | [The Parrot Problem](https://www.tryprofound.com/blog/the-parrot-problem) (50k prompts, 7 industries) | Answers are mostly *not* about your content. Denominator matters. |
| ~11% of claims about one brand were false/inaccurate | same | Fidelity is a measurable, unowned dimension |
| Top 50% of cited content is <13 weeks old | same | Freshness as a covariate |
| Social citation rate varies 3.6%–15.3% across models | [How query language reshapes AI citations](https://www.tryprofound.com/blog/how-query-language-reshapes-ai-citations) (3.25B citations) | Models are not interchangeable; never average across them |

**What they assert without publishing an experiment** — and therefore what is available to us:

> "The use of generic terms like 'enterprise grade', 'best in class', or 'industry leading' mean nothing to an answer engine because there's no extractable claim. The content on the right side of the equation reads more like 'P95 latency at 38 milliseconds'. Those are claims a model can actually retrieve and attribute." — *The Parrot Problem*

This is a **causal claim about content, stated as fact, with no experiment behind it.** It is also the single most repeated piece of GEO advice in the industry. It is directly testable in a fixed-corpus design, and testing it is the pilot's primary intervention (H4).

Similarly, the **AEO Content Score** is "a proprietary machine learning model trained on millions of top-cited pages" that predicts citation likelihood from "hundreds of signals." Note what that is: a model trained on *observational* data to predict *correlation* with being cited, sold as guidance for *causing* citation. Top-cited pages differ from uncited pages in a thousand ways — domain authority above all — and a predictor trained on that confound cannot separate "pages that get cited are structured this way" from "structuring this way gets you cited." An open benchmark can run the randomized version they cannot: same page, same corpus, one property changed.

---

## The metric set

### Group A — Selection: does the source get used at all?

**A1. Citation Presence Rate (CPR)** — *primary metric*

> CPR(d) = runs in which document d is cited ÷ total runs

Binomial per run. Report with a Wilson 95% interval, always. This is the workhorse and everything else is secondary to it.

**A2. Selection Share** — compositional

> Share(d) = citations to d ÷ all citations in the run, averaged over runs

Power-law distributed; report bootstrap CIs, never a bare mean.

### Group B — Prominence: how well is it used?

**B1. First-Citation Rate.** Share of runs where d is the first source cited. Position in the answer carries the attention, same as rank-1 in classic search.

**B2. Attributed Content Share.** Proportion of answer sentences attributed to d. This is the honest replacement for GEO-bench's *position-adjusted word count*, whose power-law decay was borrowed from search CTR curves and never validated for generative answers. We measure attribution directly and treat any positional weighting as a separate, explicit choice.

### Group C — Fidelity: is the content represented correctly?

This group is the clearest open space. GEO tooling measures *whether* you appear; almost nothing measures whether what's said about you is *right*, and the one vendor doing it (FactCheck) does so as a proprietary product. Meanwhile there is a mature academic literature to borrow from — [ALCE](https://arxiv.org/pdf/2305.14627) defines citation precision and recall via entailment, validated against human judgment at Cohen's κ = 0.698 (recall) and 0.525 (precision).

**C1. Claim Fidelity Rate.** Of the claims the answer attributes to d, the share actually entailed by d. This is ALCE's citation precision, transplanted into the GEO setting. **Nobody in the GEO industry reports this.**

**C2. Distortion Rate.** Share of runs containing at least one claim attributed to d that d does not support. The measurable core of the Parrot Problem.

**C3. Verbatim Retention.** Does distinctive phrasing from d survive into the answer? Cheap to compute, and a proxy for whether the model is quoting or paraphrasing you — which determines whether your framing survives.

### Group D — Confounds that must be measured, not assumed away

This is where an open benchmark earns its keep. Every metric above is meaningless if the variance below swamps it.

**D1. Position Sensitivity Index (PSI)** — *the one that could reframe the field*

> PSI(d) = max over positions of CPR(d, position) − min over positions of CPR(d, position)

Move the identical document to different slots in the candidate set and measure how much citation rate changes. Content held perfectly constant.

The long-context literature says this effect will be large: models attend disproportionately to the beginning and end of context, degrading in the middle ("lost in the middle"), driven by RoPE's long-term decay — and a [SIGIR 2026 reproduction study](https://arxiv.org/abs/2605.27105) confirms document position and context size effects while noting that small topic sets can mask or exaggerate them.

**If PSI exceeds the effect of any content intervention, then the entire content-optimization premise of the GEO industry is second-order to retrieval-set position.** That is a publishable finding, it is cheap to produce, and it is exactly the result a company selling content optimization has no incentive to look for.

**D2. Run Stability (ICC).** Within-condition reproducibility per model. Establishes the noise floor. A metric whose ICC is near zero cannot support any claim at achievable sample sizes and should be dropped from the standard.

**D3. Cross-Model Agreement (Kendall's W).** Do models agree on which documents deserve citation? If W is low, "GEO" is not one thing — it is N per-model optimization problems, and any single-number "AI visibility score" is incoherent by construction. This is a direct test of whether the product category's central metric is meaningful.

### Group E — Content properties (independent variables, not metrics)

The hypothesized levers, coded per document: extractable-claim density (specific figures, named quantities), quotability, structural markup, direct-answer proximity, hedging density, self-promotional tone.

---

## Pilot hypotheses

| ID | Hypothesis | Falsified if |
|---|---|---|
| **H1** | CPR is reliable enough to measure at n=10 runs | Within-condition ICC < 0.5 across most models |
| **H2** | Position effect (PSI) is large — comparable to or larger than content effects | PSI < 0.05 across models |
| **H3** | Cross-model agreement on citation-worthiness is low | Kendall's W > 0.7 |
| **H4** | Extractable-claim density causally raises CPR (Profound's specificity claim) | Paired effect CI includes zero |
| **H5** | Metrics behave consistently across content formats | Format × model interaction dominates main effects |

**H2 and H3 are the ones worth running for.** Both are cheap, both are things the incumbent has no incentive to publish, and either result is interesting: if position dominates content, the industry's advice is misdirected; if models disagree with each other, the industry's core metric is incoherent.

**Scope honesty:** this pilot has 12 prompts, below the 25-prompt floor set in the methodology spec. It is powered to validate metric *reliability* and to estimate *variance components* for designing Round 1 — it is not powered to publish an effect size for H4. Report H4 as an interval and a variance estimate, not a finding.

---

## Design

Fixed candidate corpus; retrieval held constant by construction. Each prompt carries **6 documents in 6 different content formats** (blog, news, docs, product page, forum/UGC, reference), so format is a fully paired within-prompt factor — the cleanest available test of H5.

One document per prompt is designated the **target**. Only the target varies between conditions (generic vs. claim-dense); the other five are byte-identical across arms. Document order is **randomized per run**, and the target's position is recorded, which is what makes PSI estimable at no extra cost.

Documents are short (60–110 words) by design. Engines retrieve *chunks*, not whole pages, so a chunk-sized unit is more faithful to the real pipeline than a full article would be — and it keeps token cost inside the pilot budget.

**Stated limitation, to be repeated in any publication:** this measures the synthesis stage only. It says nothing about whether a page gets retrieved in the first place, which is likely where the larger real-world effects live.
