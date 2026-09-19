#!/usr/bin/env python3
"""
OpenGEO -- tactic pilot for ROADMAP item 11.

Everything built for item 11 so far tests the *corpus*: that eight or more real
candidates can be sourced, that a target can be screened to a movable baseline. Nothing
has tested the *intervention*. No tactic variant has ever been written or run, so two
assumptions under the whole round are untested:

  1. that a tactic can be applied to a screened target at all, fact-preserving and at
     the length real federal excerpts come in
  2. that it moves citation enough to be worth ranking

This pilot answers both on three questions, ~1,800 calls, before the remaining ~11-36
questions are sourced against those assumptions. It also sizes the round: the corpus
count in ROADMAP item 11 rests on H6's +0.038 as a stand-in for tactic magnitude, and H6
was keyword stuffing, not a tactic this round will rank. A measured effect replaces the
stand-in -- OR 1.30 needs 25 questions, OR 1.15 needs 50.

**These three questions are held out of the round.** The pilot reads effect sizes, which
is what pre-registration exists to constrain; holding them out costs three of fourteen
kept questions and buys a round whose corpus has never been looked at. The tactic set
below is fixed before the pilot runs (see results/probes/, committed first) so the pilot
cannot select tactics that happened to work.

## Why these three questions

Of the fourteen kept targets, only seven have three or more sentences, and a
single-sentence document cannot carry answer-first structure or an FAQ block at all.
These three are the highest-headroom members of that seven whose control text also has a
genuine buried lede -- an answer that is not already in the first sentence -- so every
tactic below is actually defined on them:

  home_smokealarm    cpsc_blog       headroom 0.250   Daylight Saving framing, advice last
  health_bloodpressure nhlbi_hbp     headroom 0.208   caveat first, 120/80 second and third
  finance_housingshare census_story22 headroom 0.208  statistic first, definition second

Engines excluded by the screen: gpt, grok, grok. So claude, gemini and deepseek rest on
all three questions, gpt on two, grok on one. Acceptable for a pilot, which is not a
published ranking; the round's pre-registration must set a floor on these counts.

## The tactics

All four are **fact-preserving**: no numeral appears in a variant that is not in the
control. That is the point. The corpus already proves specific facts beat no facts by
+0.48 (H4); any tactic that adds a fact re-runs H4 and swamps everything else, which is
why "add statistics" -- named in the item 11 sketch -- is not here.

  answer_first  the sentence answering the question is moved to the front. On two of the
                three this is a pure permutation of the control's own sentences; on
                cpsc_blog the fronted sentence opens "As you set the new time," which
                does not stand alone, so the clause is re-hinged. No fact changes.

  faq           answer_first, plus the question itself as a heading. Deliberately nested:
                faq minus answer_first is the marginal effect of the heading. Note the
                confound this cannot escape -- an FAQ heading necessarily introduces the
                question's own words, so `faq` carries a keyword-insertion effect (H6,
                +0.038) inside it. It is reported as heading-plus-keywords, not as
                formatting alone.

  attributed    the same facts, attributed inline to the issuing agency. **Weak by
                construction on two of three:** federal pages name their own agency, so
                cpsc_blog and census_story22 already carry attribution in the control and
                the manipulation is only a strengthening. Only nhlbi_hbp is a clean
                un-attributed baseline. If this arm comes back null, that is the likeliest
                reason, and the round should source un-attributed controls for it.

  citation      the control text unchanged, plus a trailing source line naming agency,
                title and publisher. Adds no claim about the answer -- the line restates
                provenance the corpus already records.

Lengths are reported by the build. answer_first is length-identical or near it; the other
three add 10-45%, which is large in relative terms on a 32-word document. H7 measured
padding of 25-100% at +0.004 pooled, so length is not expected to carry these, but the
round's analysis must report words per variant rather than assume it.

## Provenance

The control arm is verbatim agency text, sliced from a committed snapshot and unchanged.
The tactic arms are authored rewrites of it and are marked `"authored": true` per variant,
so nothing in this corpus attributes invented words to an agency. Candidate documents are
imported unchanged from the screen corpora -- the text has exactly one source of truth --
and carry the control text under every condition, since only the target varies.

    python3 corpus/build_corpus_tacticpilot.py
"""
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
import screen  # noqa: E402  -- the pilot target must be the one screening chose

OUTDIR = pathlib.Path(__file__).parent
CONDITIONS = ["control", "answer_first", "faq", "attributed", "citation"]

# (batch corpus, screening runs, prompt_id, target key). The batch file is the immutable
# record the question was screened against; batch 5 supersedes batch 4 for re-sourced
# questions. `target_doc_id` inside a screen corpus is a provisional placeholder written
# before screening ran -- the real target is screen.py's choice, so the build re-runs the
# screen and fails if it does not name the key below.
PILOT = [
    ("corpus_rankable_screen_b6.json", "screen_rankable_b6.jsonl",
     "home_smokealarm", "cpsc_blog"),
    ("corpus_rankable_screen_b8.json", "screen_rankable_b8.jsonl",
     "health_bloodpressure", "nhlbi_hbp"),
    ("corpus_rankable_screen_b1.json", "screen_rankable_b1.jsonl",
     "finance_housingshare", "census_story22"),
]

