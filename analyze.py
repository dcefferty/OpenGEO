#!/usr/bin/env python3
"""
OpenGEO pilot analysis — computes the candidate metrics and tests H1-H5.

    python3 analyze.py --runs results/runs.jsonl

Requires numpy only. All inference is permutation- or bootstrap-based so there
are no distributional assumptions to argue about and anyone can re-run it.
"""
import argparse, json, pathlib, sys
from collections import defaultdict, Counter
import numpy as np

RNG = np.random.default_rng(20260811)


# ---------- interval helpers ----------

def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def boot_ci(x, stat=np.mean, n=4000, alpha=.05):
    x = np.asarray(x, dtype=float)
    if len(x) == 0:
        return (np.nan, np.nan)
    idx = RNG.integers(0, len(x), size=(n, len(x)))
    d = np.array([stat(x[i]) for i in idx])
    return tuple(np.percentile(d, [100 * alpha / 2, 100 * (1 - alpha / 2)]))


def perm_test_paired(d, n=20000):
    """Sign-flip permutation test on per-unit paired differences."""
    d = np.asarray(d, dtype=float)
    d = d[~np.isnan(d)]
    if len(d) == 0:
        return np.nan, np.nan
    obs = d.mean()
    signs = RNG.choice([-1.0, 1.0], size=(n, len(d)))
    null = (signs * d).mean(axis=1)
    p = (np.sum(np.abs(null) >= abs(obs)) + 1) / (n + 1)
    return obs, p


def kendall_w(rank_matrix):
    """rank_matrix: (m raters x n items) of ranks. Returns W in [0,1]."""
    r = np.asarray(rank_matrix, dtype=float)
    m, n = r.shape
    if m < 2 or n < 2:
        return np.nan
    Rj = r.sum(axis=0)
    S = ((Rj - Rj.mean()) ** 2).sum()
    return 12 * S / (m ** 2 * (n ** 3 - n))


