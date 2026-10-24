#!/usr/bin/env python3
"""
OpenGEO -- analysis for the competition round (H9).

`analyze.py` assumes a two-condition design, so the 2x2 needs its own path.
Everything here follows the analysis plan in
`preregistrations/2026-10-competition.md`:

  primary      target CPR (METHODOLOGY.md A1)
  H9           treatment_comp - control_comp, share-weighted pooled delta;
               falsified if its 95% CI includes zero
  H4r          treatment - control, the same contrast without a competitor,
               reported as a replication on the five-engine panel
  secondary    H9a interaction (H9 delta - H4r delta)
               H9b competitor CPR, treatment_comp - control_comp
               H9c target first-citation rate (B1) under competition
               H9d target selection share (A2) under competition
               Holm across the four
  pairing      per (prompt, model)
  inference    bootstrap over prompts, 10,000 resamples, percentile CIs;
               sign-flip permutation on per-prompt deltas
  exclusions   any model above 10% no-cite, reported separately

A treatment arm at or above 0.98 CPR on an engine reports a floor on that
engine's effect, not an estimate (METHODOLOGY.md §9); the saturation table says
which engines that applies to.

Pooled figures are share-weighted by `engine_weights.py`, with the unweighted
pool shown beside them (ROADMAP "What the failures changed": a pooled figure
can hide a directional split). Per-engine results are primary.

    python3 analyze_competition.py --runs results/runs_competition.jsonl
"""
import argparse
import json
import pathlib
import sys
from collections import defaultdict

import numpy as np

from analyze import cell_key, report_incomplete, wilson
from engine_weights import coverage, weights

HERE = pathlib.Path(__file__).parent
CONDITIONS = ["control", "treatment", "control_comp", "treatment_comp"]
NO_CITE_LIMIT = 0.10
SATURATED = 0.98


def hdr(t):
    print(f"\n{'=' * 74}\n{t}\n{'=' * 74}")


def load(path):
    rows, errs = [], 0
    for line in pathlib.Path(path).read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("error"):
            errs += 1
        else:
            rows.append(r)
    return rows, errs


# ---------------------------------------------------------------- metrics ----

def target_cpr(r, comp):
    return 1.0 if r["target_cited"] else 0.0


def competitor_cpr(r, comp):
    return 1.0 if comp[r["prompt_id"]] in r["cited_doc_ids"] else 0.0


def first_cite(r, comp):
    """B1: the target is the first source the answer cites."""
    return 1.0 if r.get("target_cite_rank") == 0 else 0.0


def selection_share(r, comp):
    """A2: target citations over all citations in the run; 0 for a no-cite run."""
    ids = r["cited_doc_ids"]
    return ids.count(r["target_doc_id"]) / len(ids) if ids else 0.0


# ------------------------------------------------------------- inference ----

def cell_means(rows, metric, comp, models):
    """{(prompt, model): {condition: mean metric}}"""
    acc = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r["model"] in models:
            acc[(r["prompt_id"], r["model"])][r["condition"]].append(metric(r, comp))
    return {k: {c: float(np.mean(v)) for c, v in d.items()} for k, d in acc.items()}


def contrast(cells, fn, w):
    """Per-prompt weighted mean of fn(cell) across models.

    Weighting happens across models within a prompt, then prompts are the
    resampling unit and are averaged equally.
    """
    by_prompt = defaultdict(dict)
    for (p, m), d in cells.items():
        try:
            by_prompt[p][m] = fn(d)
        except KeyError:
            continue
    out = []
    for p in sorted(by_prompt):
        per = by_prompt[p]
        tot = sum(w.get(m, 0.0) for m in per)
        if tot > 0:
            out.append(sum(w.get(m, 0.0) * v for m, v in per.items()) / tot)
    return np.array(out)


H4R = lambda d: d["treatment"] - d["control"]
H9 = lambda d: d["treatment_comp"] - d["control_comp"]
H9A = lambda d: H9(d) - H4R(d)


def boot_ci(vals, n=10000, alpha=0.05, seed=0):
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(vals), size=(n, len(vals)))
    d = vals[idx].mean(axis=1)
    return np.percentile(d, [100 * alpha / 2, 100 * (1 - alpha / 2)])


def perm_p(vals, n=20000, seed=0):
    """Sign-flip permutation on paired deltas: exchangeable under the null."""
    rng = np.random.default_rng(seed)
    obs = abs(vals.mean())
    signs = rng.choice([-1.0, 1.0], size=(n, len(vals)))
    return float((np.abs((signs * vals).mean(axis=1)) >= obs).mean())


def holm(pvals):
    order = sorted(range(len(pvals)), key=lambda i: pvals[i])
    out, run = [0.0] * len(pvals), 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(pvals) - rank) * pvals[i]))
        out[i] = run
    return out


def summarise(vals, args):
    lo, hi = boot_ci(vals, n=args.boot)
    return float(vals.mean()), lo, hi, perm_p(vals, n=args.perm), len(vals)


