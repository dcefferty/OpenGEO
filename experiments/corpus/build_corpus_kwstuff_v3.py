#!/usr/bin/env python3
"""
OpenGEO corpus -- keyword-stuffing intervention, v3 (kwstuff-v3).

Second redesign. v1 (corpus_kwstuff_v1.json) reused corpus v0.4's `treatment` variant
wholesale as its baseline and hit a ceiling (~98.5% pooled CPR, no headroom). v2
(corpus_kwstuff_v2.json) tried a "half-specific" recombination baseline, on the theory
that answering only one of a question's two target facts would land somewhere between
v0.4's true orthogonal control (pooled CPR 0.503) and its full-answer treatment (pooled
CPR 0.985). A real-model spot check of v2 (2,304 calls, 6 prompts, 0 errors) falsified
that theory: `moderate`-condition CPR came back 0.911-0.984 on every spot-checked
prompt -- the same ceiling as v1. Splicing in even one concrete, on-topic fact is
apparently sufficient by itself to push these models' citation behavior to the same
level as a fully-specific document; they do not appear to discriminate on
*completeness* of an answer, only on presence vs. absence of *any* specific content.
See `preregistrations/2026-08-kwstuff-v2.md`'s Deviations section for the full
diagnosis.

v3 abandons the "partial answer" axis entirely and returns to the one baseline this
project has *directly confirmed*, by real-model measurement, sits at a genuine
mid-range CPR: corpus v0.4's actual orthogonal `control` text -- zero specific facts on
either target fact, pooled CPR 0.503 across 8 models. v3's design:

    orthogonal = corpus v0.4's `control` variant, reused VERBATIM, unmodified. No new
                 prose, no recombination -- this is the one baseline this project has
                 already measured against real models and confirmed is not at a
                 ceiling or floor.
    stuffed    = the SAME orthogonal content, with the prompt's core topic keyword
                 (unchanged mapping from v1/v2) awkwardly repeated 4-8 times where
                 natural writing wouldn't -- with NO new facts added. This is arguably
                 a truer test of textbook SEO keyword stuffing than v1/v2's designs:
                 repetition layered onto content that doesn't actually answer the
                 question any better, which is the classic stuffing pattern (padding
                 without added substance) rather than repetition layered onto a
                 genuinely more informative document. Length-matched to `orthogonal`
                 within +/-3 words, same discipline as every corpus version in this
                 project.

Because `orthogonal` is reused byte-for-byte from `corpus_v0.4.json`, this design
carries forward the ONE piece of real-model evidence this project actually has about
where these prompts' citation midpoint sits, rather than a new, unvalidated assumption.
The pre-registration for this corpus (`preregistrations/2026-08-kwstuff-v3.md`) still
commits to a real-model spot check before the full round, per the process lesson from
v2 -- reusing validated content once already failed to guarantee the *combination*
behaves as expected, so the check runs regardless.

Reuses corpus/build_corpus.py's 48 prompts wholesale -- same questions, same domains,
same 5 non-target distractor documents per prompt, same target format balance (8
prompts/format). Only the target document's two variants differ.
"""
import json, pathlib, hashlib
import build_corpus as base

# ---------------------------------------------------------------------------
# `orthogonal` baseline: corpus v0.4's real `control` text, reused verbatim.
# Loaded directly from corpus_v0.4.json at build time -- not hand-copied -- so
# there is no risk of a transcription drift from the text this project already
# measured (pooled CPR 0.503) at real models.
# ---------------------------------------------------------------------------
_v04 = json.loads((pathlib.Path(__file__).parent / "corpus_v0.4.json").read_text())
ORTHOGONAL = {d["prompt_id"]: d["variants"]["control"] for d in _v04["documents"] if d["is_target"]}

# ---------------------------------------------------------------------------
# Keyword-stuffed counterpart of each ORTHOGONAL baseline. Same facts (i.e. none
# of the target question's facts -- orthogonal content only), same core topic
# keyword (identical mapping to kwstuff-v1/v2) repeated unnaturally 4-8 times.
# No new facts added. Length-matched to ORTHOGONAL within +/-3 words.
# ---------------------------------------------------------------------------
STUFFED = {}
def s(pid, text): STUFFED[pid] = text

