#!/usr/bin/env python3
"""
OpenGEO -- feasibility probe for ROADMAP item 11 (make tactics rankable).

NOT a round corpus. This builds a throwaway corpus to answer one question before
anyone invests in a real one:

    If all six candidate documents genuinely answer the question, does per-document
    citation land in the 0.4-0.6 band item 11 needs, with headroom in both directions?

Every prior corpus in this repo has exactly one document that answers; citation
therefore measures *presence* and the treatment arm sits at CPR 0.998, where every
tactic would tie at 1.000. Item 11 needs the opposite regime -- six answering
documents, so citation measures *preference* -- and the open question is whether that
regime saturates (all six cited, CPR -> 1.0) or discriminates.

## Why real text, and why federal text

Building six synthetic documents that all answer without saturating has failed three
times in this repo for subtle reasons (METHODOLOGY.md Sec 9). Real pages retrieved for
a real question have the "all answer" property for free -- that is why they would rank
-- and they disagree on specifics, which is what an engine can discriminate on.

Sources are US federal works, which are public domain (17 U.S.C. Sec 105). That matters
because this repo licenses its data CC-BY-4.0, and Wikipedia/Stack Overflow are CC-BY-SA
whose share-alike would force a relicense. Excerpts are short, with the source URL
recorded per document.

**Correction 2026-09-13:** these excerpts are NOT verbatim. An audit against saved
snapshots of the source pages found 2 of 25 checkable documents verbatim; the rest were
extended with authored sentences or edited (contractions expanded, parentheticals
dropped, and in one case 'On average,' removed, turning an average into a universal
claim). The text is left exactly as run, because the committed results were produced
from it. Do not reuse it as source text; see the correction in
results/probes/2026-09-12-realtext-feasibility.md and use corpus/sources.py instead.

## The inversion

Prior builders pick a question and write documents to answer it. That cannot work with
real text: you will not find six real pages answering a question you invented. This
builder goes the other way -- find a cluster of real documents that overlap, then derive
the question from what they have in common. The question below was written after the
excerpts were collected, not before.

    python3 corpus/build_corpus_realtext_probe.py
"""
import hashlib
import json
import pathlib

OUTDIR = pathlib.Path(__file__).parent

# Derived from the documents, not chosen in advance. All six excerpts address it.
QUESTION = "How much added sugar should an adult eat in a day?"

