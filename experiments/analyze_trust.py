#!/usr/bin/env python3
"""
OpenGEO -- analysis for the trust-signals round (H10-H12).

Everything here follows the analysis plan in
`preregistrations/2026-11-trust.md`:

  primary      target CPR (METHODOLOGY.md A1)
  H10          fresh - stale    a recent date beats an old one   (predicted +)
  H11          byline - control a credentialed author helps       (predicted +)
  H12          promo - control  promotional superlatives hurt     (predicted -)
               Holm across the three. Each is SUPPORTED only if its share-
               weighted 95% CI excludes zero on the predicted side AND its
               Holm-adjusted permutation p is below 0.05.
  secondary    H10a stale - control (predicted -)
               H10b fresh - control (two-sided)
               H11a byline - promo  (two-sided: the same seven words, one
                    claiming expertise, one claiming quality)
               Holm across the three
  pairing      per (prompt, model)
  inference    bootstrap over prompts, 10,000 resamples, percentile CIs;
               sign-flip permutation on per-prompt deltas
  exclusions   any model above 10% no-cite, reported separately

The echo reading is descriptive: in each arm, the share of answers that repeat
the signal (the year, the author's surname, a promotional marker), read
mechanically from the answer text with no model judge. The control arm gives
its false-positive rate, since no control document carries any of them.

    python3 analyze_trust.py --runs results/runs_trust.jsonl
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
CONDITIONS = ["control", "fresh", "stale", "byline", "promo"]
NO_CITE_LIMIT = 0.10
PINNED = 0.02          # an engine whose control CPR is within this of 0 or 1 reports a bound

# (label, fn, predicted sign: +1, -1 or 0 for two-sided)
PRIMARY = [
    ("H10 fresh - stale", lambda d: d["fresh"] - d["stale"], +1),
    ("H11 byline - control", lambda d: d["byline"] - d["control"], +1),
    ("H12 promo - control", lambda d: d["promo"] - d["control"], -1),
]
SECONDARY = [
    ("H10a stale - control", lambda d: d["stale"] - d["control"], -1),
    ("H10b fresh - control", lambda d: d["fresh"] - d["control"], 0),
    ("H11a byline - promo", lambda d: d["byline"] - d["promo"], 0),
]


# ----------------------------------------------------------------- echo ----

def echo_patterns(corpus):
    """prompt_id -> {condition: compiled regex for that arm's signal}."""
    yrs = corpus["years"]
    promo = re.compile("|".join(re.escape(m) for m in corpus["promo_markers"]), re.I)
    out = {}
    for p in corpus["prompts"]:
        out[p["prompt_id"]] = {
            "fresh": re.compile(rf"\b{yrs['fresh']}\b"),
            "stale": re.compile(rf"\b{yrs['stale']}\b"),
            "byline": re.compile(rf"\b{re.escape(p['author_surname'])}\b"),
            "promo": promo,
        }
    return out


def echoes(r, pats, signal):
    return bool(pats[r["prompt_id"]][signal].search(r.get("response_text") or ""))


# ------------------------------------------------------------------ main ----

def cell_means(rows, models):
    acc = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r["model"] in models:
            acc[(r["prompt_id"], r["model"])][r["condition"]].append(1.0 if r["target_cited"] else 0.0)
    return {k: {c: float(np.mean(v)) for c, v in d.items()} for k, d in acc.items()}


def verdict(d, lo, hi, hp, sign):
    if sign == 0:
        return "two-sided: " + ("CI excludes zero" if not lo <= 0 <= hi else "CI includes zero")
    side_ok = lo > 0 if sign > 0 else hi < 0
    if side_ok and hp < 0.05:
        return "SUPPORTED"
    if (sign > 0 and hi < 0) or (sign < 0 and lo > 0):
        return "FALSIFIED -- significant in the opposite direction"
    return "FALSIFIED (not supported)"


def family(cpr, fam, w, args, decide):
    res = [(label,) + summarise(contrast(cpr, fn, w), args)[:4] + (sign,) for label, fn, sign in fam]
    print(f"{'contrast':<26}{'delta':>9}{'95% CI':>22}{'perm p':>9}{'Holm':>8}   decision")
    for (label, d, lo, hi, p, sign), hp in zip(res, holm([x[4] for x in res])):
        v = verdict(d, lo, hi, hp, sign) if decide else ""
        print(f"  {label:<24}{d:+9.4f}{f'[{lo:+.4f}, {hi:+.4f}]':>22}{p:9.4f}{hp:8.4f}   {v}")
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="results/runs_trust.jsonl")
    ap.add_argument("--corpus", default=str(HERE / "corpus" / "corpus_trust.json"))
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--perm", type=int, default=20000)
    args = ap.parse_args(argv)

    corpus = json.loads(pathlib.Path(args.corpus).read_text())
    pats = echo_patterns(corpus)

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
    mismatch = sum(1 for r in rows
                   if r.get("model_returned") and r["model_returned"] != r["model"])
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
    w = weights(keep)
    flat = {m: 1.0 for m in keep}
    print(f"\npanel covers {coverage(keep):.1%} of measured gen-AI traffic")

    hdr("DESCRIPTIVE -- target CPR by condition, all included engines")
    print(f"{'condition':<12}{'CPR':>8}{'95% Wilson':>18}{'runs':>8}")
    for c in CONDITIONS:
        sub = [r for r in rows if r["condition"] == c]
        if sub:
            k, n = sum(r["target_cited"] for r in sub), len(sub)
            lo, hi = wilson(k, n)
            print(f"  {c:<10}{k / n:8.3f}{f'[{lo:.3f}, {hi:.3f}]':>18}{n:8d}")

    cpr = cell_means(rows, keep)
    vals = [d["control"] for d in cpr.values() if "control" in d]
    pinned = sum(v <= PINNED or v >= 1 - PINNED for v in vals)
    print(f"\n(prompt, engine) cells with control pinned at a boundary: {pinned} of {len(vals)}")

    hdr("PRIMARY -- H10, H11, H12, Holm across the three")
    for label, ww in (("share-weighted (decision)", w), ("unweighted", flat)):
        print(f"\n{label}")
        family(cpr, PRIMARY, ww, args, decide=label.startswith("share"))

    hdr("PER ENGINE (primary; weights not involved), Holm across five engines per hypothesis")
    for label, fn, _ in PRIMARY:
        print(f"\n{label}")
        print(f"{'model':<32}{'control':>9}{'delta':>9}{'95% CI':>22}{'p':>8}{'Holm':>8}")
        per = []
        for m in keep:
            cm = {k: v for k, v in cpr.items() if k[1] == m}
            base = contrast(cm, lambda x: x["control"], {m: 1.0}).mean()
            per.append((m, base) + summarise(contrast(cm, fn, {m: 1.0}), args)[:4])
        for (m, base, d, lo, hi, p), hp in zip(per, holm([e[5] for e in per])):
            flag = "  bound (control pinned)" if base <= PINNED or base >= 1 - PINNED else ""
            print(f"  {m:<30}{base:9.3f}{d:+9.3f}{f'[{lo:+.3f}, {hi:+.3f}]':>22}{p:8.4f}{hp:8.4f}"
                  f"{'*' if hp < 0.05 else ' '}{flag}")

    hdr("SECONDARY -- H10a, H10b, H11a, Holm across the three, share-weighted")
    family(cpr, SECONDARY, w, args, decide=True)

    hdr("ECHO (descriptive) -- share of answers that repeat each arm's signal")
    print("The control column is the reader's false-positive rate: no control document")
    print("carries any of these tokens.\n")
    print(f"{'signal':<10}{'in its arm':>12}{'95% Wilson':>18}{'in control':>12}"
          f"{'when target cited':>20}")
    for sig in CONDITIONS[1:]:
        arm = [r for r in rows if r["condition"] == sig]
        ctl = [r for r in rows if r["condition"] == "control"]
        cited = [r for r in arm if r["target_cited"]]
        if not arm:
            continue
        k = sum(echoes(r, pats, sig) for r in arm)
        lo, hi = wilson(k, len(arm))
        fp = np.mean([echoes(r, pats, sig) for r in ctl]) if ctl else float("nan")
        ec = np.mean([echoes(r, pats, sig) for r in cited]) if cited else float("nan")
        print(f"  {sig:<8}{k / len(arm):12.3f}{f'[{lo:.3f}, {hi:.3f}]':>18}{fp:12.3f}{ec:20.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
