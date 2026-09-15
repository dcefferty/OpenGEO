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
- **Answer levels are declared, not inferred.** `direct` states the amount the question
  asks for, for the population and context it asks about; `partial` states a related
  amount (another population, a broader quantity such as total debt rather than housing,
  or a worked example) or implies it; `none` is on-topic with no amount. The screen does not use these -- it decides on
  citation data alone -- but analysis of what the engines reward does.

Questions are chosen where authoritative sources state the answer in different forms,
which the probes found is what gives citation a movable middle. A question with one
canonical answer every source repeats screened empty.

    python3 corpus/build_corpus_rankable.py      # one corpus file per screening batch
"""
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import sources  # noqa: E402

CORPUS_DIR = pathlib.Path(__file__).parent

# Each screening run is one batch with its own corpus file, so adding questions never
# changes a corpus that already has run data. Batch 0 keeps the version string it was
# run under -- it is recorded in every row of its results file.
VERSIONS = {0: "rankable-screen-v0"}


def out_path(batch):
    return CORPUS_DIR / f"corpus_rankable_screen_b{batch}.json"


def version(batch):
    return VERSIONS.get(batch, f"rankable-screen-v0-b{batch}")


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
        "batch": 0,
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
    {
        "id": "finance_housingshare",
        "batch": 1,
        "domain": "finance",
        "question": "What share of my income should go to housing costs?",
        "docs": [
            doc("huduser_chas", "HUD Office of Policy Development and Research",
                "CHAS: Background",
                "https://www.huduser.gov/portal/datasets/cp/CHAS/bg_chas.html",
                "reference", "direct", "US federal work (HUD), 17 U.S.C. 105",
                "Cost burden - Monthly housing costs (including utilities) exceeding 30%",
                "exceeding 50% of monthly income.", multi_block=True),
            doc("census_2024", "US Census Bureau",
                "Nearly Half of Renter Households Are Cost-Burdened, Proportions Differ by Race",
                "https://www.census.gov/newsroom/press-releases/2024/renter-households-cost-burdened-race.html",
                "news", "direct", "US federal work (Census Bureau), 17 U.S.C. 105",
                "Households are considered cost-burdened when they spend more than 30% of their income on rent",
                "are considered severely cost-burdened."),
            doc("census_19m", "US Census Bureau",
                "More Than 19 Million Renters Burdened by Housing Costs",
                "https://www.census.gov/newsroom/press-releases/2022/renters-burdened-by-housing-costs.html",
                "news", "direct", "US federal work (Census Bureau), 17 U.S.C. 105",
                "Over 40% (19 million) of renter households",
                "definition of affordable housing."),
            doc("census_lowinc", "US Census Bureau",
                "Share of Income Needed to Pay Rent Increased the Most for Low-Income Households",
                "https://www.census.gov/library/stories/2023/03/low-income-renters-spent-larger-share-of-income-on-rent.html",
                "news", "direct", "US federal work (Census Bureau), 17 U.S.C. 105",
                "When a household has a cost ratio of over 30%, it is considered cost-burdened",
                "have cost ratios of over 50%."),
            doc("census_story22", "US Census Bureau",
                "Renters More Likely Than Homeowners to Spend More Than 30% of Income on Housing",
                "https://www.census.gov/library/stories/2022/12/housing-costs-burden.html",
                "news", "direct", "US federal work (Census Bureau), 17 U.S.C. 105",
                "Over 19 million U.S. renter households spent more than 30%",
                "rent, mortgage and other housing needs.", multi_block=True),
            doc("cfpb_qm_blog", "CFPB",
                "Qualified Mortgages: what are they and what do they mean for you?",
                "https://www.consumerfinance.gov/about-us/blog/qualified-mortgages-what-are-they-and-what-do-they-mean-for-you/",
                "blog", "partial", "US federal work (CFPB), 17 U.S.C. 105",
                "To get a standard Qualified Mortgage, your monthly debt-to-income ratio",
                "much lower than 43 percent of their income."),
            doc("cfpb_qm_press", "CFPB",
                "CFPB Issues Two Final Rules to Promote Access to Responsible, Affordable Mortgage Credit",
                "https://www.consumerfinance.gov/about-us/newsroom/consumer-financial-protection-bureau-issues-two-final-rules-promote-access-responsible-affordable-mortgage-credit/",
                "news", "partial", "US federal work (CFPB), 17 U.S.C. 105",
                "The Bureau has issued two rules related to QM loans.",
                "a new category for QMs, Seasoned QMs."),
            doc("cfpb_dti", "CFPB", "What is a debt-to-income ratio?",
                "https://www.consumerfinance.gov/ask-cfpb/what-is-a-debt-to-income-ratio-why-is-the-43-debt-to-income-ratio-important-en-1791/",
                "reference", "partial", "US federal work (CFPB), 17 U.S.C. 105",
                "To calculate your DTI, you add up all your monthly debt payments",
                "($2,000 is 33% of $6,000.)"),
            doc("hud_dti_archive", "HUD (FHA)", "HOC Reference Guide: Debt-to-Income Ratio",
                "https://archives.hud.gov/offices/hsg/sfh/ref/sfhp2-12.cfm",
                "docs", "partial", "US federal work (HUD), 17 U.S.C. 105",
                "When either or both of the permissible ratios of 31%/43%",
                "(Handbook 4155.1, Section 6.D)."),
        ],
    },
]


class BuildError(Exception):
    pass


def build(batch):
    prompts, documents, problems = [], [], []
    for q in [q for q in QUESTIONS if q["batch"] == batch]:
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
        "corpus_version": version(batch),
        "intervention": "none -- baseline screening corpus for ROADMAP item 11",
        "n_prompts": len(prompts), "n_docs": len(documents),
        "formats": sorted({d["format"] for d in documents}),
        "domains": sorted({q["domain"] for q in QUESTIONS if q["batch"] == batch}),
        "prompts": prompts, "documents": documents,
    }
    blob = json.dumps(corpus, sort_keys=True, separators=(",", ":")).encode()
    corpus["corpus_sha256"] = hashlib.sha256(blob).hexdigest()
    out_path(batch).write_text(json.dumps(corpus, indent=2, ensure_ascii=False) + "\n")
    return corpus


def main():
    for batch in sorted({q["batch"] for q in QUESTIONS}):
        try:
            corpus = build(batch)
        except BuildError as e:
            print(f"batch {batch}: {e}")
            sys.exit(1)
        print(f"batch {batch}: wrote {out_path(batch).name}  sha256 {corpus['corpus_sha256'][:16]}")
        by_q = {}
        for d in corpus["documents"]:
            by_q.setdefault(d["prompt_id"], []).append(d)
        for p in corpus["prompts"]:
            ds = by_q[p["prompt_id"]]
            lv = {k: sum(1 for d in ds if d["answers"] == k) for k in ("direct", "partial", "none")}
            print(f'  {p["prompt_id"]}: "{p["question"]}"')
            print(f"    {len(ds)} documents -- {lv['direct']} direct, {lv['partial']} partial, "
                  f"{lv['none']} none")
            for d in ds:
                print(f"    {d['doc_id'].split('__')[1]:<16}{d['answers']:<9}{d['words']:>4}w  "
                      f"{d['variants']['control'][:70]}")
        print()


if __name__ == "__main__":
    main()
