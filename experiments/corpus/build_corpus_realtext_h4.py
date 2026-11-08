#!/usr/bin/env python3
"""
OpenGEO -- real-text H4 replication corpus (design note
`results/probes/2026-09-23-realtext-h4-design.md`; pre-registration
`preregistrations/2026-11-realtext-h4.md`).

H4 -- stating the specific answer raises citation -- has replicated twice (+0.482 on
v0.3, +0.493 on v0.4), both times on documents this project wrote. This corpus asks
whether the same contrast holds when nobody associated with the project wrote the
page: every document is a **verbatim** span of a US federal page, and the only
authored words in the corpus are the one sentence per question that carries the
answer in the treatment arm.

## Structure

Six documents per question, 50-110 words each, matching v0.3/v0.4:

  target, control     a verbatim span of a real page that is topically adjacent but
                      answers none of the question's facts
  target, treatment   the same span with ONE of its sentences replaced by an authored
                      sentence stating the answer. Every figure in that sentence is
                      taken from a named federal page, quoted verbatim below
  five non-targets    verbatim spans of five further pages, byte-identical across arms

Formats are whatever register each page is (reference, docs, news, blog). The design
note's amendment 1 dropped v0.4's one-of-each-format structure: federal agencies do not
publish product listings or forum threads, so this round cannot speak to H5.

## Batches and the screen

Questions are built in batches and screened on the **control arm only** before the
round: a question is kept if its target's control CPR, pooled unweighted across the
five engines, lies in [0.25, 0.75] (pre-registration, "Screening"). Batch corpora carry
both arms, so the treatment text is fixed before any control-arm data exists. The round
corpus is assembled from the kept questions only, with byte-identical documents:

    python3 corpus/build_corpus_realtext_h4.py              # every batch corpus
    python3 corpus/build_corpus_realtext_h4.py --round      # the round corpus, from KEPT

## Every document comes from the committed snapshots

The design note's first sourcing pass lost nine of twenty URLs to agency blocks and an
Internet Archive outage. Batch 1 avoids the problem by drawing only on pages already
snapshotted under `corpus/sources/` for item 11 and the probes. Choosing new questions
for pages already held is the reverse of item 11, which chose pages for its questions:
those pages were sourced because they *answer*, and the spans here are chosen from the
parts of them that do not.

## Checks -- the build refuses to write the corpus unless all pass

  verbatim        every control text and non-target is a contiguous run of its
                  snapshot (sources.verbatim), sliced by anchors, never retyped
  one edit        treatment == control with exactly one declared sentence replaced,
                  that sentence occurring once in the control
  length          50-110 words per document; treatment within +/-3 words of control
                  (METHODOLOGY.md section 9)
  figures sourced every figure source passage is verbatim in its snapshot, and every
                  number in the inserted sentence appears in those passages
  no answer       the question's answer pattern matches nothing in the control arm --
                  no non-target, no control target -- and does match the treatment
  no markers      no bracketed reference markers (sources.span refuses them)
  distinct pages  the six documents of a question come from six different pages
"""
import argparse
import hashlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import sources as S  # noqa: E402

MIN_WORDS, MAX_WORDS, LENGTH_TOL = 50, 110, 3

# Metadata for pages no earlier corpus used. Every other page's agency, title, rights and
# format are reused from the corpus that first carried it (see `known_sources`).
NEW_SOURCES = {
    "https://www.irs.gov/businesses/small-businesses-self-employed/irs-audits": {
        "agency": "IRS", "title": "IRS audits", "format": "docs",
        "rights": "US federal work (IRS), 17 U.S.C. 105"},
    "https://www.fda.gov/consumers/consumer-updates/spilling-beans-how-much-caffeine-too-much": {
        "agency": "FDA", "title": "Spilling the Beans: How Much Caffeine is Too Much?",
        "format": "news", "rights": "US federal work (FDA), 17 U.S.C. 105"},
}

# --------------------------------------------------------------------------- batch 1
#
# One question per domain, domains drawn from v0.4's twenty-four. Each target is chosen
# to sit one dimension away from the question (METHODOLOGY.md section 9): about the same
# subject, a different attribute of it. Each question carries one or two clearly
# tangential non-targets, per the same section's cites/answer note.
#
# `answer` is a regex the build requires to be absent from every control-arm document
# and present in the treatment target. It is deliberately broader than the answer
# itself -- any retention period, any password length, any caffeine quantity -- because
# section 9's "presence, not completeness" rule says a partial or neighbouring figure
# saturates citation just as the full answer does.

