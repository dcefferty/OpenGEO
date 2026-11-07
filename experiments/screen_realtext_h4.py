#!/usr/bin/env python3
"""
OpenGEO -- control-arm screen for the real-text H4 round.

Applies the gate in `preregistrations/2026-11-realtext-h4.md`, "Screening": a
question is KEPT if its target's control-arm CPR, pooled unweighted across the
five engines, lies in [0.25, 0.75]; otherwise it is DISCARDED. Discarded
questions are not re-tuned and not re-screened (METHODOLOGY.md section 9).

The screen is a gate on the design, never a look at the result: it refuses to
read a runs file containing any treatment row, so the contrast the round tests
cannot be seen before the round.

Also printed, for information only and not part of the gate:
  - the target's rate on each engine, with the engines pinned at a boundary
    (<= 1/24 or >= 23/24) marked, since a pinned engine will report a bound
  - cites per answer, against v0.4's reference of 2.66 (section 9: a field cited
    far more generously than that is collectively too on-topic)

    python3 screen_realtext_h4.py --corpus corpus/corpus_realtext_h4_b1.json \\
        --runs results/screen_realtext_h4_b1.jsonl
"""
import argparse
import json
import pathlib
import sys
from collections import defaultdict

from analyze_competition import load

GATE = (0.25, 0.75)
CITES_PER_ANSWER_REF = 2.66      # corpus v0.4 control arm, METHODOLOGY.md section 9


def screen(corpus, rows):
    """{prompt_id: dict} for every prompt in the corpus."""
    by = defaultdict(lambda: defaultdict(list))
    cites = defaultdict(list)
    for r in rows:
        by[r["prompt_id"]][r["model"]].append(1.0 if r["target_cited"] else 0.0)
        cites[r["prompt_id"]].append(len(r["cited_doc_ids"]))
    out = {}
    for p in corpus["prompts"]:
        pid = p["prompt_id"]
        per = {m: sum(v) / len(v) for m, v in by[pid].items() if v}
        pooled = sum(per.values()) / len(per) if per else float("nan")
        runs = {m: len(v) for m, v in by[pid].items()}
        out[pid] = {
            "pooled": pooled, "per_engine": per, "runs": runs,
            "pinned": sorted(m for m, x in per.items()
                             if x * runs[m] <= 1 or x * runs[m] >= runs[m] - 1),
            "cites_per_answer": (sum(cites[pid]) / len(cites[pid])) if cites[pid] else float("nan"),
            "keep": bool(per) and GATE[0] <= pooled <= GATE[1],
        }
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--runs", required=True)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    corpus = json.loads(pathlib.Path(args.corpus).read_text())
    rows, errs = load(args.runs)
    conds = {r["condition"] for r in rows}
    if conds - {"control"}:
        sys.exit(f"REFUSED: runs contain {sorted(conds - {'control'})} rows. The screen reads "
                 "the control arm only; the treatment arm may not be seen before the round.")
    versions = {r["corpus_version"] for r in rows}
    if versions != {corpus["corpus_version"]}:
        sys.exit(f"runs are from {sorted(versions)}, not {corpus['corpus_version']}")

    res = screen(corpus, rows)
    if args.json:
        print(json.dumps(res, indent=2))
        return 0

    models = sorted({r["model"] for r in rows})
    short = {m.split("/")[-1][:10]: m for m in models}
    print(f"control-arm screen, {corpus['corpus_version']} ({corpus['corpus_sha256']}): "
          f"{len(rows):,} runs, {errs} errored")
    print(f"gate: pooled unweighted target CPR in [{GATE[0]:.2f}, {GATE[1]:.2f}]\n")
    head = "".join(f"{s:>11}" for s in short)
    print(f"{'question':<30}{'pooled':>8}{head}{'cites/ans':>11}   decision")
    print("-" * (52 + 11 * len(short) + 10))
    for pid, r in res.items():
        cells = "".join(
            f"{r['per_engine'].get(m, float('nan')):>10.2f}{'*' if m in r['pinned'] else ' '}"
            for m in short.values())
        print(f"{pid:<30}{r['pooled']:>8.3f}{cells}{r['cites_per_answer']:>11.2f}   "
              f"{'KEEP' if r['keep'] else 'DISCARD'}")
    kept = [p for p, r in res.items() if r["keep"]]
    print(f"\n* = pinned on that engine (<= 1 or >= n-1 citations): its round result there "
          "will be a bound, not an estimate.")
    print(f"cites/answer reference: {CITES_PER_ANSWER_REF} (corpus v0.4 control arm)")
    print(f"\nKEPT {len(kept)} of {len(res)}: {', '.join(kept) if kept else 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
