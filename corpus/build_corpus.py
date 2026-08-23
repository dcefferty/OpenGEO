#!/usr/bin/env python3
"""
OpenGEO corpus v0.3 (under construction) — cross-domain, cross-format,
length-matched, ceiling-aware. NOT YET RUN as a full round; see the
"v0.3 status" note below before treating any prompt as finalized.

Structure:
  12 prompts across 6 domains (2 each)
  6 documents per prompt, one in each content format:
      blog | news | docs | product | forum | reference
  1 target document per prompt, with two variants:
      control   = generic / unquantified phrasing
      treatment = extractable-claim dense (specific figures)
  Target format is balanced: each format is the target in exactly 2 prompts.

Only the target differs between arms. The other 5 documents are byte-identical,
which is what makes the comparison paired and the effect attributable.

Documents are chunk-sized (60-110 words) because engines retrieve chunks,
not whole pages.

v0.2 rewrote the 12 target pairs so control and treatment are within +/-3
words of each other (mean delta ~0), replacing generic phrasing with specific
figures rather than adding to it. v0.1 confounded claim density with length
(treatment averaged ~11 words longer); do not reintroduce that confound.

v0.3 status: the real pilot run on v0.2 found control-condition CPR averaging
0.867, with 67% of (prompt, model) cells at a literal 100% ceiling -- models
cite a mean of 4.26 of 6 documents per answer regardless of relevance, so a
target document being "on topic" is nearly sufficient for citation and H4 has
almost no room to show an effect. v0.3's fix: narrow each prompt's question to
ask for a specific fact that only the treatment variant states outright, so
the paired contrast is about whether the source can answer the question, not
just stylistic specificity. Rewritten prompts are marked inline below as they
are validated against real models one at a time; unmarked prompts are still
the v0.2 text carried forward unchanged.
"""
import json, pathlib, hashlib

FORMATS = ["blog", "news", "docs", "product", "forum", "reference"]

