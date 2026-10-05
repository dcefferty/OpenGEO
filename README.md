# OpenGEO

**Most advice on getting cited by AI has never been tested. OpenGEO tests it.** It is an
open, reproducible experiment: change one thing about a page, ask AI answer engines the same
question many times, and measure whether they cite the page more.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/effects-dark.svg">
  <img alt="What each tested change did to how often AI answers cited a page: stating the specific answer moved it far more than repeating the keyword, padding the page, or presentation tactics, which moved it little or not at all." src="docs/assets/effects-light.svg">
</picture>

**What it found.** Each result comes from a published round. The
[overview page](https://dcefferty.github.io/OpenGEO/) shows them per engine, and the
[findings page](https://dcefferty.github.io/OpenGEO/findings.html) in full.

<!-- findings:start -->
Change in the share of answers citing the page, in percentage points, with 95% intervals.

| What changed | Effect | Evidence |
|---|---|---|
| **State the specific answer** | **+48 points** (+40 to +56) | Found twice · held on unpublished questions |
| Repeat the keyword | +3.8 points (+0.4 to +7.5) | Pre-registered |
| Double the length with filler | +0.4 points (−2.3 to +3.1) | Pre-registered |
| Answer first, FAQ headings, attribution, citations | +0.1 points (−3.6 to +3.4) | Early probe · 3 questions |

- **Stating the specific answer** raised the share of answers citing the page by +48 points (+40 to +56) across 48 questions, and it went up on all 8 models tested. Repeated, pre-registered, on 12 questions that have never been published anywhere, it was +47 points (+38 to +57).
- **How big it is depends on your competition.** In these tests the before page didn't answer the question at all, and the after page was usually the only one that did, so it ended up cited almost every time. Against competitors that already state the answer, expect a smaller gain. The direction is solid; the size is specific to the setup.
- **Repeating your keyword** helped a little: +3.8 points (+0.4 to +7.5), pre-registered. It's real, but about 13 times smaller than stating the answer.
- **Padding a page** to twice its length with filler did nothing on average (+0.4 points, −2.3 to +3.1), and on some engines it cost citations.
- **Presentation**, meaning answer-first order, FAQ-style headings, attributing claims and citing sources, moved citation by +0.1 points (−3.6 to +3.4). That comes from an early probe of 3 questions, so read it as nothing found yet, not proof that it never helps.
- **FAQ schema**, the markup, was never tested, and this experiment can't test it: the engines here read a page's visible text, and markup doesn't carry into it.

**Being cited isn't the whole story.**

- **Engines sometimes credit you with things you didn't say.** When an answer cited a page, we checked each cited claim against the page. Between 13% and 20% of cited sentences said something the page doesn't support, depending on which model did the checking.
- **Tools that check the API may undercount you.** On 3 of 12 everyday questions, OpenAI's API cited nothing while chatgpt.com cited real sources. Most citation trackers query the API.
- **The engines largely agree.** Engines agree with each other about which pages deserve a citation about as closely as one engine agrees with itself on a re-run. A page that earns citations from one tends to earn them from the others.
<!-- findings:end -->

**Try one on your own page.** Any of these changes can be tested on your page, against your
real competitors, with [`opengeo test`](#test-your-own-page).

**Where it stops.** It measures the synthesis stage: what an engine does once it has your
page, not whether it finds your page in the first place. Documents are handed to each
engine, so retrieval is held constant by construction. That is what makes a result causal,
and it is also its limit; the caveat travels with every number the project publishes.

**Why it is different.** Everything is **reproducible**: the corpus, the harness and every
raw model response ship with each result, so anyone can re-run a round and check it. Every
result is **causal**: a paired design where only the page under test changes, not an
observational comparison of pages that already rank. And it is deliberately **not** a
brand-visibility tracker; it will never ship a composite "visibility score."

## Test your own page

Did your change to your page make AI engines more likely to cite it — against your actual
competitors? `opengeo test` runs the same paired, controlled experiment as every published
round, on your content:

```bash
export OPENROUTER_API_KEY=sk-or-...
python3 opengeo.py test \
    --question "How much does a home energy audit cost?" \
    --page     https://mysite.com/energy-audit \
    --edit     ./energy-audit-v2.md \
    --against  https://competitor-a.com/audits https://competitor-b.com/pricing
```

You get the change in citation rate with a 95% interval, per engine, a chart, and every raw
model response. About $0.30 per question at current prices. Add `--dry-run` to see the
checks and the estimated cost without sending anything.

The rigour is in the defaults, so you don't have to know it to benefit from it: 24 runs per
version, temperature 1.0, randomised document order, a check that your page has room to
improve before paying to test the edit, and a flag when your edited page hits the ceiling.
Each default and the evidence behind it is in `design/opengeo-test.md`.

It is a measurement, not advice. It tells you what your change did; it never tells you what
to change. And it measures what happens once an engine *has* your page — not whether an
engine finds it.

Prefer to ask in plain English? The Claude skill in `.claude/skills/opengeo/` gathers your
page, your question and your competitors, shows you the cost, runs the test and explains the
result: *"Test whether adding our prices to our water heater page helps us get cited."*

## Findings

The current results live in one place, generated from a ledger so they can't drift:

- **[The overview](https://dcefferty.github.io/OpenGEO/)** (`docs/index.html`) — what was
  tested, what moved citation, how sure we are and where it stops, in plain language.
- **[The findings page](https://dcefferty.github.io/OpenGEO/findings.html)** (`docs/findings.html`) —
  every finding in full, with per-engine charts and intervals.
- **`experiments/results/published/`** — the full report for each round, including the
  nulls.
- **`experiments/results/findings.json`** — the machine-readable ledger both pages are
  built from.

Every number in the project has exactly one source, the ledger. The results at the top of
this README are written into it by the same build that makes the pages, so they can't drift
from them: to change one, change the ledger and rebuild.

## Quick start

The benchmark lives in `experiments/`, and its commands run from there:

```bash
cd experiments
python3 corpus/build_corpus.py                   # regenerate the corpus + balance checks
python3 run_pilot.py --dry-run                   # cost estimate, no API calls

export OPENROUTER_API_KEY=sk-or-...
python3 run_pilot.py                             # the real thing; --resume after any interruption
python3 analyze.py --runs results/runs.jsonl
```

Verify the analysis before spending anything — `make_mock.py` plants known effects that
`analyze.py` must recover:

```bash
python3 make_mock.py
python3 analyze.py --runs results/mock.jsonl
```

Python 3.9+. The runner is standard library only; `numpy` is used for analysis.

## What's in here

| Path | What it is |
|---|---|
| `METHODOLOGY.md` | The standard: two-tier design, the metric set, sampling and statistics, corpus construction rules, provenance schema |
| `ROADMAP.md` | Open work, completed rounds, positioning, kill criteria |
| `CLAUDE.md` / `AGENTS.md` | Rules for coding agents working in the repo (`AGENTS.md` is a symlink) |
| `CONTRIBUTING.md` | How to reproduce a round, the rules that are not negotiable, and what adding a round requires |
| `experiments/` | The benchmark: corpora, pre-registrations, raw results, published reports, and the scripts that run, analyse and publish each round. [Its README](experiments/README.md) maps every file |
| `docs/` | The generated public pages: the overview (`index.html`) and the findings (`findings.html`) |
| `opengeo.py` | `opengeo test`: run a paired experiment on your own page against your competitors (`design/opengeo-test.md`) |
| `.claude/skills/opengeo/` | The Claude skill that runs `opengeo test` for you (`.agents/skills/opengeo` points to it, for Codex) |
| `design/` | Design records for `opengeo test` and the overview page |

## How a round works

1. **Build a corpus** and hash it. Document text lives in the builder, never in the JSON.
2. **Pre-register** — hypotheses, corpus hash, models, runs per cell, primary metric,
   analysis plan, stopping rule — and commit it before collecting anything.
3. **Spot check** a few hundred calls to confirm the baseline isn't at a ceiling or floor.
   This is a go/no-go gate on the design, never a peek at the result.
4. **Run it** to completion. No interim analysis.
5. **Analyse and publish**, whichever direction it went, then add the round to
   `experiments/results/findings.json` and rebuild the page:

```bash
cd experiments
python3 build_findings.py --check                # validate the ledger
python3 build_findings.py                        # regenerate both pages and the README's chart and results
```

The build refuses to publish a claim the data no longer supports, a round that carries
interim numbers, or a finding citing a report that doesn't exist.

`METHODOLOGY.md` §5.3 and §9 explain why each of those steps is there — all of them come
from a round that went wrong first.

## Where things moved

The docs were consolidated in September 2026. Older pre-registrations and reports cite the
previous locations:

| Cited as | Now |
|---|---|
| `METRICS.md` (Groups A–E, A1, B2, C1…) | `METHODOLOGY.md` §4 — IDs unchanged |
| `METHODOLOGY.md` §0 (positioning) | `ROADMAP.md` — "Why this project exists" |
| `METHODOLOGY.md` §9 (build sequence) | `ROADMAP.md` — "Open work" and "Completed" |
| `METHODOLOGY.md` §10 (risks, kill criteria) | `ROADMAP.md` — "The bear case", "Kill criteria" |
| `CLAUDE.md` "Current state" | `ROADMAP.md` — "Completed", plus the linked records |
| `ROADMAP.md` items 5b, 6 (corpus failure modes) | `METHODOLOGY.md` §9 |

`METHODOLOGY.md` §1–§8 keep their numbering, so every other section citation still resolves.

In October 2026 the benchmark moved from the repository root into `experiments/`, with its
layout inside unchanged: `corpus/`, `preregistrations/`, `results/` and the scripts sit at
the same paths relative to one another. Commands in earlier pre-registrations and reports
work as written when run from inside `experiments/`, and their links still resolve. To see
when a pre-registration was committed, follow it across the move:
`git log --follow experiments/preregistrations/<file>`.

## Licence and citation

Code MIT (`LICENSE`). Data and results CC BY 4.0 (`LICENSE-DATA`) — cite the numbers,
quote them, build on them, with attribution.

Corpus documents are excerpts of US federal works, which carry no US copyright
(17 U.S.C. § 105); each records its agency, source URL and rights basis.

`CITATION.cff` has the preferred citation. When you are quoting a specific number, cite
the round's dated report under `experiments/results/published/`, not just the
repository — the repository changes, a published round does not.