BATCH_1 = [
    {
        "prompt_id": "taxes_employment_records",
        "domain": "taxes",
        "question": "How long does a small business with employees have to keep its "
                    "employment tax records?",
        "answer": r"\byears?\b",
        "target": {
            "url": "https://www.irs.gov/businesses/small-businesses-self-employed/recordkeeping",
            "start": "Good records will help you monitor the progress of your business",
            "end": "the type of records you need to keep for federal tax purposes.",
            "replace": "However, the business you are in affects the type of records you "
                       "need to keep for federal tax purposes.",
            "with": "Employers must keep all employment tax records for at least 4 years "
                    "after the tax becomes due or is paid.",
            "figures": [("https://www.irs.gov/taxtopics/tc305",
                         "If you have employees, you must keep all your employment tax "
                         "records for at least 4 years after the tax becomes due or is "
                         "paid, whichever is later.")],
        },
        "others": [
            ("https://www.irs.gov/businesses/small-businesses-self-employed/employment-tax-recordkeeping",
             "Your employer identification number.",
             "the amount and weekly rate of payments you or third-party payers made to them."),
            ("https://www.irs.gov/newsroom/good-recordkeeping-year-round-helps-taxpayers-avoid-tax-time-frustration",
             "Identify sources of income. Taxpayers may receive money",
             "potentially overlooked deductions or credits."),
            ("https://www.irs.gov/businesses/small-businesses-self-employed/irs-audits",
             "Selection for an audit does not always suggest there's a problem.",
             "update return selection information."),
            # tangential: filing deadlines, not records
            ("https://www.irs.gov/filing/get-an-extension-to-file-your-tax-return",
             "If you need more time to file your taxes, request an extension",
             "There are 3 ways to get until October 15 to file your tax return."),
            # tangential: penalties, not records
            ("https://www.irs.gov/payments/failure-to-file-penalty",
             "You can avoid a penalty by filing and paying your tax by the due date.",
             "A payment plan can help you pay over time."),
        ],
    },
    {
        "prompt_id": "cyber_password_length",
        "domain": "cybersecurity_consumer",
        "question": "How many characters long should a password be, according to NIST's "
                    "current guidance?",
        "answer": r"\d+\s*(?:-|to)?\s*\d*\s*characters?\b|\d+-character|characters long"
                  r"|\b(?:eight|twelve|fifteen|sixty-four)\b",
        "target": {
            "url": "https://www.cisa.gov/news-events/news/choosing-and-protecting-passwords",
            "start": "Once you've come up with a strong, memorable password it's tempting",
            "end": "Use different passwords on different systems and accounts.",
            "replace": "Reusing a password, even a strong one, endangers your accounts just "
                       "as much as using a weak password.",
            "with": "NIST guidance recommends that a password should be at least 15 "
                    "characters long, and never reused.",
            "figures": [("https://www.nist.gov/cybersecurity-and-privacy/how-do-i-create-good-password",
                         "NIST guidance recommends that a password should be at least 15 "
                         "characters long.")],
        },
        "others": [
            ("https://www.nist.gov/blogs/taking-measure/easy-ways-build-better-p5w0rd",
             "Instead, passphrases should be words that can go together in your head",
             "from a hacker's perspective, it really is random."),
            ("https://consumer.ftc.gov/articles/creating-strong-passwords-and-other-ways-protect-your-accounts",
             "It's critical to protect your email account with a strong password.",
             "here's how to recover a hacked account."),
            ("https://www.cisa.gov/audiences/small-and-medium-businesses/secure-your-business/require-strong-passwords",
             "Employees only need to remember one strong master password",
             "access multiple systems with one set of credentials."),
            ("https://www.cisa.gov/resources-tools/training/formulate-strong-passwords-and-pin-codes",
             "Account authentication is one of the most important cybersecurity cornerstones",
             "to gain unauthorized access to your account."),
            # tangential: security questions, not passwords
            ("https://pages.nist.gov/800-63-FAQ/",
             "Knowledge-based authentication (KBA), sometimes referred to as",
             None),
        ],
    },
    {
        "prompt_id": "nutrition_caffeine_limit",
        "domain": "nutrition",
        "question": "How much caffeine a day is generally safe for healthy adults?",
        "answer": r"milligram|\bmg\b|cups? of (?:plain )?coffee|\d+\s*(?:to\s*\d+\s*)?cups",
        "target": {
            "url": "https://www.fda.gov/consumers/consumer-updates/spilling-beans-how-much-caffeine-too-much",
            "start": "All packaged foods are required to list caffeine",
            "end": "as to how much caffeine they contain.",
            "replace": "Many packaged foods, including beverages and dietary supplements "
                       "containing caffeine, voluntarily provide information on the label "
                       "as to how much caffeine they contain.",
            "with": "For most adults, the FDA cites 400 milligrams a day, about two to three "
                    "cups of coffee, as not generally associated with negative effects.",
            "figures": [("https://www.fda.gov/consumers/consumer-updates/spilling-beans-how-much-caffeine-too-much",
                         "For most adults, the FDA has cited 400 milligrams* a day - that's "
                         "about two to three 12-fluid-ounce cups of coffee - as an amount not "
                         "generally associated with negative effects.")],
        },
        "others": [
            ("https://www.cdc.gov/healthy-weight-growth/water-healthy-drinks/index.html",
             "Drinks with sugar alternatives: Drinks that are labeled",
             "especially for young people."),
            ("https://www.ncbi.nlm.nih.gov/books/NBK589210/",
             "Beverages such as sweetened beverages, tea, and coffee together supplied",
             "15 percent in all females' diets."),
            ("https://www.fda.gov/food/nutrition-facts-label/added-sugars-nutrition-facts-label",
             "The Dietary Guidelines for Americans states that a limited amount of added sugars",
             None),
            # tangential: label rules, not caffeine
            ("https://www.fda.gov/food/nutrition-facts-label/daily-value-nutrition-and-supplement-facts-labels",
             "The Nutrition Facts label must list total fat, saturated fat",
             "the amount contained in the food (for example, \"high\" or \"low\")."),
            # tangential: sodium, not caffeine
            ("https://www.fda.gov/consumers/consumer-updates/eating-too-much-salt-ways-cut-backgradually",
             "Sodium is added to packaged and prepared foods for a variety of reasons",
             "so we know these are achievable and acceptable."),
        ],
    },
    {
        "prompt_id": "cooking_leftovers_room_temp",
        "domain": "cooking",
        "question": "How long can cooked food be left out at room temperature before it "
                    "should be thrown away?",
        "answer": r"\bhours?\b|90 ?°|90 degrees|danger zone",
        "target": {
            "url": "https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/how-temperatures-affect-food",
            "start": "A temperature of 40 °F should be maintained in the refrigerator.",
            "end": "to verify that the temperature of the unit is correct.",
            "replace": "Bacteria capable of causing foodborne illness either don't grow or "
                       "grow very slowly at refrigerator temperatures.",
            "with": "Cooked food left out more than 2 hours, or 1 hour above 90 °F, should "
                    "be discarded.",
            "figures": [("https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/grilling-food-safely",
                         "Discard any food left out more than 2 hours (1 hour if temperature "
                         "outside is above 90°F/ 32°C).")],
        },
        "others": [
            ("https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/doneness-versus-safety",
             "Research indicates that the color of the meat and the color of the juices",
             None),
            ("https://www.usda.gov/about-usda/news/blog/cooking-meat-it-done-yet",
             "USDA recommends never relying on color, firmness or time",
             "allow meat to rest for at least three minutes before cutting or consuming."),
            ("https://www.fda.gov/food/buy-store-serve-safe-food/safe-food-handling",
             "The food supply in the United States is among the safest in the world.",
             None),
            # tangential: thermometer hardware
            ("https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/kitchen-thermometers",
             "Thermistor-style food thermometers use a resistor",
             None),
            # tangential: smoking meat
            ("https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/grilling-food-safely",
             "Smoking is cooking food indirectly in the presence of a fire.",
             "should be maintained at 250 to 300°F (121 to 149°C) for safety."),
        ],
    },
    {
        "prompt_id": "home_radon_action_level",
        "domain": "home_diy",
        "question": "At what radon level does the EPA recommend fixing your home?",
        "answer": r"pCi|picocurie|Bq/m|becquerel|working levels?\b",
        "target": {
            "url": "https://www.epa.gov/radtown/radon-homes-schools-and-buildings",
            "start": "Radon comes from the natural decay of uranium and radium",
            "end": "major remodeling or changes to the HVAC system.",
            "replace": "The EPA and the Surgeon General recommend testing all homes and "
                       "schools for radon.",
            "with": "The EPA recommends fixing a home if its radon level is 4 pCi/L or more.",
            "figures": [("https://www.epa.gov/radon/what-epas-action-level-radon-and-what-does-it-mean",
                         "The EPA recommends homes be fixed if the radon level is 4 pCi/L "
                         "(picocuries per liter) (150 becquerels per meter cubed (Bq/m3)) or "
                         "more.")],
        },
        "others": [
            ("https://www.epa.gov/ks/january-take-time-protect-your-home-invisible-cancer-risk",
             "LENEXA, KAN. (JAN. 27, 2026) - January is National Radon Action Month",
             "actions you can take today to protect your family."),
            ("https://www.epa.gov/radon/health-risk-radon",
             "Radon is the number one cause of lung cancer among non-smokers",
             None),
            ("https://www.epa.gov/radon/epa-map-radon-zones-and-supplemental-information",
             "EPA's Map of Radon Zones can be supplemented with available state-developed",
             "and six national radon testing laboratories."),
            # tangential: attic insulation
            ("https://www.energystar.gov/saveathome/seal_insulate/rule_your_attic",
             "A well-sealed and insulated attic can make a real difference",
             None),
            # tangential: smoke alarm power sources
            ("https://www.usfa.fema.gov/prevention/home-fires/prepare-for-fire/smoke-alarms/",
             "Smoke alarms are powered by battery or by your home's electrical system.",
             None),
        ],
    },
    {
        "prompt_id": "finance_emergency_400",
        "domain": "finance",
        "question": "What share of U.S. adults could cover an unexpected $400 expense using "
                    "cash or its equivalent?",
        "answer": r"percent|%|\$400|\b6\d\b|in (?:10|ten)\b|\bhalf\b|\bmajority\b"
                  r"|\bmost (?:adults|americans|people)\b",
        "target": {
            "url": "https://www.consumerfinance.gov/an-essential-guide-to-building-an-emergency-fund/",
            "start": "We've all experienced unexpected financial emergencies",
            "end": "towards reaching your larger savings goals.",
            "replace": "Large or small, these unplanned expenses often feel like they hit at "
                       "the worst times.",
            "with": "Faced with a $400 emergency expense, 63 percent of adults would cover it "
                    "with cash or its equivalent.",
            "figures": [("https://www.federalreserve.gov/publications/2026-economic-well-being-of-us-households-in-2025-savings-investments.htm",
                         "When faced with a hypothetical expense of $400, 63 percent of all "
                         "adults said they would have covered it exclusively using cash, "
                         "savings, or a credit card paid off at the next statement")],
        },
        "others": [
            ("https://www.consumerfinance.gov/archive/blog/preparedness-means-rebuilding-toward-brighter-future-emergency-savings/",
             "It might seem impossible to save enough to get you and your family",
             None),
            ("https://www.fdic.gov/consumer-resource-center/2024-01/starting-small-can-lead-big-savings",
             "Consider keeping emergency savings in a separate FDIC-insured savings account",
             None),
            ("https://www.investor.gov/introduction-investing/investing-basics/save-and-invest/save-rainy-day",
             "Savings are usually put into safe places that allow you access",
             None),
            ("https://www.fdic.gov/consumer-resource-center/2025-01/saving-unexpected-and-your-future",
             "Automatic transfers into savings on a set schedule",
             "that adds up to $520, plus interest, to your savings each year."),
            # tangential: credit scores
            ("https://www.consumerfinance.gov/ask-cfpb/what-is-a-credit-score-en-315/",
             "A credit score is a prediction of your credit behavior",
             "the interest rate and credit limit you receive."),
        ],
    },
]

