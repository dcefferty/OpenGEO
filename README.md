# OpenGEO

**An open, reproducible, causal benchmark for Generative Engine Optimization.** It changes
one thing about a document and measures whether AI answer engines cite it more.

Two things make it different from the GEO numbers already in circulation. Everything here
is **reproducible** — the corpus, the harness, and every raw model response ship with the
result, so anyone can re-run a round and check it. And every result is **causal**: a paired
design where only the document under test changes between arms, rather than an
observational comparison of pages that already rank.

It is deliberately **not** a brand-visibility tracker, and it will never ship a composite
"visibility score."

**What it measures, precisely:** the synthesis stage. Documents are supplied to the model
in context, so retrieval is held constant by construction. A result here says what a model
does with content it already has — not whether a page gets found in the first place. That
caveat travels with every number the project publishes.

## Findings

The current results live in one place, generated from a ledger so they can't drift:

- **`docs/index.html`** — the findings page: what moves citation, by how much, with
  intervals. Served by GitHub Pages once this repo is public.
- **`results/published/`** — the full report for each round, including the nulls.
- **`results/findings.json`** — the machine-readable ledger the page is built from.

No figures are written into this README on purpose: every number in the project has exactly
one source, and duplicating them here is how documentation starts lying.

## Quick start

```bash
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
| `corpus/` | Document text lives in the builders; the JSON corpora are generated and hashed |
| `preregistrations/` | One file per round, committed **before** collection. The git timestamp is the evidence |
| `results/` | Raw responses, the findings ledger, and published reports |
| `docs/` | The generated public findings page |
| `run_pilot.py` | Tier 1 runner: resumable, logs full provenance per call |
| `analyze.py` | Metrics and hypothesis tests — permutation and bootstrap only |
| `judge_fidelity.py`, `fidelity_baseline.py` | Group C fidelity judging and its baseline |
| `calibration_api.py`, `calibration_prompts.py` | Calibration study, API plane |
| `build_findings.py` | Builds the findings page from the ledger |
| `size_round1.py`, `make_mock.py`, `check_variants.py`, `engine_weights.py` | Power sizing, synthetic validation, corpus checks, engine panel |

## How a round works

1. **Build a corpus** and hash it. Document text lives in the builder, never in the JSON.
2. **Pre-register** — hypotheses, corpus hash, models, runs per cell, primary metric,
   analysis plan, stopping rule — and commit it before collecting anything.
3. **Spot check** a few hundred calls to confirm the baseline isn't at a ceiling or floor.
   This is a go/no-go gate on the design, never a peek at the result.
4. **Run it** to completion. No interim analysis.
5. **Analyse and publish**, whichever direction it went, then add the round to
   `results/findings.json` and rebuild the page:

```bash
python3 build_findings.py --check                # validate the ledger
python3 build_findings.py                        # regenerate docs/index.html
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

## Licence

Code MIT. Data and results CC-BY-4.0 — cite the numbers, quote them, build on them, with
attribution. See `LICENSE`.
