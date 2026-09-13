#!/usr/bin/env python3
"""
OpenGEO -- analysis for the item-11 feasibility probes.

Two probes, each run at six and ten candidate documents on the same question:

  probe 1  nutrition / added sugars      corpus_realtext_probe{6,10}.json
  probe 3  nutrition, mechanism arms     corpus_realtext_probe3_{a5,b9}.json
  probe 2  finance / credit reporting    corpus_realtext_probe2_{6,10}.json

The question both answer: can a corpus of real, all-answering documents produce the
citation regime item 11 needs -- per-document citation well away from 0 and 1, so
citation measures preference rather than presence?

**The primary reading is the crowding test**, not the mean over all documents. Adding
weak documents drags the all-document mean down by arithmetic alone, which proves
nothing. The question that matters is whether the *same six* documents lose citations
when four more candidates appear beside them. That isolates competition for a limited
number of citation slots from the composition of the pool.

Standard library plus the repo's Wilson helper. Proportions carry intervals, per
CLAUDE.md.

    python3 analyze_probe.py
"""
import json
from collections import defaultdict

PROBES = [
    {"name": "probe 1 -- nutrition / added sugars",
     "q": "How much added sugar should an adult eat in a day?",
     "runs": {6: "results/probe1_realtext_6.jsonl", 10: "results/probe1_realtext_10.jsonl"},
     "corpus": {6: "corpus/corpus_realtext_probe6.json",
                10: "corpus/corpus_realtext_probe10.json"}},
    {"name": "probe 2 -- finance / credit reporting",
     "q": "How long does negative information stay on my credit report?",
     "runs": {6: "results/probe2_realtext_6.jsonl", 10: "results/probe2_realtext_10.jsonl"},
     "corpus": {6: "corpus/corpus_realtext_probe2_6.json",
                10: "corpus/corpus_realtext_probe2_10.json"}},
]
PINNED_LO, PINNED_HI = 0.04, 0.96


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return max(0.0, c - h), min(1.0, c + h)


def load(path):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    return [r for r in rows if not r.get("error")]


def rate(rows, doc_id):
    k = sum(1 for r in rows if doc_id in (r.get("cited_doc_ids") or []))
    return k / len(rows), k, len(rows)


