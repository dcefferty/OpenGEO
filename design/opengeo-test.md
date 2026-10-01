# `opengeo test` — design

Settled 2026-09-26, before any of it is built, so the defaults are chosen on purpose rather
than drifting during implementation. Anything here that changes later is changed in this
file, dated, with the reason.

## What it is

A command that answers one question for anyone: **did my change to my page make AI engines
more likely to cite it, against my actual competitors?** It runs a paired, controlled
experiment — the same design as every round this project has published — on the user's own
content, and reports the effect with an interval, per engine.

It is a measurement, not advice. It never tells anyone what to change. The line between the
two is set out in `ROADMAP.md`, under "Explicitly not doing".

## The principle: rigour in the defaults, ease in the interface

The people using this are technical and hands-on, and they will check the method. They also
should not need to have read `METHODOLOGY.md` to get a correct answer. So:

- **Every guardrail runs automatically.** Nobody has to know it exists to benefit from it.
- **The rigorous path is the easy path.** The default settings are the correct settings, and
  the ones with no evidence for relaxing them cannot be changed at all.
- **Everything is inspectable.** The plain verdict and the full technical record come out of
  the same run. Anyone can check what happened; nobody has to.

## Interface

```
python3 opengeo.py test \
    --question "How much does a home energy audit cost?" \
    --page     https://mysite.com/energy-audit      # URL or local file: the page as it is now
    --edit     ./energy-audit-v2.md                  # local file: the page with your change
    --against  https://competitor-a.com/audits \     # 2+ competitor pages, 5 recommended
               https://competitor-b.com/pricing
```

`--question` may be repeated. Three to five questions a customer would actually ask is the
recommendation printed on every single-question run, because one question is not enough to
generalise from (see "Honesty in the output").

Also: `--dry-run` (cost and checks only, no calls) and `--yes` (skip the cost confirmation).

The Claude skill is a thin layer over this command. It gathers the same four inputs in
conversation, shows the cost, runs it and explains the result. It never adds a
recommendation the command would not make.

## Defaults, and the evidence behind each

Every default traces to a published result or to a round that went wrong. That is what
"backed by evidence" means for a tool: not that its output is right, but that each of its
choices can be checked.

| Default | Value | Evidence |
|---|---|---|
| Runs per version | **24, fixed** | Detecting a *difference* is what this tool does, and the split-half reliability of a difference is 0.21 at 10 runs and 0.75 at 24 — measured by **simulation** on data with a planted effect, the basis of the 24-run rule in `CLAUDE.md`. On real runs the citation rate itself is reliable at 24, Spearman-Brown 0.92–0.96 on every model (`results/published/2026-08-29-kwstuff-v3/REPORT.md`) |
| Temperature | **1.0, fixed** | Measures the answers a real user sees; lowering it measures a different, more stable system |
| Document order | **Random per run, seeded** | Position affects citation enough that the position-sensitivity index is estimable; a fixed order would bias every result |
| Design | **Paired**: only your page changes between versions | About 3× the statistical power of an unpaired comparison at identical cost (0.95 vs 0.32) |
| Engines | **The five-engine market panel**, fixed | Chosen and weighted by measured market share, 98.9% of assistant traffic (`engine_weights.py`) |
| Length of your edit | **Within ±3 words**, blocks by default | §9. Relaxable with `--allow-length-change` — see below |
| Your current page | **Must not already be cited almost always** | §9's ceiling rule, which records three distinct ways a baseline ends up at the ceiling, each found only by testing against real models |
| Your edited page | **Flagged at the ceiling if cited every time** | Public/private round: a saturated arm caps what any scale can express (§9). The output says the edit got the page cited every time against these competitors, and that it can't show how the edit would do against stronger ones (changed in 0.2.0) |
| Competitors | **2 required, 5 recommended** | Every published round used a field of 5. ROADMAP item 11: engines cite 3.2–5.7 documents per answer, so in a small field nearly everything is cited and the current page leaves no room (5 since 0.2.0) |
| Engines that cite nothing | **Excluded only if they fail on answering documents too** | Public/private round: the pooled rule dropped an engine that was abstaining correctly (§3) |
| Interrupted runs | **Resumed, never analysed short** | Length-ladder round: a mid-run credit failure left cells at 5 of 24 runs (`analyze.incomplete_cells`) |
| Document length | **The 50–110 word section most relevant to the question** | The regime every published effect was measured in; full pages behave differently (page-length screen) |

