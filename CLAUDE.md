# CLAUDE.md — OpenGEO

Context for Claude Code working in this repo. Read `METHODOLOGY.md` for the full design
argument and `METRICS.md` for metric definitions before making changes to the experiment.

## What this is

An open, reproducible **causal** benchmark for Generative Engine Optimization: does changing
a piece of content actually change whether an AI answer engine cites it?

It is deliberately **not** a brand-visibility tracker. That layer is commoditized (OneGlanse,
gego, geo-aeo-tracker are open source; Profound at ~$1B valuation, Peec, and Semrush are
commercial). Competing there is how this project dies.

## Why it exists

Two gaps in the field, established by research already done — do not re-litigate these:

1. **Nothing is reproducible.** Every published GEO benchmark number comes from a proprietary
   panel (Profound's 27M prompts, 700K conversations, 100.7M runs). None can be verified by
   anyone outside the company, and the company publishing the benchmark sells against it.
2. **Almost nothing is causal.** The public evidence base for "do X to your content" is the
   Princeton GEO paper (KDD 2024) plus one Profound A/B that came back *not statistically
   significant*. And GEO-bench never queried a real engine — it simulated one with Google
   top-5 retrieval plus GPT-3.5 synthesis. Its "+41% from adding statistics" figure describes
   a 2023 research pipeline, yet is quoted industry-wide as fact about ChatGPT.

The defensible position is neutrality plus reproducibility. A funded vendor cannot credibly
occupy it.

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
  analysis plan committed *before* collection. It is a timestamped file in `preregistrations/`.
- **Never ship a composite "visibility score."** It is unreproducible and not comparable
  across vendors. Rejecting it is a positioning decision, not an oversight.
- **All document text lives in `corpus/build_corpus.py`**, not in the generated JSON. Edit the
  builder and regenerate; never hand-edit `corpus_v0.2.json`.
- **Corpus versions are immutable once a round has run against them.** Changes get a new
  version number, because a changed denominator makes the trend line fiction.

## Commands

```bash
python3 corpus/build_corpus.py                      # regenerate + print balance checks
python3 run_pilot.py --dry-run                      # cost estimate, no API calls
python3 run_pilot.py                                # 4,608 calls at defaults
python3 run_pilot.py --resume                       # continue after interruption
python3 analyze.py --runs results/runs.jsonl

python3 make_mock.py                                # synthetic data, known effects
python3 analyze.py --runs results/mock.jsonl        # must recover them
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

## Current state

Pilot is built and verified against mock data, on corpus **v0.2** (length-matched: target pair
deltas are within ±3 words, mean ~0 — the v0.1 corpus confounded claim density with length by
~11 words on average, which is why v0.1 no longer exists on disk). **It has not yet been run
against real models.**

See `ROADMAP.md` for the prioritized backlog. Next up: pre-register the pilot
(`preregistrations/`), then the first real run.

## Scope honesty

12 prompts is below the 25-prompt floor set in `METHODOLOGY.md`. This pilot validates metric
reliability and estimates variance components to design Round 1. It is **not** powered to
publish an effect size. Report H4 as an interval and a variance estimate, not a finding.
