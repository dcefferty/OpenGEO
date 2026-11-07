#!/usr/bin/env python3
"""
OpenGEO corpus -- trust signals (trust-v1).

H4, H9 and H13 all varied *what a page says*. The most repeated GEO advice
after "add statistics" is about everything else: show a recent date, show an
expert author, and (from the other side) drop the marketing tone. None of it
has been measured causally. This corpus measures all three at once, without
changing a single fact on the page.

    control  -- corpus v0.4 `control`, verbatim: the vague target that answers
                neither of the question's facts. Pooled CPR 0.503 in v0.4 and
                0.565 in competition-v1, with 181 of 240 (prompt, engine)
                cells off the floor and ceiling there.
    fresh    -- the control with "Last reviewed and updated in October 2026."
                put in front
    stale    -- the same line with the year 2019
    byline   -- the control with "Written by <name>, <credential>." put in
                front; one fictional author per domain, credential matched to
                the domain
    promo    -- the control with a promotional line put in front (superlatives
                only, no claim of fact); one line per target format

Only the target differs between conditions. The five other documents are
v0.4's non-targets, byte-identical across all five conditions, so every
contrast is paired (CLAUDE.md, "Paired design").

**Length.** Each signal is one line of exactly seven words, placed before the
unchanged control text. The four signal arms are therefore length-matched to
each other exactly, and each is seven words longer than `control` (+9% to +21%
on targets of 33-78 words). H7 found that doubling a page's length moved
citation by +0.004 [-0.023, +0.031], so seven words is not expected to matter,
and `fresh - stale` differs by one token, the year.

Enforced at build time; the corpus is not written unless every check passes:

  verbatim     -- every arm's body after the signal line is the v0.4 control,
                  byte for byte; every non-target equals v0.4's
  seven words  -- every signal line is exactly seven words
  year only    -- `fresh` and `stale` differ in the year token and nothing else
  no facts     -- byline and promo lines contain no digit
  new tokens   -- no year used in a date line, and no author surname, appears
                  in any of the prompt's documents, so an answer that repeats
                  it took it from the signal line (the echo reading)
  unique       -- one author per domain, no two sharing a surname

Reuses corpus v0.4 wholesale, loaded programmatically from corpus_v0.4.json so
there is no transcription drift from text already measured against real
models.
"""
import hashlib
import json
import pathlib
import re
import sys

_HERE = pathlib.Path(__file__).parent
_V04 = json.loads((_HERE / "corpus_v0.4.json").read_text())

CONDITIONS = ["control", "fresh", "stale", "byline", "promo"]
SIGNAL_WORDS = 7

FRESH_YEAR, STALE_YEAR = "2026", "2019"
DATE_LINE = "Last reviewed and updated in October {year}."

# One fictional author per domain. Credentials match the domain, because the
# advice under test (E-E-A-T) is about relevant expertise, not any title.
# Names are invented; none is meant to be a real person.
BYLINES = {
    "automotive":             ("Hale",       "Written by Marcus Hale, ASE-certified master technician."),
    "career":                 ("Whitlock",   "Written by Dana Whitlock, certified career coach."),
    "consumer_product":       ("Raman",      "Written by Priya Raman, senior product tester."),
    "cooking":                ("Moretti",    "Written by Chef Luca Moretti, culinary instructor."),
    "cybersecurity_consumer": ("Varga",      "Written by Dr. Elena Varga, security researcher."),
    "education":              ("Osei",       "Written by Dr. Samuel Osei, education researcher."),
    "finance":                ("Whitcombe",  "Written by Rachel Whitcombe, certified financial planner."),
    "fitness":                ("Ellison",    "Written by Jordan Ellison, certified strength coach."),
    "furniture":              ("Lindqvist",  "Written by Nora Lindqvist, certified ergonomics specialist."),
    "gaming":                 ("Navarro",    "Written by Theo Navarro, senior hardware editor."),
    "gardening":              ("Ashby",      "Written by Helen Ashby, certified master gardener."),
    "health":                 ("Nwosu",      "Written by Dr. Amara Nwosu, board-certified physician."),
    "home_diy":               ("Tanner",     "Written by Greg Tanner, licensed general contractor."),
    "legal":                  ("Mendes",     "Written by Sofia Mendes, JD, licensed attorney."),
    "local_services":         ("Dolan",      "Written by Ray Dolan, consumer protection investigator."),
    "nutrition":              ("Bauer",      "Written by Claire Bauer, registered dietitian nutritionist."),
    "parenting":              ("Mori",       "Written by Dr. Kenji Mori, board-certified pediatrician."),
    "pets":                   ("Grantham",   "Written by Dr. Isla Grantham, practising veterinarian."),
    "photography":            ("Kovac",      "Written by Ana Kovac, professional portrait photographer."),
    "real_estate":            ("Reyes",      "Written by Martin Reyes, licensed real-estate broker."),
    "saas":                   ("Fitch",      "Written by Owen Fitch, site reliability engineer."),
    "student_loans":          ("Barrow",     "Written by Leah Barrow, certified student-loan counselor."),
    "taxes":                  ("Lam",        "Written by Victor Lam, CPA, enrolled agent."),
    "travel":                 ("Tanaka",     "Written by Mei Tanaka, senior travel editor."),
}

# One promotional line per target format: superlatives and self-praise only,
# nothing a reader could check. Matched to the format's voice so the line
# reads as the page's own marketing, not as a stray sentence.
PROMO = {
    "blog":      "Honestly the best, most trusted advice anywhere.",
    "news":      "The most trusted, unrivalled coverage you'll find.",
    "docs":      "The industry-leading, best-in-class documentation, trusted by everyone.",
    "product":   "The ultimate, best-in-class choice, simply unbeatable anywhere.",
    "forum":     "Hands down the best advice you'll get.",
    "reference": "The definitive, most authoritative and trusted reference.",
}

