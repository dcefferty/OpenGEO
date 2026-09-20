#!/usr/bin/env python3
"""
OpenGEO -- analysis for the tactic pilot (ROADMAP item 11).

Design and pre-committed reading: `results/probes/2026-09-19-tactic-pilot.md`, committed
before collection.

This is a probe at **three questions**, far below the 25-question floor
(`METHODOLOGY.md` §5.2). It estimates effects and their spread so the round can be sized.
It does not test a hypothesis and it does not publish an effect size.

The distinction that matters here is the resampling unit. Each (question, engine, tactic)
cell is 24 runs, so a cell rate is well determined and carries a clean Wilson interval.
Generalising to *other questions* is what three questions cannot support: a bootstrap over
three prompts has very few distinct resamples and its interval is not a credible statement
about questions at large. So this reports both, and says which is which:

  per-cell        Wilson on 24 runs -- solid, and the basis for "did anything move"
  pooled by cell  bootstrap over (question x engine) cells -- the sizing input,
                  optimistic about question-to-question variation by construction
  pooled by q     bootstrap over three prompts -- reported, and labelled as thin

Pooled figures are share-weighted by `engine_weights.py`, per the H7 lesson that a pooled
headline must state its weighting; per-engine results are primary. Bootstrap and
permutation only, no scipy, per the stack constraint in CLAUDE.md.

    python3 analyze_tacticpilot.py --runs results/tacticpilot.jsonl
"""
import argparse
import json
import pathlib
import sys
from collections import defaultdict

import numpy as np

from analyze import wilson
from analyze_lengthonly import boot_ci, holm, load, perm_p
from engine_weights import coverage, weights

CONTROL = "control"
NO_CITE_LIMIT = 0.10


def hdr(t):
    print(f"\n{'=' * 78}\n{t}\n{'=' * 78}")


def cited(r):
    return 1.0 if r["target_doc_id"] in (r.get("cited_doc_ids") or []) else 0.0


