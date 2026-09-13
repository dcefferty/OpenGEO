#!/usr/bin/env python3
"""
OpenGEO -- third feasibility probe for ROADMAP item 11: isolate the mechanism.

Probes 1 and 2 disagreed. Probe 1 went from six candidates to ten and the same six
documents lost 0.100 of citation rate; probe 2 made the same move and they lost nothing.
The proposed explanation is that probe 1 also went from six *answering* documents to
eight, while probe 2 stayed at five answering the whole time -- so the lever is how many
documents answer, and non-answering candidates are inert.

Both probes confound those two variables. This one does not:

    arm A   5 answering + 5 non-answering  = 10 candidates
    arm B   9 answering + 1 non-answering  = 10 candidates

Candidate count is fixed at ten. Five answering documents and one filler appear in both
arms, unchanged. The only thing that differs is whether the other four slots answer the
question or not.

**Prediction if the mechanism is right:** the five shared answering documents lose
citation share in arm B, where they compete with four more answering documents instead of
four inert ones. If they hold their rate, the mechanism is wrong and candidate
composition does not drive per-document CPR.

The five shared answerers were chosen to span the range observed in probe 1 (1.00, 0.69,
0.56, 0.52, 0.29) rather than clustered, so a dilution effect is visible wherever it acts.

Sources are US federal works, public domain under 17 U.S.C. Sec 105, quoted verbatim.
Answering documents are reused unchanged from probe 1 where possible, imported rather
than copied so there is one source of truth for the text.

    python3 corpus/build_corpus_realtext_probe3.py
"""
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from build_corpus_realtext_probe import DOCS as P1_DOCS  # noqa: E402

OUTDIR = pathlib.Path(__file__).parent
QUESTION = "How much added sugar should an adult eat in a day?"

P1 = {d["key"]: d for d in P1_DOCS}

# Present in BOTH arms. Chosen to span probe 1's observed range.
SHARED_ANSWERING = ["fda_label", "cdc_facts", "nhanes_1516", "usda_ers", "cdc_drink"]

# Present only in arm B, replacing four fillers.
EXTRA_ANSWERING = ["cdc_smart", "nhanes_1314", "fda_howto"]

ODPHP = {
    "key": "odphp_cutdown",
    "answers": "direct",
    "agency": "HHS ODPHP",
    "title": "Cut Down on Added Sugars (Dietary Guidelines 2015-2020)",
    "url": "https://odphp.health.gov/sites/default/files/2019-10/DGA_Cut-Down-On-Added-Sugars.pdf",
    "format": "docs",
    "text": (
        "Choosing a healthy eating pattern low in added sugars can have important health "
        "benefits. The 2015-2020 Dietary Guidelines for Americans recommends limiting "
        "calories from added sugars to no more than 10% each day. That is 200 calories, "
        "or about 12 teaspoons, for a 2,000 calorie diet. Reading the label is the "
        "simplest way to see how much a product contributes."
    ),
}

# Nutrition documents that do not answer the question. Each was checked at retrieval:
# none states a numeric added-sugar limit. The first is the one kept in both arms.
FILLER = [
    {
        "key": "cdc_sodium",
        "answers": "none",
        "agency": "CDC",
        "title": "About Sodium and Health",
        "url": "https://www.cdc.gov/salt/about/index.html",
        "format": "reference",
        "text": (
            "Americans consume more than 3,300 milligrams of sodium per day, on average. "
            "This is well above the federal recommendation of less than 2,300 milligrams "
            "of sodium daily for teens and adults as part of a healthy eating pattern. "
            "Most of that sodium comes from packaged and restaurant food rather than the "
            "salt shaker at the table."
        ),
    },
    {
        "key": "nhlbi_activity",
        "answers": "none",
        "agency": "NIH NHLBI",
        "title": "Get Regular Physical Activity",
        "url": "https://www.nhlbi.nih.gov/health/heart-healthy-living/physical-activity",
        "format": "blog",
        "text": (
            "Each week, adults should get at least 150 minutes to 300 minutes of "
            "moderate-intensity aerobic physical activity, or 75 minutes to 150 minutes "
            "of vigorous-intensity aerobic physical activity, or a combination of both "
            "moderate-intensity and vigorous-intensity activity. Activity can be spread "
            "across the week in whatever pattern is easiest to sustain."
        ),
    },
    {
        "key": "fda_foodsafety",
        "answers": "none",
        "agency": "FDA",
        "title": "Safe Food Handling",
        "url": "https://www.fda.gov/food/buy-store-serve-safe-food/safe-food-handling",
        "format": "docs",
        "text": (
            "Use an appliance thermometer to be sure the refrigerator temperature is "
            "consistently 40 degrees Fahrenheit or below and the freezer temperature is "
            "0 degrees Fahrenheit or below. Refrigerate or freeze meat, poultry, eggs, "
            "seafood, and other perishables within two hours of cooking or purchasing "
            "them, and within one hour in hot weather."
        ),
    },
    {
        "key": "cdc_fruitveg",
        "answers": "none",
        "agency": "CDC",
        "title": "State Indicator Report on Fruits and Vegetables",
        "url": "https://www.cdc.gov/nutrition/php/data-research/fruits-vegetables.html",
        "format": "news",
        "text": (
            "In 2015 and 2019, only about 1 in 10 adults met recommendations for fruit "
            "and vegetable intake. Eating a diet rich in fruits and vegetables can help "
            "protect against serious and costly chronic diseases. Some examples include "
            "heart disease, type 2 diabetes, some cancers, and obesity. Intake remains "
            "well below recommended levels in every state measured."
        ),
    },
    {
        "key": "cdc_water",
        "answers": "none",
        "agency": "CDC",
        "title": "About Water and Healthier Drinks",
        "url": "https://www.cdc.gov/healthy-weight-growth/water-healthy-drinks/index.html",
        "format": "blog",
        "text": (
            "Getting enough water every day is important for health. Drinking water can "
            "prevent dehydration, which may cause unclear thinking, mood change, "
            "overheating, constipation, and kidney stones. Water has no calories, so "
            "replacing other beverages with plain water can help reduce caloric intake "
            "over the course of a day."
        ),
    },
]

