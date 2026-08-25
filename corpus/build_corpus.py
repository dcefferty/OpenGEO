#!/usr/bin/env python3
"""
OpenGEO corpus v0.4 (under construction) — cross-domain, cross-format,
length-matched, ceiling-aware, scaled toward Round 1.

Structure:
  48 prompts across 24 domains (2 each)
  6 documents per prompt, one in each content format:
      blog | news | docs | product | forum | reference
  1 target document per prompt, with two variants:
      control   = generic / unquantified phrasing
      treatment = extractable-claim dense (specific figures)
  Target format is balanced: each format is the target in exactly 8 prompts.

Only the target differs between arms. The other 5 documents are byte-identical,
which is what makes the comparison paired and the effect attributable.

Documents are chunk-sized (60-110 words) because engines retrieve chunks,
not whole pages.

v0.2 rewrote the original 12 target pairs so control and treatment are within
+/-3 words of each other (mean delta ~0), replacing generic phrasing with
specific figures rather than adding to it. v0.1 confounded claim density with
length (treatment averaged ~11 words longer); do not reintroduce that
confound.

v0.3 fixed a ceiling problem: the real pilot run on v0.2 found
control-condition CPR averaging 0.867, with 67% of (prompt, model) cells at a
literal 100% ceiling -- models cite a mean of 4.26 of 6 documents per answer
regardless of relevance, so a target document being "on topic" was nearly
sufficient for citation and H4 had almost no room to show an effect. The fix,
validated against real models before being trusted: narrow each question to a
specific fact only the treatment variant states, AND rewrite control so it
shares no topical surface with that fact -- not just the literal number. Two
distinct failure modes surfaced during validation and are worth remembering
if this corpus is touched again: (1) a control that drops the number but
reuses a literal keyword the question also uses gets quoted verbatim as a
citation hook even when the model says it can't answer (e.g. fin_index's
"minimum"); (2) a control that keeps the same qualitative conclusion as the
question -- or as an unrelated distractor document -- gets cited as mutually
reinforcing evidence with zero keyword overlap and no number at all (e.g.
travel_points arguing "not worth it" without a dollar figure). Full v0.3 run
(12 prompts, `results/runs_v0.3.jsonl`): H4 pooled delta +0.493, p=0.0005,
significant for all 8 models.

v0.4 scales the validated v0.3 recipe from 12 to 48 prompts (item 5's sizing
recommendation, rounded to a clean 8-per-format multiple of 6 rather than the
uneven 50) for Round 1. The 36 new prompts were drafted applying both lessons
above from the start and audited with a keyword/directional-echo check before
being trusted -- not individually validated against real models the way the
original 12 were, since that would cost more than the Round 1 run itself.
Any prompt that still turns out to sit at a ceiling shows up in the real
run's per-prompt breakdown and gets excluded from pooled figures the same way
an unreliable model would, rather than invalidating the round.
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

    # =============== Round 1 expansion: 36 new prompts, 18 domains ===============
    # ---------------- education ----------------
    ("edu_bootcamp", "education", "How many hours per week should I expect to study in a coding bootcamp, and what's the job placement rate within 6 months?", "blog", {
        "blog": (
            "Choosing a coding bootcamp is mostly about being honest with yourself "
            "about time. Curriculum breadth matters — look for one covering a real "
            "portfolio project, not just tutorials. Mentor access is worth more than "
            "people think; being stuck a day on something a mentor could unblock in "
            "minutes is the single biggest waste. Check whether the alumni network is "
            "actually active or a dormant Slack.",
            "Choosing a coding bootcamp is mostly about being honest with yourself "
            "about time. Full-time programs expect roughly 60-70 hours a week between "
            "class and homework. Ask for the school's job placement rate directly — "
            "reputable ones report around 70-80% employed in a related role within 6 "
            "months, tracked and published under CIRR standards. Part-time programs run "
            "15-20 hours a week but take twice as long to finish."
        ),
        "news": "A coding bootcamp operator disclosed layoffs affecting roughly a third "
                "of its instructional staff this quarter, citing softer enrollment as "
                "employers tightened entry-level hiring. Industry observers noted "
                "several competitors have quietly shortened program length to cut "
                "costs. The company said existing students would not be affected and "
                "reaffirmed its outcomes reporting commitments.",
        "docs": "Enrollment requirements. Applicants complete a technical assessment "
                "covering basic logic and array manipulation before an admissions "
                "interview. A deposit is due within 10 days of acceptance to hold a "
                "cohort seat. Financing options include an income share agreement or a "
                "fixed-tuition loan through a partner lender; ISA repayment caps at a "
                "percentage of income once a qualifying job is secured.",
        "product": "CodeForge Immersive — 12-week full-time software engineering "
                   "bootcamp. Live instruction plus asynchronous project work. "
                   "Dedicated career coach assigned at week 6. Curriculum covers "
                   "full-stack JavaScript and one backend language of your choice. "
                   "Cohorts start monthly.",
        "forum": "r/codingbootcamp — Finished mine eight months ago. Nobody tells you "
                 "the actual grind is the job search after, not the bootcamp itself. "
                 "The program was fine, reasonable pace, good instructors. The career "
                 "services push was where it fell apart — felt like a form email "
                 "machine after week 2. Do your own networking from day one, don't wait "
                 "for them.",
        "reference": "Coding bootcamps are accelerated, intensive training programs "
                     "intended to prepare participants for entry-level software "
                     "development roles, typically spanning 8-24 weeks. Format varies "
                     "between full-time immersive and part-time extended schedules. "
                     "Outcomes reporting is voluntary in most jurisdictions; the "
                     "Council on Integrity in Results Reporting (CIRR) is the most "
                     "widely adopted third-party verification standard.",
    }),

    ("edu_certification", "education", "How many questions are on the PMP certification exam, and what's the passing score threshold?", "docs", {
        "blog": "Project management certifications get debated endlessly online, but "
                "the practical case for one is simple: recruiters filter on it, "
                "especially at larger companies. The value is less about the material — "
                "most of it you'll know from experience — and more about signaling you "
                "can commit to finishing something with a formal structure. Worth it if "
                "you're job hunting, less clear if you're already employed and happy.",
        "news": "The body that governs the PMP credential announced it will refresh the "
                "exam content outline next year to better reflect hybrid and agile "
                "delivery methods, following years of practitioner feedback that the "
                "exam skewed toward traditional waterfall scenarios. Training providers "
                "said they expect to update materials well ahead of the changeover "
                "date.",
        "docs": (
            # v0.4 (round 2): round 1's control opened with "Exam structure" and
            # described the scenario-based format, which was close enough to "how many
            # questions" to keep getting cited (0.952 control CPR). Pivoted entirely to
            # registration/audit logistics -- no description of exam format at all.
            "Registration requirements. Candidates must submit 35 hours of project "
            "management education and relevant experience hours before scheduling, and "
            "some applications are subject to a random audit requiring extra supporting "
            "documentation. Testing appointments are available at proctored centers or "
            "via remote online proctoring, both requiring valid photo identification at "
            "check-in. Fees are non-refundable once an appointment is booked, though "
            "limited rescheduling is permitted for an additional administrative fee.",
            "Exam structure. The exam consists of 180 questions administered over 230 "
            "minutes, with a scheduled break at the halfway point. Passing requires "
            "scoring in the 'above target' or 'target' band, which corresponds to "
            "roughly 61% of scored items correct — the exact cut score is set "
            "psychometrically per exam form and not published as a fixed number. "
            "Candidates must submit 35 hours of project management education before "
            "scheduling."
        ),
        "product": "PrepMaster PMP Question Bank — 2,000+ practice questions mapped to "
                   "the current exam content outline. Full-length timed simulations. "
                   "Explanations written by certified instructors. Mobile app included "
                   "for on-the-go review. 6-month access.",
        "forum": "r/projectmanagement — Passed on my second attempt. First time I "
                 "underestimated the situational questions, they're not knowledge "
                 "recall, they're judgment calls where two answers look reasonable. "
                 "Read the question stem twice before looking at options. The 35 "
                 "contact hours requirement trips people up too, make sure your course "
                 "actually counts before you pay for it.",
        "reference": "The Project Management Professional (PMP) is a certification "
                     "administered by the Project Management Institute, intended to "
                     "validate competency in leading and directing projects. "
                     "Eligibility requires a combination of formal education, "
                     "documented project management experience, and completion of "
                     "approved training hours prior to sitting the exam.",
    }),

    # ---------------- home / DIY ----------------
    ("diy_drill", "home_diy", "How many amp-hours does this cordless drill's battery hold, and how long does it take to fully recharge?", "forum", {
        "blog": "Cordless drill shopping comes down to matching the tool to what you'll "
                "actually use it for. A light drill/driver combo covers 90% of home "
                "tasks — hanging shelves, furniture assembly, deck screws. Hammer-drill "
                "function only matters if you're regularly drilling into masonry or "
                "concrete. Torque settings prevent stripped screws in soft wood, worth "
                "checking before you buy.",
        "news": "A major power tool manufacturer recalled a line of cordless drill "
                "battery packs after reports of overheating during charging, affecting "
                "units sold over the past two years. The company is offering free "
                "replacement packs and said the issue traces to a supplier component "
                "defect, not the charger design.",
        "docs": "Battery care. Store packs at partial charge, not full or empty, if not "
                "using the tool for more than a month. Avoid charging immediately after "
                "heavy use — let the pack cool to room temperature first. Lithium-ion "
                "packs degrade fastest when left on the charger continuously after "
                "reaching full charge; remove promptly.",
        "product": "TorqueMax 20V Drill/Driver Kit — brushless motor, 2-speed gearbox, "
                   "LED work light. Includes belt clip and carrying case. Compatible "
                   "with the full 20V tool line. Sold as bare tool or with battery and "
                   "charger.",
        "forum": (
            # v0.4 (round 2): round 1's control said "battery life... turned out to be
            # a non-issue" -- a direct qualitative verdict on battery adequacy, exactly
            # what the amp-hour/recharge question asks about. Pivoted to chuck quality
            # and grip ergonomics, no comment on battery performance at all.
            "r/tools — Upgraded from a corded drill last year and don't regret it at "
            "all. Buy into a battery platform, not just a drill — once you have a "
            "couple batteries you'll end up buying every other tool in the same line "
            "because they all share the pack. Chuck quality matters more than people "
            "mention too, a cheap chuck will slip under torque and strip screw heads "
            "badly. Grip ergonomics matter a lot for longer sessions too.",
            "r/tools — Upgraded from a corded drill last year and don't regret it at "
            "all. The 4.0Ah battery runs me a full weekend of deck-board drilling on "
            "one charge, and the rapid charger tops it back up in about 45 minutes if I "
            "do run it down. Buy into a battery platform, not just a drill — once you "
            "have a couple 4.0Ah packs you'll end up buying every other tool in the "
            "same line."
        ),
        "reference": "Cordless drills are classified by voltage (typically 12V-20V for "
                     "consumer models), chuck size, and torque output measured in "
                     "inch-pounds. Brushless motors offer longer runtime and motor life "
                     "than brushed equivalents at similar voltage. Hammer-drill "
                     "variants add a percussive action for masonry applications.",
    }),

    ("diy_kit", "home_diy", "How many square feet of coverage does one box of this laminate flooring cover, and what's the recommended acclimation time before installing?", "product", {
        "blog": "Laminate has come a long way from the shiny, obviously-fake floors of "
                "a decade ago. Textured finishes and wider planks make the good stuff "
                "hard to distinguish from real wood at a glance. The tradeoff is still "
                "water resistance — even 'waterproof' laminate is really "
                "water-resistant at the seams, not a wet-room material. Fine for "
                "kitchens, risky for a bathroom.",
        "news": "A flooring retailer settled a class action over laminate products "
                "marketed as formaldehyde-compliant that independent testing found "
                "exceeded voluntary emissions guidelines. The company said it has since "
                "switched suppliers and now publishes third-party test results for its "
                "flooring lines.",
        "docs": "Subfloor preparation. Subfloor must be flat within 3/16 inch over a "
                "10-foot span; use a self-leveling compound to correct low spots before "
                "installing underlayment. Moisture testing is required on concrete "
                "subfloors — readings above 4.5 pounds per 1,000 square feet per 24 "
                "hours require a moisture barrier.",
        "product": (
            "HearthLine Laminate Flooring — oak-look finish with a textured, "
            "scratch-resistant surface. Click-lock edges for a glueless install. "
            "Suitable for kitchens and living areas with normal foot traffic, and "
            "available in five plank colors to match interior styles. Underlayment sold "
            "separately; check compatibility with radiant heat systems before purchase.",
            "HearthLine Laminate Flooring — oak-look finish with a textured, "
            "scratch-resistant surface. Each box covers 22.5 square feet across 8 "
            "planks. Acclimate unopened boxes in the install room for 48 hours before "
            "opening, longer in humid climates. Click-lock edges for a glueless "
            "install; underlayment sold separately."
        ),
        "forum": "r/HomeImprovement — Did our living room and hallway ourselves, took a "
                 "full weekend including moving furniture. The acclimation step felt "
                 "like overkill until I read about people skipping it and getting "
                 "gapping a month later. Rent a good flooring cutter instead of using a "
                 "circular saw for the whole job, saved us so much time and dust.",
        "reference": "Laminate flooring consists of a fiberboard core topped with a "
                     "printed image layer and a clear wear layer, distinguishing it "
                     "from engineered wood, which uses a real wood veneer. AC ratings "
                     "(AC1-AC5) indicate abrasion resistance and suitability for "
                     "residential versus light commercial traffic.",
    }),

    # ---------------- pets ----------------
    ("pets_insurance", "pets", "What's the typical monthly premium range for dog insurance, and what annual deductible options are usually available?", "reference", {
        "blog": "Pet insurance is one of those purchases that only feels worth it in "
                "hindsight, either because you needed it or because you're relieved you "
                "didn't. Breed matters more than most owners realize going in — large "
                "breeds and certain purebreds carry meaningfully different risk "
                "profiles for joint and genetic conditions. Read the exclusions list "
                "before the premium; that's where policies actually differ.",
        "news": "A pet insurance provider announced expanded coverage for hereditary "
                "conditions in purebred dogs following pressure from veterinary "
                "advocacy groups, reversing a long-standing industry practice of "
                "blanket exclusions for breed-predisposed illnesses. Competitors said "
                "they were reviewing similar changes.",
        "docs": "Filing a claim. Submit the itemized invoice along with medical records "
                "from the treating veterinarian within 90 days of the visit. Claims are "
                "typically processed within 5-10 business days. Reimbursement is "
                "calculated after the deductible and selected reimbursement percentage "
                "are applied to the eligible portion of the bill.",
        "product": "PawShield Complete — accident and illness coverage for dogs and "
                   "cats. No network restrictions, use any licensed vet. Optional "
                   "wellness rider covers annual exams and vaccinations. Multi-pet "
                   "discount available.",
        "forum": "r/dogs — Got insurance for my puppy specifically because of her "
                 "breed's hip issues, and I'm glad I did before anything showed up "
                 "rather than after. Read the fine print on 'bilateral exclusions' — if "
                 "one knee ever has an issue, some insurers will exclude the other knee "
                 "forever too, even years later.",
        "reference": (
            "Pet insurance is a category of indemnity insurance covering veterinary "
            "costs resulting from illness or injury. Most policies exclude pre-existing "
            "conditions and may impose waiting periods for specific conditions such as "
            "cruciate ligament injuries. Wellness coverage for routine preventive care "
            "is typically sold as a separate optional add-on rather than bundled into "
            "accident-and-illness plans by default.",
            "Pet insurance is a category of indemnity insurance covering veterinary "
            "costs resulting from illness or injury. Monthly premiums for dogs "
            "typically run $25-70 depending on breed, age and coverage level, with "
            "annual deductibles commonly offered at $100, $250 or $500. Most policies "
            "exclude pre-existing conditions and impose waiting periods for specific "
            "conditions such as cruciate ligament injuries."
        ),
    }),

    ("pets_vaccine", "pets", "How many core vaccines does a puppy need in its first year, and at what age is the final rabies booster typically given?", "news", {
        "blog": "Puppy vaccination schedules feel overwhelming the first time around, "
                "mostly because of how many vet visits are packed into a short window. "
                "Core vaccines protect against the diseases with the highest severity "
                "or transmission risk; non-core ones depend on lifestyle factors like "
                "boarding, dog parks, or regional disease prevalence. Ask your vet to "
                "walk through which category each shot falls into rather than just "
                "booking the standard package.",
        "news": (
            "A veterinary association updated its companion animal vaccination "
            "guidelines this year, emphasizing risk-based scheduling over a "
            "one-size-fits-all approach for adult dogs. The revision reflects growing "
            "evidence that some non-core vaccines were being administered more "
            "frequently than necessary, particularly in low-exposure adult dogs living "
            "in single-pet, indoor-only households with minimal outside exposure. Core "
            "vaccine recommendations for puppies remain unchanged under the new "
            "guidance.",
            "A veterinary association updated its companion animal vaccination "
            "guidelines this year. Puppies typically receive a series of 3-4 core "
            "vaccine doses between 6 and 16 weeks of age, with the final rabies booster "
            "commonly given around 12-16 weeks and then again at one year. The revision "
            "emphasizes risk-based scheduling over a one-size-fits-all approach for "
            "adult dogs, but core puppy recommendations are unchanged."
        ),
        "docs": "Vaccine record requirements. Rabies certificates must list the "
                "vaccine's lot number, manufacturer, and administering veterinarian's "
                "license number to be valid for licensing and travel purposes. Titers "
                "may substitute for revaccination in some jurisdictions but are not "
                "universally accepted; check local requirements before relying on a "
                "titer result.",
        "product": "VitaPup Wellness Plan — covers all recommended puppy vaccine visits "
                   "in the first year at a fixed monthly price. Includes one free exam "
                   "if a vaccine reaction occurs. Available through participating "
                   "veterinary clinics only.",
        "forum": "r/puppy101 — Our vet spaced ours out slightly differently than the "
                 "printed schedule because of a mild reaction after the second round, "
                 "and that's apparently pretty normal to adjust for. Don't panic if "
                 "your clinic's exact weeks look different from what you read online, "
                 "there's a reasonable range, not one fixed calendar.",
        "reference": "Core vaccines for dogs, as defined by veterinary immunization "
                     "guidelines, protect against diseases with high mortality, high "
                     "transmissibility, or public health significance: canine "
                     "parvovirus, distemper, adenovirus, and rabies. Non-core vaccines "
                     "are recommended based on individual risk assessment and "
                     "geographic prevalence.",
    }),

    # ---------------- automotive ----------------
    ("auto_evcharger", "automotive", "How many miles of range per hour of charging does a Level 2 home EV charger typically add, and what amperage circuit does it need?", "blog", {
        "blog": (
            "Installing home EV charging is one of those projects people either "
            "overthink or underthink, rarely land in the middle. Get an electrician to "
            "actually look at your panel before ordering anything — an older home's "
            "panel capacity is the thing that derails installs, not the charger itself. "
            "Placement matters too; think about where you actually park, not just where "
            "the garage outlet happens to be.",
            "Installing home EV charging is one of those projects people either "
            "overthink or underthink, rarely land in the middle. A Level 2 charger "
            "typically adds 20-30 miles of range per hour and needs a dedicated 40-50 "
            "amp circuit, usually a 240V line similar to an electric dryer's. Get an "
            "electrician to check panel capacity before ordering — an older home's "
            "panel is what derails installs, not the charger."
        ),
        "news": "A home charging equipment maker announced a recall of a wall-mounted "
                "charger model after reports of the unit overheating at the connector "
                "under sustained high current draw. The company said a firmware update "
                "addresses the issue for most affected units without requiring hardware "
                "replacement.",
        "docs": "Installation requirements. A dedicated circuit is required; the "
                "charger may not share a circuit with other loads. Outdoor "
                "installations require a NEMA 3R-rated enclosure and GFCI protection "
                "per local electrical code. Permits and inspection are typically "
                "required before the circuit can be energized for use.",
        "product": "VoltPoint Home 48A — hardwired Level 2 EV charger, WiFi-enabled "
                   "with app scheduling for off-peak charging. 24-foot cable. UL "
                   "listed. Compatible with all major EV brands via included adapter.",
        "forum": "r/electricvehicles — Went with a 240V circuit install, cost more "
                 "upfront than the 120V trickle option but the difference in daily "
                 "convenience is night and day. If you're commuting daily, the slow "
                 "120V charger genuinely can't keep up with typical driving. Get quotes "
                 "from at least two electricians, prices varied more than I expected.",
        "reference": "Electric vehicle charging is categorized into three levels: Level "
                     "1 uses a standard 120V household outlet and adds roughly 3-5 "
                     "miles of range per hour; Level 2 uses a 240V circuit; DC fast "
                     "charging bypasses the vehicle's onboard charger for rapid "
                     "charging, typically found at public stations rather than homes.",
    }),

    ("auto_dashcam", "automotive", "How many hours of continuous footage does this dashcam's memory card hold, and does it include parking-mode motion detection?", "product", {
        "blog": "Dashcams went from a niche accessory to something insurers actively "
                "recommend, mostly because footage settles disputed-fault claims fast. "
                "Front-only coverage handles the majority of use cases; rear cameras "
                "matter more if you're worried about reversing incidents or rear-end "
                "claims specifically. Mounting placement affects both video quality and "
                "whether it's legal in your state to obstruct that part of the "
                "windshield.",
        "news": "An insurance industry group published new guidance encouraging dashcam "
                "adoption after data showed footage resolved contested liability claims "
                "significantly faster than eyewitness accounts alone. Several major "
                "insurers now offer small premium discounts for verified dashcam "
                "installation.",
        "docs": "Memory card requirements. Use a card rated for continuous/endurance "
                "video recording, not a standard consumer card — repeated overwrite "
                "cycles from loop recording wear out standard cards faster and can "
                "cause file corruption. Format the card in-device monthly rather than "
                "via a computer to maintain the correct file system structure.",
        "product": (
            "RoadWitness 4K Dashcam — front and rear camera kit with wide-angle lens "
            "and night vision enhancement. Compact housing mounts discreetly behind the "
            "rearview mirror without blocking your forward line of sight. GPS logging "
            "embeds speed and location in footage. App-based playback over WiFi. "
            "Suction and adhesive mounts included.",
            "RoadWitness 4K Dashcam — front and rear camera kit with wide-angle lens "
            "and night vision enhancement. The included 128GB card holds about 14 hours "
            "of loop footage, and parking-mode motion detection auto-records for 30 "
            "seconds when it senses movement near a parked car. GPS logging embeds "
            "speed and location in footage."
        ),
        "forum": "r/dashcam — Parking mode is the feature I didn't think I needed until "
                 "someone backed into my bumper in a lot and drove off. Footage got the "
                 "plate clearly enough for a police report. Just know parking mode "
                 "drains a car battery faster than people expect if you don't have a "
                 "hardwire kit with low-voltage cutoff.",
        "reference": "Dashcams record continuous loop video while driving, overwriting "
                     "the oldest unprotected footage as storage fills. Parking mode is "
                     "a secondary feature using motion or impact detection to trigger "
                     "recording while the vehicle is off, typically requiring either a "
                     "hardwire kit or a supplementary battery pack for power.",
    }),

    # ---------------- legal ----------------
    ("legal_smallclaims", "legal", "What's the maximum dollar amount you can sue for in small claims court, and what's the typical filing fee?", "docs", {
        "blog": "Small claims court gets recommended casually as the easy option for "
                "disputes, and mostly that's fair, but the process still rewards "
                "preparation. Bring documentation organized and duplicated for the "
                "judge and the other party. Photographs, receipts, and written "
                "communication carry more weight than a verbal account of what "
                "happened. Judges see a lot of cases in a day and reward clarity.",
        "news": "A state's judicial council raised its small claims court "
                "jurisdictional limit for the first time in over a decade, citing "
                "inflation since the threshold was last set. Consumer advocacy groups "
                "welcomed the change, saying the previous limit had pushed increasingly "
                "ordinary disputes into more expensive civil court.",
        "docs": (
            "Filing procedure. Complete the claim form identifying the defendant's full "
            "legal name and a valid address for service. Cases are generally heard "
            "without attorneys representing either party, though rules on this vary by "
            "jurisdiction. A hearing date is typically scheduled within 4-8 weeks of "
            "filing, and both parties may request one continuance.",
            "Filing procedure. Complete the claim form identifying the defendant's full "
            "legal name and a valid address for service. Small claims limits commonly "
            "range from $5,000 to $10,000 depending on jurisdiction, and filing fees "
            "typically run $30-100 based on the amount claimed. A hearing date is "
            "usually scheduled within 4-8 weeks of filing."
        ),
        "product": "ClaimEasy Filing Service — prepares and files your small claims "
                   "paperwork correctly the first time. Includes a document checklist "
                   "and a call with a paralegal to review your case summary before "
                   "filing. Does not represent you at the hearing.",
        "forum": "r/legaladvice — Won my case but the harder part was actually "
                 "collecting after. Judgment doesn't mean the money shows up "
                 "automatically, you may need to file for wage garnishment or a bank "
                 "levy separately if they don't pay voluntarily. Worth knowing going in "
                 "so you're not surprised when the judgment alone doesn't produce a "
                 "check.",
        "reference": "Small claims court is a limited-jurisdiction civil court designed "
                     "to resolve disputes involving relatively modest monetary amounts "
                     "through a simplified, expedited process, typically without formal "
                     "rules of evidence and often without attorney representation for "
                     "either party.",
    }),

    ("legal_llc", "legal", "How much does it typically cost to form an LLC, and how long does state processing usually take?", "news", {
        "blog": "Forming an LLC feels like a bigger decision than the paperwork "
                "actually is. The real work is what comes after — separating business "
                "and personal finances completely, getting an EIN, and actually "
                "maintaining the formalities that protect the liability shield you "
                "formed the LLC for in the first place. Skipping those steps is how "
                "people lose the protection without realizing it.",
        "news": (
            "A state's business filing office reported a surge in new business entity "
            "registrations this year, attributing the increase to continued growth in "
            "freelance and gig-economy work, particularly among consultants and "
            "creative freelancers formalizing sole proprietorships for the very first "
            "time. Officials also noted a rise in name-availability disputes as more "
            "applicants submit similar business names within the same industry "
            "category.",
            "A state's business filing office reported a surge in new business entity "
            "registrations this year. Standard LLC filing fees in most states run "
            "$50-500 depending on jurisdiction, with standard processing taking 1-3 "
            "weeks; expedited processing for an added fee can reduce that to 24-48 "
            "hours in many states. Officials said the office has added staff to address "
            "seasonal backlogs."
        ),
        "docs": "Registered agent requirement. Every LLC must maintain a registered "
                "agent with a physical address in the state of formation, available "
                "during business hours to receive legal documents. This can be the "
                "owner, a member of the LLC, or a commercial registered agent service; "
                "a P.O. box does not satisfy the requirement.",
        "product": "QuickForm LLC Filing — we prepare and submit your articles of "
                   "organization to the state. Includes a free registered agent for the "
                   "first year and an operating agreement template. State filing fees "
                   "billed separately at cost.",
        "forum": "r/smallbusiness — Formed mine myself directly through the state site, "
                 "took maybe 20 minutes of actual form-filling. The parts that took "
                 "longer were getting the EIN from the IRS and opening a business bank "
                 "account, which needed the EIN confirmation letter first. Budget more "
                 "time for the bank step than the filing itself.",
        "reference": "A limited liability company (LLC) is a business structure "
                     "combining the liability protection of a corporation with the "
                     "pass-through taxation typically associated with partnerships or "
                     "sole proprietorships. Formation requirements and fees are set at "
                     "the state level and vary substantially by jurisdiction.",
    }),

    # ---------------- career ----------------
    ("career_negotiate", "career", "What percentage salary increase is typically realistic to negotiate on a new job offer, and how many days do candidates usually have to respond?", "forum", {
        "blog": "Salary negotiation advice tends to be either too aggressive or too "
                "timid, rarely calibrated. The strongest position is having a competing "
                "offer, but most people negotiate without one — that's fine, it just "
                "means leaning harder on market data and your specific track record. "
                "Silence after making your ask is uncomfortable but effective; don't "
                "fill it by immediately backing down.",
        "news": "A compensation analytics firm published data showing candidates who "
                "negotiated their initial offer ended up with meaningfully higher "
                "starting salaries on average than those who accepted the first number, "
                "across nearly every industry sector surveyed. The firm noted the gap "
                "was smallest in heavily unionized industries with standardized pay "
                "scales.",
        "docs": "Offer letter components. A complete offer typically includes base "
                "salary, target bonus percentage, equity grant details if applicable, "
                "benefits summary, and a start date. Verbal offers should be followed "
                "by written confirmation before a candidate resigns from a current "
                "position.",
        "product": "OfferCraft — a salary negotiation coaching service. One-on-one "
                   "session with a former recruiter to review your specific offer and "
                   "script your counter. Includes market data lookup for your role, "
                   "level, and location.",
        "forum": (
            "r/careerguidance — Negotiated my last offer and it went better than I "
            "expected, mostly because I did the research beforehand instead of just "
            "asking for more vaguely. Frame it around market data and the specific "
            "value you bring, not personal need. Companies expect it at this point, a "
            "reasonable, well-justified ask rarely costs you the offer if you're "
            "polite, specific, and flexible about which specific parts of the offer "
            "matter most to you.",
            "r/careerguidance — Negotiated my last offer and it went better than I "
            "expected. Asked for 12% over the initial number, backed by market data, "
            "and landed at about 8% after back-and-forth — which matches what I've seen "
            "cited as a realistic 5-15% range for most roles. Most companies give you "
            "3-5 business days to respond to a written offer, though you can usually "
            "ask for a short extension if you need it."
        ),
        "reference": "Salary negotiation refers to the process by which a job candidate "
                     "and employer arrive at final compensation terms following an "
                     "initial offer. Negotiable components typically extend beyond base "
                     "salary to include signing bonuses, equity, remote work terms, and "
                     "start date flexibility.",
    }),

    ("career_resume", "career", "How many pages should a resume be for someone with 10 years of experience, and how far back should work history typically go?", "reference", {
        "blog": "Resume length debates online are mostly people arguing past each other "
                "because they're picturing different career stages. What actually "
                "matters more than page count is relevance — cut anything that isn't "
                "doing work to get you this specific role. Applicant tracking systems "
                "parse text, not formatting, so overly designed resumes sometimes lose "
                "information a plain one wouldn't.",
        "news": "A recruiting software company published an analysis of resume "
                "screening times based on internal hiring platform data, finding that "
                "initial screener attention per resume had fallen year over year as "
                "application volumes rose. The firm recommended candidates front-load "
                "the most relevant information near the top of the document.",
        "docs": "Applicant tracking system parsing. Use standard section headers "
                "(Experience, Education, Skills) rather than creative labels, since "
                "parsers rely on recognized keywords to categorize content correctly. "
                "Avoid embedding key information in tables, headers, or footers, which "
                "many parsers fail to read reliably.",
        "product": "ResumeForge Pro — AI-assisted resume builder with ATS compatibility "
                   "scoring. Templates reviewed by former recruiters. Tailoring tool "
                   "suggests keyword matches against a pasted job description.",
        "forum": "r/resumes — Got roasted here for having a 3-page resume with 8 years "
                 "of experience, and honestly the feedback was right. Cut it to one "
                 "page by removing an entire early job that wasn't relevant anymore and "
                 "tightening bullet points to outcomes instead of task lists. Got more "
                 "callbacks after the trim, for whatever that's worth anecdotally.",
        "reference": (
            "A resume is a document summarizing a candidate's professional experience, "
            "education, and qualifications, formatted for review by hiring managers or "
            "applicant tracking systems. Format and content conventions vary by "
            "industry, region, and seniority level, though certain elements — contact "
            "information, a clear chronological work history, and a concise, relevant "
            "skills section — are broadly standard everywhere.",
            "A resume is a document summarizing a candidate's professional experience, "
            "education, and qualifications, formatted for review by hiring managers or "
            "applicant tracking systems. Convention holds that a resume should run one "
            "page for early-career candidates and up to two pages for those with 10+ "
            "years of experience, with detailed work history typically limited to the "
            "most recent 10-15 years."
        ),
    }),

    # ---------------- nutrition ----------------
    ("nutr_protein", "nutrition", "How many grams of protein per pound of body weight should someone lifting weights aim for daily, and does timing around workouts matter?", "blog", {
        "blog": (
            # v0.4 (round 2): round 1's control still said "isn't hitting some exact
            # number" -- a direct qualitative answer to the gram-amount question, just
            # without stating the number. Pivoted to whole-food-vs-supplement framing,
            # no discussion of amount precision at all.
            "Protein intake advice online ranges from reasonable to absurd, often "
            "depending on who's selling supplements. Whole food sources come with "
            "fiber, micronutrients, and satiety that a shake alone doesn't replicate, "
            "worth weighing before defaulting to powder for convenience. Preparation "
            "matters too — batch-cooking sources ahead of time removes the daily "
            "decision fatigue that derails a lot of good intentions.",
            "Protein intake advice online ranges from reasonable to absurd, often "
            "depending on who's selling supplements. Research generally supports around "
            "0.7-1g per pound of body weight daily for people strength training "
            "regularly. Total daily intake matters more than precise timing — the old "
            "'anabolic window' right after lifting is much wider than once believed, "
            "more like several hours than 30 minutes."
        ),
        "news": "A sports nutrition association updated its position statement on "
                "protein intake for resistance-trained individuals, citing a "
                "meta-analysis that found diminishing returns above a certain intake "
                "threshold regardless of training volume. The update also softened "
                "previous guidance emphasizing strict post-workout timing.",
        "docs": "Serving guidance. One scoop provides 24g of protein per serving. Mix "
                "with 6-8oz of cold water or milk. Do not exceed 3 servings per day "
                "without consulting a healthcare provider. Store in a cool, dry place "
                "and reseal tightly after each use to maintain freshness.",
        "product": "PureWhey Isolate — fast-absorbing whey protein isolate, low "
                   "lactose. Third-party tested for banned substances. Available in "
                   "chocolate, vanilla, and unflavored. No added sugar.",
        "forum": "r/nutrition — Tracked my protein for a few months out of curiosity "
                 "and honestly hitting the number consistently mattered way more than I "
                 "expected for recovery and just feeling less wrecked after leg day. "
                 "Didn't obsess over timing at all, just made sure the daily total "
                 "landed where I wanted by dinner.",
        "reference": "Dietary protein requirements for resistance-trained individuals "
                     "are generally cited higher than the general population's "
                     "recommended dietary allowance, reflecting increased muscle "
                     "protein synthesis demands. Protein quality, measured by amino "
                     "acid completeness and digestibility, also influences effective "
                     "intake requirements.",
    }),

    ("nutr_meal", "nutrition", "How many calories are in one serving of this meal replacement shake, and how many grams of fiber does it contain?", "docs", {
        "blog": "Meal replacement shakes get an unfair reputation as a shortcut, but "
                "for genuinely busy days they're a reasonable tool if you're honest "
                "about what they are — convenient, not magic. The ones worth buying "
                "include real fiber and a reasonable protein-to-sugar ratio; a lot of "
                "cheaper options are mostly sugar and flavoring dressed up as a meal.",
        "news": "A consumer advocacy group published test results on several popular "
                "meal replacement shake brands, finding that actual macronutrient "
                "content varied from label claims by a wider margin than regulators "
                "typically consider acceptable for several products. The manufacturers "
                "named disputed the testing methodology.",
        "docs": (
            "Preparation instructions. Shake or blend with 8-12oz of cold water, milk, "
            "or a non-dairy alternative depending on desired consistency. Best consumed "
            "within 30 minutes of mixing for optimal texture. Not intended as a sole "
            "source of nutrition for extended periods without guidance from a "
            "healthcare provider.",
            "Preparation instructions. Shake or blend with 8-12oz of cold water, milk, "
            "or a non-dairy alternative. One serving provides 400 calories and 7g of "
            "dietary fiber. Best consumed within 30 minutes of mixing. Not intended as "
            "a sole source of nutrition for extended periods without guidance from a "
            "healthcare provider."
        ),
        "product": "NutriBase Complete Shake — balanced meal replacement with added "
                   "vitamins and minerals. Vegan formula, no artificial sweeteners. 20 "
                   "single-serving packets per box. Available in three flavors.",
        "forum": "r/mealprep — Use these for breakfast on workdays only, still eat "
                 "normal meals otherwise. Works fine for that use case. Tried using it "
                 "for two meals a day for a while and just felt hungry by mid-afternoon "
                 "every time, wasn't sustainable as a bigger replacement for me "
                 "personally.",
        "reference": "Meal replacement products are formulated foods, typically in "
                     "shake or bar form, designed to substitute for a conventional meal "
                     "while providing a defined macronutrient and micronutrient "
                     "profile. Regulatory requirements for labeling and nutrient "
                     "content vary by jurisdiction and marketing claims made.",
    }),

    # ---------------- real estate ----------------
    ("re_inspection", "real_estate", "How much does a standard home inspection typically cost, and how long does the inspection itself usually take?", "forum", {
        "blog": "Home inspections get treated as a formality by some buyers in hot "
                "markets, which is a mistake even when waiving the contingency feels "
                "necessary to compete. At minimum, get an informational inspection even "
                "if you can't negotiate on it — knowing what you're buying matters "
                "regardless of whether you can back out over it. Attend in person if "
                "you possibly can.",
        "news": "A national home inspector association reported that inspection volumes "
                "rose alongside a cooling housing market, as more buyers regained "
                "negotiating leverage to request inspections that had been widely "
                "waived during the previous seller's market. Several regional "
                "associations noted longer average wait times for scheduling as a "
                "result.",
        "docs": "Report contents. A standard inspection report covers structural "
                "components, roofing, electrical systems, plumbing, HVAC, and visible "
                "signs of water intrusion or pest activity. Inspectors typically do not "
                "move furniture, test every outlet individually, or access areas deemed "
                "unsafe to enter.",
        "product": "InspectPro Booking — schedule a licensed home inspector online, "
                   "compare credentials and reviews before booking. Add-on services "
                   "(radon, sewer scope, mold) selectable at checkout. Digital report "
                   "delivered within 24 hours.",
        "forum": (
            # v0.4 (round 2): round 1's control said "worth every penny" -- a value
            # judgment implying cost is justified, adjacent to the cost question even
            # without a number. Pivoted to scheduling logistics, no comment on cost or
            # value at all.
            "r/RealEstate — Went through this last month buying our first place. The "
            "inspector walked the whole property methodically, roof to foundation, and "
            "gave us a report with photos flagging everything from minor to serious. "
            "Scheduling was genuinely tricky in a competitive market — good inspectors "
            "book up fast, so line one up the same day your offer gets accepted.",
            "r/RealEstate — Went through this last month buying our first place. Cost "
            "us $450 for a roughly 2,200 sq ft house, and the inspector was on site for "
            "about 3 hours walking the whole property methodically. Worth every penny "
            "for the peace of mind. Ask if radon and sewer scope are included or "
            "separate before booking, those added another $200 for us."
        ),
        "reference": "A home inspection is a non-invasive visual examination of a "
                     "property's condition, typically conducted by a licensed or "
                     "certified inspector during the purchase process. It is distinct "
                     "from a home appraisal, which estimates market value rather than "
                     "assessing physical condition.",
    }),

    ("re_warranty", "real_estate", "How much does a one-year home warranty plan typically cost, and what's the standard service call fee per claim?", "product", {
        "blog": "Home warranties are one of the more polarizing purchases in real "
                "estate — some buyers swear by them, others call them a waste of money "
                "that denies claims when you actually need them. The truth depends "
                "heavily on the specific provider and reading exclusions closely; "
                "pre-existing condition clauses are where most disputes happen.",
        "news": "A consumer protection agency issued a warning about aggressive home "
                "warranty sales tactics following an increase in complaints about "
                "denied claims for conditions the agency said were reasonably covered "
                "under plain policy language. The agency urged buyers to review sample "
                "contracts before purchasing rather than relying on sales calls.",
        "docs": "Claims process. Submit a claim online or by phone before scheduling "
                "any repair independently — unauthorized repairs are not eligible for "
                "reimbursement. A network contractor will be dispatched within the "
                "timeframe specified in your plan tier. Pre-existing conditions and "
                "cosmetic issues are excluded from coverage.",
        "product": (
            "HomeShield Complete — covers major home systems and appliances against "
            "mechanical failure from normal wear and tear. 24/7 claims line. Network of "
            "pre-vetted local contractors dispatched per claim, with an online "
            "dashboard to track claim status and repair history. Coverage begins 30 "
            "days after enrollment.",
            "HomeShield Complete — covers major home systems and appliances against "
            "mechanical failure from normal wear and tear. Annual plans run $500-700 "
            "depending on coverage tier, with a $75-125 service call fee due at each "
            "claim visit. 24/7 claims line, coverage begins 30 days after enrollment."
        ),
        "forum": "r/RealEstate — Seller included one as part of closing and I was "
                 "skeptical going in. Used it twice in the first year, once for a water "
                 "heater and once for the dishwasher, both approved without a fight. "
                 "Your mileage varies a lot by provider though, definitely read reviews "
                 "for the specific company, not just the concept generally.",
        "reference": "A home warranty is a service contract covering the repair or "
                     "replacement of major home systems and appliances due to normal "
                     "wear and tear, distinct from homeowners insurance, which covers "
                     "damage from specific named perils such as fire or storms rather "
                     "than mechanical breakdown.",
    }),

    # ---------------- parenting ----------------
    ("parent_carseat", "parenting", "Up to what weight or height limit can a child typically stay rear-facing in a convertible car seat, and when do experts recommend switching to forward-facing?", "reference", {
        "blog": "Car seat safety advice has shifted noticeably over the past decade "
                "toward keeping kids rear-facing much longer than previous generations "
                "did. It feels counterintuitive to parents who grew up switching "
                "earlier, but the physics case is solid — rear-facing distributes crash "
                "forces across the back and shoulders rather than the neck. Check your "
                "specific seat's printed limits rather than going by age alone.",
        "news": "A pediatric safety organization reaffirmed its rear-facing car seat "
                "guidance after a study found no increased injury risk associated with "
                "rear-facing seating past age two, countering a persistent myth that "
                "longer rear-facing use causes leg or hip discomfort severe enough to "
                "warrant an earlier switch.",
        "docs": "Installation check. After installing, grip the seat at the belt path "
                "and confirm it does not move more than one inch side to side or front "
                "to back. Recline angle must match the indicator built into the seat, "
                "which is typically stricter for younger infants to support airway "
                "positioning.",
        "product": "SafeRide Convertible Car Seat — rear- and forward-facing "
                   "convertible seat with side-impact protection. No-rethread harness "
                   "adjusts without removing the harness straps. Machine-washable "
                   "cover.",
        "forum": "r/beyondthebump — Kept ours rear-facing until almost 3.5 because she "
                 "was still under the seat's weight limit and honestly seemed just as "
                 "comfortable as forward facing. Got comments from family about it "
                 "constantly, ignored them and just checked the seat manual's actual "
                 "numbers instead of going by what felt normal.",
        "reference": (
            "Convertible car seats are designed to transition between rear-facing and "
            "forward-facing orientations as a child grows, distinguishing them from "
            "infant seats, which are rear-facing only. Installation method (using the "
            "vehicle's seatbelt or a LATCH system) and recline angle both meaningfully "
            "affect restraint effectiveness and vary noticeably by seat model and "
            "child's age.",
            "Convertible car seats are designed to transition between rear-facing and "
            "forward-facing orientations as a child grows. Most convertible seats allow "
            "rear-facing use up to 40-50 pounds or a specified height limit printed on "
            "the seat, and safety organizations generally recommend keeping children "
            "rear-facing until at least age 2, and longer where the seat's limits "
            "allow."
        ),
    }),

    ("parent_recall", "parenting", "How many strollers were affected in this recall, and what specific hazard prompted it?", "news", {
        "blog": "Stroller recalls happen more often than most new parents realize, "
                "which is less alarming than it sounds — it usually reflects an active "
                "regulatory system catching issues, not that strollers are unusually "
                "dangerous. Register every baby gear purchase with the manufacturer "
                "specifically so recall notices reach you directly rather than relying "
                "on catching a news story.",
        "news": (
            # v0.4 (round 2): round 1's control fully stated the hazard ("hinge
            # mechanism failing during use") -- the question has two parts and round 1
            # only removed the count, leaving the hazard half fully answered (1.000
            # control CPR). Removed the hazard description entirely.
            "A major stroller manufacturer issued a voluntary recall this month, its "
            "second product safety action in as many years. The company said it is "
            "coordinating with regulators on customer outreach and is offering a free "
            "repair kit shipped directly to registered owners. Retailers carrying the "
            "model have pulled remaining inventory from shelves pending the fix.",
            "A major stroller manufacturer issued a voluntary recall affecting "
            "approximately 230,000 units this month after 12 reports of the hinge "
            "mechanism unexpectedly folding during use, causing minor injuries in at "
            "least 4 cases. The company is offering a free repair kit and said it is "
            "working with regulators to notify affected customers directly."
        ),
        "docs": "Recall registration. Product registration cards or online registration "
                "allow manufacturers to contact owners directly in the event of a "
                "safety recall. Registration typically requires the model number and "
                "serial number, both usually located on a sticker on the frame near the "
                "wheel assembly.",
        "product": "TrailGlide Jogging Stroller — all-terrain three-wheel design with "
                   "locking front swivel wheel. Adjustable suspension. One-hand fold "
                   "mechanism. Compatible with most infant car seat brands via adapter.",
        "forum": "r/beyondthebump — Got the recall email for ours and honestly the "
                 "process was painless, filled out a form and the repair kit showed up "
                 "in about a week with clear instructions. Took maybe ten minutes to "
                 "install. Glad I'd actually registered it when we bought it instead of "
                 "just assuming I'd hear about issues some other way.",
        "reference": "Consumer product recalls in the juvenile products category are "
                     "typically issued voluntarily by manufacturers in coordination "
                     "with a national consumer product safety regulator, following "
                     "injury reports or internal quality findings that indicate a "
                     "defect posing a substantial risk of injury.",
    }),

    # ---------------- gaming ----------------
    ("game_pc_upgrade", "gaming", "How much of a frame-rate improvement can you typically expect from upgrading just the GPU versus a full PC rebuild, and how many watts should the power supply be rated for?", "blog", {
        "blog": (
            # v0.4 (round 2): round 1's control still said "a CPU-bound game won't
            # benefit much from a better graphics card alone" -- a direct qualitative
            # answer to "how much frame-rate improvement," just without the literal
            # words (1.000 control CPR). Pivoted to case fit and resale value, no
            # discussion of what drives performance gains at all.
            "Upgrading a gaming PC piece by piece is usually smarter than a full "
            "rebuild unless the whole system is genuinely old. Case clearance and "
            "airflow are the parts people forget to check before buying a new "
            "component — a card that's too long for your case is a returns-department "
            "problem waiting to happen. Selling the old parts individually rather than "
            "as a bundle usually recovers more of your original spend.",
            "Upgrading a gaming PC piece by piece is usually smarter than a full "
            "rebuild unless the whole system is genuinely old. A GPU-only upgrade "
            "commonly delivers 40-70% higher frame rates if the rest of the system "
            "isn't the bottleneck, versus 80-120% for a full rebuild with a new CPU and "
            "motherboard too. Size the power supply at least 150W above the new GPU's "
            "rated draw for headroom."
        ),
        "news": "A graphics card manufacturer announced its next-generation lineup will "
                "require a new power connector standard, prompting concern among "
                "builders about compatibility with existing power supplies. The company "
                "said adapter cables will ship with every card to ease the transition "
                "for the first generation of the new connector.",
        "docs": "Compatibility checklist. Confirm motherboard PCIe slot generation "
                "matches or exceeds the card's requirement for full bandwidth, though "
                "most cards remain functional at reduced bandwidth on older slots. "
                "Verify physical case clearance for card length and confirm the power "
                "supply has the required connector count before purchasing.",
        "product": "StormForge RTX Gaming GPU — ray-tracing enabled graphics card with "
                   "16GB memory. Triple-fan cooling design. Includes a case badge and "
                   "RGB lighting software. Requires an 850W or higher power supply.",
        "forum": "r/buildapc — Upgraded just the GPU last year and honestly should have "
                 "done it a year earlier instead of waiting. Made sure to check my PSU "
                 "wattage and connector type first since that trips a lot of people up "
                 "mid-build, ended up needing a new PSU anyway since mine was older and "
                 "didn't have the right connector.",
        "reference": "Frame rate, measured in frames per second (FPS), is commonly used "
                     "to evaluate gaming performance and is influenced by GPU, CPU, and "
                     "system memory in combination rather than any single component in "
                     "isolation. A bottleneck occurs when one component limits the "
                     "performance the rest of the system could otherwise achieve.",
    }),

    ("game_headset", "gaming", "How many hours of battery life does this wireless gaming headset get on a single charge, and what's the wireless range?", "product", {
        "blog": "Wireless gaming headsets have closed most of the latency gap with "
                "wired options that used to make competitive players avoid them "
                "entirely. Comfort for long sessions matters more than most spec sheets "
                "suggest — clamping force and ear cup material make a bigger difference "
                "to a four-hour session than driver size on paper. Try before buying if "
                "you possibly can.",
        "news": "An audio equipment manufacturer settled a dispute over battery life "
                "claims after independent testing found several headset models fell "
                "meaningfully short of advertised runtime under typical gaming use with "
                "RGB lighting enabled. The company updated its marketing to specify "
                "test conditions more clearly going forward.",
        "docs": "Firmware updates. Connect the headset via USB cable and the companion "
                "app to check for firmware updates, which may improve battery reporting "
                "accuracy and fix connection drops. Do not disconnect the headset "
                "during an update, as this can corrupt the firmware and require a "
                "factory reset.",
        "product": (
            "SonicWave Wireless Gaming Headset — 50mm drivers with a detachable "
            "noise-cancelling microphone. Compatible with PC, console, and mobile via "
            "included USB dongle. Memory foam ear cushions with a breathable fabric "
            "layer for extended comfort. On-ear volume and mute controls.",
            "SonicWave Wireless Gaming Headset — 50mm drivers with a detachable "
            "noise-cancelling microphone. Rated for 30 hours of battery life per charge "
            "and a 40-foot wireless range via the included USB dongle. Compatible with "
            "PC, console, and mobile. Memory foam ear cushions."
        ),
        "forum": "r/pcmasterrace — Been using mine daily for about 8 months now. "
                 "Battery life claims from manufacturers are always a little optimistic "
                 "in my experience, with RGB on I get noticeably less than the box "
                 "says, closer to two-thirds of the advertised number. Still solid "
                 "overall, just don't take the marketing number as gospel.",
        "reference": "Wireless gaming headsets typically use either Bluetooth or a "
                     "proprietary 2.4GHz RF connection via USB dongle, with the latter "
                     "generally preferred for gaming due to lower audio latency. Range "
                     "and interference resistance vary by connection type and "
                     "environmental factors such as walls and other wireless devices.",
    }),

    # ---------------- taxes ----------------
    ("tax_freelance", "taxes", "What percentage of income should freelancers typically set aside for self-employment tax, and when are quarterly estimated payments due?", "docs", {
        "blog": "Freelance taxes intimidate people mostly because nothing is withheld "
                "automatically the way a paycheck handles it. The fix isn't complicated "
                "though — open a separate savings account, move a percentage of every "
                "payment into it the day it arrives, and treat that money as already "
                "spent. The quarterly deadlines matter less if you're already setting "
                "money aside consistently.",
        "news": "A tax preparation trade group reported that penalty notices for "
                "underpaid estimated taxes rose among self-employed filers this year, "
                "attributing the increase to income volatility making quarterly income "
                "harder to project accurately. The group renewed calls for simplified "
                "safe-harbor rules for new freelancers.",
        "docs": (
            # v0.4 (round 2): round 1's control opened with "must make quarterly
            # estimated payments," restating the question's core subject as a near-exact
            # phrase even without a percentage or date (0.994 control CPR). Retitled and
            # pivoted entirely to recordkeeping, no mention of estimated payments at all.
            "Recordkeeping overview. Self-employed individuals should retain receipts "
            "and invoices for at least three years in case of an audit, organized by "
            "category rather than by date alone. Keeping separate records for business "
            "and personal expenses throughout the year makes the eventual filing far "
            "less painful, and a dedicated business bank account is the easiest way to "
            "enforce that separation automatically.",
            "Estimated tax overview. Self-employed individuals generally must make "
            "quarterly estimated payments if they expect to owe a minimum threshold "
            "amount in tax for the year. A common rule of thumb is setting aside 25-30% "
            "of net income for self-employment and income tax combined. Quarterly "
            "payments are typically due in mid-April, June, September, and January of "
            "the following year."
        ),
        "product": "LedgerFlow Freelance Tax Tracker — automatically categorizes income "
                   "and expenses from linked accounts and estimates your quarterly tax "
                   "liability. Sends reminders before each due date. Exports a summary "
                   "for your accountant.",
        "forum": "r/freelance — First year I didn't set anything aside and the tax bill "
                 "in April was genuinely painful to deal with all at once. Now I move a "
                 "chunk to a separate account the moment a payment clears, out of sight "
                 "out of mind, and quarterly payments stopped feeling stressful once "
                 "the money was already sitting there waiting.",
        "reference": "Self-employment tax refers to the combined Social Security and "
                     "Medicare tax obligation for individuals who work for themselves, "
                     "functionally replacing the payroll tax that would otherwise be "
                     "split between an employer and employee under traditional "
                     "employment.",
    }),

    ("tax_deadline", "taxes", "What's the penalty percentage for filing a tax return late if you owe money, and is there a difference if you filed an extension?", "news", {
        "blog": "The distinction between filing late and paying late trips people up "
                "every year, and it's worth understanding because the penalties are "
                "wildly different in severity. Filing an extension is free and takes "
                "minutes; it buys you time to file correctly without the harsher "
                "penalty, even though it doesn't extend the time you have to actually "
                "pay what you owe.",
        "news": (
            "The national tax authority reminded filers of upcoming deadlines this "
            "week, noting call center wait times typically peak in the final days "
            "before the filing deadline. The agency encouraged taxpayers who cannot "
            "file on time to request an extension electronically well ahead of the "
            "deadline, rather than waiting until the final days when processing delays "
            "are most likely to cause a submission to fail.",
            "The national tax authority reminded filers of upcoming deadlines this "
            "week. Filing late without an extension carries a failure-to-file penalty "
            "of 5% of unpaid tax per month, up to 25%, notably steeper than the "
            "failure-to-pay penalty of 0.5% per month for those who filed an extension "
            "but still owe money. The agency encouraged taxpayers to request an "
            "extension electronically rather than miss the deadline outright."
        ),
        "docs": "Extension requirements. Filing an extension grants additional time to "
                "submit the return itself but does not extend the deadline to pay any "
                "tax owed. An estimated payment should accompany the extension request "
                "to minimize interest and failure-to-pay penalties that continue to "
                "accrue on any unpaid balance.",
        "product": "FileFast Extension Service — submit your tax extension request "
                   "online in under 10 minutes. Includes an estimated payment "
                   "calculator to help you avoid underpayment penalties. Confirmation "
                   "delivered immediately upon acceptance.",
        "forum": "r/tax — Filed an extension for the first time last year because I was "
                 "missing a form, and it was way less stressful than I expected once I "
                 "understood I still needed to pay an estimate by the original "
                 "deadline. The extension is just for the paperwork, not the money, "
                 "which wasn't obvious to me going in.",
        "reference": "Tax filing penalties in most jurisdictions distinguish between "
                     "failure to file a return and failure to pay tax owed, with the "
                     "former typically penalized more severely on a percentage basis to "
                     "discourage non-filing specifically, independent of a taxpayer's "
                     "ability to pay the underlying liability.",
    }),

    # ---------------- fitness ----------------
    ("fit_homegym", "fitness", "How much does a basic home gym setup with adjustable dumbbells and a bench typically cost, and how much floor space does it usually need?", "forum", {
        "blog": "Home gyms went mainstream for good reason — no commute, no waiting for "
                "equipment, workout whenever the window opens. The mistake most people "
                "make is over-buying equipment upfront based on aspiration rather than "
                "what a realistic routine actually needs. Adjustable dumbbells solve "
                "the space problem better than a full rack of fixed weights for most "
                "home setups.",
        "news": "A fitness equipment retailer reported continued growth in home gym "
                "equipment sales even as commercial gym membership numbers recovered to "
                "pre-pandemic levels, suggesting the shift toward hybrid workout habits "
                "has proven durable rather than temporary. The company said compact, "
                "space-efficient equipment drove the strongest sales growth.",
        "docs": "Assembly and safety. Ensure the bench is locked in the selected "
                "incline position before use; an unlocked adjustment mechanism is a "
                "common cause of injury. Check weight plate collars are fully tightened "
                "before each session, and inspect cables or adjustment pins "
                "periodically for wear.",
        "product": "FlexRange Adjustable Dumbbell Set — adjusts from 5 to 50 pounds per "
                   "dumbbell via a dial mechanism, replacing up to 15 pairs of fixed "
                   "dumbbells. Compact tray storage included.",
        "forum": (
            "r/homegym — Built mine out slowly over about a year instead of all at "
            "once, and I'd recommend that approach over buying everything upfront. "
            "Figure out what you'll actually use consistently before spending on the "
            "fancier stuff. Flooring matters more than people expect too, protects both "
            "the actual floor and the equipment from getting damaged.",
            "r/homegym — Built mine out slowly over about a year instead of all at "
            "once. Adjustable dumbbells plus a decent adjustable bench ran me around "
            "$600 total, and the whole setup fits in roughly a 6x8 foot area including "
            "room to actually move. Flooring matters more than people expect too, "
            "protects both the floor and the equipment."
        ),
        "reference": "Adjustable dumbbells use a mechanical selection system, typically "
                     "a dial or pin, to vary resistance within a single unit, "
                     "distinguishing them from fixed-weight dumbbells that require a "
                     "full rack of individual pairs to cover an equivalent weight "
                     "range.",
    }),

    ("fit_hrzones", "fitness", "What percentage of maximum heart rate defines 'zone 2' cardio training, and how many minutes per week is typically recommended at that intensity?", "reference", {
        "blog": "Zone 2 training went from a niche endurance-athlete concept to "
                "something everyone on fitness social media talks about, which has "
                "muddied the advice somewhat. The core idea holds up though — genuinely "
                "easy, conversational-pace cardio builds aerobic base in a way that "
                "high-intensity work doesn't replace. Most people run their 'easy' days "
                "too hard to actually be in zone 2.",
        "news": "A sports science journal published a review examining zone 2 "
                "training's rise in popularity among recreational athletes, noting that "
                "much of the underlying research originated from elite endurance sport "
                "contexts and cautioning that optimal application for casual exercisers "
                "remains less well studied.",
        "docs": "Heart rate monitor calibration. Chest strap monitors generally provide "
                "more accurate real-time readings than wrist-based optical sensors, "
                "particularly during high-intensity intervals where motion artifacts "
                "affect optical accuracy. Calibrate against a known resting heart rate "
                "measurement periodically to check for drift.",
        "product": "PulseTrack Chest Strap — Bluetooth and ANT+ compatible heart rate "
                   "monitor. Syncs with most major fitness apps and platforms. "
                   "Water-resistant. Battery rated for approximately 12 months of "
                   "typical use.",
        "forum": "r/running — Started actually tracking zone 2 properly instead of "
                 "guessing and was humbled by how slow my real zone 2 pace is compared "
                 "to what I thought was 'easy.' Took real discipline to slow down that "
                 "much on easy days instead of creeping into a harder effort out of "
                 "habit.",
        "reference": (
            "Heart rate training zones divide exercise intensity into ranges based on "
            "percentage of maximum heart rate or heart rate reserve, used to guide "
            "training toward specific physiological adaptations. Maximum heart rate is "
            "commonly estimated using an age-based formula, though individual variation "
            "from the estimate can be substantial, which is why many coaches recommend "
            "a supervised field test for a more accurate personal baseline.",
            "Heart rate training zones divide exercise intensity into ranges based on "
            "percentage of maximum heart rate. Zone 2 is generally defined as 60-70% of "
            "maximum heart rate, and endurance-focused training guidance commonly "
            "recommends accumulating 150-180 minutes per week at that intensity to "
            "build aerobic base. Maximum heart rate is commonly estimated using an "
            "age-based formula, though individual variation can be substantial."
        ),
    }),

    # ---------------- photography ----------------
    ("photo_lens", "photography", "What aperture range does this 50mm prime lens offer, and how close can it focus to a subject?", "blog", {
        "blog": (
            "A 50mm prime is the classic first lens recommendation for a reason — it "
            "forces you to move your feet instead of zooming, which genuinely improves "
            "your composition habits faster than a zoom lens does early on. Image "
            "quality per dollar is usually excellent compared to a kit zoom too. Not "
            "ideal for tight indoor spaces where you can't physically back up enough.",
            "A 50mm prime is the classic first lens recommendation for a reason — it "
            "forces you to move your feet instead of zooming. Most affordable versions "
            "offer an aperture range of f/1.8 to f/16 and a minimum focus distance "
            "around 1.5 feet, close enough for reasonably tight portraits but not true "
            "macro work. Not ideal for tight indoor spaces where you can't physically "
            "back up enough."
        ),
        "news": "A camera lens manufacturer announced a redesigned version of its "
                "popular 50mm prime lens featuring improved autofocus motor speed and "
                "updated coatings to reduce flare, aimed at addressing a common "
                "complaint from the previous generation. Pricing was set slightly above "
                "the outgoing model.",
        "docs": "Mount compatibility. Confirm the lens mount matches your camera body "
                "generation, as some manufacturers have changed mount standards across "
                "mirrorless and DSLR lines. Adapters exist for cross-mount "
                "compatibility but may disable autofocus or reduce its speed depending "
                "on the specific combination.",
        "product": "Prime50 f/1.8 Lens — lightweight full-frame prime lens with a quiet "
                   "stepping autofocus motor. Weather-sealed mount. Includes a lens "
                   "hood and soft case.",
        "forum": "r/photography — Recommend this focal length to literally everyone "
                 "starting out. Cheap, sharp, and the wide aperture teaches you to "
                 "think about depth of field in a way kit zooms don't really encourage "
                 "since they're usually slower. Only downside is the fixed focal length "
                 "takes some adjustment if you're used to just zooming to frame a shot.",
        "reference": "A prime lens has a fixed focal length, as distinguished from a "
                     "zoom lens, which offers a variable focal length range. Prime "
                     "lenses generally offer wider maximum apertures, better image "
                     "quality, and lighter weight compared to zoom lenses at an "
                     "equivalent price point, at the cost of framing flexibility.",
    }),

    ("photo_raw", "photography", "How much more storage space does a RAW photo file typically take compared to a compressed JPEG, and what dynamic range advantage does shooting RAW give you?", "docs", {
        "blog": "The RAW versus JPEG debate mostly comes down to whether you plan to "
                "edit seriously or not. If you're shooting for immediate sharing with "
                "minimal adjustment, JPEG's smaller files and faster workflow make "
                "sense. If you're editing in earnest, RAW's flexibility for recovering "
                "blown highlights or crushed shadows is hard to give up once you're "
                "used to having it.",
        "news": "A camera manufacturer released a firmware update adding a compressed "
                "RAW format option to several camera models, aimed at buyers who wanted "
                "RAW's editing flexibility without the full storage burden of "
                "uncompressed files. Early reviews noted only minor quality differences "
                "from standard RAW in most shooting conditions.",
        "docs": (
            # v0.4 (round 2): round 1's control still made comparative claims on both
            # asked dimensions (JPEG "smaller," RAW "extensive post-processing") without
            # numbers -- structurally the same failure as nutr_protein's "isn't hitting
            # some exact number." Pivoted to software/workflow compatibility, no size or
            # dynamic-range comparison at all.
            "File format overview. RAW files require compatible editing software to "
            "open and process, while JPEG files display natively in nearly any image "
            "viewer or browser without conversion. RAW files use a proprietary format "
            "specific to the camera manufacturer, occasionally requiring a software "
            "update after a new camera model release. JPEG remains the universal "
            "standard for sharing.",
            "File format overview. RAW files retain unprocessed sensor data and "
            "typically run 20-40MB per image, roughly 5-10 times larger than a "
            "same-resolution JPEG. Shooting RAW generally preserves 1-2 additional "
            "stops of recoverable dynamic range in highlights and shadows compared to "
            "an in-camera JPEG. JPEG files apply in-camera processing and compression, "
            "producing a smaller, ready-to-share file."
        ),
        "product": "PixelVault 2TB Portable SSD — rugged, drop-resistant external drive "
                   "built for field photography backup. USB-C connection with fast "
                   "transfer speeds for large RAW file batches. Includes backup "
                   "software license.",
        "forum": "r/photography — Switched to RAW exclusively a few years ago and don't "
                 "regret it despite the storage headache. Buy more storage than you "
                 "think you need, RAW files add up fast if you shoot in bursts. The "
                 "editing flexibility saved several shots I would have written off as "
                 "ruined if I'd only had the JPEG.",
        "reference": "RAW image formats store minimally processed data directly from a "
                     "digital camera's image sensor, in contrast to JPEG, a "
                     "standardized compressed format that applies lossy compression and "
                     "in-camera color and tone processing before saving.",
    }),

    # ---------------- gardening ----------------
    ("garden_raisedbed", "gardening", "How many bags of soil does it typically take to fill a standard 4x8 foot raised garden bed, and how deep should the bed be for most vegetables?", "forum", {
        "blog": "Raised beds solve a lot of problems that in-ground gardening creates, "
                "especially for anyone dealing with poor native soil or drainage "
                "issues. The upfront cost and labor put some people off, but the "
                "control over soil quality pays off across multiple growing seasons. "
                "Cedar and untreated pine are the common material choices, cedar lasts "
                "longer but costs meaningfully more.",
        "news": "A gardening supply retailer reported a sustained increase in raised "
                "bed kit sales over the past several seasons, attributing the trend "
                "partly to smaller urban yards where controlling soil quality in a "
                "defined space is more practical than amending existing ground soil.",
        "docs": "Assembly instructions. Level the ground before placing the frame; use "
                "landscape fabric beneath the bed to suppress weeds while allowing "
                "drainage. Corner brackets should be fully tightened before filling "
                "with soil, as the weight of wet soil places significant outward "
                "pressure on the frame joints.",
        "product": "GrowFrame Cedar Raised Bed Kit — 4x8 foot modular cedar frame, "
                   "tool-free corner bracket assembly. Naturally rot-resistant "
                   "untreated cedar. Expandable with additional connector kits sold "
                   "separately.",
        "forum": (
            "r/gardening — Built our first raised bed this spring and it's been one of "
            "the better projects we've done around the yard. Soil quality matters more "
            "than people expect going in — don't just grab whatever bagged soil is "
            "cheapest, a proper raised bed mix makes a real difference in how things "
            "grow. Sun exposure planning before you build matters more than the bed "
            "itself honestly.",
            "r/gardening — Built our first raised bed this spring and it's been one of "
            "the better projects we've done around the yard. Took about 20 bags of "
            "raised bed mix to fill our 4x8 bed at a 12-inch depth, which is plenty for "
            "most root vegetables and everything else we planted. Sun exposure planning "
            "before you build matters more than the bed itself honestly."
        ),
        "reference": "Raised bed gardening involves growing plants in soil contained "
                     "within a frame elevated above the surrounding ground level, "
                     "offering improved drainage, soil quality control, and reduced "
                     "soil compaction compared to traditional in-ground planting.",
    }),

    ("garden_composter", "gardening", "How many gallons does this compost tumbler hold, and how many weeks does it typically take to produce finished compost?", "product", {
        "blog": "Composting intimidates people more than it should — the tumbler-style "
                "bins especially remove most of the guesswork compared to an open pile. "
                "Balancing 'greens' and 'browns' matters more than turning frequency "
                "for how fast things actually break down. A pile that's too wet and "
                "smelly usually needs more dry browns, not less turning.",
        "news": "A municipal waste department expanded its subsidized compost bin "
                "program this year after data showed participating households diverted "
                "a meaningful share of food waste from landfill collection. Officials "
                "said tumbler-style bins saw higher sustained usage than open bin "
                "designs distributed in prior program years.",
        "docs": "Maintenance guidance. Turn the tumbler every 2-3 days to aerate "
                "contents and speed decomposition. Maintain a moisture level similar to "
                "a wrung-out sponge; add dry browns like shredded cardboard if contents "
                "become slimy or odorous, or add water if the pile appears dry and "
                "decomposition has stalled.",
        "product": (
            "DualBin Compost Tumbler — twin-chamber rotating design allows continuous "
            "composting while one side finishes. Elevated stand keeps pests out and "
            "eases turning without bending or kneeling at ground level. UV-resistant "
            "recycled plastic construction rated for years of outdoor exposure. "
            "Ventilation slots for airflow.",
            "DualBin Compost Tumbler — twin-chamber rotating design, each chamber holds "
            "27 gallons, allowing continuous composting while one side finishes. Under "
            "ideal conditions, finished compost is ready in as little as 4-6 weeks per "
            "batch. Elevated stand keeps pests out and eases turning."
        ),
        "forum": "r/composting — Upgraded from an open pile to a tumbler and the "
                 "difference in smell and pest issues alone was worth it. Finished "
                 "compost took a bit longer than the box suggested in my experience, "
                 "more like two months in cooler weather, but still way faster than the "
                 "open pile ever managed.",
        "reference": "Composting is the aerobic decomposition of organic material into "
                     "a stable, nutrient-rich soil amendment, requiring a balance of "
                     "carbon-rich ('brown') and nitrogen-rich ('green') material, "
                     "adequate moisture, and oxygen introduced through periodic turning "
                     "or passive aeration.",
    }),

    # ---------------- consumer cybersecurity ----------------
    ("sec_vpn", "cybersecurity_consumer", "How many simultaneous device connections does a typical consumer VPN subscription include, and does using one usually reduce internet speed noticeably?", "reference", {
        "blog": "VPN marketing tends to overpromise on both privacy and performance, "
                "which makes it hard to evaluate providers on the merits. The realistic "
                "case for a consumer VPN is protecting traffic on untrusted networks "
                "like public WiFi and some geographic content access, not becoming "
                "untraceable online generally — that's a much bigger, harder problem "
                "than a VPN alone solves.",
        "news": "A digital rights organization published an audit of consumer VPN "
                "providers' no-logs claims, finding that several providers had "
                "undergone independent third-party audits to verify their policies "
                "while others relied solely on self-reported claims without external "
                "verification. The group called for standardized audit requirements "
                "across the industry.",
        "docs": "Setup and configuration. Enable the kill switch feature to block "
                "internet traffic automatically if the VPN connection drops "
                "unexpectedly, preventing unprotected data from being sent. Split "
                "tunneling allows specific apps to bypass the VPN tunnel if "
                "compatibility issues arise with certain services.",
        "product": "ShieldLine VPN — no-logs policy verified by independent third-party "
                   "audit. Servers in 60+ countries. Kill switch and split tunneling "
                   "included on all plans. Works across desktop, mobile, and "
                   "router-level installation.",
        "forum": "r/privacy — Been using one for a couple years mainly for public WiFi "
                 "at coffee shops and airports. Speed hit is noticeable on video calls "
                 "sometimes but fine for browsing and most everyday stuff. Don't expect "
                 "it to fix your privacy problems generally, it's one layer, not a "
                 "complete solution by itself.",
        "reference": (
            # v0.4 (round 2): round 1's control said "affect... practical browsing
            # performance" -- directly on the speed-reduction question, just without a
            # number. Pivoted to jurisdiction/business-model framing, no comment on
            # connection count or speed impact at all.
            "A consumer virtual private network (VPN) routes internet traffic through "
            "an encrypted tunnel to a server operated by the VPN provider, masking the "
            "user's IP address from destination websites. Providers are typically "
            "incorporated in a specific jurisdiction, which determines what "
            "data-retention laws and government requests they're subject to. Free "
            "services commonly monetize through advertising or data partnerships "
            "instead of subscription fees.",
            "A consumer virtual private network (VPN) routes internet traffic through "
            "an encrypted tunnel to a server operated by the VPN provider. Most "
            "consumer plans include 5-10 simultaneous device connections per "
            "subscription, and typical speed reduction ranges from 10-25% versus an "
            "unprotected connection, depending on server load and distance. Provider "
            "logging policies and jurisdiction also affect practical privacy "
            "guarantees."
        ),
    }),

    ("sec_breach", "cybersecurity_consumer", "How many customer accounts were affected in this data breach, and what type of information was exposed?", "news", {
        "blog": "Breach notifications have become routine enough that people scroll "
                "past them, which is understandable but risky given how password reuse "
                "compounds the damage from any single breach. The practical response is "
                "always the same regardless of the specific breach details — change the "
                "password, enable two-factor authentication if you haven't, and check "
                "whether you reused that password anywhere else.",
        "news": (
            "A widely used online retailer disclosed a data security incident this "
            "week, saying it detected unauthorized access to a portion of its internal "
            "customer database and has engaged a third-party forensics firm to "
            "investigate. The company said it has notified law enforcement and is "
            "offering affected customers a complimentary monitoring service.",
            "A widely used online retailer disclosed a data security incident affecting "
            "approximately 2.3 million customer accounts this week, saying names, email "
            "addresses, and hashed passwords were exposed, though payment card data was "
            "stored separately and not affected. The company has engaged a third-party "
            "forensics firm and is offering affected customers a complimentary "
            "monitoring service."
        ),
        "docs": "Incident response disclosure requirements. Organizations are generally "
                "required to notify affected individuals within a specified window "
                "after discovering a breach involving personal data, with exact "
                "timelines and notification content requirements varying by "
                "jurisdiction and the type of data involved.",
        "product": "IdentityWatch Monitoring — monitors your email and personal "
                   "information against known data breach databases and dark web "
                   "marketplaces. Real-time alerts when new exposure is detected. "
                   "Includes identity theft insurance coverage.",
        "forum": "r/cybersecurity — Got the notification email for this one, changed "
                 "the password immediately and was relieved I hadn't reused it anywhere "
                 "else since I've been using a password manager for a couple years now. "
                 "This is exactly the scenario that convinced me to finally set one up "
                 "after putting it off for ages.",
        "reference": "A data breach is an incident in which sensitive, protected, or "
                     "confidential information is accessed, disclosed, or stolen "
                     "without authorization. Breach severity is commonly assessed by "
                     "the number of records affected and the sensitivity of the "
                     "specific data types exposed, such as financial or health "
                     "information versus contact details alone.",
    }),

    # ---------------- cooking ----------------
    ("cook_airfryer", "cooking", "How many quarts of capacity does this air fryer have, and what wattage does it draw?", "blog", {
        "blog": (
            "Air fryers earned the hype for a reason, but the size decision trips "
            "people up more than any other spec. Basket-style and oven-style designs "
            "cook noticeably differently despite similar marketing — oven-style models "
            "often preheat faster and allow multiple racks at once. Non-stick coating "
            "durability varies a lot between brands too, worth checking reviews "
            "specifically for that before buying.",
            "Air fryers earned the hype for a reason, but the size decision trips "
            "people up more than any other spec. This one holds 6 quarts and draws 1700 "
            "watts, enough capacity for a family meal and enough power to crisp food "
            "quickly rather than just drying it out. Basket-style and oven-style "
            "designs cook noticeably differently despite similar marketing."
        ),
        "news": "A kitchen appliance recall was issued for a batch of air fryers after "
                "reports of the heating element overheating under certain conditions, "
                "prompting several small fires. The manufacturer said the issue traces "
                "to a specific production run and is offering free replacement units to "
                "affected customers.",
        "docs": "Cleaning and maintenance. The basket and tray are dishwasher safe on "
                "the top rack; hand washing is recommended to preserve the non-stick "
                "coating longer. Do not use metal utensils or abrasive scouring pads on "
                "the basket, as this can damage the coating and affect cooking "
                "performance over time.",
        "product": "CrispAir 6-Quart Digital Air Fryer — 8 preset cooking functions, "
                   "digital touchscreen display. Dishwasher-safe non-stick basket. "
                   "Automatic shutoff and cool-touch handle.",
        "forum": "r/AirFryers — Upgraded from a small 3-quart to a bigger one and it's "
                 "genuinely changed how often I use it, went from occasional to almost "
                 "daily. The bigger basket means actual meals instead of just reheating "
                 "leftovers in small batches. Wish I'd sized up from the start instead "
                 "of buying small the first time.",
        "reference": "Air fryers cook food using rapid air circulation around a heating "
                     "element, producing a browned, crisped exterior similar to deep "
                     "frying while using substantially less oil. Capacity is typically "
                     "measured in quarts, and cooking performance is influenced by both "
                     "basket size and heating element wattage.",
    }),

    ("cook_knife", "cooking", "What's the blade length on this chef's knife, and what type of steel is it made from?", "product", {
        "blog": "A good chef's knife is the one purchase in a kitchen that actually "
                "justifies spending more, since it's the tool you'll use for nearly "
                "everything. Weight and balance matter more than most people expect "
                "when trying one in a store — a knife that feels heavy in five seconds "
                "will feel exhausting after twenty minutes of prep work. Hand feel "
                "beats spec sheets here.",
        "news": "A cutlery manufacturer announced it is opening its first "
                "direct-to-consumer sharpening service, allowing customers to mail in "
                "knives for professional resharpening rather than relying on home "
                "sharpening tools, following customer feedback that maintaining a "
                "proper edge was the biggest barrier to enjoying higher-end knives.",
        "docs": "Care instructions. Hand wash immediately after use and dry completely "
                "before storing to prevent staining and corrosion, even on stainless "
                "steel blades. Store in a knife block or on a magnetic strip rather "
                "than loose in a drawer, where the edge can be damaged by contact with "
                "other utensils.",
        "product": (
            "Hearthstone Chef's Knife — full-tang forged construction with a "
            "comfortable, balanced handle designed for extended prep sessions without "
            "hand or wrist fatigue. Hand-sharpened edge. Includes a protective blade "
            "guard. Dishwasher use not recommended.",
            "Hearthstone Chef's Knife — full-tang forged construction with an 8-inch "
            "high-carbon stainless steel blade, hand-sharpened to a 15-degree edge per "
            "side. Balanced handle for extended use. Includes a protective blade guard. "
            "Dishwasher use not recommended."
        ),
        "forum": "r/Cooking — Splurged on a proper chef's knife after years of cheap "
                 "ones and the difference in prep speed alone justified it within a "
                 "month. Learning to hand-sharpen took some practice and a few YouTube "
                 "videos, but keeping a real edge on it made a bigger difference to "
                 "daily cooking than I expected going in.",
        "reference": "Chef's knife steel is commonly categorized as either carbon "
                     "steel, which takes a sharper edge but requires more maintenance "
                     "to prevent rust, or stainless steel, which resists corrosion "
                     "better at some cost to edge retention and sharpening ease. "
                     "High-carbon stainless steel blends attempt to balance both "
                     "properties.",
    }),

    # ---------------- student loans ----------------
    ("loan_forgiveness", "student_loans", "How many years of qualifying payments are typically required for income-driven repayment forgiveness, and does the forgiven balance count as taxable income?", "docs", {
        "blog": "Income-driven repayment plans get discussed online as though the rules "
                "are fixed and simple, when in practice the details have shifted "
                "meaningfully over the past several years, including which payments "
                "count toward forgiveness and how forgiven amounts are taxed. Anyone "
                "pursuing forgiveness should verify current rules directly with their "
                "loan servicer rather than relying on older articles.",
        "news": "A federal loan servicer reported processing delays affecting borrowers "
                "seeking income-driven repayment forgiveness after a surge in "
                "applications following a policy clarification. The agency overseeing "
                "federal student loans said it is adding processing staff to address "
                "the backlog.",
        "docs": (
            "Income-driven repayment overview. Monthly payment amounts are recalculated "
            "annually based on updated income and family size documentation, which must "
            "be resubmitted each year through the loan servicer's online portal to "
            "remain fully enrolled without interruption. Failing to recertify on time "
            "can result in reversion to a standard repayment plan with a higher "
            "payment.",
            "Income-driven repayment overview. Most income-driven plans forgive the "
            "remaining balance after 20-25 years of qualifying payments, depending on "
            "the specific plan and loan type. Under current federal law, forgiven "
            "balances are not taxed as income through 2025, though this treatment has "
            "changed by legislation before and borrowers should confirm current rules. "
            "Monthly payments are recalculated annually."
        ),
        "product": "LoanClarity Repayment Planner — compares income-driven repayment "
                   "plans side by side based on your income, family size, and loan "
                   "balance. Projects total payments and estimated forgiveness timeline "
                   "under each plan option.",
        "forum": "r/StudentLoans — Been on an income-driven plan for six years now and "
                 "the recertification step catches people off guard every single year, "
                 "missed mine once and my payment jumped substantially until I got it "
                 "sorted out. Set a calendar reminder well before the deadline, don't "
                 "rely on the servicer's email reminder alone.",
        "reference": "Income-driven repayment plans calculate a borrower's monthly "
                     "federal student loan payment as a percentage of discretionary "
                     "income rather than the loan balance, with several plan variants "
                     "differing in the percentage used, repayment term length, and "
                     "eligibility criteria.",
    }),

    ("loan_rate", "student_loans", "What's the current fixed interest rate on new federal undergraduate student loans, and how much can a dependent undergraduate typically borrow per year?", "news", {
        "blog": "Federal student loan rates reset annually and catch a lot of families "
                "off guard because the number changes from the year before, sometimes "
                "significantly. The rate that matters is the one in effect when the "
                "loan is first disbursed, not when you applied or when you eventually "
                "start repaying — worth confirming that timing explicitly before "
                "assuming a specific rate applies.",
        "news": (
            "The federal government announced updated student loan interest rates for "
            "the upcoming academic year, following the annual formula tied to the "
            "results of the most recent 10-year Treasury note auction held earlier in "
            "the spring session. The rate adjustment applies only to loans first "
            "disbursed after July 1 and does not affect loans already disbursed under "
            "previous years' terms.",
            "The federal government announced updated student loan interest rates for "
            "the upcoming academic year: 5.5% fixed for new undergraduate loans, "
            "applying to loans first disbursed after July 1. Dependent undergraduates "
            "can typically borrow up to $5,500-$7,500 per year depending on class "
            "standing, subject to overall aggregate loan limits. The rate does not "
            "affect loans already disbursed under previous years' terms."
        ),
        "docs": "Borrowing limits. Annual and aggregate loan limits are set by loan "
                "type, dependency status, and year in school, with dependent "
                "undergraduates generally subject to lower limits than independent "
                "students. Limits are set by federal statute and apply uniformly "
                "regardless of the borrower's chosen school or program cost.",
        "product": "CampusFund 529 Planner — projects college savings growth and "
                   "compares against projected loan borrowing needs based on your "
                   "target school's cost of attendance. Includes state tax benefit "
                   "calculator for 529 contributions.",
        "forum": "r/StudentLoans — Rates jumped noticeably between my freshman and "
                 "sophomore year and nobody warned me that could happen, assumed it was "
                 "locked in from the start. Each year's loans keep their own rate "
                 "though, so it's not like older loans get repriced upward too, just "
                 "the new ones each year.",
        "reference": "Federal student loan interest rates for a given academic year are "
                     "set annually by statute, typically calculated as the 10-year "
                     "Treasury note yield plus a fixed add-on percentage that varies by "
                     "loan type, and remain fixed for the life of loans disbursed "
                     "within that academic year.",
    }),

    # ---------------- furniture ----------------
    ("furn_standingdesk", "furniture", "What's the height adjustment range on this standing desk, and how much weight can the surface support?", "forum", {
        "blog": "Standing desks get sold on the health benefits, but the honest case is "
                "more modest than the marketing implies — the real value is variety of "
                "position throughout the day, not standing all day instead of sitting "
                "all day, which brings its own problems. Alternate between sitting and "
                "standing rather than committing to one extreme.",
        "news": "An ergonomics research group published findings suggesting the health "
                "benefits of standing desks are smaller than commonly claimed in "
                "marketing, while still finding modest improvements in reported energy "
                "levels and reduced lower back discomfort among regular alternators "
                "between sitting and standing.",
        "docs": "Assembly and weight distribution. Distribute weight evenly across the "
                "desktop surface rather than concentrating heavy items to one side, "
                "particularly near the maximum height setting where lateral stability "
                "is reduced. Do not exceed the stated weight capacity, which typically "
                "accounts for even distribution.",
        "product": "RiseForm Electric Standing Desk — dual-motor lift system with "
                   "programmable height presets. Anti-collision safety sensor. Cable "
                   "management tray included. Available in three desktop sizes.",
        "forum": (
            "r/BuyItForLife — Got one after years of a fixed-height desk and the "
            "difference for my back has been real, not just placebo. Motor noise is "
            "worth checking reviews for specifically, some cheaper models are "
            "noticeably louder than others when adjusting, especially in a quiet shared "
            "home office. Cable management gets messier than expected once you're "
            "actually raising and lowering it daily, plan for that.",
            "r/BuyItForLife — Got one after years of a fixed-height desk and the "
            "difference for my back has been real. Mine adjusts from 24 to 50 inches, "
            "which covers sitting and standing for my height fine, and it's rated for "
            "200 pounds so my dual monitor setup sits on it with room to spare. Cable "
            "management gets messier than expected once you're actually raising and "
            "lowering it daily."
        ),
        "reference": "Electric standing desks use a motorized lift mechanism, typically "
                     "dual-motor for larger desktops, to adjust surface height between "
                     "sitting and standing positions. Weight capacity and height range "
                     "vary by model and generally correlate with motor strength and "
                     "frame construction quality.",
    }),

    ("furn_mattress", "furniture", "How many inches thick is this mattress, and how many years does the warranty cover?", "reference", {
        "blog": "Mattress shopping online involves an unusual amount of trust, since "
                "most boxed-mattress companies build the entire pitch around a home "
                "trial period rather than trying before buying. The trial period length "
                "and return logistics matter as much as the mattress specs themselves — "
                "check who pays for return shipping and whether a donation pickup is "
                "arranged for you.",
        "news": "A mattress-in-a-box company was named in a consumer complaint "
                "investigation over return policy practices, with several customers "
                "alleging return requests during the advertised trial period were "
                "delayed or partially denied. The company said it has since clarified "
                "its return process documentation.",
        "docs": "Warranty claim process. Sagging depth is measured with the mattress on "
                "a flat, supportive surface without a person on it; claims typically "
                "require photographic documentation and the original proof of purchase. "
                "Warranty coverage is generally void if the mattress was used without "
                "an appropriate supportive base or frame.",
        "product": "CloudLayer Hybrid Mattress — combines pocketed coil support with a "
                   "cooling gel memory foam top layer. Medium-firm feel. Ships "
                   "compressed in a box. 100-night home trial included.",
        "forum": "r/Mattress — Read the warranty fine print after a friend had a "
                 "sagging issue denied because they'd been using it without the "
                 "recommended foundation underneath. Learned that lesson secondhand "
                 "thankfully, made sure my own setup met the requirements before it "
                 "ever became an issue.",
        "reference": (
            "Mattress construction generally falls into several categories — "
            "innerspring, memory foam, latex, and hybrid designs combining coils with "
            "foam layers — each offering different support, motion isolation, and "
            "temperature regulation characteristics that matter more for some sleepers "
            "than others depending on body weight and sleeping position. Firmness is "
            "typically rated on a numeric scale not standardized across manufacturers.",
            "Mattress construction generally falls into several categories — "
            "innerspring, memory foam, latex, and hybrid designs. This hybrid model "
            "measures 12 inches thick, combining coil support with foam comfort layers, "
            "and carries a 10-year warranty against structural defects such as sagging "
            "beyond a specified depth. Firmness is typically rated on a numeric scale "
            "that is not standardized across manufacturers."
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
        "corpus_version": "0.4",
        "n_prompts": len(prompts_out),
        "n_docs": len(docs_out),
        "formats": FORMATS,
        "domains": sorted({p["domain"] for p in prompts_out}),
        "prompts": prompts_out,
        "documents": docs_out,
    }
    payload = json.dumps(corpus, indent=2, sort_keys=True, ensure_ascii=False)
    corpus["corpus_sha256"] = hashlib.sha256(payload.encode()).hexdigest()[:16]

    out = pathlib.Path(__file__).parent / "corpus_v0.4.json"
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
