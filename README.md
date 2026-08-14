# OpenGEO Pilot v0.1

Metric-validation pilot for the open GEO benchmark. Measures the **synthesis stage** —
given a fixed candidate set, which sources does a model cite, and why?

Retrieval is held constant by construction, which is the whole point: it is the only way
to attribute a change in citation rate to the content rather than to domain authority,
crawl freshness, or index position.

See `METRICS.md` for the metric definitions, the hypotheses, and what each vendor claim
we are testing actually says.

## Run it

```bash
python3 corpus/build_corpus.py          # regenerate corpus (already built)
python3 run_pilot.py --dry-run          # cost estimate, no API calls

export OPENROUTER_API_KEY=sk-or-...
python3 run_pilot.py                    # 4,608 calls, ~$1.20-$16 depending on model tier
python3 analyze.py --runs results/runs.jsonl
```

Interrupted? `python3 run_pilot.py --resume` picks up where it stopped.

Verify the analysis before spending anything:

```bash
python3 make_mock.py                    # synthetic data with KNOWN planted effects
python3 analyze.py --runs results/mock.jsonl
```

Requires Python 3.9+ and numpy. The runner is standard library only.

## Design

| | |
|---|---|
| Prompts | 12, across 6 domains (SaaS, consumer product, health, finance, local services, travel) |
| Documents | 6 per prompt, one in each format: blog, news, docs, product, forum, reference |
| Target | 1 document per prompt, with `control` (generic) and `treatment` (claim-dense) variants |
| Conditions | 2 — only the target changes; the other 5 documents are byte-identical |
| Position | randomised per run from a recorded seed; target slot logged every run |
| Models | 8 via OpenRouter (Claude, GPT, Gemini, Grok, Kimi, DeepSeek, Llama, Mistral) |
| Runs | 24 per cell |

Format is a **fully paired within-prompt factor** and target format is balanced (each
format is the target in exactly 2 prompts), so format effects are estimable without
confounding them with subject matter.

Document order randomisation is what makes the Position Sensitivity Index free: every run
lands the target in some slot, so slot effects are estimated from the same calls that
produce everything else.

Documents are chunk-sized (28–82 words). Engines retrieve chunks, not whole pages, so this
is closer to the real pipeline than full articles would be — and it keeps the pilot inside
budget.

## What the mock run already told us

The synthetic-data check was not a formality. It found two problems before any money was spent.

**1. Kendall's W has a noise floor that swamps the signal.** The first version reported
cross-model W = 0.15 and called H3 "supported — models disagree." But the mock plants
*identical* structure across all models, so they should have agreed. The low W was sampling
noise, not disagreement — a model at finite runs does not even agree with itself. The fix
computes a within-model split-half W as the baseline; only the gap between cross-model and
within-model W is evidence. **Any published claim that models rank sources differently, made
without this baseline, is unsupported** — and this is a claim the vendor literature makes
routinely.

**2. Ten runs per cell is not enough.** Split-half reliability on clean synthetic data with
a real planted signal:

| runs/cell | Spearman-Brown |
|---|---|
| 4 | 0.15 |
| 10 | 0.21 |
| 16 | 0.61 |
| 24 | **0.75** |
| 40 | 0.75 |

Reliability crosses into usable territory between 16 and 24, and plateaus after. The
industry convention of ~10 runs per prompt is calibrated for *estimating a level* to within
a few points; it is not sufficient for *detecting a difference*. Default is now 24.

The mock also confirmed the pipeline recovers what is planted: the U-shaped position profile
came back as 0.61 / 0.44 / 0.28 / 0.31 / 0.38 / 0.55 across slots 0–5, and the planted OR of
1.40 came back as a pooled +6.7pp shift (p = 0.019) — significant pooled, non-significant for
most individual models, which is exactly the power story 12 prompts predicts.

## Reading the output

The section that matters most is the **variance decomposition** at the end. It reports η² for
model, prompt, position, format, domain and the content intervention against the same
outcome. If position outweighs the content condition — as it did by roughly 10× in the mock —
then the industry's content-optimisation advice is second-order to where you land in the
retrieval set, and that is the headline.

## Known limitations

- **12 prompts is below the 25-prompt floor** in the methodology spec. This pilot validates
  metric reliability and estimates variance components for designing Round 1. It is not
  powered to publish an effect size for H4.
- **Synthesis stage only.** Says nothing about whether a page gets retrieved at all, which is
  probably where the larger real-world effects live.
- **Model routing.** OpenRouter may serve different backends or quantisations over time.
  `model_returned` is logged per run; check it before comparing across sessions.
- **Cheap model tiers.** Frontier flagships would blow the budget on input tokens. The pilot
  tests whether the *metrics* work, not which model is best.

## Files

```
METRICS.md              metric definitions, hypotheses, vendor-claim analysis
corpus/build_corpus.py  corpus source (all document text lives here)
corpus/corpus_v0.2.json generated, hashed, length-matched
run_pilot.py            OpenRouter runner, resumable, full provenance
make_mock.py            synthetic data with planted effects
analyze.py              metrics + H1-H5 tests
results/runs.jsonl      one JSON record per run
```
