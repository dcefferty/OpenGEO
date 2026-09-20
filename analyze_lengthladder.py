#!/usr/bin/env python3
"""
OpenGEO -- analysis for the length-ladder probe (ROADMAP item 11).

Design, pre-committed reading, and the phase-1 deviation:
`results/probes/2026-09-19-length-ladder.md`.

Three questions, a target at three nested lengths, each with and without `answer_first`.
The question is whether the `answer_first` effect grows with document length -- if it is
flat at zero across a 4-8x length range, the tactic pilot's null is not a length artefact.

Cell selection follows the logged deviation: the primary figures use cells whose
**control** rate at that rung sits inside [3/24, 21/24]. That selects on the control arm
only, which the treatment arm does not touch, so it cannot be steered by the outcome.
All-cell figures are printed beside every restricted one so the restriction stays visible.

Bootstrap and permutation only, no scipy, per the stack constraint in CLAUDE.md.

    python3 analyze_lengthladder.py --runs results/lengthladder.jsonl
"""
import argparse
import json
import sys
from collections import defaultdict

import numpy as np

from analyze import wilson
from analyze_lengthonly import load, perm_p
from engine_weights import coverage, weights

RUNGS = ["short", "mid", "long"]
LO, HI = 3 / 24, 1 - 3 / 24
NO_CITE_LIMIT = 0.10
# questions whose answer moves further from the top as the rung grows, vs the one where
# it stays at sentence two -- the contrast that separates burial depth from length itself
DEEPENING = ["home_smokealarm", "home_radon"]
FIXED = ["finance_housingshare"]


def hdr(t):
    print(f"\n{'=' * 80}\n{t}\n{'=' * 80}")