# Tactic text per target. control is NOT written here -- it is read from the screen corpus
# and asserted unchanged, so the verbatim arm cannot drift by being retyped.
VARIANTS = {
    "home_smokealarm__cpsc_blog": {
        "answer_first": (
            "Now is the perfect time to check and change the batteries in smoke and "
            "carbon monoxide (CO) alarms, the U.S. Consumer Product Safety Commission "
            "(CPSC) reminds you. Consumers will turn their clocks back one hour when "
            "Daylight Saving Time ends on Sunday, November 3, 2019, at 2:00 a.m., and "
            "setting the new time is the occasion to do it."
        ),
        "faq": (
            "How often should I test and replace my smoke alarm?\n\n"
            "Now is the perfect time to check and change the batteries in smoke and "
            "carbon monoxide (CO) alarms, the U.S. Consumer Product Safety Commission "
            "(CPSC) reminds you. Consumers will turn their clocks back one hour when "
            "Daylight Saving Time ends on Sunday, November 3, 2019, at 2:00 a.m., and "
            "setting the new time is the occasion to do it."
        ),
        "attributed": (
            "The U.S. Consumer Product Safety Commission (CPSC), the federal agency "
            "responsible for consumer product safety, advises the following. Consumers "
            "will turn their clocks back one hour when Daylight Saving Time ends on "
            "Sunday, November 3, 2019, at 2:00 a.m. As you set the new time, CPSC "
            "reminds you that now is the perfect time to check and change the batteries "
            "in smoke and carbon monoxide (CO) alarms."
        ),
        "citation": (
            "Consumers will turn their clocks back one hour when Daylight Saving Time "
            "ends on Sunday, November 3, 2019, at 2:00 a.m. As you set the new time, the "
            "U.S. Consumer Product Safety Commission (CPSC) reminds you that now is the "
            "perfect time to check and change the batteries in smoke and carbon monoxide "
            "(CO) alarms.\n\n"
            "Source: U.S. Consumer Product Safety Commission, CPSC OnSafety blog."
        ),
    },
    "health_bloodpressure__nhlbi_hbp": {
        "answer_first": (
            "A healthy systolic blood pressure is less than 120 mm Hg. A healthy "
            "diastolic pressure is less than 80 mm Hg. Your blood pressure changes "
            "throughout the day based on your activities."
        ),
        "faq": (
            "What blood pressure reading counts as high?\n\n"
            "A healthy systolic blood pressure is less than 120 mm Hg. A healthy "
            "diastolic pressure is less than 80 mm Hg. Your blood pressure changes "
            "throughout the day based on your activities."
        ),
        "attributed": (
            "According to the National Heart, Lung, and Blood Institute, your blood "
            "pressure changes throughout the day based on your activities. NHLBI puts a "
            "healthy systolic blood pressure at less than 120 mm Hg, and a healthy "
            "diastolic pressure at less than 80 mm Hg."
        ),
        "citation": (
            "Your blood pressure changes throughout the day based on your activities. A "
            "healthy systolic blood pressure is less than 120 mm Hg. A healthy diastolic "
            "pressure is less than 80 mm Hg.\n\n"
            "Source: National Heart, Lung, and Blood Institute, National Institutes of "
            "Health."
        ),
    },
    "finance_housingshare__census_story22": {
        "answer_first": (
            "Households are considered cost burdened when they spend more than 30% of "
            "their income on rent, mortgage and other housing needs. Over 19 million "
            "U.S. renter households spent more than 30% of their income on housing costs "
            "in 2021, according to data from the 2017-2021 American Community Survey "
            "(ACS) 5-year estimates released today."
        ),
        "faq": (
            "What share of my income should go to housing costs?\n\n"
            "Households are considered cost burdened when they spend more than 30% of "
            "their income on rent, mortgage and other housing needs. Over 19 million "
            "U.S. renter households spent more than 30% of their income on housing costs "
            "in 2021, according to data from the 2017-2021 American Community Survey "
            "(ACS) 5-year estimates released today."
        ),
        "attributed": (
            "According to the U.S. Census Bureau, over 19 million U.S. renter households "
            "spent more than 30% of their income on housing costs in 2021, a finding the "
            "Bureau draws from the 2017-2021 American Community Survey (ACS) 5-year "
            "estimates released today. The Census Bureau considers households cost "
            "burdened when they spend more than 30% of their income on rent, mortgage "
            "and other housing needs."
        ),
        "citation": (
            "Over 19 million U.S. renter households spent more than 30% of their income "
            "on housing costs in 2021, according to data from the 2017-2021 American "
            "Community Survey (ACS) 5-year estimates released today. Households are "
            "considered cost burdened when they spend more than 30% of their income on "
            "rent, mortgage and other housing needs.\n\n"
            "Source: U.S. Census Bureau, America Counts."
        ),
    },
}