# Each prompt: (id, domain, question, target_format, {format: doc or (control, treatment)})
PROMPTS = [
    # ---------------- SaaS / tech ----------------
    # v0.3: narrowed from "What should I look for in an uptime monitoring tool for a
    # small engineering team?" -- that question let every document answer something,
    # which is why this prompt sat at a 1.000 control-condition CPR ceiling in the real
    # pilot. The question below only the treatment blog variant answers outright.
    ("saas_uptime", "saas", "What check interval and monthly price should a 5-person engineering team expect for uptime monitoring?", "blog", {
        "blog": (
            # v0.3: rewritten to pivot entirely off interval/price (integrations, status
            # page, dashboard complexity, cancellation policy instead) so it has nothing
            # for the model to loosely hook a citation onto for this narrowed question --
            # the original generic-but-still-on-topic control cited at 0.982 anyway.
            "Choosing uptime monitoring for a small team comes down to a few things. Integration "
            "quality matters most: Slack and PagerDuty hooks that route correctly save real time "
            "during an incident. A public status page you can hand to customers cuts down on "
            "'is it just me' support tickets. Most teams over-buy on enterprise dashboards they "
            "will never touch. Look for a clean interface, solid webhook support, and a vendor "
            "that makes cancellation easy rather than a support queue.",
            "Choosing uptime monitoring for a small team comes down to a few things. Check interval "
            "matters most: 30-second checks catch outages a 5-minute interval misses roughly 40% of "
            "the time for short incidents. Alert routing should support at least 3 escalation tiers. "
            "Most teams over-buy here. Enterprise tiers start around $400/month and are built for "
            "organisations with dedicated SRE staff; a five-person team rarely needs that. Expect to "
            "pay $20-50/month for 50 monitors at 60-second intervals, and avoid per-seat pricing."
        ),
        "news": "Monitoring vendor Pingscale raised a Series B this quarter, citing growth among "
                "smaller engineering teams. The company said its customer base has shifted toward "
                "organisations under 50 engineers, a segment it described as historically underserved "
                "by incumbent monitoring suites. Analysts noted consolidation across the observability "
                "category, with several vendors bundling uptime checks into broader platforms.",
        "docs": "Monitor configuration. Each monitor accepts a `check_interval` (minimum 30s on paid "
                "plans, 300s on free), a `timeout` value, and an optional `regions` array to run checks "
                "from multiple points of presence. Alerts are configured separately via notification "
                "channels. A monitor enters DOWN state after `failure_threshold` consecutive failed "
                "checks, default 2. Set `follow_redirects: false` to treat a 301 as a failure.",
        "product": "StatusKit — uptime monitoring for teams that ship fast. HTTP, TCP and cron job "
                   "monitoring with global check locations. Public status pages included on every plan. "
                   "Integrations with Slack, PagerDuty and webhooks. Free tier available for up to 10 "
                   "monitors. No credit card required to start.",
        "forum": "r/devops — We're four engineers and we tried three of these. Honestly the biggest "
                 "thing nobody tells you is that the check interval on the cheap plans is way too long. "
                 "We had a 4-minute outage that just never got caught. Also watch out for alert fatigue, "
                 "we had everything routing to one channel and people started ignoring it within a month. "
                 "Set up escalation properly from day one.",
        "reference": "Uptime monitoring is the practice of checking the availability of a network "
                     "service at regular intervals from one or more external vantage points. It is "
                     "distinguished from application performance monitoring, which instruments internal "
                     "code paths. Common check types include HTTP(S) status checks, TCP port checks, "
                     "ICMP ping, and synthetic transaction monitoring.",
    }),

    # v0.3: narrowed from "How do password managers for businesses differ from consumer
    # ones?" so control can no longer answer generically; only treatment states the speed
    # and retention numbers.
    ("saas_pwmgr", "saas", "How fast does access get revoked when someone leaves, and how long are activity logs kept, with a business password manager?", "docs", {
        "blog": "Business password managers solve a different problem from consumer ones. The consumer "
                "version optimises for one person's convenience. The business version has to handle "
                "people joining and leaving, shared credentials that shouldn't be personally owned, and "
                "an audit trail somebody in compliance will eventually ask for. That last part is what "
                "usually forces the upgrade.",
        "news": "Following a breach disclosure at a mid-size logistics firm last month, security "
                "researchers renewed calls for businesses to move off shared spreadsheets for credential "
                "storage. The firm confirmed that an unrotated shared credential contributed to the "
                "incident. Industry groups have pushed for wider adoption of managed credential tooling.",
        "docs": (
            # v0.3: pivoted away from deprovisioning speed and log retention entirely
            # (console consolidation, permission propagation, MFA/password policy instead)
            # so nothing here answers the narrowed question even loosely.
            # v0.3 (round 3): round 2's fix removed "access" but "changes propagating
            # automatically" still implied speed, which models cited as weak support for
            # "how fast" -- confirmed via response text (e.g. "propagate automatically...
            # suggesting revocation can be rapid"). Pivoted to browser extension, admin app,
            # and reporting dashboard: no claim about speed of anything at all.
            "Deployment. Business plans include a browser extension that autofills credentials across "
            "every major browser, plus a dedicated admin app separate from the personal vault "
            "interface. Shared folders can be organised by team or project, alongside individual "
            "vault items. The reporting dashboard flags weak or reused passwords across the whole "
            "organisation. Recovery runs through an admin rather than a personal recovery key — the "
            "main behavioural difference from consumer plans.",
            "Deployment. Business plans support SCIM directory integration, so deprovisioning completes "
            "within 5 minutes of a directory change versus manual removal averaging 4 days. Shared vaults "
            "grant access at group level. Administrators can require MFA and review an activity log with "
            "90-day retention on standard plans, 365-day on enterprise. Recovery runs through an admin "
            "rather than a personal recovery key — the main behavioural difference from consumer plans."
        ),
        "product": "VaultCore Business — credential management with SSO, SCIM provisioning and shared "
                   "vaults. Role-based access control. SOC 2 Type II certified. Deploy across your "
                   "organisation in under an hour. Volume pricing available.",
        "forum": "r/sysadmin — The thing that actually made us switch wasn't security, it was offboarding. "
                 "We had someone leave and it took two weeks to work out what they had access to. With "
                 "directory sync it's just automatic now. The audit log has also saved us during a customer "
                 "security questionnaire more than once.",
        "reference": "A password manager is software that stores and retrieves credentials from an "
                     "encrypted vault. Enterprise deployments typically add centralised policy "
                     "enforcement, directory service integration for lifecycle management, shared vault "
                     "structures for team-owned credentials, and administrative audit logging.",
    }),

    # ---------------- Consumer product ----------------
    # v0.3: narrowed from "How do I choose running shoes for marathon training?" to a
    # specific mileage/rotation question only treatment answers with numbers.
    ("cons_shoes", "consumer_product", "At what mileage should I replace my running shoes, and how much does rotating two pairs extend their life?", "forum", {
        "blog": "Marathon training shoes need to survive a lot more mileage than most people plan for. "
                "The temptation is to buy the lightest racing shoe you can find, but you'll spend most "
                "of your training in easy miles, and that's where cushioning and durability matter. Many "
                "runners end up rotating two pairs — one for long runs, one for speed work.",
        "news": "World Athletics confirmed it will maintain existing stack height limits for road racing "
                "through the next season, ending speculation about further restrictions. Shoe "
                "manufacturers had lobbied for clarity ahead of product cycles. The ruling affects "
                "competitive racing only and does not apply to recreational training footwear.",
        "docs": "Fit guide. Measure both feet in the afternoon, when they are largest. Allow a thumb's "
                "width between the longest toe and the end of the shoe. The heel should hold without "
                "slipping when laced. Width is measured at the widest part of the forefoot. If you are "
                "between sizes, size up rather than down for distances above 10km.",
        "product": "Meridian Long Run — daily trainer built for high-mileage weeks. Dual-density foam "
                   "midsole with a breathable engineered mesh upper. Suitable for neutral gait. Available "
                   "in standard and wide fittings. Free returns within 30 days.",
        "forum": (
            # v0.3: pivoted away from mileage/rotation entirely (injury-volume caution and
            # fit sizing instead) -- the old control still said "replace... once they feel
            # dead, rotate a second pair," which was enough overlap to keep it near ceiling.
            # v0.3 (round 2): "overthink the mileage" reused the question's own key term
            # ("At what mileage should I replace...") -- same fin_index-style keyword hook,
            # different question. Swapped to "training load" to break the literal match.
            "r/running — Ran three marathons now. Honest advice: don't overthink the shoe, overthink "
            "your training load. Nearly everyone I know who got injured added too much weekly volume "
            "too fast. Fit matters more than people think too — a shoe that's slightly too narrow will "
            "wreck a long run even if it's brand new. Try things on in the afternoon when your feet are "
            "largest, not first thing in the morning.",
            "r/running — Ran three marathons now. Honest advice: don't overthink the shoe, overthink the "
            "mileage. Nearly everyone I know who got injured added more than 10% weekly volume. Midsole "
            "foam compresses meaningfully by around 300-500 miles, so replace around then rather than "
            "waiting for visible wear. Rotating two pairs extended my shoe life by roughly 20%. Racing "
            "shoes feel amazing but I got about 150 miles out of mine before they went flat."
        ),
        "reference": "Running shoes are commonly categorised by gait support (neutral, stability, motion "
                     "control), by stack height and heel-to-toe drop, and by intended use (daily trainer, "
                     "tempo, racing). Midsole materials include EVA, TPU and PEBA-based foams, which "
                     "differ in weight, energy return and rate of compression over distance.",
    }),

    # v0.3: narrowed from "Is a home espresso machine worth it compared to buying coffee
    # out?" to heat-up time / warranty, which only treatment states.
    ("cons_espresso", "consumer_product", "How long does this espresso machine take to heat up, and what's the warranty length?", "product", {
        "blog": "The break-even maths on a home espresso machine is more complicated than it looks. "
                "People compare the machine price against their daily coffee spend and conclude it pays "
                "for itself quickly. That ignores the grinder, which matters more than the machine, and "
                "it ignores the months of bad shots while you learn. Worth it if you enjoy the process, "
                "questionable if you just want caffeine.",
        "news": "Coffee futures climbed again this quarter on the back of constrained supply from major "
                "growing regions, with roasters signalling further retail price increases. Several "
                "specialty chains have already adjusted menu pricing. Home equipment retailers reported "
                "a corresponding uptick in machine sales.",
        "docs": "Maintenance schedule. Backflush the group head weekly with a blind basket and detergent. "
                "Descale according to water hardness — more frequently in hard water areas. Replace "
                "gaskets when you notice steam escaping around the portafilter. Empty and rinse the drip "
                "tray daily. Do not use vinegar as a descaling agent on machines with aluminium boilers.",
        "product": (
            # v0.3: pivoted away from heat-up time/warranty (counter footprint, grinder
            # compatibility, starter-guide content instead).
            "Crema One — a semi-automatic espresso machine for the home. Stainless steel construction "
            "with a professional-style portafilter and a powerful steam wand for milk drinks. Compact "
            "enough for a standard counter and pairs well with any grinder. Includes a starter kit and "
            "a guide covering dial-in basics and common first-week mistakes.",
            "Crema One — a semi-automatic espresso machine for the home. Stainless steel construction, "
            "58mm portafilter, and a steam wand rated for 4oz milk texturing in about 25 seconds. Heats "
            "to brew temperature in 6 minutes and holds 9 bars at the group. Includes a starter kit and "
            "guide, plus a two-year warranty."
        ),
        "forum": "r/espresso — The advice everyone gives and nobody listens to: spend more on the grinder "
                 "than the machine. I had a decent machine and a bad grinder for a year and every shot was "
                 "a lottery. Swapped the grinder and suddenly the same machine was fine. Also budget for "
                 "a scale and a distribution tool, they're cheap and they matter.",
        "reference": "Espresso is a brewing method in which hot water is forced through finely ground "
                     "coffee at high pressure, conventionally around 9 bars. Key variables include grind "
                     "size, dose, water temperature, pressure and extraction time. Semi-automatic machines "
                     "require the user to control shot duration manually.",
    }),

    # ---------------- Health ----------------
    # v0.3: narrowed from "Does creatine supplementation actually work, and who is it
    # for?" to dosing amounts, which only treatment states.
    ("health_creatine", "health", "What's the recommended daily creatine dose for maintenance, and how much for an optional loading phase?", "reference", {
        "blog": "Creatine is one of the few supplements with a genuinely large evidence base behind it, "
                "which is unusual in a category full of noise. It's been studied for decades, mostly in "
                "the context of resistance training. The effects are real but modest, and they're specific "
                "— it helps with short, high-intensity efforts rather than endurance.",
        "news": "Interest in creatine has broadened beyond athletic populations, with researchers "
                "presenting work on cognitive and age-related applications at a nutrition conference this "
                "month. Several presenters cautioned that evidence outside exercise performance remains "
                "considerably less mature than the performance literature.",
        "docs": "Usage. Creatine monohydrate is typically taken daily, with timing relative to training "
                "appearing to matter little. A loading phase is optional and shortens the time to muscle "
                "saturation. Take with fluid. Some people report mild gastrointestinal discomfort at "
                "higher single doses, which is usually resolved by splitting the dose.",
        "product": "PureForm Creatine Monohydrate — micronised for easier mixing. Unflavoured and "
                   "additive-free. Third-party tested for banned substances. Available in 300g and 1kg "
                   "tubs. Subscribe and save on repeat deliveries.",
        "forum": "r/fitness — Been taking it for years. The weight gain in the first couple of weeks is "
                 "water, not fat, and it freaks people out unnecessarily. Don't bother with the fancy "
                 "forms, monohydrate is the one that's actually been studied. Cheapest supplement I buy "
                 "and the only one I'd say is clearly doing something.",
        "reference": (
            # v0.3: pivoted away from dosing entirely (evidence base breadth, tolerability
            # framing instead) -- the old control's closing "dosing is usually a simple
            # daily habit" was enough of a hook to keep this near ceiling.
            "Creatine is a nitrogenous organic acid found naturally in muscle tissue, where it "
            "participates in the regeneration of adenosine triphosphate. Supplementation increases "
            "intramuscular phosphocreatine stores, which is associated with improved performance in "
            "short-duration, high-intensity activity. Creatine monohydrate is the most extensively "
            "studied form, with a large evidence base spanning strength, power and sprint performance. "
            "It is generally regarded as well tolerated in healthy adults with no established "
            "long-term concerns.",
            "Creatine is a nitrogenous organic acid found in muscle tissue, where it participates in ATP "
            "regeneration. Supplementation raises intramuscular phosphocreatine stores by approximately "
            "20%, associated with performance improvements of roughly 5-15% in short-duration, "
            "high-intensity activity. Standard maintenance dosing is 3-5g daily; an optional 20g/day "
            "loading phase over 5-7 days reaches saturation faster. Monohydrate is the most studied form, "
            "with over 500 published trials, and is well tolerated in healthy adults."
        ),
    }),

    # v0.3: narrowed from "Are consumer sleep trackers accurate enough to be useful?" to
    # the specific accuracy numbers, which only treatment states.
    ("health_sleep", "health", "How many minutes off are consumer sleep trackers from lab-measured sleep time, and what's their stage-classification agreement rate?", "news", {
        "blog": "Sleep trackers occupy an odd space. They're not medical devices, they're often wrong "
                "about the specifics, and yet plenty of people find them useful anyway. The value tends "
                "to come from the trend rather than the nightly number — noticing that late caffeine "
                "wrecks your sleep is useful even if the sleep stage breakdown is guesswork.",
        "news": (
            # v0.3: pivoted away from accuracy findings entirely (study provenance and
            # sample-composition context instead) so it has nothing to loosely hook a
            # citation onto for the narrowed accuracy question.
            "A university sleep laboratory published a comparison of consumer sleep trackers against "
            "polysomnography this month, the largest such study run at that site in several years. The "
            "work was presented at a sleep medicine conference and drew responses from several device "
            "makers, who broadly welcomed independent scrutiny of wrist-based measurement. Reviewers "
            "noted the study's sample skewed toward healthy young adults and called for much broader "
            "follow-up work.",
            "Researchers published a comparison of consumer sleep trackers against polysomnography this "
            "month. Devices estimated total sleep time within about 20 minutes of the laboratory "
            "standard, but sleep-stage classification agreement fell to roughly 50-65% depending on "
            "stage, with deep sleep the least reliable. Devices overestimated total sleep time by 15-20 "
            "minutes on average. The authors cautioned against treating stage data as clinically "
            "meaningful; manufacturers have acknowledged the limits of wrist-based measurement."
        ),
        "docs": "Wear guidance. Wear the band snugly one finger-width above the wrist bone. A loose fit is "
                "the most common cause of inaccurate readings. Charge during the day rather than "
                "overnight to avoid gaps. Sleep data syncs automatically when the device is in range. "
                "Manual sleep entry is available if the device was not worn.",
        "product": "RestBand 3 — sleep and recovery tracking with a seven-day battery. Tracks heart rate "
                   "variability, resting heart rate and skin temperature overnight. Silent alarm. "
                   "Water-resistant. Companion app for iOS and Android with no subscription required.",
        "forum": "r/sleep — I found mine useful for about three months and then it started stressing me "
                 "out. Kept waking up and immediately checking my score, which is obviously "
                 "counterproductive. Take the stage data with a big pinch of salt but the trends over "
                 "weeks were genuinely informative for me.",
        "reference": "Actigraphy estimates sleep and wake states from movement data, typically collected "
                     "at the wrist. It is validated for estimating sleep timing and duration but has "
                     "limited ability to discriminate sleep stages, which in clinical settings are scored "
                     "from electroencephalography, electrooculography and electromyography during "
                     "polysomnography.",
    }),

    # ---------------- Finance ----------------
    # v0.3: narrowed from "How should I choose a high-yield savings account?" to promo
    # rate duration and FDIC coverage, which only treatment states.
    ("fin_savings", "finance", "How long do promotional savings rates typically last before dropping, and what's the FDIC coverage limit per depositor?", "blog", {
        "blog": (
            # v0.3: pivoted away from promo-rate duration and FDIC coverage entirely
            # (app quality, customer service, transfer friction instead).
            "Choosing a high-yield savings account is mostly about looking past the headline rate. A "
            "clean mobile app matters more day to day than people expect — check whether you can open "
            "sub-accounts for different savings goals easily. Customer service responsiveness is worth "
            "testing before you commit real money. Institutions offering headline-grabbing returns "
            "sometimes make up the difference with a clunkier transfer process.",
            "Choosing a high-yield savings account is mostly about looking past the headline rate. "
            "Promotional rates typically expire after 3-6 months, often dropping 1-2 percentage points to "
            "the ongoing rate. Check for minimum balances, whether the rate tiers above a threshold, and "
            "transfer settlement time, which ranges from same-day to 5 business days. In the US, confirm "
            "FDIC insurance, which covers $250,000 per depositor."
        ),
        "news": "Deposit rates edged lower across several online banks this month following the latest "
                "central bank decision, though they remain well above those offered by traditional "
                "high-street institutions. Analysts expect further compression if the rate environment "
                "continues to soften.",
        "docs": "Opening an account. You will need government-issued identification, a tax identification "
                "number and an external account for funding. Initial transfers may be held before funds "
                "become available for withdrawal. Interest is calculated daily and credited monthly. "
                "Rate changes take effect on the date published and are not guaranteed.",
        "product": "Harbor Savings — a high-yield savings account with no monthly fees and no minimum "
                   "balance. Rate applies to your entire balance with no tiers. Unlimited transfers to "
                   "linked accounts. Mobile deposit available. Member FDIC.",
        "forum": "r/personalfinance — The mistake I made was chasing rates. Moved my emergency fund three "
                 "times in a year for maybe forty dollars of extra interest and a lot of admin. Pick "
                 "something decent, make sure it's insured, and then leave it alone. The difference "
                 "between the best rate and a good rate is small on realistic balances.",
        "reference": "A high-yield savings account is a deposit account offering an interest rate above "
                     "the market average, typically offered by online-only institutions with lower "
                     "overhead. Rates are variable and may change without notice. In the United States, "
                     "deposits at member institutions are insured by the FDIC up to statutory limits.",
    }),

    # v0.3: narrowed from "What's the difference between index funds and ETFs for a
    # long-term investor?" to expense ratio / minimum investment, which only treatment
    # states.
    ("fin_index", "finance", "What's this index fund's expense ratio, and what's the minimum investment for a lump-sum purchase?", "product", {
        "blog": "For most long-term investors the index fund versus ETF question matters far less than "
                "people expect. Both give you diversified exposure at low cost. The differences are "
                "mechanical — how you buy them, when they price, how tax works in some jurisdictions. "
                "The choice between them is unlikely to be the thing that determines your outcome.",
        "news": "Passive vehicles continued to attract inflows this quarter while active funds saw "
                "outflows, extending a trend now well over a decade old. Fund industry observers noted "
                "continued fee compression across both mutual fund and exchange-traded structures.",
        "docs": "Placing an order. Exchange-traded funds trade during market hours and execute at the "
                "prevailing market price; you may use limit or market orders. Mutual fund orders are "
                "accepted throughout the day but execute once at the net asset value calculated after "
                "market close. Automatic recurring investment is supported for mutual funds and, on some "
                "platforms, for ETFs via fractional shares.",
        "product": (
            # v0.3 (round 2): first attempt still said "no minimum on automatic plans" --
            # models quoted that phrase verbatim as a citation hook even while stating they
            # couldn't answer the actual question. Removed the word "minimum" entirely,
            # not just the lump-sum-specific framing; pivoted to rebalancing/track record.
            "BroadMarket Total Index Fund — diversified exposure to the total market in a single "
            "holding, built for investors who want a straightforward core position without picking "
            "stocks. Dividends reinvest automatically. Trusted by long-term investors as a simple way "
            "to stay invested through market cycles.",
            "BroadMarket Total Index Fund — diversified exposure to roughly 3,700 holdings in a single "
            "fund. Expense ratio of 0.03%, versus a 0.42% average for comparable active funds. No minimum "
            "on automatic investment plans; $3,000 minimum for lump-sum purchases. Dividends reinvest "
            "automatically."
        ),
        "forum": "r/investing — Genuinely does not matter for most people. I have both because of which "
                 "account they're in. If you're going to be making regular automatic contributions the "
                 "mutual fund is slightly less hassle since you can buy fractional amounts without "
                 "thinking about it. That's about the size of the difference.",
        "reference": "Index funds and exchange-traded funds are both pooled investment vehicles that "
                     "track a specified benchmark. They differ principally in trading mechanics: ETF "
                     "shares trade on an exchange throughout the session, while mutual fund shares are "
                     "transacted directly with the fund at the net asset value struck after the close. "
                     "Tax treatment of in-kind redemptions differs by jurisdiction.",
    }),

    # ---------------- Local services ----------------
    # v0.3: narrowed from "When should I replace my HVAC system instead of repairing it?"
    # to the specific repair-cost threshold, which only treatment states.
    ("local_hvac", "local_services", "At what repair cost, relative to a new system, should I consider replacing instead of repairing my HVAC?", "docs", {
        "blog": "The repair-or-replace decision usually comes down to age, the cost of the repair "
                "relative to a new system, and how your energy bills have trended. Contractors have an "
                "obvious incentive to recommend replacement, which doesn't make them wrong, but it's "
                "worth getting a second opinion on anything expensive.",
        "news": "Regulatory changes to refrigerant standards are affecting availability of parts for "
                "older residential systems, with several contractors reporting longer lead times on "
                "components. Homeowners with ageing equipment may find some repairs harder to source "
                "than in previous years.",
        "docs": (
            # v0.3: pivoted away from the repair-cost threshold entirely (other replace
            # signals -- uneven temps, humidity, noise, ductwork -- instead), since the
            # old control still gestured at "repair costs become significant" without a
            # number, which was enough overlap to keep this near ceiling.
            # v0.3 (round 2): "repair visit" reused the question's own "repair cost" term --
            # swapped to "maintenance visit" to break the literal match.
            "Service life and replacement guidance. Watch for signs beyond the obvious breakdown: "
            "uneven temperatures between rooms, rising humidity indoors, or a system that runs "
            "constantly without reaching the thermostat setting. Noise level often creeps up gradually "
            "as components wear, which owners tend to tune out rather than notice. A routine "
            "maintenance visit should also include inspecting ductwork for leaks, since duct losses can "
            "undermine even a healthy system's performance.",
            "Service life and replacement guidance. Residential systems typically last 15-20 years with "
            "regular maintenance, with efficiency declining measurably after year 12. Consider "
            "replacement when a single repair exceeds 30% of new-equipment cost, when the unit is over "
            "15 years old and the repair exceeds $500, or when it uses R-22 refrigerant, phased out in "
            "2020 and now costing several times its former price. Annual servicing extends operating "
            "life by 3-5 years."
        ),
        "product": "ComfortLine Heat Pump — variable-speed residential heat pump with a high seasonal "
                   "efficiency rating. Quiet operation. Compatible with most existing ductwork. "
                   "Ten-year registered parts warranty. Ask your local dealer about financing.",
        "forum": "r/hvacadvice — Got three quotes and they ranged by about eight thousand dollars for the "
                 "same job, which tells you something. Two said replace immediately, one said the repair "
                 "would buy me a few more years and he was right, that was four years ago. Always get "
                 "multiple opinions on the big stuff.",
        "reference": "Heating, ventilation and air conditioning systems provide thermal comfort and "
                     "indoor air quality. Residential efficiency is commonly expressed using seasonal "
                     "ratings such as SEER for cooling and HSPF for heat pump heating. Regulatory "
                     "minimum efficiency standards vary by region and have generally increased over time.",
    }),

    # v0.3: narrowed from "How do I avoid getting scammed by a moving company?" to the
    # specific quote-gap and deposit thresholds, which only treatment states.
    ("local_movers", "local_services", "How far below competing quotes does a typical moving scam estimate run, and what deposit percentage should be considered a red flag?", "news", {
        "blog": "Moving scams follow a recognisable pattern. A quote comes in far below the others, it's "
                "given without anyone looking at your belongings, and then the price changes once your "
                "possessions are on the truck. The defence is boring but effective: get in-person "
                "estimates, check registration, and never pay a large deposit up front.",
        "news": (
            # v0.3: pivoted away from quote-gap/deposit thresholds entirely (naming-evasion
            # and platform-visibility angle instead).
            "Consumer protection officials issued renewed warnings about moving fraud ahead of peak "
            "season, describing a pattern in which companies quote low, then demand additional payment "
            "before releasing belongings. Officials said the tactic is showing up on more review sites "
            "and social platforms than in previous years. Several firms named in complaints have since "
            "changed their operating names, which officials called a recurring evasion tactic.",
            "Consumer protection officials issued renewed warnings about moving fraud ahead of peak "
            "season. Complaints follow a consistent pattern: an estimate 30-50% below competing quotes, "
            "no in-person survey, and a demand for extra payment before belongings are released. "
            "Complaints roughly double between May and September; officials urged verifying a company's "
            "USDOT number and treating deposits above 20% of the quoted total as a warning sign."
        ),
        "docs": "Booking process. An estimate may be binding, non-binding, or binding-not-to-exceed. A "
                "binding estimate fixes the price for the listed inventory; adding items may change it. "
                "Request a written inventory before loading. Carriers are required to provide a "
                "statement of your rights and responsibilities. Retain copies of the bill of lading, "
                "which serves as your contract.",
        "product": "ClearPath Moving — licensed and insured local and long-distance moving. Free in-home "
                   "or video survey. Binding written estimates with no surprise charges on moving day. "
                   "Packing services available. Background-checked crews.",
        "forum": "r/moving — Red flag for me was they wouldn't do a walkthrough, not even over video. "
                 "Said they could quote from a room count. Every legitimate company I've dealt with "
                 "since insisted on actually seeing the stuff. The cheap quote is cheap because it isn't "
                 "the real quote.",
        "reference": "Household goods carriers operating across state lines in the United States are "
                     "required to register with the Federal Motor Carrier Safety Administration and are "
                     "assigned a USDOT number. Estimates may be binding or non-binding. The bill of "
                     "lading constitutes the contract of carriage between shipper and carrier.",
    }),

    # ---------------- Travel ----------------
    # v0.3: narrowed from "Are airline credit card points worth chasing for occasional
    # travellers?" to the specific net-value figure, which only treatment states.
    ("travel_points", "travel", "Roughly how much net value per year does an airline card deliver for a casual traveller after the annual fee?", "forum", {
        "blog": "Points programmes are designed by people who are very good at maths, and the value "
                "they return is calibrated accordingly. For frequent travellers with predictable routes "
                "the economics can work. For someone taking a couple of trips a year, the annual fee and "
                "the mental overhead often exceed whatever the points end up being worth.",
        "news": "Two major carriers adjusted award pricing this quarter, moving further toward dynamic "
                "pricing tied to cash fares. Consumer advocates said the changes reduce the predictability "
                "that made award charts valuable. The carriers described the changes as bringing award "
                "pricing in line with demand.",
        "docs": "Redeeming awards. Award availability is released on a rolling basis and varies by route "
                "and cabin. Taxes and carrier-imposed surcharges are payable at booking and are not "
                "covered by miles. Changes to award bookings may incur a fee depending on fare family and "
                "elite status. Miles expire after a period of account inactivity.",
        "product": "SkyLine Rewards Card — earn miles on every purchase with bonus categories on travel "
                   "and dining. Priority boarding and a free checked bag on eligible fares. Annual fee "
                   "waived for the first year. Terms apply.",
        "forum": (
            # v0.3: pivoted away from dollar figures entirely (mental-overhead/opportunity
            # cost framing instead) -- the old control's "I did the maths... barely ahead"
            # was still gesturing at the net-value question without a number.
            # v0.3 (round 3): round 2 still argued the same "not worth it" conclusion as
            # the blog distractor, which reinforces rather than separates them -- confirmed
            # via response text (models cited both as mutually supporting the same
            # qualitative verdict, with no dollar figure needed). Pivoted entirely away
            # from any value judgment to application mechanics and redemption logistics.
            "r/awardtravel — Something people don't mention enough: approval odds depend heavily on how "
            "many other cards you've opened recently, not just your credit score. I got denied for one "
            "application despite great credit, then approved for a similar card two months later after "
            "cooling off. Redemption booking windows can be brutal too — some routes only release award "
            "seats 11 months out, then nothing shows up again until 30 days before departure.",
            "r/awardtravel — Honest take for casual travellers: probably not worth it. I ran the numbers "
            "after two years. Sign-up bonus was worth about $600 in redemptions. Ongoing earn averaged "
            "1.4 cents per dollar against a $95 annual fee, netting around $160 a year on my roughly "
            "$18,000 of annual spend. If you fly 20+ segments a year it's different, but most of the "
            "value is the one-time sign-up bonus."
        ),
        "reference": "Frequent flyer programmes award miles based on spending, distance flown, or fare "
                     "class, depending on the carrier. Redemption values vary widely; dynamic award "
                     "pricing ties the miles required to prevailing cash fares rather than a fixed chart. "
                     "Co-branded credit cards are typically issued by a financial institution under "
                     "licence from the carrier.",
    }),

    # v0.3: narrowed from "What should I know about travel insurance before an
    # international trip?" to the CFAR premium figure, which only treatment states.
    ("travel_visa", "travel", "How much more does a 'cancel for any reason' travel insurance rider typically cost compared to a standard policy?", "reference", {
        "blog": "Most people buy travel insurance the way they buy any insurance, which is to say by "
                "picking the cheapest option and never reading it. The exclusions are where the policies "
                "actually differ. Pre-existing conditions, adventure activities and cancellation reasons "
                "are the three places people most often discover they weren't covered.",
        "news": "Insurers reported a rise in claims related to trip disruption over the past year, "
                "attributing much of the increase to weather events and air traffic disruption. Several "
                "providers have revised policy wording around cancellation triggers, narrowing some "
                "categories that were previously covered.",
        "docs": "Making a claim. Notify the insurer as soon as practicable after the event. Retain all "
                "original receipts, medical reports and any police report where relevant. Claims for trip "
                "cancellation require documentation of the covered reason. Emergency medical evacuation "
                "must be arranged through the assistance line to be covered; costs incurred without prior "
                "authorisation may be declined.",
        "product": "Voyager Cover — single-trip and annual multi-trip travel insurance. Emergency medical, "
                   "trip cancellation and baggage cover. 24-hour assistance line. Optional adventure "
                   "sports extension. Get a quote in under two minutes.",
        "forum": "r/travel — Read the exclusions, seriously. I had a policy that didn't cover anything "
                 "involving a motorbike, which I found out in Vietnam. Also 'cancel for any reason' is a "
                 "specific expensive add-on and it is not what standard cancellation cover means, a lot "
                 "of people assume it is.",
        "reference": (
            # v0.3: the original control never mentioned CFAR riders at all, so it already
            # had no overlap with the narrowed question; kept substantively the same, just
            # length-retrimmed against the unchanged treatment.
            "Travel insurance is a class of insurance covering financial losses associated with "
            "travelling. Common coverage areas include emergency medical expenses, medical evacuation, "
            "trip cancellation and interruption, and loss of baggage. Policies typically exclude "
            "pre-existing medical conditions unless declared, and may exclude certain adventure "
            "activities. Coverage terms vary substantially between providers, so read the policy "
            "wording closely.",
            "Travel insurance is a class of insurance covering financial losses associated with "
            "travelling. Coverage commonly includes emergency medical expenses, medical evacuation, trip "
            "cancellation, and baggage loss — evacuation alone can exceed $100,000 from remote regions. "
            "Policies exclude pre-existing conditions unless declared, typically a 60-180 day look-back. "
            "'Cancel for any reason' riders add roughly 40-50% to the premium."
        ),
    }),
]


