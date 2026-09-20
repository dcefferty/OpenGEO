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
