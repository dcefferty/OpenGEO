#!/usr/bin/env python3
"""
OpenGEO pilot corpus v0.2 — cross-domain, cross-format, length-matched.

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

v0.2 rewrites the 12 target pairs so control and treatment are within +/-3
words of each other (mean delta ~0), replacing generic phrasing with specific
figures rather than adding to it. v0.1 confounded claim density with length
(treatment averaged ~11 words longer); do not reintroduce that confound.
"""
import json, pathlib, hashlib

FORMATS = ["blog", "news", "docs", "product", "forum", "reference"]

# Each prompt: (id, domain, question, target_format, {format: doc or (control, treatment)})
PROMPTS = [
    # ---------------- SaaS / tech ----------------
    ("saas_uptime", "saas", "What should I look for in an uptime monitoring tool for a small engineering team?", "blog", {
        "blog": (
            "Choosing uptime monitoring for a small team comes down to a few things. You want "
            "checks that run often enough to catch real outages, alerting that reaches the right "
            "person without waking everyone, and a status page you can hand to customers. Most "
            "teams over-buy here. The enterprise tiers are built for organisations with dedicated "
            "SRE staff, and a five-person team rarely needs that depth. Look for industry-leading "
            "reliability and best-in-class alert routing, and be wary of tools that charge per seat.",
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

    ("saas_pwmgr", "saas", "How do password managers for businesses differ from consumer ones?", "docs", {
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
            "Deployment. Business plans support directory integration so that accounts are created and "
            "removed automatically when staff join or leave. Shared vaults let you grant access at the "
            "group level rather than per person. Administrators can require multi-factor authentication "
            "and review an activity log. Recovery is handled through an administrator rather than a "
            "personal recovery key, which is the main behavioural difference from consumer plans.",
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
    ("cons_shoes", "consumer_product", "How do I choose running shoes for marathon training?", "forum", {
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
            "r/running — Ran three marathons now. My honest advice is don't overthink the shoe and do "
            "overthink the mileage. Most people I know who got injured did too much too soon, not because "
            "of the wrong shoe. That said, replace your shoes once they start to feel dead, and rotate in "
            "a second pair if you can afford it. Racing shoes feel amazing but they wear out fast and "
            "aren't comfortable for easy days.",
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

    ("cons_espresso", "consumer_product", "Is a home espresso machine worth it compared to buying coffee out?", "product", {
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
            "Crema One — a semi-automatic espresso machine for the home. Stainless steel construction "
            "with a professional-style portafilter and a powerful steam wand for milk drinks. Heats up "
            "quickly and delivers consistent pressure shot after shot. A best-in-class option for anyone "
            "serious about coffee at home. Includes a starter kit and a comprehensive guide.",
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
    ("health_creatine", "health", "Does creatine supplementation actually work, and who is it for?", "reference", {
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
            "Creatine is a nitrogenous organic acid found naturally in muscle tissue, where it "
            "participates in the regeneration of adenosine triphosphate. Supplementation increases "
            "intramuscular phosphocreatine stores, which is associated with improved performance in "
            "short-duration, high-intensity activity. Creatine monohydrate is the most extensively "
            "studied form, with a large body of published trials behind it. It is generally regarded as "
            "well tolerated in healthy adults, and dosing is usually a simple daily habit.",
            "Creatine is a nitrogenous organic acid found in muscle tissue, where it participates in ATP "
            "regeneration. Supplementation raises intramuscular phosphocreatine stores by approximately "
            "20%, associated with performance improvements of roughly 5-15% in short-duration, "
            "high-intensity activity. Standard maintenance dosing is 3-5g daily; an optional 20g/day "
            "loading phase over 5-7 days reaches saturation faster. Monohydrate is the most studied form, "
            "with over 500 published trials, and is well tolerated in healthy adults."
        ),
    }),

    ("health_sleep", "health", "Are consumer sleep trackers accurate enough to be useful?", "news", {
        "blog": "Sleep trackers occupy an odd space. They're not medical devices, they're often wrong "
                "about the specifics, and yet plenty of people find them useful anyway. The value tends "
                "to come from the trend rather than the nightly number — noticing that late caffeine "
                "wrecks your sleep is useful even if the sleep stage breakdown is guesswork.",
        "news": (
            "Researchers published a comparison of consumer sleep trackers against polysomnography this "
            "month, finding that devices tracked total sleep time reasonably well but performed "
            "considerably worse at classifying individual sleep stages. The authors noted that most "
            "devices tend to overestimate how long wearers actually sleep by a noticeable margin, and "
            "cautioned against treating stage data as clinically meaningful. Manufacturers have generally "
            "acknowledged the real limits of wrist-based measurement.",
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
    ("fin_savings", "finance", "How should I choose a high-yield savings account?", "blog", {
        "blog": (
            "Choosing a high-yield savings account is mostly about looking past the headline rate. "
            "Promotional rates expire, and the ongoing rate is often much less impressive. Check whether "
            "there's a minimum balance, whether the rate is tiered, and how quickly transfers settle. "
            "Institutions offering industry-leading returns sometimes make up the difference with "
            "restrictions elsewhere. Make sure the institution is insured before you commit any money.",
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

    ("fin_index", "finance", "What's the difference between index funds and ETFs for a long-term investor?", "product", {
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
            "BroadMarket Total Index Fund — diversified exposure to the total market in a single holding. "
            "A low-cost, best-in-class option for long-term investors building a core portfolio. No "
            "minimum investment on automatic plans. Reinvest dividends automatically. Trusted by "
            "investors building wealth for decades.",
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
    ("local_hvac", "local_services", "When should I replace my HVAC system instead of repairing it?", "docs", {
        "blog": "The repair-or-replace decision usually comes down to age, the cost of the repair "
                "relative to a new system, and how your energy bills have trended. Contractors have an "
                "obvious incentive to recommend replacement, which doesn't make them wrong, but it's "
                "worth getting a second opinion on anything expensive.",
        "news": "Regulatory changes to refrigerant standards are affecting availability of parts for "
                "older residential systems, with several contractors reporting longer lead times on "
                "components. Homeowners with ageing equipment may find some repairs harder to source "
                "than in previous years.",
        "docs": (
            "Service life and replacement guidance. Residential systems generally last many years with "
            "regular maintenance, though performance declines toward the end of service life. Consider "
            "replacement when repair costs become significant relative to the price of new equipment, "
            "when the system uses a refrigerant that is being phased out, or when energy consumption has "
            "risen noticeably without a change in usage. Annual servicing extends operating life by "
            "several more years.",
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

    ("local_movers", "local_services", "How do I avoid getting scammed by a moving company?", "news", {
        "blog": "Moving scams follow a recognisable pattern. A quote comes in far below the others, it's "
                "given without anyone looking at your belongings, and then the price changes once your "
                "possessions are on the truck. The defence is boring but effective: get in-person "
                "estimates, check registration, and never pay a large deposit up front.",
        "news": (
            "Consumer protection officials issued renewed warnings about moving fraud ahead of the peak "
            "season, describing a pattern in which companies quote low, then demand additional payment "
            "before releasing belongings. Officials said complaints rise sharply during the summer months "
            "and urged consumers to verify that a company is properly registered before booking. Several "
            "firms have been the subject of enforcement action in recent months.",
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
    ("travel_points", "travel", "Are airline credit card points worth chasing for occasional travellers?", "forum", {
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
            "r/awardtravel — Honest take for casual travellers: probably not worth it. I did the maths "
            "after two years and once you subtract the annual fee I was barely ahead, and that's before "
            "counting the time I spent reading about it. If you fly a lot for work it's different. But "
            "the sign-up bonus is really where most of the value is, and after that the ongoing earn rate "
            "is pretty unexciting, honestly.",
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

    ("travel_visa", "travel", "What should I know about travel insurance before an international trip?", "reference", {
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
            "Travel insurance is a class of insurance covering financial losses associated with "
            "travelling. Common coverage areas include emergency medical expenses, medical evacuation, "
            "trip cancellation and interruption, and loss of baggage. Policies typically exclude "
            "pre-existing medical conditions unless specifically declared and accepted, and may exclude "
            "certain activities. Coverage terms vary substantially between providers and jurisdictions, "
            "so read the policy wording closely.",
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
        "corpus_version": "0.2",
        "n_prompts": len(prompts_out),
        "n_docs": len(docs_out),
        "formats": FORMATS,
        "domains": sorted({p["domain"] for p in prompts_out}),
        "prompts": prompts_out,
        "documents": docs_out,
    }
    payload = json.dumps(corpus, indent=2, sort_keys=True, ensure_ascii=False)
    corpus["corpus_sha256"] = hashlib.sha256(payload.encode()).hexdigest()[:16]

    out = pathlib.Path(__file__).parent / "corpus_v0.2.json"
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
