#!/usr/bin/env python3
"""
OpenGEO corpus -- the specific-answer effect under competition (competition-v1).

H4 is the project's headline: replacing vague claims with specific figures
raised target CPR by +0.482 on corpus v0.4. But that corpus was built so the
target is the *only* document that answers the question, and the treatment arm
saturates at ~0.99. The delta is therefore mostly `1 - control`, a statement
about where the control sits (METHODOLOGY.md §9), and it is measured in a
setting practitioners almost never face: in the real world, someone else's
page usually answers the question too.

This corpus measures the effect with an answering competitor present.

    control          -- corpus v0.4 control, verbatim
    treatment        -- corpus v0.4 treatment, verbatim
    control_comp     -- v0.4 control target; one distractor replaced by an
                        answering competitor
    treatment_comp   -- v0.4 treatment target; the same competitor

A 2x2 within prompt: target (control/treatment) x competitor (absent/present).
The first pair replicates H4 on the five-engine panel in the same session as
the rest, so the interaction is not confounded with model drift since v0.4.
The second pair is H9. Within each pair the five non-target documents are
byte-identical, which keeps both contrasts paired.

**How the competitor is placed.** run_pilot.py takes the document set from
`prompt["doc_ids"]` and indexes each document's text by condition, so the set
cannot change between conditions. The competitor therefore occupies one
distractor's doc_id: in the two `_comp` conditions that document's variant is
the competitor text, and in the other two it is the original distractor. The
prompt records which doc_id this is as `competitor_doc_id`, and the displaced
distractor's format as `competitor_format`. In the `_comp` conditions,
`cited_doc_ids` containing that id means the competitor was cited.

**What a competitor is.** A document in its slot's register (blog, news, docs,
product, forum, reference) that answers the question with the *same* figures as
the treatment target, in different words. Same figures, because a competitor
stating different ones is a conflict between sources -- a different hypothesis
(H13 in the 2026-10-24 shortlist). Different words, because a near-copy of the
treatment would measure duplication rather than competition. Enforced at build
time:

  numerals     -- every numeric token in the competitor appears in the
                  treatment target (no new or conflicting figures)
  answers      -- the competitor carries at least one of the treatment's
                  figures that the control lacks
  not a copy   -- content-word Jaccard with the treatment below 0.60
  length       -- 50-110 words, the v0.3/v0.4 chunk regime

Competitor formats are assigned so each format is the competitor in 8 prompts
and never the target's own format.

Business and product names follow the convention of the skill's eval fixtures:
fictional, and named products reuse the v0.4 target's own name so a question
about "this" product is answered about the same product.

Reuses corpus v0.4's 48 prompts wholesale, loaded programmatically from
corpus_v0.4.json so there is no transcription drift from text already measured
against real models.
"""
import hashlib
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from check_variants import content_words  # noqa: E402

_HERE = pathlib.Path(__file__).parent
_V04 = json.loads((_HERE / "corpus_v0.4.json").read_text())

CONDITIONS = ["control", "treatment", "control_comp", "treatment_comp"]

