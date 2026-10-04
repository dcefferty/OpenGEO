#!/usr/bin/env python3
"""
OpenGEO -- page-length screening probe for ROADMAP item 11.

The tactic pilot and the length ladder both ran on a corpus of 12-104 word snippets with
one longer target. Both found the same thing: usable cells are lost to saturation, because
the inclusive engines cite a strong answer almost always. The length ladder's phase-1
deviation named the cause -- a target that contains the answer is conspicuous against a
field of snippets -- and could not fix it by lengthening the target alone.

This probe changes the field instead. **Every** document is a 250-460 word page section,
which is closer to what an answer engine actually synthesises from: real retrieval returns
pages, not sentences. The question is narrow and prior to any tactic:

    does a page-length candidate field sit at usable citation rates, or does it saturate?

It is a screening run -- control text only, no tactic arms. If the field unpins, the
page-length rebuild is justified and item 11 has a route forward. If every document
saturates, that is the probe-2 failure mode arriving from the other direction, and item 11
is finished in Tier 1.

## Risk, stated in advance

Longer candidates answer more completely. "Every document fully answers" is exactly what
gave probe 2 zero usable targets out of ten. Against that, a page-length field may cause
engines to cite *fewer* documents per answer -- two or three suffice instead of five --
which would push per-document rates down and unpin the field. Which force wins is the
empirical question, and the honest prior is near even.

## Questions

All three are already held out of the round by the pilot or the ladder, so this probe
costs no new corpus.

  finance_housingshare   8 candidates
  health_bloodpressure   8 candidates  (7 kept + cdc_hbp, newly sourced)
  home_smokealarm        7 candidates  -- see the deviation below

Documents dropped because their source page has no 250-word run at all:
`hud_dti_archive` (160w of prose), `usfa_prepare` (50w), `nhlbi_stress` (144w).

**Deviation: `home_smokealarm` runs at 7 candidates, below the 8+ rule (ROADMAP item 11,
2026-09-17).** Replacements could not be sourced: cpsc.gov returns HTTP 403 to automated
fetching, cdc.gov/fire-safety likewise, the Internet Archive CDX index is returning
HTTP 0, and NFPA is not a federal work. The deviation is **conservative for this probe's
hypothesis**: the 8+ rule exists because 4-6 candidates pin everything, so 7 biases toward
saturation. If the field unpins at 7 the result is robust; if it does not, 8 might have.

## Span selection

Each document is a contiguous run of its committed snapshot, sliced by `sources.py:span()`
with `multi_block=True` so a run may include the headings a real page section contains.
Anchors are frozen below rather than computed at build time, so a source page changing
under the corpus fails the build instead of silently moving the text.

Spans were chosen mechanically, and the rule matters: among runs of 250-600 words that
mention the question's terms, take the **earliest** on the page -- not the best-matching.
Selecting each page's most answer-like passage would manufacture the very saturation this
probe exists to detect. Site furniture (archive banners, "NIH is moving the launch of its
new website", Census navigation, tag lists) is excluded by pattern.

    python3 corpus/build_corpus_pagelength.py
"""
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import sources as S  # noqa: E402

SCREEN_CORPORA = ["corpus_rankable_screen_b1.json", "corpus_rankable_screen_b6.json",
                  "corpus_rankable_screen_b8.json"]

# Newly sourced for this probe; every other document reuses its screen-corpus metadata.
NEW = {
    "health_bloodpressure__cdc_hbp": {
        "agency": "CDC", "title": "About High Blood Pressure",
        "url": "https://www.cdc.gov/high-blood-pressure/about/index.html",
        "rights": "US federal work (CDC), 17 U.S.C. 105",
        "rights_evidence": "cdc.gov, HHS operating division; page carries no third-party "
                           "credit and does not trip the A.D.A.M. licensing guard",
        "format": "docs", "domain": "health", "answers": "direct",
    },
}

