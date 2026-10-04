#!/usr/bin/env python3
"""
Generate synthetic runs with KNOWN planted effects, to verify that analyze.py
recovers them before spending money on real API calls.

    python3 make_mock.py --runs 10 && python3 analyze.py --runs results/mock.jsonl

Planted ground truth (see PLANTED below): a U-shaped position effect, a modest
treatment effect, per-model baselines, and a format effect. If analyze.py cannot
recover these from clean synthetic data, it will not recover anything from noisy
real data either.
"""
import argparse, hashlib, json, pathlib, random
import numpy as np

HERE = pathlib.Path(__file__).parent

PLANTED = {
    # log-odds bump by slot: ends favoured, middle penalised ("lost in the middle")
    "slot_logodds": [0.75, 0.10, -0.35, -0.40, 0.05, 0.60],
    "treatment_logodds": 0.34,          # ~OR 1.40
    "model_baseline_logodds": {         # per-model intercept
        "anthropic/claude-haiku-4.5": 0.30, "openai/gpt-5.4-mini": 0.10,
        "google/gemini-3-flash-preview": -0.15, "x-ai/grok-4.3": -0.30,
        "moonshotai/kimi-k2": 0.05, "deepseek/deepseek-chat": -0.20,
        "meta-llama/llama-4-maverick": -0.45, "mistralai/mistral-medium-3": 0.00,
    },
    "format_logodds": {"blog": 0.20, "news": -0.25, "docs": 0.15,
                       "product": -0.35, "forum": 0.05, "reference": 0.30},
    "base_logodds": -0.5,
}


def expit(x):
    return 1 / (1 + np.exp(-x))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=str(HERE / "corpus" / "corpus_v0.2.json"))
    ap.add_argument("--out", default=str(HERE / "results" / "mock.jsonl"))
    ap.add_argument("--runs", type=int, default=10)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    corpus = json.loads(pathlib.Path(args.corpus).read_text())
    rng = np.random.default_rng(args.seed)
    models = list(PLANTED["model_baseline_logodds"])

    outp = pathlib.Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with outp.open("w") as fh:
        for m in models:
            for p in corpus["prompts"]:
                # per-prompt random intercept
                p_eff = rng.normal(0, 0.55)
                for cond in ("control", "treatment"):
                    for rep in range(args.runs):
                        key = f"{m}|{p['prompt_id']}|{cond}|{rep}"
                        order = list(p["doc_ids"])
                        seed = int(hashlib.sha256(
                            f"{corpus['corpus_version']}|{key}".encode()).hexdigest()[:12], 16)
                        random.Random(seed).shuffle(order)
                        slot = order.index(p["target_doc_id"])

                        lo = (PLANTED["base_logodds"] + p_eff
                              + PLANTED["slot_logodds"][slot]
                              + PLANTED["model_baseline_logodds"][m]
                              + PLANTED["format_logodds"][p["target_format"]]
                              + (PLANTED["treatment_logodds"] if cond == "treatment" else 0.0))
                        cited = bool(rng.random() < expit(lo))

                        # other docs cited with a slot-shaped probability too
                        cited_ids = []
                        for i, d in enumerate(order):
                            if d == p["target_doc_id"]:
                                if cited:
                                    cited_ids.append(d)
                            elif rng.random() < expit(-0.6 + PLANTED["slot_logodds"][i]
                                                      + rng.normal(0, .3)):
                                cited_ids.append(d)

                        fh.write(json.dumps({
                            "run_key": key, "harness_version": "MOCK",
                            "timestamp_utc": "2026-08-11T00:00:00+00:00",
                            "corpus_version": corpus["corpus_version"], "model": m,
                            "prompt_id": p["prompt_id"], "domain": p["domain"],
                            "condition": cond, "rep": rep, "temperature": 1.0,
                            "presentation_order": order,
                            "target_doc_id": p["target_doc_id"],
                            "target_format": p["target_format"],
                            "target_slot": slot, "n_docs": len(order),
                            "response_text": "MOCK", "cited_doc_ids": cited_ids,
                            "cited_display_idx": [order.index(d) + 1 for d in cited_ids],
                            "target_cited": cited,
                            "target_cite_rank": (cited_ids.index(p["target_doc_id"])
                                                 if cited else None),
                            "sentence_citations": [],
                        }) + "\n")
                        n += 1

    print(f"wrote {n:,} mock runs -> {outp}")
    print("\nPLANTED GROUND TRUTH (analyze.py should recover these):")
    s = PLANTED["slot_logodds"]
    print(f"  slot log-odds      : {s}")
    print(f"  implied PSI approx : {expit(-0.5+max(s)) - expit(-0.5+min(s)):.3f}")
    print(f"  treatment log-odds : {PLANTED['treatment_logodds']:.2f} "
          f"(OR {np.exp(PLANTED['treatment_logodds']):.2f})")
    print(f"  format ordering    : "
          f"{sorted(PLANTED['format_logodds'], key=PLANTED['format_logodds'].get, reverse=True)}")
    print("  models share the same slot/format structure => Kendall's W should be HIGH here.")
    print("  (Real data showing LOW W would therefore be a real finding, not an artefact.)")


if __name__ == "__main__":
    main()
