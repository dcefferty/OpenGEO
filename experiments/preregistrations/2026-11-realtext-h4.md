# OpenGEO Real-Text H4 Replication Pre-Registration — v1 — 2026-11

Committed before any row is written to a results file for any corpus named here. Per
`preregistrations/README.md`, the git timestamp on this file is the evidence.

**This file is committed before screening, one step earlier than the design note's
sequence** (`results/probes/2026-09-23-realtext-h4-design.md`, "Sequence", which put
pre-registration after screening). Committing first means the screen itself, and the rule
for which questions enter the round, are fixed before any data exists. The one thing that
cannot be fixed yet is the round corpus's hash, because it depends on which questions pass
the screen. It is recorded by a dated entry under **Deviations** that names the kept
questions and the hash, committed **before any treatment-arm call**. The batch corpora's
hashes, which carry both arms, are recorded here now.

## Why this round

Of the public findings, most rest on synthetic documents this project wrote. The one built
on verbatim real text, the Tier 1 scope probe, is a null, and it tested presentation
tactics, a different hypothesis. A reader will notice that the headline result, **H4**
(stating the specific answer raises citation: +0.482 on v0.3, +0.493 on v0.4), has never
been measured on a page nobody associated with the project wrote.

This round replicates H4 on **verbatim US federal text**. In each question, the target's
control arm is a real page span that is topically adjacent to the question but answers none
of it, and the treatment arm is the same span with one sentence replaced by an authored
sentence stating the answer. That is the edit a practitioner makes. Every figure in the
inserted sentence is taken from a named federal page, and the build checks it.

## Design

