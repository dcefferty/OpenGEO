# Roadmap

Where this project is going, and where it has been. The technical spec is
`METHODOLOGY.md`; the findings themselves are on the published page and in
`results/findings.json`.

Open items state an acceptance criterion so they can be picked up cold. Completed items
are kept at their original numbers, because published reports and pre-registrations cite
them by number.

---

## Why this project exists

Two gaps in the field, established by research already done. Do not re-litigate them.

**1. Nothing is reproducible.** Every published GEO benchmark number comes from a
proprietary panel — 27M prompts, 700K conversations, 100.7M runs. Nobody outside those
companies can verify, replicate or re-run any of it, and the vendor publishing the
benchmark is the vendor selling against it.

**2. Almost nothing is causal.** Everything published is observational. The causal
question — *if I change X on my page, does citation go up, by how much, on which engines*
— has been answered publicly about twice: the Princeton GEO paper, and a single Profound
A/B reported as **not statistically significant**. And the Princeton result has a
disqualifying limitation the marketing discourse omits: **GEO-bench never queried a real
generative engine.** It simulated one — Google top-5 retrieval, then GPT-3.5 synthesis.
Its "+41% from adding statistics" describes a 2023 research pipeline, not ChatGPT, and is
now quoted across hundreds of agency posts as settled fact about live engines.

So the project is **the open, reproducible, causal benchmark for GEO**. Statistical
discipline is table stakes adopted from prior work and cited. The contribution is running
real controlled experiments on real engines with open data and an open harness, so the
results can be checked. A funded vendor cannot credibly occupy that position.

---

## Open work

### 8. Calibration study — v1 done, three gaps open
v1 measured API vs logged-out UI for one engine: divergence 0.368, 95% CI [0.139, 0.625]
(`results/published/2026-08-30-calibration-v1/REPORT.md`). Still open:

- **Logged-in UI plane.** Needs real personal accounts; deliberately deferred.
- **More engines.** v1 covered OpenAI only. Perplexity's logged-out UI blocks search behind
  a signup wall, so it cannot be compared this way at all.
- **Plane or model?** The API plane used `gpt-5.4-mini`; the model behind an anonymous
  chatgpt.com session is not confirmed, so part of the gap may be model identity.
- **Temporal replication.** v1 was a single session on a single day.

*Acceptance:* a divergence coefficient per engine, with the model held constant across
planes or the confound stated as a limitation, replicated on at least two dates.

### 9. Tier 2 live-web field experiment
Real pages, randomised within-site pairs, published, measured after recrawl. Budget an
eight-week clock — time-to-first-citation runs ~6.8 days median, 37 days P90. Needs 5–10
donor sites. This is a partnerships problem before it is a code problem.

*Acceptance:* one completed paired round on donated inventory, published with intervals.

### 10. Held-out private split
Contamination defence. Publish only aggregate results from the private half; rotate a
fraction of public prompts each round.

*Acceptance:* a private split exists, is excluded from the public corpus, and one round
reports public and private results side by side.

### 11. Make tactics rankable
**The largest open research item.** The current corpus proves *specific facts beat no
facts*, decisively, on every engine — but its treatment arm sits at CPR 0.9981. Statistics,
attributed quotations, source citations, answer-first structure and FAQ blocks would all
land at 1.000 and be indistinguishable. You cannot rank what you cannot separate.

The regime that would allow ranking already shows up in the existing data: engines cite
2.72 of 6 documents per answer on average, narrowing from 3.17 under control to 2.27 under
treatment. That narrowing is the engine discriminating; the present design gives it nothing
to discriminate between, because only the target answers the question.

The design is a corpus where **all six documents answer**, so citation measures preference
rather than presence, with the target varying by tactic. The hard part is building six
answering documents that do not all saturate — see `METHODOLOGY.md` §9 for the three ways
that has gone wrong so far.

**Feasibility probed 2026-09-12/13, three times.** Real US federal text (public domain,
so no CC-BY-SA conflict) can reach the regime. Full numbers:
`results/probes/2026-09-12-realtext-feasibility.md`.

- **The lever is how many documents ANSWER, not how many candidates there are.** Probe 3
  held candidates at ten and varied only the answering count (5 → 9): the five answering
  documents present in both arms lost 0.142 of citation rate, negative on all five
  engines, while the filler present in both moved by exactly 0.000. Non-answering
  candidates are inert. Dilution bites hardest on mid-range documents, which is the only
  part item 11 can use, making the answering count the knob that places the baseline
  (`METHODOLOGY.md` §5.2).
- **Pick questions whose sources disagree about the form of the answer.** Probe 2's
  sources all say the same thing, so every document was fully responsive or irrelevant —
  0 of 10 usable as a target. Probe 1's disagree on form (% of calories vs grams per meal
  vs teaspoons per 1,000 calories), which creates the graded middle.
