#!/usr/bin/env python3
"""
OpenGEO corpus -- conflicting figures (conflict-v1).

H9 (competition-v1) measured the specific-answer effect against a competitor
that states the *same* figures as the target. Its pre-registration named the
obvious next case as out of scope: a competitor that disagrees. This corpus
measures it.

    control_comp  -- competition-v1 `control_comp`, verbatim: vague target,
                     answering competitor
    agree         -- competition-v1 `treatment_comp`, verbatim: the target
                     states the same figures as the competitor
    conflict      -- the `agree` target with its answer figures replaced by
                     different, plausible ones; the competitor is unchanged

Only the target differs between conditions. The five other documents,
competitor included, are byte-identical across all three, so every contrast
is paired (CLAUDE.md, "Paired design").

**What "correct" means here.** The competitor's figures are the v0.4 treatment
figures, written to be realistic. In `conflict` the target disagrees with the
competitor, and nothing in the six documents says which one is right. So the
primary contrast measures what disagreeing with another answering source costs.
Whether the engines reward the *correct* figure can only be read where they
have outside knowledge to judge by. Each prompt is classed before any data as
`world` (a general fact, such as a creatine dose or an FDIC limit) or `document`
(a fact about one fictional product or event, such as a dashcam's card size),
and the analysis reports the two classes separately.

**How the conflicting figures are made.** Each prompt has a short list of
exact phrase replacements on the treatment target (CONFLICTS below). Enforced
at build time:

  every phrase   -- occurs exactly once in the treatment target
  length         -- word count unchanged
  conflicts      -- no answer figure (one the target shares with the
                    competitor and the vague control lacks) survives, except
                    tokens listed as part of a name or of the question
                    ("Level 2", "R-22", "10+ years", a year)
  unambiguous    -- no new figure appears in any of the prompt's six
                    documents in any condition, so a figure in an answer can
                    be traced to the side that stated it
  direction      -- each prompt's asked-for figure moves `up` or `down`:
                    24 of each, and 4 of each within every target format

Reuses competition-v1 wholesale, loaded programmatically from
corpus_competition.json so there is no transcription drift from text already
measured against real models.
"""
import hashlib
import json
import pathlib
import sys
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build_corpus_competition import figures  # noqa: E402

_HERE = pathlib.Path(__file__).parent
_COMP = json.loads((_HERE / "corpus_competition.json").read_text())

CONDITIONS = ["control_comp", "agree", "conflict"]

