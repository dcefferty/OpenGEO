# Roadmap

Where this project is going, and where it has been. The technical spec is
`METHODOLOGY.md`; the findings themselves are on the published page and in
`experiments/results/findings.json`.

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
(`experiments/results/published/2026-08-30-calibration-v1/REPORT.md`). Still open:

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

### 10. Held-out private split — done 2026-09-22
Contamination defence. Publish only aggregate results from the private half; rotate a
fraction of public prompts each round. Protocol in `METHODOLOGY.md` §10.1.

**Structure in place 2026-09-20**, split still empty. `experiments/private/` is gitignored,
`experiments/private/MANIFEST.json` records the split, and `check_private.py` fails the
build if any private prompt_id appears in a tracked file **or in any commit message** — a
question leaks by being mentioned at least as easily as by being committed.

**Correction to an earlier plan.** This item was previously treated as a gate that had to
clear before the repository could go public. That was wrong in one direction and right in
another, and the distinction matters:

- It is **not** a publication blocker. The split's value comes from its questions never
  having been published, which freshly sourced material satisfies whenever it is created.
  Building it after launch costs nothing.
- What **is** irreversible is already done: all 16 item-11 screened questions sit in git
  history across 8 commits. They cannot join the split, because removing them would mean
  rewriting the history that proves when each round was pre-registered — and that evidence
  is the thing this project is actually selling. So the split must be sourced fresh, and
  that cost is now fixed regardless of when it is paid.

**Split v1 built 2026-09-21: twelve questions, screened, format-balanced.** Baseline
placement matches the public corpus closely -- pooled control CPR 0.515, CI
[0.489, 0.541], against v0.4's 0.503, with every question inside [0.25, 0.75]. That
matching is the point: a divergence between halves should be attributable to
contamination rather than to one half being harder. Two prompts per target format across
the six, twelve distinct domains all drawn from v0.4's own twenty-four.

Built in three batches under `METHODOLOGY.md` §9, control arm only. The treatment arm has
never been run against it, because the §5.3 gate is about baseline placement and running
the treatment arm would measure the effect a round exists to report.

The build was also where §9's two new construction rules came from and where the second of
them was confirmed prospectively -- first-pass yield went 0 of 6, to 5 of 6, to 3 of 3 as
they were learned and applied.

*Acceptance:* a private split exists, is excluded from the public corpus, and one round
reports public and private results side by side. **All three met 2026-09-22** — see the
Completed table.

### 11. Make tactics rankable — closed in Tier 1, 2026-09-20
*Closed negative in this design and published as the Tier 1 scope report
(`experiments/results/published/2026-09-20-tier1-scope/REPORT.md`), which is the
"presentation" entry on the findings page. The acceptance below was not met; ranking
presentation tactics moves to Tier 2 (item 9), where retrieval is not held constant. The
history follows.*

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
`experiments/results/probes/2026-09-12-realtext-feasibility.md`.

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
  agency that did not write them. `experiments/corpus/sources.py` snapshots each source
  page and rejects any excerpt that is not a contiguous run of it; the corpus build fails
  on a miss rather than warning.
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

**Confirmed prospectively 2026-09-17.** The three questions batch 4 discarded at 4-5
candidates were re-sourced to 8, 10 and 8 and all three then passed -- the rule was stated
before the retry, not fitted after it. Across ten distinct questions the separation is now
7-10 candidates kept, 4-6 discarded, with no overlap, and the share of the candidate set
cited is what moves: cooking went from 91% of its set cited to 69%, retirement from 85% to
67%. Adding candidates raises citations only slightly (cooking 3.6 to 5.6 per answer), so
the extra documents dilute per-document rates and unpin some of them.

**Half the screened targets are too short to carry a structural tactic (2026-09-19).**
Of the fourteen kept targets, **only seven have three or more sentences**; five are a
single sentence of 16-44 words. Answer-first structure and FAQ blocks are undefined on a
one-sentence document, so the corpus as built cannot express two of the five tactics this
item names. The cause is how the excerpts were sliced: the source pages run 900-3,900
words but are stored as short blocks, and in six of seven cases the excerpt is already the
*entire* host block. Longer targets are available through multi-block spans, still
verbatim, but re-anchoring changes baseline placement and so requires a re-screen
(~$0.15 a question).

Deliberately **not** fixed by lengthening every candidate. Longer excerpts answer more
completely, and a field where every document fully answers is the probe-2 failure mode
that yielded 0 of 10 usable targets. The short-excerpt regime may be *why* screening works
at all. Only the target needs the length, and since every tactic arm is compared against
the control arm of that same target, the target being longer than its competitors does not
confound the tactic contrast -- it only moves the baseline, which the re-screen re-measures.

