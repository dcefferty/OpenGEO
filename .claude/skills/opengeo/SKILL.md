---
name: opengeo
description: Run a controlled experiment to test whether a change to a web page makes AI answer engines — ChatGPT, Gemini, Claude, DeepSeek, Grok — more likely to cite it, against the user's real competitors, using the OpenGEO benchmark's method. Use this whenever someone wants to know if editing their page, landing page, product page, docs or blog post will help it get cited, mentioned or recommended in AI answers, or asks whether a specific content change "works" for AI search. Trigger on phrasings like AI visibility, getting cited by ChatGPT, GEO, generative engine optimization, AEO, answer engine optimization, LLM SEO, "will AI recommend my business", or "does adding X to my page help with AI" — even if they never mention testing. Also use it when someone asks what actually works for getting cited by AI, because it carries the published evidence with its confidence levels. It measures what a change did; it does not audit pages or prescribe changes.
---

# OpenGEO: test whether a change gets a page cited more by AI

This skill runs `opengeo test`, which puts the user's page — as it is, and with their
change — among their competitors' pages, asks five AI engines the user's question 24 times
each, and measures whether the change moved how often the page gets cited. It's the same
paired, controlled design as every round OpenGEO has published, applied to one person's
content.

## The one line this skill doesn't cross

It measures what the user's change did. It never decides what the change should be.

That line is the whole point of the project. The AI-visibility market is full of tools that
score a page and sell a list of fixes; their conclusions can't be checked, and they profit
from the fixes. OpenGEO's value is that it is neutral and its numbers are reproducible.
The moment this skill starts telling people what their page should say, it becomes one more
vendor with an opinion, and its measurements stop being trustworthy.

So in practice:

- **Do** help the user test *their* idea, and turn it into a clean edit they approve.
- **Do** relay what the published evidence found, with how strong it is, and help them pick
  which of their ideas is worth testing first — framed as something to test, not a verdict.
  See `references/evidence.md`.
- **Don't** hand them a list of changes their page "needs", or present an untested tactic as
  proven.
- **Don't** invent facts to put in an edit. If they want to add their prices, get the real
  prices from them. A test built on made-up numbers measures whether engines reward
  fabricated specificity — and if they then publish it, they've published something false.

## Setup

Run these checks before gathering anything, because each one fails in a way that wastes the
user's time if it's discovered later.

1. **Find the tool.** `opengeo.py` lives at the root of the OpenGEO repository. If the
   current directory isn't that repo, ask the user where their copy is.
2. **Python with numpy.** The dry run needs only the standard library, but the real run
   analyses with numpy. Check with `python3 -c "import numpy"`. If that fails, try other
   interpreters on the machine (`python3.13`, `python3.12`), or suggest
   `pip install numpy`. Use whichever works for every command after this.
3. **The API key**, which must be in the environment as `OPENROUTER_API_KEY`. Check it
   without revealing it: `python3 -c "import os; print('set' if os.environ.get('OPENROUTER_API_KEY') else 'not set')"`.
   If it's missing, ask the user to add `export OPENROUTER_API_KEY=sk-or-...` to their
   shell profile and restart the session. **Never ask them to paste the key into chat, and
   never put it inside a command you run.** Commands can be saved: in this very project an
   approved command carrying a key inline ended up written into
   `.claude/settings.local.json`. The key belongs in their environment, nowhere else.

## The workflow

### 1. Pin down what's being tested

Get clear on the change the user has in mind and the question it's meant to help with.
"Add our prices" is a change; "how much does water heater replacement cost?" is the
question. If they only have a vague goal ("get cited more"), that's the moment to read
`references/evidence.md` and help them pick something specific to test.

### 2. Gather the four inputs

- **The question, or three to five of them.** Real questions their customers ask, in the
  customer's words. One question is fine to start, but the result then describes that
  question only — say so now rather than after they've paid.
- **Their page as it is now:** a URL or a saved file.
- **Their edited page.** If they already have one, use it. If they want help making it, see
  step 3.