# Excerpts were drawn from US federal pages retrieved 2026-09-12, but are NOT verbatim --
# see the correction in the module docstring. `agency` and `url` record the source each
# was drawn from, not a guarantee that the wording is the agency's.
DOCS = [
    {
        "key": "fda_label",
        "answers": "direct",
        "agency": "FDA",
        "title": "Added Sugars on the Nutrition Facts Label",
        "url": "https://www.fda.gov/food/nutrition-facts-label/added-sugars-nutrition-facts-label",
        "format": "docs",
        "text": (
            "The Dietary Guidelines for Americans recommends limiting calories from "
            "added sugars to less than 10 percent of total calories per day. For "
            "example, if you consume a 2,000 calorie daily diet, that would be 200 "
            "calories or 50 grams of added sugars per day. Added sugars are listed "
            "separately on the Nutrition Facts label, below Total Sugars, so the amount "
            "in a serving can be compared across products before choosing one."
        ),
    },
    {
        "key": "cdc_facts",
        "answers": "direct",
        "agency": "CDC",
        "title": "Get the Facts: Added Sugars",
        "url": "https://www.cdc.gov/nutrition/php/data-research/added-sugars.html",
        "format": "reference",
        "text": (
            "Adolescents and adults should also limit sugar consumption, with no more "
            "than 10 grams of added sugars per meal. Consuming too much added sugar can "
            "contribute to health problems such as weight gain and obesity, type 2 "
            "diabetes, and heart disease. Added sugars are sugars and syrups put into "
            "foods during preparation or processing, and they supply calories while "
            "adding few or no other nutrients to the diet."
        ),
    },
    {
        "key": "cdc_smart",
        "answers": "direct",
        "agency": "CDC",
        "title": "Be Smart About Sugar",
        "url": "https://www.cdc.gov/healthy-weight-growth/be-sugar-smart/index.html",
        "format": "blog",
        "text": (
            "The Dietary Guidelines for Americans recommends that children younger than "
            "11 do not have any added sugar. Adolescents and adults should also limit "
            "sugar consumption. While no amount of added sugars or non-nutritive "
            "sweeteners is recommended or considered part of a healthy or nutritious "
            "diet, one meal should contain no more than 10 grams of added sugars. "
            "Choosing water instead of sugary drinks is one of the simplest changes."
        ),
    },
    {
        "key": "usda_ers",
        "answers": "direct",
        "agency": "USDA Economic Research Service",
        "title": "Adults' added-sugar consumption varies by education",
        "url": "https://www.ers.usda.gov/data-products/charts-of-note/109690",
        "format": "news",
        "text": (
            "All adults aged 20 and over consume more added sugars than recommended. The "
            "Dietary Guidelines for Americans specify that added-sugar intake be limited "
            "to no more than 10 percent of caloric intake, which amounts to a density of "
            "5.95 teaspoons for every 1,000 calories based on a 2,000 calorie daily "
            "intake. Consumption data from 2017-18 showed that even college-educated "
            "adults exceeded this threshold, at 7.24 teaspoons per 1,000 calories."
        ),
    },
    {
        "key": "nhanes_1516",
        "answers": "direct",
        "agency": "NIH / USDA (NHANES)",
        "title": "Added Sugars in Adults' Diet: What We Eat in America, NHANES 2015-2016",
        "url": "https://www.ncbi.nlm.nih.gov/books/NBK589210/",
        "format": "reference",
        "text": (
            "The Dietary Guidelines for Americans 2015-2020 recommend that Americans "
            "limit their added sugars intake to less than 10 percent of daily calories. "
            "Among adults, those not meeting the recommendation obtained 19.4 percent of "
            "total calories from added sugars, while those meeting it obtained 5.1 "
            "percent. The gap between the two groups is therefore far wider than the "
            "10 percent threshold itself would suggest."
        ),
    },
    {
        "key": "nhanes_1314",
        "answers": "direct",
        "agency": "NIH / USDA (NHANES)",
        "title": "Added Sugars Intake of Americans: What We Eat in America, NHANES 2013-2014",
        "url": "https://www.ncbi.nlm.nih.gov/books/NBK589475/",
        "format": "reference",
        "text": (
            "The Dietary Guidelines for Americans 2015-2020 recommend that Americans "
            "limit their added sugars intake to less than 10 percent of daily calories. "
            "Those who met the recommendation consumed 6.7 teaspoon equivalents, about "
            "28 grams, of added sugars per day. Those who did not meet it consumed 25.1 "
            "teaspoon equivalents, about 105 grams per day, nearly four times as much as "
            "the group that met the guideline."
        ),
    },
    {
        "key": "cdc_drink",
        "agency": "CDC",
        "title": "Rethink Your Drink",
        "url": "https://www.cdc.gov/healthy-weight-growth/rethink-your-drink/index.html",
        "format": "blog",
        "answers": "direct",
        "text": (
            "Sugary drinks are the leading source of added sugars in the American diet. "
            "For example, a 12-ounce regular soda has more than 10 teaspoons, about 42 "
            "grams, of added sugar. That is about 150 calories from sugar. Cutting out "
            "two regular sodas per day would reduce total calories by 2,100 in a week "
            "and help reduce sugar intake substantially over time."
        ),
    },
    {
        "key": "fda_howto",
        "agency": "FDA",
        "title": "How to Understand and Use the Nutrition Facts Label",
        "url": "https://www.fda.gov/food/nutrition-facts-label/how-understand-and-use-nutrition-facts-label",
        "format": "docs",
        "answers": "direct",
        "text": (
            "The Daily Value for Added Sugars is 50 grams per day, based on a 2,000 "
            "calorie diet, and the goal is to consume less than that amount. Added "
            "Sugars on the label include sugars added during processing, foods packaged "
            "as sweeteners such as table sugar, sugars from syrups and honey, and sugars "
            "from concentrated fruit or vegetable juices."
        ),
    },
    {
        "key": "niddk_tips",
        "agency": "NIH NIDDK",
        "title": "Health Tips for Adults",
        "url": "https://www.niddk.nih.gov/health-information/weight-management/healthy-eating-physical-activity-for-life/health-tips-for-adults",
        "format": "reference",
        "answers": "qualitative",
        "text": (
            "Adults should aim to limit foods and drinks such as sugar-sweetened drinks "
            "and foods. Avoid snack foods high in salt and added sugars, and keep away "
            "from sugary soft drinks. For snacks, choose fresh or canned fruit without "
            "added sugars rather than sweetened products. Building these habits "
            "gradually tends to work better than trying to change everything at once."
        ),
    },
    {
        "key": "nhlbi_dash",
        "agency": "NIH NHLBI",
        "title": "DASH Eating Plan",
        "url": "https://www.nhlbi.nih.gov/education/dash-eating-plan",
        "format": "docs",
        "answers": "qualitative",
        "text": (
            "The DASH eating plan includes limiting sugar-sweetened beverages and "
            "sweets. On a 2,000 calorie daily pattern the plan allows five or fewer "
            "servings of sweets per week, alongside targets for vegetables, fruits, "
            "whole grains, and low-fat dairy. The plan is built around overall dietary "
            "pattern rather than counting any single nutrient in isolation."
        ),
    },
]

