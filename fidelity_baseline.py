#!/usr/bin/env python3
"""
OpenGEO -- baseline misattribution rate from Group C judge output.

Of the answer sentences that cite a page, what share does a judge model find the page
does not support at all (NOT_SUPPORTED)? Pooled over both conditions of the round, on
clean judgments only -- truncated ("length") judgments are missing data, exactly as in
the Group C analysis -- keeping the last row per item_key, since judge files carry
duplicate rows for items retried with --resume.

The unit of resampling is the prompt, not the sentence. Sentences answering the same
question are not independent, and a sentence-level interval would be falsely narrow.

Standard library only.

    python3 fidelity_baseline.py results/fidelity_kwstuff-v3_glm-5.3_full.jsonl \\
        results/fidelity_kwstuff-v3_qwen3.8-max_full.jsonl
    python3 fidelity_baseline.py --json ...    # machine-readable, for results/findings.json
"""
import argparse, json, random
from collections import OrderedDict, defaultdict

RESAMPLES = 10_000
SEED = 20260830
LABELS = ("NOT_SUPPORTED", "PARTIAL", "SUPPORTED")


def load(path):
    last = OrderedDict()
    with open(path) as fh:
        for line in fh:
            if line.strip():
                r = json.loads(line)
                last[r["item_key"]] = r
    return [r for r in last.values()
            if r.get("judge_finish_reason") == "stop" and r.get("judge_label") in LABELS]


def summarise(path):
    rows = load(path)
    counts = defaultdict(lambda: dict.fromkeys(LABELS, 0))
    for r in rows:
        counts[r["prompt_id"]][r["judge_label"]] += 1
    prompts = sorted(counts)

    def share(sample, label):
        k = sum(counts[p][label] for p in sample)
        n = sum(sum(counts[p].values()) for p in sample)
        return k / n

    rng = random.Random(SEED)
    out = {"file": path, "judge": rows[0].get("judge_model") if rows else None,
           "sentences": len(rows), "prompts": len(prompts),
           "resamples": RESAMPLES, "seed": SEED}
    for label in ("NOT_SUPPORTED", "SUPPORTED"):
        boot = sorted(share([rng.choice(prompts) for _ in prompts], label)
                      for _ in range(RESAMPLES))
        out[label] = {"rate": share(prompts, label),
                      "ci": [boot[int(0.025 * RESAMPLES)], boot[int(0.975 * RESAMPLES) - 1]]}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", help="judge_fidelity.py output files")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    results = [summarise(p) for p in args.files]
    if args.json:
        print(json.dumps(results, indent=2))
        return
    print(f"{'judge':22} {'sentences':>9} {'prompts':>7}   {'not supported':>28}   {'supported':>28}")
    for r in results:
        ns, su = r["NOT_SUPPORTED"], r["SUPPORTED"]
        print(f"{str(r['judge']):22} {r['sentences']:>9,} {r['prompts']:>7}   "
              f"{ns['rate']:.4f} [{ns['ci'][0]:.4f}, {ns['ci'][1]:.4f}]   "
              f"{su['rate']:.4f} [{su['ci'][0]:.4f}, {su['ci'][1]:.4f}]")
    print(f"\n95% intervals: bootstrap over prompts, {RESAMPLES:,} resamples, seed {SEED}.")


if __name__ == "__main__":
    main()
