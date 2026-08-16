#!/usr/bin/env python3
"""
Round 1 power sizing.

    python3 size_round1.py --runs results/runs.jsonl

Why this exists instead of reusing METHODOLOGY.md's original power table:
that table assumed per-prompt baseline visibility ~ Beta(1.2, 3) (mean ~29%),
a reasonable guess made before any real data existed. The pilot found real
control-condition CPR averaging 87%, with 56 of 84 (prompt, model) cells at a
literal 100% ceiling. A treatment effect has almost no room to show up as a
probability increase against a near-ceiling baseline, which changes the power
picture substantially -- so this script resamples the pilot's own empirical
(prompt, model) baseline cells (bootstrap, not a distributional assumption)
instead of the old prior, and simulates the exact sign-flip permutation test
analyze.py's pooled H4 test uses, so the simulated p-values mean the same
thing a real Round 1 analysis would produce.

Also runs the same grid against the original Beta(1.2, 3) assumption, printed
side by side, so the size of the discrepancy is visible rather than asserted.

Standard-library + numpy only, per CLAUDE.md's stack constraints. No
distributional test assumptions beyond the binomial data-generating process
itself, which is a fact about the outcome (a citation either happens or not),
not a modeling choice.
"""
import argparse, json, pathlib, sys
import numpy as np

RNG = np.random.default_rng(20260815)

EXCLUDED_MODELS = {"moonshotai/kimi-k2"}  # 34.4% no-cite rate in the pilot; see pre-registration


def load_empirical_cell_rates(path, exclude=EXCLUDED_MODELS):
    recs = [json.loads(l) for l in pathlib.Path(path).read_text().splitlines() if l.strip()]
    recs = [r for r in recs if not r.get("error") and r["model"] not in exclude
            and r["condition"] == "control"]
    cells = {}
    for r in recs:
        key = (r["prompt_id"], r["model"])
        cells.setdefault(key, [0, 0])
        cells[key][0] += r["target_cited"]
        cells[key][1] += 1
    n_models = len({m for _, m in cells})
    raw_rates = np.array([k / n for k, n in cells.values()])
    # continuity-corrected rate so ceiling/floor cells don't produce +-inf logits
    rates = np.array([(k + 0.5) / (n + 1) for k, n in cells.values()])
    return rates, raw_rates, n_models, cells


def logit(p):
    return np.log(p / (1 - p))


def expit(x):
    return 1 / (1 + np.exp(-x))


def simulate_power(cell_rates, n_models, n_prompts, runs_per_arm, log_or,
                    n_mc=400, n_perm=400, alpha=0.05):
    """Vectorized Monte Carlo: for each of n_mc simulated Round-1-shaped
    datasets, resample n_prompts x n_models baseline rates from cell_rates
    (bootstrap), plant log_or on the treatment arm, simulate runs_per_arm
    binomial draws per (prompt, model, condition) cell, pool across models
    per prompt (matching analyze.py's ALL-MODELS-POOLED H4 test), then run
    the same sign-flip permutation test on the per-prompt differences."""
    shape = (n_mc, n_prompts, n_models)
    base_p = RNG.choice(cell_rates, size=shape)
    treat_p = expit(logit(base_p) + log_or)

    k_c = RNG.binomial(runs_per_arm, base_p)
    k_t = RNG.binomial(runs_per_arm, treat_p)
    p_c = k_c.sum(axis=2) / (n_models * runs_per_arm)   # (n_mc, n_prompts)
    p_t = k_t.sum(axis=2) / (n_models * runs_per_arm)
    diffs = (p_t - p_c).astype(np.float32)               # (n_mc, n_prompts)
    obs = diffs.mean(axis=1)                             # (n_mc,)

    signs = RNG.choice(np.array([-1.0, 1.0], dtype=np.float32), size=(n_mc, n_perm, n_prompts))
    null = (signs * diffs[:, None, :]).mean(axis=2)      # (n_mc, n_perm)
    p_vals = (np.sum(np.abs(null) >= np.abs(obs)[:, None], axis=1) + 1) / (n_perm + 1)
    return float(np.mean(p_vals < alpha))