# prompt_id -> (format of the distractor the competitor displaces, competitor text)
COMPETITORS = {
    "saas_uptime": ("news",
        "A survey of small engineering teams published this week found that most overpay "
        "for uptime monitoring. Teams of around five engineers typically spend $20-50/month, "
        "enough for 50 monitors checked every 60 seconds, while enterprise tiers starting "
        "near $400/month mainly suit companies with dedicated SRE staff. The report's authors "
        "recommended 30-second checks where budgets allow, noting that longer intervals miss "
        "a large share of brief outages, and advised buyers to avoid per-seat pricing."),
    "saas_pwmgr": ("forum",
        "r/ITManagers — We moved to a business password manager with SCIM last year. "
        "Offboarding is basically instant now: when HR disables someone in the directory, "
        "their vault access is gone within 5 minutes. Before that it took us around 4 days "
        "to chase down everything by hand. The activity log is kept 90 days on the standard "
        "plan; we pay for enterprise mainly because compliance wanted 365-day retention."),
    "cons_shoes": ("docs",
        "Care and replacement. Running shoe midsoles lose most of their cushioning between "
        "300 and 500 miles, so plan to replace a pair within that range even if the upper "
        "and outsole still look fine. Rotating between two pairs lets the foam recover "
        "between runs and extends each pair's usable life by roughly 20%. Log mileage per "
        "pair rather than relying on visible wear, which shows up well after the cushioning "
        "has declined."),
    "cons_espresso": ("reference",
        "Crema One is a semi-automatic home espresso machine with a 58mm portafilter and a "
        "stainless steel body. From a cold start it reaches brewing temperature in "
        "approximately 6 minutes, after which it maintains 9 bars of pressure at the group "
        "head. The manufacturer covers the machine with a two-year warranty. It is sold with "
        "a starter kit and a printed guide to dialling in a first shot."),
    "health_creatine": ("blog",
        "I get asked about creatine more than any other supplement, so here's the short "
        "version. For maintenance, take 3-5g of creatine monohydrate daily, including rest "
        "days. If you want to reach saturation faster, you can do an optional loading phase "
        "of 20g/day, split into smaller doses, for 5-7 days, then drop back to the "
        "maintenance dose. Skip the fancy forms: monohydrate is the one with the research "
        "behind it."),
    "health_sleep": ("product",
        "Quillmoor Sleep Band — wrist-worn sleep tracking with a nightly sleep score and "
        "stage breakdown. How accurate is it? Validated against lab polysomnography, consumer "
        "trackers like ours estimate total sleep time within about 20 minutes, and tend to "
        "overestimate it by 15-20 minutes. Stage classification agrees with the lab roughly "
        "50-65% of the time, so treat deep-sleep figures as a trend rather than a diagnosis. "
        "Syncs to the companion app each morning."),
    "fin_savings": ("docs",
        "Account terms. Promotional APYs on high-yield savings accounts are usually "
        "guaranteed for an introductory period of 3-6 months. When the promotion ends, the "
        "rate reverts to the standard variable rate, commonly 1-2 percentage points lower. "
        "Deposits are insured by the FDIC up to $250,000 per depositor, per insured bank, for "
        "each account ownership category. Review the rate schedule before opening an account."),
    "fin_index": ("blog",
        "Low-cost index funds are the boring backbone of most portfolios, and BroadMarket "
        "Total Index Fund is a good example of why. Its expense ratio is just 0.03%, a "
        "fraction of the 0.42% that comparable actively managed funds charge on average. If "
        "you're buying with a lump sum, the minimum is $3,000; set up an automatic investment "
        "plan instead and there's no minimum at all. For a first fund, it is hard to argue with."),
    "local_hvac": ("news",
        "With equipment prices rising, contractors are fielding more questions about when an "
        "HVAC repair stops making sense. The guideline most of them cite: consider replacing "
        "the system when a single repair would cost more than 30% of a new unit, or when the "
        "system is past 15 years old and the repair tops $500. Residential systems typically "
        "last 15-20 years, industry representatives said, and units still running on R-22 "
        "refrigerant face steep repair bills since its 2020 phase-out."),
    "local_movers": ("product",
        "Thistlecombe Movers — licensed interstate moving with free in-home surveys. Before "
        "you book anyone, know the warning signs of a moving scam: an estimate 30-50% below "
        "other quotes, no in-person or video survey, and a deposit request above 20% of the "
        "quoted total. We never ask for more than that, and our USDOT number is printed on "
        "every quote. Binding estimates available on request."),
    "travel_points": ("reference",
        "Co-branded airline credit cards earn miles on spending in exchange for an annual "
        "fee, commonly $95 for entry-level cards. For a casual traveller, net annual value "
        "after the fee is modest: at around $18,000 of yearly spend and an earn rate near "
        "1.4 cents per dollar, the card nets roughly $160 a year. Most of the card's total "
        "value comes from the one-time sign-up bonus, which can be worth about $600 in "
        "redemptions."),
    "travel_visa": ("forum",
        "r/travel — Priced this out for a trip to Peru last month. The standard policy was "
        "one number, and adding the 'cancel for any reason' rider bumped it by close to half. "
        "From what I've read that's normal: CFAR usually adds 40-50% to the premium. You only "
        "get part of your trip cost back with it, but for nonrefundable bookings it was worth "
        "it for the peace of mind."),
    "edu_bootcamp": ("product",
        "Forgeline Academy Full-Stack Bootcamp — live instruction, career coaching and a "
        "capstone project. Plan your schedule honestly: the full-time track takes roughly "
        "60-70 hours a week including homework, while the part-time track runs 15-20 hours a "
        "week over twice as long. Our outcomes are reported under CIRR standards, with 70-80% "
        "of graduates employed in a related role within 6 months."),
    "edu_certification": ("blog",
        "If you're starting PMP prep, know what you're walking into. The exam is 180 "
        "questions over 230 minutes, with a scheduled break halfway through. There's no fixed "
        "published passing score, because the cut score is set per exam form, but candidates "
        "who pass generally get around 61% of scored items right, landing in the 'target' or "
        "'above target' band. Before you can even book, you'll need 35 hours of project "
        "management education."),
    "diy_drill": ("reference",
        "Cordless drills run on rechargeable lithium-ion packs rated in amp-hours (Ah), a "
        "measure of stored charge. The drill in question ships with a 4.0Ah battery, enough "
        "for extended sessions such as a full weekend of deck building, and its rapid charger "
        "restores a fully depleted pack in approximately 45 minutes. Higher-capacity packs add "
        "runtime at the cost of weight, and packs are generally interchangeable within a "
        "manufacturer's tool line."),
    "diy_kit": ("forum",
        "r/HomeImprovement — Just did our hallway in the HearthLine oak laminate. Heads up, "
        "each box only covers 22.5 sq ft (8 planks), so measure carefully and buy extra for "
        "cuts. They tell you to let the unopened boxes acclimate in the room for 48 hours "
        "before installing; we waited longer because it's humid here and have had zero "
        "gapping. The click-lock went together fine without glue."),
    "pets_insurance": ("news",
        "Pet insurance enrolments continued to climb this year as veterinary costs rose. For "
        "dogs, monthly premiums typically fall between $25 and $70, depending on breed, age "
        "and the coverage level chosen, according to industry figures. Most insurers let "
        "owners choose an annual deductible of $100, $250 or $500, with higher deductibles "
        "lowering the monthly cost. Policies generally still exclude pre-existing conditions."),
    "pets_vaccine": ("docs",
        "Puppy vaccination schedule. Administer a series of 3-4 core vaccine doses between 6 "
        "and 16 weeks of age, spaced several weeks apart. The final rabies dose of the puppy "
        "series is typically given at 12-16 weeks, followed by a booster at one year of age. "
        "Adult dogs then move to a risk-based schedule set by the veterinarian according to "
        "lifestyle and local disease exposure."),
    "auto_evcharger": ("forum",
        "r/electricvehicles — Had a Level 2 charger put in this spring. It adds about 20-30 "
        "miles of range for every hour plugged in, so overnight charging is never an issue. "
        "The electrician ran a dedicated 240V, 50 amp circuit for it, though a 40 amp circuit "
        "works for lower-output units. Have them check your panel capacity first; ours almost "
        "needed an upgrade before the install could go ahead."),
    "auto_dashcam": ("docs",
        "Storage and recording. The RoadWitness 4K ships with a 128GB memory card, which holds "
        "approximately 14 hours of continuous loop footage before the oldest files are "
        "overwritten. Parking mode is included: when motion is detected near the parked "
        "vehicle, the camera records a 30-second clip automatically. GPS data, including speed "
        "and location, is embedded in each recorded file."),
    "legal_smallclaims": ("product",
        "Pinebrook Small Claims Kit — step-by-step forms and instructions for filing in small "
        "claims court. Know the limits before you file: most jurisdictions cap claims between "
        "$5,000 and $10,000, and court filing fees typically run $30-100 depending on the "
        "amount you claim. The kit includes a service-of-process checklist and a hearing "
        "preparation guide."),
    "legal_llc": ("reference",
        "A limited liability company (LLC) is formed by filing articles of organization with a "
        "state's business filing office. State filing fees for a standard LLC range from about "
        "$50 to $500 depending on jurisdiction. Standard processing typically takes 1-3 weeks, "
        "and many states offer expedited processing for an additional fee that can shorten "
        "this to 24-48 hours."),
    "career_negotiate": ("news",
        "Recruiters say candidates are negotiating job offers more often, and usually "
        "successfully. A realistic target for most roles is an increase of 5-15% over the "
        "initial offer, career advisers said, provided the request is backed by market data. "
        "Employers typically give candidates 3-5 business days to respond to a written offer, "
        "and short extensions are commonly granted on request."),
    "career_resume": ("blog",
        "The one-page resume rule stops applying once you have real experience behind you. "
        "With 10 years or more, two pages is completely normal and often expected. What matters "
        "more is what you cut: keep detailed work history to the most recent 10-15 years, and "
        "summarize or drop anything older. Hiring managers skim, so put your strongest recent "
        "roles first and make every line earn its space."),
    "nutr_protein": ("reference",
        "Protein requirements for people engaged in regular resistance training exceed those "
        "of sedentary adults. Research generally supports a daily intake of about 0.7-1g of "
        "protein per pound of body weight for this group. Total daily intake is considered "
        "more important than precise timing; the post-exercise 'anabolic window' is now "
        "understood to extend over several hours rather than the 30 minutes once believed."),
    "nutr_meal": ("product",
        "Steadfold Complete Meal Shake — a ready-to-mix meal replacement powder in chocolate "
        "and vanilla. Nutrition per serving: 400 calories and 7g of dietary fiber. Mix one "
        "scoop with 8-12oz of water, milk or a plant-based alternative and drink within 30 "
        "minutes. Not intended as a sole source of nutrition over extended periods."),
    "re_inspection": ("blog",
        "Booking a home inspection was the least stressful part of buying our first house, as "
        "long as you know what to expect. A standard inspection for a typical single-family "
        "home runs around $450, and the inspector will usually spend about 3 hours on site "
        "going through the property. Ask upfront whether radon testing or a sewer scope is "
        "included, since those are often add-ons that cost extra."),
    "re_warranty": ("news",
        "Home warranty sales rose this year as homeowners looked to hedge against appliance "
        "repair costs. Annual plans typically cost $500-700 depending on the coverage tier, "
        "according to providers, and homeowners pay a service call fee of $75-125 each time a "
        "technician visits for a claim. Most plans impose a 30-day waiting period before "
        "coverage begins."),
    "parent_carseat": ("forum",
        "r/beyondthebump — PSA since this comes up constantly: you don't have to flip the seat "
        "at 2. Most convertible seats let you stay rear-facing up to 40-50 lbs or the seat's "
        "height limit, which is printed on the label. The recommendation is rear-facing until "
        "at least age 2, and longer if your kid still fits. Our preschooler is still "
        "rear-facing and totally fine."),
    "parent_recall": ("docs",
        "Recall remedy instructions. This voluntary recall covers approximately 230,000 "
        "strollers. The hazard: the hinge mechanism can unexpectedly fold during use, and 12 "
        "incidents have been reported, including at least 4 minor injuries. Stop using the "
        "stroller and request the free repair kit, which will be shipped with installation "
        "instructions. Repaired strollers can return to normal use once the kit is fitted and "
        "the hinge locks firmly in place."),
    "game_pc_upgrade": ("news",
        "With graphics card prices easing, more gamers are weighing a GPU swap against a "
        "complete rebuild. Hardware testers report that a GPU-only upgrade typically raises "
        "frame rates by 40-70% when the CPU is not a bottleneck, compared with 80-120% for a "
        "full rebuild with a new processor and motherboard. They recommend a power supply "
        "rated at least 150W above the new card's rated draw."),
    "game_headset": ("reference",
        "SonicWave is a line of over-ear headsets aimed at players who want to move away from "
        "a cabled setup. Its wireless model lasts about 30 hours between charges and holds a "
        "stable link up to 40 feet from its receiver, which plugs into a free port on a "
        "computer or console. Like most headsets in this class, it trades some audio fidelity "
        "for the convenience of no cord."),
    "tax_freelance": ("blog",
        "My first year freelancing, the tax bill was a nasty surprise. Don't repeat my "
        "mistake: set aside 25-30% of your net income for self-employment and income tax "
        "combined. And you can't just pay once a year. Quarterly estimated payments are due in "
        "mid-April, June, September, and January of the following year. I put mine on the "
        "calendar the day I opened my business account."),
    "tax_deadline": ("docs",
        "Penalties for late filing and payment. If you owe tax and file late without an "
        "extension, the failure-to-file penalty is 5% of the unpaid tax for each month the "
        "return is late, up to a maximum of 25%. If you filed an extension but still owe, the "
        "failure-to-pay penalty applies instead, at 0.5% per month. Request an extension "
        "before the deadline to avoid the larger penalty."),
    "fit_homegym": ("product",
        "Ironwell Home Starter Bundle — adjustable dumbbells and an adjustable bench, the core "
        "of a basic home gym, for around $600 total. The full setup fits in about a 6x8 foot "
        "area, including space to move through each exercise. Rubber floor mats are "
        "recommended to protect both the floor and the equipment, and are sold separately."),
    "fit_hrzones": ("forum",
        "r/AdvancedRunning — Zone 2 is 60-70% of your max heart rate. Most endurance guidance "
        "I've seen says build up to 150-180 minutes a week there for aerobic base. Just note "
        "that the age-based formulas for max HR can be way off for some people, so a field "
        "test is worth doing before you set your zones."),
    "photo_lens": ("reference",
        "A 50mm prime lens is a fixed-focal-length lens commonly recommended as a first "
        "upgrade over a kit zoom. Affordable versions typically offer an aperture range of "
        "f/1.8 to f/16. Minimum focus distance is around 1.5 feet, which allows reasonably "
        "tight portraits but falls short of true macro reproduction. Because it cannot zoom, "
        "framing is adjusted by moving closer or further away."),
    "photo_raw": ("reference",
        "RAW is a family of image formats that store minimally processed data from a camera's "
        "sensor. A RAW file typically occupies 20-40MB per image, roughly 5-10 times the size "
        "of a JPEG at the same resolution. In exchange, RAW generally preserves 1-2 additional "
        "stops of recoverable dynamic range in highlights and shadows compared with an "
        "in-camera JPEG."),
    "garden_raisedbed": ("product",
        "Fernhollow Raised Bed Mix — a blend of compost, topsoil and aeration material for "
        "vegetable beds. Coverage guide: a standard 4x8 foot raised bed filled to a 12-inch "
        "depth takes about 20 bags. A 12-inch depth is enough for most vegetables, including "
        "root crops. Water the mix thoroughly after filling and let it settle before planting."),
    "garden_composter": ("forum",
        "r/composting — Got the DualBin tumbler last spring. Each side holds 27 gallons, so I "
        "fill one while the other cooks. In summer with a good green/brown mix I get finished "
        "compost in 4-6 weeks, slower when it's cold out. The raised stand has kept the "
        "raccoons out completely, and turning it is easy enough."),
    "sec_vpn": ("blog",
        "People ask me whether a VPN is worth it, and the practical answers matter more than "
        "the marketing. Most consumer subscriptions cover 5-10 devices at once, so one plan "
        "usually handles a whole household. And yes, you'll notice a slowdown: expect speeds "
        "about 10-25% lower than your unprotected connection, depending on how busy and how "
        "far away the server is."),
    "sec_breach": ("product",
        "Harrowgate Identity Watch — complimentary for customers affected by the recent "
        "retailer data incident. The breach affected approximately 2.3 million customer "
        "accounts and exposed names, email addresses and hashed passwords; payment card data "
        "was stored separately and was not affected. Enroll to receive alerts if your "
        "information appears for sale online."),
    "cook_airfryer": ("news",
        "A new basket-style air fryer drew attention at a home appliance show this week for "
        "pairing family-sized capacity with high power. The model holds 6 quarts and draws "
        "1700 watts, which reviewers said lets it crisp food quickly rather than just drying "
        "it out. Exhibitors noted that capacity remains the specification buyers most often "
        "get wrong."),
    "cook_knife": ("news",
        "Kitchenware maker Hearthstone launched a forged knife this month aimed at home cooks "
        "who want one blade for nearly every task. It measures 8 inches and is made from "
        "high-carbon stainless steel, honed to 15 degrees on each side. Early reviewers praised "
        "its weight and balance in long prep sessions; the maker advises washing it by hand."),
    "loan_forgiveness": ("forum",
        "r/StudentLoans — Got my forgiveness last year so I can answer this one. Most "
        "income-driven plans forgive whatever's left after 20-25 years of qualifying payments, "
        "depending on your plan and loan type. As for taxes: federally, forgiven balances "
        "aren't counted as taxable income through 2025, but that has changed before, so check "
        "the current rules. Also recertify every year, since your payment gets recalculated."),
    "loan_rate": ("docs",
        "Interest rates and annual limits. New federal undergraduate loans first disbursed "
        "after July 1 carry a fixed interest rate of 5.5%. Dependent undergraduates may borrow "
        "up to $5,500-$7,500 per year, depending on year in school, subject to aggregate loan "
        "limits. Rates for loans disbursed in prior years are unchanged, and the new rate is "
        "fixed for the life of each loan."),
    "furn_standingdesk": ("blog",
        "I put off buying a standing desk for years, and I wish I hadn't. The one I settled on "
        "adjusts from 24 to 50 inches, which covers both sitting and standing comfortably for "
        "most heights, and the surface is rated for 200 pounds, so two monitors and a laptop "
        "are no problem. Plan your cable management before you start raising and lowering it "
        "every day."),
    "furn_mattress": ("docs",
        "Specifications. This hybrid mattress measures 12 inches thick, with a pocketed coil "
        "support core beneath foam comfort layers. Warranty: 10 years against structural "
        "defects, including sagging beyond the specified depth. Firmness ratings are "
        "manufacturer-specific and are not standardized across brands, so compare the comfort "
        "layers directly. Normal body impressions within the specified depth are not "
        "considered defects under the warranty terms."),
}

