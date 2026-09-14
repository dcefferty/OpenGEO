#!/usr/bin/env python3
"""
OpenGEO -- the rankable corpus (ROADMAP item 11).

Every earlier corpus has exactly one document that answers its question, so citation
measures presence, the treatment arm saturates, and tactics cannot be ranked. This
corpus is built from real text in which several candidates answer, so citation measures
preference. Its design comes from three feasibility probes
(results/probes/2026-09-12-realtext-feasibility.md) and the audit that corrected them.

This file builds the SCREENING corpus: baseline text only, no tactic variants. Each
question is run once, screen.py picks a target that no engine pins at 0 or 1, and
questions with no such target are discarded before any variant is written.

## Rules this builder enforces, and the failure each exists because of

- **Every excerpt is a span of a saved snapshot, never typed.** Documents give a start
  and end phrase; sources.span() slices the passage out. The probes' excerpts were
  typed and extended, and 23 of 25 turned out not to be the source's words.
- **Every document states its rights, with evidence.** A .gov domain does not make a
  page a federal work: MedlinePlus Encyclopedia articles are A.D.A.M., Inc. content, and
  NCBI Bookshelf hosts WHO guidelines. A document without a rights statement fails.
- **No reference markers in excerpts.** sources.span() rejects "[1]"-style markers,
  which collide with the harness's own citation syntax.
- **One document per source page.** Two excerpts from one page would be one source
  counted twice.
- **Answer levels are declared, not inferred.** `direct` states a daily limit for the
  population asked about; `partial` states it for another population or implies it;
  `none` is on-topic with no amount. The screen does not use these -- it decides on
  citation data alone -- but analysis of what the engines reward does.

Questions are chosen where authoritative sources state the answer in different forms,
which the probes found is what gives citation a movable middle. A question with one
canonical answer every source repeats screened empty.

    python3 corpus/build_corpus_rankable.py
"""
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import sources  # noqa: E402

OUT = pathlib.Path(__file__).parent / "corpus_rankable_screen.json"
LEVELS = {"direct", "partial", "none"}

USDA = "US federal work (USDA), 17 U.S.C. 105"
FDA = "US federal work (FDA), 17 U.S.C. 105"
HHS = "US federal work (HHS), 17 U.S.C. 105"
NIH = "US federal work (NIH), 17 U.S.C. 105"


def doc(key, agency, title, url, fmt, answers, rights, start, end, multi_block=False,
        evidence=None):
    return dict(key=key, agency=agency, title=title, url=url, format=fmt,
                answers=answers, rights=rights, start=start, end=end,
                multi_block=multi_block, evidence=evidence)


QUESTIONS = [
    {
        "id": "nutrition_addedsugar",
        "domain": "nutrition",
        "question": "How much added sugar should an adult have per day?",
        "docs": [
            doc("fda_label", "FDA", "Added Sugars on the Nutrition Facts Label",
                "https://www.fda.gov/food/nutrition-facts-label/added-sugars-nutrition-facts-label",
                "docs", "direct", FDA,
                "The Dietary Guidelines for Americans recommends limiting calories",
                "staying within calorie limits."),
            doc("usda_ers", "USDA Economic Research Service",
                "Adults' added-sugar consumption varies by education",
                "https://www.ers.usda.gov/data-products/charts-of-note/109690",
                "news", "direct", USDA,
                "On average, all adults aged 20 and over consume more added sugars",
                "based on a 2,000 calorie daily intake."),
            doc("nhanes_1516", "USDA ARS Food Surveys Research Group",
                "Added Sugars in Adults' Diet: What We Eat in America, NHANES 2015-2016",
                "https://www.ncbi.nlm.nih.gov/books/NBK589210/",
                "reference", "direct", USDA,
                "Overall, 47 percent of adults, 20 years and over, met",
                "less than 10% of daily calories.",
                evidence="Bookshelf publisher line: Beltsville (MD): United States "
                         "Department of Agriculture (USDA)"),
            doc("nhanes_1314", "USDA ARS Food Surveys Research Group",
                "Added Sugars Intake of Americans: What We Eat in America, NHANES 2013-2014",
                "https://www.ncbi.nlm.nih.gov/books/NBK589475/",
                "reference", "partial", USDA,
                "On average, those who met the DGA recommendation consumed",
                "25.1 tsp. eq. (105 g).",
                evidence="FSRG Dietary Data Brief, USDA ARS"),
            doc("nhanes_kids", "USDA ARS Food Surveys Research Group",
                "Added Sugars in American Children's Diet: What We Eat in America, NHANES 2015-2016",
                "https://www.ncbi.nlm.nih.gov/books/NBK589213/",
                "reference", "partial", USDA,
                "About 35 percent of children 2 to 19 years of age met",
                "less than 10% of total energy for the day.",
                evidence="FSRG Dietary Data Brief, USDA ARS"),
            doc("fns_school", "USDA Food and Nutrition Service",
                "Added Sugars (school nutrition standards)",
                "https://www.fna.usda.gov/cn/school-nutrition-standards-updates/added-sugars",
                "docs", "partial", USDA,
                "In addition to product-based limits described above",
                "in the school lunch and breakfast programs."),
            doc("nhlbi_foods", "NIH NHLBI", "Heart-Healthy Living: Choose Heart-Healthy Foods",
                "https://www.nhlbi.nih.gov/health/heart-healthy-living/healthy-foods",
                "docs", "none", NIH,
                "You should limit the amount of calories you get each day from added sugars.",
                "stay within your daily calorie limit."),
            doc("fda_howto", "FDA", "How to Understand and Use the Nutrition Facts Label",
                "https://www.fda.gov/food/nutrition-facts-label/how-understand-and-use-nutrition-facts-label",
                "docs", "none", FDA,
                "Added Sugars on the Nutrition Facts label include sugars",
                "staying within calorie limits."),
            doc("hp2030_nws10", "HHS ODPHP (Healthy People 2030)",
                "Reduce consumption of added sugars by people aged 2 years and over (NWS-10)",
                "https://odphp.health.gov/healthypeople/objectives-and-data/browse-objectives/nutrition-and-healthy-eating/reduce-consumption-added-sugars-people-aged-2-years-and-over-nws-10",
                "reference", "none", HHS,
                "Added sugars in foods and drinks can make it hard",
                "consume too much added sugar."),
        ],
    },
]