# (doc key, start anchor, end anchor). Frozen from the mechanical proposal described above.
SPANS = {
    "finance_housingshare": [
        ("huduser_chas", 'The primary purpose of the CHAS data is to', 'thousands of states, counties, cities, and neighborhoods.'),
        ("census_2024", 'SEPT. 12, 2024 – Over 21 million renter households', 'or More Races, or Hispanic renter households.'),
        ("census_19m", 'DEC. 8, 2022 — Over 40% (19 million) of', 'household income higher than the national median.'),
        ("census_lowinc", 'The pandemic began in the United States following a', 'United States were cost burdened in 2021.'),
        ("census_story22", 'Over 19 million U.S. renter households spent more than', 'had lower overall housing costs than renters.'),
        ("cfpb_qm_blog", 'If you’re looking to buy a home in 2014,', 'somewhat higher for loan amounts under $100,000.'),
        ("cfpb_qm_press", 'WASHINGTON, D.C. — Today, the Consumer Financial Protection Bureau', 'could impair access to responsible, affordable credit.'),
        ("cfpb_dti", 'Your debt-to-income ratio (DTI) is all your monthly debt', 'financial products are transparent, fair, and competitive.'),
    ],
    "home_smokealarm": [
        ("usfa_alarms", 'Installing smoke alarms in every bedroom, outside each separate', "department's nonemergency phone number for more information."),
        ("cpsc_2023b", 'WASHINGTON, D.C. – As the season changes, consumers should', 'is clean before or after each use.'),
        ("cpsc_2015", 'WASHINGTON, D.C. – Fall is a good time of', 'inside each bedroom, and outside sleeping areas.'),
        ("ready_fires", 'A fire can become life-threatening in just two minutes.', 'inventory and contacting fire damage restoration companies.'),
        ("cpsc_2023a", 'WASHINGTON, D.C. – Daylight Saving Time ends on Sunday,', 'Centers for Disease Control and Prevention (CDC).'),
        ("cpsc_2004", 'This is Fire Prevention Week (October 5-11), but the', 'in waking children and alerting older people.'),
        ("cpsc_blog", 'Consumers will turn their clocks back one hour when', 'they are more than 10 years old.'),
    ],
    "health_bloodpressure": [
        ("fda_bp", 'Nearly half, more than 119 million, American adults have', 'yet considered to have high blood pressure.'),
        ("nhlbi_hbp", 'High blood pressure, or hypertension, is a common condition', 'readings of 80 mm Hg or higher.'),
        ("nhlbi_diag", 'Everyone who’s age 3 or older should have their', 'from the office and from other places.'),
        ("nia_bp", 'High blood pressure, or hypertension, is a major health', 'your heart relaxes and fills with blood.'),
        ("niddk_bp", 'Blood pressure is the force of blood pushing against', 'after diabetes, as illustrated in Figure 1.2'),
        ("nhlbi_sym", 'It is important to check your blood pressure readings', 'brain, kidneys, or legs, arms, or pelvis.'),
        ("nhlbi_causes", 'Many factors raise your risk of high blood pressure.', 'clinical and population science, implementation, and translational.'),
        ("cdc_hbp", 'High blood pressure typically has no signs or symptoms', 'pressure levels and comparing them to guidelines.'),
    ],
}


def main():
    src_by_prompt = {}
    for fname in SCREEN_CORPORA:
        c = json.load(open(HERE / fname))
        byid = {d["doc_id"]: d for d in c["documents"]}
        for p in c["prompts"]:
            if p["prompt_id"] in SPANS:
                src_by_prompt[p["prompt_id"]] = (p, byid, c["corpus_version"])

    documents, prompts, report = [], [], []
    for pid, spans in SPANS.items():
        prompt, byid, ver = src_by_prompt[pid]
        ids = []
        for key, start, end in spans:
            did = f"{pid}__{key}"
            meta = NEW.get(did)
            if meta is None:
                d = byid[did]
                url, source = d["source"]["url"], dict(d["source"])
                fmt, domain, answers = d["format"], d["domain"], d.get("answers")
            else:
                url = meta["url"]
                source = {k: meta[k] for k in
                          ("agency", "title", "url", "rights", "rights_evidence")}
                fmt, domain, answers = meta["format"], meta["domain"], meta["answers"]

            text = S.span(url, start, end, multi_block=True)
            snap = S.load(url)
            ok, missing = S.verbatim(text, snap["text"])
            if not ok:
                raise AssertionError(f"{did}: not verbatim -- {missing[:1]}")
            source.update(snapshot_sha256=snap["text_sha256"],
                          retrieved_utc=snap["retrieved_utc"], method=snap["method"])
            documents.append({
                "doc_id": did, "prompt_id": pid, "format": fmt, "domain": domain,
                "is_target": False,  # the screen picks the target; none is nominated
                "source": source, "answers": answers,
                "words": len(text.split()),
                "variants": {"control": text},
            })
            ids.append(did)

        prompts.append({"prompt_id": pid, "domain": documents[-1]["domain"],
                        "question": prompt["question"], "doc_ids": ids,
                        "target_doc_id": ids[0], "target_format": documents[-1]["format"],
                        "source_corpus": ver})
        w = [d["words"] for d in documents if d["prompt_id"] == pid]
        report.append((pid, len(ids), min(w), max(w), sum(w)))

    corpus = {
        "corpus_version": "pagelength-screen-v1",
        "intervention": "none -- screening run: does a page-length field saturate?",
        "conditions": ["control"],
        "held_out_of_round": sorted(SPANS),
        "n_prompts": len(prompts), "n_docs": len(documents),
        "formats": sorted({d["format"] for d in documents}),
        "domains": sorted({d["domain"] for d in documents}),
        "prompts": prompts, "documents": documents,
    }
    blob = json.dumps(corpus, sort_keys=True, separators=(",", ":")).encode()
    corpus["corpus_sha256"] = hashlib.sha256(blob).hexdigest()
    out = HERE / "corpus_pagelength.json"
    out.write_text(json.dumps(corpus, indent=2) + "\n")

    print(f"wrote {out.name}  sha256 {corpus['corpus_sha256'][:16]}")
    print(f"{len(prompts)} questions, {len(documents)} documents, control only\n")
    print(f"{'question':<24}{'cand':>5}{'words/doc':>14}{'context':>10}")
    print("-" * 56)
    for pid, n, lo, hi, tot in report:
        flag = "  < 8, deviation logged" if n < 8 else ""
        print(f"{pid:<24}{n:>5}{f'{lo}-{hi}':>14}{tot:>9}w{flag}")
    prev = 843
    print(f"\nPrior corpora ran ~{prev} input tokens per call; these contexts are roughly "
          f"{int(sum(r[4] for r in report) / len(report) * 1.33):,} tokens.")


if __name__ == "__main__":
    main()
