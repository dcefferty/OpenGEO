#!/usr/bin/env python3
"""
Synthetic runs for the real-text H4 round, with KNOWN planted effects, to verify
that screen_realtext_h4.py and analyze_realtext_h4.py recover them before any
money is spent.

    python3 make_mock_realtext_h4.py --screen                 # control-only batch runs
    python3 screen_realtext_h4.py --corpus corpus/corpus_realtext_h4_b1.json \\
        --runs results/mock_realtext_h4_screen.jsonl
    python3 make_mock_realtext_h4.py                          # both arms, planted effect
    python3 analyze_realtext_h4.py --corpus corpus/corpus_realtext_h4_b1.json \\
        --runs results/mock_realtext_h4.jsonl
    python3 make_mock_realtext_h4.py --null --seed 7          # planted null

Each prompt gets a planted control log-odds (PROMPT_BASE, chosen so the screen
must keep some questions and discard others), an engine offset, and a treatment
effect scaled per engine. Treated answers state the answer at a planted rate and
control answers at a lower one, so the echo reader is exercised. The unchanged
documents lose a planted amount of citation under treatment, for the
displacement secondary. Ground truth is printed on the probability scale,
share-weighted, from the same probabilities the runs are drawn from.
"""
import argparse
import hashlib
import json
import pathlib
import random

import numpy as np

from engine_weights import weights

HERE = pathlib.Path(__file__).parent

# control log-odds per prompt, in corpus order; cycled if the corpus is longer.
# expit: -2.2 -> 0.10, -0.4 -> 0.40, 0.0 -> 0.50, 0.5 -> 0.62, 1.8 -> 0.86, -0.8 -> 0.31
PROMPT_BASE = [-2.2, -0.4, 0.0, 0.5, 1.8, -0.8]
PLANTED = {
    "treatment": 2.0,
    "engine_scale": {
        "openai/gpt-5.4-mini": 1.3, "google/gemini-3-flash-preview": 0.7,
        "anthropic/claude-haiku-4.5": 1.1, "deepseek/deepseek-chat": 0.9,
        "x-ai/grok-4.3": 0.8,
    },
    "model_baseline": {
        "openai/gpt-5.4-mini": -0.3, "google/gemini-3-flash-preview": 0.4,
        "anthropic/claude-haiku-4.5": -0.4, "deepseek/deepseek-chat": 0.2,
        "x-ai/grok-4.3": 0.3,
    },
    "others_base": 0.0,
    "others_shift": -0.6,          # log-odds shift on unchanged documents under treatment
    "echo": {"control": 0.10, "treatment": 0.70},
}
ECHO_TEXT = {
    "taxes_employment_records": "keep them for 4 years",
    "cyber_password_length": "at least 15 characters",
    "nutrition_caffeine_limit": "400 mg a day",
    "cooking_leftovers_room_temp": "no more than 2 hours",
    "home_radon_action_level": "4 pCi/L",
    "finance_emergency_400": "63 percent",
}


def expit(x):
    return 1 / (1 + np.exp(-x))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=str(HERE / "corpus" / "corpus_realtext_h4_b1.json"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--runs", type=int, default=24)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--null", action="store_true", help="plant no treatment effect")
    ap.add_argument("--screen", action="store_true", help="control arm only, as the screen runs")
    args = ap.parse_args()

    corpus = json.loads(pathlib.Path(args.corpus).read_text())
    out = pathlib.Path(args.out or HERE / "results" /
                       ("mock_realtext_h4_screen.jsonl" if args.screen else "mock_realtext_h4.jsonl"))
    rng = np.random.default_rng(args.seed)
    models = list(PLANTED["model_baseline"])
    w = weights(models)
    conds = ["control"] if args.screen else ["control", "treatment"]
    eff = 0.0 if args.null else PLANTED["treatment"]
    shift = 0.0 if args.null else PLANTED["others_shift"]
    truth, truth_base, truth_disp, pooled_ctl = [], [], [], {}

    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with out.open("w") as fh:
        for i, p in enumerate(corpus["prompts"]):
            pb = PROMPT_BASE[i % len(PROMPT_BASE)]
            t_delta = t_base = t_disp = 0.0
            ctl = []
            for m in models:
                base = pb + PLANTED["model_baseline"][m]
                pr = {"control": expit(base),
                      "treatment": expit(base + PLANTED["engine_scale"][m] * eff)}
                po = {"control": expit(PLANTED["others_base"]),
                      "treatment": expit(PLANTED["others_base"] + shift)}
                t_delta += w[m] * (pr["treatment"] - pr["control"])
                t_base += w[m] * pr["control"]
                t_disp += w[m] * (po["treatment"] - po["control"])
                ctl.append(pr["control"])
                for cond in conds:
                    for rep in range(args.runs):
                        key = f"{m}|{p['prompt_id']}|{cond}|{rep}"
                        order = list(p["doc_ids"])
                        seed = int(hashlib.sha256(
                            f"{corpus['corpus_version']}|{key}".encode()).hexdigest()[:12], 16)
                        random.Random(seed).shuffle(order)
                        cited = [d for d in order
                                 if rng.random() < (pr[cond] if d == p["target_doc_id"] else po[cond])]
                        rng.shuffle(cited)
                        text = "MOCK answer."
                        if rng.random() < PLANTED["echo"][cond]:
                            text += " " + ECHO_TEXT.get(p["prompt_id"], "")
                        hit = p["target_doc_id"] in cited
                        fh.write(json.dumps({
                            "run_key": key, "harness_version": "MOCK",
                            "timestamp_utc": "2026-11-07T00:00:00+00:00",
                            "corpus_version": corpus["corpus_version"], "model": m,
                            "model_returned": m, "prompt_id": p["prompt_id"],
                            "domain": p["domain"], "condition": cond, "rep": rep,
                            "temperature": 1.0, "presentation_order": order,
                            "target_doc_id": p["target_doc_id"],
                            "target_format": p["target_format"],
                            "target_slot": order.index(p["target_doc_id"]),
                            "n_docs": len(order), "response_text": text,
                            "cited_doc_ids": cited,
                            "cited_display_idx": [order.index(d) + 1 for d in cited],
                            "target_cited": hit,
                            "target_cite_rank": cited.index(p["target_doc_id"]) if hit else None,
                            "sentence_citations": [],
                        }) + "\n")
                        n += 1
            truth.append(t_delta)
            truth_base.append(t_base)
            truth_disp.append(t_disp)
            pooled_ctl[p["prompt_id"]] = float(np.mean(ctl))

    print(f"wrote {n:,} mock runs -> {out}")
    if args.screen:
        print("\nPLANTED control CPR per question, unweighted across engines "
              "(the screen should KEEP those in [0.25, 0.75]):")
        for pid, v in pooled_ctl.items():
            print(f"  {pid:<32}{v:.3f}  {'KEEP' if 0.25 <= v <= 0.75 else 'DISCARD'}")
        return
    print("\nPLANTED GROUND TRUTH, share-weighted, probability scale")
    print("(analyze_realtext_h4.py's share-weighted intervals should contain these):")
    print(f"  H4-RT    {np.mean(truth):+.4f}   (control baseline {np.mean(truth_base):.3f})")
    print(f"  H4-RT-b  {np.mean(truth_disp):+.4f}")
    print(f"planted echo rates: control {PLANTED['echo']['control']:.2f}, "
          f"treatment {PLANTED['echo']['treatment']:.2f}")


if __name__ == "__main__":
    main()