## Three kinds of guardrail

**Fixed** — no flag exists. Runs per version, temperature, random order, the engine panel.
There is no evidence that relaxing any of them leaves the result unbiased, and a cheaper,
noisier answer that looks identical to a correct one is worse than no answer. At roughly
$0.30 per question, cost is not a reason to cut any of them.

**Blocking, relaxable with evidence** — one case: edit length. The ±3-word rule exists so an
effect cannot be word count in disguise. But H7 measured padding a page to double its length
at **+0.004, CI [−0.023, +0.031]**: length alone does not move citation. Most real edits add
content rather than swapping it, so a strict rule would reject the edits people actually
make. `--allow-length-change` permits it, and the report states the length difference and
cites H7 as the reason it is not a confound. The flag is named for what it does and its use
is recorded in the output — a documented deviation, like the ones this project logs in its
own pre-registrations, not a silent setting.

**Warning** — the run proceeds and the report says what it means. An edited page cited
every time (a ceiling), fewer than five competitors (less competition than every published
round had), an edit that also changes the page's title, a single question.

Two further blocks are input errors rather than guardrails, so no flag relaxes them: a
Python without numpy, which the analysis needs after every call has been paid for, and a
page title on only one of the two versions (0.2.0).

## Three design decisions

**Competitors come from the user.** A paired test needs other documents for the page to
compete against. The user supplies them because it is the more useful question — not "does
my edit help in general" but "does it help against the people I compete with" — and they
already know who those are. Discovering competitors automatically from search results was
rejected: it adds a live-web dependency, so the same command would give a different answer
next week for reasons unrelated to the edit.

**The tested section of your page is found from your edit.** The tool compares `--page` and
`--edit`, locates the region that changed, and takes the 50–110 word section around it from
each. So the control is exactly the text you had and the treatment is exactly the text you
propose, and nothing else on your page is part of the test. For each competitor it takes the
section most relevant to the question, which is what a retrieval step would plausibly hand
an engine. If that makes the competitors decisively better answers than your page, the
ceiling check reports it — which is itself useful to know.

**Every page is shown with its title** (0.2.0). A search result or a retrieved passage
travels with its page's title, and the title is usually where a page says who it is and
where — the business name, the city. An excerpt chosen around an edit can easily miss the
heading, and before 0.2.0 an engine asked about water heaters in Tucson could not see that
the user's page was a Tucson plumber's. Each document is now its page's `<title>` (or first
`<h1>` when there is none) on one line, then its excerpt. It applies to every page alike, so
it is identical between the two versions unless the edit itself changes the title. The
published rounds' documents had no titles, so a corpus built from them is unchanged.

## Output

On the terminal: a one-line verdict, the effect with its interval, a per-engine chart, and
the caveats written as advice.

In `./opengeo-results/<date>-<slug>/`:

| File | Contents |
|---|---|
| `report.md` | The result in the same format as this project's published rounds |
| `chart.svg` | Per-engine before and after, with intervals |
| `runs.jsonl` | Every raw model response |
| `corpus.json` | The exact text of every document tested, hashed |
| `manifest.json` | Tool version, model identifiers as returned, settings, flags used |

With `corpus.json` and `manifest.json`, anyone can re-run the identical test later — which
is how a user checks whether a result still holds after the engines change.

## Honesty in the output

Two statements appear on every result, in plain language, because they are the two ways
this tool's output is most likely to be over-read:

1. **One question is one question.** *"This is one question, against these competitors.
   Test 3–5 questions your customers actually ask before making the same kind of change
   elsewhere."* A pooled result across several questions is reported when they are given;
   below 25 questions it is described as an estimate, never as a general rule, matching the
   floor this project holds itself to. Whether a result could be chance is a separate
   statement, made from the result's own permutation test (0.2.0).
2. **It measures what happens once an engine has your page.** *"This does not tell you
   whether an AI will find your page in the first place."* The documents are supplied
   directly, so retrieval is held constant. That is what makes the result causal, and it is
   also its limit.