PROMPT_ID = "nutrition_addedsugar"
DOMAIN = "nutrition"

ARMS = {
    # arm: (answering keys, filler keys)
    "a5": (SHARED_ANSWERING, [f["key"] for f in FILLER]),
    "b9": (SHARED_ANSWERING + EXTRA_ANSWERING + [ODPHP["key"]], [FILLER[0]["key"]]),
}


def build(arm):
    ans_keys, fill_keys = ARMS[arm]
    pool = {**P1, ODPHP["key"]: ODPHP, **{f["key"]: f for f in FILLER}}
    keys = ans_keys + fill_keys
    assert len(keys) == 10, f"{arm}: {len(keys)} candidates, expected 10"

    documents = []
    for k in keys:
        d = pool[k]
        documents.append({
            "doc_id": f"{PROMPT_ID}__{k}",
            "prompt_id": PROMPT_ID,
            "format": d["format"],
            "domain": DOMAIN,
            "is_target": k == ans_keys[0],
            "source": {"agency": d["agency"], "title": d["title"], "url": d["url"],
                       "rights": "US federal work, public domain (17 U.S.C. 105)"},
            "answers": d["answers"],
            "words": len(d["text"].split()),
            "variants": {"control": d["text"]},
        })

    prompt = {
        "prompt_id": PROMPT_ID, "domain": DOMAIN, "question": QUESTION,
        "target_doc_id": documents[0]["doc_id"],
        "target_format": documents[0]["format"],
        "doc_ids": [d["doc_id"] for d in documents],
    }
    corpus = {
        "corpus_version": f"realtext-probe3-{arm}",
        "intervention": "none -- mechanism probe for ROADMAP item 11",
        "n_prompts": 1, "n_docs": len(documents),
        "n_answering": len(ans_keys),
        "formats": sorted({d["format"] for d in documents}),
        "domains": [DOMAIN], "prompts": [prompt], "documents": documents,
    }
    blob = json.dumps(corpus, sort_keys=True, separators=(",", ":")).encode()
    corpus["corpus_sha256"] = hashlib.sha256(blob).hexdigest()
    out = OUTDIR / f"corpus_realtext_probe3_{arm}.json"
    out.write_text(json.dumps(corpus, indent=2) + "\n")
    w = [d["words"] for d in documents]
    print(f"wrote {out.name}  sha256 {corpus['corpus_sha256'][:16]}")
    print(f"  10 candidates, {len(ans_keys)} answering, {len(fill_keys)} filler, "
          f"{min(w)}-{max(w)} words")


if __name__ == "__main__":
    print(f"question: {QUESTION}\n")
    for arm in ARMS:
        build(arm)
    shared = set(ARMS["a5"][0]) | {FILLER[0]["key"]}
    print(f"\nshared across both arms, unchanged: {len(shared)} documents")
    print(f"  answering: {', '.join(SHARED_ANSWERING)}")
    print(f"  filler:    {FILLER[0]['key']}")
    print("\nCandidate count is fixed at 10. If the five shared answering documents lose")
    print("citation share in arm B, the lever is how many documents answer. If they hold,")
    print("the mechanism proposed after probes 1 and 2 is wrong.")