**Four fact-preserving tactics moved nothing, at three questions (2026-09-19).** The
first test of the *intervention* rather than the corpus: 1,800 calls, 0 errors, four
tactics against a screened control on three questions
(`experiments/results/probes/2026-09-19-tactic-pilot.md`, design committed before
collection). `answer_first` -0.019, `faq` -0.005, `attributed` +0.017, `citation` +0.010;
every Holm-corrected p is 1.000 and the largest odds ratio is 1.05, CI [0.77, 1.43]. The
committed reading for that outcome is **inconclusive -- widen the pilot before sizing the
round**, and that stands.

Post-hoc diagnostics say the null is not an artefact. Per-cell movement is at resampling
noise (mean |delta| over the noise expectation: 0.81 to 1.36, with `attributed` *below*
noise), so unlike H7 there is no directional split cancelling out. Restricting to the nine
cells with real headroom at run time collapses every arm to about 0.00. The variants were
verified distinct as sent, and the metric agrees with the harness on 1,800 of 1,800 runs.

**Screening certifies headroom from one noisy estimate (2026-09-19).** A 24-run rate of
0.21 carries a Wilson interval of about [0.09, 0.41], and by run time **6 of 15 cells
certified as movable sat at or past a boundary** -- claude 0.21 -> 0.04 on two questions.
The gate is weaker than its design assumes. Same error class as raw cross-model Kendall's
W: a quantity measured at finite runs treated as exact. Certify at more runs, or require a
wider margin, before the round.

Together with the sentence-count finding above, the binding constraint on this item is not
statistical power but that the corpus can barely express the tactics: `answer_first` is a
real manipulation on roughly 3 of 14 targets, and those 3 are the pilot. Sequence is
re-anchor to longer spans, re-screen at a wider margin, re-probe -- then source at scale.
If that proves too expensive, the negative result is itself publishable and is the
opposite of what the GEO advice market sells: at the lengths real federal sources come in,
fact-preserving presentation changes do not move citation, and only adding facts does
(H4, +0.48).

**The gradeable middle is an artefact of truncation (2026-09-20).** The decisive probe.
Every document in three already-held-out questions was rebuilt as a 252-345 word page
section instead of a 12-104 word snippet -- closer to what an answer engine actually
synthesises from -- and screened
(`experiments/results/probes/2026-09-20-pagelength-screen.md`, design committed before
collection). **1 of 3 questions kept a usable target, against 3 of 3 as snippets**, which
is the committed SATURATES branch. Unpinned cells went 34% to 31%.

The hypothesised mechanism did not fire: page length was meant to work by making engines
cite fewer documents per answer, and cites per answer held at 4.68 to 4.84. What happened
instead is that the distributions polarised. On blood pressure, four documents sit above
0.78 and four below 0.08 with nothing between; smoke alarm collapsed to 0.93-0.99 across
the board.

A short snippet is a *partial* answer and earns an intermediate rate. A full page either
contains the answer or does not. So the rankable regime -- several documents answering,
citation measuring preference rather than presence -- is a property of how severely the
documents were cut, not of the content. That is worse for this item than a null: measuring
tactics in that regime measures something that does not correspond to how an engine sees a
real page.

Not uniform -- `finance_housingshare` improved (40% to 48% unpinned, 1 to 2 usable
targets) -- and three questions is a probe, so a corpus from richer sources is not
excluded. But the page-length rebuild is not the cheap fix the ladder's deviation implied.

