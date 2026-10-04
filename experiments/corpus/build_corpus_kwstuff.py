#!/usr/bin/env python3
"""
OpenGEO corpus -- keyword-stuffing intervention (kwstuff-v1), under construction.

A new, independent intervention, not a replacement for the claim-density corpus
(v0.2-v0.4). Reuses corpus/build_corpus.py's 48 prompts wholesale -- same questions,
same domains, same 5 non-target distractor documents per prompt, same target format
balance (8 prompts/format) -- and only swaps the target document's two variants.

Where v0.2-v0.4 tested "generic phrasing vs specific figures," this tests "natural
fact-dense prose vs the same facts wrapped in unnatural keyword repetition":

    control = the SAME validated claim-dense text from corpus_v0.4.json's treatment
              variant (already proven to avoid the ceiling problem -- see
              corpus/build_corpus.py's module docstring for that history). Natural
              prose, states the specific facts once.
    stuffed = the same facts, with the prompt's core topic phrase (e.g. "uptime
              monitoring") awkwardly repeated 4-8 times where natural writing
              wouldn't -- the textbook SEO keyword-stuffing pattern. Length-matched
              to control within +/-3 words, same discipline as every other corpus
              version in this project.

Hypothesis (H6, to be stated formally in the pre-registration before any real-model
collection): keyword stuffing does NOT increase citation, and plausibly decreases it,
relative to equally fact-complete natural prose. This is deliberately not a bet that
mirrors claim density's "specificity helps" finding -- METHODOLOGY.md §4 already flags
self-promotional tone as a hypothesized negative signal, and no one in the GEO
industry has tested stuffing against real 2026 models. A null or negative result here
is a genuinely novel contribution; a positive result would also be worth publishing,
since it would cut against common editorial advice to avoid stuffing.

Per this project's own working practice (CLAUDE.md: "pre-register each round... a
timestamped file in preregistrations/, committed before collection"), this corpus is
authored and audited before any real-model validation call is made -- unlike the
claim-density corpus, which was validated prompt-by-prompt as it was built. The
keyword-repetition pattern itself is what is being tested, so there is no ceiling-style
"does the content answer the question" risk to iterate against here; both variants
already state the same specific facts that corpus v0.4 proved avoid the ceiling.
"""
import json, pathlib, hashlib
import build_corpus as base

