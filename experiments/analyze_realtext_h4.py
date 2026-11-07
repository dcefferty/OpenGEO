#!/usr/bin/env python3
"""
OpenGEO -- analysis for the real-text H4 round.

Everything here follows the analysis plan in
`preregistrations/2026-11-realtext-h4.md`:

  primary      target CPR (METHODOLOGY.md A1)
  H4-RT        treatment - control: stating the answer, in one sentence inserted
               into a verbatim federal page, raises that page's citation rate
               (predicted +). SUPPORTED only if the share-weighted 95% CI excludes
               zero on the positive side AND the permutation p is below 0.05.
  per engine   primary, Holm across the five engines; an engine whose control CPR
               is within 0.02 of 0 or 1 reports a bound, not an estimate
  secondary    H4-RT-b displacement: mean CPR of the five unchanged documents,
               treatment - control (two-sided)
  descriptive  control-arm CPR -- the quantity of interest alongside the delta,
               because the treatment arm is expected to saturate and the delta is
               then mechanically 1 - control (design note); cites per answer by arm;
               answer echo by arm
  pairing      per (prompt, model). Deltas are taken within each cell, weighted
               across models within a prompt; prompts are the resampling unit
  inference    bootstrap over prompts, 10,000 resamples, percentile CIs; sign-flip
               permutation on per-prompt deltas, 20,000 permutations
  exclusions   any model above 10% no-cite, reported separately. No prompt
               exclusions.

Answer echo is read mechanically: the share of answers matching the question's
`answer_pattern` from the corpus, no model judge. In the control arm no document
carries a match (the builder guarantees it), so the control column is the rate at
which engines state the answer from their own knowledge.

    python3 analyze_realtext_h4.py --runs results/runs_realtext_h4.jsonl
"""
import argparse
import json
import pathlib
import re
import sys
from collections import defaultdict

import numpy as np

from analyze import cell_key, report_incomplete, wilson
from analyze_competition import contrast, hdr, holm, load, summarise
from engine_weights import coverage, weights

HERE = pathlib.Path(__file__).parent
CONDITIONS = ["control", "treatment"]
NO_CITE_LIMIT = 0.10
PINNED = 0.02


def cells(rows, models, others):
    """(prompt, model) -> {condition: target CPR, condition+'_others': mean CPR of the
    five unchanged documents}."""
    acc = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r["model"] not in models:
            continue
        k = (r["prompt_id"], r["model"])
        c = r["condition"]
        acc[k][c].append(1.0 if r["target_cited"] else 0.0)
        ids = others[r["prompt_id"]]
        acc[k][c + "_others"].append(sum(d in r["cited_doc_ids"] for d in ids) / len(ids))
    return {k: {c: float(np.mean(v)) for c, v in d.items()} for k, d in acc.items()}