| | |
|---|---|
| Built by | `corpus/build_corpus_realtext_h4.py` |
| Batch 1 corpus | `corpus/corpus_realtext_h4_b1.json`, version `realtext-h4-screen-b1`, sha `0011a90d43066fc1` |
| Round corpus | `corpus/corpus_realtext_h4.json`, version `realtext-h4-v1`; sha recorded under Deviations before any treatment call |
| Questions | 25 for the round (the `METHODOLOGY.md` §5.2 floor), from batches of 6 |
| Documents | 6 per question, 50–110 words, each a verbatim span of a different federal page; only the target varies |
| Conditions | 2 — `control`, `treatment` |
| Models | the five-engine panel in `engine_weights.py`: `openai/gpt-5.4-mini`, `google/gemini-3-flash-preview`, `anthropic/claude-haiku-4.5`, `deepseek/deepseek-chat`, `x-ai/grok-4.3` |
| Runs per cell | 24 |
| Temperature | 1.0 |
| Document order | randomized per run from a seeded hash, recorded every run |
| Screening calls | 6 questions × 1 arm × 5 engines × 24 = **720 per batch**, about $0.72 (the trust spot check's measured $0.72 for 720) |
| Round calls | 25 × 2 × 5 × 24 = **6,000**, about $6; more if the last batch overshoots 25 (see Stopping rule) |

### How each question is built

| part | rule |
|---|---|
| target, `control` | a verbatim span of a real page, **one dimension away** from the question (§9): the same subject, a different attribute of it |
| target, `treatment` | the same span with **exactly one** of its sentences replaced by one authored sentence stating the answer, within ±3 words of the control's length (§9) |
| figures | every number in the inserted sentence must appear in a quoted passage of a named federal page, and that passage must be verbatim in its committed snapshot |
| five non-targets | verbatim spans of five further pages, byte-identical across arms; one or two clearly tangential (§9's cites-per-answer note) |
| no answer | a per-question answer pattern, deliberately broader than the answer (any retention period, any password length, any caffeine quantity), must match nothing in the control arm and must match the treatment target |

The build refuses to write a corpus unless every one of those checks passes, plus: every
span is sliced from its snapshot by anchors and passes `sources.verbatim`; no span
contains a bracketed reference marker; no two documents of a question share a page.

**Formats are not balanced.** v0.4 gives each question one document per format. Federal
agencies publish no product listings or forum threads, so this round uses the registers
the pages are (reference, docs, news, blog) and **cannot speak to H5**. That was settled in
the design note's amendment 1.

**All documents come from the committed snapshots** under `corpus/sources/`. The design
note's first sourcing pass lost nine of twenty URLs to agency blocks and an Internet Archive
outage, and the environment that built this corpus could reach no federal site at all.
Questions were chosen to fit pages already held, from the parts of those pages that do not
answer them. Later batches may add snapshots with `sources.py fetch`; the same checks apply.

### Batch 1, fixed here

Chosen before any data. One question per domain, domains from v0.4's twenty-four.

| question | target (control is a verbatim span of) | inserted sentence | figures from |
|---|---|---|---|
| `taxes_employment_records` How long does a small business with employees have to keep its employment tax records? | IRS, Recordkeeping (why records matter, which system to use) | "Employers must keep all employment tax records for at least 4 years after the tax becomes due or is paid." | IRS Topic 305 |
| `cyber_password_length` How many characters long should a password be, according to NIST's current guidance? | CISA, Choosing and Protecting Passwords (do not reuse passwords) | "NIST guidance recommends that a password should be at least 15 characters long, and never reused." | NIST, How do I create a good password? |
| `nutrition_caffeine_limit` How much caffeine a day is generally safe for healthy adults? | FDA, Spilling the Beans (how caffeine is labelled) | "For most adults, the FDA cites 400 milligrams a day, about two to three cups of coffee, as not generally associated with negative effects." | the same FDA page |
| `cooking_leftovers_room_temp` How long can cooked food be left out at room temperature before it should be thrown away? | USDA FSIS, How Temperatures Affect Food (refrigerator storage) | "Cooked food left out more than 2 hours, or 1 hour above 90 °F, should be discarded." | USDA FSIS, Grilling Food Safely |
| `home_radon_action_level` At what radon level does the EPA recommend fixing your home? | EPA RadTown, Radon in Homes, Schools and Buildings (where radon comes from) | "The EPA recommends fixing a home if its radon level is 4 pCi/L or more." | EPA, What is EPA's Action Level for Radon |
| `finance_emergency_400` What share of U.S. adults could cover an unexpected $400 expense using cash or its equivalent? | CFPB, An essential guide to building an emergency fund (why have one) | "Faced with a $400 emergency expense, 63 percent of adults would cover it with cash or its equivalent." | Federal Reserve, Economic Well-Being of U.S. Households in 2025 |

The full text of every document, the replaced sentence, and each figure passage are in the
builder and the batch corpus.

## Screening

Each batch runs **the `control` arm only**, on the five engines at 24 runs per cell:

```
python3 corpus/build_corpus_realtext_h4.py
python3 run_pilot.py --corpus corpus/corpus_realtext_h4_b1.json \
  --out results/screen_realtext_h4_b1.jsonl --runs 24 --conditions control \
  --models openai/gpt-5.4-mini google/gemini-3-flash-preview anthropic/claude-haiku-4.5 \
           deepseek/deepseek-chat x-ai/grok-4.3
python3 screen_realtext_h4.py --corpus corpus/corpus_realtext_h4_b1.json \
  --runs results/screen_realtext_h4_b1.jsonl
```

**Gate.** A question is **KEPT** if its target's control CPR, pooled **unweighted** across
the five engines, lies in **[0.25, 0.75]** (§9's bar, as the design note set it). Otherwise
it is **DISCARDED**.

- **No re-tuning.** A discarded question is not edited and re-screened. A replacement is a
  new question in a later batch, built from scratch (§9: a second pass fits the first
  pass's noise).
- **The treatment arm is never run during screening.** `screen_realtext_h4.py` refuses a
  runs file containing any treatment row.
- **Per-engine rates and cites per answer are printed but are not part of the gate.** An
  engine pinned at a boundary on a kept question will report a bound there, under the
  boundary rule below.
- **Screening data is archived and never pooled into the round.** The round re-measures
  the control arm from scratch. Reusing screening runs would carry the selection on
  control CPR into the estimate, which then regresses toward the mean.
- After each batch, the kept questions are appended to `KEPT` in the builder by a dated
  commit that cites the screen output, and logged under Deviations.

**The screen stands in for the spot check** (`METHODOLOGY.md` §5.3). It runs after this
file is committed, before the round, on the control arm only, and it measures the baseline
of every question the round will contain, not a subset. No separate spot check is run.
The round's only other gate is data health: no engine above 10% no-cite in the screen.

## Stopping rule

- **Screening** stops when **25 questions are kept**, or after **8 batches** (48 questions
  screened, about $5.80), whichever comes first.
- **The round contains every kept question.** If the batch that crosses 25 keeps more than
  needed, all of them go in, so no kept question is dropped by choice. The round then has
  25 to 30 questions and its call count scales accordingly.
- **If fewer than 25 are kept after 8 batches**, the round does not run as a finding.
  - With **12 or more** kept (the design note's interim milestone), it may run as a
    sub-floor estimate, reported as an interval and not a published effect size
    (`CLAUDE.md`, "Scope honesty"). That decision is the repo owner's, logged under
    Deviations before any treatment call.
  - With **fewer than 12**, the round does not run, and the screening yield is published as
    the result: real federal text at this length could not place a control mid-range often
    enough, which would mean the synthetic corpora are load-bearing for H4, not decorative.
- **One round.** No interim analysis, no adding models, questions or arms after seeing
  treatment data. A round that fails on data health is rerun in full and the failed attempt
  archived, not merged.

## Hypotheses

**H4-RT (primary). Stating the answer raises citation on real text.**

> A verbatim federal page span is cited more often when one of its sentences is replaced by
> a sentence stating the answer to the question.

Contrast `treatment − control`, predicted **positive**.

**Decision rule.** SUPPORTED only if the share-weighted pooled delta's 95% bootstrap CI
excludes zero on the positive side **and** its sign-flip permutation p is below 0.05.
Otherwise FALSIFIED, with the interval reported. A CI excluding zero below it is reported
as falsified in the opposite direction.

**What a positive result does and does not show.** v0.3 and v0.4 found the treatment arm
saturating, which makes the delta mechanically `1 − control`: a statement about where the
control sits, which the screen selects. A positive H4-RT shows that the construction is
achievable on text nobody here wrote, and that one inserted sentence is enough to move a
real page. It does not identify the effect's true size. The write-up therefore reports the
**control baseline as the quantity of interest alongside the delta**, compares both to
v0.3/v0.4 descriptively only (different questions, different documents), and, if most
treatment cells saturate, calls the delta a floor (§9).

### Secondary

- **H4-RT-b, displacement.** Mean CPR of the five unchanged documents, `treatment −
  control`. **Two-sided.** On an earlier corpus engines cited fewer documents when
  the target answered (3.17 → 2.27 cites per answer, `ROADMAP.md` item 11); this asks whether real neighbours lose
  citation when the target gains it.

### Descriptive, not tested

- Target CPR and cites per answer by arm.
- **Answer echo:** the share of answers matching each question's answer pattern, by arm,
  read mechanically with no model judge. No control-arm document matches, so the control
  column is the rate at which engines state the answer from their own knowledge. It is
  reported per question because some answers here (400 mg of caffeine, the 2-hour rule) are
  widely known and others (63 percent) are not.

## Analysis plan

Executed by `analyze_realtext_h4.py --runs results/runs_realtext_h4.jsonl`.

- **Primary metric:** target CPR (`METHODOLOGY.md` A1).
- **Pairing:** per (prompt, model). Deltas are taken within each cell, weighted across
  models within a prompt, and prompts are the resampling unit.
- **Inference:** bootstrap over prompts, 10,000 resamples, 95% percentile CIs; sign-flip
  permutation test on the per-prompt deltas, 20,000 permutations. No scipy.
- **Pooling:** share-weighted by `engine_weights.py` for the decision (ChatGPT 0.559,
  Gemini 0.284, Claude 0.094, DeepSeek 0.037, Grok 0.026), unweighted printed beside it.
  **Per-engine results are primary**, with Holm across the five engines.
- **Boundary rule:** an engine whose pooled control CPR is within 0.02 of 0 or 1 reports
  its delta as a bound, not an estimate (§9).
- **Model exclusion:** standing rule. Any model above 10% no-cite is excluded from pooled
  figures and reported separately.
- **No question exclusions** once the round corpus is fixed.

### Verified before collection

`make_mock_realtext_h4.py` plants a known effect on the batch 1 corpus. On seed 42 the
analyser recovers H4-RT **+0.324 [+0.212, +0.414]** against a planted **+0.364**, and
H4-RT-b **−0.146 [−0.181, −0.115]** against a planted **−0.146**. Over 20 seeds, **20 of
20** H4-RT intervals contain the planted value. Under a planted null, **2 of 100** mock
rounds returned SUPPORTED, against a one-sided nominal 2.5%. In control-only mode the mock
plants two questions outside the gate, and the screen discards exactly those two.

Each mock has six questions, so these checks exercise the code, not the round's power.

### Power, stated honestly

H4 has been +0.48 to +0.49 on synthetic text. If real text lands anywhere near that, 25
questions detect it easily. The risk to this round is not power but **yield**: whether
enough real spans sit mid-range. The page-length screen kept one target in three
(`results/probes/2026-09-20-pagelength-screen.md`), and §9's rules placed five of six on a
synthetic corpus. Eight batches allow for a yield as low as about one in two.

## Reporting

Published under `results/published/` whatever the outcome: a supported H4-RT, a null, or a
screen that could not fill the round. The headline is the delta beside both arm means and
the control baseline, with its per-engine breakdown and the screening yield (questions
screened, kept, discarded).

Every sentence carries the Tier 1 caveat: synthesis stage only, retrieval held constant.

## Limitations known in advance

- **Retrieval is held constant.** The round says nothing about whether the edited page
  would be retrieved.
- **The treatment sentence is authored.** Only the control arm is verbatim. Its figures are
  real and sourced, but the sentence carrying them is ours, and the document is declared as
  edited.
- **Questions were chosen to fit pages already held.** They are not a random sample of
  questions, and a question whose spans all answer it could not be built.
- **The screen selects on control CPR.** Kept questions are, by construction, ones where
  the control sits mid-range. The round re-measures the control fresh for that reason, but
  the population it generalizes to is "real pages that sit mid-range", which is what H4 has
  always been measured on.
- **No format balance**, so no H5, and format is nested within question.
- **Federal text only.** Government pages may read as more authoritative to an engine than
  commercial ones, which could raise the control baseline relative to v0.4.
- **Some answers are common knowledge.** An engine may answer from memory without citing;
  the echo reading measures how often.

## Deviations

Logged here with a timestamp before analysis, not made silently.

**2026-11-08 — batch 1 screened: 2 of 6 kept; the screen's data-health condition fails as
written, and is put to the repo owner.**

Ran the batch 1 screen exactly as specified under Screening, after this file was merged
(PR #39): `corpus_realtext_h4_b1.json` rebuilt at sha `0011a90d43066fc1`, `control` only,
the five panel engines, 24 runs per cell = **720 calls, 0 errors, 0 `model_returned`
mismatches** (`results/screen_realtext_h4_b1.jsonl`). Logged spend $0.75. No treatment
row exists.

| question | pooled control CPR | claude | deepseek | gemini | gpt | grok | decision |
|---|---|---|---|---|---|---|---|
| `taxes_employment_records` | 0.775 | 0.08 | 1.00 | 0.96 | 0.83 | 1.00 | DISCARD |
| `cyber_password_length` | 0.742 | 0.54 | 0.62 | 1.00 | 0.92 | 0.62 | **KEEP** |
| `nutrition_caffeine_limit` | 0.783 | 0.08 | 0.83 | 1.00 | 1.00 | 1.00 | DISCARD |
| `cooking_leftovers_room_temp` | 0.767 | 0.29 | 0.58 | 1.00 | 1.00 | 0.96 | DISCARD |
| `home_radon_action_level` | 0.942 | 1.00 | 0.96 | 1.00 | 0.75 | 1.00 | DISCARD |
| `finance_emergency_400` | 0.750 | 0.46 | 0.38 | 1.00 | 0.92 | 1.00 | **KEEP** |

`cyber_password_length` and `finance_emergency_400` are appended to `KEPT`. Both sit at the
top edge of the gate and both are pinned at 1.00 on Gemini, so under the boundary rule
Gemini will report a bound on them. The gate is applied as written; per-engine pinning is
not part of it.

**What batch 1 says about the design.** All six controls landed at or above 0.74, and
four failed at the **ceiling**, none at the floor. Gemini cited the target in at least 23 of
24 runs on every question. Real federal spans placed one dimension away (§9) sit higher
than v0.4's authored controls did; the limitation that federal pages may read as more
authoritative is the likely reason. At this yield, eight batches keep about 16 questions,
short of 25. Later batches are built from scratch under the same checks, so their targets
may be placed further from the question; that is a construction choice for new questions,
not a re-tune of discarded ones.

**The data-health condition.** Screening says the round's only other gate is "no engine
above 10% no-cite in the screen". In this screen, no-cite was **26.4%** on
`anthropic/claude-haiku-4.5` (38 of 144), **24.3%** on `deepseek/deepseek-chat` (35 of
144) and 4.9% on `openai/gpt-5.4-mini`. The no-cite answers read "I cannot answer this
question based on the provided sources": the correct response when, by construction, no
document answers. The 10% rule comes from the analysis plan, where it applies to a round's
data across both arms; transplanting it to a control-only screen of non-answering documents
was a drafting error in this file, made before any data. It is logged here rather than
corrected. Whether the condition stands as written (no round can run with this panel), or
is read as the analysis plan's both-arm rule applied to the round itself, is the repo
owner's decision. It will be logged below, dated, before any treatment call.