class BuildError(Exception):
    pass


def build():
    prompts, documents, problems = [], [], []
    for q in QUESTIONS:
        seen_urls = set()
        ids = []
        for d in q["docs"]:
            did = f"{q['id']}__{d['key']}"
            where = f"{q['id']}/{d['key']}"
            if d["answers"] not in LEVELS:
                problems.append(f"{where}: answers must be one of {sorted(LEVELS)}")
            if not d.get("rights"):
                problems.append(f"{where}: no rights statement")
            if d["url"] in seen_urls:
                problems.append(f"{where}: second document from the same source page")
            seen_urls.add(d["url"])
            try:
                text = sources.span(d["url"], d["start"], d["end"], d["multi_block"])
            except sources.SpanError as e:
                problems.append(f"{where}: {e}")
                continue
            snap = sources.load(d["url"])
            documents.append({
                "doc_id": did, "prompt_id": q["id"], "format": d["format"],
                "domain": q["domain"], "is_target": False,
                "answers": d["answers"], "words": len(text.split()),
                "source": {"agency": d["agency"], "title": d["title"], "url": d["url"],
                           "rights": d["rights"], "rights_evidence": d["evidence"],
                           "snapshot_sha256": snap["text_sha256"],
                           "retrieved_utc": snap["retrieved_utc"],
                           "method": snap["method"]},
                "variants": {"control": text},
            })
            ids.append(did)
        prompts.append({
            "prompt_id": q["id"], "domain": q["domain"], "question": q["question"],
            # No target yet -- screen.py chooses it. run_pilot.py requires the field,
            # so it names the first document provisionally; nothing reads it as a target.
            "target_doc_id": ids[0] if ids else None,
            "target_format": q["docs"][0]["format"],
            "doc_ids": ids,
        })

    if problems:
        raise BuildError("corpus not built:\n  " + "\n  ".join(problems))

    corpus = {
        "corpus_version": "rankable-screen-v0",
        "intervention": "none -- baseline screening corpus for ROADMAP item 11",
        "n_prompts": len(prompts), "n_docs": len(documents),
        "formats": sorted({d["format"] for d in documents}),
        "domains": sorted({q["domain"] for q in QUESTIONS}),
        "prompts": prompts, "documents": documents,
    }
    blob = json.dumps(corpus, sort_keys=True, separators=(",", ":")).encode()
    corpus["corpus_sha256"] = hashlib.sha256(blob).hexdigest()
    OUT.write_text(json.dumps(corpus, indent=2, ensure_ascii=False) + "\n")
    return corpus


def main():
    try:
        corpus = build()
    except BuildError as e:
        print(e)
        sys.exit(1)
    print(f"wrote {OUT.name}  sha256 {corpus['corpus_sha256'][:16]}")
    print(f"{corpus['n_prompts']} questions, {corpus['n_docs']} documents, every excerpt "
          "sliced from a snapshot\n")
    by_q = {}
    for d in corpus["documents"]:
        by_q.setdefault(d["prompt_id"], []).append(d)
    for p in corpus["prompts"]:
        ds = by_q[p["prompt_id"]]
        lv = {k: sum(1 for d in ds if d["answers"] == k) for k in ("direct", "partial", "none")}
        print(f'{p["prompt_id"]}: "{p["question"]}"')
        print(f"  {len(ds)} documents -- {lv['direct']} direct, {lv['partial']} partial, "
              f"{lv['none']} none")
        for d in ds:
            print(f"  {d['doc_id'].split('__')[1]:<14}{d['answers']:<9}{d['words']:>4}w  "
                  f"{d['variants']['control'][:78]}")
        print()


if __name__ == "__main__":
    main()
