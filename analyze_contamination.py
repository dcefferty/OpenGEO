#!/usr/bin/env python3
"""
OpenGEO -- analysis for the public/private round.

Design and the logged re-scoping of H9: `preregistrations/2026-09-contamination.md`.

  H8  H4 replicates on held-out questions.
      Falsified if the private pooled treatment - control CI includes zero.
  H9  The effect is the same on both halves (re-scoped 2026-09-22 from a contamination
      test to a corpus-equivalence check, because the repository has never been public
      and neither half has been exposed).
      Falsified if the CI on the public - private difference excludes zero.

**The odds ratio is the primary scale for H9.** A risk difference is bounded by its
baseline -- a cell starting at 0.806 cannot rise by 0.48 whatever the intervention does --
and the halves' per-engine baselines differ by up to 0.187. Risk differences are printed
beside the odds ratios, and where the two scales disagree that disagreement is the finding.

**This script will not print private per-prompt figures.** METHODOLOGY 10.1 permits
aggregates only from the private half, permanently; a per-prompt table would burn the
split as surely as publishing the corpus. The restriction is enforced here rather than
left to whoever runs it.

    python3 analyze_contamination.py \
        --public results/runs_contamination_public.jsonl \
        --private private/results/runs_contamination_private.jsonl
"""
import argparse
import json
import math
import sys
from collections import defaultdict

import numpy as np

from analyze import cell_key, incomplete_cells, report_incomplete, wilson
from analyze_lengthonly import holm, load, perm_p
from engine_weights import coverage, weights

NO_CITE_LIMIT = 0.10
MIN_RUNS_FRAC = 0.8


def hdr(t):
    print(f"\n{'=' * 78}\n{t}\n{'=' * 78}")


def dedupe(rows):
    last = {}
    for r in rows:
        last[r["run_key"]] = r
    return list(last.values())


def odds(k, n):
    """Haldane-Anscombe corrected odds, so a saturated cell does not produce an infinity."""
    return (k + 0.5) / (n - k + 0.5)


class Half:
    def __init__(self, name, rows, public):
        self.name, self.public = name, public
        self.rows = dedupe(rows)
        self.prompts = sorted({r["prompt_id"] for r in self.rows})
        self.models = sorted({r["model"] for r in self.rows})
        self.cell = defaultdict(lambda: [0, 0])
        for r in self.rows:
            c = self.cell[(r["prompt_id"], r["model"], r["condition"])]
            c[0] += r["target_cited"]
            c[1] += 1

    def counts(self, model, cond, prompts=None):
        k = n = 0
        for p in (prompts if prompts is not None else self.prompts):
            a, b = self.cell[(p, model, cond)]
            k += a
            n += b
        return k, n

    def deltas(self, model, prompts=None):
        out = []
        for p in (prompts if prompts is not None else self.prompts):
            kc, nc = self.cell[(p, model, "control")]
            kt, nt = self.cell[(p, model, "treatment")]
            if nc and nt:
                out.append(kt / nt - kc / nc)
        return np.array(out)

    def log_or(self, model, prompts=None):
        kc, nc = self.counts(model, "control", prompts)
        kt, nt = self.counts(model, "treatment", prompts)
        if not nc or not nt:
            return float("nan")
        return math.log(odds(kt, nt) / odds(kc, nc))


