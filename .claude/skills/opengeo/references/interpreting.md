# Explaining a result

Read this before explaining an `opengeo test` result. The numbers are careful; the easiest
way to undo that is to explain them loosely.

## What each part of the output means

**The verdict** comes from the pooled 95% interval across engines and a permutation test of
the same figure. The two agree except close to the line:

- **raised** — the interval is entirely above zero, and the permutation test agrees. The
  edit made citation more likely, for this question, against these competitors.
- **lowered** — entirely below zero, and the test agrees. The edit made citation *less*
  likely. Say so plainly; it's as useful a result as an improvement, and people miss it when
  it's softened.
- **borderline** — the two disagree. Treat it as unproven, and don't round it up to
  "raised": more questions are what settle it.
- **no detectable change** — the interval includes zero. This is a real result, not a failed
  test: the test couldn't tell the edit apart from no change. It doesn't prove the edit does
  nothing, only that any effect is too small to see with this much data.

**How likely chance is** is stated for each result: how often an edit that did nothing would
show a difference this large ("less than 1 time in 1,000", or "about 1 time in 40"). Relay
that sentence rather than a blanket "1 in 20", which describes the 95% bar, not the result.

**Points** are percentage points of citation rate. "+33 points" means that out of every 100
answers, about 33 more cited the page. Not "33% better" — that would be a different and
larger-sounding number.

**The interval** — "95% CI +21 to +45" — is the range the true change plausibly falls in. A
wide one means uncertain, a narrow one means precise. When it's wide, say that rather than
leading with the point estimate.

**"Held on N of 5 engines"** counts engines whose own interval clears zero in the same
direction as the overall result and whose own permutation test agrees. A result that holds
on five engines is more robust than one carried by one or two — and a single engine at 24
runs per version can't separate, say, 83% from 100% with confidence, so an engine that moved
the right way without holding is "not shown on its own", not "no effect". When the user
cares about one engine, ChatGPT especially, say plainly whether that engine held.

**The markers:**

- `^ ceiling` — the edited page was cited in almost every run on that engine, as high as the
  test can measure. It shows the edit got the page cited every time against *these*
  competitors, not how it would do against pages that also answer the question. Common when
  an edit adds a specific answer the page was missing.
- `* no room` — the current page was already cited almost every time on that engine, so
  there was little room to show any improvement there. A small change on that engine means
  little either way.
- An engine **left out** of the pooled figure cited nothing in too many answers even when
  the edited page was present — a failure to follow instructions, not a visibility signal.
  An engine that only cites nothing when *no* page answers is abstaining, which is correct
  behaviour, and is kept.

**A question marked "not tested"** had a current page already cited so often that there was
no room for an edit to show an improvement, so its edited version was never run. That isn't
a failure: their page is already doing well on that question. Suggest a question where their
page isn't the obvious answer yet.

## The ways results get over-read

Watch for these in your own explanation as much as in the user's reading of it.

**Generalising from one question.** A single question is a single question. Chance and
scope are separate worries, so keep them apart. On chance, the output says how often an
edit that did nothing would show a difference this large: a clear result is very unlikely
to be chance, and a narrow one deserves confirming. On scope, even a result that is surely
real describes this question against these competitors, and says nothing certain about
the user's other questions or pages. The honest next step
after one good result is testing three to five more questions, not rewriting the site. If
they ran several, the "across questions" summary is the part that speaks to their site more
broadly; below 25 questions it's still a rough estimate.

**Reading it as "AI will find me now."** The test hands the page to each engine directly.
It measures what happens *once an engine has the page* — not whether an engine will find,
retrieve or recommend it in the first place. For many small businesses, being found is the
bigger problem, and this doesn't measure it.

**Reading a ceiling as "at least".** With `^` markers the edited page was cited every time,
so the change shown is how much room there was, not how strong the edit is. Don't say "at
least" or promise the same gain elsewhere: against competitors that also answer the
question, the same edit could gain less.

**Treating the result as permanent.** Engines change their models and behaviour. The
results folder contains everything needed to re-run the identical test later — `corpus.json`
and `manifest.json` — which is how to check whether it still holds.

**Turning the result into advice for other pages.** It describes this edit, on this page,
against these competitors. If the user wants to apply the same kind of change elsewhere,
that's something to test there too.

## After explaining

Offer what would genuinely tell them more — more questions, a different edit, other
competitors — and let them choose. Suggesting what to test next is fine; telling them what
their page should say is the line this skill doesn't cross.