- **Screening is mandatory, and more answering documents does not widen the window.**
  Usable targets went 0 of 10 at five answering documents, 2 of 10 at eight, 1 of 10 at
  nine, under a rule requiring three citations and three non-citations from each
  boundary on every engine (first reported as 0/3/2 under a looser cutoff). Inclusive engines (grok 7.6 of 10, deepseek 7.1, gemini 6.9) pin documents near
  1.00; selective ones (gpt 4.1, claude 3.6) pin them near 0.00, and dilution slides a
  document from one pin to the other. A round needs only one target per question, so two
  or three usable of ten is enough — but questions that screen empty must be discarded.
  Budget ~1.5 screened questions per usable one, ~$0.15 each.
- **Every excerpt must pass a mechanical verbatim check.** The probes' excerpts were
  described as verbatim federal text; an audit found 2 of 25 were — the rest had
  authored sentences or edits, one of which changed a claim's meaning. The mechanism
  findings are likely unaffected, but a published corpus cannot attribute words to an
  agency that did not write them. `corpus/sources.py` snapshots each source page and
  rejects any excerpt that is not a contiguous run of it; the corpus build fails on a
  miss rather than warning.
- **Sourcing enough answering documents is the real cost.** A heavily-covered topic
  yielded 9; another yielded 5. Several agency sites block automated fetching.

- **A target may be pinned on at most one engine (decided 2026-09-14).** Screened on
  verbatim federal text, requiring every engine discarded both questions. The engines
  differ too much in how much they cite: on the housing question grok cited 80% of
  candidates and claude 41%, and a document must sit mid-range on all five at once. In
  each question, removing one engine's requirement produced a target. That is a property
  of the engines, not of real text, so a synthetic corpus would face it too. The repo
  owner chose to keep all five engines and let a question leave one out, reporting that
  engine's result there as uninformative, over dropping grok from the panel. A target
  movable on every engine is always preferred; ties go to the smallest market weight
  excluded. **Watch:** both questions kept so far exclude grok, and the tie-break leans
  that way. Per-engine question counts are printed by `screen.py`, and the pre-registration
  must set a floor on them.
*An earlier round of this note said "use ten candidates"; probe 2 falsified that and probe
3 replaced it with the answering-count mechanism. Recorded because acting on the first
probe alone would have sent the corpus work down the wrong path.*

**Source at least 8 on-topic candidates per question (2026-09-17).** Across ten screened
questions, candidate count separates the outcome perfectly and the number of directly
answering documents does not:

| | candidates | directly answering |
|---|---|---|
| kept (5) | 7-9 | 2-5 |
| discarded (5) | 4-6 | 2-5 |

Engines cite a fairly sticky number of documents -- 3.2 to 5.7 per answer here -- so with
four or five candidates that is 64-91% of the entire set and every document pins near a
ceiling. With seven to nine it is 42-80%, which leaves some documents mid-range. This
refines the probes' finding that non-answering candidates are inert: probe 3's filler was
*off-topic* and was never cited, but on-topic partial answerers are cited at 0.24-0.85 and
do compete for citation slots. Caveat: richer topics got more sourcing effort, so candidate
count is confounded with topic richness at n=10; the share-of-set figures are the part that
does not depend on that.

Practically, a thin candidate set fails however well its sources disagree, and the three
questions discarded in batch 4 (cooking temperature, Social Security claiming age, vitamin
D) are under-sourced rather than unusable -- each had 4-5 candidates and can be retried at 8+.

**Sized 2026-09-15 against the screened baselines, not an inherited number.** The five
kept targets sit at 0.354-0.642 (mean 0.498) with no cell at a ceiling, which is what
screening is for -- the v0.2 pilot's baseline was 0.87 with 67% of cells pinned. Power to
detect a tactic against baseline, at 24 runs per arm (`size_round1.py` on those baselines):

| smallest effect | 25 questions | 50 questions | 50 questions, 40 runs |
|---|---|---|---|
| OR 1.30 (~+6.5 pts) | 0.95 | 1.00 | 1.00 |
| OR 1.20 (~+4.5 pts) | 0.71 | 0.95 | 0.99 |
| OR 1.15 (~+3.5 pts) | 0.51 | 0.81 | 0.94 |

So the question count follows from the smallest tactic worth ranking. H6's keyword-stuffing
effect was +0.038, about OR 1.15, where 25 questions is a coin flip. **Plan on ~50 questions
if tactics are expected to differ by a few points; 25 only suffices if they differ by 6 or
more.** Separating tactics from each other is harder still than separating one from
baseline, which this table does not cover.

*Acceptance:* a question whose authoritative sources differ in framing, an answering-document
count tuned so the target sits mid-range, and a target movable on all but at most one
engine — confirmed by a pre-committed screening run — followed by a pre-registered round
producing a ranked table with intervals, each engine's ranking stating how many questions
it rests on.

---

## Completed

