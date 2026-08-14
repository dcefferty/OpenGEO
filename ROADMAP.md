# Roadmap

Ordered by what makes the project real, not by what is most fun to build.
Each task states its acceptance criterion so it can be picked up cold.

---

## P0 — before the first real run

### 1. Length-matched corpus v0.2 — done (2026-08-11)
Rewrote the 12 target-document pairs so control and treatment are within ±3 words of each
other, replacing generic phrasing with specific figures rather than *adding* them.
`corpus/corpus_v0.2.json` (sha `491dad19cb3cd9b0`): target length delta min=-3 max=3 mean=-0.2.
`corpus_v0.1.json` no longer exists on disk — it was never run against real models, so there
was nothing to preserve under the immutability rule.

### 2. Pre-register the pilot — done (2026-08-13)
`preregistrations/2026-08-pilot.md` — hypotheses H1–H5, corpus hash `491dad19cb3cd9b0`,
8-model list, 24 runs/cell, primary metric (target CPR), full analysis plan, reporting rules,
and stopping rule. Committed before `results/runs.jsonl` exists.

### 3. First real run
`python3 run_pilot.py --dry-run`, confirm cost, then run. Expect ~4,608 calls.

*Done when:* `results/runs.jsonl` is complete with <2% error rate and `analyze.py` runs clean.

**Check before trusting anything:** the per-model no-cite rate in the DATA HEALTH section. A
model that frequently fails to emit parseable `[n]` citations is an instruction-following
failure, not a low-visibility signal. Exclude it explicitly; never average it in.

---

## P1 — making the result publishable

### 4. Fidelity metrics (Group C)
`METRICS.md` defines Claim Fidelity Rate and Distortion Rate but `analyze.py` does not compute
them. Implement via entailment checking of each attributed sentence against its cited document,
following ALCE's citation-precision construction (arXiv 2305.14627). Needs a judge model —
use a different model family than the one under test, and report judge-model sensitivity.

*Why it matters:* nobody in the GEO industry reports fidelity. It is the clearest open space
in the metric set.

### 5. Power analysis for Round 1
Use the pilot's observed variance components to size Round 1 properly: how many prompts, how
many runs, to detect an OR of 1.3 at 80% power. The simulation approach is in
`METHODOLOGY.md` §5.2.

### 6. Round 1 as a Princeton replication
Re-run GEO-bench's intervention set (statistics, quotations, citations, fluency, keyword
stuffing, authority claims) against real 2026 models on the v0.2 corpus, ≥25 prompts.

*Why this one:* "we re-ran the most-cited GEO study against real engines and here is what held
up" is a headline the industry has to read, because it has been quoting those numbers for two
years. If it fails to replicate, that is the finding.

### 7. Publish
Results as CC-BY, code MIT. Raw `runs.jsonl` published alongside the analysis — the raw data
being downloadable *is* the differentiator. Include nulls with equal prominence.

---

## P2 — the harder, more valuable work

### 8. Calibration study
API vs logged-out UI vs logged-in UI divergence on a prompt subset. Graphite documented that
these "vary significantly" and that tracking tools "should not be used as ground truth," but
published no magnitude. Nobody has. Small n, quarterly, manual collection acceptable.

*Why it matters:* converts the project's main methodological weakness into a novel published
result.

### 9. Tier 2 live-web field experiment
Real pages, randomized within-site pairs, published, measured after recrawl. Budget an 8-week
clock — time-to-first-citation runs ~6.8 days median, 37 days P90. Needs 5–10 donor sites.

### 10. Held-out private split
Contamination defence. Publish only aggregate results from the private half; rotate a fraction
of public prompts each round.

---

## Explicitly not doing

- A brand-tracking dashboard or per-customer monitoring.
- Recommendations / audit / "fix your site" tooling. Selling the fix destroys the credibility
  of the measurement.
- A composite "visibility score."
- Browser automation as the primary query plane.

---

## Kill criteria

Decided in advance, while unattached to the outcome: **if after two published rounds nobody
outside the author's own network cites or re-runs the benchmark**, the standard is not being
adopted. Convert the harness into a narrow paid tool, or stop. Revisit this honestly rather
than moving the goalposts.