**Where item 11 stands.** Three probes now point the same way: four fact-preserving
tactics at resampling noise, a length ladder whose own mechanism contrast contradicted it,
and a page-length field that saturates. The ranked table is not obtainable in Tier 1 by
either route tested. The result to publish is the scope boundary: at the synthesis stage
with retrieval held constant, what moves citation is whether a document answers the
question (H4, +0.48) -- not how the answer is presented. Presentation tactics belong to
Tier 2 (item 9), because their causal path runs through the retrieval stage this design
holds constant by construction. That is a publishable finding and the opposite of what the
GEO advice market sells.

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
| 1 | Length-matched corpus v0.2 | 12 target pairs within ±3 words; sha `491dad19cb3cd9b0` | `experiments/corpus/build_corpus.py` |
| 2 | Pre-register the pilot | H1–H5, corpus hash, 8 models, 24 runs/cell, analysis plan, stopping rule | `experiments/preregistrations/2026-08-pilot.md` |
| 3 | First real run | 4,608 calls, 0 errors. **H4 null** (+0.001, CI includes zero) — diagnosed as a control-arm ceiling, not a true null. `kimi-k2` excluded for a 34.4% no-cite rate | same pre-registration's deviations |
| 4 | Fidelity metrics (Group C) | `judge_fidelity.py`. A 500-item pilot suggested a large effect; it did **not** replicate at 11,657 items under paired analysis. Confirmed null by two different-vendor judges | `experiments/results/published/2026-08-29-kwstuff-v3/REPORT.md` |
| 5 | Power analysis | `size_round1.py`. Found the spec's own Beta(1.2,3) prior was wrong by ~2.5× in power terms, and that **baseline placement dominates sample size** | `METHODOLOGY.md` §5.2 |
| 5b | Ceiling-fix corpus (v0.3) | Rewrote 12 prompts so controls share no topical surface with the answer. **H4 +0.493, CI [+0.352, +0.641], p=0.0005** | `experiments/results/runs_v0.3.jsonl` |
| 6 | Scale-up (corpus v0.4) | 48 prompts, 18,432 calls. **H4 +0.482, CI [+0.404, +0.563], p<0.0001**, significant for all 8 models. Not pre-registered, so published as exploratory rather than claimed as Round 1 | `experiments/results/published/2026-08-25-corpus-v0.4-exploratory/REPORT.md` |
| 7 | Publish the v0.4 round | Full H1–H5 results including the H3 null, variance decomposition, limitations, reproduction steps | same report |
| 7b | Keyword stuffing (H6) — the citable Round 1 | Pre-registered before collection; took three corpus designs. **H6 falsified: +0.038, CI [+0.004, +0.075], p=0.045.** Stuffing slightly *increases* citation, and Group C shows it does so without lower fidelity | `experiments/preregistrations/2026-08-kwstuff-v3.md`, `experiments/results/published/2026-08-29-kwstuff-v3/REPORT.md` |
| 8 (v1) | Calibration study v1 | **Divergence 0.368, CI [0.139, 0.625].** On 3 of 12 questions the API cited nothing where the logged-out UI cited real sources | `experiments/results/published/2026-08-30-calibration-v1/REPORT.md` |
| 10 | Held-out private split | Twelve questions, screened, format-balanced, never published. Pooled control CPR 0.515 vs the public corpus's 0.503. **H4 replicates on the held-out half: +0.441, CI [+0.324, +0.560]**, and η² for the public/private term is 0.0001 against 0.2795 for the intervention. Banks the pre-publication baseline a contamination test needs | `experiments/preregistrations/2026-09-contamination.md`, `experiments/results/published/2026-09-22-public-private/REPORT.md` |
| 11 | Make tactics rankable (Tier 1) | **Closed negative.** Four fact-preserving presentation tactics pooled +0.001, CI [−0.036, +0.034], at 3 questions — an estimate, not an effect size. The gradeable middle a ranking needs is an artefact of truncated documents, so presentation tactics belong to Tier 2 | `experiments/results/published/2026-09-20-tier1-scope/REPORT.md` |
| 12 | Length-only round (H7) | **H7 not falsified: pooled +0.004, CI [−0.023, +0.031], p=0.73** (share-weighted, 5 engines). But three engines cite padded pages *less*, two significantly after correction, and an **unweighted** pool would have falsified H7 at −0.023, CI [−0.042, −0.005] — the headline turns on a documented weighting parameter | `experiments/results/published/2026-09-11-lengthonly/REPORT.md` |

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
- **An analyser must not average an incomplete cell beside a complete one** (2026-09-20).
  The length-ladder probe lost 129 calls to `HTTP 402 Payment Required` when the account
  balance ran out mid-collection, leaving twelve cells between 5 and 22 runs of 24. The
  analyser averaged them in silently and produced a confident-looking table in which one
  cell carried five times another's weight. Every analyser in the repo had that gap,
  because every round until then had finished with zero errors. `analyze.incomplete_cells`
  is now shared by all four: it reports every short cell and drops those below 80% of a
  full complement, and it is a no-op on every round published so far.
- **A pooled figure can hide a directional split** (item 12). H7's share-weighted pool is a
  clean null while three of five engines point negative; an unweighted pool of the same data
  falsifies it. Per-engine results stay primary, and any pooled headline states its weighting.

---

## Publication checklist

The repository went public on 2026-10-04, on the owner's instruction, once everything
below was done. The site is at https://dcefferty.github.io/OpenGEO/.

Done:

- [x] Licence split so GitHub parses it — `LICENSE` (MIT), `LICENSE-DATA` (CC BY 4.0).
      A single file with both made GitHub report "Other" and show no licence badge, on a
      project whose entire pitch is openness.