s("auto_dashcam", "RoadWitness — the dashcam with front and rear cameras, wide-angle lens, and night vision. This dashcam's compact housing mounts discreetly behind the mirror without blocking your dashcam view. This dashcam's GPS logging embeds speed and location. This dashcam offers app-based playback over WiFi, with dashcam suction and adhesive mounts included.")
s("auto_evcharger", "Installing an EV charger at home is one of those EV charger projects people either overthink or underthink. Get an electrician to check your panel before ordering an EV charger — an older home's panel capacity derails EV charger installs, not the EV charger itself. EV charger placement matters too; think about where you park, not just where the garage EV charger outlet happens to be.")
s("career_negotiate", "r/careerguidance — My salary negotiation went better than expected, mostly because I researched before my salary negotiation instead of asking vaguely. Frame your salary negotiation around market data and specific value, not personal need. Companies expect a salary negotiation at this point — a reasonable, well-justified salary negotiation rarely costs the offer if you're polite, specific, and flexible about which parts matter most in your salary negotiation. Timing your salary negotiation matters too, in my experience.")
s("career_resume", "A resume summarizes a candidate's professional experience, education, and qualifications for hiring managers and applicant tracking systems reviewing each resume. Resume format and resume content conventions vary by industry, region, and seniority, though certain resume elements — contact info, chronological resume history, and a resume skills section — are broadly standard everywhere. A resume should be proofread carefully.")
s("cons_espresso", "Crema One — the espresso machine for the home. This espresso machine features stainless steel construction, a professional-style portafilter, and a powerful steam wand. This espresso machine is compact enough for a standard counter and pairs well with any grinder. This espresso machine includes a starter kit and a dial-in guide.")
s("cons_shoes", "r/running — Ran three marathons in these running shoes. Honest advice: don't overthink the running shoes, overthink your training load. Nearly everyone who got injured added too much volume too fast, not from the running shoes themselves. Fit matters more for running shoes than people think — running shoes that run narrow will wreck a long run. Try running shoes on in the afternoon, not first thing. Buy running shoes a half size larger.")
s("cook_airfryer", "Air fryers earned the hype, but the size decision trips air fryer buyers up most. Basket-style and oven-style air fryer designs cook differently despite similar air fryer marketing — oven-style air fryers often preheat faster and allow multiple air fryer racks at once. Non-stick air fryer coating durability varies between brands, worth checking air fryer reviews before buying.")
s("cook_knife", "Hearthstone — the chef's knife with full-tang forged construction and a comfortable, balanced chef's knife handle for extended prep without hand fatigue. This chef's knife has a hand-sharpened edge. This chef's knife should avoid the dishwasher.")
s("diy_drill", "r/tools — Upgraded to a cordless drill last year, best cordless drill decision ever. Buy into a cordless drill battery platform, not just a cordless drill — once you have packs for your cordless drill you'll buy every tool in that cordless drill line. Cordless drill chuck quality matters too, a cheap cordless drill chuck will slip and strip screws. Cordless drill grip ergonomics matter for longer sessions. A quality battery and charger combo makes the real cordless drill difference.")
s("diy_kit", "HearthLine — the laminate flooring with an oak-look, scratch-resistant surface. This laminate flooring has click-lock edges for a glueless install. This laminate flooring suits kitchens and living areas, available in five laminate flooring colors. Laminate flooring underlayment sold separately; check laminate flooring compatibility with radiant heat systems first.")
s("edu_bootcamp", "Choosing a coding bootcamp means being honest about time. Coding bootcamp curriculum breadth matters — look for a coding bootcamp covering a real portfolio project, not tutorials. Coding bootcamp mentor access is worth more than people think; a stuck coding bootcamp student wastes real time waiting. Check whether the coding bootcamp alumni network is active or dormant. Research each coding bootcamp carefully before enrolling in one.")
s("edu_certification", "PMP certification registration requirements: PMP certification candidates must submit 35 hours of education before scheduling, and some PMP certification applications face a random audit requiring extra documentation. PMP certification testing is available at proctored centers or via remote proctoring, both requiring photo ID. PMP certification fees are non-refundable once booked, though PMP certification rescheduling is permitted for a fee. Study consistently for weeks before your PMP certification exam date.")
s("fin_index", "BroadMarket — the index fund with exposure to the total market. This index fund is built for investors who want a core index fund position without picking stocks. This index fund reinvests dividends automatically. This index fund is trusted by long-term index fund investors through market cycles.")
s("fin_savings", "Choosing a high-yield savings account means looking past the headline rate. A clean high-yield savings account app matters more than expected — check if your high-yield savings account offers sub-accounts. High-yield savings account customer service is worth testing before committing. A high-yield savings account with a great rate sometimes has a clunkier transfer process. Compare a high-yield savings account's mobile app reviews too.")
s("fit_homegym", "r/homegym — Built my home gym slowly over a year, and I'd recommend that home gym approach over buying upfront. Figure out what home gym equipment you'll actually use before spending on fancier home gym gear. Home gym flooring matters more than expected, protecting both the floor and the home gym equipment.")
s("fit_hrzones", "Heart rate training zones divide intensity into ranges based on percentage of maximum heart rate or heart rate reserve, guiding training toward heart rate adaptations. Maximum heart rate is estimated using an age-based heart rate formula, though heart rate variation from the estimate can be substantial, which is why coaches recommend a heart rate field test. Heart rate accuracy varies by device and sensor placement.")
s("furn_mattress", "Mattress construction falls into categories — innerspring, memory foam, latex, and hybrid mattress designs combining coils with foam mattress layers — each offering different mattress support, motion isolation, and mattress temperature regulation that matters more for some mattress sleepers depending on body weight. Mattress firmness is rated on a scale not standardized across mattress manufacturers.")
s("furn_standingdesk", "r/BuyItForLife — Got a standing desk after years of a fixed-height desk and my back thanks this standing desk, not placebo. Standing desk motor noise is worth checking reviews for — some standing desk models are louder when adjusting, especially in a quiet home office. Standing desk cable management gets messier than expected once raising and lowering it daily. A sturdy frame matters as much as speed.")
s("game_headset", "SonicWave — the wireless gaming headset with 50mm drivers and a detachable noise-cancelling mic. This wireless gaming headset works on PC, console, and mobile via USB dongle. This wireless gaming headset has memory foam ear cushions with breathable fabric.")
s("game_pc_upgrade", "A gaming PC upgrade piece by piece beats a full gaming PC rebuild unless the system is old. Case clearance and airflow are what people forget to check before any gaming PC upgrade — a card too long for your case ruins the gaming PC upgrade. Selling old gaming PC upgrade parts individually usually recovers more of your original spend. Check part compatibility carefully before starting any gaming PC upgrade project.")
s("garden_composter", "DualBin — the compost tumbler with a twin-chamber rotating design for continuous compost tumbler composting. This compost tumbler's elevated stand keeps pests out and eases compost tumbler turning without bending. UV-resistant compost tumbler construction is rated for years of outdoor compost tumbler exposure.")
s("garden_raisedbed", "r/gardening — Built our first raised garden bed this spring, one of our better yard projects. Raised garden bed soil quality matters more than expected — don't grab the cheapest bagged soil for your raised garden bed, a proper raised garden bed mix makes a real difference. Sun exposure planning before building your raised garden bed matters more than the bed itself. Cedar lasts longest for raised garden beds.")
s("health_creatine", "Creatine dosing starts with creatine as a nitrogenous organic acid in muscle tissue, participating in ATP regeneration. Creatine dosing supplementation increases phosphocreatine stores, associated with improved performance. Monohydrate creatine dosing is the most studied form, with a large evidence base spanning strength and sprint performance. Creatine dosing is well tolerated in healthy adults with no long-term concerns. Confirm your creatine dosing plan with a doctor before starting any routine.")
s("health_sleep", "A sleep lab published a sleep tracker comparison against polysomnography this month, the largest sleep tracker study at that site in years. The sleep tracker work was presented at a conference and drew responses from sleep tracker makers, who welcomed scrutiny of wrist-based sleep tracker measurement. Reviewers noted the sleep tracker sample skewed young and called for broader follow-up. Sleep tracker accuracy varied more during light sleep stages.")
s("legal_llc", "A state filing office reported a surge in LLC registrations this year, attributing the increase to freelance and gig-economy growth, particularly among consultants forming an LLC for the first time. Officials noted a rise in LLC name-availability disputes as more LLC applicants submit similar business names within the same LLC industry category. Filing an LLC correctly the first time avoids costly delays.")
s("legal_smallclaims", "Small claims court filing procedure: complete the small claims court form with the defendant's name and address. Small claims court cases are generally heard without attorneys, though small claims court rules vary by jurisdiction. A small claims court hearing date is scheduled within 4-8 weeks, and both parties may request a small claims court continuance.")
s("loan_forgiveness", "Income-driven repayment overview: income-driven repayment amounts are recalculated annually based on updated income documentation, resubmitted each year through the income-driven repayment servicer's portal to stay enrolled. Missing an income-driven repayment recertification deadline can revert you to a standard repayment plan with a higher income-driven repayment payment. Track your income-driven repayment progress yearly toward eligibility.")
s("loan_rate", "The federal student loan interest rate for the upcoming year follows the annual formula tied to the 10-year Treasury note auction. This student loan interest rate adjustment applies only to loans disbursed after July 1 and does not affect prior years' student loan interest rate terms already disbursed. Compare this student loan interest rate against private loan options too before deciding.")
s("local_hvac", "HVAC system service life guidance: watch for HVAC system signs beyond breakdown — uneven temperatures, rising humidity, or an HVAC system running constantly without reaching the thermostat setting. HVAC system noise often creeps up as components wear. An HVAC system maintenance visit should inspect ductwork for leaks, since duct losses undermine even a healthy HVAC system. Getting HVAC system maintenance right the first time saves real money over the long term.")
s("local_movers", "Officials warned about moving company fraud ahead of peak season, describing a pattern where a moving company quotes low, then demands extra payment before releasing belongings. Officials said the moving company tactic is showing up on more review sites. Several moving company firms named in complaints have since changed their moving company operating names, a recurring evasion tactic. Always vet your moving company thoroughly before signing anything.")
s("nutr_meal", "Meal replacement shake preparation: shake this meal replacement shake with 8-12oz of water or milk. Consume your meal replacement shake within 30 minutes for optimal texture. Not intended as a sole nutrition source — talk to a provider before relying on a meal replacement shake long-term.")
s("nutr_protein", "Protein intake advice ranges from reasonable to absurd online. Whole food protein intake sources come with fiber and micronutrients a shake alone doesn't replicate, worth weighing before defaulting to protein intake powder for convenience. Protein intake preparation matters too — batch-cooking removes the daily decision fatigue that derails good protein intake intentions. Track your protein intake consistently for the most reliable results.")
s("parent_carseat", "A convertible car seat transitions between rear- and forward-facing as a child grows, distinguishing a convertible car seat from infant seats, which are rear-facing only. Convertible car seat installation method (seatbelt or LATCH) and recline angle both affect convertible car seat effectiveness and vary by convertible car seat model and age.")
s("parent_recall", "A stroller recall this month is the manufacturer's second stroller recall in as many years. The stroller recall company is coordinating with regulators on customer outreach and offering a free stroller recall repair kit shipped to registered owners. Retailers have pulled the stroller recall model from shelves pending the fix. Parents can check the stroller recall online.")
s("pets_insurance", "Dog insurance is indemnity insurance covering veterinary costs from illness or injury. Most dog insurance policies exclude pre-existing conditions and may impose dog insurance waiting periods for conditions such as cruciate ligament injuries. Wellness dog insurance coverage for routine care is typically a separate optional dog insurance add-on, not bundled by default. Dog insurance waiting periods vary by provider.")
s("pets_vaccine", "A vet association updated puppy vaccine guidelines this year, emphasizing risk-based scheduling for adult dogs rather than puppy vaccine one-size-fits-all. The puppy vaccine revision reflects evidence that non-core vaccines were given more than necessary, particularly to low-exposure adult dogs in single-pet households. Core puppy vaccine recommendations remain unchanged under the new puppy vaccine guidance. Boosters remain important for adult dogs too.")
s("photo_lens", "The 50mm prime lens is the classic first lens recommendation — this 50mm prime lens forces you to move your feet instead of zooming, improving composition habits faster than a zoom. This 50mm prime lens offers excellent image quality per dollar versus a kit zoom. Not ideal for tight spaces where a 50mm prime lens can't back up enough. Many keep a 50mm prime lens handy.")
s("photo_raw", "RAW photo files overview: RAW photo files require compatible editing software to open, while JPEG displays natively in any viewer without conversion. RAW photo files use a manufacturer-specific proprietary format, occasionally requiring a software update after a new camera release. JPEG remains the universal standard for sharing RAW photo files alternatives. Most working professionals shoot RAW by default.")
s("re_inspection", "r/RealEstate — Went through our home inspection last month buying our first place. The home inspection walked the property methodically, roof to foundation, with a home inspection report flagging everything from minor to serious. Home inspection scheduling was tricky in a competitive market — good home inspection providers book up fast, so line one up the same day.")
s("re_warranty", "HomeShield — the home warranty covering major systems and appliances against mechanical failure. This home warranty includes a 24/7 claims line. This home warranty's network of pre-vetted contractors is dispatched per home warranty claim. Home warranty coverage begins 30 days after enrollment.")
s("saas_pwmgr", "Deployment: a business password manager includes a browser extension that autofills credentials, plus a dedicated business password manager admin app separate from the personal vault. Business password manager folders can be organised by team. The business password manager dashboard flags weak or reused passwords. Business password manager recovery runs through an admin, not a personal key. Every business password manager should also support multi-factor authentication for stronger account protection overall.")
s("saas_uptime", "Choosing uptime monitoring for a small team comes down to a few things. For uptime monitoring, integration quality matters most: Slack and PagerDuty hooks that route correctly. An uptime monitoring status page cuts down on support tickets. Most teams over-buy on uptime monitoring dashboards they'll never touch. Look for clean uptime monitoring interfaces, solid webhook support, and easy uptime monitoring cancellation. Free trials for uptime monitoring tools are common, so test a few uptime monitoring options before committing to one.")
s("sec_breach", "A retailer disclosed a data breach this week, saying it detected unauthorized access behind the data breach in its internal customer database and engaged forensics to investigate the data breach. The company said it notified law enforcement about the data breach and is offering affected customers complimentary data breach monitoring.")
s("sec_vpn", "A consumer VPN routes traffic through an encrypted tunnel to a consumer VPN provider's server, masking your IP from destination sites. Consumer VPN providers are typically incorporated in a jurisdiction determining what consumer VPN data-retention laws apply. Free consumer VPN services commonly monetize through advertising or data partnerships instead of subscription fees. A no-logs consumer VPN policy is difficult to verify independently.")
s("tax_deadline", "The tax authority reminded filers about the tax filing deadline this week, noting call center wait times peak near the tax filing deadline. The agency encouraged taxpayers who can't meet the tax filing deadline to request an extension electronically well ahead, rather than waiting until the tax filing deadline when delays cause submissions to fail. Some states set their own separate tax filing deadline entirely.")
s("tax_freelance", "Self-employment tax recordkeeping overview: self-employment tax filers should retain receipts for three years in case of a self-employment tax audit, organized by category. Keeping separate records for business and personal expenses makes eventual self-employment tax filing less painful, and a dedicated bank account is the easiest way to enforce that self-employment tax separation. Late self-employment tax filing can trigger extra penalties too.")
s("travel_points", "r/awardtravel — Approval odds for an airline credit card depend heavily on how many other airline credit cards you've opened recently, not just credit score. I got denied for one airline credit card despite great credit, approved for a similar airline credit card two months later. Airline credit card redemption windows can be brutal — some routes only release airline credit card seats 11 months out. Annual fee waivers help the airline credit card math.")
s("travel_visa", "Travel insurance covers financial losses from travelling. Common travel insurance coverage areas include emergency medical, evacuation, cancellation, and baggage loss. Travel insurance policies typically exclude pre-existing conditions unless declared, and may exclude certain travel insurance adventure activities. Travel insurance terms vary between providers, so read the travel insurance policy wording closely. Compare travel insurance policies carefully before buying.")


