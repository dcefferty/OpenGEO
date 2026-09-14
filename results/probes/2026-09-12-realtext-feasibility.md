# Probe: real public-domain text as the route to a rankable corpus (item 11)

> **Correction, 2026-09-13 — the probe documents are not verbatim federal text.**
>
> This note and its builders described every excerpt as verbatim US federal text. It is
> not. Building item 11's sourcing tools, each probe document was checked against a saved
> snapshot of its source page (`corpus/sources.py`; six CDC pages that block non-browser
> clients were checked inside a real browser against the rendered page instead):
>
> | | documents |
> |---|---|
> | verbatim | **2** — `cfpb_score`, `ftc_free` |
> | not verbatim | **23** |
> | not mechanically checked | 1 — `odphp_cutdown`, a PDF, and edited on inspection |
>
> The failures were introduced while assembling the corpus, not by the source pages:
>
> - **Sentences written to reach a target length** and attributed to the agency — in most
>   documents. `nhanes_1516` closes with editorializing that appears nowhere in its source.
> - **Edits to real sentences** — contractions expanded, parentheticals such as "(mg)" and
>   "(DGA)" dropped, "40° F" spelled out, list items joined with commas.
> - **One edit that changes meaning.** USDA ERS writes "*On average,* all adults aged 20 and
>   over consume more added sugars than recommended." The excerpt dropped "On average,",
>   turning a claim about a mean into a claim about every adult.
> - **Sentences built from tables or summaries** — `fda_howto` turns a Daily Value table
>   row into prose; `nhlbi_dash` was composed almost entirely.
>
> **What this does and does not change.** The facts in the documents are real and on the
> source pages; the wording is not the agencies'. The mechanism findings below rest on
> whether a document answers the question and on how many do, which the edits did not
> change, so they are likely to hold — but they were measured on government-derived
> text with authored additions, not on the federal text this note claimed. Item 11's
> screening runs on text that passes the verbatim check, and serves as the replication.
>
> The document text is left exactly as run: the committed results were produced from it,
> and all six corpus hashes are unchanged by this correction. **Do not reuse these
> excerpts as source text.**

**2026-09-12. Not a round.** No hypothesis was pre-registered and nothing here is a
finding about GEO. These are design probes: they ask whether a corpus built from real
federal text can produce the citation regime ROADMAP item 11 needs, before anyone spends
weeks building one.

Three probes:

| probe | domain | design | question |
|---|---|---|---|
| 1 | nutrition | 6 vs 10 candidates | How much added sugar should an adult eat in a day? |
| 2 | finance | 6 vs 10 candidates | How long does negative information stay on my credit report? |
| 3 | nutrition | **10 candidates fixed, 5 vs 9 answering** | (same as probe 1) |

720 calls, 0 errors, ~$0.90. Reproduce with:

```bash
python3 corpus/build_corpus_realtext_probe.py       # probe 1, N=6 and N=10
python3 corpus/build_corpus_realtext_probe2.py      # probe 2, N=6 and N=10
python3 corpus/build_corpus_realtext_probe3.py      # probe 3, both arms at N=10
# four run_pilot.py invocations, --conditions control --runs 24, five-engine panel
python3 analyze_probe.py
```

## The question

Every corpus in this repo has exactly one document that answers, so citation measures
*presence*, the treatment arm sits at CPR 0.998, and every tactic would tie at 1.000.
Item 11 needs the opposite regime — candidates that all answer, so citation measures
*preference*.

## Verdict

**Viable, but only for a specific class of question — and the first probe's conclusion
was wrong.**

Probe 1 alone said: use ten candidates instead of six, because per-document CPR fell from
0.778 to 0.561. Probe 2 falsified that as stated. Recording it because acting on one
probe would have sent the corpus work down the wrong path.

### 1. The lever is the number of documents that ANSWER, not the number of candidates

**Probe 3 tests this directly.** Probes 1 and 2 each confounded candidate count with
answering count. Probe 3 holds candidates at ten and varies only how many answer, with
five answering documents and one filler appearing in both arms unchanged:

| document | answers | arm A (5 answering) | arm B (9 answering) | change |
|---|---|---|---|---|
| fda_label | direct | 1.000 | 1.000 | +0.000 |
| cdc_facts | direct | 0.783 | 0.742 | −0.042 |
| nhanes_1516 | direct | 0.808 | 0.592 | −0.217 |
| usda_ers | direct | 0.842 | 0.442 | **−0.400** |
| cdc_drink | direct | 0.233 | 0.183 | −0.050 |
| **cdc_sodium** | **none** | **0.000** | **0.000** | **+0.000** |

Mean change across the five shared answering documents: **−0.142** (−0.177 excluding
`fda_label`, which is pinned at 1.000 in every run of every probe). Negative on all five
engines. The shared filler moved by exactly zero — **non-answering candidates are inert,
not merely weak.**

Dilution acts hardest on the middle. The document at the ceiling and the one near the
floor barely moved; the mid-range documents moved 0.217 and 0.400. That is convenient,
because the middle is the only part item 11 can use.

This also makes the answering count a **tuning knob for baseline placement** —
`METHODOLOGY.md` §5.2's standing lesson is that baseline placement dominates sample size,
and for a real-text corpus this is the lever that sets it.

### 1b. Why the earlier probes disagreed

| probe | candidates | answering | cites per answer | cites as share of answering set |
|---|---|---|---|---|
| 1 | 6 | 6 | 4.67 | 78% |
| 1 | 10 | **8** | 5.61 | 70% |
| 2 | 6 | 5 | 4.36 | 87% |
| 2 | 10 | **5** | 4.55 | 91% |

Probe 1 went from six candidates to ten *and* from six answering documents to eight. The
same six documents lost 0.100 of citation rate. Probe 2 went from six candidates to ten
while the answering count stayed at five — and the same six documents did not lose
citations at all (+0.014).

Engines cite 70–91% of the documents that answer and ignore the rest. Diluting
per-document CPR therefore requires finding more documents that genuinely answer, which
is the hard part, not padding the candidate set, which is the easy part.

### 2. Citation is bimodal, and whether a usable middle exists depends on the question

| | probe 1 | probe 2 |
|---|---|---|
| documents answering directly | 0.650 | **0.888** |
| documents topically adjacent | 0.204 | **0.022** |
| usable as a target (pinned on no engine) | 3 of 10 | **0 of 10** |

Probe 2 has no middle whatsoever. Its five answering documents sit at 0.71–0.97 and its
five adjacent ones at 0.00–0.07; every one is pinned at a ceiling or a floor on at least
one engine. A tactic has nothing to move.

**The difference between the probes is whether the sources disagree.** Probe 2's sources
all say the same thing — seven years, ten for bankruptcy — so each document is either
fully responsive or irrelevant. Probe 1's sources disagree about the *form* of the
answer: less than 10% of calories (FDA), no more than 10 grams per meal (CDC), 5.95
teaspoons per 1,000 calories (USDA ERS), 6.7 teaspoon equivalents (NHANES). That
disagreement creates partial relevance, and partial relevance is the graded middle item
11 needs.

**This is the binding corpus criterion, and it is not the one item 11 assumed.** Pick
questions where authoritative sources differ in framing. A question with one canonical
answer that every source states identically is unusable, however many documents you find.

### 3. The canonical best answer saturates and cannot be the target

Probe 1's FDA page — "less than 10 percent… 50 grams" — was cited in **120 of 120 runs on
every engine at both set sizes.** Probe 2's two cleanest answers sit at 0.97 pooled,
pinned on three and four engines. Targeting the best document guarantees a null.

Target selection therefore needs a screening run per question, then a pick from the
movable rows. It costs ~120 calls (~$0.15) and is the same shape as the spot check the
repo already mandates. On probe 2 the screen returns nothing, which is the correct
outcome: that question should be discarded before a round is designed around it.

### 3b. More answering documents does NOT widen the usable target window

This is the finding that most constrains item 11, and probe 3 is what exposed it.

