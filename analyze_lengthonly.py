#!/usr/bin/env python3
"""
OpenGEO -- analysis for the length-only round (H7).

`analyze.py` assumes a two-condition design and indexes `control`/`treatment`
directly, so the dose ladder needs its own path. Everything here follows the
analysis plan committed in `preregistrations/2026-09-lengthonly.md`:

  primary      target CPR (METRICS.md A1)
  pairing      per (prompt, model) -- only the target document differs
  inference    bootstrap over prompts, 10,000 resamples, percentile CIs;
               permutation over condition labels within (prompt, model)
  multiplicity Holm across the three pad contrasts
  H7           falsified if the pooled pad200 - control CI excludes zero
  exclusions   any model above 10% no-cite, reported separately

Pooled figures are **share-weighted** by `engine_weights.py`; per-engine results
are primary and do not depend on the weights.

Bootstrap and permutation only -- no scipy, no distributional assumptions, per
the stack constraint in CLAUDE.md.

    python3 analyze_lengthonly.py --runs results/runs_lengthonly.jsonl
"""
import argparse
import json
import pathlib
import sys
from collections import defaultdict

import numpy as np

from analyze import wilson
from engine_weights import coverage, weights

CONDITIONS = ["control", "pad125", "pad150", "pad200"]
PADS = CONDITIONS[1:]
NO_CITE_LIMIT = 0.10


def hdr(t):
    print(f"\n{'=' * 74}\n{t}\n{'=' * 74}")


# ---------------------------------------------------------------- loading ----

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


def b2_share(rec):
    """B2 Attributed Content Share: fraction of answer sentences citing the target.

    METRICS.md's stated replacement for position-adjusted word count. Credit is
    split when a sentence cites several sources, so shares across documents sum
    to at most 1 rather than double-counting.
    """
    sents = rec.get("sentence_citations") or []
    if not sents:
        return 0.0
    try:
        idx = rec["presentation_order"].index(rec["target_doc_id"]) + 1
    except (ValueError, KeyError):
        return 0.0
    total = 0.0
    for s in sents:
        cites = s.get("cites") or []
        if idx in cites:
            total += 1.0 / len(cites)
    return total / len(sents)


# ------------------------------------------------------------- inference ----

def paired_cells(rows, metric, models):
    """{(prompt, model): {condition: mean metric}} over that cell's runs."""
    acc = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r["model"] not in models:
            continue
        acc[(r["prompt_id"], r["model"])][r["condition"]].append(metric(r))
    return {k: {c: float(np.mean(v)) for c, v in d.items()} for k, d in acc.items()}


def weighted_delta(cells, cond, w):
    """Share-weighted mean paired delta (cond - control), averaged over prompts.

    Weighting happens across models within a prompt, then prompts are averaged
    equally -- prompts are the resampling unit, so they must not also carry the
    weights.
    """
    by_prompt = defaultdict(dict)
    for (p, m), d in cells.items():
        if cond in d and "control" in d:
            by_prompt[p][m] = d[cond] - d["control"]
    out = []
    for p, per_model in by_prompt.items():
        tot = sum(w.get(m, 0.0) for m in per_model)
        if tot <= 0:
            continue
        out.append(sum(w.get(m, 0.0) * v for m, v in per_model.items()) / tot)
    return np.array(out), sorted(by_prompt)


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
    null = (signs * vals).mean(axis=1)
    return float((np.abs(null) >= obs).mean())


def holm(pvals):
    order = sorted(range(len(pvals)), key=lambda i: pvals[i])
    out = [0.0] * len(pvals)
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(pvals) - rank) * pvals[i]))
        out[i] = run
    return out


def spearman(a, b):
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    if np.std(ra) < 1e-12 or np.std(rb) < 1e-12:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def eta_squared(rows, key, metric):
    y = np.array([metric(r) for r in rows])
    grand = y.mean()
    ss_tot = ((y - grand) ** 2).sum()
    if ss_tot <= 0:
        return 0.0
    groups = defaultdict(list)
    for r, v in zip(rows, y):
        groups[key(r)].append(v)
    ss_between = sum(len(v) * (np.mean(v) - grand) ** 2 for v in groups.values())
    return float(ss_between / ss_tot)