KWSTUFF = {
    "saas_uptime": {  # keyword: "uptime monitoring"
        "control": (
            "Choosing uptime monitoring for a small team comes down to a few things. "
            "Check interval matters most: 30-second checks catch outages a 5-minute "
            "interval misses roughly 40% of the time for short incidents. Alert routing "
            "should support at least 3 escalation tiers. Most teams over-buy here. "
            "Enterprise tiers start around $400/month and are built for organisations "
            "with dedicated SRE staff; a five-person team rarely needs that. Expect to "
            "pay $20-50/month for 50 monitors at 60-second intervals, and avoid "
            "per-seat pricing."
        ),
        "stuffed": (
            "When you're evaluating uptime monitoring, the best uptime monitoring tool "
            "comes down to a few things. For uptime monitoring, check interval matters "
            "most: 30-second checks catch outages a 5-minute interval misses roughly "
            "40% of the time. Top uptime monitoring solutions support at least 3 "
            "escalation tiers. Enterprise uptime monitoring tiers start around "
            "$400/month; a five-person team rarely needs that. Budget uptime monitoring "
            "runs $20-50/month for 50 monitors at 60-second intervals — avoid per-seat "
            "uptime monitoring pricing. Choose uptime monitoring wisely."
        ),
    },
    "saas_pwmgr": {  # keyword: "business password manager"
        "control": (
            "Deployment. Business plans support SCIM directory integration, so "
            "deprovisioning completes within 5 minutes of a directory change versus "
            "manual removal averaging 4 days. Shared vaults grant access at group "
            "level. Administrators can require MFA and review an activity log with "
            "90-day retention on standard plans, 365-day on enterprise. Recovery runs "
            "through an admin rather than a personal recovery key — the main "
            "behavioural difference from consumer plans."
        ),
        "stuffed": (
            "Deployment. The best business password manager supports SCIM directory "
            "integration, so a business password manager completes deprovisioning "
            "within 5 minutes versus manual removal averaging 4 days. Every top "
            "business password manager grants shared vault access at group level. "
            "Choose a business password manager requiring MFA with 90-day log retention "
            "on standard, 365-day on enterprise plans. Business password manager "
            "recovery runs through an admin, not a personal key."
        ),
    },
    "cons_shoes": {  # keyword: "running shoes"
        "control": (
            "r/running — Ran three marathons now. Honest advice: don't overthink the "
            "shoe, overthink the mileage. Nearly everyone I know who got injured added "
            "more than 10% weekly volume. Midsole foam compresses meaningfully by "
            "around 300-500 miles, so replace around then rather than waiting for "
            "visible wear. Rotating two pairs extended my shoe life by roughly 20%. "
            "Racing shoes feel amazing but I got about 150 miles out of mine before "
            "they went flat."
        ),
        "stuffed": (
            "r/running — Ran three marathons in these running shoes. Honest advice on "
            "running shoes: don't overthink the running shoes, overthink the mileage. "
            "Injuries came from weekly volume, not from the running shoes themselves. "
            "Running shoes lose meaningful cushioning by 300-500 miles — replace your "
            "running shoes then. Rotating two pairs of running shoes extended shoe life "
            "by 20%. Racing running shoes feel amazing but only lasted 150 miles for "
            "me."
        ),
    },
    "cons_espresso": {  # keyword: "espresso machine"
        "control": (
            "Crema One — a semi-automatic espresso machine for the home. Stainless "
            "steel construction, 58mm portafilter, and a steam wand rated for 4oz milk "
            "texturing in about 25 seconds. Heats to brew temperature in 6 minutes and "
            "holds 9 bars at the group. Includes a starter kit and guide, plus a "
            "two-year warranty."
        ),
        "stuffed": (
            "Crema One — the semi-automatic espresso machine every espresso machine "
            "buyer should consider. This espresso machine features stainless steel "
            "construction, a 58mm portafilter, and a steam wand texturing 4oz of milk. "
            "This espresso machine heats to brew temperature in 6 minutes and holds 9 "
            "bars. Includes a starter kit and guide."
        ),
    },
    "health_creatine": {  # keyword: "creatine dosing"
        "control": (
            "Creatine is a nitrogenous organic acid found in muscle tissue, where it "
            "participates in ATP regeneration. Supplementation raises intramuscular "
            "phosphocreatine stores by approximately 20%, associated with performance "
            "improvements of roughly 5-15% in short-duration, high-intensity activity. "
            "Standard maintenance dosing is 3-5g daily; an optional 20g/day loading "
            "phase over 5-7 days reaches saturation faster. Monohydrate is the most "
            "studied form, with over 500 published trials, and is well tolerated in "
            "healthy adults."
        ),
        "stuffed": (
            "Creatine dosing starts with understanding creatine as a nitrogenous "
            "organic acid in muscle tissue. Proper creatine dosing raises "
            "phosphocreatine stores by 20%, improving performance 5-15%. Standard "
            "creatine dosing is 3-5g daily; optional creatine dosing during a 20g/day "
            "loading phase over 5-7 days reaches saturation faster. Monohydrate "
            "creatine dosing is the most studied, well tolerated in healthy adults. "
            "Confirm your creatine dosing plan with a doctor before starting any new "
            "supplementation routine."
        ),
    },
    "health_sleep": {  # keyword: "sleep trackers"
        "control": (
            "Researchers published a comparison of consumer sleep trackers against "
            "polysomnography this month. Devices estimated total sleep time within "
            "about 20 minutes of the laboratory standard, but sleep-stage "
            "classification agreement fell to roughly 50-65% depending on stage, with "
            "deep sleep the least reliable. Devices overestimated total sleep time by "
            "15-20 minutes on average. The authors cautioned against treating stage "
            "data as clinically meaningful; manufacturers have acknowledged the limits "
            "of wrist-based measurement."
        ),
        "stuffed": (
            "Researchers published a sleep tracker comparison against polysomnography "
            "this month, testing popular sleep trackers directly. These sleep trackers "
            "estimated total sleep time within 20 minutes of lab standards, but sleep "
            "tracker stage-classification agreement fell to 50-65%, with deep sleep "
            "weakest. Sleep trackers overestimated total sleep time by 15-20 minutes. "
            "The authors cautioned against treating sleep tracker stage data as "
            "clinically meaningful; sleep tracker makers acknowledged wrist-based "
            "limits."
        ),
    },
    "fin_savings": {  # keyword: "high-yield savings account"
        "control": (
            "Choosing a high-yield savings account is mostly about looking past the "
            "headline rate. Promotional rates typically expire after 3-6 months, often "
            "dropping 1-2 percentage points to the ongoing rate. Check for minimum "
            "balances, whether the rate tiers above a threshold, and transfer "
            "settlement time, which ranges from same-day to 5 business days. In the US, "
            "confirm FDIC insurance, which covers $250,000 per depositor."
        ),
        "stuffed": (
            "Choosing the best high-yield savings account is about looking past the "
            "headline rate. High-yield savings account promo rates expire after 3-6 "
            "months, dropping 1-2 points. A good high-yield savings account has no "
            "minimum balance, and high-yield savings account transfers settle same-day "
            "to 5 days. Confirm your high-yield savings account carries FDIC insurance "
            "covering $250,000 per depositor — essential for any high-yield savings "
            "account."
        ),
    },
    "fin_index": {  # keyword: "index fund"
        "control": (
            "BroadMarket Total Index Fund — diversified exposure to roughly 3,700 "
            "holdings in a single fund. Expense ratio of 0.03%, versus a 0.42% average "
            "for comparable active funds. No minimum on automatic investment plans; "
            "$3,000 minimum for lump-sum purchases. Dividends reinvest automatically."
        ),
        "stuffed": (
            "BroadMarket Total Index Fund — the index fund with exposure to 3,700 "
            "holdings. This index fund charges a 0.03% expense ratio versus 0.42% for "
            "active funds. No minimum on automatic index fund plans; $3,000 minimum for "
            "lump-sum purchases. This index fund reinvests dividends automatically."
        ),
    },
    "local_hvac": {  # keyword: "HVAC system"
        "control": (
            "Service life and replacement guidance. Residential systems typically last "
            "15-20 years with regular maintenance, with efficiency declining measurably "
            "after year 12. Consider replacement when a single repair exceeds 30% of "
            "new-equipment cost, when the unit is over 15 years old and the repair "
            "exceeds $500, or when it uses R-22 refrigerant, phased out in 2020 and now "
            "costing several times its former price. Annual servicing extends operating "
            "life by 3-5 years."
        ),
        "stuffed": (
            "HVAC system service life guidance. A residential HVAC system typically "
            "lasts 15-20 years, with HVAC system efficiency declining after year 12. "
            "Replace your HVAC system when a repair exceeds 30% of new-HVAC-system "
            "cost, when the HVAC system is over 15 and repair exceeds $500, or when "
            "your HVAC system uses R-22, phased out in 2020. Annual HVAC system "
            "servicing extends life by 3-5 years. Getting HVAC system maintenance right "
            "saves money long term."
        ),
    },
    "local_movers": {  # keyword: "moving company"
        "control": (
            "Consumer protection officials issued renewed warnings about moving fraud "
            "ahead of peak season. Complaints follow a consistent pattern: an estimate "
            "30-50% below competing quotes, no in-person survey, and a demand for extra "
            "payment before belongings are released. Complaints roughly double between "
            "May and September; officials urged verifying a company's USDOT number and "
            "treating deposits above 20% of the quoted total as a warning sign."
        ),
        "stuffed": (
            "Consumer officials warned about moving company fraud ahead of peak season. "
            "Moving company complaints follow a pattern: a moving company quote 30-50% "
            "below competitors, no survey, and extra payment demands. Moving company "
            "complaints double May-September; officials urged verifying a moving "
            "company's USDOT number and treating deposits above 20% as a moving company "
            "warning sign. Always vet your moving company thoroughly before signing any "
            "moving company contract."
        ),
    },
    "travel_points": {  # keyword: "airline credit card"
        "control": (
            "r/awardtravel — Honest take for casual travellers: probably not worth it. "
            "I ran the numbers after two years. Sign-up bonus was worth about $600 in "
            "redemptions. Ongoing earn averaged 1.4 cents per dollar against a $95 "
            "annual fee, netting around $160 a year on my roughly $18,000 of annual "
            "spend. If you fly 20+ segments a year it's different, but most of the "
            "value is the one-time sign-up bonus."
        ),
        "stuffed": (
            "r/awardtravel — Honest take on airline credit cards: probably not worth "
            "it. My airline credit card numbers after two years: sign-up bonus worth "
            "$600. This airline credit card earned 1.4 cents per dollar against a $95 "
            "fee, netting $160 a year on $18,000 spend. If you fly 20+ segments, a "
            "different airline credit card math applies, but most airline credit card "
            "value is the sign-up bonus."
        ),
    },
    "travel_visa": {  # keyword: "travel insurance"
        "control": (
            "Travel insurance is a class of insurance covering financial losses "
            "associated with travelling. Coverage commonly includes emergency medical "
            "expenses, medical evacuation, trip cancellation, and baggage loss — "
            "evacuation alone can exceed $100,000 from remote regions. Policies exclude "
            "pre-existing conditions unless declared, typically a 60-180 day look-back. "
            "'Cancel for any reason' riders add roughly 40-50% to the premium."
        ),
        "stuffed": (
            "Travel insurance covers financial losses from travelling. The best travel "
            "insurance includes emergency medical, evacuation, cancellation, and "
            "baggage coverage — travel insurance evacuation alone can exceed $100,000. "
            "Travel insurance excludes pre-existing conditions unless declared, a "
            "60-180 day look-back. 'Cancel for any reason' travel insurance riders add "
            "40-50% to your premium. Compare providers carefully before buying any "
            "travel insurance policy."
        ),
    },
    "edu_bootcamp": {  # keyword: "coding bootcamp"
        "control": (
            "Choosing a coding bootcamp is mostly about being honest with yourself "
            "about time. Full-time programs expect roughly 60-70 hours a week between "
            "class and homework. Ask for the school's job placement rate directly — "
            "reputable ones report around 70-80% employed in a related role within 6 "
            "months, tracked and published under CIRR standards. Part-time programs run "
            "15-20 hours a week but take twice as long to finish."
        ),
        "stuffed": (
            "Choosing a coding bootcamp means being honest about time. A full-time "
            "coding bootcamp expects 60-70 hours weekly. Ask any coding bootcamp for "
            "its job placement rate — a reputable coding bootcamp reports 70-80% "
            "employed within 6 months under CIRR standards. A part-time coding bootcamp "
            "runs 15-20 hours weekly but takes twice as long as a full-time coding "
            "bootcamp. Research each coding bootcamp carefully before enrolling in a "
            "coding bootcamp program."
        ),
    },
    "edu_certification": {  # keyword: "PMP certification"
        "control": (
            "Exam structure. The exam consists of 180 questions administered over 230 "
            "minutes, with a scheduled break at the halfway point. Passing requires "
            "scoring in the 'above target' or 'target' band, which corresponds to "
            "roughly 61% of scored items correct — the exact cut score is set "
            "psychometrically per exam form and not published as a fixed number. "
            "Candidates must submit 35 hours of project management education before "
            "scheduling."
        ),
        "stuffed": (
            "PMP certification exam structure. The PMP certification exam has 180 "
            "questions over 230 minutes. Passing the PMP certification requires the "
            "'above target' band, roughly 61% correct — PMP certification cut scores "
            "aren't published as a fixed number. PMP certification candidates must "
            "submit 35 hours of education before scheduling the PMP certification exam. "
            "Study consistently for weeks before your PMP certification exam date to "
            "pass the PMP certification on the first attempt."
        ),
    },
    "diy_drill": {  # keyword: "cordless drill"
        "control": (
            "r/tools — Upgraded from a corded drill last year and don't regret it at "
            "all. The 4.0Ah battery runs me a full weekend of deck-board drilling on "
            "one charge, and the rapid charger tops it back up in about 45 minutes if I "
            "do run it down. Buy into a battery platform, not just a drill — once you "
            "have a couple 4.0Ah packs you'll end up buying every other tool in the "
            "same line."
        ),
        "stuffed": (
            "r/tools — Upgraded to a cordless drill last year, best cordless drill "
            "decision ever. My cordless drill's 4.0Ah battery runs a full weekend on "
            "one charge, and the cordless drill's rapid charger tops up in 45 minutes. "
            "Buy into a cordless drill battery platform — once you have 4.0Ah packs for "
            "your cordless drill you'll buy every tool in that cordless drill line. A "
            "quality battery and charger combo makes the real difference."
        ),
    },
    "diy_kit": {  # keyword: "laminate flooring"
        "control": (
            "HearthLine Laminate Flooring — oak-look finish with a textured, "
            "scratch-resistant surface. Each box covers 22.5 square feet across 8 "
            "planks. Acclimate unopened boxes in the install room for 48 hours before "
            "opening, longer in humid climates. Click-lock edges for a glueless "
            "install; underlayment sold separately."
        ),
        "stuffed": (
            "HearthLine — the laminate flooring with an oak-look, scratch-resistant "
            "surface. Each laminate flooring box covers 22.5 square feet across 8 "
            "laminate flooring planks. Acclimate this laminate flooring for 48 hours "
            "before opening. Click-lock laminate flooring edges enable a glueless "
            "install; underlayment sold separately."
        ),
    },
    "pets_insurance": {  # keyword: "dog insurance"
        "control": (
            "Pet insurance is a category of indemnity insurance covering veterinary "
            "costs resulting from illness or injury. Monthly premiums for dogs "
            "typically run $25-70 depending on breed, age and coverage level, with "
            "annual deductibles commonly offered at $100, $250 or $500. Most policies "
            "exclude pre-existing conditions and impose waiting periods for specific "
            "conditions such as cruciate ligament injuries."
        ),
        "stuffed": (
            "Dog insurance is indemnity insurance covering veterinary costs from "
            "illness or injury. Dog insurance premiums run $25-70 depending on breed; "
            "dog insurance deductibles are commonly $100, $250, or $500. Most dog "
            "insurance policies exclude pre-existing conditions and impose waiting "
            "periods — read your dog insurance policy for cruciate ligament exclusions "
            "before buying dog insurance."
        ),
    },
    "pets_vaccine": {  # keyword: "puppy vaccine"
        "control": (
            "A veterinary association updated its companion animal vaccination "
            "guidelines this year. Puppies typically receive a series of 3-4 core "
            "vaccine doses between 6 and 16 weeks of age, with the final rabies booster "
            "commonly given around 12-16 weeks and then again at one year. The revision "
            "emphasizes risk-based scheduling over a one-size-fits-all approach for "
            "adult dogs, but core puppy recommendations are unchanged."
        ),
        "stuffed": (
            "A vet association updated puppy vaccine guidelines this year. Puppy "
            "vaccines typically total 3-4 core doses between 6 and 16 weeks, with the "
            "rabies puppy vaccine given at 12-16 weeks and again at one year. The "
            "revision covers adult dogs; core puppy vaccine recommendations are "
            "unchanged, so puppy vaccine schedules stay consistent for new owners. Ask "
            "your vet about exact timing."
        ),
    },
    "auto_evcharger": {  # keyword: "EV charger"
        "control": (
            "Installing home EV charging is one of those projects people either "
            "overthink or underthink, rarely land in the middle. A Level 2 charger "
            "typically adds 20-30 miles of range per hour and needs a dedicated 40-50 "
            "amp circuit, usually a 240V line similar to an electric dryer's. Get an "
            "electrician to check panel capacity before ordering — an older home's "
            "panel is what derails installs, not the charger."
        ),
        "stuffed": (
            "Installing an EV charger at home means picking the right EV charger. A "
            "Level 2 EV charger adds 20-30 miles per hour and needs a dedicated 40-50 "
            "amp circuit for your EV charger, similar to a dryer's 240V line. Get an "
            "electrician to check panel capacity before your EV charger install — panel "
            "capacity, not the EV charger, derails most installs. Compare brands and "
            "pricing first."
        ),
    },
    "auto_dashcam": {  # keyword: "dashcam"
        "control": (
            "RoadWitness 4K Dashcam — front and rear camera kit with wide-angle lens "
            "and night vision enhancement. The included 128GB card holds about 14 hours "
            "of loop footage, and parking-mode motion detection auto-records for 30 "
            "seconds when it senses movement near a parked car. GPS logging embeds "
            "speed and location in footage."
        ),
        "stuffed": (
            "RoadWitness 4K Dashcam — the dashcam with front and rear cameras and night "
            "vision. This dashcam's 128GB card holds 14 hours of loop footage, and this "
            "dashcam's parking-mode auto-records 30 seconds on motion. Every dashcam "
            "buyer wants GPS logging — this dashcam embeds speed and location, making "
            "it the dashcam to beat."
        ),
    },
    "legal_smallclaims": {  # keyword: "small claims court"
        "control": (
            "Filing procedure. Complete the claim form identifying the defendant's full "
            "legal name and a valid address for service. Small claims limits commonly "
            "range from $5,000 to $10,000 depending on jurisdiction, and filing fees "
            "typically run $30-100 based on the amount claimed. A hearing date is "
            "usually scheduled within 4-8 weeks of filing."
        ),
        "stuffed": (
            "Small claims court filing procedure. Complete the small claims court form "
            "with the defendant's name and address. Small claims court limits range "
            "$5,000-$10,000; small claims court filing fees run $30-100. Your small "
            "claims court hearing is scheduled within 4-8 weeks — small claims court "
            "moves faster than regular civil court for most disputes."
        ),
    },
    "legal_llc": {  # keyword: "LLC"
        "control": (
            "A state's business filing office reported a surge in new business entity "
            "registrations this year. Standard LLC filing fees in most states run "
            "$50-500 depending on jurisdiction, with standard processing taking 1-3 "
            "weeks; expedited processing for an added fee can reduce that to 24-48 "
            "hours in many states. Officials said the office has added staff to address "
            "seasonal backlogs."
        ),
        "stuffed": (
            "A state filing office reported a surge in LLC registrations this year. LLC "
            "filing fees run $50-500; standard LLC processing takes 1-3 weeks, and "
            "expedited LLC processing costs extra for 24-48 hour turnaround. Officials "
            "added staff to address LLC filing backlogs, since forming an LLC remains "
            "popular. Filing an LLC correctly the first time avoids costly delays."
        ),
    },
    "career_negotiate": {  # keyword: "salary negotiation"
        "control": (
            "r/careerguidance — Negotiated my last offer and it went better than I "
            "expected. Asked for 12% over the initial number, backed by market data, "
            "and landed at about 8% after back-and-forth — which matches what I've seen "
            "cited as a realistic 5-15% range for most roles. Most companies give you "
            "3-5 business days to respond to a written offer, though you can usually "
            "ask for a short extension if you need it."
        ),
        "stuffed": (
            "r/careerguidance — Salary negotiation went better than expected. My salary "
            "negotiation asked for 12% over the initial number, landing at 8% — "
            "matching the typical salary negotiation range of 5-15%. Salary negotiation "
            "timelines give you 3-5 business days to respond, though salary negotiation "
            "extensions are usually possible if you ask for more salary negotiation "
            "time. Always negotiate calmly and back every ask with solid, specific "
            "market data and evidence."
        ),
    },
    "career_resume": {  # keyword: "resume"
        "control": (
            "A resume is a document summarizing a candidate's professional experience, "
            "education, and qualifications, formatted for review by hiring managers or "
            "applicant tracking systems. Convention holds that a resume should run one "
            "page for early-career candidates and up to two pages for those with 10+ "
            "years of experience, with detailed work history typically limited to the "
            "most recent 10-15 years."
        ),
        "stuffed": (
            "A resume summarizes professional experience for hiring managers and "
            "applicant tracking systems. Your resume should run one page early-career, "
            "up to two resume pages with 10+ years experience. A good resume limits "
            "detailed work history to the most recent 10-15 years — resume length "
            "matters as much as resume content. A tailored resume always beats a "
            "generic one."
        ),
    },
    "nutr_protein": {  # keyword: "protein intake"
        "control": (
            "Protein intake advice online ranges from reasonable to absurd, often "
            "depending on who's selling supplements. Research generally supports around "
            "0.7-1g per pound of body weight daily for people strength training "
            "regularly. Total daily intake matters more than precise timing — the old "
            "'anabolic window' right after lifting is much wider than once believed, "
            "more like several hours than 30 minutes."
        ),
        "stuffed": (
            "Protein intake advice ranges from reasonable to absurd online. Research "
            "supports 0.7-1g of protein intake per pound of body weight daily for "
            "strength training. Total daily protein intake matters more than timing — "
            "the 'anabolic window' for protein intake is wider than believed, hours not "
            "30 minutes. Track your protein intake consistently for the most reliable "
            "results over time."
        ),
    },
    "nutr_meal": {  # keyword: "meal replacement shake"
        "control": (
            "Preparation instructions. Shake or blend with 8-12oz of cold water, milk, "
            "or a non-dairy alternative. One serving provides 400 calories and 7g of "
            "dietary fiber. Best consumed within 30 minutes of mixing. Not intended as "
            "a sole source of nutrition for extended periods without guidance from a "
            "healthcare provider."
        ),
        "stuffed": (
            "Meal replacement shake preparation. Shake this meal replacement shake with "
            "8-12oz of water or milk. One meal replacement shake serving provides 400 "
            "calories, 7g fiber. Consume your meal replacement shake within 30 minutes. "
            "Not a sole nutrition source — talk to a provider before relying on a meal "
            "replacement shake long-term."
        ),
    },
    "re_inspection": {  # keyword: "home inspection"
        "control": (
            "r/RealEstate — Went through this last month buying our first place. Cost "
            "us $450 for a roughly 2,200 sq ft house, and the inspector was on site for "
            "about 3 hours walking the whole property methodically. Worth every penny "
            "for the peace of mind. Ask if radon and sewer scope are included or "
            "separate before booking, those added another $200 for us."
        ),
        "stuffed": (
            "r/RealEstate — Our home inspection last month cost $450 for a 2,200 sq ft "
            "house. The home inspection took 3 hours, methodically covering the "
            "property. Worth every penny for a home inspection. Ask if radon and sewer "
            "scope are part of your home inspection or separate — add-ons cost another "
            "$200 for a full home inspection. Always attend in person if you can."
        ),
    },
    "re_warranty": {  # keyword: "home warranty"
        "control": (
            "HomeShield Complete — covers major home systems and appliances against "
            "mechanical failure from normal wear and tear. Annual plans run $500-700 "
            "depending on coverage tier, with a $75-125 service call fee due at each "
            "claim visit. 24/7 claims line, coverage begins 30 days after enrollment."
        ),
        "stuffed": (
            "HomeShield — the home warranty covering major systems and appliances. This "
            "home warranty runs $500-700 annually, with a $75-125 home warranty service "
            "call fee per visit. Every home warranty claim goes through a 24/7 line, "
            "and home warranty coverage begins 30 days after enrolling in this home "
            "warranty."
        ),
    },
    "parent_carseat": {  # keyword: "convertible car seat"
        "control": (
            "Convertible car seats are designed to transition between rear-facing and "
            "forward-facing orientations as a child grows. Most convertible seats allow "
            "rear-facing use up to 40-50 pounds or a specified height limit printed on "
            "the seat, and safety organizations generally recommend keeping children "
            "rear-facing until at least age 2, and longer where the seat's limits "
            "allow."
        ),
        "stuffed": (
            "A convertible car seat transitions between rear- and forward-facing as a "
            "child grows. Most convertible car seat models allow rear-facing to 40-50 "
            "pounds or a printed height limit. Every convertible car seat should stay "
            "rear-facing until age 2, longer if your convertible car seat's limits "
            "allow — check your convertible car seat manual."
        ),
    },
    "parent_recall": {  # keyword: "stroller recall"
        "control": (
            "A major stroller manufacturer issued a voluntary recall affecting "
            "approximately 230,000 units this month after 12 reports of the hinge "
            "mechanism unexpectedly folding during use, causing minor injuries in at "
            "least 4 cases. The company is offering a free repair kit and said it is "
            "working with regulators to notify affected customers directly."
        ),
        "stuffed": (
            "A stroller recall this month affects approximately 230,000 units after 12 "
            "hinge-folding reports causing minor injuries in 4 cases. This stroller "
            "recall includes a free repair kit, and the stroller recall notice is going "
            "to affected customers directly as regulators coordinate on the stroller "
            "recall rollout. Check your model against this list."
        ),
    },
    "game_pc_upgrade": {  # keyword: "gaming PC upgrade"
        "control": (
            "Upgrading a gaming PC piece by piece is usually smarter than a full "
            "rebuild unless the whole system is genuinely old. A GPU-only upgrade "
            "commonly delivers 40-70% higher frame rates if the rest of the system "
            "isn't the bottleneck, versus 80-120% for a full rebuild with a new CPU and "
            "motherboard too. Size the power supply at least 150W above the new GPU's "
            "rated draw for headroom."
        ),
        "stuffed": (
            "A gaming PC upgrade piece by piece beats a full gaming PC rebuild unless "
            "the system is old. A GPU-only gaming PC upgrade delivers 40-70% higher "
            "frame rates, versus 80-120% for a full gaming PC upgrade with new CPU too. "
            "Size your gaming PC upgrade's power supply 150W above the GPU's draw for "
            "headroom. Check part compatibility carefully before starting any upgrade "
            "project to avoid wasting money."
        ),
    },
    "game_headset": {  # keyword: "wireless gaming headset"
        "control": (
            "SonicWave Wireless Gaming Headset — 50mm drivers with a detachable "
            "noise-cancelling microphone. Rated for 30 hours of battery life per charge "
            "and a 40-foot wireless range via the included USB dongle. Compatible with "
            "PC, console, and mobile. Memory foam ear cushions."
        ),
        "stuffed": (
            "SonicWave — the wireless gaming headset with 50mm drivers and a "
            "noise-cancelling mic. This wireless gaming headset is rated for 30 hours "
            "battery and 40-foot range. This wireless gaming headset works on PC, "
            "console, and mobile. Memory foam ear cushions add comfort."
        ),
    },
    "tax_freelance": {  # keyword: "self-employment tax"
        "control": (
            "Estimated tax overview. Self-employed individuals generally must make "
            "quarterly estimated payments if they expect to owe a minimum threshold "
            "amount in tax for the year. A common rule of thumb is setting aside 25-30% "
            "of net income for self-employment and income tax combined. Quarterly "
            "payments are typically due in mid-April, June, September, and January of "
            "the following year."
        ),
        "stuffed": (
            "Self-employment tax overview. Self-employed filers must make quarterly "
            "self-employment tax payments if they expect to owe above a threshold. Set "
            "aside 25-30% of net income for self-employment tax and income tax "
            "combined. Self-employment tax payments are due mid-April, June, September, "
            "and January — mark your self-employment tax calendar. Setting aside "
            "self-employment tax money monthly avoids a painful self-employment tax "
            "bill."
        ),
    },
    "tax_deadline": {  # keyword: "tax filing deadline"
        "control": (
            "The national tax authority reminded filers of upcoming deadlines this "
            "week. Filing late without an extension carries a failure-to-file penalty "
            "of 5% of unpaid tax per month, up to 25%, notably steeper than the "
            "failure-to-pay penalty of 0.5% per month for those who filed an extension "
            "but still owe money. The agency encouraged taxpayers to request an "
            "extension electronically rather than miss the deadline outright."
        ),
        "stuffed": (
            "The tax authority reminded filers about the tax filing deadline this week. "
            "Missing the tax filing deadline without an extension carries a 5% monthly "
            "penalty, up to 25% — steeper than the 0.5% penalty for those who met the "
            "tax filing deadline via extension. Request an extension electronically "
            "rather than missing the tax filing deadline outright this year. Mark your "
            "calendar early each year."
        ),
    },
    "fit_homegym": {  # keyword: "home gym"
        "control": (
            "r/homegym — Built mine out slowly over about a year instead of all at "
            "once. Adjustable dumbbells plus a decent adjustable bench ran me around "
            "$600 total, and the whole setup fits in roughly a 6x8 foot area including "
            "room to actually move. Flooring matters more than people expect too, "
            "protects both the floor and the equipment."
        ),
        "stuffed": (
            "r/homegym — Built my home gym slowly over a year. My home gym's adjustable "
            "dumbbells and bench ran $600 total, and my home gym fits in a 6x8 foot "
            "area with room to move. Home gym flooring matters more than expected, "
            "protecting both floor and home gym equipment from damage. Plan your layout "
            "before you buy."
        ),
    },
    "fit_hrzones": {  # keyword: "heart rate"
        "control": (
            "Heart rate training zones divide exercise intensity into ranges based on "
            "percentage of maximum heart rate. Zone 2 is generally defined as 60-70% of "
            "maximum heart rate, and endurance-focused training guidance commonly "
            "recommends accumulating 150-180 minutes per week at that intensity to "
            "build aerobic base. Maximum heart rate is commonly estimated using an "
            "age-based formula, though individual variation can be substantial."
        ),
        "stuffed": (
            "Heart rate zones divide intensity by percentage of maximum heart rate. "
            "Zone 2 heart rate is 60-70% of maximum heart rate, and training guidance "
            "recommends 150-180 minutes weekly in this heart rate zone for aerobic "
            "base. Maximum heart rate is estimated by an age formula, though heart rate "
            "variation can be substantial. Track it consistently to stay in zone."
        ),
    },
    "photo_lens": {  # keyword: "50mm prime lens"
        "control": (
            "A 50mm prime is the classic first lens recommendation for a reason — it "
            "forces you to move your feet instead of zooming. Most affordable versions "
            "offer an aperture range of f/1.8 to f/16 and a minimum focus distance "
            "around 1.5 feet, close enough for reasonably tight portraits but not true "
            "macro work. Not ideal for tight indoor spaces where you can't physically "
            "back up enough."
        ),
        "stuffed": (
            "The 50mm prime lens is the classic first lens recommendation — this 50mm "
            "prime lens forces you to move your feet. Most 50mm prime lens options "
            "offer f/1.8 to f/16 aperture and 1.5-foot minimum focus, good for "
            "portraits but not macro. This 50mm prime lens isn't ideal for tight indoor "
            "spaces. Many photographers keep a 50mm prime lens as their go-to "
            "walk-around choice."
        ),
    },
    "photo_raw": {  # keyword: "RAW photo files"
        "control": (
            "File format overview. RAW files retain unprocessed sensor data and "
            "typically run 20-40MB per image, roughly 5-10 times larger than a "
            "same-resolution JPEG. Shooting RAW generally preserves 1-2 additional "
            "stops of recoverable dynamic range in highlights and shadows compared to "
            "an in-camera JPEG. JPEG files apply in-camera processing and compression, "
            "producing a smaller, ready-to-share file."
        ),
        "stuffed": (
            "RAW photo files overview. RAW photo files retain unprocessed sensor data "
            "and run 20-40MB, 5-10 times larger than JPEG. RAW photo files preserve 1-2 "
            "additional stops of dynamic range versus JPEG. JPEG applies in-camera "
            "processing, producing a smaller file. Most working professionals shoot RAW "
            "photo files by default for maximum flexibility. Editing latitude matters "
            "most."
        ),
    },
    "garden_raisedbed": {  # keyword: "raised garden bed"
        "control": (
            "r/gardening — Built our first raised bed this spring and it's been one of "
            "the better projects we've done around the yard. Took about 20 bags of "
            "raised bed mix to fill our 4x8 bed at a 12-inch depth, which is plenty for "
            "most root vegetables and everything else we planted. Sun exposure planning "
            "before you build matters more than the bed itself honestly."
        ),
        "stuffed": (
            "r/gardening — Built our first raised garden bed this spring, best yard "
            "project yet. Our raised garden bed took 20 bags of mix to fill at 12-inch "
            "depth — plenty for a raised garden bed growing root vegetables. Sun "
            "exposure planning before building your raised garden bed matters more than "
            "the raised garden bed itself. Plan your raised garden bed layout before "
            "buying raised garden bed materials."
        ),
    },
    "garden_composter": {  # keyword: "compost tumbler"
        "control": (
            "DualBin Compost Tumbler — twin-chamber rotating design, each chamber holds "
            "27 gallons, allowing continuous composting while one side finishes. Under "
            "ideal conditions, finished compost is ready in as little as 4-6 weeks per "
            "batch. Elevated stand keeps pests out and eases turning."
        ),
        "stuffed": (
            "DualBin — the compost tumbler with twin 27-gallon chambers for continuous "
            "composting. This compost tumbler produces finished compost in 4-6 weeks. "
            "This compost tumbler's elevated stand keeps pests out and eases turning. "
            "This tumbler suits any backyard composting setup well."
        ),
    },
    "sec_vpn": {  # keyword: "consumer VPN"
        "control": (
            "A consumer virtual private network (VPN) routes internet traffic through "
            "an encrypted tunnel to a server operated by the VPN provider. Most "
            "consumer plans include 5-10 simultaneous device connections per "
            "subscription, and typical speed reduction ranges from 10-25% versus an "
            "unprotected connection, depending on server load and distance. Provider "
            "logging policies and jurisdiction also affect practical privacy "
            "guarantees."
        ),
        "stuffed": (
            "A consumer VPN routes traffic through an encrypted tunnel to a VPN "
            "provider's server. Most consumer VPN plans include 5-10 device "
            "connections, and consumer VPN speed reduction ranges 10-25% depending on "
            "load. Consumer VPN logging policies and jurisdiction affect privacy "
            "guarantees. Choose your consumer VPN provider carefully based on these "
            "factors. Read independent reviews first."
        ),
    },
    "sec_breach": {  # keyword: "data breach"
        "control": (
            "A widely used online retailer disclosed a data security incident affecting "
            "approximately 2.3 million customer accounts this week, saying names, email "
            "addresses, and hashed passwords were exposed, though payment card data was "
            "stored separately and not affected. The company has engaged a third-party "
            "forensics firm and is offering affected customers a complimentary "
            "monitoring service."
        ),
        "stuffed": (
            "A retailer disclosed a data breach affecting 2.3 million accounts this "
            "week. This data breach exposed names, emails, and hashed passwords, though "
            "payment data was unaffected by the data breach. The company engaged "
            "forensics after the data breach and is offering data breach monitoring to "
            "customers affected by the data breach."
        ),
    },
    "cook_airfryer": {  # keyword: "air fryer"
        "control": (
            "Air fryers earned the hype for a reason, but the size decision trips "
            "people up more than any other spec. This one holds 6 quarts and draws 1700 "
            "watts, enough capacity for a family meal and enough power to crisp food "
            "quickly rather than just drying it out. Basket-style and oven-style "
            "designs cook noticeably differently despite similar marketing."
        ),
        "stuffed": (
            "Air fryers earned the hype, but size trips up air fryer buyers most. This "
            "air fryer holds 6 quarts and draws 1700 watts — enough air fryer capacity "
            "for a family, enough air fryer power to crisp food fast. Basket-style and "
            "oven-style air fryer designs cook differently despite similar marketing. "
            "Clean the basket often for best results."
        ),
    },
    "cook_knife": {  # keyword: "chef's knife"
        "control": (
            "Hearthstone Chef's Knife — full-tang forged construction with an 8-inch "
            "high-carbon stainless steel blade, hand-sharpened to a 15-degree edge per "
            "side. Balanced handle for extended use. Includes a protective blade guard. "
            "Dishwasher use not recommended."
        ),
        "stuffed": (
            "Hearthstone — the chef's knife with full-tang construction and an 8-inch "
            "high-carbon steel blade. This chef's knife is hand-sharpened to 15 degrees "
            "per side and has a balanced handle. Includes a protective blade guard for "
            "storage."
        ),
    },
    "loan_forgiveness": {  # keyword: "income-driven repayment"
        "control": (
            "Income-driven repayment overview. Most income-driven plans forgive the "
            "remaining balance after 20-25 years of qualifying payments, depending on "
            "the specific plan and loan type. Under current federal law, forgiven "
            "balances are not taxed as income through 2025, though this treatment has "
            "changed by legislation before and borrowers should confirm current rules. "
            "Monthly payments are recalculated annually."
        ),
        "stuffed": (
            "Income-driven repayment overview. Income-driven repayment forgives the "
            "balance after 20-25 years of qualifying payments. Under current law, "
            "income-driven repayment forgiveness isn't taxed through 2025, though "
            "income-driven repayment tax rules have changed before — confirm current "
            "rules. Income-driven repayment payments recalculate annually based on "
            "income. Track your income-driven repayment progress yearly toward "
            "income-driven repayment eligibility."
        ),
    },
    "loan_rate": {  # keyword: "student loan interest rate"
        "control": (
            "The federal government announced updated student loan interest rates for "
            "the upcoming academic year: 5.5% fixed for new undergraduate loans, "
            "applying to loans first disbursed after July 1. Dependent undergraduates "
            "can typically borrow up to $5,500-$7,500 per year depending on class "
            "standing, subject to overall aggregate loan limits. The rate does not "
            "affect loans already disbursed under previous years' terms."
        ),
        "stuffed": (
            "The federal student loan interest rate for the upcoming year is 5.5% fixed "
            "for new undergraduate loans. This student loan interest rate applies to "
            "loans disbursed after July 1. Dependent undergraduates can borrow "
            "$5,500-$7,500 yearly under this student loan interest rate, which doesn't "
            "affect prior years' student loan interest rate terms. Compare this student "
            "loan interest rate against private loan options too."
        ),
    },
    "furn_standingdesk": {  # keyword: "standing desk"
        "control": (
            "r/BuyItForLife — Got one after years of a fixed-height desk and the "
            "difference for my back has been real. Mine adjusts from 24 to 50 inches, "
            "which covers sitting and standing for my height fine, and it's rated for "
            "200 pounds so my dual monitor setup sits on it with room to spare. Cable "
            "management gets messier than expected once you're actually raising and "
            "lowering it daily."
        ),
        "stuffed": (
            "r/BuyItForLife — My standing desk replaced a fixed-height desk and my back "
            "thanks this standing desk. My standing desk adjusts 24 to 50 inches, and "
            "this standing desk is rated for 200 pounds so my monitors fit easily. "
            "Standing desk cable management gets messier than expected daily. A sturdy "
            "frame matters as much as motor speed. Cable management and motor noise "
            "both matter as much as the frame quality here."
        ),
    },
    "furn_mattress": {  # keyword: "mattress"
        "control": (
            "Mattress construction generally falls into several categories — "
            "innerspring, memory foam, latex, and hybrid designs. This hybrid model "
            "measures 12 inches thick, combining coil support with foam comfort layers, "
            "and carries a 10-year warranty against structural defects such as sagging "
            "beyond a specified depth. Firmness is typically rated on a numeric scale "
            "that is not standardized across manufacturers."
        ),
        "stuffed": (
            "Mattress construction falls into categories — innerspring, memory foam, "
            "latex, and hybrid mattress designs. This hybrid mattress measures 12 "
            "inches, combining coil support with foam mattress comfort layers, carrying "
            "a 10-year mattress warranty against sagging. Mattress firmness is rated on "
            "a scale not standardized across mattress manufacturers. Test any mattress "
            "in person before buying, since mattress firmness preference varies by "
            "sleeper."
        ),
    },
}