MIN_WORDS, MAX_WORDS = 50, 110
MAX_JACCARD = 0.60
MIN_ANSWER_NUMERALS = 1


def figures(text):
    """Every digit run, unit suffix or not ("7g", "50mm", "6x8" count).

    check_variants.numerals() needs a word boundary after the number, so it
    misses figures glued to a unit. That is fine for its job (catching an
    added fact) but too loose for "the competitor adds no new figure".
    """
    return set(re.findall(r"\d+(?:\.\d+)?", text.replace(",", "")))


def jaccard(a, b):
    a, b = content_words(a), content_words(b)
    return len(a & b) / len(a | b) if a | b else 0.0


def check_competitor(pid, text, control, treatment):
    """Failure strings for one competitor; empty means it passes."""
    fails = []
    words = len(text.split())
    if not MIN_WORDS <= words <= MAX_WORDS:
        fails.append(f"length {words} words, outside {MIN_WORDS}-{MAX_WORDS}")
    t_nums, c_nums = figures(treatment), figures(control)
    extra = sorted(figures(text) - t_nums)
    if extra:
        fails.append(f"numerals not in the treatment target: {extra}")
    answering = figures(text) & (t_nums - c_nums)
    if len(answering) < MIN_ANSWER_NUMERALS:
        fails.append(f"only {len(answering)} answering numeral(s): {sorted(answering)}")
    j = jaccard(text, treatment)
    if j >= MAX_JACCARD:
        fails.append(f"content-word Jaccard with treatment {j:.2f} >= {MAX_JACCARD}")
    return fails


