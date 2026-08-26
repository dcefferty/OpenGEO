# OpenGEO — Corpus v0.4 Exploratory Run

**Published 2026-08-25. NOT PRE-REGISTERED.**

This round is published as strong confirmatory evidence, explicitly **not** as a
pre-registered finding. Per this project's own credibility standard (see `CLAUDE.md`,
`ROADMAP.md` item 6), a round without a pre-registration committed before collection does
not get to call itself "Round 1," no matter how clean the result looks in hindsight. That
label is reserved for the next genuinely new intervention, run under a pre-registration
committed before any data exists. Treat everything below as evidence worth taking
seriously, not as a citable finding.

## What this tests

Does extractable-claim density — specific figures and quantities in place of generic,
unquantified phrasing — causally raise the odds that an AI answer engine cites a document,
holding retrieval constant? This is the specificity claim made throughout the GEO industry
(see `METRICS.md` for the full argument and sourcing), tested here as a controlled,
paired intervention rather than an observational correlation.

## Design

| | |
|---|---|
| Corpus | v0.4, `corpus/corpus_v0.4.json`, sha `f1d0672d1d295a66` |
| Prompts | 48, across 24 domains (2 each) |
| Documents | 6 per prompt, one per format: blog, news, docs, product, forum, reference |
| Target format balance | exactly 8 prompts per format |
| Conditions | paired — only the target document differs between control and treatment; the other 5 are byte-identical |
| Models | 8, via OpenRouter: `claude-haiku-4.5`, `gpt-5.4-mini`, `gemini-3-flash-preview`, `grok-4.3`, `kimi-k2`, `deepseek-chat`, `llama-4-maverick`, `mistral-medium-3` |
| Runs per cell | 24 |
| Temperature | 1.0 (the model's natural distribution, not lowered for stability) |
| Document order | randomized per run from a seeded hash, recorded every run |
| Total calls | 18,432, 0 final errors (see Data Health) |
| Raw data | `results/runs_v0.4.jsonl`, git commit `b5b7092` |

Retrieval is held constant by construction — documents are supplied directly in context.
This measures the synthesis stage only: what a model does with content it already has, not
whether that content gets retrieved in the first place.

## Headline result — H4: claim density → citation

**Pooled across all 8 models: control CPR 0.503, treatment CPR 0.985, delta +0.482, 95% CI
[+0.404, +0.563], p<0.0001.** Individually significant for every model, including
`kimi-k2` (delta +0.491, p<0.0001), which has a known instruction-following weakness (see
Limitations) but is not required for this result to hold.

| Model | Control CPR | Treatment CPR | Delta | 95% CI | p |
|---|---|---|---|---|---|
| claude-haiku-4.5 | 0.383 | 0.997 | +0.614 | [+0.510, +0.715] | <0.0001 |
| deepseek-chat | 0.591 | 0.999 | +0.408 | [+0.303, +0.510] | <0.0001 |
| gemini-3-flash-preview | 0.631 | 1.000 | +0.369 | [+0.270, +0.470] | <0.0001 |
| llama-4-maverick | 0.387 | 1.000 | +0.613 | [+0.514, +0.708] | <0.0001 |
| mistral-medium-3 | 0.565 | 1.000 | +0.435 | [+0.337, +0.530] | <0.0001 |
| kimi-k2 | 0.405 | 0.896 | +0.491 | [+0.402, +0.577] | <0.0001 |
| gpt-5.4-mini | 0.447 | 0.998 | +0.551 | [+0.447, +0.654] | <0.0001 |
| grok-4.3 | 0.615 | 0.993 | +0.378 | [+0.281, +0.473] | <0.0001 |
| **All models pooled** | **0.503** | **0.985** | **+0.482** | **[+0.404, +0.563]** | **<0.0001** |

This is not what the same corpus design found at v0.2 scale. The original 12-prompt
pre-registered pilot on this project's earlier corpus design found H4 **null** (pooled
delta +0.001, CI included zero) — because control-condition CPR sat at a near-ceiling
0.867, with 67% of (prompt, model) cells at a literal 100% citation rate. Broad questions
("what should I look for in X") let every one of 6 candidate documents answer *something*,
so citation stopped discriminating on content at all. Corpus v0.3 and v0.4 fixed this by
narrowing each question to one specific fact and rewriting control documents to share no
topical surface — not just the literal number — with that fact. See `ROADMAP.md` items 5b
and 6 for the full diagnosis and the two distinct failure modes that surfaced during
validation.

