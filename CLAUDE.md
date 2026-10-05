# CLAUDE.md — OpenGEO

Context for coding agents (Claude Code, Codex) working in this repo. `AGENTS.md` is a
symlink to this file, so both tools read the same rules.

Read `METHODOLOGY.md` before changing anything about the experiment — it is the standard:
design, metric definitions (§4), statistics (§5), corpus construction (§9). `ROADMAP.md`
has what is open, what has already run, and why the project exists.

## What this is

An open, reproducible **causal** benchmark for Generative Engine Optimization: does
changing a piece of content actually change whether an AI answer engine cites it?

It is deliberately **not** a brand-visibility tracker. That layer is commoditised
(OneGlanse, gego, geo-aeo-tracker are open source; Profound, Peec and Semrush are
commercial). Competing there is how this project dies. The defensible position is
neutrality plus reproducibility, and a funded vendor cannot occupy it — see `ROADMAP.md`,
"Why this project exists". Do not re-litigate that.

## Load-bearing design decisions

Changing any of these breaks the experiment. If a change seems to require it, stop and ask.

- **Retrieval is held constant.** Documents are supplied in context; we measure the synthesis
  stage only. Every published result must carry that caveat. Do not add live web search to the
  Tier 1 harness — that is Tier 2 and a different experiment.
- **Document order is randomised per run**, seeded from the run key. This is what makes the
  Position Sensitivity Index estimable for free. Do not fix the order to "reduce variance."
- **Temperature stays at 1.0.** We are measuring the distribution a real user is exposed to.
  Lowering it to stabilise numbers measures a different thing.
- **Paired design.** Only the target document differs between arms; the other five are
  byte-identical. Pairing is worth ~3× the statistical power at identical cost (0.95 vs 0.32
  at 50 prompts × 20 runs). Never compare against a different set of control documents.
- **24 runs per cell minimum.** Split-half reliability was 0.21 at n=10 and 0.75 at n=24 on
  clean synthetic data with a real planted signal. The industry's ~10-run convention is
  calibrated for estimating a *level*, not detecting a *difference*.
- **Every reported proportion carries an interval.** Wilson for single proportions, bootstrap
  for shares and ranks. A number without a denominator, an engine breakdown, and an interval
  is not a measurement.
- **Kendall's W needs its within-model baseline.** A model at finite runs does not agree with
  itself; raw cross-model W is mostly noise floor. Only the gap is evidence. This bug was
  already caught once — don't reintroduce it.

## Working practices

- **Verify against mock data before spending money.** `make_mock.py` plants known effects.
  Any change to `analyze.py` must still recover them. This has already caught two real bugs.
- **Publish nulls.** A benchmark that only reports wins is a marketing site.
- **Pre-register each round** — hypotheses, corpus hash, interventions, primary metric, and
  analysis plan committed *before* collection. It is a timestamped file in
  `experiments/preregistrations/`.
- **Spot-check before every full round.** A few hundred real calls confirming the baseline is
  not at a ceiling or floor, after pre-registration and before collection. It is a gate on the
  design, not a look at the result. Two rounds were wasted learning this (`METHODOLOGY.md` §5.3).
- **Never ship a composite "visibility score."** It is unreproducible and not comparable
  across vendors. Rejecting it is a positioning decision, not an oversight.
- **All document text lives in the corpus builders**, not in the generated JSON. Edit the
  builder and regenerate; never hand-edit a `corpus_*.json`.
- **Corpus versions are immutable once a round has run against them.** Changes get a new
  version number, because a changed denominator makes the trend line fiction.
- **Pre-registrations and published reports are immutable too.** Log deviations inside the
  pre-registration, dated; never quietly edit what a round said it would do.
- **The public page is generated, never edited.** A round is published by adding its entry
  to `experiments/results/findings.json` — every figure citing the round's committed
  report — and running `build_findings.py`, which also rewrites the README's results
  between its `findings` markers; never edit inside them. Prose claims like "every model"
  carry named assertions in the ledger; if new data breaks one, the build refuses. Fix the
  sentence, not the assertion. In-progress rounds may not carry result data, by the same
  no-interim-analysis rule every pre-registration states.
- **The root holds the tool and the project docs; the benchmark lives in `experiments/`.**
  New round code and data go there. Paths in its scripts, pre-registrations and reports are
  relative to that folder; the findings ledger's paths are relative to the repository root,
  because it also links outside it.

## Commands

The benchmark runs from `experiments/`:

```bash
cd experiments
python3 corpus/build_corpus.py                      # regenerate + print balance checks
python3 run_pilot.py --dry-run                      # cost estimate, no API calls
python3 run_pilot.py                                # 4,608 calls at defaults
python3 run_pilot.py --resume                       # continue after interruption
python3 analyze.py --runs results/runs.jsonl

python3 make_mock.py                                # synthetic data, known effects
python3 analyze.py --runs results/mock.jsonl        # must recover them

python3 build_findings.py --check                   # validate results/findings.json
python3 build_findings.py                           # regenerate ../docs/index.html (overview) and ../docs/findings.html
python3 render_preview.py                           # redraw the link-preview image when results change (needs Chrome)
```

Needs `OPENROUTER_API_KEY`. Python 3.9+; numpy for analysis, stdlib only for the runner.

## Stack constraints

- **Runner stays standard-library only.** Contributors must be able to reproduce a round
  without a dependency tree. numpy is acceptable in `analyze.py`; nothing heavier.
- **All inference is permutation- or bootstrap-based.** No distributional assumptions to
  argue about, and anyone can re-run it. Don't reach for scipy/statsmodels to save a few lines.
- **OpenRouter is the query plane.** APIs, not browser automation — reproducible, ToS-clean,
  and maintainable by one person on nights and weekends. Log `model_returned` on every run;
  OpenRouter may silently reroute backends or quantisations.

## Scope honesty

A round below the 25-prompt floor (`METHODOLOGY.md` §5.2) estimates an effect and its
variance; it does not publish an effect size. Report it as an interval, and say which it is.

## Where things stand

Not here — it goes stale. Current results are in `experiments/results/findings.json` and
on the generated page; open work and completed rounds are in `ROADMAP.md`.