def odds(p, k, n):
    """Odds with a Haldane-Anscombe 0.5 correction when a cell saturates."""
    if 0.0 < p < 1.0:
        return p / (1.0 - p)
    return (k + 0.5) / (n - k + 0.5)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="results/tacticpilot.jsonl")
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--perm", type=int, default=20000)
    args = ap.parse_args(argv)

    rows, errs = load(args.runs)
    if not rows:
        sys.exit("no successful runs to analyse")

    # last row per run_key, as every other analyser does
    last = {}
    for r in rows:
        last[r["run_key"]] = r
    rows = list(last.values())

    models = sorted({r["model"] for r in rows})
    prompts = sorted({r["prompt_id"] for r in rows})
    conds = [CONTROL] + [c for c in sorted({r["condition"] for r in rows}) if c != CONTROL]
    tactics = conds[1:]

    hdr("DATA HEALTH")
    print(f"usable runs {len(rows):,}   errored {errs}")
    mism = sum(1 for r in rows
               if r.get("model_returned") and r["model_returned"] != r["model"])
    print(f"model_returned mismatches: {mism}")
    print(f"\n{'model':<34}{'no-cite':>9}{'runs':>8}   status")
    keep = []
    for m in models:
        s = [r for r in rows if r["model"] == m]
        nc = sum(1 for r in s if not (r.get("cited_doc_ids") or [])) / len(s)
        ok = nc <= NO_CITE_LIMIT
        keep.append(m) if ok else None
        print(f"{m:<34}{nc:>8.1%}{len(s):>8}   {'ok' if ok else 'EXCLUDED >10% no-cite'}")
    models = keep
    cov = coverage(models)
    w = weights(models)
    print(f"\npanel covers {cov:.1%} of measured assistant traffic")

    # ---- cell rates: (prompt, model, condition) -> (k, n) -------------------
    cell = defaultdict(lambda: [0, 0])
    for r in rows:
        if r["model"] not in models:
            continue
        c = cell[(r["prompt_id"], r["model"], r["condition"])]
        c[0] += cited(r)
        c[1] += 1

    hdr("BASELINE PLACEMENT (control arm, the screen's prediction)")
    print(f"{'question':<24}" + "".join(f"{m.split('/')[1][:10]:>12}" for m in models))
    for p in prompts:
        line = f"{p:<24}"
        for m in models:
            k, n = cell[(p, m, CONTROL)]
            line += f"{(k / n if n else float('nan')):>12.2f}"
        print(line)
    print("\nA tactic can only show up where the control is off the floor and ceiling.")

    # ---- per question x tactic ---------------------------------------------
    for p in prompts:
        hdr(f"{p}")
        print(f"{'engine':<20}{'control':>16}" + "".join(f"{t[:14]:>18}" for t in tactics))
        for m in models:
            kc, nc_ = cell[(p, m, CONTROL)]
            lo, hi = wilson(kc, nc_)
            line = f"{m.split('/')[1][:18]:<20}{f'{kc/nc_:.2f} [{lo:.2f},{hi:.2f}]':>16}"
            for t in tactics:
                kt, nt = cell[(p, m, t)]
                d = kt / nt - kc / nc_
                line += f"{f'{kt/nt:.2f} ({d:+.2f})':>18}"
            print(line)

    # ---- pooled per tactic --------------------------------------------------
    hdr("POOLED EFFECT PER TACTIC  (share-weighted; control-relative)")
    print("delta is the share-weighted mean of per-cell (tactic - control) rates.")
    print("OR pools counts across cells with a Haldane correction on saturated cells.\n")
    print(f"{'tactic':<16}{'delta':>9}{'95% CI (cells)':>20}{'OR':>7}"
          f"{'95% CI':>16}{'p':>9}{'95% CI (3 q)':>20}")

    results, pvals = {}, []
    for t in tactics:
        # per-cell deltas and their weights
        deltas, wts, pid_of = [], [], []
        kt_tot = nt_tot = kc_tot = nc_tot = 0
        for p in prompts:
            for m in models:
                kc, nc_ = cell[(p, m, CONTROL)]
                kt, nt = cell[(p, m, t)]
                if not nc_ or not nt:
                    continue
                deltas.append(kt / nt - kc / nc_)
                wts.append(w.get(m, 0.0))
                pid_of.append(p)
                kt_tot += kt; nt_tot += nt; kc_tot += kc; nc_tot += nc_
        deltas = np.array(deltas); wts = np.array(wts); pid_of = np.array(pid_of)

        def wmean(idx):
            ww = wts[idx]
            return float((deltas[idx] * ww).sum() / ww.sum()) if ww.sum() > 0 else np.nan

        obs = wmean(np.arange(len(deltas)))

        rng = np.random.default_rng(0)
        bs = np.array([wmean(rng.integers(0, len(deltas), len(deltas)))
                       for _ in range(args.boot)])
        ci = np.nanpercentile(bs, [2.5, 97.5])

        # per-question bootstrap: the honest unit, thin at three
        qd = np.array([wmean(np.where(pid_of == p)[0]) for p in prompts])
        qci = boot_ci(qd, n=args.boot)

        pt, pc = kt_tot / nt_tot, kc_tot / nc_tot
        or_obs = odds(pt, kt_tot, nt_tot) / odds(pc, kc_tot, nc_tot)
        # OR interval from the same cell bootstrap, recomputing pooled counts
        idx_all = np.arange(len(deltas))
        cells_t = [(cell[(p, m, t)], cell[(p, m, CONTROL)])
                   for p in prompts for m in models if cell[(p, m, t)][1]]
        bs_or = []
        for _ in range(args.boot):
            pick = rng.integers(0, len(cells_t), len(cells_t))
            a = b = c = d_ = 0
            for i in pick:
                (kt, nt), (kc, nc_) = cells_t[i]
                a += kt; b += nt; c += kc; d_ += nc_
            bs_or.append(odds(a / b, a, b) / odds(c / d_, c, d_))
        or_ci = np.percentile(bs_or, [2.5, 97.5])

        pv = perm_p(deltas, n=args.perm)
        pvals.append(pv)
        results[t] = {"delta": obs, "ci": ci, "or": or_obs, "or_ci": or_ci,
                      "p": pv, "qci": qci, "rate": pt, "control_rate": pc}
        print(f"{t:<16}{obs:>+9.3f}{f'[{ci[0]:+.3f},{ci[1]:+.3f}]':>20}{or_obs:>7.2f}"
              f"{f'[{or_ci[0]:.2f},{or_ci[1]:.2f}]':>16}{pv:>9.4f}"
              f"{f'[{qci[0]:+.3f},{qci[1]:+.3f}]':>20}")

    for t, hp in zip(tactics, holm(pvals)):
        results[t]["p_holm"] = hp
    print("\nHolm-corrected p: " + "   ".join(
        f"{t}={results[t]['p_holm']:.4f}" for t in tactics))
    print("\n'95% CI (cells)' resamples question x engine cells and is OPTIMISTIC about")
    print("question-to-question variation. '95% CI (3 q)' resamples the three questions")
    print("and is the honest unit -- at n=3 it is thin and wide, and that is the point.")

    # ---- the heading's marginal effect --------------------------------------
    if "faq" in tactics and "answer_first" in tactics:
        hdr("FAQ HEADING, MARGINAL  (faq - answer_first; bodies are byte-identical)")
        d = []
        for p in prompts:
            for m in models:
                kf, nf = cell[(p, m, "faq")]
                ka, na = cell[(p, m, "answer_first")]
                if nf and na:
                    d.append((kf / nf - ka / na, w.get(m, 0.0)))
        dv = np.array([x[0] for x in d]); wv = np.array([x[1] for x in d])
        obs = float((dv * wv).sum() / wv.sum())
        rng = np.random.default_rng(1)
        bs = []
        for _ in range(args.boot):
            i = rng.integers(0, len(dv), len(dv))
            bs.append((dv[i] * wv[i]).sum() / wv[i].sum())
        ci = np.percentile(bs, [2.5, 97.5])
        print(f"delta {obs:+.3f}  95% CI [{ci[0]:+.3f}, {ci[1]:+.3f}]  "
              f"p={perm_p(dv, n=args.perm):.4f}")
        print("\nThe heading carries the question's own words, so this is the heading")
        print("PLUS keyword insertion, never formatting alone. H6 put keyword stuffing")
        print("at +0.038 -- that is the reference point for the keyword component.")

    # ---- per-engine ranking -------------------------------------------------
    hdr("PER-ENGINE (primary; pooled figures depend on the weighting, these do not)")
    print(f"{'engine':<22}{'weight':>8}" + "".join(f"{t[:14]:>16}" for t in tactics))
    for m in models:
        line = f"{m.split('/')[1][:20]:<22}{w.get(m, 0.0):>8.3f}"
        for t in tactics:
            ds = []
            for p in prompts:
                kc, nc_ = cell[(p, m, CONTROL)]
                kt, nt = cell[(p, m, t)]
                if nc_ and nt:
                    ds.append(kt / nt - kc / nc_)
            line += f"{np.mean(ds):>+16.3f}"
        print(line)
    print(f"\nEach figure is a mean over {len(prompts)} questions. The screen excluded one")
    print("engine per question as uninformative there; those cells are included here and")
    print("a round must handle them per its analysis plan.")

    # ---- the pre-committed reading ------------------------------------------
    hdr("PRE-COMMITTED READING  (fixed before collection)")
    best = max(tactics, key=lambda t: results[t]["or"])
    r = results[best]
    print(f"largest tactic: {best}   OR {r['or']:.2f}  95% CI "
          f"[{r['or_ci'][0]:.2f}, {r['or_ci'][1]:.2f}]   "
          f"delta {r['delta']:+.3f}   rate {r['control_rate']:.3f} -> {r['rate']:.3f}")
    if r["or"] >= 1.30:
        v = ("ROUND SIZED AT 25 QUESTIONS (~11 more to source): "
             "largest tactic is at or above OR 1.30.")
    elif r["or"] >= 1.15:
        v = ("ROUND SIZED AT 50 QUESTIONS (~36 more to source): "
             "largest tactic is between OR 1.15 and 1.30.")
    elif r["or_ci"][1] < 1.30:
        v = ("DO NOT SOURCE 36 MORE QUESTIONS AGAINST THESE TACTICS. No tactic clears "
             "OR 1.15 and the interval excludes OR 1.30. Re-anchor targets to longer "
             "spans, re-screen, re-probe; the document-length finding is the main result.")
    else:
        v = ("INCONCLUSIVE: the point estimate is below OR 1.15 but the interval still "
             "reaches OR 1.30. Widen the pilot before sizing the round.")
    print("\n" + "\n".join(v[i:i + 76] for i in range(0, len(v), 76)))
    print("\nThree questions. This sizes a round; it does not rank tactics and the")
    print("numbers above are not a published effect size.")


if __name__ == "__main__":
    main()