| probe | answering documents | usable as target |
|---|---|---|
| 2 | 5 of 10 | **0 of 10** |
| 1 | 8 of 10 | 3 of 10 |
| 3 arm B | 9 of 10 | **2 of 10** |

Going from eight answering documents to nine lowered mean per-document CPR as predicted —
and left *fewer* usable targets, not more. Dilution does not open the window; it slides
documents through it.

**The cause is the engine split.** Citations per answer in probe 3 arm B:

| engine | cites of 10 |
|---|---|
| grok-4.3 | 7.62 |
| deepseek-chat | 7.08 |
| gemini-3-flash | 6.88 |
| gpt-5.4-mini | 4.08 |
| claude-haiku-4.5 | 3.58 |

Inclusive engines cite nearly everything that answers, pinning documents near 1.00.
Selective engines cite roughly a third, pinning them near 0.00. A document has to sit
inside both windows at once, and adding answering competitors pushes it down — out of the
inclusive engines' ceiling, but into the selective engines' floor. In arm B, `usda_ers`
lands at 1.00 on grok and 0.21 on gpt; `cdc_smart` at 1.00 on gemini and 0.08 on gpt.

**This does not block item 11, because a round needs only one target per question.** Two
or three usable documents out of ten is sufficient — you pick one and vary it by tactic.
It does mean the screening run is mandatory rather than advisory, and that some questions
are discarded. Across the three probes, two of three questions yielded at least one usable
target, so budget roughly 1.5 screened questions per usable one: for a 48-prompt corpus,
about 72 screens at ~$0.15, or ~$11 total.

### 4. Position effects do not scale with set size

Probe 1 showed PSI 0.258 across 6 slots rising to 0.300 across 10, which looked like
position mattering more in bigger sets. Probe 2 went the other way — 0.125 at six slots,
0.108 at ten. The apparent scaling does not replicate and should not be planned around.

## What replicated cleanly

- **Sharp discrimination on answer directness.** 3.2× in probe 1, 40× in probe 2. When
  documents answer, citation stops being a coin flip. This is the premise item 11 rests
  on and it holds in both domains.
- **Sourcing and licensing.** US federal works are public domain (17 U.S.C. §105), so
  *verbatim* excerpts ship under this repo's CC-BY-4.0 without conflict. (Authored
  additions are not federal works — one more reason the correction above matters.) Wikipedia and Stack
  Overflow are CC-BY-SA, whose share-alike would force a relicense of the dataset.
- **The inversion.** Prior builders pick a question and write documents to answer it.
  With real text that is impossible — you cannot find real pages answering a question you
  invented. Finding a cluster of overlapping real documents and deriving the question
  from them worked on the first attempt in both domains.

## Operational findings

- **Sourcing friction is real.** `nhtsa.gov` and `myplate.gov` return 403 to automated
  fetches; `studentaid.gov` timed out on 3 of 4 attempts; several agency PDFs are
  image-based and yield no text. Working: `fda.gov`, `cdc.gov`, `ers.usda.gov`,
  `ncbi.nlm.nih.gov`, `consumerfinance.gov`, `consumer.ftc.gov`, `fdic.gov`,
  `fueleconomy.gov`. A 48-prompt corpus needs bulk or archival sourcing, not ad-hoc
  fetching.
- **Finding enough answering documents is the constraint.** Probe 1 yielded 8 from a
  heavily-covered topic; probe 2 yielded 5. Getting to 10 genuinely-answering documents
  per question, across 48 questions, is the real cost of this route.
- **Format collapses.** Real federal text is uniformly reference/docs register. H5's
  format dimension (η²=0.062, product 0.717 vs blog 0.357) does not survive the move to
  public-domain government sources, which have no "product" or "forum" equivalent.

## What this does not establish

Two questions, two domains, 24 runs per cell, one screening panel. The
answering-count mechanism rests on a two-probe contrast, not a designed experiment that
varies answering count while holding candidate count fixed — that is the obvious next
probe and it is cheap. Documents added at N=10 are shorter than the originals in both
probes (53–71 vs 63–71 words in probe 1), which H7 showed is not free on three engines.
Treat every number here as a design input, not a measurement.