# ------------------------------------------------------------------ main ----

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="results/runs_lengthonly.jsonl")
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--perm", type=int, default=20000)
    args = ap.parse_args(argv)

    rows, errs = load(args.runs)
    if not rows:
        sys.exit("no successful runs to analyse")
    all_models = sorted({r["model"] for r in rows})

    hdr("DATA HEALTH")
    print(f"usable runs {len(rows):,}   errored {errs}")
    mismatch = sum(1 for r in rows
                   if r.get("model_returned") and r["model_returned"] != r["model"])
    print(f"model_returned mismatches: {mismatch}")
    print(f"\n{'model':<34}{'no-cite':>9}{'runs':>8}   status")
    keep = []
    for m in all_models:
        sub = [r for r in rows if r["model"] == m]
        nc = sum(1 for r in sub if not r["cited_doc_ids"]) / len(sub)
        ok = nc <= NO_CITE_LIMIT
        keep.append(m) if ok else None
        print(f"  {m:<32}{nc:8.1%}{len(sub):8d}   {'included' if ok else 'EXCLUDED (>10%)'}")
    if not keep:
        sys.exit("every model failed data health")

    w = weights(keep)
    print(f"\nshare weights (engine_weights.py):")
    for m, x in sorted(w.items(), key=lambda kv: -kv[1]):
        print(f"  {m:<32}{x:7.1%}")
    print(f"  panel covers {coverage(keep):.1%} of measured gen-AI traffic")

    cpr = lambda r: 1.0 if r["target_cited"] else 0.0

    hdr("DESCRIPTIVE -- target CPR by condition")
    print(f"{'condition':<12}{'CPR':>8}{'95% Wilson':>20}{'runs':>9}")
    for c in CONDITIONS:
        sub = [r for r in rows if r["condition"] == c and r["model"] in keep]
        if not sub:
            continue
        k, n = sum(r["target_cited"] for r in sub), len(sub)
        lo, hi = wilson(k, n)
        print(f"  {c:<10}{k/n:8.3f}{f'[{lo:.3f}, {hi:.3f}]':>20}{n:9d}")

    hdr("H7 -- adding words without adding facts does not increase citation")
    print("share-weighted paired deltas vs control; bootstrap over prompts\n")
    cells = paired_cells(rows, cpr, keep)
    print(f"{'contrast':<18}{'delta':>9}{'95% CI':>22}{'perm p':>9}{'Holm p':>9}")
    raw_p, results = [], []
    for c in PADS:
        vals, prompts = weighted_delta(cells, c, w)
        lo, hi = boot_ci(vals, n=args.boot)
        p = perm_p(vals, n=args.perm)
        raw_p.append(p)
        results.append((c, vals.mean(), lo, hi, p, len(prompts)))
    for (c, d, lo, hi, p, npr), hp in zip(results, holm(raw_p)):
        star = " *" if hp < 0.05 else ""
        print(f"  {c:<16}{d:+9.4f}{f'[{lo:+.4f}, {hi:+.4f}]':>22}{p:9.4f}{hp:9.4f}{star}")

    c, d, lo, hi, p, npr = results[-1]
    falsified = not (lo <= 0 <= hi)
    print(f"\n  H7 falsification contrast is pad200 - control, fixed in advance.")
    print(f"  delta {d:+.4f}, 95% CI [{lo:+.4f}, {hi:+.4f}] over {npr} prompts")
    print(f"  --> H7 {'FALSIFIED' if falsified else 'NOT falsified'}"
          f" (CI {'excludes' if falsified else 'includes'} zero)")
    if falsified:
        print(f"      direction: padding {'INCREASED' if d > 0 else 'DECREASED'} citation")

    hdr("H7 per engine (primary; weights not involved)")
    print(f"{'model':<32}{'control':>9}{'pad125':>9}{'pad150':>9}{'pad200':>9}{'d(200)':>9}")
    for m in keep:
        line = f"  {m:<30}"
        base = None
        for c in CONDITIONS:
            sub = [r for r in rows if r["model"] == m and r["condition"] == c]
            v = sum(r["target_cited"] for r in sub) / len(sub) if sub else float("nan")
            if c == "control":
                base = v
            line += f"{v:9.3f}"
        line += f"{v - base:+9.3f}"
        print(line)

    hdr("H7a -- dose-response")
    doses = [1.0, 1.31, 1.58, 2.06]
    rhos = []
    for m in keep:
        means = []
        for c in CONDITIONS:
            sub = [r for r in rows if r["model"] == m and r["condition"] == c]
            means.append(sum(r["target_cited"] for r in sub) / len(sub) if sub else np.nan)
        rho = spearman(np.array(doses), np.array(means))
        rhos.append(rho)
        print(f"  {m:<32}rho={rho:+.3f}   {' '.join(f'{x:.3f}' for x in means)}")
    mono = all(r == 1.0 for r in rhos) or all(r == -1.0 for r in rhos)
    print(f"\n  mean rho {np.nanmean(rhos):+.3f}; "
          f"{'monotone on every engine' if mono else 'not monotone on every engine'}")

    hdr("H7b -- CPR vs B2 Attributed Content Share")
    print("is the share metric more sensitive to padding than CPR?\n")
    print(f"{'metric':<16}{'d(pad200)':>12}{'95% CI':>24}")
    for name, fn in (("CPR", cpr), ("B2 share", b2_share)):
        cl = paired_cells(rows, fn, keep)
        vals, _ = weighted_delta(cl, "pad200", w)
        lo, hi = boot_ci(vals, n=max(args.boot // 2, 2000))
        print(f"  {name:<14}{vals.mean():+12.4f}{f'[{lo:+.4f}, {hi:+.4f}]':>24}")
    print("\n  No significance test on the difference is pre-registered; reported as\n"
          "  two intervals, per the analysis plan.")

    hdr("VARIANCE COMPONENTS (eta squared, target CPR)")
    usable = [r for r in rows if r["model"] in keep]
    for label, key in (("condition (padding)", lambda r: r["condition"]),
                       ("prompt identity", lambda r: r["prompt_id"]),
                       ("target format", lambda r: r["target_format"]),
                       ("target slot", lambda r: r["target_slot"]),
                       ("model", lambda r: r["model"])):
        print(f"  {label:<24}{eta_squared(usable, key, cpr):.4f}")
    print("\n  v0.4 reference: format 0.483, prompt 0.484, slot 0.003.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