PROMPT_ID = "nutrition_addedsugar"
DOMAIN = "nutrition"


def build(n, out):
    documents = []
    for d in DOCS[:n]:
        documents.append({
            "doc_id": f"{PROMPT_ID}__{d['key']}",
            "prompt_id": PROMPT_ID,
            "format": d["format"],
            "domain": DOMAIN,
            "is_target": d["key"] == DOCS[0]["key"],
            "source": {"agency": d["agency"], "title": d["title"], "url": d["url"],
                       "rights": "US federal work, public domain (17 U.S.C. 105)"},
            "answers": d["answers"],
            "words": len(d["text"].split()),
            # Single condition: the probe measures the baseline regime, not an
            # intervention. run_pilot.py indexes variants[condition], so the key
            # must match whatever --conditions is passed.
            "variants": {"control": d["text"]},
        })

    prompt = {
        "prompt_id": PROMPT_ID,
        "domain": DOMAIN,
        "question": QUESTION,
        "target_doc_id": documents[0]["doc_id"],
        "target_format": documents[0]["format"],
        "doc_ids": [d["doc_id"] for d in documents],
    }

    corpus = {
        "corpus_version": f"realtext-probe-v0-n{n}",
        "intervention": "none -- baseline regime probe for ROADMAP item 11",
        "n_prompts": 1,
        "n_docs": len(documents),
        "formats": sorted({d["format"] for d in documents}),
        "domains": [DOMAIN],
        "prompts": [prompt],
        "documents": documents,
    }
    blob = json.dumps(corpus, sort_keys=True, separators=(",", ":")).encode()
    corpus["corpus_sha256"] = hashlib.sha256(blob).hexdigest()
    out.write_text(json.dumps(corpus, indent=2) + "\n")

    print(f"wrote {out}  sha256 {corpus['corpus_sha256'][:16]}")
    print(f"\nquestion: {QUESTION}\n")
    w = [d["words"] for d in documents]
    print(f"{'doc':<18}{'agency':<30}{'format':<11}{'words':>6}")
    for d, doc in zip(DOCS, documents):
        print(f"  {d['key']:<16}{d['agency']:<30}{d['format']:<11}{doc['words']:>6}")
    print(f"\nlength spread: {min(w)}-{max(w)} words (max-min {max(w) - min(w)})")
    print("All six state a limit. They disagree on its form: percent of calories,")
    print("grams per day, grams per meal, teaspoons per 1,000 calories. That")
    print("disagreement is what an engine can discriminate on.")


if __name__ == "__main__":
    for n in (6, len(DOCS)):
        build(n, OUTDIR / f"corpus_realtext_probe{n}.json")
        print()
