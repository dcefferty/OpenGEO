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
- **The public page is generated, never edited.** A round is published by adding its entry
  to `results/findings.json` — every figure citing the round's committed report — and
  running `build_findings.py`. Prose claims like "every model" carry named assertions in
  the ledger; if new data breaks one, the build refuses. Fix the sentence, not the
  assertion. In-progress rounds may not carry result data, by the same no-interim-analysis
  rule every pre-registration states.

## Commands

```bash
python3 corpus/build_corpus.py                      # regenerate + print balance checks
python3 run_pilot.py --dry-run                      # cost estimate, no API calls
python3 run_pilot.py                                # 4,608 calls at defaults
python3 run_pilot.py --resume                       # continue after interruption
python3 analyze.py --runs results/runs.jsonl

python3 make_mock.py                                # synthetic data, known effects
python3 analyze.py --runs results/mock.jsonl        # must recover them

python3 build_findings.py --check                   # validate results/findings.json
python3 build_findings.py                           # regenerate docs/index.html
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

The v0.2 pilot ran clean against real models (4,608 calls, 0 errors, pre-registered in
`preregistrations/2026-08-pilot.md`) but H4 (claim density → citation) came back a clean null
— pooled delta +0.001, CI includes zero. Diagnosis: control-condition CPR averaged 0.867 with
67% of (prompt, model) cells at a literal 100% ceiling, because the broad "what should I look
for in X" style questions let every one of the 6 candidate documents answer *something*, so
citation stopped discriminating on content at all.

**Corpus v0.3** (`corpus/corpus_v0.3.json`, under construction in `corpus/build_corpus.py`)
fixes this: each of the 12 questions was narrowed to ask for one specific fact that only the
treatment variant states outright, and — the part that actually mattered — each control
document was rewritten to share *no* topical surface with that fact, not just the literal
number. A control that merely omits the number but still gestures at the same topic (e.g.
"be wary of tools that charge per seat") still gets cited; models will quote even a loosely
adjacent phrase as justification. Validated prompt-by-prompt against real models before the
full run (see git history on `corpus/build_corpus.py` for the per-prompt diagnosis trail —
several first-draft fixes failed for subtle reasons worth reading if touching this corpus
again). Full v0.3 run (`results/runs_v0.3.jsonl`, 4,608 calls, 0 errors): H4 pooled delta
+0.493, CI [+0.352, +0.641], p=0.0005, individually significant for all 8 models.

v0.3 has not been pre-registered as a numbered round — it's the corpus-design validation that
Round 1 will be built from, not Round 1 itself.

**Corpus v0.4** scales the validated v0.3 recipe from 12 to 48 prompts (24 domains × 2, 8
prompts per format). Validation surfaced a subtler failure mode than v0.3's: even with zero
literal keyword overlap, a control document could still fail if any sentence gave a
qualitative or directional answer in different words (e.g. "a CPU-bound game won't benefit
much" answers a frame-rate-improvement question without using those words). Caught only by
testing against real models, not by inspection or keyword scripts. Full v0.4 run
(`results/runs_v0.4.jsonl`, 18,432 calls, 0 final errors after a mid-run API-key spending
limit was hit and removed): H4 pooled delta +0.482, CI [+0.404, +0.563], p<0.0001,
individually significant for all 8 models.

**v0.4 was not pre-registered before collection**, so it is strong scaled-up confirmatory
evidence, not yet the citable "Round 1" by this project's own standard. Published
2026-08-25 explicitly labeled exploratory:
`results/published/2026-08-25-corpus-v0.4-exploratory/REPORT.md`.

**Keyword-stuffing intervention (H6)** — a genuinely new intervention, chosen and
pre-registered specifically so a fully pre-registered-before-collection round would
exist. Took three corpus designs to get a real answer, and the two failures are worth
knowing about before touching this intervention again:

- **v1** reused v0.4's `treatment` text (already ~98.5% CPR) as its "natural" baseline
  — no headroom, uninformative null (pooled delta −0.001, p=0.57).
- **v2** tried a "half-specific" baseline (one of two target facts stated, one left
  orthogonal), theorizing partial completeness would land mid-range. A pre-committed
  real-model spot check falsified that before the full round ran: half a specific
  answer gets cited at the same ~0.91–0.98 ceiling as a whole one. These models
  discriminate on presence-vs-absence of *any* specific fact, not on completeness.
  Full diagnosis in `preregistrations/2026-08-kwstuff-v2.md`.
- **v3** went back to v0.4's *actual* orthogonal control text (already measured,
  pooled CPR 0.503, confirmed non-ceiling) and stuffed keywords into it unmodified,
  with no new facts added. Spot check confirmed real headroom (per-prompt CPR
  0.17–0.87). Full run (`results/runs_kwstuff_v3.jsonl`, 18,432 calls, 0 errors):
  **H6 falsified** — pooled delta +0.038, 95% CI [+0.004, +0.075], p=0.045 (7 models,
  `kimi-k2` excluded per standing rule). Keyword stuffing did not decrease citation;
  it modestly but measurably *increased* it. Small effect (η²=0.002, dwarfed by
  prompt/domain variance), but the direction is consistently positive across models,
  not one outlier. Pre-registered 2026-08-28, before any real-model call. Published:
  `results/published/2026-08-29-kwstuff-v3/REPORT.md`.

**Group C fidelity follow-up (2026-08-30)** — `judge_fidelity.py`, the first
implementation of `METRICS.md`'s Claim Fidelity Rate / Distortion Rate (ALCE-style
entailment judging, judge model outside the 8-model test panel). Tested the report's
own speculated mechanism for H6 — does stuffing win citations partly through
distortion, not just repetition? A 500-item pilot suggested yes (dramatically); it did
**not** replicate at full scale (11,657 items, proper per-prompt paired analysis),
confirmed null by two independent different-vendor judges (qwen3.8-max and glm-5.3,
93.2% agreement on the distortion question). Keyword stuffing wins citations without
measurably lower fidelity — a pure citation-count effect, not a "cheats its way in"
effect. See ROADMAP.md item 4 and the REPORT.md's Group C section.

**Calibration study v1 (2026-08-30)** — first real measurement of the gap this project
has asserted since the beginning: API-plane results (this project's primary
measurement plane throughout) vs. what an ordinary logged-out user actually sees.
OpenAI only (Perplexity's logged-out UI blocks search entirely behind a signup wall,
confirmed by direct testing — itself a finding). 12 prompts: **divergence coefficient
0.368, 95% CI [0.139, 0.625]**, driven mostly by the API plane returning zero
citations on 3/12 prompts where the logged-out consumer UI cited real sources for the
same question — a hint that the API plane may undercount citation activity relative
to real usage. See ROADMAP.md item 8 and
`results/published/2026-08-30-calibration-v1/REPORT.md`.

**Process lesson for future interventions:** neither v1's "reuse already-validated
content wholesale" nor v2's "recombine already-validated pieces" assumption held up
without a real-model check. A pre-committed spot check *after* pre-registration but
*before* the full round — cheap (~$1-2, ~2,300 calls) relative to a wasted full round
(~$5-14, 18,432 calls) — is now the standing practice for any new corpus design in this
project, not an exception.

## Scope honesty

12 prompts is below the 25-prompt floor set in `METHODOLOGY.md`. This pilot validates metric
reliability and estimates variance components to design Round 1. It is **not** powered to
publish an effect size. Report H4 as an interval and a variance estimate, not a finding.