## API keys

Read from `OPENROUTER_API_KEY` in the environment, and nowhere else. Never written to disk,
never printed, never included in `manifest.json` or an error message. This repository has
already had a key end up in a tracked-adjacent settings file from an approved command, so the
rule is stated here rather than left to care.

## Out of scope for the first version

Recommendations of any kind. Retrieval — whether a page gets found. Automatic competitor
discovery. Tracking over time or a dashboard. A score. Engines outside the panel. Browser
automation.

## Build plan

Almost all of it already exists and has been exercised on published rounds:

| Needed | Reused from |
|---|---|
| Model calls, citation parsing, run keys, order seeding | `run_pilot.py` |
| Fetching and slicing pages | `corpus/sources.py` |
| Length and numeral checks | `check_variants.py` |
| Intervals, permutation tests | `analyze.py` |
| Incomplete-cell and abstention guardrails | `analyze.py` |
| Engine panel and weights | `engine_weights.py` |

New code: argument handling, the edit-region detection, corpus assembly for one test, the
terminal and file output, and the chart. The runner stays standard-library only, per the
stack rule in `CLAUDE.md`; `numpy` only in analysis.

Validated before release the way this project validates everything: against a synthetic run
with a planted effect that the tool must recover, and against one of the published rounds,
which it must reproduce.

## Changes made while building it (2026-09-26)

Recorded here, as the header of this file requires, rather than left in the code.

**The ceiling rule is a gate between two phases, not a pre-flight check.** Whether your
current page is already cited almost every time can only be known by running it, so the
command runs your current page first and uses that as the gate. A question whose current
page is cited in at least 21 of 24 runs is reported as *not tested* and its edited version
is never sent. That is the §5.3 spot check applied automatically, and it means a test that
cannot be informative costs half what it otherwise would.

**The results folder is named for the test, not the date.** `<question>-<hash>`, where the
hash is of the exact text tested. Re-running an identical command therefore lands in the
same folder and resumes where it stopped, making no calls for anything already done. A
changed page produces a different hash and a new folder, which is correct: it is a
different test. The date lives in `manifest.json` and `report.md`.

**One chart per question.** `chart.svg` for a single question, `chart-q1.svg`,
`chart-q2.svg` and so on for several.

**Where each interval comes from.** For one question the interval is a bootstrap over runs
— valid for that question, and silent about any other, which is the statistical form of
"one question is one question". Across questions, the interval is a bootstrap over
*questions*, which is what captures question-to-question variation, and it is only
reported from five questions up; below 25 it is labelled a rough estimate.

**Output is written for pipes as well as terminals.** A live counter that overwrites itself
works in a terminal and becomes one unreadable line in a log or inside the Claude skill, so
the command detects which it is writing to. Errors are also flushed after the output they
refer to, not before it.

**`.gitignore` covers `opengeo-results/`**, because it holds the pages a user tested —
their competitors' included — and must never reach this repository by accident.

### Validated before release

- **Calibration**, 300 simulations per case: true nulls called significant 5.3% and 6.3%
  of the time against a 5% target; intervals covering the true effect 94.7% and 93.7%;
  estimates unbiased (mean −0.008 and −0.006 on true zeros, +0.394 on a true +0.40).
- **Reproduction of a published result.** Corpus v0.4's `cons_shoes`, run through the
  command with its own documents: **+0.60** share-weighted against the published **+0.609**
  on the same five-engine panel. Every engine's current-page rate landed within one
  citation in 24 of the published one (ChatGPT 5 against 4, Gemini 21 against 22, Claude 1
  against 1, DeepSeek 18 against 19, Grok 4 against 4), and the edited page was cited in
  all 24 runs on every engine, as published. Every engine was flagged at the ceiling
  (labelled "lower bound" in 0.1.0), as the published round predicts, and Gemini as having
  no room.

  *Corrected 2026-09-26.* An earlier version of this paragraph compared against per-engine
  figures that were computed wrongly during validation. It reported ChatGPT as +0.79
  against +0.79 and a Grok discrepancy (0.17 against 0.46) that does not exist. The
  published counts above come from `target_cited` in `results/runs_v0.4.jsonl`, the field
  `analyze.py` uses, deduplicated by run key.
