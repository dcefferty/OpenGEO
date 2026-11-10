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

# fueleconomy.gov is run for DOE and EPA by a contractor lab, so unlike the other pages
# its text is not plainly a federal employee's work. Recorded as such, not assumed.
FUELECONOMY_RIGHTS = ("US federal website (DOE and EPA), administered for them by Oak Ridge "
                      "National Laboratory; 17 U.S.C. 105 status of contractor-written text "
                      "not confirmed. Short excerpt quoted for research")

# Metadata for pages no earlier corpus used. Every other page's agency, title, rights and
# format are reused from the corpus that first carried it (see `known_sources`).
NEW_SOURCES = {
    "https://www.irs.gov/businesses/small-businesses-self-employed/irs-audits": {
        "agency": "IRS", "title": "IRS audits", "format": "docs",
        "rights": "US federal work (IRS), 17 U.S.C. 105"},
    "https://www.fda.gov/consumers/consumer-updates/spilling-beans-how-much-caffeine-too-much": {
        "agency": "FDA", "title": "Spilling the Beans: How Much Caffeine is Too Much?",
        "format": "news", "rights": "US federal work (FDA), 17 U.S.C. 105"},
    # batch 2 (fetched 2026-11-09, after .gov hosts were allowlisted)
    "https://www.fueleconomy.gov/feg/how_tested.shtml": {
        "agency": "DOE/EPA (fueleconomy.gov)", "title": "How Vehicles Are Tested",
        "format": "docs", "rights": FUELECONOMY_RIGHTS},
    "https://www.fueleconomy.gov/feg/maintain.jsp": {
        "agency": "DOE/EPA (fueleconomy.gov)",
        "title": "Gas Mileage Tips - Keeping Your Vehicle in Shape",
        "format": "docs", "rights": FUELECONOMY_RIGHTS},
    "https://www.fueleconomy.gov/feg/coldweather.shtml": {
        "agency": "DOE/EPA (fueleconomy.gov)", "title": "Fuel Economy in Cold Weather",
        "format": "docs", "rights": FUELECONOMY_RIGHTS},
    "https://www.fueleconomy.gov/feg/hotweather.shtml": {
        "agency": "DOE/EPA (fueleconomy.gov)", "title": "Fuel Economy in Hot Weather",
        "format": "docs", "rights": FUELECONOMY_RIGHTS},
    "https://www.fueleconomy.gov/feg/info.shtml": {
        "agency": "DOE/EPA (fueleconomy.gov)", "title": "Frequently Asked Questions",
        "format": "reference", "rights": FUELECONOMY_RIGHTS},
    "https://www.epa.gov/greenvehicles/fuel-economy-and-ev-range-testing": {
        "agency": "EPA", "title": "Fuel Economy and EV Range Testing", "format": "docs",
        "rights": "US federal work (EPA), 17 U.S.C. 105"},
    "https://odphp.health.gov/our-work/nutrition-physical-activity/physical-activity-guidelines": {
        "agency": "HHS ODPHP", "title": "Physical Activity Guidelines for Americans",
        "format": "docs", "rights": "US federal work (HHS), 17 U.S.C. 105"},
    "https://odphp.health.gov/our-work/nutrition-physical-activity/physical-activity-guidelines/current-guidelines/top-10-things-know": {
        "agency": "HHS ODPHP",
        "title": "Top 10 Things to Know About the Second Edition of the Physical Activity "
                 "Guidelines for Americans",
        "format": "reference", "rights": "US federal work (HHS), 17 U.S.C. 105"},
    "https://www.nia.nih.gov/health/exercise-and-physical-activity/four-types-exercise-can-improve-your-health-and-physical": {
        "agency": "NIH NIA",
        "title": "Three Types of Exercise Can Improve Your Health and Physical Ability",
        "format": "docs", "rights": "US federal work (NIH), 17 U.S.C. 105"},
    "https://odphp.health.gov/myhealthfinder/health-conditions/diabetes/watch-your-weight": {
        "agency": "HHS ODPHP (MyHealthfinder)", "title": "Aim for a Healthy Weight",
        "format": "docs", "rights": "US federal work (HHS), 17 U.S.C. 105"},
    # batch 3 (2026-11-10)
    "https://www.tsa.gov/travel/security-screening/whatcanibring/all": {
        "agency": "TSA", "title": "What Can I Bring?", "format": "reference", "rights": "US federal work (TSA), 17 U.S.C. 105"},
    "https://www.tsa.gov/travel/security-screening/liquids-aerosols-gels-rule": {
        "agency": "TSA", "title": "Liquids, Aerosols, and Gels Rule", "format": "docs", "rights": "US federal work (TSA), 17 U.S.C. 105"},
    "https://www.tsa.gov/travel/security-screening/whatcanibring/items/baby-formula": {
        "agency": "TSA", "title": "Baby Formula", "format": "reference", "rights": "US federal work (TSA), 17 U.S.C. 105"},
    "https://www.tsa.gov/travel/security-screening/whatcanibring/items/juice-babies": {
        "agency": "TSA", "title": "Juice for Babies", "format": "reference", "rights": "US federal work (TSA), 17 U.S.C. 105"},
    "https://www.tsa.gov/travel/frequently-asked-questions/breast-milk-formula-and-juice-exempt-3-1-1-liquids-rule": {
        "agency": "TSA",
        "title": "Is Breast Milk, Formula and Juice exempt from the 3-1-1 liquids rule?",
        "format": "reference", "rights": "US federal work (TSA), 17 U.S.C. 105"},
    "https://www.tsa.gov/travel/frequently-asked-questions": {
        "agency": "TSA", "title": "Frequently Asked Questions", "format": "reference", "rights": "US federal work (TSA), 17 U.S.C. 105"},
    "https://www.energy.gov/energysaver/thermostats": {
        "agency": "DOE", "title": "Thermostats", "format": "docs",
        "rights": "US federal work (DOE), 17 U.S.C. 105"},
    "https://www.ssa.gov/benefits/retirement/": {
        "agency": "SSA", "title": "Retirement Benefits", "format": "docs",
        "rights": "US federal work (SSA), 17 U.S.C. 105"},
    "https://www.fda.gov/regulatory-information/search-fda-guidance-documents/small-entity-compliance-guide-health-claims-calcium-and-osteoporosis-and-calcium-vitamin-d-and": {
        "agency": "FDA",
        "title": "Small Entity Compliance Guide: Health Claims on Calcium and Osteoporosis; "
                 "and Calcium, Vitamin D, and Osteoporosis",
        "format": "docs", "rights": "US federal work (FDA), 17 U.S.C. 105"},
    "https://www.nhlbi.nih.gov/health/heart-healthy-living": {
        "agency": "NIH NHLBI", "title": "Heart-Healthy Living", "format": "docs",
        "rights": "US federal work (NIH), 17 U.S.C. 105"},
    "https://www.usa.gov/government-home-loans": {
        "agency": "GSA (USAGov)",
        "title": "Government-backed home loans and mortgage assistance",
        "format": "reference", "rights": "US federal work (GSA), 17 U.S.C. 105"},
    "https://www.consumerfinance.gov/archive/blog/7-factors-determine-your-mortgage-interest-rate/": {
        "agency": "CFPB", "title": "Seven factors that determine your mortgage interest rate",
        "format": "blog", "rights": "US federal work (CFPB), 17 U.S.C. 105"},
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

# --------------------------------------------------------------------------- batch 2
#
# Built 2026-11-09, after batch 1's screen (pre-registration, Deviations, 2026-11-08):
# all six batch-1 controls landed at or above 0.74, and four failed at the ceiling. Batch 2
# is built from scratch under the same checks, with two construction changes, both
# allowed for new questions by that entry:
#
#   - the target sits TWO dimensions from the question (METHODOLOGY.md section 9): an
#     unrelated aspect of the subject -- how mileage is measured, an exemption petition
#     against the rule, what alarms cost -- not a neighbouring attribute of it
#   - at least two non-targets sit CLOSER to the question than the target does: same
#     subject, the question's own dimension, facts withheld. Each question keeps one or
#     two clearly tangential documents as well.
#
# Section 9 measured two-dimensions-away authored controls at 0.11-0.17; batch 1's real
# spans one dimension away ran 0.74-0.94 against v0.4's 0.41-0.75. Whether real text two
# dimensions away lands inside the gate is what this batch's screen finds out.

BATCH_2 = [
    {
        "prompt_id": "auto_tire_pressure_mpg",
        "domain": "automotive",
        "question": "How much does driving on under-inflated tires lower a car's gas mileage?",
        "answer": r"\bpsi\b|inflat|tire pressure",
        "target": {   # two away: how MPG is measured in the lab
            "url": "https://www.fueleconomy.gov/feg/how_tested.shtml",
            "start": "In the laboratory, the vehicle's drive wheels are placed on a machine",
            "end": "These cycles simulate \"typical\" trips in the city or on the highway.",
            "replace": "Engineers adjust the amount of energy required to move the rollers to "
                       "account for wind resistance and the vehicle's weight.",
            "with": "Under-inflated tires can lower gas mileage by about 0.2% for every 1 psi "
                    "drop in the average pressure of all tires.",
            "figures": [("https://www.fueleconomy.gov/feg/maintain.jsp",
                         "Under-inflated tires can lower gas mileage by about 0.2% for every 1 "
                         "psi drop in the average pressure of all tires.")],
        },
        "others": [
            # closer: other maintenance that lowers mileage
            ("https://www.fueleconomy.gov/feg/maintain.jsp",
             "You can improve your gas mileage by 1%-2% by using the manufacturer's",
             "to be sure it contains friction-reducing additives."),
            # closer: conditions that lower mileage
            ("https://www.fueleconomy.gov/feg/coldweather.shtml",
             "Cold weather and winter driving conditions can reduce your fuel economy",
             "About two-thirds of the extra energy consumed is used to heat the cabin."),
            ("https://www.fueleconomy.gov/feg/hotweather.shtml",
             "Hot weather can actually increase your fuel economy.",
             "using the air conditioning (AC) can reduce fuel economy."),
            # tangential: a tax on poor fuel economy
            ("https://www.fueleconomy.gov/feg/info.shtml",
             "The Energy Tax Act of 1978 established a Gas Guzzler Tax", None),
            # tangential: EV range testing
            ("https://www.epa.gov/greenvehicles/fuel-economy-and-ev-range-testing",
             "A vehicle with a fully charged battery is driven continuously", None),
        ],
    },
    {
        "prompt_id": "legal_cooling_off_days",
        "domain": "legal",
        "question": "How many days do you have to cancel a door-to-door sale under the FTC's "
                    "Cooling-Off Rule?",
        "answer": r"\b(three|3)\b|\bthird\b|\bdays?\b|midnight|72 hours",
        "target": {   # two away: a 1996 exemption petition against the rule
            "url": "https://www.ftc.gov/news-events/news/press-releases/1996/03/ftc-today-announced-it-has-denied-request-exemption-ftcs-cooling-rule-filed-seven-life-insurance",
            "start": "After evaluating the request, the Commission determined", "end": None,
            "replace": "The Commission also determined that the petitioners did not "
                       "demonstrate any compelling reason to treat the sale of pre-need "
                       "funeral arrangements differently from other in-home sales.",
            "with": "Under the Cooling-Off Rule, consumers have three days to cancel certain "
                    "sales made at their home, workplace, dormitory, or a seller's temporary "
                    "location, such as a hotel room.",
            "figures": [("https://consumer.ftc.gov/articles/buyers-remorse-ftcs-cooling-rule-may-help",
                         "The Cooling-Off Rule gives you three days to cancel certain sales "
                         "made at your home, workplace, or dormitory, or at a seller's "
                         "temporary location, like a hotel or motel room, convention center, "
                         "fairground, or restaurant.")],
        },
        "others": [
            # closer: what the seller must give you about cancelling
            ("https://consumer.ftc.gov/articles/buyers-remorse-ftcs-cooling-rule-may-help",
             "By law, the seller has to tell you at the time of the sale about your right",
             "must be in the same language that's used in the sales presentation."),
            # closer: why the rule lets consumers cancel
            ("https://www.ftc.gov/news-events/news/press-releases/1995/10/fyi-ftc-has-decided-retain-minor-changes-its-cooling-rule",
             "Door-to-door sales and face-to-face transactions at places other than", None),
            # the rule's 2009 review: comment period
            ("https://www.ftc.gov/news-events/news/press-releases/2009/07/commission-reopens-public-comment-period-cooling-rule",
             "In the April notice, the FTC stated that the public comment period", None),
            # tangential: disputing credit report errors
            ("https://consumer.ftc.gov/articles/disputing-errors-your-credit-reports",
             "Both the credit bureau and the business that supplied the information", None),
            # tangential: credit repair
            ("https://consumer.ftc.gov/articles/fixing-your-credit-faqs",
             "Is there information on your credit report that's correct", None),
        ],
    },
    {
        "prompt_id": "health_bp_threshold",
        "domain": "health",
        "question": "At what blood pressure reading is an adult considered to have high "
                    "blood pressure?",
        "answer": r"mm ?Hg|\d{2,3} ?/ ?\d{2,3}|systolic|diastolic|\b(120|130|139|140|80|89|90)\b"
                  r"|top number|bottom number",
        "target": {   # two away: stress and heart health
            "url": "https://www.nhlbi.nih.gov/health/heart-healthy-living/manage-stress",
            "start": "Research suggests that an emotionally upsetting event", "end": None,
            "replace": "Research suggests that an emotionally upsetting event, particularly "
                       "one involving anger, can serve as a trigger for a heart attack or "
                       "angina in some people.",
            "with": "High blood pressure, also called hypertension, is blood pressure that is "
                    "consistently at or above 130/80 mm Hg, which is higher than normal.",
            "figures": [("https://www.cdc.gov/high-blood-pressure/about/index.html",
                         "High blood pressure, also called hypertension, is blood pressure "
                         "that is higher than normal. High blood pressure is consistently at "
                         "or above 130/80 mm Hg.")],
        },
        "others": [
            # closer: how high blood pressure is detected
            ("https://www.nia.nih.gov/health/high-blood-pressure/high-blood-pressure-and-older-adults",
             "High blood pressure often has no signs or symptoms, but routine checks",
             "may suggest exercise, changes in your diet, and medications."),
            ("https://www.fda.gov/drugs/information-consumers-and-patients-drugs/high-blood-pressure-understanding-silent-killer",
             "Early detection of high blood pressure is very important.", None),
            # closer: who develops it
            ("https://www.nhlbi.nih.gov/health/high-blood-pressure/causes",
             "Men are more likely than women to develop high blood pressure",
             "lower the chance of pregnancy complications and won't harm the developing baby."),
            # tangential: an eating plan
            ("https://www.nhlbi.nih.gov/education/dash-eating-plan",
             "DASH (Dietary Approaches to Stop Hypertension) is a flexible",
             "and tropical oils such as coconut, palm kernel, and palm oils"),
            # tangential: heart-healthy living in general
            ("https://www.nhlbi.nih.gov/health/heart-healthy-living",
             "Heart-healthy living involves understanding your risk", None),
        ],
    },
    {
        "prompt_id": "fitness_weekly_minutes",
        "domain": "fitness",
        "question": "How many minutes of moderate-intensity aerobic activity should adults "
                    "get each week?",
        "answer": r"\bminutes?\b|\bhours?\b|\b(150|300|75|60|30)\b|\bper week\b|\ba week\b"
                  r"|\beach week\b",
        "target": {   # two away: the guidelines as a publication
            "url": "https://odphp.health.gov/our-work/nutrition-physical-activity/physical-activity-guidelines",
            "start": "Physical activity is key to improving the health of the nation.",
            "end": None,
            "replace": "Learn ways to help people understand the benefits of physical activity "
                       "and how to make it a part of their regular routine.",
            "with": "To attain the most health benefits, adults need at least 150 to 300 "
                    "minutes of moderate-intensity aerobic activity each week.",
            "figures": [("https://odphp.health.gov/our-work/nutrition-physical-activity/physical-activity-guidelines/current-guidelines/top-10-things-know",
                         "To attain the most health benefits from physical activity, adults "
                         "need at least 150 to 300 minutes of moderate-intensity aerobic "
                         "activity, like brisk walking or fast dancing, each week.")],
        },
        "others": [
            # closer: what kind of activity, and how much is safe
            ("https://odphp.health.gov/our-work/nutrition-physical-activity/physical-activity-guidelines/current-guidelines/top-10-things-know",
             "The first key guideline for adults is to move more and sit less.", None),
            ("https://www.nia.nih.gov/health/exercise-and-physical-activity/four-types-exercise-can-improve-your-health-and-physical",
             "Most people tend to focus on one type of exercise or activity",
             "such as yoga, dancing, or water aerobics."),
            ("https://www.nhlbi.nih.gov/health/heart-healthy-living/physical-activity",
             "Talk with your healthcare provider before you start a new exercise plan.",
             "such as brisk walking, running, biking, and swimming."),
            # tangential: snacks, and weight
            ("https://www.niddk.nih.gov/health-information/weight-management/healthy-eating-physical-activity-for-life/health-tips-for-adults",
             "Have healthy snacks on hand.", None),
            ("https://odphp.health.gov/myhealthfinder/health-conditions/diabetes/watch-your-weight",
             "If you have overweight and have risk factors for heart disease", None),
        ],
    },
    {
        "prompt_id": "home_smoke_alarm_replace",
        "domain": "consumer_product",
        "question": "How often should you replace a smoke alarm?",
        "answer": r"\byears?\b|\bannual\w*|\bmonth\w*|\btwice\b|\bdecade|\bforever\b|\b10\b(?!,\d)"
                  r"|\bten\b|\bold\b",
        "target": {   # two away: what alarms cost
            "url": "https://www.usfa.fema.gov/prevention/home-fires/prepare-for-fire/smoke-alarms/",
            "start": "Smoke alarms are not expensive and are worth the lives they can help save.",
            "end": "check with your local fire marshal for information on what type of alarm "
                   "you need.",
            "replace": "Contact your local fire department's nonemergency phone number for "
                       "more information.",
            "with": "Smoke alarms do not last forever; get new ones every 10 years.",
            "figures": [("https://www.usfa.fema.gov/prevention/home-fires/prepare-for-fire/smoke-alarms/",
                         "Smoke alarms do not last forever. Get new smoke alarms every 10 years.")],
        },
        "others": [
            # closer: where to put alarms, keeping them working
            ("https://www.cpsc.gov/Newsroom/News-Releases/2004/CPSC-Warns-Millions-of-Americans-Have-Smoke-Alarms-that-Dont-Work",
             "CPSC recommends consumers place a smoke alarm that meets the requirements", None),
            ("https://www.cpsc.gov/Newsroom/News-Releases/2023/Its-Time-to-Change-Smoke-and-Carbon-Monoxide-Alarm-Batteries-as-Daylight-Saving-Time-Ends",
             "Many electronic devices and appliances will adjust automatically",
             "making working smoke and CO alarms all the more important."),
            ("https://onsafety.cpsc.gov/blog/2019/10/29/its-time-check-and-change-your-smoke-and-carbon-monoxide-alarm-batteries/",
             "CPSC estimates that in 2016, there were nearly 352,000 residential",
             "resulted from fires in homes with no working smoke alarms."),
            # tangential: escaping a fire, dryer fires
            ("https://www.ready.gov/home-fires",
             "Drop down to the floor and crawl low, under any smoke to your exit.",
             "Tell the emergency operator where the person is located."),
            ("https://www.cpsc.gov/Newsroom/News-Releases/2023/Save-Daylight-Save-Lives-Replace-Batteries-in-Smoke-and-Carbon-Monoxide-Alarms",
             "Clothes dryers can be a hidden hazard.",
             "the outdoor vent flap will open when the dryer is operating."),
        ],
    },
    {
        "prompt_id": "realestate_fha_down_payment",
        "domain": "real_estate",
        "question": "What is the minimum down payment for an FHA loan?",
        "answer": r"\d+(\.\d+)? ?(%|percent)|\bpercent\b|no down payment|zero down"
                  r"|no-down-payment|minimum down|\bas low as\b",
        "target": {   # two away: other federal homebuying programs
            "url": "https://www.usa.gov/government-home-loans",
            "start": "HUD's Good Neighbor Next Door Sales Program offers large discounts",
            "end": "EEMs can also be used to finance energy-efficient home improvements.",
            "replace": "EEMs can be used to purchase or refinance an existing or new Energy "
                       "Star-certified home.",
            "with": "FHA loans are available with a down payment of 3.5 percent or higher.",
            "figures": [("https://www.consumerfinance.gov/archive/blog/how-decide-how-much-spend-your-down-payment/",
                         "FHA loans are available with a down payment of 3.5 percent or higher.")],
        },
        "others": [
            # closer: paying for the down payment, and around it
            ("https://www.consumerfinance.gov/archive/blog/how-decide-how-much-spend-your-down-payment/",
             "Gifts from family or friends.", None),
            ("https://www.consumerfinance.gov/ask-cfpb/what-kind-of-down-payment-do-i-need-how-does-the-amount-of-down-payment-i-make-affect-the-terms-of-my-mortgage-loan-en-120/",
             "Don't forget to factor in all the upfront costs you will have",
             "what options you have when you shop around for different loans."),
            ("https://www.consumerfinance.gov/ask-cfpb/what-is-mortgage-insurance-and-how-does-it-work-en-1953/",
             "Mortgage insurance, no matter what kind, protects the lender", None),
            # tangential: rate types, loan standards
            ("https://www.consumerfinance.gov/archive/blog/7-factors-determine-your-mortgage-interest-rate/",
             "Interest rates come in two basic types: fixed and adjustable.",
             "to see how this choice affects interest rates."),
            ("https://www.consumerfinance.gov/about-us/blog/qualified-mortgages-what-are-they-and-what-do-they-mean-for-you/",
             "Not every loan has to be a standard QM.", None),
        ],
    },
]

# --------------------------------------------------------------------------- batch 3
#
# Built 2026-11-10, after batch 2's screen (pre-registration, Deviations, 2026-11-10):
# batch 1's targets, one dimension away, failed at the ceiling; batch 2's, two away,
# kept 4 of 6 and failed only at the floor, on the two targets furthest from their
# questions (stress for a blood-pressure question; a regulatory petition). Batch 3 keeps
# batch 2's construction and narrows it to what was kept: the target is on the
# question's own SUBJECT, on an unrelated aspect of it (where to mount the thermostat,
# how credit scores vary, earning while on benefits), never a different subject. At
# least two non-targets sit closer to the question; one or two are tangential.

BATCH_3 = [
    {
        "prompt_id": "travel_tsa_liquids",
        "domain": "travel",
        "question": "What is the largest liquid container you can bring in a carry-on bag "
                    "through TSA airport security?",
        "answer": r"ounces?|\boz\b|\bml\b|millilit|3-1-1|3\.4|\b100\b|quart|travel.size"
                  r"|liters?|gallons?",
        "target": {   # same subject, other aspect: additional screening, asking TSA
            "url": "https://www.tsa.gov/travel/security-screening/whatcanibring/all",
            "start": "Even if an item is generally permitted, it may be subject to additional",
            "end": "live assistance is available from 8 am - 6 pm (ET).",
            "replace": "For items not listed here, our AskTSA team looks forward to "
                       "answering your questions 365 days a year; live assistance is "
                       "available from 8 am - 6 pm (ET).",
            "with": "Liquids, aerosols, gels, creams and pastes in your carry-on bag are "
                    "limited to travel-sized containers that are 3.4 ounces (100 "
                    "milliliters) or less per item through the checkpoint.",
            "figures": [("https://www.tsa.gov/travel/security-screening/liquids-aerosols-gels-rule",
                         "These are limited to travel-sized containers that are 3.4 ounces "
                         "(100 milliliters) or less per item.")],
        },
        "others": [
            # closer: liquids that may exceed the rule, and how liquids are screened
            ("https://www.tsa.gov/travel/security-screening/liquids-aerosols-gels-rule",
             "The duty free liquids were purchased internationally",
             "the purchase was made within 48 hours."),
            ("https://www.tsa.gov/travel/security-screening/whatcanibring/items/baby-formula",
             "Although not required, to expedite the screening process", None),
            ("https://www.tsa.gov/travel/security-screening/whatcanibring/items/juice-babies",
             "TSA X-ray machines do not adversely affect food or medicines.", None),
            ("https://www.tsa.gov/travel/frequently-asked-questions/breast-milk-formula-and-juice-exempt-3-1-1-liquids-rule",
             "Ice packs, freezer packs, frozen gel packs and other accessories", None),
            # tangential: lost and found
            ("https://www.tsa.gov/travel/frequently-asked-questions",
             "TSA makes every effort to reunite passengers with items left behind", None),
        ],
    },
    {
        "prompt_id": "home_thermostat_setback",
        "domain": "home_diy",
        "question": "How much can you save on heating and cooling by turning your "
                    "thermostat back 7 to 10 degrees for 8 hours a day?",
        "answer": r"\d+ ?%|percent|\d+ ?°|degrees",
        "target": {   # same subject, other aspect: where to mount the thermostat
            "url": "https://www.energy.gov/energysaver/thermostats",
            "start": "The location of your thermostat can affect its performance", "end": None,
            "replace": "To operate properly, a thermostat must be on an interior wall away "
                       "from direct sunlight, drafts, doorways, skylights, and windows.",
            "with": "Turning your thermostat back 7°-10°F for 8 hours a day can save as much "
                    "as 10% a year on heating and cooling.",
            "figures": [("https://www.energy.gov/energysaver/thermostats",
                         "You can save as much as 10% a year on heating and cooling by simply "
                         "turning your thermostat back 7°-10°F for 8 hours a day from its "
                         "normal setting.")],
        },
        "others": [
            # closer: other ways to cut heating and cooling use
            ("https://www.energystar.gov/saveathome/heating-cooling/duct-sealing/benefits",
             "Sealing and insulating ducts can help with common comfort problems",
             "reducing the risk of pollutants entering ducts and circulating through your home."),
            ("https://www.energystar.gov/saveathome/seal_insulate/rule_your_attic",
             "Making sure your attic is well-sealed and properly insulated", None),
            ("https://www.energystar.gov/saveathome/seal_insulate/why-seal-and-insulate",
             "Less pollen, dust and insects (or pests) entering your home",
             "the equivalent of having a window open every day of the year!"),
            # tangential: heating with a stove; how EPA modelled homes
            ("https://www.ready.gov/home-fires",
             "Never use a stove range or oven to heat your home.", None),
            ("https://www.energystar.gov/saveathome/seal_insulate/methodology",
             "Geographic climate factors, regional construction styles", None),
        ],
    },
    {
        "prompt_id": "retirement_full_age",
        "domain": "retirement",
        "question": "What is the full retirement age for Social Security if you were born "
                    "in 1960 or later?",
        "answer": r"\b(6[0-9]|70)s?\b|sixty|seventy",
        "target": {   # same subject, other aspect: working while receiving benefits
            "url": "https://www.ssa.gov/benefits/retirement/planner/applying2.html",
            "start": "You may work after you start receiving benefits",
            "end": "regardless of your yearly earnings.",
            "replace": "We may withhold some of your benefits if you earn more than the "
                       "yearly earnings limit.",
            "with": "If you were born in 1960 or later, your full retirement age is 67.",
            "figures": [("https://www.ssa.gov/benefits/retirement/planner/1960.html",
                         "If you were born in 1960 or later, your full retirement age is 67")],
        },
        "others": [
            # closer: claiming early or late, without the ages
            ("https://www.ssa.gov/benefits/retirement/planner/agereduction.html",
             "There are advantages and disadvantages to taking your benefit before",
             "delayed retirement credits that would increase your monthly benefit."),
            ("https://www.ssa.gov/benefits/retirement/planner/delayret.html",
             "Choosing when to begin your retirement benefits is an important", None),
            ("https://www.ssa.gov/faqs/en/questions/KA-03391.html",
             "On the other hand, if you delay claiming your benefit",
             "by creating or signing in to your personal my Social Security."),
            # tangential: Medicare and taxes; the program
            ("https://www.ssa.gov/retirement/plan-for-retirement",
             "If you're getting Medicare Part B (medical insurance)",
             "request to have them withheld."),
            ("https://www.ssa.gov/benefits/retirement/",
             "Social Security is part of the retirement plan for almost every",
             "makes it easy to apply for benefits."),
        ],
    },
    {
        "prompt_id": "credit_negative_info_years",
        "domain": "credit",
        "question": "How long can accurate negative information, like late payments, stay "
                    "on your credit report?",
        "answer": r"\byears?\b|\bseven\b|\b7\b|\b10\b|\bten\b|forever|time limits?",
        "target": {   # same subject, other aspect: why credit scores differ
            "url": "https://www.consumerfinance.gov/ask-cfpb/what-is-a-credit-score-en-315/",
            "start": "You do not have just \"one\" credit score.",
            "end": "Most credit scores range from 300-850.",
            "replace": "Usually a higher score makes it easier to qualify for a loan and may "
                       "result in a better interest rate or loan terms.",
            "with": "Credit reporting companies can generally report negative information, "
                    "such as late payments, about your account payment history for up to "
                    "seven years.",
            "figures": [("https://www.consumerfinance.gov/ask-cfpb/how-long-does-information-stay-on-my-credit-report-en-323/",
                         "Credit reporting companies can generally report negative "
                         "information about your credit account payment history for up to "
                         "seven years, and may report positive information for longer.")],
        },
        "others": [
            # closer: removing negative information, and correcting errors
            ("https://www.consumerfinance.gov/ask-cfpb/is-it-possible-to-remove-accurate-negative-information-from-my-credit-report-en-1249/",
             "You can also dispute negative information that arose from identity theft",
             "It's probably a credit repair scam."),
            ("https://www.consumerfinance.gov/ask-cfpb/how-long-does-information-stay-on-my-credit-report-en-323/",
             "Many companies promise to \"repair\" or \"fix\" your credit", None),
            ("https://www.fdic.gov/consumer-resource-center/credit-reports",
             "If you identify information in your file that is incomplete or inaccurate",
             "may continue to report information it has verified as accurate."),
            # tangential: imposter sites; what bureaus collect
            ("https://consumer.ftc.gov/articles/free-credit-reports",
             "You might see companies and sites offering free credit reports", None),
            ("https://www.consumerfinance.gov/ask-cfpb/what-is-a-credit-report-en-309/",
             "Most people have more than one credit report.", None),
        ],
    },
    {
        "prompt_id": "nutrition_vitamin_d_adults",
        "domain": "nutrition",
        "question": "How much vitamin D do adults aged 19 to 70 need each day?",
        "answer": r"\bIU\b|international units|\bmcg\b|micrograms?|\b(400|600|800|15|20)\b"
                  r"|4,000|recommended (daily |dietary )?amounts?|\bRDA\b",
        "target": {   # same subject, other aspect: vitamin D and blood sugar
            "url": "https://ods.od.nih.gov/factsheets/VitaminD-Consumer/",
            "start": "Vitamin D helps your body regulate blood sugar levels.", "end": None,
            "replace": "Other studies show that vitamin D supplements don't stop most people "
                       "with prediabetes from developing diabetes.",
            "with": "Adults aged 19 to 70 years need 15 mcg (600 IU) of vitamin D each day.",
            "figures": [("https://ods.od.nih.gov/factsheets/VitaminD-Consumer/",
                         "Adults 19–70 years 15 mcg (600 IU)")],
        },
        "others": [
            # closer: getting enough vitamin D from food
            ("https://www.niams.nih.gov/health-topics/calcium-and-vitamin-d-important-bone-health",
             "In the United States, most people do not consume enough vitamin D",
             "but most other dairy products do not have added vitamin D."),
            ("https://www.dietaryguidelines.gov/resources/2020-2025-dietary-guidelines-online-materials/food-sources-select-nutrients/food-sources-vitamin-d",
             "Getting enough vitamin D is important for strong bones", None),
            ("https://www.nia.nih.gov/health/vitamins-and-supplements/vitamins-and-minerals-older-adults",
             "It is usually better to get the nutrients you need from food",
             "may recommend a vitamin or dietary supplement."),
            # tangential: label claims; calcium
            ("https://www.fda.gov/regulatory-information/search-fda-guidance-documents/small-entity-compliance-guide-health-claims-calcium-and-osteoporosis-and-calcium-vitamin-d-and",
             "2. What specific requirements must be met to make a claim",
             "the only recognized risk factor for the development of osteoporosis."),
            ("https://ods.od.nih.gov/factsheets/Calcium-Consumer/",
             "Calcium is a mineral your body needs to build and maintain strong bones",
             "Vitamin D helps your body absorb calcium."),
        ],
    },
    {
        "prompt_id": "housing_cost_burden",
        "domain": "real_estate",
        "question": "What share of its income does a household have to spend on housing to "
                    "be considered cost-burdened?",
        "answer": r"\d+(\.\d+)? ?%|percent|\bhalf\b|\bthird\b|one-third|\bmajority\b",
        "target": {   # same subject, other aspect: how HUD's CHAS data are organised
            "url": "https://www.huduser.gov/portal/datasets/cp/CHAS/bg_chas.html",
            "start": "In addition to estimating low-income housing needs, the CHAS data",
            "end": "which are grouped by theme.",
            "replace": "To streamline the data and make it easier to use, HUD has created a "
                       "series of \"tables,\" which are grouped by theme.",
            "with": "Households are considered cost-burdened when they spend more than 30% of "
                    "their income on rent, mortgage payments, and other housing costs.",
            "figures": [("https://www.census.gov/newsroom/press-releases/2024/renter-households-cost-burdened-race.html",
                         "Households are considered cost-burdened when they spend more than "
                         "30% of their income on rent, mortgage payments, and other housing "
                         "costs, according to the U.S. Department of Housing and Urban "
                         "Development (HUD).")],
        },
        "others": [
            # closer: housing costs against income, without the threshold
            ("https://www.census.gov/library/stories/2022/12/housing-costs-burden.html",
             "High housing costs can impact the amount of money households are able",
             "continue to be burdened by housing expenses."),
            ("https://www.census.gov/library/stories/2023/03/low-income-renters-spent-larger-share-of-income-on-rent.html",
             "For example, while the median housing cost ratio was higher",
             "compared to those in higher-income groups."),
            ("https://www.census.gov/newsroom/press-releases/2024/renter-households-cost-burdened-race.html",
             "\"Housing costs rose between 2022 and 2023 for both homeowners and renters.", None),
            # tangential: a data release schedule; buying a home
            ("https://www.census.gov/newsroom/press-releases/2022/renters-burdened-by-housing-costs.html",
             "The Census Bureau is set to release ACS 5-year Public Use Microdata", None),
            ("https://www.consumerfinance.gov/archive/blog/how-decide-how-much-spend-your-down-payment/",
             "Buying a home is exciting.",
             "join the conversation on Facebook and Twitter using #ShopMortgage."),
        ],
    },
]

BATCHES = {1: BATCH_1, 2: BATCH_2, 3: BATCH_3}

# prompt_ids that cleared the screen, in the order they enter the round corpus. Empty
# until batch 1 is screened; filled in by a dated commit that cites the screen output.
KEPT = [
    # batch 1, screened 2026-11-08 (results/screen_realtext_h4_b1.jsonl): 2 of 6 kept
    "cyber_password_length",
    "finance_emergency_400",
    # batch 2, screened 2026-11-10 (results/screen_realtext_h4_b2.jsonl): 4 of 6 kept
    "auto_tire_pressure_mpg",
    "fitness_weekly_minutes",
    "home_smoke_alarm_replace",
    "realestate_fha_down_payment",
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
        source, fmt = meta.get(url, ({"url": url}, None))
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
