# Real-text H4 round — design note

**Not a pre-registration.** This records the design decisions and the reasoning behind
them, so that the pre-registration committed before collection can cite a design that was
settled first. Written 2026-09-23.

## Why

Of the eight public findings, **seven rest on synthetic authored documents. The one built
on real verbatim text is a null.** That sentence is true as written, and a reader will
write it. The real explanation — the null tested presentation tactics, an entirely
different hypothesis — is a defence, and defences are weaker than evidence.

This round replicates **H4** (replacing vague claims with specific figures raises citation)
on documents nobody associated with this project wrote.

## What cannot be reused, and why

`corpus/sources/` holds 175 snapshots over 123 rights-cleared pages. Almost none of it
fits. Item 11 sourced pages that **answer** its questions, because the rankable regime
needs several answerers competing. H4 needs the opposite: six topically adjacent documents
of which **none** answers the question's specific facts, so that the treatment arm's single
answering document is the only thing that changed.

Counting `partial` and `none` together, only **2 of 16** item-11 questions have six
non-answering documents. The material is the wrong shape and is not forced into it.

The direction of difficulty reverses, which is the useful part: item 11's bottleneck was
finding pages that state a specific figure, which is rare. Here the requirement is pages
that discuss a topic *without* stating it, which is most of the web.

## Design

| | |
|---|---|
| Structure | 6 documents per question; 1 target with two variants, 5 identical across arms |
| Conditions | `control`, `treatment` — the H4 contrast, unchanged from v0.3/v0.4 |
| Target control | a **verbatim** span of a real page, topically adjacent, answering none of the question's facts |
| Target treatment | the same span with the specific figures inserted — an authored edit, declared |
| Non-targets | verbatim spans of five further real pages, non-answering, identical across arms |
| Document length | 50–110 words, matching v0.3/v0.4 |
| Models | the five-engine market panel |
| Runs per cell | 24 |
| Target size | 25 questions; 12 is the interim milestone |

### Three decisions worth stating

**1. Only the control arm can be verbatim, and that is correct rather than a compromise.**
The intervention *is* an edit. A design where both arms were verbatim would have to compare
two different pages, which breaks the pairing that makes every round in this project
causal. So: control is the page as it exists, treatment is that page with figures added.
That is exactly the action a practitioner takes, and it is declared per document rather
than glossed.

**2. The inserted figures must be true and attributable.** A treatment arm carrying
invented numbers would measure whether engines reward *fabricated* specificity, which is a
different and much less useful question — and would make the corpus unpublishable as a
reference. Every inserted figure is sourced from an authoritative page recorded alongside
the document, even though the sentence carrying it is authored.

**3. Length regime matches v0.3/v0.4 rather than the page-length regime.** The claim under
test is "H4 replicates on real text". Moving to page-length documents at the same time
would change two variables at once, and the page-length screen showed that regime behaves
differently — real page sections polarise, most documents either always cited or never
(`results/probes/2026-09-20-pagelength-screen.md`). Matching the established length keeps
the comparison to +0.482 and +0.493 clean. Page-length is a separate follow-up, not a
confound folded into this one.

## Question selection

Item 11 chose heavily-covered questions so that many pages would answer. This round wants
the reverse: **questions whose specific answer is uncommon in real content**, so that six
topically adjacent non-answering pages are readily available and the control lands
mid-range rather than at a ceiling.

Domains are drawn from v0.4's own twenty-four, so a difference against v0.4 cannot be a
domain effect. One question per target format per batch, as in every corpus here.

## The gate, and the risk it is guarding

Control-arm-only screening before the round is pre-registered, per §5.3, and the bar is
§9's: pooled control CPR in [0.25, 0.75] per question.

**The risk is real and was measured recently.** The page-length screen found that real
documents polarise — at 252–345 words, four documents sat above 0.78 and four below 0.08
with nothing between, and one of three questions kept a usable target. Shorter spans may
behave differently, since a short excerpt is a partial answer where a full page is not, but
that is a hypothesis rather than a result. **If real text cannot place a control mid-range
at this length, the round does not run**, and that failure is itself reportable: it would
say the synthetic corpora are load-bearing for the finding, not decorative.

## What this round does not fix

**H4's delta is mechanically `1.0 − control`.** The treatment arm saturates in every round
this project has run, so the headline number is largely a statement about where the control
sits, which is a corpus construction choice (§9). Replicating on real text tests whether
that construction is *achievable without authoring the documents* — a real and necessary
check — but it does not identify the effect's true magnitude. The write-up states this
rather than defending the delta, and reports the control baseline as the quantity of
interest alongside it.

## Amendments after the first sourcing pass (2026-09-23)

**1. The six-format structure cannot be replicated on public-domain sources, and the round
drops it.** v0.4 gives every question one document in each of blog, news, docs, product,
forum and reference. Across all 175 real documents item 11 ever built, only four registers
appear — reference 50, docs 48, news 24, blog 15 — and **never `product` or `forum`**.
Federal agencies do not publish product listings or forum posts, and a real one is not a
federal work, so it cannot be used under 17 U.S.C. 105 alongside this corpus's licence.

The round therefore uses six real documents per question **without format balance**, drawn
from the registers that exist. This costs nothing on H4, whose contrast is facts versus no
facts, but it means **this round cannot speak to H5 (content format)** and must say so.
That is itself a result worth reporting: the format dimension of the benchmark is not
testable on public-domain text at all, which bounds what any rights-clean corpus can
measure.

**2. Sourcing is currently throttled by two simultaneous outages.** A first pass over
twenty candidate URLs returned nine failures. `cdc.gov`, `nhtsa.gov`, `cpsc.gov`, `fda.gov`
and `energy.gov` refused automated requests (403/404), **and the Internet Archive CDX index
is returning HTTP 503/0**, so the fallback that normally covers exactly those refusals is
down too. Per-question yield was 3, 2, 2, 1, 1, 2 against the six needed.

Questions are therefore re-anchored on domains that fetch directly. Of 183 snapshots, 146
came via curl, and the domains that reliably answer are `consumerfinance.gov` (18),
`irs.gov` (16), `ssa.gov` (11), `nhlbi.nih.gov` (11), `fda.gov` (11), `odphp.health.gov`
(9), `tsa.gov` (7), `ftc.gov` (11 with `consumer.ftc.gov`), `epa.gov` (6),
`fsis.usda.gov` (5), `energystar.gov` (5), `fdic.gov` (5). `cdc.gov` is archive-only and is
unavailable while the outage lasts.

This is a scheduling constraint rather than a design flaw, and it is recorded because it
has now interrupted sourcing three times across two items. A corpus that depends on one
archive being up is fragile, and the fragility belongs in the limitations rather than in
anyone's memory.

## Sequence

1. Source and build batch 1, six questions, one per target format
2. Screen control-arm only — 6 × 5 × 24 = 720 calls, about $1
3. Repeat until 25 questions clear the gate; discard rather than re-tune twice (§9)
4. Pre-register, citing the screening evidence
5. Run: 25 × 2 × 5 × 24 = 6,000 calls, roughly $2–7
