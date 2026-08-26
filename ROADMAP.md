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

### 3. First real run — done (2026-08-14)
4,608 calls, 0 errors, `analyze.py` runs clean. Two attempts: the first hit a bug (3 of 8
pre-registered model IDs were invalid on OpenRouter, unrelated to a mid-run credit exhaustion)
— see the deviation logged in `preregistrations/2026-08-pilot.md` and the archived failed
attempt at `results/runs_attempt1_failed.jsonl`. The corrected second attempt is clean.

**Check before trusting anything:** the per-model no-cite rate in the DATA HEALTH section. A
model that frequently fails to emit parseable `[n]` citations is an instruction-following
failure, not a low-visibility signal. Exclude it explicitly; never average it in.
**`moonshotai/kimi-k2` triggers this here — 34.4% no-cite rate, an order of magnitude above
every other model (next highest: 1.7%).** Its CPR (0.545) and its H4 result (the only
individually significant one, p=0.0227) are not trustworthy until re-run with that excluded.

Real-data highlights (all subject to the scope-honesty caveat below):
- H4 pooled (all 8 models): delta +0.001, 95% CI [-0.030, +0.026], p=0.96 — a clean null,
  consistent with the pre-registration's power expectation at 12 prompts.
- H2 (position): mean PSI 0.102, but η² for target slot is only 0.003 vs. η²=0.483 for
  content format and η²=0.484 for prompt identity — position matters less than *what kind of
  document* it is. `product`-format documents cite at 0.232 vs. 0.90+ for every other format.
- H3 (cross-model agreement): cross-model W 0.801 vs. within-model baseline 0.785 — gap
  −0.015. **Not supported** — models agree with each other about as much as they agree with
  themselves. Contradicts the "AI visibility is engine-specific" narrative, at least on this
  corpus.
- H1 (reliability): Spearman-Brown ≥ 0.91 for 7 of 8 models; kimi-k2 at 0.691 tracks its
  citation-parsing problem above.

---

## P1 — making the result publishable

### 4. Fidelity metrics (Group C)
`METRICS.md` defines Claim Fidelity Rate and Distortion Rate but `analyze.py` does not compute
them. Implement via entailment checking of each attributed sentence against its cited document,
following ALCE's citation-precision construction (arXiv 2305.14627). Needs a judge model —
use a different model family than the one under test, and report judge-model sensitivity.

*Why it matters:* nobody in the GEO industry reports fidelity. It is the clearest open space
in the metric set.

### 5. Power analysis for Round 1 — done (2026-08-16)
`size_round1.py` resamples the pilot's real (prompt, model) control-condition cells (bootstrap,
not the `METHODOLOGY.md` §5.2 Beta(1.2,3) assumption) and simulates the same sign-flip
permutation test `analyze.py` uses.

**The headline finding isn't a number, it's that the original table's assumption was wrong.**
Real control CPR averages 0.867, with 67% of (prompt, model) cells at a literal 100% ceiling —
vs. the assumed Beta(1.2,3) prior (mean 0.288). A treatment effect has almost no room to move
against a near-ceiling baseline: at the pilot's own scale (12 prompts x 24 runs/arm), real power
for OR=1.3 is 0.34, vs. 0.87 under the old assumption at the identical size. This is a ~2.5x
miss, not a rounding error.

*Recommended design:* **50 prompts x 24 runs/arm = 16,800 calls, power ~0.96 for OR=1.3.** Kept
runs/arm >= 24 deliberately — some cheaper configurations (e.g. 100 x 10) reach similar power on
paper but violate the 24-runs/cell reliability floor in `CLAUDE.md`, which exists for a
different reason (split-half reliability) than statistical power and shouldn't be silently
traded away. 25 x 30 (10,500 calls, power 0.80) is viable but has no margin.

*The more consequential fix is corpus design, not N.* If Round 1's target documents aren't the
obviously-best match among only 6 candidates — i.e., control CPR sits in a more sensitive
30-70% range instead of 87%+ — power at the *pilot's own* 12x24 scale would be 0.87 instead of
0.34. Ceiling avoidance is free; more calls is not. Corpus construction for Round 1 should
prioritize this over simply scaling up the pilot's prompt style.

