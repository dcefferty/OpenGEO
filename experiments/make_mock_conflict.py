#!/usr/bin/env python3
"""
Synthetic runs for the conflicting-figures round, with KNOWN planted effects,
to verify that analyze_conflict.py recovers them before any money is spent.

    python3 make_mock_conflict.py
    python3 analyze_conflict.py --runs results/mock_conflict.jsonl

Planted on the log-odds scale (PLANTED below): a target that states the answer
gains over the vague one, a contradicting target gains less, the competitor
gains when contradicted, and contradicting answers adopt the competitor's
figure more often on `world` prompts than on `document` ones. Each answer's
text carries one side's figure, so the adoption reader is exercised too.
Ground truth is printed on the probability scale, computed from the same draws.
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
    "target_base": -1.30,
    "states_answer": 2.60,
    "contradicted": -0.90,
    "contradicted_world_extra": -0.40,
    "competitor_base": 2.50,
    "competitor_when_contradicted": 0.80,
    "adopt_correct": {"world": 0.80, "document": 0.55},
    "adopt_decided": 0.85,
    "model_baseline": {
        "openai/gpt-5.4-mini": -0.40, "google/gemini-3-flash-preview": 0.60,
        "anthropic/claude-haiku-4.5": -0.30, "deepseek/deepseek-chat": 0.20,
        "x-ai/grok-4.3": 0.10,
    },
    "prompt_sd": 0.55,
}


def expit(x):
    return 1 / (1 + np.exp(-x))


def target_lo(base, cond, world):
    if cond == "control_comp":
        return base
    lo = base + PLANTED["states_answer"]
    if cond == "conflict":
        lo += PLANTED["contradicted"] + PLANTED["contradicted_world_extra"] * world
    return lo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=str(HERE / "corpus" / "corpus_conflict.json"))
    ap.add_argument("--out", default=str(HERE / "results" / "mock_conflict.jsonl"))
    ap.add_argument("--runs", type=int, default=24)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    from analyze_conflict import sides
    corpus = json.loads(pathlib.Path(args.corpus).read_text())
    S = sides(corpus)
    rng = np.random.default_rng(args.seed)
    models = list(PLANTED["model_baseline"])
    w = weights(models)
    truth = {k: {"world": [], "document": []} for k in ("H13", "H13a", "H13b", "H13c")}

    outp = pathlib.Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with outp.open("w") as fh:
        for p in corpus["prompts"]:
            pt, pc = rng.normal(0, PLANTED["prompt_sd"], size=2)
            cls = p["truth_class"]
            world = cls == "world"
            q = PLANTED["adopt_correct"][cls]
            correct, wrong = (sorted(s) for s in S[p["prompt_id"]])
            per = {k: 0.0 for k in truth}
            for m in models:
                base = PLANTED["target_base"] + pt + PLANTED["model_baseline"][m]
                cbase = PLANTED["competitor_base"] + pc + PLANTED["model_baseline"][m]
                pr = {c: expit(target_lo(base, c, world)) for c in corpus["conditions"]}
                pcomp = {c: expit(cbase + PLANTED["competitor_when_contradicted"] * (c == "conflict"))
                         for c in corpus["conditions"]}
                for k, v in (("H13", pr["agree"] - pr["conflict"]),
                             ("H13a", pr["conflict"] - pr["control_comp"]),
                             ("H13b", pcomp["conflict"] - pcomp["agree"]),
                             ("H13c", q - 0.5)):
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
                            elif d == p["competitor_doc_id"]:
                                prob = pcomp[cond]
                            else:
                                prob = expit(-1.5)
                            if rng.random() < prob:
                                cited.append(d)
                        rng.shuffle(cited)
                        text = "MOCK"
                        if cond == "conflict":
                            if rng.random() < PLANTED["adopt_decided"]:
                                text = f"MOCK {correct[0] if rng.random() < q else wrong[0]}"
                        elif cond == "agree" or rng.random() < 0.5:
                            text = f"MOCK {correct[0]}"
                        hit = p["target_doc_id"] in cited
                        fh.write(json.dumps({
                            "run_key": key, "harness_version": "MOCK",
                            "timestamp_utc": "2026-11-01T00:00:00+00:00",
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
                truth[k][cls].append(per[k])

    print(f"wrote {n:,} mock runs -> {outp}")
    print("\nPLANTED GROUND TRUTH, share-weighted, probability scale")
    print("(analyze_conflict.py's share-weighted intervals should contain these):")
    for k, v in truth.items():
        print(f"  {k:<5} {np.mean(v['world'] + v['document']):+.4f}")
    print(f"  H13d  {np.mean(truth['H13']['world']) - np.mean(truth['H13']['document']):+.4f}")


if __name__ == "__main__":
    main()