def build():
    docs_by_id = {d["doc_id"]: d for d in _V04["documents"]}
    assert set(COMPETITORS) == {p["prompt_id"] for p in _V04["prompts"]}, \
        "every v0.4 prompt needs exactly one competitor"

    prompts_out, docs_out, failures, stats = [], [], [], []
    comp_ids = {}
    for p in _V04["prompts"]:
        pid = p["prompt_id"]
        fmt, text = COMPETITORS[pid]
        assert fmt != p["target_format"], f"{pid}: competitor displaces the target"
        cid = f"{pid}__{fmt}"
        assert cid in p["doc_ids"], f"{pid}: no {fmt} distractor to displace"
        comp_ids[cid] = text.strip()
        tgt = docs_by_id[p["target_doc_id"]]["variants"]
        for f in check_competitor(pid, text, tgt["control"], tgt["treatment"]):
            failures.append(f"{pid}: {f}")
        stats.append((pid, len(text.split()), jaccard(text, tgt["treatment"])))
        prompts_out.append({**p, "competitor_doc_id": cid, "competitor_format": fmt})

    for d in _V04["documents"]:
        v = d["variants"]
        if d["is_target"]:
            variants = {"control": v["control"], "treatment": v["treatment"],
                        "control_comp": v["control"], "treatment_comp": v["treatment"]}
        else:
            # Paired design: within each pair of conditions every non-target is
            # byte-identical. The competitor slot differs only *between* pairs.
            alt = comp_ids.get(d["doc_id"], v["control"])
            variants = {"control": v["control"], "treatment": v["control"],
                        "control_comp": alt, "treatment_comp": alt}
        docs_out.append({**d, "variants": variants,
                         "is_competitor_slot": d["doc_id"] in comp_ids})

    if failures:
        print("competitor checks FAILED -- corpus not written:")
        for f in failures:
            print(f"  {f}")
        sys.exit(1)

    corpus = {
        "corpus_version": "competition-v1",
        "intervention": "specific figures, with and without an answering competitor",
        "base_corpus_version": "v0.4",
        "supersedes": None,
        "n_prompts": len(prompts_out),
        "n_docs": len(docs_out),
        "formats": _V04["formats"],
        "domains": _V04["domains"],
        "conditions": CONDITIONS,
        "prompts": prompts_out,
        "documents": docs_out,
    }
    payload = json.dumps(corpus, indent=2, sort_keys=True, ensure_ascii=False)
    corpus["corpus_sha256"] = hashlib.sha256(payload.encode()).hexdigest()[:16]

    out = _HERE / "corpus_competition.json"
    out.write_text(json.dumps(corpus, indent=2, ensure_ascii=False))

    from collections import Counter
    cf = Counter(p["competitor_format"] for p in prompts_out)
    pair = Counter((p["target_format"], p["competitor_format"]) for p in prompts_out)
    words = sorted(s[1] for s in stats)
    jac = sorted(s[2] for s in stats)
    print(f"wrote {out}")
    print(f"  prompts={len(prompts_out)} docs={len(docs_out)} sha={corpus['corpus_sha256']}")
    print(f"  competitor format balance: {dict(cf)}")
    print(f"  distinct (target, competitor) format pairs: {len(pair)}")
    print(f"  competitor length words: min={words[0]} median={words[len(words)//2]} max={words[-1]}")
    print(f"  Jaccard with treatment:  min={jac[0]:.2f} median={jac[len(jac)//2]:.2f} max={jac[-1]:.2f}")
    print("  all competitor checks passed: numerals within treatment, answering, not a copy")


if __name__ == "__main__":
    build()