| # | Item | Outcome | Records |
|---|---|---|---|
| 1 | Length-matched corpus v0.2 | 12 target pairs within ±3 words; sha `491dad19cb3cd9b0` | `corpus/build_corpus.py` |
| 2 | Pre-register the pilot | H1–H5, corpus hash, 8 models, 24 runs/cell, analysis plan, stopping rule | `preregistrations/2026-08-pilot.md` |
| 3 | First real run | 4,608 calls, 0 errors. **H4 null** (+0.001, CI includes zero) — diagnosed as a control-arm ceiling, not a true null. `kimi-k2` excluded for a 34.4% no-cite rate | same pre-registration's deviations |
| 4 | Fidelity metrics (Group C) | `judge_fidelity.py`. A 500-item pilot suggested a large effect; it did **not** replicate at 11,657 items under paired analysis. Confirmed null by two different-vendor judges | `results/published/2026-08-29-kwstuff-v3/REPORT.md` |
| 5 | Power analysis | `size_round1.py`. Found the spec's own Beta(1.2,3) prior was wrong by ~2.5× in power terms, and that **baseline placement dominates sample size** | `METHODOLOGY.md` §5.2 |
| 5b | Ceiling-fix corpus (v0.3) | Rewrote 12 prompts so controls share no topical surface with the answer. **H4 +0.493, CI [+0.352, +0.641], p=0.0005** | `results/runs_v0.3.jsonl` |
| 6 | Scale-up (corpus v0.4) | 48 prompts, 18,432 calls. **H4 +0.482, CI [+0.404, +0.563], p<0.0001**, significant for all 8 models. Not pre-registered, so published as exploratory rather than claimed as Round 1 | `results/published/2026-08-25-corpus-v0.4-exploratory/REPORT.md` |
| 7 | Publish the v0.4 round | Full H1–H5 results including the H3 null, variance decomposition, limitations, reproduction steps | same report |
| 7b | Keyword stuffing (H6) — the citable Round 1 | Pre-registered before collection; took three corpus designs. **H6 falsified: +0.038, CI [+0.004, +0.075], p=0.045.** Stuffing slightly *increases* citation, and Group C shows it does so without lower fidelity | `preregistrations/2026-08-kwstuff-v3.md`, `results/published/2026-08-29-kwstuff-v3/REPORT.md` |
| 8 (v1) | Calibration study v1 | **Divergence 0.368, CI [0.139, 0.625].** On 3 of 12 questions the API cited nothing where the logged-out UI cited real sources | `results/published/2026-08-30-calibration-v1/REPORT.md` |
| 12 | Length-only round (H7) | **H7 not falsified: pooled +0.004, CI [−0.024, +0.030], p=0.73** (share-weighted, 5 engines). But three engines cite padded pages *less*, two significantly after correction, and an **unweighted** pool would have falsified H7 at −0.023, CI [−0.042, −0.005] — the headline turns on a documented weighting parameter | `results/published/2026-09-11-lengthonly/REPORT.md` |

Two notes for anyone following a citation into this file:

- Reports pointing at **items 5b and 6** for the corpus failure-mode diagnosis will find
  that material, in full and generalised, in `METHODOLOGY.md` §9.
- The per-round narrative that used to live in `CLAUDE.md` under "Current state" is the
  table above plus the linked records.

---

## What the failures changed

Three protocol rules exist because a round went wrong first. All three are now in the
standard rather than in anyone's memory:

- **A pre-committed spot check before every full round** (`METHODOLOGY.md` §5.3). Two
  keyword-stuffing corpora reused "already-validated" text on the assumption it would
  behave the same way in a new experiment. It did not, both times.
- **A gate must be stated against the same prompts it will be checked on** (§5.3). The
  length-only gate was written against a 48-prompt pooled figure and evaluated on six
  prompts; it failed on arithmetic, not on the corpus.
- **Baseline placement over sample size** (§5.2, §9). Ceiling avoidance is free; more calls
  are not.
- **A pooled figure can hide a directional split** (item 12). H7's share-weighted pool is a
  clean null while three of five engines point negative; an unweighted pool of the same data
  falsifies it. Per-engine results stay primary, and any pooled headline states its weighting.

---

## Explicitly not doing

- A brand-tracking dashboard or per-customer monitoring.
- Recommendations, audits or "fix your site" tooling. Selling the fix destroys the
  credibility of the measurement.
- A composite "visibility score."
- Browser automation as the primary query plane.

---

## The bear case

The strongest version: Profound has a research team, proprietary data at a scale this
project cannot approach, and a full-time writer publishing exactly this kind of content.
They may out-publish it on everything except reproducibility — and the market may not value
reproducibility, because marketers buy dashboards, not benchmarks.

That is largely right about the *market* and largely wrong about the *niche*. The
defensible ground is narrow and real: this project can run controlled experiments and
publish the data; they can run controlled experiments and publish conclusions. When those
disagree, only one is checkable. That matters to journalists, academics, enterprise buyers
doing vendor diligence, and eventually regulators — none of whom are users, all of whom are
distribution.

The realistic success case is not a company. It is that OpenGEO becomes the thing people
cite when they need a number that isn't from a vendor.

---

## Kill criteria

Decided in advance, while unattached to the outcome: **if after two published rounds nobody
outside the author's own network cites or re-runs the benchmark**, the standard is not being
adopted. Convert the harness into a narrow paid tool, or stop. Revisit this honestly rather
than moving the goalposts.