def boot_prompts(half, model, stat, n=10000, seed=0):
    rng = np.random.default_rng(seed)
    ps = half.prompts
    out = []
    for _ in range(n):
        pick = [ps[i] for i in rng.integers(0, len(ps), len(ps))]
        v = stat(half, model, pick)
        if not (isinstance(v, float) and math.isnan(v)):
            out.append(v)
    return np.array(out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--public", default="results/runs_contamination_public.jsonl")
    ap.add_argument("--private", default="private/results/runs_contamination_private.jsonl")
    ap.add_argument("--boot", type=int, default=10000)
    args = ap.parse_args(argv)

    pub_rows, pub_err = load(args.public)
    priv_rows, priv_err = load(args.private)
    if not pub_rows or not priv_rows:
        sys.exit("both halves are required")

    hdr("DATA HEALTH")
    print(f"public  {len(dedupe(pub_rows)):,} usable, {pub_err} errored")
    print(f"private {len(dedupe(priv_rows)):,} usable, {priv_err} errored")

    # The pre-registration says a dropped cell means resume to completion, not analyse short.
    halt = False
    for label, rows in (("public", pub_rows), ("private", priv_rows)):
        print(f"\n[{label}]")
        _, short, drop = incomplete_cells(dedupe(rows))
        if short:
            report_incomplete(dedupe(rows))
            halt = True
        else:
            print("  all cells complete")
    if halt:
        sys.exit("\nSTOP: the pre-registration requires resuming to completion rather than "
                 "analysing short cells. Run run_pilot.py --resume on the affected half.")

    pub = Half("public", pub_rows, True)
    priv = Half("private", priv_rows, False)
    models = [m for m in pub.models if m in priv.models]

    print(f"\n{'model':<34}{'public no-cite':>16}{'private no-cite':>17}")
    keep = []
    for m in models:
        a = [r for r in pub.rows if r["model"] == m]
        b = [r for r in priv.rows if r["model"] == m]
        na = sum(1 for r in a if not (r.get("cited_doc_ids") or [])) / len(a)
        nb = sum(1 for r in b if not (r.get("cited_doc_ids") or [])) / len(b)
        ok = max(na, nb) <= NO_CITE_LIMIT
        keep.append(m) if ok else None
        print(f"{m:<34}{na:>15.1%}{nb:>16.1%}{'' if ok else '   EXCLUDED'}")
    models = keep
    w = weights(models)
    print(f"\npanel covers {coverage(models):.1%} of measured assistant traffic")
    print(f"public {len(pub.prompts)} prompts, private {len(priv.prompts)} prompts")

    # ---- baselines, against what the pre-registration recorded --------------
    hdr("BASELINE PLACEMENT  (control arm; the pre-registration tabulated these in advance)")
    print(f"{'engine':<34}{'public':>9}{'private':>10}{'diff':>9}")
    for m in models:
        kc, nc = pub.counts(m, "control")
        kd, nd = priv.counts(m, "control")
        print(f"{m:<34}{kc / nc:>9.3f}{kd / nd:>10.3f}{kd / nd - kc / nc:>+9.3f}")

    # ---- H8 -----------------------------------------------------------------
    hdr("H8. DOES H4 REPLICATE ON HELD-OUT QUESTIONS?  (private half)")
    print(f"{'engine':<34}{'control':>9}{'treat':>8}{'delta':>9}{'95% CI':>20}{'p':>9}")
    h8 = {}
    for m in models:
        kc, nc = priv.counts(m, "control")
        kt, nt = priv.counts(m, "treatment")
        d = priv.deltas(m)
        bs = boot_prompts(priv, m, lambda h, mm, ps: h.deltas(mm, ps).mean(), args.boot)
        ci = np.percentile(bs, [2.5, 97.5])
        pv = perm_p(d)
        h8[m] = (float(d.mean()), ci, pv)
        print(f"{m:<34}{kc / nc:>9.3f}{kt / nt:>8.3f}{d.mean():>+9.3f}"
              f"{f'[{ci[0]:+.3f},{ci[1]:+.3f}]':>20}{pv:>9.4f}")
    # share-weighted pooled
    def pooled_delta(half, prompts=None):
        num = den = 0.0
        for m in models:
            d = half.deltas(m, prompts)
            if len(d):
                num += w.get(m, 0.0) * d.mean()
                den += w.get(m, 0.0)
        return num / den if den else float("nan")
    rng = np.random.default_rng(1)
    bs = []
    for _ in range(args.boot):
        pick = [priv.prompts[i] for i in rng.integers(0, len(priv.prompts), len(priv.prompts))]
        bs.append(pooled_delta(priv, pick))
    pci = np.percentile(bs, [2.5, 97.5])
    pd_ = pooled_delta(priv)
    print(f"\n{'POOLED (share-weighted)':<34}{'':>9}{'':>8}{pd_:>+9.3f}"
          f"{f'[{pci[0]:+.3f},{pci[1]:+.3f}]':>20}")
    print(f"\nH8 {'NOT FALSIFIED' if pci[0] > 0 else 'FALSIFIED'}: the private interval "
          f"{'excludes' if pci[0] > 0 else 'includes'} zero.")
    print("For comparison, H4 was +0.493 on corpus v0.3 and +0.482 on v0.4.")

    # ---- H9 -----------------------------------------------------------------
    hdr("H9. ARE THE TWO HALVES EQUIVALENT?  (primary scale: odds ratio)")
    print("Re-scoped 2026-09-22: this is a corpus-equivalence check, not a contamination")
    print("test -- the repository has never been public, so neither half has been exposed.\n")
    print(f"{'engine':<26}{'OR pub':>8}{'OR priv':>9}{'lnOR diff':>11}"
          f"{'95% CI':>20}{'RD diff':>9}")
    rows_h9, pvals = [], []
    for m in models:
        lo_pub, lo_priv = pub.log_or(m), priv.log_or(m)
        bp = boot_prompts(pub, m, lambda h, mm, ps: h.log_or(mm, ps), args.boot, seed=2)
        bq = boot_prompts(priv, m, lambda h, mm, ps: h.log_or(mm, ps), args.boot, seed=3)
        n = min(len(bp), len(bq))
        diff_bs = bp[:n] - bq[:n]
        ci = np.percentile(diff_bs, [2.5, 97.5])
        d = lo_pub - lo_priv
        # two-sided bootstrap p: how much mass lies on the far side of zero
        pv = 2 * min((diff_bs <= 0).mean(), (diff_bs >= 0).mean())
        rd = pub.deltas(m).mean() - priv.deltas(m).mean()
        rows_h9.append((m, math.exp(lo_pub), math.exp(lo_priv), d, ci, rd, pv))
        pvals.append(pv)
    for (m, orp, orq, d, ci, rd, pv), hp in zip(rows_h9, holm(pvals)):
        flag = "  *" if hp < 0.05 else ""
        print(f"{m.split('/')[1][:24]:<26}{orp:>8.2f}{orq:>9.2f}{d:>+11.3f}"
              f"{f'[{ci[0]:+.3f},{ci[1]:+.3f}]':>20}{rd:>+9.3f}{flag}")
    print("\n* = Holm-corrected across the five engines, p < .05")

    # pooled lnOR difference
    def pooled_lnor(half, prompts=None):
        num = den = 0.0
        for m in models:
            v = half.log_or(m, prompts)
            if not math.isnan(v):
                num += w.get(m, 0.0) * v
                den += w.get(m, 0.0)
        return num / den if den else float("nan")
    rngp = np.random.default_rng(4)
    rngq = np.random.default_rng(5)
    bs = []
    for _ in range(args.boot):
        pp = [pub.prompts[i] for i in rngp.integers(0, len(pub.prompts), len(pub.prompts))]
        qq = [priv.prompts[i] for i in rngq.integers(0, len(priv.prompts), len(priv.prompts))]
        bs.append(pooled_lnor(pub, pp) - pooled_lnor(priv, qq))
    bs = np.array(bs)
    ci = np.percentile(bs, [2.5, 97.5])
    obs = pooled_lnor(pub) - pooled_lnor(priv)
    pv = 2 * min((bs <= 0).mean(), (bs >= 0).mean())
    print(f"\nPOOLED lnOR difference  {obs:+.3f}  95% CI [{ci[0]:+.3f}, {ci[1]:+.3f}]  "
          f"p={pv:.4f}")
    print(f"  as a ratio of odds ratios: {math.exp(obs):.2f}x")
    falsified = ci[0] > 0 or ci[1] < 0
    print(f"\nH9 {'FALSIFIED' if falsified else 'NOT FALSIFIED'}: the interval "
          f"{'excludes' if falsified else 'includes'} zero.")
    if falsified:
        print("  The halves are NOT interchangeable. Under the logged re-scoping this means")
        print("  the corpora differ, not that contamination was found.")
    else:
        print("  The halves behave equivalently, which is the precondition for the split")
        print("  serving as a comparator in a post-publication re-run.")

    # ---- variance components ------------------------------------------------
    hdr("VARIANCE COMPONENTS  (eta-squared)")
    allrows = [(r, True) for r in pub.rows] + [(r, False) for r in priv.rows]
    allrows = [(r, p) for r, p in allrows if r["model"] in models]
    y = np.array([r["target_cited"] for r, _ in allrows], float)
    grand = y.mean()
    ss_tot = ((y - grand) ** 2).sum()
    for label, key in (("condition", lambda r, p: r["condition"]),
                       ("half (public/private)", lambda r, p: p),
                       ("prompt identity", lambda r, p: (p, r["prompt_id"])),
                       ("target format", lambda r, p: r.get("target_format")),
                       ("model", lambda r, p: r["model"])):
        g = defaultdict(list)
        for (r, p), v in zip(allrows, y):
            g[key(r, p)].append(v)
        ssb = sum(len(v) * (np.mean(v) - grand) ** 2 for v in g.values())
        print(f"  {label:<26}{ssb / ss_tot:.4f}")
    print("\n'half' is the term of interest and has not been estimated before.")

    hdr("REPORTING CONSTRAINT")
    print("Per METHODOLOGY 10.1 the private half is reported as aggregates only, and this")
    print("script prints none of its per-prompt figures. That restriction is permanent:")
    print("a per-prompt table would burn the split as surely as publishing the corpus.")


if __name__ == "__main__":
    main()