def beta_prior_rates(n=20000, a=1.2, b=3.0):
    return RNG.beta(a, b, size=n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="results/runs.jsonl")
    ap.add_argument("--n-mc", type=int, default=400)
    ap.add_argument("--n-perm", type=int, default=400)
    ap.add_argument("--prompts", default="12,25,50,100")
    ap.add_argument("--runs-per-arm", default="10,20,24,30,40")
    ap.add_argument("--ors", default="1.3,1.5,2.0")
    ap.add_argument("--models", type=int, default=None,
                     help="models pooled per prompt; default = valid model count from --runs")
    args = ap.parse_args()

    path = pathlib.Path(args.runs)
    if not path.exists():
        sys.exit(f"no results at {path} — run run_pilot.py first")

    cell_rates, raw_rates, n_models_observed, cells = load_empirical_cell_rates(path)
    n_models = args.models or n_models_observed
    prompts_grid = [int(x) for x in args.prompts.split(",")]
    runs_grid = [int(x) for x in args.runs_per_arm.split(",")]
    or_grid = [float(x) for x in args.ors.split(",")]
    beta_rates = beta_prior_rates()

    print("=" * 84)
    print("EMPIRICAL BASELINE (from real pilot control-condition data)")
    print("=" * 84)
    print(f"(prompt, model) cells: {len(cell_rates)}   models pooled per prompt: {n_models}")
    print(f"empirical control CPR: mean={raw_rates.mean():.3f}  sd={raw_rates.std():.3f}")
    ceiling = np.mean(raw_rates == 1.0)
    print(f"cells at a literal 100% ceiling (24/24): {100*ceiling:.0f}%")
    print(f"vs. METHODOLOGY.md's original assumption, Beta(1.2,3): "
          f"mean={beta_rates.mean():.3f}  sd={beta_rates.std():.3f}")
    print("\nThe gap between these two rows is the whole point of this script: the original")
    print("power table was sized for a ~29% baseline. Real baseline is ~87% and frequently")
    print("at a literal ceiling, which compresses the room a treatment effect has to move.")

    for label, rates in (("REAL PILOT DATA (empirical bootstrap)", cell_rates),
                          ("OLD ASSUMPTION (Beta(1.2,3) prior)", beta_rates)):
        print("\n" + "=" * 84)
        print(f"POWER TABLE — {label}")
        print("=" * 84)
        header = f"{'prompts':>7} {'runs/arm':>9} {'calls':>8}  " + \
                 "  ".join(f"OR {o:>4}" for o in or_grid)
        print(header)
        for p in prompts_grid:
            for r in runs_grid:
                calls = p * n_models * r * 2
                row = f"{p:>7} {r:>9} {calls:>8,}  "
                for o in or_grid:
                    power = simulate_power(rates, n_models, p, r, np.log(o),
                                            n_mc=args.n_mc, n_perm=args.n_perm)
                    row += f"  {power:>6.2f}"
                print(row)

    print("\n" + "=" * 84)
    print("READING THIS TABLE")
    print("=" * 84)
    print("Columns are power (proportion of simulated rounds reaching p<0.05) to detect")
    print("each odds ratio, at n_mc={} / n_perm={} Monte Carlo replicates. 'calls' assumes"
          .format(args.n_mc, args.n_perm))
    print(f"{n_models} models (the pilot's roster minus kimi-k2) and 2 arms per prompt.")
    print("Compare the two tables above at the same (prompts, runs/arm) cell: the real-data")
    print("table is the one to design Round 1 against. The Beta(1.2,3) table is kept only")
    print("to show how much the original, pre-pilot assumption would have mis-sized this.")


if __name__ == "__main__":
    main()