def hdr(t):
    print("\n" + "=" * 74)
    print(t)
    print("=" * 74)


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="results/runs.jsonl")
    ap.add_argument("--corpus", default="corpus/corpus_v0.2.json")
    args = ap.parse_args()

    path = pathlib.Path(args.runs)
    if not path.exists():
        sys.exit(f"no results at {path} — run run_pilot.py first")

    recs, errs = [], 0
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("error"):
            errs += 1
        else:
            recs.append(r)

    if not recs:
        sys.exit("no successful runs to analyse")

    models = sorted({r["model"] for r in recs})
    prompts = sorted({r["prompt_id"] for r in recs})
    n_docs = recs[0]["n_docs"]

    hdr("DATA HEALTH")
    print(f"successful runs : {len(recs):,}   errors: {errs}")
    print(f"models          : {len(models)}   prompts: {len(prompts)}   docs/prompt: {n_docs}")
    no_cite = sum(1 for r in recs if not r["cited_doc_ids"])
    print(f"runs citing nothing parseable : {no_cite} ({100*no_cite/len(recs):.1f}%)")
    ncit = [len(r["cited_doc_ids"]) for r in recs]
    print(f"citations per answer          : mean {np.mean(ncit):.2f}  median {np.median(ncit):.0f}")
    print("\nper-model citation-parse health (high no-cite rate = instruction-following failure,")
    print("not a visibility signal — such a model must be excluded, not averaged in):")
    for m in models:
        sub = [r for r in recs if r["model"] == m]
        nc = sum(1 for r in sub if not r["cited_doc_ids"])
        print(f"  {m:<38} n={len(sub):<5} no-cite={100*nc/len(sub):5.1f}%  "
              f"cites/answer={np.mean([len(r['cited_doc_ids']) for r in sub]):.2f}")

    # ---------------- A1: CPR ----------------
    hdr("A1. CITATION PRESENCE RATE (target document), by model")
    print(f"{'model':<38} {'CPR':>7}  {'Wilson 95% CI':>18}  {'n':>5}")
    cpr_by_model = {}
    for m in models:
        sub = [r for r in recs if r["model"] == m]
        k = sum(r["target_cited"] for r in sub)
        lo, hi = wilson(k, len(sub))
        cpr_by_model[m] = k / len(sub)
        print(f"{m:<38} {k/len(sub):>7.3f}  [{lo:.3f}, {hi:.3f}]{'':>4}  {len(sub):>5}")

    # ---------------- H2 / D1: position ----------------
    hdr("H2 / D1. POSITION SENSITIVITY INDEX  (identical content, different slot)")
    print("If PSI is large, slot in the candidate set outweighs anything written on the page.\n")
    print(f"{'model':<30} " + " ".join(f"s{i}" .rjust(6) for i in range(n_docs)) + f" {'PSI':>7} {'p':>8}")
    psi_rows = []
    for m in models:
        sub = [r for r in recs if r["model"] == m]
        by_slot = defaultdict(list)
        for r in sub:
            by_slot[r["target_slot"]].append(r["target_cited"])
        rates = [np.mean(by_slot[i]) if by_slot[i] else np.nan for i in range(n_docs)]
        psi = np.nanmax(rates) - np.nanmin(rates)
        # permutation test: shuffle slot labels within model
        y = np.array([r["target_cited"] for r in sub], dtype=float)
        s = np.array([r["target_slot"] for r in sub])
        obs = psi
        null = []
        for _ in range(2000):
            sp = RNG.permutation(s)
            rr = [y[sp == i].mean() if (sp == i).any() else np.nan for i in range(n_docs)]
            null.append(np.nanmax(rr) - np.nanmin(rr))
        p = (np.sum(np.array(null) >= obs) + 1) / 2001
        psi_rows.append((m, psi, p))
        print(f"{m:<30} " + " ".join(f"{r:6.3f}" if not np.isnan(r) else "   nan" for r in rates)
              + f" {psi:>7.3f} {p:>8.4f}")

    pooled_psi = np.mean([p for _, p, _ in psi_rows])
    print(f"\nmean PSI across models: {pooled_psi:.3f}")
    print("H2 verdict:", "SUPPORTED — position effect is material"
          if pooled_psi >= 0.05 else "NOT SUPPORTED — position effect is small")

    # slot profile pooled
    by_slot = defaultdict(list)
    for r in recs:
        by_slot[r["target_slot"]].append(r["target_cited"])
    print("\npooled slot profile (tests the 'lost in the middle' shape):")
    for i in range(n_docs):
        v = by_slot[i]
        lo, hi = wilson(sum(v), len(v))
        bar = "#" * int(round(np.mean(v) * 40))
        print(f"  slot {i}: {np.mean(v):.3f} [{lo:.3f},{hi:.3f}] n={len(v):<5} {bar}")

    # ---------------- H4: treatment ----------------
    hdr("H4. CLAIM-DENSITY INTERVENTION  (paired, per prompt)")
    print("Tests Profound's assertion that specific extractable claims raise citation.\n")
    print(f"{'model':<34} {'control':>8} {'treat':>8} {'delta':>8} {'95% CI':>18} {'p':>8}")
    for m in models + ["ALL MODELS POOLED"]:
        sub = [r for r in recs if (m == "ALL MODELS POOLED" or r["model"] == m)]
        diffs, cs, ts = [], [], []
        for p_id in prompts:
            c = [r["target_cited"] for r in sub if r["prompt_id"] == p_id and r["condition"] == "control"]
            t = [r["target_cited"] for r in sub if r["prompt_id"] == p_id and r["condition"] == "treatment"]
            if c and t:
                diffs.append(np.mean(t) - np.mean(c)); cs.append(np.mean(c)); ts.append(np.mean(t))
        if not diffs:
            continue
        obs, pv = perm_test_paired(diffs)
        lo, hi = boot_ci(diffs)
        star = " *" if pv < .05 else ""
        print(f"{m:<34} {np.mean(cs):>8.3f} {np.mean(ts):>8.3f} {obs:>+8.3f} "
              f"[{lo:>+.3f},{hi:>+.3f}] {pv:>8.4f}{star}")
    print("\nNOTE: treatment docs average ~11 words longer than control. Length is a")
    print("confound in this corpus version; a null here is interpretable, a positive")
    print("result needs the length-matched corpus (v0.2) before it means anything.")

    # ---------------- H3: cross-model agreement ----------------
    hdr("H3. CROSS-MODEL AGREEMENT  (Kendall's W on document citation rates)")
    print("Low W => 'AI visibility' is not one quantity and a single score is incoherent.")
    print("CRITICAL: raw W has a noise floor. At finite runs a model does not even agree")
    print("with ITSELF, so cross-model W must be read against a within-model baseline.")
    print("We compute both. Only the gap between them is evidence of real disagreement.\n")

    def doc_rank_vector(sub, docs_sorted):
        rate = [np.mean([d in r["cited_doc_ids"] for r in sub]) if sub else 0.0
                for d in docs_sorted]
        a = np.asarray(rate)
        tmp = a.argsort()[::-1]
        ranks = np.empty(len(a), float)
        ranks[tmp] = np.arange(1, len(a) + 1)
        return ranks

    ws, ws_null = [], []
    for p_id in prompts:
        docs_sorted = sorted(set(
            d for r in recs if r["prompt_id"] == p_id for d in r["presentation_order"]))
        mat, null_mat = [], []
        for m in models:
            sub = [r for r in recs if r["prompt_id"] == p_id and r["model"] == m]
            if not sub:
                continue
            mat.append(doc_rank_vector(sub, docs_sorted))
            # within-model split-half: two pseudo-raters from the SAME model
            idx = RNG.permutation(len(sub))
            h = len(sub) // 2
            if h >= 2:
                null_mat.append(doc_rank_vector([sub[i] for i in idx[:h]], docs_sorted))
                null_mat.append(doc_rank_vector([sub[i] for i in idx[h:2 * h]], docs_sorted))
        if len(mat) >= 2:
            ws.append(kendall_w(np.array(mat)))
        if len(null_mat) >= 2:
            ws_null.append(kendall_w(np.array(null_mat)))

    if ws:
        lo, hi = boot_ci(ws)
        print(f"  cross-model W  : {np.mean(ws):.3f}  [{lo:.3f}, {hi:.3f}]")
        if ws_null:
            nlo, nhi = boot_ci(ws_null)
            print(f"  within-model W : {np.mean(ws_null):.3f}  [{nlo:.3f}, {nhi:.3f}]"
                  f"   <- noise floor (same model, split-half)")
            gap = np.mean(ws_null) - np.mean(ws)
            print(f"  gap            : {gap:+.3f}")
            if np.mean(ws_null) < 0.35:
                print("\n  W is uninformative at this sample size — the noise floor is too")
                print("  high to detect disagreement. Increase runs per cell before reading H3.")
            elif gap > 0.15:
                print("\n  H3 SUPPORTED — models agree with themselves far more than with each")
                print("  other, so a single cross-model 'visibility score' is not coherent.")
            else:
                print("\n  H3 NOT SUPPORTED — cross-model agreement is close to the noise floor,")
                print("  i.e. no evidence models rank sources differently from one another.")

    # pairwise model correlation on target CPR across prompts
    print("\npairwise correlation of per-prompt target CPR between models:")
    vec = {}
    for m in models:
        vec[m] = np.array([np.mean([r["target_cited"] for r in recs
                                    if r["model"] == m and r["prompt_id"] == p]) for p in prompts])
    cors = []
    for i, a in enumerate(models):
        for b in models[i + 1:]:
            if np.std(vec[a]) > 0 and np.std(vec[b]) > 0:
                cors.append(np.corrcoef(vec[a], vec[b])[0, 1])
    if cors:
        print(f"  mean pairwise r = {np.mean(cors):.3f}  (min {np.min(cors):.3f}, max {np.max(cors):.3f})")

    # ---------------- H1: reliability ----------------
    hdr("H1. RELIABILITY  (split-half on CPR, Spearman-Brown corrected)")
    print("A metric that cannot reproduce itself across half-samples cannot support a claim.\n")
    for m in models:
        A, B = [], []
        for p_id in prompts:
            for cond in ("control", "treatment"):
                sub = [r for r in recs if r["model"] == m and r["prompt_id"] == p_id
                       and r["condition"] == cond]
                if len(sub) < 4:
                    continue
                y = np.array([r["target_cited"] for r in sub], dtype=float)
                idx = RNG.permutation(len(y))
                h = len(y) // 2
                A.append(y[idx[:h]].mean()); B.append(y[idx[h:2 * h]].mean())
        if len(A) > 3 and np.std(A) > 0 and np.std(B) > 0:
            r_half = np.corrcoef(A, B)[0, 1]
            sb = 2 * r_half / (1 + r_half) if r_half > -1 else np.nan
            flag = "" if sb >= .5 else "   <-- below usable threshold"
            print(f"  {m:<38} split-half r={r_half:>6.3f}  Spearman-Brown={sb:>6.3f}{flag}")
        else:
            print(f"  {m:<38} insufficient variance to estimate")

    # reliability as a function of runs per cell -> tells you what Round 1 needs
    print("\nreliability vs runs per cell (pooled across models; subsampled from data):")
    max_rep = max(r["rep"] for r in recs) + 1
    for k in [n for n in (4, 6, 10, 16, 24, 40) if n <= max_rep]:
        A, B = [], []
        for m in models:
            for p_id in prompts:
                for cond in ("control", "treatment"):
                    sub = [r for r in recs if r["model"] == m and r["prompt_id"] == p_id
                           and r["condition"] == cond]
                    if len(sub) < k:
                        continue
                    idx = RNG.permutation(len(sub))[:k]
                    y = np.array([sub[i]["target_cited"] for i in idx], dtype=float)
                    h = k // 2
                    A.append(y[:h].mean()); B.append(y[h:2 * h].mean())
        if len(A) > 5 and np.std(A) > 0 and np.std(B) > 0:
            rh = np.corrcoef(A, B)[0, 1]
            sb = 2 * rh / (1 + rh) if rh > -1 else np.nan
            mark = "  <- usable" if sb >= .7 else ("  <- marginal" if sb >= .5 else "")
            print(f"    n={k:<3} split-half r={rh:>6.3f}  Spearman-Brown={sb:>6.3f}{mark}")
    print("  (Spearman-Brown here estimates reliability at n/2; the full-cell value is")
    print("   higher. Use this to choose runs per cell for Round 1, not to judge n=10.)")

    # ---------------- H5: format ----------------
    hdr("H5. CONTENT FORMAT  (is the metric format-universal?)")
    print(f"{'format':<12} {'CPR':>7} {'Wilson 95% CI':>18} {'n':>6}   per-model spread")
    fmts = sorted({r["target_format"] for r in recs})
    for f in fmts:
        sub = [r for r in recs if r["target_format"] == f]
        k = sum(r["target_cited"] for r in sub)
        lo, hi = wilson(k, len(sub))
        per = [np.mean([r["target_cited"] for r in sub if r["model"] == m])
               for m in models if any(r["model"] == m for r in sub)]
        print(f"{f:<12} {k/len(sub):>7.3f} [{lo:.3f}, {hi:.3f}]{'':>3} {len(sub):>6}   "
              f"{np.min(per):.2f}-{np.max(per):.2f}")

    # how much of the variance is format vs model vs prompt vs slot?
    hdr("VARIANCE DECOMPOSITION  (what actually drives citation?)")
    print("Between-group variance in target CPR attributable to each factor.")
    print("This is the number that tells you where optimisation effort belongs.\n")
    y = np.array([r["target_cited"] for r in recs], dtype=float)
    tot = y.var()
    for name, keyf in (("model", lambda r: r["model"]),
                       ("prompt", lambda r: r["prompt_id"]),
                       ("target slot (position)", lambda r: r["target_slot"]),
                       ("content format", lambda r: r["target_format"]),
                       ("domain", lambda r: r["domain"]),
                       ("condition (claim density)", lambda r: r["condition"])):
        g = defaultdict(list)
        for r in recs:
            g[keyf(r)].append(r["target_cited"])
        means = np.array([np.mean(v) for v in g.values()])
        ns = np.array([len(v) for v in g.values()])
        between = np.sum(ns * (means - y.mean()) ** 2) / len(y)
        print(f"  {name:<28} eta^2 = {between/tot:6.3f}   "
              f"({len(g)} levels, range {means.min():.3f}-{means.max():.3f})")

    hdr("SUMMARY")
    print(f"  mean PSI (position)         : {pooled_psi:.3f}")
    if ws:
        print(f"  Kendall's W (model agreement): {np.mean(ws):.3f}")
    print(f"  target CPR overall          : {np.mean([r['target_cited'] for r in recs]):.3f}")
    print("\nRemember: this is the synthesis stage only, with retrieval held constant.")
    print("It says nothing about whether a page gets retrieved in the first place.")


if __name__ == "__main__":
    main()