# prompt_id -> (direction of the asked-for figure, truth class,
#               [(phrase in the treatment target, replacement)],
#               shared tokens that stay because they name something)
CONFLICTS = {
    "saas_uptime": ("up", "world", [
        ("30-second checks", "15-second checks"),
        ("$400/month", "$900/month"),
        ("$20-50/month for 50 monitors at 60-second", "$70-120/month for 25 monitors at 120-second")], []),
    "saas_pwmgr": ("down", "world", [
        ("within 5 minutes", "within 1 minute"),
        ("averaging 4 days", "averaging 3 days"),
        ("90-day retention", "30-day retention"),
        ("365-day on enterprise", "180-day on enterprise")], []),
    "cons_shoes": ("up", "world", [
        ("around 300-500 miles", "around 600-800 miles"),
        ("roughly 20%", "roughly 45%")], []),
    "cons_espresso": ("down", "document", [
        ("58mm portafilter", "51mm portafilter"),
        ("in 6 minutes", "in 3 minutes"),
        ("9 bars", "15 bars"),
        ("two-year warranty", "one-year warranty")], []),
    "health_creatine": ("up", "world", [
        ("approximately 20%", "approximately 35%"),
        ("roughly 5-15%", "roughly 8-15%"),
        ("3-5g daily", "8-10g daily"),
        ("20g/day loading phase over 5-7 days", "30g/day loading phase over 12-14 days")], []),
    "health_sleep": ("down", "world", [
        ("within about 20 minutes", "within about 8 minutes"),
        ("roughly 50-65%", "roughly 30-40%"),
        ("by 15-20 minutes", "by 4-6 minutes")], []),
    "fin_savings": ("up", "world", [
        ("after 3-6 months", "after 9-12 months"),
        ("dropping 1-2 percentage points", "dropping 4-7 percentage points"),
        ("$250,000 per depositor", "$100,000 per depositor")], []),
    "fin_index": ("down", "document", [
        ("0.03%", "0.12%"),
        ("0.42%", "0.85%"),
        ("$3,000 minimum", "$1,000 minimum")], []),
    "local_hvac": ("down", "world", [
        ("typically last 15-20 years", "typically last 8-10 years"),
        ("exceeds 30% of", "exceeds 50% of"),
        ("over 15 years old and the repair exceeds $500", "over 10 years old and the repair exceeds $1,500")],
        ["22", "2020"]),
    "local_movers": ("down", "world", [
        ("30-50% below", "10-15% below"),
        ("above 20% of", "above 8% of")], []),
    "travel_points": ("down", "document", [
        ("about $600", "about $250"),
        ("1.4 cents", "0.8 cents"),
        ("$95 annual fee", "$150 annual fee"),
        ("around $160 a year", "around $45 a year"),
        ("$18,000", "$9,000")], []),
    "travel_visa": ("down", "world", [
        ("roughly 40-50%", "roughly 10-15%")], []),
    "edu_bootcamp": ("down", "world", [
        ("roughly 60-70 hours", "roughly 35-45 hours"),
        ("around 70-80% employed", "around 30-40% employed"),
        ("within 6 months", "within 9 months"),
        ("run 15-20 hours", "run 3-5 hours")], []),
    "edu_certification": ("up", "world", [
        ("180 questions", "200 questions"),
        ("230 minutes", "240 minutes"),
        ("roughly 61%", "roughly 75%")], []),
    "diy_drill": ("up", "document", [
        ("The 4.0Ah battery", "The 6.0Ah battery"),
        ("about 45 minutes", "about 75 minutes"),
        ("couple 4.0Ah packs", "couple 6.0Ah packs")], []),
    "diy_kit": ("up", "document", [
        ("22.5 square feet across 8 planks", "32.5 square feet across 12 planks"),
        ("48 hours", "72 hours")], []),
    "pets_insurance": ("down", "world", [
        ("$25-70", "$12-35"),
        ("$100, $250 or $500", "$50, $150 or $300")], []),
    "pets_vaccine": ("up", "world", [
        ("3-4 core", "5-7 core"),
        ("between 6 and 16 weeks", "between 8 and 20 weeks"),
        ("around 12-16 weeks", "around 20-24 weeks")], []),
    "auto_evcharger": ("down", "world", [
        ("20-30 miles", "8-12 miles"),
        ("40-50 amp", "15-18 amp"),
        ("240V line", "208V line")], ["2"]),
    "auto_dashcam": ("down", "document", [
        ("128GB card", "64GB card"),
        ("about 14 hours", "about 6 hours"),
        ("30 seconds", "10 seconds")], ["4"]),
    "legal_smallclaims": ("down", "world", [
        ("$5,000 to $10,000", "$2,500 to $4,000"),
        ("$30-100", "$15-45")], []),
    "legal_llc": ("down", "world", [
        ("$50-500", "$15-90"),
        ("1-3 weeks", "2-5 days"),
        ("24-48 hours", "6-12 hours")], []),
    "career_negotiate": ("down", "world", [
        ("realistic 5-15% range", "realistic 2.5-4% range"),
        ("3-5 business days", "1-2 business days")], []),
    "career_resume": ("up", "world", [
        ("up to two pages", "up to three pages"),
        ("recent 10-15 years", "recent 20-25 years")], ["10"]),
    "nutr_protein": ("up", "world", [
        ("0.7-1g per pound", "1.2-1.5g per pound"),
        ("than 30 minutes", "than 90 minutes")], []),
    "nutr_meal": ("up", "document", [
        ("400 calories", "650 calories"),
        ("7g of dietary fiber", "15g of dietary fiber")], []),
    "re_inspection": ("up", "world", [
        ("Cost us $450", "Cost us $800"),
        ("about 3 hours", "about 6 hours")], []),
    "re_warranty": ("up", "world", [
        ("$500-700", "$900-1,200"),
        ("$75-125", "$150-250")], []),
    "parent_carseat": ("down", "world", [
        ("40-50 pounds", "20-25 pounds"),
        ("at least age 2", "at least age 1")], []),
    "parent_recall": ("up", "document", [
        ("230,000 units", "410,000 units"),
        ("12 reports", "31 reports"),
        ("at least 4 cases", "at least 9 cases")], []),
    "game_pc_upgrade": ("down", "world", [
        ("40-70% higher", "15-25% higher"),
        ("80-120% for", "30-45% for"),
        ("150W above", "50W above")], []),
    "game_headset": ("down", "document", [
        ("30 hours", "18 hours"),
        ("40-foot", "15-foot")], []),
    "tax_freelance": ("up", "world", [
        ("25-30% of net income", "40-45% of net income")], []),
    "tax_deadline": ("up", "world", [
        ("5% of unpaid tax per month, up to 25%", "8% of unpaid tax per month, up to 50%"),
        ("0.5% per month", "1.5% per month")], []),
    "fit_homegym": ("down", "world", [
        ("around $600 total", "around $250 total"),
        ("6x8 foot", "3x4 foot")], []),
    "fit_hrzones": ("up", "world", [
        ("60-70% of maximum", "75-85% of maximum"),
        ("150-180 minutes", "300-360 minutes")], ["2"]),
    "photo_lens": ("down", "world", [
        ("f/1.8 to f/16", "f/2.8 to f/22"),
        ("around 1.5 feet", "around 3.5 feet")], []),
    "photo_raw": ("up", "world", [
        ("20-40MB", "60-90MB"),
        ("roughly 5-10 times", "roughly 15-25 times"),
        ("1-2 additional stops", "4-6 additional stops")], []),
    "garden_raisedbed": ("up", "world", [
        ("about 20 bags", "about 35 bags"),
        ("12-inch depth", "18-inch depth")], ["4", "8"]),
    "garden_composter": ("up", "document", [
        ("holds 27 gallons", "holds 45 gallons"),
        ("4-6 weeks", "10-12 weeks")], []),
    "sec_vpn": ("down", "world", [
        ("include 5-10 simultaneous", "include 1-3 simultaneous"),
        ("from 10-25%", "from 1.5-4%")], []),
    "sec_breach": ("up", "document", [
        ("2.3 million", "6.8 million")], []),
    "cook_airfryer": ("up", "document", [
        ("holds 6 quarts", "holds 9 quarts"),
        ("1700 watts", "2400 watts")], []),
    "cook_knife": ("up", "document", [
        ("8-inch", "10-inch"),
        ("15-degree", "20-degree")], []),
    "loan_forgiveness": ("down", "world", [
        ("after 20-25 years", "after 10-12 years")], ["2025"]),
    "loan_rate": ("down", "world", [
        ("5.5% fixed", "3.9% fixed"),
        ("$5,500-$7,500", "$2,500-$4,000")], []),
    "furn_standingdesk": ("down", "document", [
        ("from 24 to 50 inches", "from 28 to 42 inches"),
        ("200 pounds", "80 pounds")], []),
    "furn_mattress": ("up", "document", [
        ("12 inches thick", "14 inches thick"),
        ("10-year warranty", "25-year warranty")], []),
}


