#!/usr/bin/env python3
"""
OpenGEO -- target screening for rankable (item-11) corpora.

A round varies one target document per question by tactic and measures how its
citation rate moves. That only works if the target's baseline rate can move in both
directions on every engine. The feasibility probes found it usually cannot: the
cleanest answer on a question is cited in every run on every engine, and documents
near the bottom are never cited by the selective engines. A target pinned at either
end on any engine makes that engine's contribution to the round a guaranteed null.

So targets are screened, not chosen. This reads a baseline run of a candidate corpus
and, per question:

  - reports each document's citation rate on each engine
  - marks a document PINNED if any engine cites it in <= 4% or >= 96% of runs
  - scores every unpinned document by its worst-case headroom: the smallest distance
    to 0 or 1 across all engines, min over engines of min(rate, 1 - rate)
  - requires worst-case headroom of at least 3/24 -- three citations and three
    non-citations from each boundary on every engine
  - recommends the highest-scoring document as the target, or DISCARD if none
    qualifies

Worst-case headroom is the rule because a target is only as movable as its most
constrained engine. A document at 0.5 on four engines and 0.97 on the fifth is not a
usable target; averaging would call it a good one.

The screen is a gate on the design, not a look at any result: it runs on the baseline
text only, before any tactic variant exists.

    python3 screen.py --corpus corpus/corpus_rankable_screen_b1.json --runs results/screen_rankable_b1.jsonl
    python3 screen.py ... --json      # machine-readable, consumed by the corpus builder
"""
import argparse
import json
from collections import defaultdict

PINNED_LO, PINNED_HI = 0.04, 0.96
# A document can clear the pinning cutoffs and still be unusable: at 24 runs, 1/24 = 0.042
# and 23/24 = 0.958 both pass them, yet a tactic cannot move a rate measurably below one
# citation or above twenty-three. A target must be at least 3 citations and 3
# non-citations from each boundary on EVERY engine -- worst-case headroom >= 3/24 --
# so no engine's count sits within a run or two of a floor or ceiling.
#
# Added 2026-09-13 after the first rankable screen recommended a target cited in 1 of
# 24 runs on grok. The rule is stated from counts, not tuned to that question; it
# is applied retroactively to the feasibility probes, where it also lowers the
# usable-target counts (results/probes/2026-09-12-realtext-feasibility.md).
MIN_HEADROOM = 3 / 24


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return max(0.0, c - h), min(1.0, c + h)


def load_runs(path):
    """Last row per run_key, successful rows only -- matching every other analyzer."""
    last = {}
    for line in open(path):
        if line.strip():
            r = json.loads(line)
            last[r["run_key"]] = r
    return [r for r in last.values() if not r.get("error")]


def screen_question(prompt, docs, rows):
    models = sorted({r["model"] for r in rows})
    by_model = defaultdict(list)
    for r in rows:
        by_model[r["model"]].append(r)

    out_docs = []
    for d in docs:
        i = d["doc_id"]
        per = {}
        for m in models:
            s = by_model[m]
            per[m] = sum(1 for r in s if i in (r.get("cited_doc_ids") or [])) / len(s)
        k = sum(1 for r in rows if i in (r.get("cited_doc_ids") or []))
        pinned = [m for m, v in per.items() if v <= PINNED_LO or v >= PINNED_HI]
        headroom = min(min(v, 1 - v) for v in per.values())
        out_docs.append({
            "doc_id": i, "answers": d.get("answers"), "per_engine": per,
            "pooled": k / len(rows), "pooled_ci": wilson(k, len(rows)),
            "pinned_on": pinned, "headroom": headroom,
        })

    usable = [d for d in out_docs if not d["pinned_on"] and d["headroom"] >= MIN_HEADROOM]
    target = max(usable, key=lambda d: d["headroom"]) if usable else None
    cites = sum(len(r.get("cited_doc_ids") or []) for r in rows) / len(rows)
    return {
        "prompt_id": prompt["prompt_id"], "question": prompt["question"],
        "n_docs": len(docs), "runs": len(rows), "models": models,
        "cites_per_answer": cites,
        "n_answering": sum(1 for d in docs if d.get("answers") == "direct"),
        "documents": out_docs,
        "usable": [d["doc_id"] for d in usable],
        "target": target["doc_id"] if target else None,
        "verdict": "KEEP" if target else "DISCARD",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--runs", required=True)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    corpus = json.load(open(args.corpus))
    docs_by_id = {d["doc_id"]: d for d in corpus["documents"]}
    rows = load_runs(args.runs)
    by_prompt = defaultdict(list)
    for r in rows:
        by_prompt[r["prompt_id"]].append(r)

    results = []
    for p in corpus["prompts"]:
        if not by_prompt[p["prompt_id"]]:
            results.append({"prompt_id": p["prompt_id"], "verdict": "NOT RUN"})
            continue
        results.append(screen_question(p, [docs_by_id[i] for i in p["doc_ids"]],
                                       by_prompt[p["prompt_id"]]))

    if args.json:
        print(json.dumps(results, indent=2))
        return

    for q in results:
        print("\n" + "=" * 96)
        if q["verdict"] == "NOT RUN":
            print(f"{q['prompt_id']}: NOT RUN")
            continue
        print(f"{q['prompt_id']}  --  {q['verdict']}")
        print(f'"{q["question"]}"')
        print(f"{q['n_docs']} candidates, {q['n_answering']} answering, {q['runs']} runs, "
              f"{q['cites_per_answer']:.2f} cited per answer")
        print("=" * 96)
        short = [m.split("/")[1][:10] for m in q["models"]]
        print(f"{'document':<26}" + "".join(f"{s:>11}" for s in short)
              + f"{'pooled':>8}{'headroom':>10}  status")
        for d in sorted(q["documents"], key=lambda d: -d["headroom"]):
            tag = ("TARGET" if d["doc_id"] == q["target"]
                   else "usable" if d["doc_id"] in q["usable"]
                   else f"pinned on {len(d['pinned_on'])}" if d["pinned_on"]
                   else f"too close to a boundary (headroom < {MIN_HEADROOM:.3f})")
            print(f"  {d['doc_id'].split('__')[-1]:<24}"
                  + "".join(f"{d['per_engine'][m]:>11.2f}" for m in q["models"])
                  + f"{d['pooled']:>8.2f}{d['headroom']:>10.2f}  {tag}")

    kept = [q for q in results if q["verdict"] == "KEEP"]
    run = [q for q in results if q["verdict"] != "NOT RUN"]
    print("\n" + "=" * 96)
    print(f"SCREEN: {len(kept)} of {len(run)} questions have a usable target")
    for q in run:
        t = q["target"].split("__")[-1] if q["target"] else "-"
        h = max((d["headroom"] for d in q["documents"] if d["doc_id"] == q["target"]),
                default=0.0)
        print(f"  {q['verdict']:<8}{q['prompt_id']:<34}target {t:<24}"
              f"worst-engine headroom {h:.2f}   usable {len(q['usable'])}/{q['n_docs']}")


if __name__ == "__main__":
    main()
