#!/usr/bin/env python3
"""
OpenGEO -- analysis for the conflicting-figures round (H13).

Everything here follows the analysis plan in
`preregistrations/2026-11-conflict.md`:

  primary      target CPR (METHODOLOGY.md A1)
  H13          agree - conflict, share-weighted pooled delta; falsified if its
               95% CI includes zero
  secondary    H13a conflict - control_comp (a disagreeing figure vs no figure)
               H13b competitor CPR, conflict - agree
               H13c adoption: in `conflict` answers that state one side's
                    figure, the share that state the competitor's, against 0.5
               H13d H13 in `world` prompts minus H13 in `document` prompts
               Holm across the four
  pairing      per (prompt, model)
  inference    bootstrap over prompts, 10,000 resamples, percentile CIs;
               sign-flip permutation on per-prompt deltas (label permutation
               for H13d, whose two groups are different prompts)
  exclusions   any model above 10% no-cite, reported separately

Adoption is read mechanically from the answer text. A figure counts for a side
only if it is *distinctive*: not in the question and not a single-digit whole
number, which answers quote for other reasons. A prompt with no distinctive
figure on either side is left out of H13c, and the analyser says which.
`--validate-extractor` runs the same reader over a finished competition-v1
file, where the target never states a conflicting figure, to measure how often
it reports one that is not there.

    python3 analyze_conflict.py --runs results/runs_conflict.jsonl
    python3 analyze_conflict.py --validate-extractor results/runs_competition.jsonl
"""
import argparse
import json
import pathlib
import sys
from collections import Counter, defaultdict

import numpy as np

from analyze import cell_key, report_incomplete, wilson
from analyze_competition import boot_ci, contrast, hdr, holm, load, perm_p, summarise
from corpus.build_corpus_competition import figures
from engine_weights import coverage, weights

HERE = pathlib.Path(__file__).parent
CONDITIONS = ["control_comp", "agree", "conflict"]
NO_CITE_LIMIT = 0.10
SATURATED = 0.98

H13 = lambda d: d["agree"] - d["conflict"]
H13A = lambda d: d["conflict"] - d["control_comp"]
H13B = lambda d: d["conflict"] - d["agree"]


# ------------------------------------------------------------- adoption ----

def distinctive(tokens, question):
    q = figures(question)
    return {t for t in tokens if t not in q and not (t.isdigit() and int(t) < 10)}


def sides(corpus):
    """prompt_id -> (distinctive correct figures, distinctive wrong figures)."""
    return {p["prompt_id"]: (distinctive(p["correct_figures"], p["question"]),
                             distinctive(p["wrong_figures"], p["question"]))
            for p in corpus["prompts"]}


def adoption(text, correct, wrong):
    """'correct', 'wrong', 'both' or 'neither': which side's figures the answer states."""
    f = figures(text or "")
    c, w = bool(f & correct), bool(f & wrong)
    return "both" if c and w else "correct" if c else "wrong" if w else "neither"


def validate_extractor(path, corpus):
    """False-positive rate of the reader on answers where no conflicting figure exists."""
    S = sides(corpus)
    rows, _ = load(path)
    hdr(f"EXTRACTOR VALIDATION on {path}")
    print("competition-v1 never shows a conflicting figure, so any 'wrong' reading is a")
    print("false positive. treatment_comp is this round's `agree` text, byte for byte.\n")
    print(f"{'condition':<16}{'runs':>7}{'correct':>9}{'wrong':>8}{'both':>7}{'neither':>9}"
          f"{'false +':>9}{'95% Wilson':>18}")
    for cond in ("control_comp", "treatment_comp"):
        sub = [r for r in rows if r["condition"] == cond and all(S[r["prompt_id"]])]
        k = Counter(adoption(r.get("response_text"), *S[r["prompt_id"]]) for r in sub)
        fp = k["wrong"] + k["both"]
        lo, hi = wilson(fp, len(sub))
        print(f"  {cond:<14}{len(sub):7d}{k['correct']:9d}{k['wrong']:8d}{k['both']:7d}"
              f"{k['neither']:9d}{fp / len(sub):9.2%}{f'[{lo:.2%}, {hi:.2%}]':>18}")
    return 0


# ------------------------------------------------------------------ main ----

