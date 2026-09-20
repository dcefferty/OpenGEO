# Page-length screen — does a full-page candidate field saturate?

**Committed before collection, 2026-09-20.** A screening run, not a round: control text
only, no tactic arms, no hypothesis test, no published effect size.

## Why

The tactic pilot and the length ladder both ran on a field of 12–104 word snippets with
one longer target, and both lost usable cells to saturation. The ladder's phase-1
deviation named the cause: clean nesting requires the answer at every rung, a document
containing the answer is a strong answer, and the inclusive engines cite strong answers
almost always — gemini sat at 1.00 on every rung of two questions. Lengthening the target
alone cannot fix that, because it makes the target *more* conspicuous, not less.

This probe changes the field instead. Every document is a 252–345 word page section, which
is closer to what an answer engine actually synthesises from: real retrieval returns pages,
not sentences. The question is narrow and prior to any tactic:

    does a page-length candidate field sit at usable citation rates, or does it saturate?

## Risk, stated in advance

Longer candidates answer more completely, and "every document fully answers" is exactly
what gave probe 2 zero usable targets out of ten. Against that, a page-length field may
make engines cite *fewer* documents per answer — two or three instead of five — which
would push per-document rates down and unpin the field. Which force wins is the empirical
question and the honest prior is near even.

## Corpus

`pagelength-screen-v1`, sha256 `064dd9e715a265b8`, built by
`corpus/build_corpus_pagelength.py`. 23 documents over 3 questions, contexts of
1,930–2,363 words (~2,876 input tokens per call, against ~843 measured on the prior
corpora). 360 calls at 5 engines × 24 runs.

All three questions are already held out of the round by the pilot or the ladder, so this
probe costs no new corpus.

Spans are contiguous runs of each committed snapshot, anchored explicitly in the builder
so a page changing underneath fails the build. The selection rule matters: among runs of
250–600 words mentioning the question's terms, take the **earliest** on the page, not the
best-matching. Picking each page's most answer-like passage would manufacture the
saturation this probe exists to detect.

**Deviation: `home_smokealarm` runs at 7 candidates, below the 8+ rule.** Replacements
could not be sourced — cpsc.gov and cdc.gov/fire-safety return HTTP 403 to automated
fetching, the Internet Archive CDX index is returning HTTP 0, and NFPA is not a federal
work. The deviation is conservative here: the 8+ rule exists because 4–6 candidates pin
everything, so 7 biases *toward* saturation. If the field unpins at 7 the result is
robust. Three documents were dropped for having no 250-word run at all
(`hud_dti_archive` 160w of prose, `usfa_prepare` 50w, `nhlbi_stress` 144w).

## Baseline to beat — the same three questions as snippets

Computed from the committed screening runs before this probe was collected:

| question | docs | usable targets | unpinned cells | cites/answer |
|---|---|---|---|---|
| `finance_housingshare` | 9 | 1 | 18/45 (40%) | 5.65 |
| `home_smokealarm` | 8 | 1 | 14/40 (35%) | 4.52 |
| `health_bloodpressure` | 8 | 1 | 11/40 (28%) | 3.88 |
| **total** | 25 | **3** | **43/125 (34%)** | |

A cell is unpinned when its citation rate is inside [3/24, 21/24]. Counts are compared as
fractions because the smokealarm deviation changes its denominator.

## Pre-committed reading

- **UNPINS** — unpinned-cell fraction ≥ 45%, and at least 2 of 3 questions yield a usable
  target under `screen.py`'s existing rule → the page-length rebuild is justified. Item 11
  proceeds on a rebuilt corpus, and the tactic probe is re-run in that regime before any
  round is sized.
- **SATURATES** — unpinned fraction ≤ 25%, or at most 1 question yields a usable target →
  probe 2's failure mode arriving from the other direction. Item 11's ranked table is not
  obtainable in Tier 1 by either route, snippets or pages. Publish the scope finding.
- **NEUTRAL** — anything between → page length is not the lever. No rebuild; the decision
  falls back to banking the Tier 1 scope finding and going public.