def wboot(vals, wts, n=10000, seed=0):
    if len(vals) == 0:
        return float("nan"), (float("nan"), float("nan"))
    v, w = np.asarray(vals, float), np.asarray(wts, float)
    obs = float((v * w).sum() / w.sum())
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(n):
        i = rng.integers(0, len(v), len(v))
        bs.append((v[i] * w[i]).sum() / w[i].sum())
    return obs, tuple(np.percentile(bs, [2.5, 97.5]))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="results/lengthladder.jsonl")
    ap.add_argument("--boot", type=int, default=10000)
    args = ap.parse_args(argv)

    rows, errs = load(args.runs)
    if not rows:
        sys.exit("no successful runs to analyse")
    last = {}
    for r in rows:
        last[r["run_key"]] = r
    rows = list(last.values())

    models = sorted({r["model"] for r in rows})
    prompts = sorted({r["prompt_id"] for r in rows})

    hdr("DATA HEALTH")
    print(f"usable runs {len(rows):,}   errored {errs}")
    print(f"model_returned mismatches: "
          f"{sum(1 for r in rows if r.get('model_returned') and r['model_returned'] != r['model'])}")
    keep = []
    for m in models:
        s = [r for r in rows if r["model"] == m]
        nc = sum(1 for r in s if not (r.get("cited_doc_ids") or [])) / len(s)
        if nc <= NO_CITE_LIMIT:
            keep.append(m)
        else:
            print(f"  EXCLUDED {m}: {nc:.1%} no-cite")
    models = keep
    w = weights(models)
    print(f"panel covers {coverage(models):.1%} of measured assistant traffic")

    cell = defaultdict(lambda: [0, 0])
    for r in rows:
        if r["model"] in models:
            c = cell[(r["prompt_id"], r["model"], r["condition"])]
            c[0] += r["target_cited"]
            c[1] += 1

    # A cell short of its runs is not a smaller sample of the same thing when the cause
    # is a mid-run failure: it is a cell whose interval is wider than the table implies.
    # Report them rather than averaging them in silently. MIN_RUNS is the floor below
    # which a cell is dropped from the primary figures entirely.
    MIN_RUNS = 20
    incomplete = sorted(((p_, m_, c_), n) for (p_, m_, c_), (k, n) in cell.items()
                        if n < 24)
    if incomplete:
        print(f"\nINCOMPLETE CELLS: {len(incomplete)} of {len(cell)} did not reach 24 runs")
        for (p_, m_, c_), n in incomplete[:15]:
            flag = "  DROPPED" if n < MIN_RUNS else ""
            print(f"  {p_:<22}{m_.split('/')[1][:10]:<12}{c_:<14}{n:>3}/24{flag}")
        print(f"  cells below {MIN_RUNS} runs are dropped from the primary figures.")
        print("  Complete the run (run_pilot.py --resume) before treating this as final.")

    def rate(p, m, cond):
        k, n = cell[(p, m, cond)]
        return (k / n) if n >= MIN_RUNS else None

    def unpinned(p, m, rung):
        v = rate(p, m, f"{rung}_control")
        return v is not None and LO <= v <= HI

    # ---- per question x rung x engine ---------------------------------------
    for p in prompts:
        hdr(f"{p}")
        print(f"{'engine':<20}" + "".join(f"{r:>26}" for r in RUNGS))
        print(f"{'':<20}" + "".join(f"{'ctl -> first  (delta)':>26}" for r in RUNGS))
        for m in models:
            line = f"{m.split('/')[1][:18]:<20}"
            for rung in RUNGS:
                c, f_ = rate(p, m, f"{rung}_control"), rate(p, m, f"{rung}_first")
                if c is None or f_ is None:
                    line += f"{'-':>26}"
                    continue
                tag = "" if unpinned(p, m, rung) else "*"
                line += f"{f'{c:.2f} -> {f_:.2f} ({f_ - c:+.2f}){tag}':>26}"
            print(line)
        print("* control pinned at this rung; excluded from the primary figures")

    # ---- per-rung pooled effect ---------------------------------------------
    hdr("ANSWER_FIRST EFFECT BY RUNG  (share-weighted)")
    print(f"{'rung':<8}{'n':>4}{'delta (unpinned)':>22}{'95% CI':>20}"
          f"{'n':>5}{'delta (all cells)':>20}")
    per_rung = {}
    for rung in RUNGS:
        vu, wu, va, wa = [], [], [], []
        for p in prompts:
            for m in models:
                c, f_ = rate(p, m, f"{rung}_control"), rate(p, m, f"{rung}_first")
                if c is None or f_ is None:
                    continue
                va.append(f_ - c); wa.append(w.get(m, 0.0))
                if unpinned(p, m, rung):
                    vu.append(f_ - c); wu.append(w.get(m, 0.0))
        du, ciu = wboot(vu, wu, args.boot)
        da, _ = wboot(va, wa, args.boot)
        per_rung[rung] = (du, ciu, len(vu))
        print(f"{rung:<8}{len(vu):>4}{du:>+22.3f}{f'[{ciu[0]:+.3f},{ciu[1]:+.3f}]':>20}"
              f"{len(va):>5}{da:>+20.3f}")

    # ---- primary contrast: the interaction ----------------------------------
    hdr("PRIMARY CONTRAST  (long_first - long_control) - (short_first - short_control)")
    vi, wi, cells = [], [], []
    for p in prompts:
        for m in models:
            if not (unpinned(p, m, "short") and unpinned(p, m, "long")):
                continue
            lf, sf = rate(p, m, "long_first"), rate(p, m, "short_first")
            if lf is None or sf is None:
                continue  # partial collection; the arm has not been run for this cell
            d_long = lf - rate(p, m, "long_control")
            d_short = sf - rate(p, m, "short_control")
            vi.append(d_long - d_short); wi.append(w.get(m, 0.0))
            cells.append(f"{p.split('_')[0]}/{m.split('/')[1][:8]}")
    di, cii = wboot(vi, wi, args.boot)
    print(f"interaction {di:+.3f}   95% CI [{cii[0]:+.3f}, {cii[1]:+.3f}]   "
          f"p={perm_p(np.array(vi)) if len(vi) > 1 else float('nan'):.4f}   n={len(vi)} cells")
    print(f"cells: {', '.join(cells)}")
    # At six cells with one carrying 56% of the panel weight, a percentile bootstrap CI
    # and a sign-flip permutation test can disagree sharply: the bootstrap usually keeps
    # the dominant cell, the permutation can flip its sign and reverse the mean on its
    # own. Report the disagreement and the leave-one-out range rather than quoting
    # whichever interval reads better.
    vi_a, wi_a = np.asarray(vi, float), np.asarray(wi, float)
    pp = perm_p(vi_a) if len(vi_a) > 1 else float("nan")
    jk = [float((np.delete(vi_a, i) * np.delete(wi_a, i)).sum()
                / np.delete(wi_a, i).sum()) for i in range(len(vi_a))]
    print(f"\nROBUSTNESS")
    print(f"  cells positive        {int((vi_a > 0).sum())} of {len(vi_a)}"
          f"   unweighted mean {vi_a.mean():+.3f}   median {np.median(vi_a):+.3f}")
    print(f"  leave-one-out range   {min(jk):+.3f} to {max(jk):+.3f}")
    print(f"  bootstrap CI          [{cii[0]:+.3f}, {cii[1]:+.3f}]  (excludes 0: "
          f"{'yes' if cii[0] > 0 or cii[1] < 0 else 'no'})")
    print(f"  permutation p         {pp:.4f}  (significant at .05: "
          f"{'yes' if pp < 0.05 else 'NO'})")
    if (cii[0] > 0 or cii[1] < 0) and pp >= 0.05:
        print("  ** THE TWO DISAGREE. With this many cells the percentile CI is")
        print("     anti-conservative; the sign-flip test is the more trustworthy of")
        print("     the two here, and it does not clear .05. Treat the interaction as")
        print("     suggestive, not established, whatever the committed rule prints.")
    print(f"\nThe probe projected +/-0.10 on this contrast. Requiring BOTH rungs unpinned")
    print(f"in the same cell leaves {len(vi)} of 15, so its actual half-width is about")
    print(f"{(cii[1] - cii[0]) / 2:.3f}. The per-rung figures above carry the weight instead;")
    print("the committed reading needs the long-rung effect as well, which is why.")

    # ---- burial depth vs length itself --------------------------------------
    hdr("BURIAL DEPTH vs DOCUMENT LENGTH")
    print("Deepening questions move the answer further from the top as the rung grows;")
    print("the fixed question grows the document with the answer at sentence two.\n")
    print(f"{'group':<34}" + "".join(f"{r:>16}" for r in RUNGS))
    for label, group in (("deepening (smokealarm, radon)", DEEPENING),
                         ("fixed position (housingshare)", FIXED)):
        line = f"{label:<34}"
        for rung in RUNGS:
            v, ww = [], []
            for p in group:
                for m in models:
                    c, f_ = rate(p, m, f"{rung}_control"), rate(p, m, f"{rung}_first")
                    if c is not None and f_ is not None and unpinned(p, m, rung):
                        v.append(f_ - c); ww.append(w.get(m, 0.0))
            d, _ = wboot(v, ww, 2000)
            line += f"{f'{d:+.3f} (n={len(v)})' if len(v) else '-':>16}"
        print(line)

    # ---- pre-committed reading ----------------------------------------------
    hdr("PRE-COMMITTED READING  (fixed before collection)")
    dl, cil, nl = per_rung["long"]
    ds = per_rung["short"][0]
    print(f"interaction  {di:+.3f}  CI [{cii[0]:+.3f}, {cii[1]:+.3f}]")
    print(f"long rung    {dl:+.3f}  CI [{cil[0]:+.3f}, {cil[1]:+.3f}]   (n={nl} cells)")
    print(f"short rung   {ds:+.3f}")
    grows = dl > ds
    supports = di >= 0.10 and cii[0] > 0 and grows
    long_null = cil[0] <= 0 <= cil[1]
    if supports:
        v = ("B SUPPORTED: length moderates the answer-first effect. Re-anchor the "
             "corpus to longer targets, re-screen at a wider margin, and size item 11 "
             "from the long-rung effect rather than from H6.")
    elif cii[0] <= 0 <= cii[1] and long_null:
        v = ("B IS DEAD: at 4-8x the document length, with the answer up to 216 words "
             "from the top, moving it to the front changes nothing. Explanation A "
             "survives -- item 11's ranked table is not obtainable in Tier 1, and the "
             "result to publish is the scope boundary: presentation tactics are a Tier 2 "
             "question because their causal path runs through the retrieval stage this "
             "design holds constant.")
    else:
        v = ("INCONCLUSIVE by the committed rule; report as an interval and do not size "
             "the round.")
    print("\n" + "\n".join(v[i:i + 78] for i in range(0, len(v), 78)))
    print("\nThree questions. This sizes a decision about the round; it is not a")
    print("published effect size and it does not rank tactics.")


if __name__ == "__main__":
    main()