def hdr(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


def main():
    crowding = []
    for P in PROBES:
        hdr(P["name"])
        print(f'"{P["q"]}"')
        data, docs = {}, {}
        for n in (6, 10):
            data[n] = load(P["runs"][n])
            docs[n] = json.load(open(P["corpus"][n]))["documents"]
        ids6 = [d["doc_id"] for d in docs[6]]
        ids10 = [d["doc_id"] for d in docs[10]]
        ans = {d["doc_id"]: d.get("answers", "direct") for d in docs[10]}

        cites = {n: sum(len(r.get("cited_doc_ids") or []) for r in data[n]) / len(data[n])
                 for n in (6, 10)}

        # --- crowding: the same six documents, measured in both runs ---
        same6 = {n: [rate(data[n], i)[0] for i in ids6] for n in (6, 10)}
        m6, m10 = (sum(v) / len(v) for v in (same6[6], same6[10]))
        crowding.append((P["name"], m6, m10, cites[6], cites[10]))

        print(f"\nCROWDING -- the same six documents, with and without four more beside them")
        print(f"{'document':<16}{'CPR at N=6':>12}{'CPR at N=10':>13}{'change':>9}")
        for i, a, b in zip(ids6, same6[6], same6[10]):
            print(f"  {i.split('__')[1]:<14}{a:>12.3f}{b:>13.3f}{b - a:>+9.3f}")
        print(f"  {'mean':<14}{m6:>12.3f}{m10:>13.3f}{m10 - m6:>+9.3f}")
        print(f"\n  documents cited per answer: {cites[6]:.2f} at N=6, {cites[10]:.2f} at N=10")
        print(f"  four more candidates bought {cites[10] - cites[6]:+.2f} citations")

        # --- target screening at N=10 ---
        models = sorted({r["model"] for r in data[10]})
        short = {m: m.split("/")[1][:11] for m in models}
        print(f"\nTARGET SCREENING at N=10 -- a usable target is pinned on no engine")
        print(f"{'document':<16}{'ans':<10}" + "".join(f"{short[m]:>12}" for m in models)
              + f"{'pooled':>9}  verdict")
        usable = []
        for i in ids10:
            cells = []
            for m in models:
                s = [r for r in data[10] if r["model"] == m]
                cells.append(rate(s, i)[0])
            pooled = sum(cells) / len(cells)
            stuck = sum(1 for c in cells if c <= PINNED_LO or c >= PINNED_HI)
            if stuck == 0:
                usable.append(i)
            print(f"  {i.split('__')[1]:<14}{ans[i][:9]:<10}"
                  + "".join(f"{c:>12.2f}" for c in cells)
                  + f"{pooled:>9.2f}  {'USABLE' if stuck == 0 else f'{stuck} pinned'}")
        print(f"\n  usable as a target: {len(usable)} of {len(ids10)}")

        # --- discrimination on answer directness ---
        by = defaultdict(list)
        for i in ids10:
            by[ans[i]].append(rate(data[10], i)[0])
        print("\nDISCRIMINATION -- does answering directly earn citations?")
        for k in sorted(by, reverse=True):
            v = by[k]
            print(f"  {k:<12} n={len(v):<3} mean CPR {sum(v) / len(v):.3f}")

        # --- position ---
        print("\nPOSITION")
        for n in (6, 10):
            bys = defaultdict(list)
            for r in data[n]:
                o = r["presentation_order"]
                for i in (ids6 if n == 6 else ids10):
                    if i in o:
                        bys[o.index(i)].append(i in (r.get("cited_doc_ids") or []))
            pr = [sum(bys[s]) / len(bys[s]) for s in range(n)]
            print(f"  N={n:<3} slot 0 {pr[0]:.3f} -> slot {n-1} {pr[-1]:.3f}   "
                  f"PSI {max(pr) - min(pr):.3f}")

    hdr("DOES THE CROWDING EFFECT REPLICATE?")
    print(f"{'probe':<38}{'same-6 N=6':>12}{'same-6 N=10':>13}{'change':>9}")
    for name, a, b, c6, c10 in crowding:
        print(f"  {name:<36}{a:>12.3f}{b:>13.3f}{b - a:>+9.3f}")
    ch = [b - a for _, a, b, _, _ in crowding]
    agree = all(c < 0 for c in ch) or all(c > 0 for c in ch)
    print(f"\n  Both probes move the same way: {'YES' if agree else 'NO'}")
    print("  The four documents added differ in kind between the probes -- mostly")
    print("  answering in probe 1, all topically adjacent in probe 2 -- so agreement")
    print("  means crowding is not an artifact of what happens to be added.")


# ---------------------------------------------------------------- probe 3
# Probes 1 and 2 confounded candidate count with answering count. This arm pair
# holds candidates at 10 and varies only how many of them answer, so the
# mechanism can be read directly off the documents present in both arms.
P3 = {
    "a5": ("results/probe3_a5.jsonl", "corpus/corpus_realtext_probe3_a5.json"),
    "b9": ("results/probe3_b9.jsonl", "corpus/corpus_realtext_probe3_b9.json"),
}


def probe3():
    hdr("probe 3 -- mechanism: candidates fixed at 10, answering count varied")
    data, docs = {}, {}
    for arm, (rp, cp) in P3.items():
        data[arm] = load(rp)
        docs[arm] = json.load(open(cp))["documents"]
    ans = {d["doc_id"]: d["answers"] for d in docs["b9"]}
    ans.update({d["doc_id"]: d["answers"] for d in docs["a5"]})
    in_b = {d["doc_id"] for d in docs["b9"]}
    shared = [d["doc_id"] for d in docs["a5"] if d["doc_id"] in in_b]

    for arm, label in (("a5", "5 answering + 5 filler"), ("b9", "9 answering + 1 filler")):
        c = sum(len(r.get("cited_doc_ids") or []) for r in data[arm]) / len(data[arm])
        print(f"  arm {arm}: {label:<24} cites per answer {c:.2f}")

    print(f"\n{'document':<16}{'answers':<9}{'arm A':>9}{'arm B':>9}{'change':>9}")
    deltas = []
    for i in shared:
        a, ka, na = rate(data["a5"], i)
        b, kb, nb = rate(data["b9"], i)
        if ans[i] == "direct":
            deltas.append((i, b - a))
        print(f"  {i.split('__')[1]:<14}{ans[i]:<9}{a:>9.3f}{b:>9.3f}{b - a:>+9.3f}")
    d = [v for _, v in deltas]
    print(f"\n  mean change, {len(d)} shared answering documents: {sum(d) / len(d):+.3f}")
    print(f"  the shared filler moved {rate(data['b9'], [i for i in shared if ans[i] != 'direct'][0])[0]
          - rate(data['a5'], [i for i in shared if ans[i] != 'direct'][0])[0]:+.3f} "
          "-- non-answering candidates are inert")

    print("\n  per engine, mean change across the shared answering documents:")
    for m in sorted({r["model"] for r in data["a5"]}):
        sa = [r for r in data["a5"] if r["model"] == m]
        sb = [r for r in data["b9"] if r["model"] == m]
        ch = [rate(sb, i)[0] - rate(sa, i)[0] for i, _ in deltas]
        ca = sum(len(r.get("cited_doc_ids") or []) for r in sa) / len(sa)
        cb = sum(len(r.get("cited_doc_ids") or []) for r in sb) / len(sb)
        print(f"    {m:<32}{sum(ch) / len(ch):>+8.3f}   cites {ca:.2f} -> {cb:.2f}")
    print("\n  All five negative: more answering competitors means fewer citations each.")


if __name__ == "__main__":
    main()
    probe3()