BATCHES = {1: BATCH_1}

# prompt_ids that cleared the screen, in the order they enter the round corpus. Empty
# until batch 1 is screened; filled in by a dated commit that cites the screen output.
KEPT = [
    # batch 1, screened 2026-11-08 (results/screen_realtext_h4_b1.jsonl): 2 of 6 kept
    "cyber_password_length",
    "finance_emergency_400",
]


# ---------------------------------------------------------------------- helpers

def known_sources():
    """url -> (source metadata, format) from every corpus built so far."""
    out = {}
    for f in sorted(HERE.glob("corpus_*.json")):
        if f.name.startswith("corpus_realtext_h4"):
            continue
        for d in json.loads(f.read_text())["documents"]:
            s = d.get("source")
            if s and s.get("url") and s["url"] not in out:
                out[s["url"]] = ({k: s.get(k) for k in
                                  ("agency", "title", "url", "rights", "rights_evidence")},
                                 d.get("format"))
    for url, m in NEW_SOURCES.items():
        out.setdefault(url, ({"agency": m["agency"], "title": m["title"], "url": url,
                              "rights": m["rights"], "rights_evidence": None}, m["format"]))
    return out


def block_end(url, start):
    """End anchor for a span that is exactly the paragraph `start` opens."""
    for p in S.passages(url, start[:40], min_words=1):
        if S.norm(p).startswith(S.norm(start)):
            return p[-60:]
    raise S.SpanError(f"no paragraph opens with {start[:50]!r} in {url}")