### 5b. Ceiling-fix corpus (v0.3) — done (2026-08-23)
Acted on item 5's corpus-design finding rather than just sizing around it. Rewrote all 12
prompts in `corpus/build_corpus.py`: narrowed each question to one specific fact, then rewrote
each control document to share *no* topical surface with that fact — not just the number.
First-draft fixes failed in two distinct ways worth remembering if this corpus is touched
again: (1) a control that drops the number but keeps a literal keyword the question also uses
(e.g. "minimum" in both) gets quoted verbatim as a citation hook even when the model says it
can't answer; (2) a control that keeps the same *qualitative conclusion* as the question, or as
an unrelated distractor document, gets cited as mutually-reinforcing evidence even with zero
keyword overlap and no number. Every prompt was validated against real models — individually at
first, then a full 4,608-call run — before being treated as done; several looked fine on
read-through and still failed until tested.

*Result:* H4 pooled delta went from +0.001 (v0.2, null) to **+0.493, CI [+0.352, +0.641],
p=0.0005** on v0.3, individually significant for all 8 models including `kimi-k2`. Condition
(claim density) is now the largest variance driver (η²=0.315, was 0.000). H1/H2/H3/H5 all
replicate their v0.2 verdicts. Full results: `results/runs_v0.3.jsonl`.

v0.3 is corpus-design validation, not a pre-registered round — see item 6.

### 6. Round 1 as a Princeton replication — run, but not yet pre-registered (2026-08-25)
Scaled the v0.3 recipe from 12 to 48 prompts (corpus v0.4, 24 domains × 2, item 5's sizing
target) and ran it for real: 18,432 calls. Two operational snags along the way, both
resolved without data loss — a mid-run `403 Key limit exceeded` (a spending cap configured
on the API key itself, not the account; removed by the user, then `--resume` picked up
cleanly) and, during corpus construction, a harder-to-catch failure mode than v0.3's: even
after removing literal keyword overlap, a control document could still fail if *any*
sentence gave a qualitative/directional answer to the question in different words (e.g. "a
CPU-bound game won't benefit much" answers "how much frame-rate improvement," and "worth
every penny" answers a cost question, neither using the question's own vocabulary). Caught
by testing prompts against real models, not by inspection — a purely keyword-based audit
script missed all of these.

*Result:* H4 pooled delta +0.482, 95% CI [+0.404, +0.563], p<0.0001, individually
significant for all 8 models (including kimi-k2, p<0.0001) — the tightest, most
unambiguous version of this finding yet. Condition remains the dominant variance driver
(eta^2=0.305). H1/H2/H3/H5 all replicate. Full results: `results/runs_v0.4.jsonl`.

**This was not pre-registered before collection**, so per this project's own credibility
standard it is strong scaled-up confirmatory evidence, not yet "the" citable Round 1. Before
publishing this as a headline result, either (a) write and commit a pre-registration for a
fresh run on this same v0.4 corpus, or (b) if re-running is wasteful given how unambiguous
this result already is, publish it explicitly labeled as exploratory/non-pre-registered and
reserve "Round 1" for the next genuinely new intervention or corpus. Don't retroactively
call this pre-registered — that defeats the point of the practice.

**Decision (2026-08-25): (b).** Re-running an experiment to satisfy pre-registration after
already seeing the result twice, at two scales, doesn't buy the credibility pre-registration
exists to provide — it would be theater, not rigor. Published as exploratory instead; see
item 7. "Round 1" stays reserved for the next genuinely new intervention, run under a
pre-registration committed before any data exists.

*Why replication matters:* "we re-ran the most-cited GEO study against real engines and here
is what held up" is a headline the industry has to read, because it has been quoting those
numbers for two years.

### 7. Publish — done for the v0.4 exploratory round (2026-08-25)
`results/published/2026-08-25-corpus-v0.4-exploratory/REPORT.md` — full H1-H5 results
including the H3 null, variance decomposition, limitations, and reproduction steps. Code
MIT, data CC-BY per `LICENSE`. Raw `results/runs_v0.4.jsonl` stays in the main tree
(referenced, not duplicated, to avoid bloating the repo with a second 50MB+ copy) with its
git commit pinned in the report for provenance.

Still open: a genuinely pre-registered Round 1 (a new intervention or corpus, pre-registration
committed before collection) remains undone — this item covers publishing what exists, not
producing the citable "Round 1" that item 6 explicitly declined to claim.

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