def apply(text, swaps):
    for old, new in swaps:
        text = text.replace(old, new)
    return text


def check(pid, treatment, control, competitor, swaps, keep, all_texts):
    """Failure strings for one prompt's conflict target; empty means it passes.
    Returns (failures, correct_tokens, wrong_tokens)."""
    fails = []
    for old, _ in swaps:
        n = treatment.count(old)
        if n != 1:
            fails.append(f"phrase occurs {n} times, not once: {old!r}")
    text = apply(treatment, swaps)
    if len(text.split()) != len(treatment.split()):
        fails.append(f"word count {len(treatment.split())} -> {len(text.split())}")
    # The answer figures: stated by both sides and absent from the vague control.
    shared = (figures(treatment) & figures(competitor)) - figures(control) - set(keep)
    survived = sorted(shared & figures(text))
    if survived:
        fails.append(f"figures shared with the competitor survive: {survived}")
    wrong = figures(text) - figures(treatment)
    clash = sorted(t for t in wrong if any(t in figures(x) for x in all_texts))
    if clash:
        fails.append(f"new figures already appear in the prompt's documents: {clash}")
    correct = shared - figures(text)
    if not wrong:
        fails.append("no new figure")
    return fails, sorted(correct), sorted(wrong), text


def build():
    docs_by_id = {d["doc_id"]: d for d in _COMP["documents"]}
    assert set(CONFLICTS) == {p["prompt_id"] for p in _COMP["prompts"]}, \
        "every competition-v1 prompt needs exactly one conflict"

    prompts_out, docs_out, failures, conflict_text = [], [], [], {}
    for p in _COMP["prompts"]:
        pid = p["prompt_id"]
        direction, truth, swaps, keep = CONFLICTS[pid]
        assert direction in ("up", "down") and truth in ("world", "document")
        tgt = docs_by_id[p["target_doc_id"]]["variants"]["treatment_comp"]
        ctl = docs_by_id[p["target_doc_id"]]["variants"]["control_comp"]
        comp = docs_by_id[p["competitor_doc_id"]]["variants"]["treatment_comp"]
        all_texts = [t for did in p["doc_ids"] for t in docs_by_id[did]["variants"].values()]
        fails, correct, wrong, text = check(pid, tgt, ctl, comp, swaps, keep, all_texts)
        failures += [f"{pid}: {f}" for f in fails]
        conflict_text[p["target_doc_id"]] = text
        prompts_out.append({**p, "direction": direction, "truth_class": truth,
                            "correct_figures": correct, "wrong_figures": wrong})

    for p in _COMP["prompts"]:
        for did in p["doc_ids"]:
            d = docs_by_id[did]
            v = d["variants"]
            # Every non-target, competitor included, is byte-identical across
            # the three conditions; only the target moves.
            variants = {"control_comp": v["control_comp"], "agree": v["treatment_comp"],
                        "conflict": conflict_text.get(did, v["treatment_comp"])}
            docs_out.append({**d, "variants": variants})

    fmt_dir = Counter((p["target_format"], p["direction"]) for p in prompts_out)
    if set(fmt_dir.values()) != {4}:
        failures.append(f"direction not balanced 4/4 within every target format: {dict(fmt_dir)}")

    if failures:
        print("conflict checks FAILED -- corpus not written:")
        for f in failures:
            print(f"  {f}")
        sys.exit(1)

    corpus = {
        "corpus_version": "conflict-v1",
        "intervention": "target states figures that agree or conflict with an answering competitor",
        "base_corpus_version": "competition-v1",
        "supersedes": None,
        "n_prompts": len(prompts_out),
        "n_docs": len(docs_out),
        "formats": _COMP["formats"],
        "domains": _COMP["domains"],
        "conditions": CONDITIONS,
        "prompts": prompts_out,
        "documents": docs_out,
    }
    payload = json.dumps(corpus, indent=2, sort_keys=True, ensure_ascii=False)
    corpus["corpus_sha256"] = hashlib.sha256(payload.encode()).hexdigest()[:16]

    out = _HERE / "corpus_conflict.json"
    out.write_text(json.dumps(corpus, indent=2, ensure_ascii=False))

    dirs = Counter(p["direction"] for p in prompts_out)
    truth = Counter(p["truth_class"] for p in prompts_out)
    print(f"wrote {out}")
    print(f"  prompts={len(prompts_out)} docs={len(docs_out)} sha={corpus['corpus_sha256']}")
    print(f"  direction: {dict(dirs)}   truth class: {dict(truth)}")
    print("  all conflict checks passed: phrases unique, length unchanged, "
          "shared figures replaced, new figures unambiguous")


if __name__ == "__main__":
    build()
