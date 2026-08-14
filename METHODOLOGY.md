# OpenGEO: An Open Measurement Standard for Generative Engine Optimization

**Methodology Specification v0.1 (draft)**
Status: design document, pre-implementation
Date: August 2026

---

## 0. Read this first: the positioning has to be sharper than "measurement rigor"

Since the initial framing, one thing changed. The statistical-rigor gap is **partially closed already**, and by people with more data than you will ever have:

- **[arXiv 2603.08924](https://arxiv.org/abs/2603.08924)** (Sielinski, March 2026, revised June 2026) established the core statistical argument: citation distributions are power-law, run-to-run variance is large, bootstrap CIs show many reported domain differences sit inside the noise floor, and rank instability extends well beyond the tail.
- **[Graphite's "Demystifying Randomness in AI"](https://graphite.io/five-percent/demystifying-randomness-in-ai)** published the empirical sampling work: 200-response ground truth, Wilson score intervals, sequential sampling, and the finding that 10 responses gives ~5.6% mean absolute error with 98.6% of prompts under 10% MAE.
- **[Profound's research](https://nicklafferty.com/blog/ai-visibility-metrics-reference/)** has published a full metrics taxonomy with benchmarks — time-to-first-citation (median 6.81 days, P90 37.10), co-citation rates, prompt fanout uniqueness (ChatGPT 91% vs Perplexity 14%), shopping trigger rates by category.

If you launch "a project that says visibility numbers need confidence intervals," you are publishing a summary of work that already exists.

**The gap that is still genuinely open has two halves:**

**(a) Reproducibility.** Every benchmark number above comes from a proprietary panel — 27M prompts, 700K conversations, 100.7M runs. Nobody outside those companies can verify, replicate, or re-run any of it. The vendor publishing the benchmark is the vendor selling against the benchmark. There is no independently auditable number in this entire field.

**(b) Causality.** Everything published is *observational*. It describes what visibility looks like. The causal question — *if I change X on my page, does citation rate go up, by how much, and on which engines* — has been answered publicly exactly twice: the Princeton GEO paper (2023–24), and a single Profound A/B (Markdown vs HTML, 381 pages, 16% mean lift, **reported as not statistically significant**). That is the entire public evidence base for an industry with $300M+ of invested capital telling people what to do to their websites.

And the Princeton result has a specific, disqualifying limitation that almost nobody in the marketing discourse mentions: **GEO-bench never queried a real generative engine.** It simulated one — Google Search top-5 retrieval, then GPT-3.5-turbo synthesis. Its headline numbers ("+41% from adding statistics") describe the behavior of a 2023 research pipeline, not ChatGPT, not Gemini, not AI Overviews. Those numbers are now cited across hundreds of agency blog posts as settled fact about live engines.

**So the project is: the open, reproducible, causal benchmark for GEO.** The statistical discipline is table stakes you adopt from prior work and cite. The contribution is running real controlled experiments on real engines with open data and an open harness, so the results can be checked.

That is a defensible position precisely because a funded vendor cannot credibly occupy it.

---

## 1. Scope and non-goals

**In scope**

- A frozen, versioned, openly published **prompt corpus** per vertical.
- A **controlled-intervention protocol** that isolates cause from correlation.
- A **statistical standard** for reporting (adopted from prior work, formalized).
- An **engine adapter contract** plus a mandatory provenance record per run.
- Periodic published **benchmark rounds**, re-run as models change.

**Explicitly not in scope**

- Per-customer brand tracking dashboards. That layer is commoditized and well funded ([OneGlanse](https://github.com/aryamantodkar/oneglanse), [gego](https://github.com/AI2HU/gego), plus Profound/Peec/Semrush commercially). Competing there is how this project dies.
- Recommendations, audits, or "fix your site" tooling. Selling the fix destroys the credibility of the measurement. If it works, someone else builds that layer on top — ideally paying you for it later.
- Claiming to replicate the consumer product experience exactly. See §3.

---

## 2. The central design problem: two stages, two different experiments

A generative engine answer is produced by two stages, and **the GEO literature routinely conflates them**:

| Stage | Question | What controls it |
|---|---|---|
| **Retrieval** | Does my page get into the candidate set at all? | Crawlability, index freshness, query fanout, domain authority |
| **Synthesis** | Given that it's in the set, does the model cite it in the answer? | Content structure, quotability, stats, phrasing, extractability |

Almost every published "GEO tactic" is a synthesis-stage claim ("add statistics," "use expert quotes") being sold as if it affects the whole pipeline. Meanwhile the largest real-world effects are probably retrieval-stage and technical (Profound's own guidance: a page uncited past day 37 is almost always a robots.txt or crawler-access problem, not a content-quality problem).

**Separating these two stages is the core scientific contribution of this project.** It gives the benchmark a two-tier structure.

### Tier 1 — Synthesis benchmark (fast, cheap, fully reproducible)

Fix the retrieval set. Supply a frozen corpus of source documents directly in context, pose the query, and measure which sources get cited. Apply the intervention to exactly one source document; hold every other document constant.

- **Reproducible by construction** — the corpus ships with the benchmark, so anyone can re-run it and get comparable results. No live web dependency.
- **Isolates the causal effect** of content properties on citation, with retrieval held constant by design.
- **Runs in hours for tens of dollars** (see §6).
- **Limitation, stated loudly in every publication:** this measures the synthesis stage only. A Tier 1 result is a claim about *what a model does with content it already has*, not a claim about traffic.

This is GEO-bench's design — but run against real 2026 frontier models rather than a GPT-3.5 stand-in, with proper statistics, and versioned as models change.

### Tier 2 — Live-web field experiment (slow, expensive, high external validity)

Real pages on real domains, randomized to treatment/control, published, then measured after recrawl.

- **Timing is set by the retrieval loop, not by you.** Median time-to-first-citation is ~6.8 days, P90 ~37 days. A Tier 2 round is a *two-month* experiment. Design for that from the start.
- **Requires donated inventory.** You need many real pages across many domains. This is the community program: site owners contribute pages under a standard protocol and get their results (plus the aggregate) free.
- **Randomization is what makes it worth doing.** Pair pages within a site by topic and traffic, randomize treatment within pair, so site-level authority differences cancel.

Tier 1 makes the project exist. Tier 2 makes it matter. Ship Tier 1 first.

---

## 3. Query plane: recommendation

You asked to see the tradeoffs. Here they are, and the recommendation.

| | API with search | Browser automation (consumer UI) |
|---|---|---|
| Reproducibility | High — pinned model IDs, logged params | Low — UI changes silently, no version pin |
| Cost / speed | Cents per run, parallelizable | Slow, proxy costs, CAPTCHAs |
| ToS posture | Clean, intended use | Gray at best; scraping consumer UIs breaks most ToS |
| Maintenance | Low | High and unpredictable — the killer for nights-and-weekends |
| Fidelity to real users | **Imperfect and documented as such** | Higher, but not ground truth either (logged-in ≠ logged-out) |

**Recommendation: API-with-search as the primary measurement plane**, for three reasons. It is the only plane where results are reproducible by a third party, it is the only one whose maintenance burden fits your time budget, and it is the only one that stays clean legally as the project gains visibility.

**But make the fidelity gap a first-class measured quantity rather than a disclaimer.** Graphite documented that "responses from APIs, logged-out accounts, and logged-in accounts can vary significantly" and concluded that tracking tools "should not be used as ground truth" — but published no magnitude for that divergence. **Nobody has.**

So the project runs a periodic **Calibration Study**: a smaller prompt set executed on all three planes (API / logged-out UI / logged-in UI), publishing a per-engine divergence coefficient. This is a genuinely novel result, it directly serves the standard's purpose, and it converts your primary weakness into a published contribution. Manual or lightly-assisted collection is acceptable here because n is small and the study runs quarterly.

**Registered engines for v0.1:** OpenAI (search-enabled), Google Gemini (grounded), Anthropic Claude (web search), Perplexity. Note from prior work that these are *not* interchangeable — fanout uniqueness runs 91% on ChatGPT vs 14% on Perplexity, which means ChatGPT needs materially more runs to hit the same precision. And Gemini / AI Overviews / AI Mode behave as three distinct products with a median 8-point visibility gap; never report a single "Google" number.

---

## 4. Metrics

Every metric is defined as an estimator with a stated denominator. **The unit of observation is the run, not the report.**

### Primary

**Citation Presence Rate (CPR).** Proportion of runs in which the target source is cited at all. Binomial; this is the workhorse. Report with a **Wilson score interval**.

### Secondary

**Linked Mention Rate.** Proportion of runs where the mention carries a clickable URL. Kept separate from CPR — after ChatGPT's May 7, 2026 shift to inline branded links, this is the metric with traffic attached (answers with a clickable brand URL went from 4–5% to 22%). Any series spanning that date must be split into two eras.

**Position-Adjusted Prominence.** Inherited in spirit from GEO-bench's position-adjusted word count, but with a **published, justified decay function** rather than an assumed one. GEO-bench borrowed a CTR-style power-law decay from traditional search without validating it for generative answers. Flag as provisional; treat calibrating it as an open research question.

**Rank Stability.** Consistency of ordering across repeated runs. Reported via bootstrap CI. Serves as the audit metric on all the others: if rank is unstable at your sample size, no other number from that sample is trustworthy.

### Deprecated by this standard

A single composite "visibility score." Unreproducible, no denominator, not comparable across vendors. The standard's position: **a number without a denominator, an engine breakdown, and an interval is not a measurement.**

---

## 5. Sampling and statistics

### 5.1 Baseline: estimating a level

For a single (prompt, engine) visibility estimate, prior empirical work supports **10 runs as a floor** (MAE ~5.6%; 98.6% of prompts under 10% MAE) and 40 runs to get 94.9% of prompts under 5% MAE. Report a Wilson 95% interval always.

Be honest about how wide these are. Computed for this spec:

| runs | p̂=0.10 | p̂=0.30 | p̂=0.50 |
|---|---|---|---|
| 10 | 1.8–40.4% | 10.8–60.3% | 23.7–76.3% |
| 20 | 2.8–30.1% | 14.5–51.9% | 29.9–70.1% |
| 30 | 3.5–25.6% | 16.7–47.9% | 33.2–66.8% |
| 100 | 5.5–17.4% | 21.9–39.6% | 40.4–59.6% |

At 10 runs, a 30% visibility estimate is compatible with anything from 11% to 60%. Publishing that table prominently is itself a contribution — it makes the "our dashboard says you're at 34%" claim visibly absurd.

### 5.2 The design that actually matters: detecting a *difference*

Estimating a level and detecting an intervention effect are different problems, and the second needs a different design. Use a **paired design** — same prompt, treated vs. control source — analyzed with prompt as a blocking factor. Pairing removes between-prompt variance, which is the dominant variance component, and is far more efficient than comparing independent groups.

**Analysis:** mixed-effects logistic regression, treatment as fixed effect, random intercept per prompt. For the headline test, a sign-flip permutation test on per-prompt differences — assumption-light and easy for others to reproduce.

**Power.** Simulated for this spec (paired design, per-prompt baseline visibility ~ Beta(1.2, 3), sign-flip permutation test, α=0.05):

| prompts | runs/arm | OR 1.3 | OR 1.5 | OR 2.0 | calls/experiment |
|---|---|---|---|---|---|
| 25 | 20 | 0.35 | 0.68 | 0.99 | 1,000 |
| 50 | 20 | **0.66** | **0.95** | 1.00 | 2,000 |
| 50 | 30 | 0.84 | 1.00 | 1.00 | 3,000 |
| 100 | 20 | 0.91 | 1.00 | 1.00 | 4,000 |
| 100 | 30 | 0.98 | 1.00 | 1.00 | 6,000 |

**Defaults:** *standard tier* 50 prompts × 20 runs/arm (well powered for OR ≥ 1.5); *high-sensitivity tier* 100 prompts × 20 (detects OR 1.3). Anything below 25 prompts is underpowered for realistic effects and should not be published as a finding.

**Pairing is not a stylistic preference — it is most of the power.** Simulated at identical budget (50 prompts × 20 runs, OR 1.5): paired design **0.95** power, unpaired **0.32**. Same number of API calls, three times the sensitivity. Any study in this field that compares treated pages against a *different* set of control pages is throwing away most of its statistical power, and that is worth demonstrating publicly. (Type I error of the permutation test verified at 0.045 under the null; Wilson interval coverage verified at 0.93–0.98 across the grid above.)

The important consequence, which the standard should state explicitly: **more runs of a frozen prompt set beat more prompts run once**, because the variance lives at the run level. And per-prompt claims are almost never supportable — inference is at the corpus level. "Adding statistics raised citation odds ~1.4× across this corpus" is defensible; "adding statistics will get *your page* cited" is not, and the standard should refuse to make that leap.

### 5.3 Pre-registration

Each benchmark round publishes hypotheses, prompt set hash, interventions, primary metric, and analysis plan **before collection**. Cheap to do (a timestamped file in the repo), and it is the single strongest credibility signal against a field where every published number comes from someone selling something. It also protects you from your own garden of forking paths.

---

## 6. Feasibility and cost

Compute cost is not the constraint. Computed for this spec:

- One intervention experiment (50 prompts × 20 runs × 2 arms = 2,000 calls): **$10–$120** depending on model tier.
- A full 9-intervention sweep across 4 engines at standard tier: 72,000 calls, **~$360–$1,440**.

That is a fundable hobby project, and grant- or sponsor-fundable at modest scale. **Your real constraints are wall-clock time and maintenance**, which is exactly why the API plane and the Tier-1-first sequencing matter.

Recurring burden to plan for: engines change under you. Model deprecations, retrieval changes, and product shifts (the May 7 hyperlink change is the archetype) each invalidate comparisons across the boundary. Budget for **re-running the whole suite quarterly** and treat each round as a dated, immutable release rather than a live dashboard. A live dashboard is a maintenance treadmill; a quarterly report is a publication.

---

## 7. Threats to validity

| Threat | Mitigation |
|---|---|
| **Contamination** — corpus leaks into training data, or vendors optimize to the public set | Public + held-out private split. Publish only aggregate results from the private split. Rotate a fraction of prompts each round. |
| **Gaming** — parties tune content to benchmark specifics | Never publish a "score" a brand can chase. Publish intervention effects, not leaderboards of brands. |
| **Engine drift** | Pin model IDs; date-stamp every round; refuse cross-round comparison across a known product change. |
| **Tier 1 over-generalization** | Every Tier 1 result carries a fixed caveat: synthesis stage only, retrieval held constant. |
| **Time-of-day / regional effects** | Randomize collection times across the diurnal cycle; log region; never compare a business-hours sample to a round-the-clock one. |
| **Multiple comparisons** | 9+ interventions × 4 engines is 36 tests. Pre-register the primary; Benjamini–Hochberg on the rest. |
| **Your own incentives** | If the project ever monetizes, the measurement layer and any advisory layer must be separated in public and in fact. |

---

## 8. Provenance record (mandatory per run)

A run without a complete record does not count toward a published number. This schema is the thing other tools would adopt if the standard succeeds — it is arguably the most reusable artifact in the project.

```
run_id, round_id, timestamp_utc, prompt_id, prompt_text_hash,
engine_id, model_id_pinned, api_version, search_enabled,
sampling_params (temperature, top_p, seed_if_any),
auth_state (api | logged_out | logged_in), region, locale,
corpus_version, condition (control | intervention_id),
raw_response_text, extracted_citations[], extracted_mentions[],
extraction_method_version, harness_version
```

Two notes. Store the **raw response**, not just extracted citations — extraction logic will change and you will need to re-derive. And version the **extractor** separately, because a silent change in mention-detection is indistinguishable from an engine change otherwise.

---

## 9. Build sequence for v0.1 (nights and weekends)

Ordered by "what makes the project real," not by what is most fun.

| Phase | Weeks | Output |
|---|---|---|
| **1. Protocol document** | 1–2 | This spec, cleaned up, public in the repo. Citable before any code exists. |
| **2. Tier 1 harness** | 3–5 | Engine adapters (start with 2), provenance logging, Wilson/bootstrap/permutation analysis, one config-driven experiment end to end. |
| **3. Corpus v0.1** | 4–6 | One vertical, 50 prompts, frozen and hashed, with a documented construction method. Pick a vertical you know. |
| **4. Round 1** | 7–8 | Pre-register, run 3–4 interventions from the GEO-bench set against real 2026 engines, publish with intervals — **including the nulls**. |
| **5. Calibration study** | 9–10 | API vs logged-out vs logged-in divergence on a subset. Novel result; likely the piece that gets attention. |
| **6. Tier 2 pilot** | 11+ | Recruit 5–10 site owners, paired randomization, ~8 week clock. |

**The single highest-leverage publication is Round 1 if it fails to replicate Princeton.** "We re-ran the most-cited GEO study against real 2026 engines and here is what held up" is a headline that an entire industry has to read, because they have been quoting those numbers for two years. Design Round 1 as a replication study specifically.

Publish nulls with equal prominence. A standard that only publishes wins is a marketing site.

### License and governance

Code MIT or Apache-2.0. **Data and results CC-BY** — you want vendors citing your numbers, which means making that frictionless while requiring attribution. Governance can stay benevolent-dictator at this stage; a neutral-governance structure only matters if vendors start wanting to influence the corpus, which is a good problem to have later.

---

## 10. Honest assessment of the risks

**The strongest version of the bear case:** Profound has a research team, proprietary data at a scale you cannot approach, and a full-time writer publishing exactly this kind of content. They may simply out-publish you on everything except reproducibility — and the market may not actually value reproducibility, because marketers buy dashboards, not benchmarks.

That bear case is largely right about the *market* and largely wrong about the *niche*. Your defensible ground is narrow and real: you can run controlled experiments and publish the data; they can run controlled experiments and publish conclusions. When those two disagree, only one is checkable. That matters to journalists, to academics, to enterprise buyers doing diligence on vendor claims, and eventually to regulators — none of whom are your users, but all of whom are your distribution.

**The realistic success case is not a company.** It is that OpenGEO becomes the thing people cite when they need a number that isn't from a vendor — the way independent benchmarks function in other domains. That is a reputation asset with real option value (consulting, sponsorship, acquisition, a research role, a later product built on the harness), and it is achievable on nights and weekends in a way that competing with a $1B-valuation company is not.

**Kill criteria — decide these now, while you're unattached to the outcome:** if after two published rounds nobody outside your own network cites or re-runs the benchmark, the standard is not being adopted, and the correct move is to convert the harness into a narrow paid tool or stop. Write that down before Round 1, not after.

---

## Sources

- [GEO: Generative Engine Optimization](https://arxiv.org/abs/2311.09735) — Aggarwal et al., KDD 2024
- [Quantifying Uncertainty in AI Visibility](https://arxiv.org/abs/2603.08924) — Sielinski, March 2026
- [Demystifying Randomness in AI](https://graphite.io/five-percent/demystifying-randomness-in-ai) — Graphite
- [AI Visibility Metrics: Formulas, Benchmarks & Sample Sizes (2026)](https://nicklafferty.com/blog/ai-visibility-metrics-reference/) — Lafferty
- [OneGlanse](https://github.com/aryamantodkar/oneglanse), [gego](https://github.com/AI2HU/gego), [geo-aeo-tracker](https://github.com/danishashko/geo-aeo-tracker) — existing open-source trackers