- [x] `CITATION.cff` — the audience that matters here (journalists, academics, buyers
      doing vendor diligence) needs something to cite.
- [x] `CONTRIBUTING.md` — reproduction steps, the non-negotiable design rules, and what
      adding a round requires.
- [x] Repository description and topics.
- [x] `.gitignore` pins `experiments/private/` and `.claude/settings.local.json`; the latter
      accumulates literal shell commands from approved tool calls and has held an API key
      inline, protected until now only by a machine-local global ignore.
- [x] Tidy the root for a first-time visitor. Done 2026-10-04: the benchmark's scripts,
      corpora, pre-registrations and results moved into `experiments/` with their layout
      inside unchanged, so commands in earlier reports still work from there (README,
      "Where things moved").
- [x] Commit emails. Done 2026-10-03: the history keeps the addresses its commits were
      made with, because rewriting it would change every commit ID, and the commit dates
      are the evidence of when each round was pre-registered. New commits use the GitHub
      noreply address, signed with a key registered on GitHub, so they show as Verified.

To do **at launch, in one go** — these are coupled and a half-done launch looks worse than
none:

- [x] `python3 check_private.py` — must pass. Once public, a leaked private prompt_id
      cannot be un-leaked.
- [x] Drop "Draft" from both pages: `page.eyebrow`, `page.footer`, `story.eyebrow` and
      `story.footer` in `experiments/results/findings.json`.
- [x] Check that no business name in the skill's eval fixtures
      (`.claude/skills/opengeo/evals/fixtures/`) belongs to a real business; they are
      written as fictional and some make claims about the business. Done 2026-10-01: two
      were renamed for being too close to real plumbing businesses (`em_comp3.html` is now
      Mesquite Hollow Plumbing, `comp4.html` Copperlane Home Notes); the rest returned no
      match.
- [x] `python3 build_findings.py --check` then `build_findings.py`; confirm
      `docs/index.html` (the overview) and `docs/findings.html` are current.
- [x] Make the repository public. Done 2026-10-04, after a last check: tree clean,
      `check_private.py` passing, pages current with the ledger, and no key or token
      pattern anywhere in the history.
- [x] Enable GitHub Pages on `main` / `docs`. Deliberately not enabled earlier: on a
      private repository this is either unavailable or is itself a publication step.
      Done 2026-10-04: https://dcefferty.github.io/OpenGEO/
- [x] Set the homepage URL to the Pages site **after** Pages is live, not before — a
      repository whose homepage 404s is a bad first impression. Done 2026-10-04.
- [x] Decide whether the Tier 1 scope report
      (`experiments/results/published/2026-09-20-tier1-scope/REPORT.md`) gets a
      `findings.json` entry and a place on the page. It is the most contrarian result the
      project has; it is also probe-level, so its ledger entry must not present an effect
      size. Done: it is the "presentation" entry, reported as an interval and labelled as
      not a published effect size.

Not blocking, and deliberately so:

- **Item 10, the private split.** It is not a publication gate — see item 10 for why the
  earlier framing was wrong. The split is sourced fresh whenever it is built.

---

## Explicitly not doing

- A brand-tracking dashboard or per-customer monitoring.
- Recommendations, audits or "fix your site" tooling. Selling the fix destroys the
  credibility of the measurement.
- A composite "visibility score."
- Browser automation as the primary query plane.

### The line between the tool and the fix (clarified 2026-09-26)

`opengeo test` (`design/opengeo-test.md`) lets anyone run a controlled experiment on
their own page. That sits on the permitted side of the line above, and the reason is
worth stating precisely, because the two are easy to confuse.

| | Permitted | Ruled out |
|---|---|---|
| **What it does** | Measures whether *your* change moved citation | Tells you what to change |
| **What it returns** | An effect with an interval, per engine | A score, a grade, or a to-do list |
| **Who decides** | You choose the change; the tool reports what happened | The tool chooses the change |
| **Rigour** | The benchmark's own guardrails, not optional | Whatever produces a clean answer |

The test is whether the output is *a measurement of something the user decided* or *a
recommendation the tool generated*. A measurement is this project's mission applied to
someone else's content. A recommendation turns the benchmark into a product that profits
from its own conclusions, and that is where credibility goes.

Concretely, the tool may say *"your edit raised citation from 38% to 71%, CI +21 to +45,
on this one question"*. It may not say *"add pricing to your page"*. The published
findings can say what the evidence supports and how strongly, because they are the
measurement. The tool just lets people take the same measurement themselves.

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