- **Two to five competitor pages** that someone asking this question might also be shown.
  Four or five is better: every published round had five other documents. If they don't
  know who competes, suggest they try the question in an AI assistant or search engine and
  note who comes up — the tool deliberately doesn't discover competitors itself, because
  that would make the same test give a different answer next week.

A page that refuses automated requests (a 403, or almost no text because it's built with
JavaScript) can be saved from their browser with File > Save As and passed as a file.

### 3. Help draft the edit, if asked

The edit must be made against *exactly* the text the test will read, or the comparison sees
spurious differences throughout the page. So:

```bash
python3 opengeo.py fetch <their-page-url-or-file> --out opengeo-results/drafts/current.txt
```

Copy that to `opengeo-results/drafts/edited.txt`, make the user's change in the copy, and
show them the before and after of the part you changed. Get their approval before testing.
(`opengeo-results/` is gitignored, so drafts can't be committed by accident.)

Make only the change they asked for. Keep it within about three words of the original
length by *replacing* vague wording rather than adding to it, if that reads naturally — the
tool enforces this by default so a length change can't masquerade as an effect. If the
natural edit genuinely adds content, don't contort it: the test can run with
`--allow-length-change` (step 4 explains when that's fine).

### 4. Dry run, then ask

Always dry-run first. It runs every check and prices the test without sending anything:

```bash
python3 opengeo.py test --question "..." --page <current> --edit <edited> \
    --against <competitor1> <competitor2> ... --dry-run
```

Show the user the checks and the estimated cost, and **wait for a clear yes before running
for real.** It's their OpenRouter account. The cost is small — roughly $0.05–$0.15 per
question — but spending it is their call, and the dry run is also where problems surface
before any money moves.

If a check is marked ✗, the run is blocked. Explain it plainly and let them choose:

- **Length changed by more than three words.** Two honest options: rework the edit to
  replace wording instead of adding it, or add `--allow-length-change`. The flag is
  justified by evidence — OpenGEO measured doubling a page's length at +0.004, CI −0.023 to
  +0.031, so length alone doesn't move citation — and the report records that it was used.
  Let the user pick; don't add the flag on their behalf without saying so.
- **Fewer than two competitors.** With nothing to compete against, a page gets cited by
  default and the test says nothing.

### 5. Run it

Re-run the same command without `--dry-run` and with `--yes` (the user has already
approved the cost in conversation, and the tool's interactive prompt can't be answered from
here). One question is 240 calls and takes two or three minutes; several questions take
proportionally longer, so run it in the background if your environment allows and let the
user know roughly how long to expect.

If it's interrupted, re-running the identical command resumes where it stopped and sends
nothing that already succeeded. It never analyses a partial run — a result built on missing
data looks confident and isn't.

### 6. Explain the result

The tool prints a verdict, a per-engine breakdown and its own "What this means". Relay that
faithfully, show the chart (`chart.svg` in the results folder) if you can display files, and
then answer the user's follow-up questions without going beyond what the numbers support.
**Read `references/interpreting.md` before explaining a result** — it covers what each part
of the output means and the specific ways results get over-read.

Three things belong in almost every explanation:

- **One question is one question.** About 1 in 20 tests shows a change by pure chance, so a
  single result — however clean — is a reason to test more questions, not to rewrite a site.
- **It measures what happens once an engine has the page**, not whether an engine will find
  the page in the first place. Retrieval is held constant; that's what makes the result
  causal, and it's also its limit.
- **What to test next**, if they want to go further — never what to change.

## Where things live

In this skill's folder:

- `references/evidence.md` — how to relay the evidence without turning it into advice
- `references/interpreting.md` — how to explain a result without over-reading it

At the root of the OpenGEO repository:

- `opengeo.py` — the tool; `python3 opengeo.py test --help` lists every option
- `design/opengeo-test.md` — every default and the evidence behind it
- `results/findings.json` and `results/published/` — the published evidence, and the
  authority whenever it differs from the summary in `references/evidence.md`
