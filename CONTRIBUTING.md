# Contributing

The most useful contribution is **re-running a round and disagreeing with it**. Everything
needed to do that ships with each result: the corpus, the harness, and every raw model
response. If your numbers differ from the published ones, that is a finding — open an
issue with your `runs.jsonl` and the corpus hash you ran against.

## Reproducing a round

Everything a round needs lives in `experiments/`, and runs from there:

```bash
cd experiments
python3 corpus/build_corpus.py                   # regenerate the corpus + balance checks
python3 run_pilot.py --dry-run                   # cost estimate, no API calls

export OPENROUTER_API_KEY=sk-or-...
python3 run_pilot.py                             # --resume after any interruption
python3 analyze.py --runs results/runs.jsonl
```

Validate the analysis before spending anything — `make_mock.py` plants known effects that
`analyze.py` must recover:

```bash
python3 make_mock.py
python3 analyze.py --runs results/mock.jsonl
```

Python 3.9+. The runner is standard library only; `numpy` is used for analysis.

## The rules that are not negotiable

These are what the benchmark is for. A change that breaks one is a different experiment,
not an improvement — `METHODOLOGY.md` explains each, and `CLAUDE.md` lists them compactly.

- **Retrieval is held constant.** Documents are supplied in context. Adding live web search
  makes it Tier 2, and every published result carries the caveat.
- **Document order is randomised per run**, seeded from the run key.
- **Temperature stays at 1.0.** We measure the distribution a real user is exposed to.
- **Paired design.** Only the target document differs between arms.
- **24 runs per cell minimum.** Split-half reliability is 0.21 at n=10 and 0.75 at n=24.
- **Every reported proportion carries an interval** — Wilson for single proportions,
  bootstrap for shares and ranks.
- **Inference is permutation- or bootstrap-based.** No scipy, no distributional
  assumptions to argue about.
- **No composite "visibility score."** Unreproducible and not comparable across vendors.

## If you are adding a round

1. **Pre-register it** — hypotheses, corpus hash, models, runs per cell, primary metric,
   analysis plan, stopping rule — and commit that file *before* collecting. The git
   timestamp is the evidence.
2. **Spot check** a few hundred calls to confirm the baseline is not at a ceiling or floor.
   This is a go/no-go gate on the design, never a peek at the result.
3. **Run it to completion.** No interim analysis.
4. **Publish whichever direction it went.** Nulls get equal prominence; a benchmark that
   only reports wins is a marketing site.
5. Log any deviation inside the pre-registration, dated. Never quietly edit what a round
   said it would do.

## Corpus rules

- **All document text lives in the builders**, never hand-edited into a `corpus_*.json`.
  Edit the builder and regenerate.
- **Excerpts are sliced from committed snapshots**, never retyped —
  `experiments/corpus/sources.py` fails the build rather than warning if a source has
  drifted.
- **Rights are established per document**, with evidence. A `.gov` domain is not by itself
  a federal work.
- **Corpus versions are immutable once a round has run against them.** Changes get a new
  version; a changed denominator makes the trend line fiction.

## Before opening a PR

```bash
cd experiments
python3 build_findings.py --check                # validate the findings ledger
python3 check_private.py                         # private-split leak check
```

The findings page is generated, never hand-edited. A round is published by adding its
entry to `experiments/results/findings.json` and running `build_findings.py`; the build
refuses a claim the data no longer supports.
