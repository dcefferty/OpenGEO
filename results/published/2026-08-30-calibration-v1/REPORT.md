# OpenGEO — Calibration Study v1: API vs. Logged-Out UI Divergence

**Published 2026-08-30. Exploratory — small-n by design**, per `METHODOLOGY.md` §3:
"Manual or lightly-assisted collection is acceptable here because n is small and the
study runs quarterly." Not pre-registered — this is measurement-infrastructure work in
the same spirit as Group C, not a causal intervention test.

## What this tests

Graphite documented that "responses from APIs, logged-out accounts, and logged-in
accounts can vary significantly" and concluded that tracking tools "should not be used
as ground truth" — but published no magnitude for that divergence. **Nobody has.** This
project runs the API-with-search plane as its primary measurement plane throughout
(`CLAUDE.md`, `METHODOLOGY.md` §3), on reproducibility, cost, and ToS grounds. This
study puts a number on the gap between that plane and what an ordinary person
actually sees.

## What this is not

This is not the Tier 1 harness used by every other round in this project (v0.4,
kwstuff-v1/v2/v3). Those hold retrieval constant — a fixed 6-document corpus supplied
in context. This study is closer to Tier 2: real consumer AI products with live web
search, on ordinary open-web questions, comparing query **planes** for the same
engine rather than comparing document variants.

## Design

| | |
|---|---|
| Prompts | 12 natural, citation-likely everyday questions across finance/health/consumer/pets/news (`calibration_prompts.py`) |
| Engine | OpenAI only for the plane comparison (see Scope below) |
| API plane | `openai/gpt-5.4-mini` + OpenRouter's `web` plugin, 3 reps/prompt, temperature 1.0 (`calibration_api.py`, `results/calibration_api.jsonl`) |
| Logged-out UI plane | chatgpt.com, no account, 1 rep/prompt, collected manually via browser (`results/calibration_ui_logged_out.jsonl`) |
| Metric | Per-prompt Jaccard similarity of cited-domain sets between planes; divergence = 1 − mean Jaccard, bootstrap 95% CI |

**Scope note — Perplexity was dropped from the plane comparison.** Its logged-out web
UI blocks search submission entirely behind a signup wall (query text stays in the
box; no answer is produced without an account) — confirmed by direct testing, not
assumed. This is itself a reportable finding: **as of this testing, Perplexity's
public UI requires an account to search at all, unlike its API.** OpenAI's logged-out
UI works without an account and was used for the full 12-prompt comparison.

## Headline result

**Divergence coefficient (API vs. logged-out UI, OpenAI): 0.368, 95% bootstrap CI
[0.139, 0.625]** (mean Jaccard similarity 0.632, n=12 prompts).

| Prompt | API-plane cited domains (3 reps, union) | Logged-out UI domains (n=1) | Jaccard |
|---|---|---|---|
| finance_fedrate | federalreserve.gov | federalreserve.gov | 1.00 |
| finance_ira | *(none)* | *(none)* | 1.00 |
| health_creatine | *(none)* | *(none)* | 1.00 |
| health_allergies | *(none)* | *(none)* | 1.00 |
| photo_lens | *(none)* | *(none)*¹ | 1.00 |
| ref_mortgage | *(none)* | *(none)* | 1.00 |
| sports_f1 | formula1.com | formula1.com | 1.00 |
| auto_evcharger | afdc.energy.gov, angi.com, homeadvisor.com | afdc.energy.gov, qmerit.com | 0.25 |
| tech_keyboard | rtings.com, tomsguide.com, tomshardware.com | rtings.com | 0.33 |
| news_weather_sea | *(none)* | timeanddate.com, weather.gov | 0.00 |
| nutrition_chipotle | *(none)* | chipotle.com | 0.00 |
| pets_vaccine | *(none)* | aaha.org | 0.00 |

¹ Logged-out UI showed shopping-style product cards (Adorama, B&H Photo with prices)
for this prompt, not the standard citation mechanism — excluded from both planes'
domain sets for consistency, noted as its own data-quality observation below.

**The divergence is driven almost entirely by asymmetric citation propensity, not by
disagreement about which sources to use when both planes do cite.** For every prompt
where both planes returned at least one citation, they overlapped substantially or
fully (federalreserve.gov, formula1.com exact matches; afdc.energy.gov and rtings.com
shared in the two partial-overlap cases). But for 3 of 12 prompts (weather, Chipotle
calories, puppy vaccines), **the API plane returned zero citations while the logged-out
UI plane cited real, specific sources for the identical question.** The consumer
website appears to invoke search more readily than the same model reached through the
API with the `web` plugin — this project's primary measurement plane may be
systematically *undercounting* citation activity relative to what an ordinary user
would see.

## Why this matters for every other round in this project

Every prior round (v0.4, kwstuff) measured the API/Tier-1 plane exclusively, per
`METHODOLOGY.md`'s own recommendation. This result doesn't invalidate those rounds —
retrieval is held constant by design there, which is a different question — but it is
the first actual measurement of the gap `CLAUDE.md` has asserted since the beginning:
*"Every published result must carry that caveat."* Now there's a number to put next to
the caveat, at least for one engine, one small prompt set, one day.

## Limitations

- **n=12 prompts, n=1 rep for the UI plane.** Small by design (`METHODOLOGY.md`
  explicitly sanctions this), but the CI is wide [0.139, 0.625] — read the divergence
  coefficient as an order-of-magnitude estimate, not a precise figure.
- **Possible model-identity confound.** The API plane deliberately used
  `gpt-5.4-mini` (this project's standard cost-tier model); the logged-out UI plane
  used whatever model chatgpt.com defaults to for an anonymous session, which is not
  confirmed to be the same model. Some of the observed divergence could be model
  choice rather than plane (API vs. UI) per se — this study cannot separate the two
  effects with the current design. A v2 would need to either match models explicitly
  or treat this as an irreducible part of "what a real anonymous user experiences,"
  which is itself a defensible framing.
- **One collection session, one day (2026-08-30).** No temporal replication. Recency-
  sensitive prompts (F1 results, weather) are especially exposed to day-to-day
  variance that this single-session design can't distinguish from genuine plane
  divergence.
- **Perplexity excluded from the plane comparison** — its logged-out UI doesn't
  support search at all, confirmed by direct testing (see Scope above). The
  signup-wall finding itself is reported, but no divergence coefficient exists for
  this engine.
- **Logged-in UI plane not attempted** in this round — would require real personal
  accounts; deferred per the explicit scoping decision for v1.
- **Manual UI collection, not automated.** Per `METHODOLOGY.md`'s own tradeoff table,
  consumer-UI automation sits in ToS gray territory; this round used interactive
  browser sessions for a small, fixed prompt set rather than a scripted scraping loop.

## Reproducing this

```bash
export OPENROUTER_API_KEY=sk-or-...
python3 calibration_api.py --dry-run          # cost estimate
python3 calibration_api.py --runs 3           # API plane, ~$1.50, 72 calls
# Logged-out UI plane: manual, see results/calibration_ui_logged_out.jsonl for the
# collected data and calibration_prompts.py for the exact prompt wording used.
```

Raw data: `results/calibration_api.jsonl` (API plane, 72 calls, 0 errors),
`results/calibration_ui_logged_out.jsonl` (logged-out UI plane, 12 manually-collected
records).

## License

Code MIT. This data and analysis are CC-BY-4.0 — cite it, quote it, build on it, with
attribution. See `LICENSE`.