def words(t):
    return len(t.split())


def numbers(t):
    return set(re.findall(r"\d+(?:[.,]\d+)?", t))


def build_question(q, meta, fail):
    pid, pat = q["prompt_id"], re.compile(q["answer"], re.I)
    docs = []

    def doc(url, start, end, role):
        end = end or block_end(url, start)
        text = S.span(url, start, end, multi_block=True)
        snap = S.load(url)
        ok, missing = S.verbatim(text, snap["text"])
        if not ok:
            fail(f"{pid}/{role}: not verbatim -- {missing[:1]}")
        if url not in meta:
            fail(f"{pid}/{role}: no metadata for {url}; add it to NEW_SOURCES")
        source, fmt = meta[url]
        source = dict(source, snapshot_sha256=snap["text_sha256"],
                      retrieved_utc=snap["retrieved_utc"], method=snap["method"])
        n = words(text)
        if not MIN_WORDS <= n <= MAX_WORDS:
            fail(f"{pid}/{role}: {n} words, outside {MIN_WORDS}-{MAX_WORDS}")
        if pat.search(text):
            fail(f"{pid}/{role}: control-arm text states the answer: "
                 f"{pat.search(text).group()!r}")
        return text, source, fmt

    t = q["target"]
    control, source, fmt = doc(t["url"], t["start"], t["end"], "target")
    if control.count(S.norm(t["replace"])) != 1:
        fail(f"{pid}/target: the replaced sentence must occur exactly once in the control")
    treatment = control.replace(S.norm(t["replace"]), t["with"])
    if abs(words(treatment) - words(control)) > LENGTH_TOL:
        fail(f"{pid}/target: treatment {words(treatment)}w vs control {words(control)}w "
             f"exceeds +/-{LENGTH_TOL}")
    if not pat.search(treatment):
        fail(f"{pid}/target: treatment does not state the answer")
    sourced = set()
    figure_sources = []
    for url, passage in t["figures"]:
        snap = S.load(url)
        if snap is None or not S.verbatim(passage, snap["text"])[0]:
            fail(f"{pid}/target: figure passage is not verbatim in {url}")
        sourced |= numbers(passage)
        figure_sources.append({"url": url, "agency": meta.get(url, ({},))[0].get("agency"),
                               "passage": passage,
                               "snapshot_sha256": snap["text_sha256"] if snap else None})
    unsourced = numbers(t["with"]) - sourced
    if unsourced:
        fail(f"{pid}/target: inserted figures not in any figure source: {sorted(unsourced)}")

    target_id = f"{pid}__target"
    docs.append({
        "doc_id": target_id, "prompt_id": pid, "format": fmt, "domain": q["domain"],
        "is_target": True, "source": source, "words": words(control),
        "variants": {"control": control, "treatment": treatment},
        "edit": {"replaced": S.norm(t["replace"]), "inserted": t["with"],
                 "authored": True, "figure_sources": figure_sources},
    })
    for i, (url, start, end) in enumerate(q["others"], 1):
        text, src, f = doc(url, start, end, f"other{i}")
        docs.append({
            "doc_id": f"{pid}__doc{i}", "prompt_id": pid, "format": f,
            "domain": q["domain"], "is_target": False, "source": src,
            "words": words(text), "variants": {"control": text, "treatment": text},
        })

    urls = [d["source"]["url"] for d in docs]
    if len(set(urls)) != len(urls):
        fail(f"{pid}: two documents share a source page")
    prompt = {"prompt_id": pid, "domain": q["domain"], "question": q["question"],
              "target_doc_id": target_id, "target_format": fmt,
              "doc_ids": [d["doc_id"] for d in docs], "answer_pattern": q["answer"]}
    return prompt, docs