def competitor_cpr(r, comp):
    return 1.0 if comp[r["prompt_id"]] in r["cited_doc_ids"] else 0.0


def cell_means(rows, metric, comp, models):
    acc = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r["model"] in models:
            acc[(r["prompt_id"], r["model"])][r["condition"]].append(metric(r, comp))
    return {k: {c: float(np.mean(v)) for c, v in d.items()} for k, d in acc.items()}


def adoption_share(rows, S, w):
    """Per-prompt share-weighted share of decided `conflict` answers that use the
    competitor's figure. Engines with no decided answer on a prompt drop out of
    that prompt's weighting."""
    acc = defaultdict(lambda: defaultdict(Counter))
    for r in rows:
        if r["condition"] == "conflict" and all(S[r["prompt_id"]]):
            acc[r["prompt_id"]][r["model"]][adoption(r.get("response_text"), *S[r["prompt_id"]])] += 1
    out = {}
    for p, per in acc.items():
        num = den = 0.0
        for m, k in per.items():
            decided = k["correct"] + k["wrong"]
            if decided:
                num += w.get(m, 0) * k["correct"] / decided
                den += w.get(m, 0)
        if den:
            out[p] = num / den
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="results/runs_conflict.jsonl")
    ap.add_argument("--corpus", default=str(HERE / "corpus" / "corpus_conflict.json"))
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--perm", type=int, default=20000)
    ap.add_argument("--validate-extractor", metavar="RUNS",
                    help="measure the adoption reader's false-positive rate on a competition-v1 file")
    args = ap.parse_args(argv)

    corpus = json.loads(pathlib.Path(args.corpus).read_text())
    if args.validate_extractor:
        return validate_extractor(args.validate_extractor, corpus)

    comp = {p["prompt_id"]: p["competitor_doc_id"] for p in corpus["prompts"]}
    truth = {p["prompt_id"]: p["truth_class"] for p in corpus["prompts"]}
    S = sides(corpus)

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

    hdr("DESCRIPTIVE -- by condition, all included engines")
    print(f"{'condition':<16}{'target CPR':>11}{'95% Wilson':>18}{'competitor CPR':>16}{'runs':>8}")
    for c in CONDITIONS:
        sub = [r for r in rows if r["condition"] == c]
        if not sub:
            continue
        k, n = sum(r["target_cited"] for r in sub), len(sub)
        lo, hi = wilson(k, n)
        cc = np.mean([competitor_cpr(r, comp) for r in sub])
        print(f"  {c:<14}{k / n:11.3f}{f'[{lo:.3f}, {hi:.3f}]':>18}{cc:16.3f}{n:8d}")

    cpr = cell_means(rows, lambda r, c: 1.0 if r["target_cited"] else 0.0, comp, keep)

    hdr("SATURATION -- is each engine's agree arm an estimate or a floor?")
    for m in keep:
        a = np.mean([r["target_cited"] for r in rows if r["model"] == m and r["condition"] == "agree"])
        print(f"  {m:<30}{a:8.3f}   H13 delta is "
              f"{'a floor (saturated)' if a >= SATURATED else 'an estimate'}")

    hdr("H13 (primary) -- agreeing with the competitor vs contradicting it")
    print("agree - conflict, paired per prompt, bootstrap over prompts\n")
    print(f"{'pool':<16}{'delta':>9}{'95% CI':>22}{'perm p':>9}{'prompts':>9}")
    res = {}
    for label, ww in (("share-weighted", w), ("unweighted", flat)):
        d, lo, hi, p, n = summarise(contrast(cpr, H13, ww), args)
        res[label] = (d, lo, hi)
        print(f"  {label:<14}{d:+9.4f}{f'[{lo:+.4f}, {hi:+.4f}]':>22}{p:9.4f}{n:9d}")
    d, lo, hi = res["share-weighted"]
    print(f"\n  The pre-registered decision uses the share-weighted pool.")
    print(f"  --> H13 {'FALSIFIED (CI includes zero)' if lo <= 0 <= hi else 'SUPPORTED (CI excludes zero)'}")

    hdr("H13 per engine (primary; weights not involved)")
    print(f"{'model':<32}{'agree':>8}{'conflict':>10}{'delta':>9}{'95% CI':>22}{'p':>8}{'Holm':>8}")
    per = []
    for m in keep:
        cm = {k: v for k, v in cpr.items() if k[1] == m}
        a = contrast(cm, lambda x: x["agree"], {m: 1.0}).mean()
        c = contrast(cm, lambda x: x["conflict"], {m: 1.0}).mean()
        per.append((m, a, c) + summarise(contrast(cm, H13, {m: 1.0}), args)[:4])
    for (m, a, c, d, lo, hi, p), hp in zip(per, holm([e[6] for e in per])):
        print(f"  {m:<30}{a:8.3f}{c:10.3f}{d:+9.3f}{f'[{lo:+.3f}, {hi:+.3f}]':>22}{p:8.4f}{hp:8.4f}"
              f"{'*' if hp < 0.05 else ' '}")

    hdr("ADOPTION -- which side's figure do `conflict` answers state?")
    out_of = sorted(p for p, s in S.items() if not all(s))
    print(f"prompts without a distinctive figure on both sides (left out): {out_of or 'none'}")
    print(f"\n{'model':<32}{'correct':>9}{'wrong':>8}{'both':>7}{'neither':>9}{'share correct':>15}")
    for m in keep:
        k = Counter(adoption(r.get("response_text"), *S[r["prompt_id"]]) for r in rows
                    if r["model"] == m and r["condition"] == "conflict" and all(S[r["prompt_id"]]))
        dec = k["correct"] + k["wrong"]
        print(f"  {m:<30}{k['correct']:9d}{k['wrong']:8d}{k['both']:7d}{k['neither']:9d}"
              f"{(k['correct'] / dec if dec else float('nan')):15.3f}")
    share = adoption_share(rows, S, w)
    for cls in ("world", "document"):
        v = np.array([s for p, s in share.items() if truth[p] == cls])
        if len(v):
            lo, hi = boot_ci(v, n=args.boot)
            print(f"  {cls:<9} share correct {v.mean():.3f} [{lo:.3f}, {hi:.3f}]  ({len(v)} prompts)")

    hdr("SECONDARY -- H13a-H13d, Holm across the four, share-weighted")
    fam = []
    for label, cells, fn in (
            ("H13a conflict - control_comp, target CPR", cpr, H13A),
            ("H13b competitor CPR, conflict - agree",
             cell_means(rows, competitor_cpr, comp, keep), H13B)):
        fam.append((label,) + summarise(contrast(cells, fn, w), args)[:4])

    sv = np.array([share[p] - 0.5 for p in sorted(share)])
    lo, hi = boot_ci(sv, n=args.boot)
    fam.append(("H13c adoption share correct - 0.5", float(sv.mean()), lo, hi, perm_p(sv, n=args.perm)))

    prompts = sorted({p for p, _ in cpr})
    by_p = dict(zip(prompts, contrast(cpr, H13, w)))
    cls = np.array([truth[p] == "world" for p in prompts])
    vals = np.array([by_p[p] for p in prompts])
    obs = vals[cls].mean() - vals[~cls].mean()
    rng = np.random.default_rng(0)
    bs = []
    for _ in range(args.boot):
        a = rng.choice(vals[cls], size=cls.sum())
        b = rng.choice(vals[~cls], size=(~cls).sum())
        bs.append(a.mean() - b.mean())
    lo, hi = np.percentile(bs, [2.5, 97.5])
    perm = [abs(vals[s].mean() - vals[~s].mean()) >= abs(obs)
            for s in (rng.permutation(cls) for _ in range(args.perm))]
    fam.append(("H13d H13 world - H13 document", float(obs), lo, hi, float(np.mean(perm))))

    print(f"{'contrast':<46}{'delta':>9}{'95% CI':>22}{'p':>8}{'Holm':>8}")
    for (label, d, lo, hi, p), hp in zip(fam, holm([f[4] for f in fam])):
        print(f"  {label:<44}{d:+9.4f}{f'[{lo:+.4f}, {hi:+.4f}]':>22}{p:8.4f}{hp:8.4f}"
              f"{'*' if hp < 0.05 else ' '}")
    print("\n  H13a is two-sided and its direction is not predicted: a figure the")
    print("  competitor contradicts may still beat a page that states none.")
    print(f"  H13d compares {int(cls.sum())} world prompts with {int((~cls).sum())} document prompts,")
    print("  classed in the corpus builder before any data.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
