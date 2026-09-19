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
  page a federal work: MedlinePlus Encyclopedia articles are A.D.A.M., Inc. content,
  NCBI Bookshelf hosts WHO guidelines, and VA News publishes guest posts -- both VA home
  loan articles found while sourcing were written by mortgage-industry authors, one a
  director at a private lender. Check the byline and author bio, not the domain. A
  document without a rights statement fails.
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

They also need **at least 8 on-topic candidates**. Engines cite a sticky number of
documents regardless of how many are offered, so a four- or five-document set has nearly
all of it cited and every document pinned. Across the first ten screened questions,
candidate count separated kept from discarded perfectly (7-9 against 4-6) while the count
of directly answering documents did not (2-5 in both).

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
VA = "US federal work (Department of Veterans Affairs), 17 U.S.C. 105"
FDIC = "US federal work (FDIC), 17 U.S.C. 105"
SEC = "US federal work (SEC), 17 U.S.C. 105"
FED = "US federal work (Federal Reserve Board), 17 U.S.C. 105"
IRS = "US federal work (IRS), 17 U.S.C. 105"
EPA = "US federal work (EPA / ENERGY STAR), 17 U.S.C. 105"
SSA = "US federal work (Social Security Administration), 17 U.S.C. 105"
NIST = "US federal work (NIST), 17 U.S.C. 105"
CISA = "US federal work (CISA), 17 U.S.C. 105"
FTC = "US federal work (FTC), 17 U.S.C. 105"
CPSC = "US federal work (CPSC), 17 U.S.C. 105"
FEMA = "US federal work (FEMA / US Fire Administration), 17 U.S.C. 105"


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
    {
        "id": "finance_downpayment",
        "batch": 2,
        "domain": "finance",
        "question": "How much should I put down when buying a home?",
        "docs": [
            doc("cfpb_dp_blog", "CFPB", "How to decide how much to spend on your down payment",
                "https://www.consumerfinance.gov/archive/blog/how-decide-how-much-spend-your-down-payment/",
                "blog", "direct", "US federal work (CFPB), 17 U.S.C. 105",
                "One of the toughest parts of buying a home for the first time",
                "what works best for your situation."),
            doc("cfpb_dp_kind", "CFPB", "What kind of down payment do I need?",
                "https://www.consumerfinance.gov/ask-cfpb/what-kind-of-down-payment-do-i-need-how-does-the-amount-of-down-payment-i-make-affect-the-terms-of-my-mortgage-loan-en-120/",
                "reference", "direct", "US federal work (CFPB), 17 U.S.C. 105",
                "Generally, the larger the down payment you are able to make",
                "or obtain an FHA, VA, or USDA loan."),
            doc("cfpb_pmi", "CFPB", "What is private mortgage insurance?",
                "https://www.consumerfinance.gov/ask-cfpb/what-is-private-mortgage-insurance-en-122/",
                "reference", "partial", "US federal work (CFPB), 17 U.S.C. 105",
                "Private mortgage insurance (PMI) is a type of mortgage insurance",
                "if you stop making payments on your loan."),
            doc("cfpb_mi_how", "CFPB", "What is mortgage insurance and how does it work?",
                "https://www.consumerfinance.gov/ask-cfpb/what-is-mortgage-insurance-and-how-does-it-work-en-1953/",
                "reference", "partial", "US federal work (CFPB), 17 U.S.C. 105",
                "Typically, borrowers making a down payment of less than 20 percent",
                "U.S. Department of Agriculture (USDA) loans."),
            doc("va_purchase", "Department of Veterans Affairs", "Purchase loan",
                "https://www.va.gov/housing-assistance/home-loans/loan-types/purchase-loan/",
                "docs", "partial", VA,
                "No need for private mortgage insurance (PMI) or mortgage insurance premiums (MIP).",
                "against future loss.",
                evidence="va.gov benefits page, not VA News (which carries guest posts)"),
            doc("cfpb_fha", "CFPB", "FHA loans",
                "https://www.consumerfinance.gov/owning-a-home/fha-loans/",
                "docs", "partial", "US federal work (CFPB), 17 U.S.C. 105",
                "For borrowers with good credit and a medium (10-15 percent) down payment",
                "can often be the cheapest option."),
            doc("va_fee", "Department of Veterans Affairs", "VA funding fee and loan closing costs",
                "https://www.va.gov/housing-assistance/home-loans/funding-fee-and-closing-costs/",
                "docs", "partial", VA,
                "For example: Let's say you're using a VA-backed loan for the first time",
                "not the purchase price of the home.",
                evidence="va.gov benefits page, not VA News (which carries guest posts)"),
        ],
    },
    {
        "id": "finance_emergencyfund",
        "batch": 2,
        "domain": "finance",
        "question": "How much money should I keep in an emergency fund?",
        "docs": [
            doc("fdic_2024", "FDIC", "Starting Small Can Lead to Big Savings",
                "https://www.fdic.gov/consumer-resource-center/2024-01/starting-small-can-lead-big-savings",
                "docs", "direct", FDIC,
                "Also, consider setting a goal to build up an",
                "not covered by insurance."),
            doc("cfpb_guide", "CFPB", "An essential guide to building an emergency fund",
                "https://www.consumerfinance.gov/an-essential-guide-to-building-an-emergency-fund/",
                "docs", "direct", "US federal work (CFPB), 17 U.S.C. 105",
                "The amount you need to have in an emergency savings fund depends on your situation.",
                "how much you want to have set aside."),
            doc("sec_rainyday", "SEC Office of Investor Education and Advocacy", "Save for a Rainy Day",
                "https://www.investor.gov/introduction-investing/investing-basics/save-and-invest/save-rainy-day",
                "reference", "direct", SEC,
                "Most smart investors put enough money in savings to cover an emergency",
                "when they need it."),
            doc("fdic_2009", "FDIC", "Ways to Spend Less, Save More in Good Times and Bad",
                "https://www.fdic.gov/consumer-resource-center/2009-ways-spend-less-save-more-good-times-and-bad",
                "docs", "direct", FDIC,
                "Have an emergency savings account.",
                "six or more months of anticipated expenses."),
            doc("cfpb_prep", "CFPB", "Preparedness means rebuilding toward a brighter future with emergency savings",
                "https://www.consumerfinance.gov/archive/blog/preparedness-means-rebuilding-toward-brighter-future-emergency-savings/",
                "blog", "partial", "US federal work (CFPB), 17 U.S.C. 105",
                "It might seem impossible to save enough",
                "when it is over."),
            doc("fed_shed26", "Federal Reserve Board",
                "Economic Well-Being of U.S. Households in 2025: Savings and Investments",
                "https://www.federalreserve.gov/publications/2026-economic-well-being-of-us-households-in-2025-savings-investments.htm",
                "reference", "partial", FED,
                "Having a buffer of savings for emergencies can help families cope with income fluctuations",
                "was unchanged from 2024 as well."),
            doc("fdic_editorial", "FDIC", "Your Savings: Good for You, Your Family, and Your Peace of Mind",
                "https://www.fdic.gov/news/editorials/your_savings.html",
                "blog", "partial", FDIC,
                "Putting even small amounts of money into a rainy-day fund",
                "earn a little interest on the money.",
                evidence="Byline: FDIC Chairman Sheila Bair, writing in official capacity"),
            doc("sec_buildwealth", "SEC Office of Investor Education and Advocacy",
                "Build Wealth Over Time Through Saving and Investing",
                "https://www.investor.gov/build-wealth-over-time-through-saving-and-investing",
                "docs", "none", SEC,
                "Start an emergency fund in a savings account at your bank or credit union",
                "if you have an unexpected expense."),
            doc("fdic_2025", "FDIC", "Saving for the Unexpected and Your Future",
                "https://www.fdic.gov/consumer-resource-center/2025-01/saving-unexpected-and-your-future",
                "docs", "none", FDIC,
                "Saving for emergencies, retirement, or other expenses can seem difficult",
                "some of these questions."),
        ],
    },
    {
        "id": "nutrition_sodium",
        "batch": 2,
        "domain": "nutrition",
        "question": "How much sodium should an adult have per day?",
        "docs": [
            doc("odphp_tips", "HHS ODPHP (MyHealthfinder)", "Eat Less Sodium: Quick Tips",
                "https://odphp.health.gov/myhealthfinder/health-conditions/heart-health/eat-less-sodium-quick-tips",
                "docs", "direct", HHS,
                "Ask your doctor how much sodium is okay for you.",
                "no more than 1,200 mg a day", multi_block=True),
            doc("fda_diet", "FDA", "Sodium in Your Diet",
                "https://www.fda.gov/food/nutrition-education-resources-materials/sodium-your-diet",
                "docs", "direct", FDA,
                "Know the Daily Value.",
                "less than 2,300 milligrams (mg) per day."),
            doc("fda_cutback", "FDA", "Eating Too Much Salt? Ways to Cut Back...Gradually",
                "https://www.fda.gov/consumers/consumer-updates/eating-too-much-salt-ways-cut-backgradually",
                "blog", "direct", FDA,
                "You and your family can also take steps to ease into reducing",
                "more than the recommended limit."),
            doc("fda_goals", "FDA", "Guidance for Industry: Voluntary Sodium Reduction Goals",
                "https://www.fda.gov/regulatory-information/search-fda-guidance-documents/guidance-industry-voluntary-sodium-reduction-goals",
                "reference", "direct", FDA,
                "Average sodium intake in the U.S. is approximately 3,400 milligrams/day",
                "for those 14 years and older."),
            doc("nhlbi_dash", "NIH NHLBI", "DASH Eating Plan",
                "https://www.nhlbi.nih.gov/education/dash-eating-plan",
                "docs", "direct", NIH,
                "*1,500 milligrams (mg) sodium lowers blood pressure",
                "2,300 mg sodium daily."),
            doc("nhlbi_halt", "NIH NHLBI", "Halt the Salt: 5 Ways to Cut Down on Sodium",
                "https://www.nhlbi.nih.gov/news/2023/halt-salt-5-ways-cut-down-sodium-and-improve-your-heart-health",
                "news", "partial", NIH,
                "It's a fact: Americans love salty foods",
                "is only growing."),
        ],
    },
    {
        "id": "taxes_recordkeeping",
        "batch": 3,
        "domain": "taxes",
        "question": "How long should I keep my tax records?",
        "docs": [
            doc("irs_howlong", "IRS", "How long should I keep records?",
                "https://www.irs.gov/businesses/small-businesses-self-employed/how-long-should-i-keep-records",
                "reference", "direct", IRS,
                "Keep records for 3 years from the date you filed your original return",
                "if you do not file a return.", multi_block=True),
            doc("irs_tc305", "IRS", "Topic no. 305, Recordkeeping",
                "https://www.irs.gov/taxtopics/tc305",
                "reference", "direct", IRS,
                "6 years - If you don't report income that you should have reported",
                "6 years from the date you filed the return."),
            doc("irs_employment", "IRS", "Employment tax recordkeeping",
                "https://www.irs.gov/businesses/small-businesses-self-employed/employment-tax-recordkeeping",
                "docs", "direct", IRS,
                "Keep all records of employment taxes for at least four years after filing",
                "available for IRS review."),
            doc("irs_smallbiz", "IRS", "Common questions about recordkeeping for small businesses",
                "https://www.irs.gov/newsroom/common-questions-about-recordkeeping-for-small-businesses",
                "news", "direct", IRS,
                "The general rule is three years depending on the action",
                "recorded in the document."),
            doc("irs_recordkeeping", "IRS", "Recordkeeping",
                "https://www.irs.gov/businesses/small-businesses-self-employed/recordkeeping",
                "docs", "direct", IRS,
                "Keep all records of employment taxes for at least four years.",
                "at least four years."),
            doc("irs_statutes", "IRS",
                "Statutes of limitations for assessing, collecting and refunding tax",
                "https://www.irs.gov/filing/statutes-of-limitations-for-assessing-collecting-and-refunding-tax",
                "reference", "partial", IRS,
                "A statute of limitation is the time period established by law",
                "allow you to claim a refund."),
            doc("irs_news", "IRS",
                "Good recordkeeping year-round helps taxpayers avoid tax time frustration",
                "https://www.irs.gov/newsroom/good-recordkeeping-year-round-helps-taxpayers-avoid-tax-time-frustration",
                "news", "partial", IRS,
                "Tax-related records.",
                "a credit reported on their tax return."),
        ],
    },
    {
        "id": "home_energysaving",
        "batch": 3,
        "domain": "home_diy",
        "question": "How much can I save by air sealing and insulating my home?",
        "docs": [
            doc("es_method", "EPA ENERGY STAR", "Methodology for Estimated Energy Savings",
                "https://www.energystar.gov/saveathome/seal_insulate/methodology",
                "reference", "direct", EPA,
                "EPA estimates that homeowners can save an average of 15% on heating and cooling costs",
                "accessible basement rim joists."),
            doc("es_why", "EPA ENERGY STAR", "Why Seal and Insulate?",
                "https://www.energystar.gov/saveathome/seal_insulate/why-seal-and-insulate",
                "docs", "direct", EPA,
                "Air that leaks through your home's envelope",
                "floors over crawl spaces and basements."),
            doc("es_attic", "EPA ENERGY STAR", "Rule Your Attic! For Comfort and Savings",
                "https://www.energystar.gov/saveathome/seal_insulate/rule_your_attic",
                "blog", "direct", EPA,
                "A well-sealed and insulated attic can make a real difference",
                "floors over crawl spaces and basements."),
            doc("es_duct", "EPA ENERGY STAR", "Benefits of Duct Sealing",
                "https://www.energystar.gov/saveathome/heating-cooling/duct-sealing/benefits",
                "docs", "direct", EPA,
                "Leaky ducts can reduce heating and cooling system efficiency",
                "pay for itself in energy savings."),
        ],
    },
    {
        "id": "cooking_temperature",
        "batch": 4,
        "domain": "cooking",
        "question": "What internal temperature should I cook meat to?",
        "docs": [
            doc("fsis_doneness", "USDA FSIS", "Doneness Versus Safety",
                "https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/doneness-versus-safety",
                "docs", "direct", USDA,
                "FSIS recommends cooking whole poultry to a safe minimum internal temperature of 165",
                "choose to cook poultry to higher temperatures."),
            doc("usda_blog", "USDA", "Cooking Meat: Is It Done Yet?",
                "https://www.usda.gov/about-usda/news/blog/cooking-meat-it-done-yet",
                "blog", "direct", USDA,
                "Cook raw beef, pork, lamb and veal steaks, chops, and roasts",
                "160 F as measured with a food thermometer.", multi_block=True),
            doc("fsis_chart", "USDA FSIS", "Safe Minimum Internal Temperature Chart",
                "https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/safe-temperature-chart",
                "reference", "partial", USDA,
                "Cook all food to these minimum internal temperatures",
                "choose to cook food to higher temperatures."),
            doc("fs_minternal", "HHS FoodSafety.gov", "Cook to a Safe Minimum Internal Temperature",
                "https://www.foodsafety.gov/food-safety-charts/safe-minimum-internal-temperatures",
                "reference", "partial", HHS,
                "Follow the guidelines below for how to cook raw meat",
                "germs that cause food poisoning."),
        ],
    },
    {
        "id": "retirement_claimage",
        "batch": 4,
        "domain": "retirement",
        "question": "At what age should I start taking Social Security retirement benefits?",
        "docs": [
            doc("ssa_agered", "Social Security Administration",
                "Retirement Age and Benefit Reduction",
                "https://www.ssa.gov/benefits/retirement/planner/agereduction.html",
                "reference", "direct", SSA,
                "You can start receiving your Social Security retirement benefits as early as age 62.",
                "your benefit amount will increase."),
            doc("ssa_earlylate", "Social Security Administration", "Early or Late Retirement",
                "https://www.ssa.gov/oact/quickcalc/early_late.html",
                "reference", "direct", SSA,
                "A worker can choose to retire as early as age 62, but",
                "by retiring at age 70.", multi_block=True),
            doc("ssa_1960delay", "Social Security Administration", "Delayed Retirement, Born in 1960",
                "https://www.ssa.gov/benefits/retirement/planner/1960-delay.html",
                "reference", "direct", SSA,
                "The chart below explains how delayed retirement affects your benefit.",
                "124 percent of the monthly benefit"),
            doc("ssa_1960", "Social Security Administration", "Born in 1960 or later",
                "https://www.ssa.gov/benefits/retirement/planner/1960.html",
                "reference", "direct", SSA,
                "You can start receiving your Social Security retirement benefits as early as age 62,",
                "less than your full retirement benefit amount."),
            doc("ssa_delay", "Social Security Administration", "Delayed Retirement Credits",
                "https://www.ssa.gov/benefits/retirement/planner/delayret.html",
                "reference", "partial", SSA,
                "For example, if you reach your full retirement age (67) in June",
                "the year before your 69th birthday."),
        ],
    },
    {
        "id": "health_vitamind",
        "batch": 4,
        "domain": "health",
        "question": "How much vitamin D does an adult need per day?",
        "docs": [
            doc("ods_hp", "NIH Office of Dietary Supplements",
                "Vitamin D - Health Professional Fact Sheet",
                "https://ods.od.nih.gov/factsheets/VitaminD-HealthProfessional/",
                "reference", "direct", NIH,
                "These values range from 15 to 20 mcg (600-800 IU) for adults",
                "depending on age."),
            doc("nia_vit", "NIH National Institute on Aging",
                "Vitamins and Minerals for Older Adults",
                "https://www.nia.nih.gov/health/vitamins-and-supplements/vitamins-and-minerals-older-adults",
                "docs", "direct", NIH,
                # "If you are age 51-70..." appears twice on this page, under Men and
                # under Women, with identical wording; span() refused it. Anchored on the
                # unique vitamin D food-sources line so the passage is unambiguous.
                "You can get vitamin D from fatty fish",
                "If you are over age 70, you need at least 20 mcg (800 IU), but not more "
                "than 100 mcg (4,000 IU).", multi_block=True),
            doc("ods_con", "NIH Office of Dietary Supplements", "Vitamin D - Consumer Fact Sheet",
                "https://ods.od.nih.gov/factsheets/VitaminD-Consumer/",
                "reference", "partial", NIH,
                "The amount of vitamin D you need each day depends on your age.",
                "micrograms (mcg) and International Units (IU)."),
            doc("niams", "NIH NIAMS", "Calcium and Vitamin D: Important for Bone Health",
                "https://www.niams.nih.gov/health-topics/calcium-and-vitamin-d-important-bone-health",
                "docs", "partial", NIH,
                "Table 2 lists how much vitamin D people need every day",
                "to keep their bones healthy."),
            doc("fda_dv", "FDA", "Daily Value on the Nutrition and Supplement Facts Labels",
                "https://www.fda.gov/food/nutrition-facts-label/daily-value-nutrition-and-supplement-facts-labels",
                "docs", "none", FDA,
                "DVs are the recommended amounts of nutrients to consume or not to exceed each day.",
                "contributes to your daily diet."),
        ],
    },
    # Batch 5 retries the three questions batch 4 discarded. Each had only 4-5 candidates,
    # and candidate count -- not how many sources answer directly -- is what separated kept
    # from discarded across the first ten screens. Same question ids: batch 4's versions are
    # discarded and will not appear in the round.
    {
        "id": "cooking_temperature",
        "batch": 5,
        "domain": "cooking",
        "question": "What internal temperature should I cook meat to?",
        "docs": [
            doc("fsis_doneness", "USDA FSIS", "Doneness Versus Safety",
                "https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/doneness-versus-safety",
                "docs", "direct", USDA,
                "FSIS recommends cooking whole poultry to a safe minimum internal temperature of 165",
                "choose to cook poultry to higher temperatures."),
            doc("usda_blog", "USDA", "Cooking Meat: Is It Done Yet?",
                "https://www.usda.gov/about-usda/news/blog/cooking-meat-it-done-yet",
                "blog", "direct", USDA,
                "Cook raw beef, pork, lamb and veal steaks, chops, and roasts",
                "160 F as measured with a food thermometer.", multi_block=True),
            doc("usda_newtemp", "USDA", "Cooking Meat? Check the New Recommended Temperatures",
                "https://www.usda.gov/about-usda/news/blog/cooking-meat-check-new-recommended-temperatures",
                "blog", "direct", USDA,
                "Cooking Whole Cuts of Pork: USDA has lowered the recommended safe cooking temperature",
                "before carving or consuming."),
            doc("fsis_grill", "USDA FSIS", "Grilling Food Safely",
                "https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/grilling-food-safely",
                "docs", "direct", USDA,
                "Cook all raw beef, pork, lamb and veal steaks, chops, and roasts to a minimum internal temperature of 145",
                "at least 3 minutes before carving or consuming."),
            doc("fsis_howtemp", "USDA FSIS", "How Temperatures Affect Food",
                "https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/how-temperatures-affect-food",
                "reference", "direct", USDA,
                "Raw meat and poultry should always be cooked to a safe minimum internal temperature.",
                "no lower than 325"),
            doc("fsis_chart", "USDA FSIS", "Safe Minimum Internal Temperature Chart",
                "https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/safe-temperature-chart",
                "reference", "partial", USDA,
                "Cook all food to these minimum internal temperatures",
                "choose to cook food to higher temperatures."),
            doc("fs_minternal", "HHS FoodSafety.gov", "Cook to a Safe Minimum Internal Temperature",
                "https://www.foodsafety.gov/food-safety-charts/safe-minimum-internal-temperatures",
                "reference", "partial", HHS,
                "Follow the guidelines below for how to cook raw meat",
                "germs that cause food poisoning."),
            doc("fsis_therm", "USDA FSIS", "Kitchen Thermometers",
                "https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/kitchen-thermometers",
                "reference", "partial", USDA,
                "Many food handlers believe that visible indicators",
                "color and texture indicators are unreliable."),
        ],
    },
    {
        "id": "retirement_claimage",
        "batch": 5,
        "domain": "retirement",
        "question": "At what age should I start taking Social Security retirement benefits?",
        "docs": [
            doc("ssa_agered", "Social Security Administration", "Retirement Age and Benefit Reduction",
                "https://www.ssa.gov/benefits/retirement/planner/agereduction.html",
                "reference", "direct", SSA,
                "You can start receiving your Social Security retirement benefits as early as age 62.",
                "your benefit amount will increase."),
            doc("ssa_earlylate", "Social Security Administration", "Early or Late Retirement",
                "https://www.ssa.gov/oact/quickcalc/early_late.html",
                "reference", "direct", SSA,
                "A worker can choose to retire as early as age 62, but",
                "by retiring at age 70.", multi_block=True),
            doc("ssa_1960delay", "Social Security Administration", "Delayed Retirement, Born in 1960",
                "https://www.ssa.gov/benefits/retirement/planner/1960-delay.html",
                "reference", "direct", SSA,
                "The chart below explains how delayed retirement affects your benefit.",
                "124 percent of the monthly benefit"),
            doc("ssa_1960", "Social Security Administration", "Born in 1960 or later",
                "https://www.ssa.gov/benefits/retirement/planner/1960.html",
                "reference", "direct", SSA,
                "You can start receiving your Social Security retirement benefits as early as age 62,",
                "less than your full retirement benefit amount."),
            doc("ssa_faq", "Social Security Administration",
                "At what age should I start receiving my retirement benefits?",
                "https://www.ssa.gov/faqs/en/questions/KA-03391.html",
                "reference", "direct", SSA,
                "You can start receiving your Social Security retirement benefit as early as age 62.",
                "until your full retirement age."),
            doc("ssa_applying2", "Social Security Administration",
                "You Can Receive Benefits Before Your Full Retirement Age",
                "https://www.ssa.gov/benefits/retirement/planner/applying2.html",
                "reference", "direct", SSA,
                "If you wait until age 70 to start your benefits",
                "for each month you delay filing for benefits."),
            doc("ssa_plan", "Social Security Administration", "Plan for Retirement",
                "https://www.ssa.gov/retirement/plan-for-retirement",
                "docs", "direct", SSA,
                "Apply for your monthly Retirement benefit anytime between age 62 and 70.",
                "up until age 70."),
            doc("cfpb_claim", "CFPB", "Planning your Social Security claiming age",
                "https://www.consumerfinance.gov/consumer-tools/retirement/before-you-claim/",
                "docs", "direct", "US federal work (CFPB), 17 U.S.C. 105",
                "Under Social Security rules, you are allowed to claim your benefits as early as age 62.",
                "claim as late as age 70."),
            doc("ssa_delay", "Social Security Administration", "Delayed Retirement Credits",
                "https://www.ssa.gov/benefits/retirement/planner/delayret.html",
                "reference", "partial", SSA,
                "For example, if you reach your full retirement age (67) in June",
                "the year before your 69th birthday."),
            doc("ssa_ageinc", "Social Security Administration", "Retirement Age Calculator",
                "https://www.ssa.gov/benefits/retirement/planner/ageincrease.html",
                "reference", "partial", SSA,
                "Full retirement age, also called",
                "healthier in older age."),
        ],
    },
    {
        "id": "health_vitamind",
        "batch": 5,
        "domain": "health",
        "question": "How much vitamin D does an adult need per day?",
        "docs": [
            doc("ods_hp", "NIH Office of Dietary Supplements", "Vitamin D - Health Professional Fact Sheet",
                "https://ods.od.nih.gov/factsheets/VitaminD-HealthProfessional/",
                "reference", "direct", NIH,
                "These values range from 15 to 20 mcg (600-800 IU) for adults",
                "depending on age."),
            doc("nia_vit", "NIH National Institute on Aging", "Vitamins and Minerals for Older Adults",
                "https://www.nia.nih.gov/health/vitamins-and-supplements/vitamins-and-minerals-older-adults",
                "docs", "direct", NIH,
                "You can get vitamin D from fatty fish",
                "If you are over age 70, you need at least 20 mcg (800 IU), but not more "
                "than 100 mcg (4,000 IU).", multi_block=True),
            doc("ods_con", "NIH Office of Dietary Supplements", "Vitamin D - Consumer Fact Sheet",
                "https://ods.od.nih.gov/factsheets/VitaminD-Consumer/",
                "reference", "partial", NIH,
                "The amount of vitamin D you need each day depends on your age.",
                "micrograms (mcg) and International Units (IU)."),
            doc("niams", "NIH NIAMS", "Calcium and Vitamin D: Important for Bone Health",
                "https://www.niams.nih.gov/health-topics/calcium-and-vitamin-d-important-bone-health",
                "docs", "partial", NIH,
                "Table 2 lists how much vitamin D people need every day",
                "to keep their bones healthy."),
            doc("dga_foodsrc", "USDA / HHS Dietary Guidelines", "Food Sources of Vitamin D",
                "https://www.dietaryguidelines.gov/resources/2020-2025-dietary-guidelines-online-materials/food-sources-select-nutrients/food-sources-vitamin-d",
                "reference", "partial", USDA,
                "Getting enough vitamin D is important for strong bones and overall health.",
                "that contain it naturally."),
            doc("ods_calcium", "NIH Office of Dietary Supplements", "Calcium - Consumer Fact Sheet",
                "https://ods.od.nih.gov/factsheets/Calcium-Consumer/",
                "reference", "partial", NIH,
                "Calcium is found in many multivitamin/mineral supplements",
                "amount of calcium in the supplement."),
            doc("fda_dv", "FDA", "Daily Value on the Nutrition and Supplement Facts Labels",
                "https://www.fda.gov/food/nutrition-facts-label/daily-value-nutrition-and-supplement-facts-labels",
                "docs", "none", FDA,
                "DVs are the recommended amounts of nutrients to consume or not to exceed each day.",
                "contributes to your daily diet."),
            doc("fda_changes", "FDA", "Changes to the Nutrition Facts Label",
                "https://www.fda.gov/food/food-labeling-nutrition/changes-nutrition-facts-label",
                "docs", "none", FDA,
                "Manufacturers must declare the actual amount",
                "for other vitamins and minerals."),
        ],
    },
    {
        "id": "security_passwordlength",
        "batch": 6,
        "domain": "cybersecurity_consumer",
        "question": "How long should my password be?",
        "docs": [
            doc("nist_63b_pw", "NIST", "SP 800-63B: Strength of Passwords",
                "https://pages.nist.gov/800-63-4/sp800-63b/passwords/",
                "reference", "direct", NIST,
                "Passwords that are too short yield to brute-force attacks",
                "depends on the threat model being addressed."),
            doc("cisa_choose", "CISA", "Choosing and Protecting Passwords",
                "https://www.cisa.gov/news-events/news/choosing-and-protecting-passwords",
                "news", "direct", CISA,
                "The National Institute of Standards and Technology (NIST) has developed",
                "permissible (8-64 characters) when you can."),
            doc("ftc_pw", "FTC", "Creating Strong Passwords and Other Ways to Protect Your Accounts",
                "https://consumer.ftc.gov/articles/creating-strong-passwords-and-other-ways-protect-your-accounts",
                "blog", "direct", FTC,
                "When you set up an online account",
                "aim for at least 12 characters."),
            doc("cisa_smb", "CISA", "Require Strong Passwords",
                "https://www.cisa.gov/audiences/small-and-medium-businesses/secure-your-business/require-strong-passwords",
                "docs", "direct", CISA,
                "Random: A mix of upper/lowercase letters, numbers and symbols",
                "a passphrase of 5-7 unrelated words"),
            doc("nist_howto", "NIST", "How Do I Create a Good Password?",
                "https://www.nist.gov/cybersecurity-and-privacy/how-do-i-create-good-password",
                "blog", "direct", NIST,
                "The most important part of a good password is its length.",
                "would take at most 26 guesses."),
            doc("nist_blog", "NIST", "Easy Ways to Build a Better Password",
                "https://www.nist.gov/blogs/taking-measure/easy-ways-build-better-p5w0rd",
                "blog", "partial", NIST,
                "So, we've established that, at least for password purposes",
                "that would be a nightmare to type."),
            doc("nist_faq", "NIST", "SP 800-63 Digital Identity Guidelines FAQ",
                "https://pages.nist.gov/800-63-FAQ/",
                "reference", "none", NIST,
                "The following list of FAQs for Special Publication (SP) 800-63",
                "we will update these FAQs."),
            doc("cisa_train", "CISA", "Formulate Strong Passwords and PIN Codes",
                "https://www.cisa.gov/resources-tools/training/formulate-strong-passwords-and-pin-codes",
                "docs", "none", CISA,
                "Random. Use a random code as opposed to a simple pattern",
                "a simple pattern like 123456."),
        ],
    },
    {
        "id": "home_smokealarm",
        "batch": 6,
        "domain": "home_diy",
        "question": "How often should I test and replace my smoke alarm?",
        "docs": [
            doc("usfa_alarms", "FEMA US Fire Administration", "Smoke Alarms",
                "https://www.usfa.fema.gov/prevention/home-fires/prepare-for-fire/smoke-alarms/",
                "docs", "direct", FEMA,
                "Age matters when it comes to smoke alarms.",
                "10 years from the manufacture date."),
            doc("cpsc_2023b", "CPSC", "Save Daylight, Save Lives: Replace Batteries in Alarms",
                "https://www.cpsc.gov/Newsroom/News-Releases/2023/Save-Daylight-Save-Lives-Replace-Batteries-in-Smoke-and-Carbon-Monoxide-Alarms",
                "news", "direct", CPSC,
                "Test the alarms monthly and replace the batteries at least yearly",
                "unless the alarms have sealed 10-year batteries."),
            doc("cpsc_2015", "CPSC", "When Turning Clocks Back, Replace Batteries in Alarms",
                "https://www.cpsc.gov/Newsroom/News-Releases/2015/When-Turning-Clocks-Back-After-Daylight-Saving-Time-Replace-Batteries-in-Smoke-and-Carbon-Monoxide-Alarms",
                "news", "direct", CPSC,
                "Batteries should be replaced in smoke alarms at least once a year",
                "make sure that the alarms are working properly."),
            doc("ready_fires", "FEMA Ready.gov", "Home Fires",
                "https://www.ready.gov/home-fires",
                "docs", "direct", FEMA,
                "Replace batteries twice a year",
                "unless you are using 10-year lithium batteries."),
            doc("cpsc_2023a", "CPSC", "It's Time to Change Smoke and CO Alarm Batteries",
                "https://www.cpsc.gov/Newsroom/News-Releases/2023/Its-Time-to-Change-Smoke-and-Carbon-Monoxide-Alarm-Batteries-as-Daylight-Saving-Time-Ends",
                "news", "partial", CPSC,
                "WASHINGTON, D.C. - Daylight Saving Time ends on Sunday, November 6, 2022",
                "when you turn your clocks back one hour."),
            doc("cpsc_2004", "CPSC", "CPSC Warns: Millions Have Smoke Alarms That Don't Work",
                "https://www.cpsc.gov/Newsroom/News-Releases/2004/CPSC-Warns-Millions-of-Americans-Have-Smoke-Alarms-that-Dont-Work",
                "news", "partial", CPSC,
                "This is Fire Prevention Week",
                "the batteries are dead or missing."),
            doc("cpsc_blog", "CPSC", "It's Time. Check and Change Your Alarm Batteries",
                "https://onsafety.cpsc.gov/blog/2019/10/29/its-time-check-and-change-your-smoke-and-carbon-monoxide-alarm-batteries/",
                "blog", "partial", CPSC,
                "Consumers will turn their clocks back one hour",
                "in smoke and carbon monoxide (CO) alarms."),
            doc("usfa_prepare", "FEMA US Fire Administration", "Prepare for Fire",
                "https://www.usfa.fema.gov/prevention/home-fires/prepare-for-fire/",
                "docs", "none", FEMA,
                "The U.S. Fire Administration provides safety awareness materials",
                "about preparing for a home fire."),
        ],
    },
    {
        "id": "legal_coolingoff",
        "batch": 6,
        "domain": "legal",
        "question": "How long do I have to cancel a purchase made at my home?",
        "docs": [
            doc("ftc_remorse", "FTC", "Buyer's Remorse: The FTC's Cooling-Off Rule May Help",
                "https://consumer.ftc.gov/articles/buyers-remorse-ftcs-cooling-rule-may-help",
                "blog", "direct", FTC,
                "The Cooling-Off Rule gives you three days to cancel certain sales",
                "make a presentation in your home."),
            doc("ftc_rule", "FTC", "Cooling-off Period for Sales Made at Home or Other Locations",
                "https://www.ftc.gov/legal-library/browse/rules/cooling-period-sales-made-home-or-other-locations",
                "reference", "direct", FTC,
                "The Cooling Off Rule provides that it is unfair and deceptive",
                "within three business days of the transaction."),
            doc("ftc_2012", "FTC", "FTC Concludes Regulatory Review of Cooling Off Rule",
                "https://www.ftc.gov/news-events/news/press-releases/2012/12/ftc-concludes-regulatory-review-cooling-rule-proposes-increase-threshold-amount-coverage-rule-25-130",
                "news", "direct", FTC,
                "Currently, the Cooling Off Rule provides",
                "increase the $25 exempted dollar amount to $130."),
            doc("ftc_1995", "FTC", "FTC Has Decided To Retain with Minor Changes its Cooling-Off Rule",
                "https://www.ftc.gov/news-events/news/press-releases/1995/10/fyi-ftc-has-decided-retain-minor-changes-its-cooling-rule",
                "news", "direct", FTC,
                "The Federal Trade Commission has decided to retain with minor changes",
                "away from the seller's normal place of business."),
            doc("ftc_2009jul", "FTC", "Commission Reopens Public Comment Period On the Cooling Off Rule",
                "https://www.ftc.gov/news-events/news/press-releases/2009/07/commission-reopens-public-comment-period-cooling-rule",
                "news", "direct", FTC,
                "On April 21, 2009, the FTC issued a Federal Register notice",
                "right to cancel within three business days."),
            doc("ftc_1996", "FTC", "FTC Denies Cooling-Off Rule Exemption Request",
                "https://www.ftc.gov/news-events/news/press-releases/1996/03/ftc-today-announced-it-has-denied-request-exemption-ftcs-cooling-rule-filed-seven-life-insurance",
                "news", "direct", FTC,
                "The Cooling-Off Rule, promulgated in 1972, requires a seller",
                "three business days and receive a full refund."),
            doc("ftc_2009apr", "FTC", "Commission Approves Notice Seeking Comments on Cooling-Off Rule",
                "https://www.ftc.gov/news-events/news/press-releases/2009/04/commission-approves-federal-register-notice-seeking-comments-cooling-rule-commission-approves-final",
                "news", "partial", FTC,
                "The Rule also requires such sellers, within 10 businesses days",
                "any security interests created by the sale,"),
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