- **No key in any output.** The results folder was searched for the key after a live run.

## Changes in 0.2.0 (2026-09-30)

Found by testing the Claude skill: agents with and without it were given realistic requests
and their answers graded, and the answers turned up problems in the tool itself.

**The corpus version is a hash of the experiment, not of where the files were.** In 0.1.0 it
covered each page's file path, so the identical test run from another folder got a
different version — and therefore different document orders and a different results
folder — and the path put the user's home directory into `corpus.json`. It now covers the
questions and the exact text of every document, and provenance records file names only.

**A missing numpy blocks the run before anything is spent.** It is needed only by the
analysis, which runs after every call has been paid for, so in 0.1.0 a missing numpy
surfaced as a crash after the spend.

**"Lower bound" became "ceiling".** METHODOLOGY §9 calls a saturated treatment arm's effect
a floor, which is right for researchers and misread by everyone else as "at least this
much, on my other pages too". In a user's own test the change shown is all the room there
was, so the output now says the edit got the page cited every time against these
competitors, and not how it would do against pages that also answer the question.

**Chance is stated from the result itself.** 0.1.0 printed "about 1 in 20 tests shows a
change by chance alone" under every result. That is the false-positive rate of the 95% bar,
not the chance that a given result is noise, and it cast doubt on clear results. The pooled
figure now has its own permutation test, stratified by engine, and the output says how
often an edit that did nothing would show a difference this large. Calibrated on 300 true
nulls: 3.0% significant against a 5% target.

**A borderline verdict.** The pooled interval and the permutation test agree except near
the line. Where they disagree, the result is called borderline rather than raised or
lowered.

**Intervals no longer collapse at the ceiling.** When the edited page is cited in all 24
runs — what an edit that adds a missing answer usually produces — that arm has no variance,
and a plain percentile bootstrap treats 24 of 24 as certain. A real run showed it: ChatGPT
at 83% → 100% got an interval of +4 to +33 while its own permutation test gave p = 0.108.
By simulation at n = 24, coverage was 91% at 83% → 100% and 61% at 96% → 100%. Each arm is
now resampled with one success and one failure added (Agresti and Caffo, 2000), which
brings those to 93% and 100%; away from the ceiling it errs wide (97–99%). Pooled over
engines, 2.7% of 300 true nulls were called raised or lowered, and power on a true +10
points went from 28% to 24% — the price of intervals that don't overstate. An engine now
counts toward "held on N of 5" only when its interval and its permutation test agree.

**Every page is shown with its title**, as set out under "Three design decisions" above.
`fetch` writes the title as the first line of its file, so a test built from fetched text
and one built from the HTML are identical; an edit to the title alone is tested under the
same excerpt; a title on only one version is blocked.

**Competitor sections skip navigation.** Page extraction turns a menu or link list into one
run-on "sentence", whose many topic words won the relevance score: on live pages, 0.1.0
picked 234–377 words of navigation instead of an 80-word section. A section now never
includes a "sentence" over 75 words — 95% of sentences on 183 real pages run under 64, and
the top 2% run 145 or more — and a page with no prose section long enough falls back to its
best 80-word window. Clean inputs are unaffected: the published reproduction's corpus is
byte-identical.

**5 competitors recommended, up from 4**, as the defaults table records.

**The cost estimate uses each engine's own price.** 0.1.0 assumed one flat price bracket
and a 220-token answer for every engine. The panel's prices are higher than that bracket,
and Grok's answers run to about 600 tokens because its reasoning is billed, so a real run
cost $0.29 against an estimated $0.06–$0.18. The estimate now uses each engine's current
price from OpenRouter's public model list (a dated table when it can't be reached) and
each engine's mean answer length over 27,360 published answers. On two real runs, each
billed total fell inside the new range. Every run now also reports what it actually cost,
as billed, in the terminal, `report.md` and `manifest.json`.

**Shown before anything is spent:** the excerpt and title the engines will see, and that a
question whose current page leaves no room stops halfway at about half the cost. The
report quotes the excerpt in full under "What the engines saw".
