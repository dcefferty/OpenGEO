#!/usr/bin/env python3
"""
Synthetic runs for the trust-signals round, with KNOWN planted effects, to
verify that analyze_trust.py recovers them before any money is spent.

    python3 make_mock_trust.py
    python3 analyze_trust.py --runs results/mock_trust.jsonl
    python3 make_mock_trust.py --null --runs 12 --seed 7   # planted null

Planted on the log-odds scale (PLANTED below), with an engine-specific
multiplier so per-engine effects differ in size. Answers in each signal arm
repeat the signal at a planted rate, so the echo reader is exercised too.
Ground truth is printed on the probability scale, share-weighted, computed from
the same draws the runs come from.
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
    "target_base": 0.10,
    "arm": {"control": 0.0, "fresh": 0.20, "stale": -0.35, "byline": 0.25, "promo": -0.30},
    "engine_scale": {
        "openai/gpt-5.4-mini": 1.4, "google/gemini-3-flash-preview": 0.6,
        "anthropic/claude-haiku-4.5": 1.2, "deepseek/deepseek-chat": 0.8,
        "x-ai/grok-4.3": 0.7,
    },
    "model_baseline": {
        "openai/gpt-5.4-mini": -0.40, "google/gemini-3-flash-preview": 0.60,
        "anthropic/claude-haiku-4.5": -0.50, "deepseek/deepseek-chat": 0.20,
        "x-ai/grok-4.3": 0.40,
    },
    "prompt_sd": 1.20,
    "echo": {"fresh": 0.15, "stale": 0.25, "byline": 0.10, "promo": 0.03},
}
CONTRASTS = {
    "H10": ("fresh", "stale"), "H11": ("byline", "control"), "H12": ("promo", "control"),
    "H10a": ("stale", "control"), "H10b": ("fresh", "control"), "H11a": ("byline", "promo"),
}


def expit(x):
    return 1 / (1 + np.exp(-x))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=str(HERE / "corpus" / "corpus_trust.json"))
    ap.add_argument("--out", default=str(HERE / "results" / "mock_trust.jsonl"))
    ap.add_argument("--runs", type=int, default=24)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--null", action="store_true", help="plant no arm effects at all")
    args = ap.parse_args()

    corpus = json.loads(pathlib.Path(args.corpus).read_text())
    rng = np.random.default_rng(args.seed)
    models = list(PLANTED["model_baseline"])
    w = weights(models)
    arm = {c: (0.0 if args.null else v) for c, v in PLANTED["arm"].items()}
    truth = {k: [] for k in CONTRASTS}
    echo_tok = {"fresh": "October 2026", "stale": "2019", "promo": "best-in-class"}

    outp = pathlib.Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with outp.open("w") as fh:
        for p in corpus["prompts"]:
            pt = rng.normal(0, PLANTED["prompt_sd"])
            per = {k: 0.0 for k in CONTRASTS}
            for m in models:
                base = PLANTED["target_base"] + pt + PLANTED["model_baseline"][m]
                pr = {c: expit(base + PLANTED["engine_scale"][m] * arm[c]) for c in corpus["conditions"]}
                for k, (a, b) in CONTRASTS.items():
                    per[k] += w[m] * (pr[a] - pr[b])
                for cond in corpus["conditions"]:
                    for rep in range(args.runs):
                        key = f"{m}|{p['prompt_id']}|{cond}|{rep}"
                        order = list(p["doc_ids"])
                        seed = int(hashlib.sha256(
                            f"{corpus['corpus_version']}|{key}".encode()).hexdigest()[:12], 16)
                        random.Random(seed).shuffle(order)
                        cited = [d for d in order
                                 if rng.random() < (pr[cond] if d == p["target_doc_id"] else expit(0.3))]
                        rng.shuffle(cited)
                        text = "MOCK answer, cited 2025 figures."
                        if cond != "control" and rng.random() < PLANTED["echo"][cond]:
                            tok = p["author_surname"] if cond == "byline" else echo_tok[cond]
                            text += f" Source note: {tok}."
                        hit = p["target_doc_id"] in cited
                        fh.write(json.dumps({
                            "run_key": key, "harness_version": "MOCK",
                            "timestamp_utc": "2026-11-06T00:00:00+00:00",
                            "corpus_version": corpus["corpus_version"], "model": m,
                            "model_returned": m,
                            "prompt_id": p["prompt_id"], "domain": p["domain"],
                            "condition": cond, "rep": rep, "temperature": 1.0,
                            "presentation_order": order,
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
            for k in truth:
                truth[k].append(per[k])

    print(f"wrote {n:,} mock runs -> {outp}")
    print("\nPLANTED GROUND TRUTH, share-weighted, probability scale")
    print("(analyze_trust.py's share-weighted intervals should contain these):")
    for k, v in truth.items():
        print(f"  {k:<5} {np.mean(v):+.4f}")
    print("planted echo rates: " + ", ".join(f"{k} {v:.2f}" for k, v in PLANTED["echo"].items()))


if __name__ == "__main__":
    main()