def write(name, version, prompts, documents, note):
    corpus = {
        "corpus_version": version,
        "intervention": "H4 on verbatim federal text: the target's control is a real page "
                        "span; treatment replaces one sentence with a sourced statement "
                        "of the answer",
        "conditions": ["control", "treatment"],
        "note": note,
        "n_prompts": len(prompts), "n_docs": len(documents),
        "formats": sorted({d["format"] for d in documents}),
        "domains": sorted({d["domain"] for d in documents}),
        "prompts": prompts, "documents": documents,
    }
    blob = json.dumps(corpus, sort_keys=True, separators=(",", ":")).encode()
    corpus["corpus_sha256"] = hashlib.sha256(blob).hexdigest()[:16]
    out = HERE / name
    out.write_text(json.dumps(corpus, indent=2, ensure_ascii=False) + "\n")
    return out, corpus["corpus_sha256"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", action="store_true",
                    help="assemble the round corpus from KEPT instead of the batch corpora")
    args = ap.parse_args(argv)

    meta = known_sources()
    problems = []
    built = {}
    for b, qs in BATCHES.items():
        for q in qs:
            try:
                built[q["prompt_id"]] = (b,) + build_question(q, meta, problems.append)
            except S.SpanError as e:
                problems.append(f"{q['prompt_id']}: {e}")
    if problems:
        print("BUILD REFUSED -- every check must pass:\n")
        for p in problems:
            print("  " + p)
        return 1

    if args.round:
        if len(KEPT) < 25:
            print(f"KEPT has {len(KEPT)} questions; the round needs 25 (pre-registration, "
                  "'Stopping rule'). Not writing the round corpus.")
            return 1
        prompts = [built[p][1] for p in KEPT]
        docs = [d for p in KEPT for d in built[p][2]]
        out, sha = write("corpus_realtext_h4.json", "realtext-h4-v1", prompts, docs,
                         "round corpus: the questions that cleared the control-arm screen")
        print(f"wrote {out.name}  sha256 {sha}  ({len(prompts)} questions)")
        return 0

    for b, qs in BATCHES.items():
        ids = [q["prompt_id"] for q in qs]
        prompts = [built[p][1] for p in ids]
        docs = [d for p in ids for d in built[p][2]]
        out, sha = write(f"corpus_realtext_h4_b{b}.json", f"realtext-h4-screen-b{b}",
                         prompts, docs, f"screening batch {b}: run the control arm only")
        print(f"wrote {out.name}  sha256 {sha}")
        print(f"\n{'question':<30}{'target fmt':>11}{'ctl w':>7}{'trt w':>7}"
              f"{'others w':>12}{'context w':>11}")
        print("-" * 78)
        for p in ids:
            ds = built[p][2]
            t = ds[0]
            ow = [d["words"] for d in ds[1:]]
            print(f"{p:<30}{t['format']:>11}{words(t['variants']['control']):>7}"
                  f"{words(t['variants']['treatment']):>7}{f'{min(ow)}-{max(ow)}':>12}"
                  f"{sum(d['words'] for d in ds):>11}")
        fm = {}
        for p in ids:
            fm[built[p][2][0]["format"]] = fm.get(built[p][2][0]["format"], 0) + 1
        print(f"\ntarget formats: {fm}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