def build():
    base_prompts = {p[0]: p for p in base.PROMPTS}
    assert set(ORTHOGONAL) == set(STUFFED) == set(base_prompts), "prompt id mismatch"
    docs_out, prompts_out = [], []
    for pid in ORTHOGONAL:
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
                        "control": ORTHOGONAL[pid].strip(),
                        "treatment": STUFFED[pid].strip(),
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
        "corpus_version": "kwstuff-v3",
        "intervention": "keyword_stuffing",
        "base_corpus_version": "0.4",
        "supersedes": "kwstuff-v2",
        "n_prompts": len(prompts_out),
        "n_docs": len(docs_out),
        "formats": base.FORMATS,
        "domains": sorted({p["domain"] for p in prompts_out}),
        "prompts": prompts_out,
        "documents": docs_out,
    }
    payload = json.dumps(corpus, indent=2, sort_keys=True, ensure_ascii=False)
    corpus["corpus_sha256"] = hashlib.sha256(payload.encode()).hexdigest()[:16]

    out = pathlib.Path(__file__).parent / "corpus_kwstuff_v3.json"
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
    print(f"  target length delta (stuffed-orthogonal): min={min(delta)} max={max(delta)} mean={sum(delta)/len(delta):.1f}")


if __name__ == "__main__":
    build()