## The other hypotheses — published with equal prominence, including the null

| H | Result | Verdict |
|---|---|---|
| H1 — reliability at n=24 | Spearman-Brown ≥0.957 for every model; pooled reliability is "usable" even at n=4 | Supported |
| H2 — position effect (PSI) is material | Mean PSI 0.066, but η²=0.001 for slot vs. η²=0.305 for condition | Supported by the letter of the pre-registered magnitude test, but position is a minor factor next to claim density in this corpus |
| **H3 — cross-model agreement on citation-worthiness is low** | Cross-model Kendall's W 0.803 vs. within-model noise floor 0.772 (gap −0.031) | **Not supported.** Models agree with each other about as much as they agree with themselves — this cuts against the "each engine is its own optimization problem" narrative common in GEO marketing. |
| H5 — format × model interaction dominates main effects | η²(interaction)=0.010 vs. η²(format)=0.021, η²(model)=0.018 | Supported (interaction does not dominate) |

H3 is the one worth reading twice: it's a genuine null on a hypothesis this project
expected might hold, and it's published exactly as prominently as the positive H4 result,
per this project's own stated principle that a benchmark reporting only wins is a
marketing site.

## Variance decomposition — where the effect actually lives

| Factor | η² | Levels | Range |
|---|---|---|---|
| Condition (claim density) | **0.305** | 2 | 0.503–0.985 |
| Prompt | 0.106 | 48 | 0.510–0.987 |
| Domain | 0.054 | 24 | 0.538–0.914 |
| Content format | 0.021 | 6 | 0.656–0.838 |
| Model | 0.018 | 8 | 0.650–0.816 |
| Target slot (position) | 0.001 | 6 | 0.728–0.755 |

Claim density is, by a wide margin, the largest single driver of citation variance in this
corpus — larger than which model answered, which document format was used, or where the
document sat in the context window.

## Limitations

- **Not pre-registered.** State this every time this data is cited.
- **Synthesis stage only.** Retrieval is held constant by design; this says nothing about
  whether a page gets retrieved in the first place. See `METHODOLOGY.md` §2 for the
  two-tier argument.
- **`kimi-k2` has an elevated no-cite rate** (13.3% of runs produced no parseable
  citation, vs. 0–3.3% for every other model) — an instruction-following weakness, not a
  low-visibility signal. It is reported individually above rather than silently averaged
  in, and the pooled H4 result does not depend on it.
- **The corpus was authored, not sampled from the wild.** All 288 documents were written
  for this benchmark, following a documented construction method (`corpus/build_corpus.py`).
  This is what makes the paired design possible, at the cost of not being a random sample
  of real web content.
- **Format is nested within prompt** (8 prompts per format) — the H5 interaction test
  cannot fully separate "format" from "these specific prompts." See the CAVEAT printed by
  `analyze.py`'s H5 section for the exact statement.

## Reproducing this

```bash
python3 corpus/build_corpus.py                                  # regenerates corpus_v0.4.json; verify sha matches f1d0672d1d295a66
python3 analyze.py --runs results/runs_v0.4.jsonl --corpus corpus/corpus_v0.4.json
```

Raw data (`results/runs_v0.4.jsonl`) and corpus (`corpus/corpus_v0.4.json`) are committed
at git commit `b5b7092` and after. Every run record carries full provenance: model,
`model_returned` (checked against silent OpenRouter reroutes), presentation order, target
slot, condition, and the raw response text — not just extracted citations.

## License

Code MIT. This data and analysis are CC-BY-4.0 — cite it, quote it, build on it, with
attribution. See `LICENSE`.
