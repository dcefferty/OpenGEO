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
    --against  https://competitor-a.com/audits \     # 2+ competitor pages, 4-5 recommended
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
| Your edited page | **Flagged if cited every time** | Public/private round: a saturated arm makes the effect a lower bound on every scale (§9) |
| Engines that cite nothing | **Excluded only if they fail on answering documents too** | Public/private round: the pooled rule dropped an engine that was abstaining correctly (§3) |
| Interrupted runs | **Resumed, never analysed short** | Length-ladder round: a mid-run credit failure left cells at 5 of 24 runs (`analyze.incomplete_cells`) |
| Document length | **The 50–110 word section most relevant to the question** | The regime every published effect was measured in; full pages behave differently (page-length screen) |

## Three kinds of guardrail

**Fixed** — no flag exists. Runs per version, temperature, random order, the engine panel.
There is no evidence that relaxing any of them leaves the result unbiased, and a cheaper,
noisier answer that looks identical to a correct one is worse than no answer. At roughly
$0.05 per question, cost is not a reason to cut any of them.

**Blocking, relaxable with evidence** — one case: edit length. The ±3-word rule exists so an
effect cannot be word count in disguise. But H7 measured padding a page to double its length
at **+0.004, CI [−0.023, +0.031]**: length alone does not move citation. Most real edits add
content rather than swapping it, so a strict rule would reject the edits people actually
make. `--allow-length-change` permits it, and the report states the length difference and
cites H7 as the reason it is not a confound. The flag is named for what it does and its use
is recorded in the output — a documented deviation, like the ones this project logs in its
own pre-registrations, not a silent setting.

**Warning** — the run proceeds and the report says what it means. A saturated edited page
(the effect is a lower bound), fewer than four competitors (less competition than every
published round had), a single question.

## Two design decisions

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

1. **One question is one question.** *"This tells you about this question, against these
   competitors. Test 3–5 questions your customers actually ask before changing your whole
   site."* A pooled result across several questions is reported when they are given; below
   25 questions it is described as an estimate, never as a general rule, matching the floor
   this project holds itself to.
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