# Words the echo reading looks for in answers to `promo` (descriptive only).
PROMO_MARKERS = ["best-in-class", "industry-leading", "unrivalled", "unbeatable",
                 "most trusted", "definitive", "most authoritative", "hands down",
                 "the ultimate", "the best advice", "best, most trusted"]


def words(s):
    return len(s.split())


def signal_line(cond, p):
    if cond == "fresh":
        return DATE_LINE.format(year=FRESH_YEAR)
    if cond == "stale":
        return DATE_LINE.format(year=STALE_YEAR)
    if cond == "byline":
        return BYLINES[p["domain"]][1]
    if cond == "promo":
        return PROMO[p["target_format"]]
    raise KeyError(cond)


def build():
    docs = {d["doc_id"]: d for d in _V04["documents"]}
    fails = []

    if set(BYLINES) != set(_V04["domains"]):
        fails.append(f"bylines do not cover the domains exactly: "
                     f"{sorted(set(BYLINES) ^ set(_V04['domains']))}")
    if set(PROMO) != set(_V04["formats"]):
        fails.append("promo lines do not cover the formats exactly")
    surnames = [s for s, _ in BYLINES.values()]
    if len(set(surnames)) != len(surnames):
        fails.append("two authors share a surname")
    for dom, (sur, line) in BYLINES.items():
        if sur not in line:
            fails.append(f"{dom}: surname {sur!r} not in its byline")

    fresh, stale = DATE_LINE.format(year=FRESH_YEAR), DATE_LINE.format(year=STALE_YEAR)
    diff = [(a, b) for a, b in zip(fresh.split(), stale.split()) if a != b]
    if diff != [(FRESH_YEAR + ".", STALE_YEAR + ".")]:
        fails.append(f"fresh and stale differ in more than the year: {diff}")

    lines = [fresh, stale] + [l for _, l in BYLINES.values()] + list(PROMO.values())
    for l in lines:
        if words(l) != SIGNAL_WORDS:
            fails.append(f"signal line is {words(l)} words, not {SIGNAL_WORDS}: {l!r}")
    for l in [l for _, l in BYLINES.values()] + list(PROMO.values()):
        if re.search(r"\d", l):
            fails.append(f"byline or promo line contains a digit: {l!r}")

    prompts_out, docs_out = [], []
    for p in _V04["prompts"]:
        texts = [v for did in p["doc_ids"] for v in docs[did]["variants"].values()]
        blob = " ".join(texts)
        for tok in (FRESH_YEAR, STALE_YEAR):
            if re.search(rf"\b{tok}\b", blob):
                fails.append(f"{p['prompt_id']}: year {tok} already appears in its documents")
        sur = BYLINES[p["domain"]][0]
        if re.search(rf"\b{re.escape(sur)}\b", blob):
            fails.append(f"{p['prompt_id']}: surname {sur} already appears in its documents")
        prompts_out.append({**p,
                            "author_surname": sur,
                            "signal_lines": {c: signal_line(c, p) for c in CONDITIONS[1:]}})

    for p in _V04["prompts"]:
        for did in p["doc_ids"]:
            d = docs[did]
            ctl = d["variants"]["control"]
            if did == p["target_doc_id"]:
                variants = {"control": ctl}
                for c in CONDITIONS[1:]:
                    line = signal_line(c, p)
                    text = f"{line} {ctl}"
                    if text[len(line) + 1:] != ctl:
                        fails.append(f"{did}/{c}: body is not the v0.4 control verbatim")
                    variants[c] = text
            else:
                # Non-targets: v0.4's own text, the same in every condition.
                variants = {c: ctl for c in CONDITIONS}
                if d["variants"].get("treatment", ctl) != ctl:
                    fails.append(f"{did}: v0.4 non-target differs between its arms")
            docs_out.append({**d, "variants": variants})

    if fails:
        print("trust checks FAILED -- corpus not written:")
        for f in fails:
            print(f"  {f}")
        sys.exit(1)

    corpus = {
        "corpus_version": "trust-v1",
        "intervention": "fact-free trust signals put in front of the vague v0.4 target: "
                        "a fresh or stale date, a credentialed byline, promotional superlatives",
        "base_corpus_version": "0.4",
        "supersedes": None,
        "n_prompts": len(prompts_out),
        "n_docs": len(docs_out),
        "formats": _V04["formats"],
        "domains": _V04["domains"],
        "conditions": CONDITIONS,
        "signal_words": SIGNAL_WORDS,
        "years": {"fresh": FRESH_YEAR, "stale": STALE_YEAR},
        "promo_markers": PROMO_MARKERS,
        "prompts": prompts_out,
        "documents": docs_out,
    }
    payload = json.dumps(corpus, indent=2, sort_keys=True, ensure_ascii=False)
    corpus["corpus_sha256"] = hashlib.sha256(payload.encode()).hexdigest()[:16]

    out = _HERE / "corpus_trust.json"
    out.write_text(json.dumps(corpus, indent=2, ensure_ascii=False))
    tw = [words(docs[p["target_doc_id"]]["variants"]["control"]) for p in _V04["prompts"]]
    print(f"wrote {out}")
    print(f"  prompts={len(prompts_out)} docs={len(docs_out)} sha={corpus['corpus_sha256']}")
    print(f"  control target length {min(tw)}-{max(tw)} words; every signal arm +{SIGNAL_WORDS}")
    print("  all trust checks passed: bodies verbatim, signal lines 7 words, "
          "dates differ only in year, no digits in byline/promo, echo tokens new")


if __name__ == "__main__":
    build()