def main():
    documents, prompts = [], []
    for fname, runsname, pid, tkey in PILOT:
        src = json.load(open(OUTDIR / fname))
        byid = {d["doc_id"]: d for d in src["documents"]}
        prompt = next(p for p in src["prompts"] if p["prompt_id"] == pid)
        tid = f"{pid}__{tkey}"
        assert tid in byid, f"{pid}: no target {tid}"

        rows = [r for r in screen.load_runs(f"results/{runsname}")
                if r["prompt_id"] == pid]
        sc = screen.screen_question(prompt, [byid[i] for i in prompt["doc_ids"]], rows)
        assert sc["verdict"] == "KEEP", f"{pid}: screen says {sc['verdict']}"
        assert sc["target"] == tid, f"{pid}: screen chose {sc['target']}, pilot expects {tid}"
        td = next(d for d in sc["documents"] if d["doc_id"] == tid)

        for did in prompt["doc_ids"]:
            d = dict(byid[did])
            # the screen corpora flag a provisional target chosen before screening ran;
            # re-flag against screen.py's actual choice or check_variants finds nothing
            d["is_target"] = (did == tid)
            control = d["variants"]["control"]
            if did == tid:
                v = VARIANTS[tid]
                missing = [c for c in CONDITIONS[1:] if c not in v]
                assert not missing, f"{tid}: no text for {missing}"
                d["variants"] = {"control": control, **{c: v[c].strip() for c in CONDITIONS[1:]}}
                d["variant_provenance"] = {
                    "control": "verbatim, sliced from the committed snapshot",
                    **{c: "authored rewrite of the control; not agency wording"
                       for c in CONDITIONS[1:]},
                }
                d["authored_variants"] = CONDITIONS[1:]
            else:
                # only the target varies; candidates carry control text under every arm
                d["variants"] = {c: control for c in CONDITIONS}
            d["words"] = len(control.split())
            documents.append(d)

        prompts.append({**prompt, "target_doc_id": tid,
                        "target_format": byid[tid]["format"],
                        "source_corpus": src["corpus_version"],
                        "screen": {"runs": runsname,
                                   "headroom_movable": round(td["headroom_movable"], 4),
                                   "baseline_pooled": round(td["pooled"], 4),
                                   "per_engine": {m: round(v, 4)
                                                  for m, v in td["per_engine"].items()},
                                   "excluded_engines": sc["excluded_engines"]}})

    corpus = {
        "corpus_version": "tactic-pilot-v1",
        "intervention": "four fact-preserving tactics applied to a screened target",
        "conditions": CONDITIONS,
        "held_out_of_round": [p["prompt_id"] for p in prompts],
        "n_prompts": len(prompts), "n_docs": len(documents),
        "formats": sorted({d["format"] for d in documents}),
        "domains": sorted({d["domain"] for d in documents}),
        "prompts": prompts, "documents": documents,
    }
    blob = json.dumps(corpus, sort_keys=True, separators=(",", ":")).encode()
    corpus["corpus_sha256"] = hashlib.sha256(blob).hexdigest()
    out = OUTDIR / "corpus_tacticpilot.json"
    out.write_text(json.dumps(corpus, indent=2) + "\n")

    print(f"wrote {out.name}  sha256 {corpus['corpus_sha256'][:16]}")
    print(f"{len(prompts)} questions, {len(documents)} documents, "
          f"{len(CONDITIONS)} conditions\n")
    print(f"{'question':<24}{'target':<18}{'baseline':>9}{'headroom':>10}  excludes")
    for p in prompts:
        s_ = p["screen"]
        ex = ", ".join(m.split("/")[1] for m in s_["excluded_engines"]) or "none"
        print(f"  {p['prompt_id']:<22}{p['target_doc_id'].split('__')[-1]:<18}"
              f"{s_['baseline_pooled']:>9.2f}{s_['headroom_movable']:>10.3f}  {ex}")
    print()
    hdr = f"{'target':<34}" + "".join(f"{c[:11]:>13}" for c in CONDITIONS)
    print(hdr); print("-" * len(hdr))
    for fname, runsname, pid, tkey in PILOT:
        d = next(x for x in documents if x["doc_id"] == f"{pid}__{tkey}")
        base = len(d["variants"]["control"].split())
        row = f"{d['doc_id'].split('__')[-1]:<34}"
        for c in CONDITIONS:
            w = len(d["variants"][c].split())
            row += f"{w:>7}{'':>1}{f'{(w/base-1)*100:+.0f}%' if c != 'control' else '   ':>5}"
        print(row)
    print("\n'+%' is length against that target's own control. answer_first is the")
    print("length-neutral arm; the other three add words, which the analysis must report.")


if __name__ == "__main__":
    main()