def build():
    base_prompts = {p[0]: p for p in base.PROMPTS}
    docs_out, prompts_out = [], []
    for pid, entry in KWSTUFF.items():
        _, domain, question, target_fmt, base_docs = base_prompts[pid]
        assert set(base_docs) == set(base.FORMATS), f"{pid}: format set mismatch"
        doc_ids = []
        for fmt in base.FORMATS:
            did = f"{pid}__{fmt}"
            doc_ids.append(did)
            if fmt == target_fmt:
                docs_out.append({
                    "doc_id": did, "prompt_id": pid, "format": fmt, "domain": domain,
                    "is_target": True,
                    "variants": {
                        "control": entry["control"].strip(),
                        "treatment": entry["stuffed"].strip(),
                    },
                })
            else:
                body = base_docs[fmt]
                assert isinstance(body, str), f"{pid}: unexpected tuple in non-target {fmt}"
                docs_out.append({
                    "doc_id": did, "prompt_id": pid, "format": fmt, "domain": domain,
                    "is_target": False,
                    "variants": {"control": body.strip(), "treatment": body.strip()},
                })
        prompts_out.append({
            "prompt_id": pid, "domain": domain, "question": question,
            "target_doc_id": f"{pid}__{target_fmt}", "target_format": target_fmt,
            "doc_ids": doc_ids,
        })

    corpus = {
        "corpus_version": "kwstuff-v1",
        "intervention": "keyword_stuffing",
        "base_corpus_version": "0.4",
        "n_prompts": len(prompts_out),
        "n_docs": len(docs_out),
        "formats": base.FORMATS,
        "domains": sorted({p["domain"] for p in prompts_out}),
        "prompts": prompts_out,
        "documents": docs_out,
    }
    payload = json.dumps(corpus, indent=2, sort_keys=True, ensure_ascii=False)
    corpus["corpus_sha256"] = hashlib.sha256(payload.encode()).hexdigest()[:16]

    out = pathlib.Path(__file__).parent / "corpus_kwstuff_v1.json"
    out.write_text(json.dumps(corpus, indent=2, ensure_ascii=False))

    from collections import Counter
    tf = Counter(p["target_format"] for p in prompts_out)
    dm = Counter(p["domain"] for p in prompts_out)
    print(f"wrote {out}")
    print(f"  prompts={len(prompts_out)} docs={len(docs_out)} sha={corpus['corpus_sha256']}")
    print(f"  target format balance: {dict(tf)}")
    print(f"  domain balance:        {dict(dm)}")
    wc = [len(d["variants"]["control"].split()) for d in docs_out]
    print(f"  doc length words: min={min(wc)} median={sorted(wc)[len(wc)//2]} max={max(wc)}")
    tgt = [d for d in docs_out if d["is_target"]]
    delta = [len(d["variants"]["treatment"].split()) - len(d["variants"]["control"].split()) for d in tgt]
    print(f"  target length delta (stuffed-control): min={min(delta)} max={max(delta)} mean={sum(delta)/len(delta):.1f}")


if __name__ == "__main__":
    build()