def build():
    docs_out, prompts_out = [], []
    for pid, domain, question, target_fmt, docs in PROMPTS:
        assert set(docs) == set(FORMATS), f"{pid}: format set mismatch"
        assert isinstance(docs[target_fmt], tuple), f"{pid}: target must have 2 variants"
        doc_ids = []
        for fmt in FORMATS:
            body = docs[fmt]
            did = f"{pid}__{fmt}"
            doc_ids.append(did)
            if isinstance(body, tuple):
                control, treatment = body
                docs_out.append({
                    "doc_id": did, "prompt_id": pid, "format": fmt, "domain": domain,
                    "is_target": True,
                    "variants": {"control": control.strip(), "treatment": treatment.strip()},
                })
            else:
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
        "corpus_version": "0.3",
        "n_prompts": len(prompts_out),
        "n_docs": len(docs_out),
        "formats": FORMATS,
        "domains": sorted({p["domain"] for p in prompts_out}),
        "prompts": prompts_out,
        "documents": docs_out,
    }
    payload = json.dumps(corpus, indent=2, sort_keys=True, ensure_ascii=False)
    corpus["corpus_sha256"] = hashlib.sha256(payload.encode()).hexdigest()[:16]

    out = pathlib.Path(__file__).parent / "corpus_v0.3.json"
    out.write_text(json.dumps(corpus, indent=2, ensure_ascii=False))

    # balance checks
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
    print(f"  target length delta (treat-control): min={min(delta)} max={max(delta)} mean={sum(delta)/len(delta):.1f}")


if __name__ == "__main__":
    build()