# ------------------------------------------------------------------ main ----

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="results/runs_competition.jsonl")
    ap.add_argument("--corpus", default=str(HERE / "corpus" / "corpus_competition.json"))
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--perm", type=int, default=20000)
    args = ap.parse_args(argv)

    corpus = json.loads(pathlib.Path(args.corpus).read_text())
    comp = {p["prompt_id"]: p["competitor_doc_id"] for p in corpus["prompts"]}

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
    print("\nshare weights (engine_weights.py):")
    for m, x in sorted(w.items(), key=lambda kv: -kv[1]):
        print(f"  {m:<32}{x:7.1%}")
    print(f"  panel covers {coverage(keep):.1%} of measured gen-AI traffic")

    hdr("DESCRIPTIVE -- by condition, all included engines")
    print(f"{'condition':<16}{'target CPR':>11}{'95% Wilson':>18}"
          f"{'competitor CPR':>16}{'cites/answer':>14}{'runs':>8}")
    for c in CONDITIONS:
        sub = [r for r in rows if r["condition"] == c]
        if not sub:
            continue
        k, n = sum(r["target_cited"] for r in sub), len(sub)
        lo, hi = wilson(k, n)
        cc = (np.mean([competitor_cpr(r, comp) for r in sub])
              if c.endswith("_comp") else float("nan"))
        cpa = np.mean([len(r["cited_doc_ids"]) for r in sub])
        print(f"  {c:<14}{k/n:11.3f}{f'[{lo:.3f}, {hi:.3f}]':>18}"
              f"{cc:16.3f}{cpa:14.2f}{n:8d}")
    print("\n  Competitor CPR is the displaced slot in the _comp conditions only.")

    cpr = cell_means(rows, target_cpr, comp, keep)

    hdr("SATURATION -- is each engine's treatment arm an estimate or a floor?")
    print(f"{'model':<32}{'treatment':>11}{'treat_comp':>12}   reading")
    for m in keep:
        t = np.mean([r["target_cited"] for r in rows
                     if r["model"] == m and r["condition"] == "treatment"])
        tc = np.mean([r["target_cited"] for r in rows
                      if r["model"] == m and r["condition"] == "treatment_comp"])
        flag = "a floor (saturated)" if tc >= SATURATED else "an estimate"
        print(f"  {m:<30}{t:11.3f}{tc:12.3f}   H9 delta is {flag}")

    hdr("H9 (primary) -- specific figures raise citation with a competitor present")
    print("treatment_comp - control_comp, paired per prompt, bootstrap over prompts\n")
    print(f"{'pool':<16}{'delta':>9}{'95% CI':>22}{'perm p':>9}{'prompts':>9}")
    res = {}
    for label, ww in (("share-weighted", w), ("unweighted", flat)):
        d, lo, hi, p, n = summarise(contrast(cpr, H9, ww), args)
        res[label] = (d, lo, hi)
        print(f"  {label:<14}{d:+9.4f}{f'[{lo:+.4f}, {hi:+.4f}]':>22}{p:9.4f}{n:9d}")
    d, lo, hi = res["share-weighted"]
    falsified = lo <= 0 <= hi
    print(f"\n  The pre-registered decision uses the share-weighted pool.")
    print(f"  --> H9 {'FALSIFIED (CI includes zero)' if falsified else 'SUPPORTED (CI excludes zero)'}")

    hdr("H9 per engine (primary; weights not involved)")
    print(f"{'model':<32}{'ctrl_comp':>10}{'treat_comp':>11}{'delta':>9}"
          f"{'95% CI':>22}{'p':>8}{'Holm':>8}")
    per = []
    for m in keep:
        cm = {k: v for k, v in cpr.items() if k[1] == m}
        vals = contrast(cm, H9, {m: 1.0})
        base = contrast(cm, lambda x: x["control_comp"], {m: 1.0}).mean()
        top = contrast(cm, lambda x: x["treatment_comp"], {m: 1.0}).mean()
        per.append((m, base, top) + summarise(vals, args)[:4])
    for (m, b, t, d, lo, hi, p), hp in zip(per, holm([e[6] for e in per])):
        print(f"  {m:<30}{b:10.3f}{t:11.3f}{d:+9.3f}"
              f"{f'[{lo:+.3f}, {hi:+.3f}]':>22}{p:8.4f}{hp:8.4f}{'*' if hp < 0.05 else ' '}")

    hdr("H4r -- the same contrast with no competitor (replication on this panel)")
    print(f"{'pool':<16}{'delta':>9}{'95% CI':>22}{'perm p':>9}")
    for label, ww in (("share-weighted", w), ("unweighted", flat)):
        d, lo, hi, p, n = summarise(contrast(cpr, H4R, ww), args)
        print(f"  {label:<14}{d:+9.4f}{f'[{lo:+.4f}, {hi:+.4f}]':>22}{p:9.4f}")
    print("  v0.4 reference (8 models, equal weight): +0.482 [+0.404, +0.563]")

    hdr("SECONDARY -- H9a-H9d, Holm across the four, share-weighted")
    fam = [
        ("H9a interaction (H9 - H4r), target CPR", cpr, H9A),
        ("H9b competitor CPR, treat_comp - ctrl_comp",
         cell_means(rows, competitor_cpr, comp, keep), H9),
        ("H9c target first-citation (B1)", cell_means(rows, first_cite, comp, keep), H9),
        ("H9d target selection share (A2)", cell_means(rows, selection_share, comp, keep), H9),
    ]
    out = []
    for label, cells, fn in fam:
        out.append((label,) + summarise(contrast(cells, fn, w), args)[:4])
    print(f"{'contrast':<46}{'delta':>9}{'95% CI':>22}{'p':>8}{'Holm':>8}")
    for (label, d, lo, hi, p), hp in zip(out, holm([o[4] for o in out])):
        print(f"  {label:<44}{d:+9.4f}{f'[{lo:+.4f}, {hi:+.4f}]':>22}{p:8.4f}{hp:8.4f}"
              f"{'*' if hp < 0.05 else ' '}")
    print("\n  H9a is two-sided and its direction is not predicted: a competitor can")
    print("  shrink the effect by sharing citations with the treated target, or grow it")
    print("  by pulling the untreated target down further than the treated one.")
    print("  A saturated treatment arm compresses H9a toward the difference in controls.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
