#!/usr/bin/env python3
"""
Synthetic runs for the competition round, with KNOWN planted effects, to verify
that analyze_competition.py recovers them before any money is spent.

    python3 make_mock_competition.py
    python3 analyze_competition.py --runs results/mock_competition.jsonl

Planted on the log-odds scale (PLANTED below): a treatment effect, a penalty
for the competitor's presence, a negative treatment x competitor interaction,
and a competitor that loses citations when the target is treated. Ground truth
is also printed on the probability scale, computed from the same draws, so
each analyser interval can be checked against the number it should contain.
"""
import argparse
import hashlib
import json
import pathlib
import random

import numpy as np

from engine_weights import weights

HERE = pathlib.Path(__file__).parent

PLANTED = {
    "target_base": -0.30,
    "treatment": 1.20,
    "competitor_present": -0.60,
    "interaction": -0.40,
    "competitor_base": 1.00,
    "competitor_when_treated": -0.50,
    "model_baseline": {
        "openai/gpt-5.4-mini": 0.10, "google/gemini-3-flash-preview": 0.60,
        "anthropic/claude-haiku-4.5": -0.40, "deepseek/deepseek-chat": 0.30,
        "x-ai/grok-4.3": 0.70,
    },
    "prompt_sd": 0.55,
}


def expit(x):
    return 1 / (1 + np.exp(-x))


def target_lo(base, cond):
    t = cond.startswith("treatment")
    c = cond.endswith("_comp")
    return (base + PLANTED["treatment"] * t + PLANTED["competitor_present"] * c
            + PLANTED["interaction"] * (t and c))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=str(HERE / "corpus" / "corpus_competition.json"))
    ap.add_argument("--out", default=str(HERE / "results" / "mock_competition.jsonl"))
    ap.add_argument("--runs", type=int, default=24)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    corpus = json.loads(pathlib.Path(args.corpus).read_text())
    rng = np.random.default_rng(args.seed)
    models = list(PLANTED["model_baseline"])
    w = weights(models)
    truth = {k: [] for k in ("H4r", "H9", "H9a", "H9b")}

    outp = pathlib.Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with outp.open("w") as fh:
        effects = {p["prompt_id"]: (rng.normal(0, PLANTED["prompt_sd"]),
                                    rng.normal(0, PLANTED["prompt_sd"]))
                   for p in corpus["prompts"]}
        for p in corpus["prompts"]:
            pt, pc = effects[p["prompt_id"]]
            per = {k: 0.0 for k in truth}
            for m in models:
                base = PLANTED["target_base"] + pt + PLANTED["model_baseline"][m]
                cbase = PLANTED["competitor_base"] + pc + PLANTED["model_baseline"][m]
                pr = {c: expit(target_lo(base, c)) for c in
                      ("control", "treatment", "control_comp", "treatment_comp")}
                h4r = pr["treatment"] - pr["control"]
                h9 = pr["treatment_comp"] - pr["control_comp"]
                h9b = expit(cbase + PLANTED["competitor_when_treated"]) - expit(cbase)
                for k, v in (("H4r", h4r), ("H9", h9), ("H9a", h9 - h4r), ("H9b", h9b)):
                    per[k] += w[m] * v

                for cond in corpus["conditions"]:
                    for rep in range(args.runs):
                        key = f"{m}|{p['prompt_id']}|{cond}|{rep}"
                        order = list(p["doc_ids"])
                        seed = int(hashlib.sha256(
                            f"{corpus['corpus_version']}|{key}".encode()).hexdigest()[:12], 16)
                        random.Random(seed).shuffle(order)
                        cited = []
                        for d in order:
                            if d == p["target_doc_id"]:
                                prob = pr[cond]
                            elif d == p["competitor_doc_id"] and cond.endswith("_comp"):
                                prob = expit(cbase + PLANTED["competitor_when_treated"]
                                             * cond.startswith("treatment"))
                            else:
                                prob = expit(-0.3)
                            if rng.random() < prob:
                                cited.append(d)
                        rng.shuffle(cited)
                        hit = p["target_doc_id"] in cited
                        fh.write(json.dumps({
                            "run_key": key, "harness_version": "MOCK",
                            "timestamp_utc": "2026-10-24T00:00:00+00:00",
                            "corpus_version": corpus["corpus_version"], "model": m,
                            "model_returned": m,
                            "prompt_id": p["prompt_id"], "domain": p["domain"],
                            "condition": cond, "rep": rep, "temperature": 1.0,
                            "presentation_order": order,
                            "target_doc_id": p["target_doc_id"],
                            "target_format": p["target_format"],
                            "target_slot": order.index(p["target_doc_id"]),
                            "n_docs": len(order), "response_text": "MOCK",
                            "cited_doc_ids": cited,
                            "cited_display_idx": [order.index(d) + 1 for d in cited],
                            "target_cited": hit,
                            "target_cite_rank": cited.index(p["target_doc_id"]) if hit else None,
                            "sentence_citations": [],
                        }) + "\n")
                        n += 1
            for k in truth:
                truth[k].append(per[k])

    print(f"wrote {n:,} mock runs -> {outp}")
    print("\nPLANTED GROUND TRUTH, share-weighted, probability scale")
    print("(analyze_competition.py's share-weighted intervals should contain these):")
    for k, v in truth.items():
        print(f"  {k:<4} {np.mean(v):+.4f}")


if __name__ == "__main__":
    main()