Secondary, and the mechanism to watch either way: **cites per answer**. If a page-length
field works by making engines cite fewer documents, this should fall below the snippet
values above. If it rises or holds while rates saturate, the extra content is simply making
every document citable.

---

# Results — collected 2026-09-20

360 calls, **0 errors**, 0 `model_returned` mismatches. Runs in
`results/pagelength_screen.jsonl`.

| question | regime | docs | usable targets | unpinned cells | cites/answer |
|---|---|---|---|---|---|
| `finance_housingshare` | snippet | 9 | 1 | 18/45 (40%) | 5.65 |
| | **page-length** | 8 | **2** | **19/40 (48%)** | 5.03 |
| `home_smokealarm` | snippet | 8 | 1 | 14/40 (35%) | 4.52 |
| | **page-length** | 7 | **0** | **9/35 (26%)** | 5.77 |
| `health_bloodpressure` | snippet | 8 | 1 | 11/40 (28%) | 3.88 |
| | **page-length** | 8 | **0** | **8/40 (20%)** | 3.71 |
| **total** | snippet | 25 | **3** | 43/125 (34%) | |
| | **page-length** | 23 | **2** | 36/115 (31%) | |

## Verdict: SATURATES

The committed rule fires on its second branch — *at most 1 question yields a usable
target*. **1 of 3 does**, against 3 of 3 as snippets. The unpinned-cell fraction (31%)
happens to land in the neutral band, but it moved the wrong way and the question-count
branch is unambiguous: the UNPINS branch required both ≥45% and ≥2 questions, and neither
holds.

**The hypothesised mechanism did not operate.** Page length was supposed to work by making
engines cite fewer documents per answer. Cites per answer did not fall — 4.68 → 4.84 on
average, up on one question and down on two. Engines kept citing about the same number of
documents; there were simply fewer documents in the middle to choose from.

## What actually happened: the middle disappeared

The distributions polarise. `health_bloodpressure` at page length:

| document | pooled rate |
|---|---|
| `fda_bp` | 1.00 |
| `cdc_hbp` | 0.95 |
| `nhlbi_sym` | 0.86 |
| `nhlbi_hbp` | 0.78 |
| `nia_bp` | 0.07 |
| `nhlbi_diag` | 0.03 |
| `niddk_bp` | 0.01 |
| `nhlbi_causes` | 0.01 |

Four documents above 0.78, four below 0.08, nothing between. `home_smokealarm` collapsed
entirely to one end: every document lands at 0.93–0.99.

**The graded middle is an artefact of truncation.** A 30-word snippet is a *partial*
answer, and partial answers earn intermediate citation rates. A 300-word page section
either contains the answer or does not, and engines treat it accordingly. The rankable
regime this whole item depends on — several documents answering, citation measuring
preference rather than presence — exists because the documents were cut short.

That is the finding, and it is worse for item 11 than a null. The regime needed to rank
tactics is not a property of the content; it is a property of how severely the content was
truncated. Measuring tactics in it would measure something that does not correspond to how
an engine sees a real page.

## Honest limits

Three questions, one carrying a logged 7-candidate deviation, and one question
(`finance_housingshare`) actually **improved** — 40% → 48% unpinned, 1 → 2 usable targets.
The effect is not uniform, and a page-length corpus built from richer, more varied sources
might screen better. This probe does not exclude that.

What it does establish is that the page-length rebuild is not the cheap fix the ladder's
deviation suggested. Two of three questions lost their target entirely, and the mechanism
that was supposed to make it work did not fire.

## Consequence

Item 11's ranked table is not obtainable in Tier 1 by either route tested. Snippets give a
gradeable field that is an artefact of truncation; pages give a faithful field with no
gradeable middle. Combined with the tactic pilot (four tactics at resampling noise) and
the length ladder (suggestive at best, and contradicted by its own mechanism contrast),
three probes now point the same way.

The result to publish is the scope boundary, which is a real and useful finding: at the
synthesis stage, with retrieval held constant, what moves citation is whether a document
answers the question (+0.48, H4) — not how the answer is presented. Presentation tactics
are a Tier 2 question (ROADMAP item 9), because their causal path runs through the
retrieval stage this design holds constant by construction.