def verdict(lo, hi, hp):
    if lo > 0 and hp < 0.05:
        return "SUPPORTED"
    if hi < 0:
        return "FALSIFIED -- significant in the opposite direction"
    return "FALSIFIED (not supported)"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="results/runs_realtext_h4.jsonl")
    ap.add_argument("--corpus", default=str(HERE / "corpus" / "corpus_realtext_h4.json"))
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--perm", type=int, default=20000)
    args = ap.parse_args(argv)

    corpus = json.loads(pathlib.Path(args.corpus).read_text())
    pats = {p["prompt_id"]: re.compile(p["answer_pattern"], re.I) for p in corpus["prompts"]}
    others = {p["prompt_id"]: [d for d in p["doc_ids"] if d != p["target_doc_id"]]
              for p in corpus["prompts"]}

    rows, errs = load(args.runs)
    if not rows:
        sys.exit("no successful runs to analyse")
    versions = {r["corpus_version"] for r in rows}
    if versions != {corpus["corpus_version"]}:
        sys.exit(f"runs are from corpus {sorted(versions)}, not {corpus['corpus_version']}")

    hdr("DATA HEALTH")
    print(f"usable runs {len(rows):,}   errored {errs}")
    drop = report_incomplete(rows)
    if drop:
        rows = [r for r in rows if cell_key(r) not in drop]
        print(f"  analysing {len(rows):,} runs from complete-enough cells")
    mismatch = sum(1 for r in rows if r.get("model_returned") and r["model_returned"] != r["model"])
    print(f"model_returned mismatches: {mismatch}")
    print(f"\n{'model':<34}{'no-cite':>9}{'runs':>8}   status")
    keep = []
    for m in sorted({r["model"] for r in rows}):
        sub = [r for r in rows if r["model"] == m]
        nc = sum(1 for r in sub if not r["cited_doc_ids"]) / len(sub)
        if nc <= NO_CITE_LIMIT:
            keep.append(m)
        print(f"  {m:<32}{nc:8.1%}{len(sub):8d}   "
              f"{'included' if nc <= NO_CITE_LIMIT else 'EXCLUDED (>10%)'}")
    if not keep:
        sys.exit("every model failed data health")
    rows = [r for r in rows if r["model"] in keep]
    w, flat = weights(keep), {m: 1.0 for m in keep}
    print(f"\npanel covers {coverage(keep):.1%} of measured gen-AI traffic")

    hdr("DESCRIPTIVE -- target CPR and cites per answer by condition, all included engines")
    print(f"{'condition':<12}{'CPR':>8}{'95% Wilson':>18}{'runs':>8}{'cites/ans':>11}")
    for c in CONDITIONS:
        sub = [r for r in rows if r["condition"] == c]
        if sub:
            k, n = sum(r["target_cited"] for r in sub), len(sub)
            lo, hi = wilson(k, n)
            cpa = np.mean([len(r["cited_doc_ids"]) for r in sub])
            print(f"  {c:<10}{k / n:8.3f}{f'[{lo:.3f}, {hi:.3f}]':>18}{n:8d}{cpa:11.2f}")

    cpr = cells(rows, keep, others)
    for label, ww in (("share-weighted", w), ("unweighted", flat)):
        base = contrast(cpr, lambda d: d["control"], ww)
        trt = contrast(cpr, lambda d: d["treatment"], ww)
        print(f"\ncontrol baseline, {label}: {base.mean():.3f}   treatment: {trt.mean():.3f}"
              f"   headroom 1 - control: {1 - base.mean():.3f}")
    vals = [d["control"] for d in cpr.values() if "control" in d]
    pinned = sum(v <= PINNED or v >= 1 - PINNED for v in vals)
    sat = sum(d.get("treatment", 0) >= 1 - PINNED for d in cpr.values())
    print(f"(prompt, engine) cells with control pinned at a boundary: {pinned} of {len(vals)}")
    print(f"(prompt, engine) cells with treatment saturated (>= 0.98): {sat} of {len(cpr)}")
    if sat > len(cpr) / 2:
        print("  Most treatment cells are saturated: the delta is a FLOOR on the effect, not an "
              "estimate (METHODOLOGY.md section 9).")

    hdr("PRIMARY -- H4-RT, treatment - control")
    print(f"{'pool':<28}{'delta':>9}{'95% CI':>22}{'perm p':>9}{'prompts':>9}   decision")
    for label, ww in (("share-weighted (decision)", w), ("unweighted", flat)):
        d, lo, hi, p, n = summarise(contrast(cpr, lambda x: x["treatment"] - x["control"], ww), args)
        v = verdict(lo, hi, p) if label.startswith("share") else ""
        print(f"  {label:<26}{d:+9.4f}{f'[{lo:+.4f}, {hi:+.4f}]':>22}{p:9.4f}{n:9d}   {v}")
    if len(corpus["prompts"]) < 25:
        print(f"\n  {len(corpus['prompts'])} prompts is below the 25-prompt floor (METHODOLOGY.md "
              "section 5.2): report as an interval, not a published effect size.")

    hdr("PER ENGINE (primary; weights not involved), Holm across engines")
    print(f"{'model':<32}{'control':>9}{'treat':>8}{'delta':>9}{'95% CI':>22}{'p':>8}{'Holm':>8}")
    per = []
    for m in keep:
        cm = {k: v for k, v in cpr.items() if k[1] == m}
        b = contrast(cm, lambda x: x["control"], {m: 1.0}).mean()
        t = contrast(cm, lambda x: x["treatment"], {m: 1.0}).mean()
        per.append((m, b, t) + summarise(contrast(cm, lambda x: x["treatment"] - x["control"],
                                                  {m: 1.0}), args)[:4])
    for (m, b, t, d, lo, hi, p), hp in zip(per, holm([e[6] for e in per])):
        flag = "  bound (control pinned)" if b <= PINNED or b >= 1 - PINNED else ""
        print(f"  {m:<30}{b:9.3f}{t:8.3f}{d:+9.3f}{f'[{lo:+.3f}, {hi:+.3f}]':>22}{p:8.4f}{hp:8.4f}"
              f"{'*' if hp < 0.05 else ' '}{flag}")

    hdr("SECONDARY -- H4-RT-b displacement of the five unchanged documents (two-sided)")
    d, lo, hi, p, n = summarise(
        contrast(cpr, lambda x: x["treatment_others"] - x["control_others"], w), args)
    print(f"  share-weighted  {d:+.4f}  [{lo:+.4f}, {hi:+.4f}]  perm p {p:.4f}  "
          f"({'CI excludes zero' if not lo <= 0 <= hi else 'CI includes zero'})")

    hdr("ANSWER ECHO (descriptive) -- share of answers matching the question's answer pattern")
    print("No control-arm document matches; the control column is the engines' own knowledge.\n")
    print(f"{'condition':<12}{'echo':>8}{'95% Wilson':>18}{'when target cited':>20}")
    for c in CONDITIONS:
        sub = [r for r in rows if r["condition"] == c]
        if not sub:
            continue
        hits = [bool(pats[r["prompt_id"]].search(r.get("response_text") or "")) for r in sub]
        k = sum(hits)
        lo, hi = wilson(k, len(sub))
        cited = [h for h, r in zip(hits, sub) if r["target_cited"]]
        print(f"  {c:<10}{k / len(sub):8.3f}{f'[{lo:.3f}, {hi:.3f}]':>18}"
              f"{(np.mean(cited) if cited else float('nan')):20.3f}")
    print("\nper question, control-arm echo (high = the answer is common knowledge to the engines):")
    for p in corpus["prompts"]:
        sub = [r for r in rows if r["condition"] == "control" and r["prompt_id"] == p["prompt_id"]]
        if sub:
            e = np.mean([bool(pats[p["prompt_id"]].search(r.get("response_text") or "")) for r in sub])
            print(f"  {p['prompt_id']:<32}{e:6.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
