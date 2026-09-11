#!/usr/bin/env python3
"""
OpenGEO -- corpus variant manipulation checks.

Verifies that a corpus variant changed what its design says it changed, and
nothing else, before a round spends money against real models.

This exists because of the v0.3 and v0.4 corpus-design failures, both of which
were the same failure: a control document that was *supposed* to be orthogonal
still shared topical surface with the question, so it got cited anyway. v0.3
caught it as literal keyword overlap; v0.4 caught a subtler form -- a sentence
answering the question directionally in different words ("a CPU-bound game
won't benefit much"). Both were found only by testing against real models,
after the corpus was built.

A script cannot replace that real-model spot check, and this one does not try
to. What it can do is catch the coarse failures for free, in a second, so the
spot check is spent on the subtle ones. Three checks matter:

  numerals      -- a variant that should add no facts must add no figures
  question leak -- no content word from the prompt's own question may be
                   newly introduced by a variant that is meant to stay
                   orthogonal to it
  answer leak   -- no content word unique to the *treatment* variant may be
                   newly introduced either; treatment text is, by
                   construction, the language that answers the question

Standard library only, per the stack constraint in CLAUDE.md.

Usage:
    python3 check_variants.py --corpus corpus/corpus_lengthonly.json \\
        --base control --expect-no-facts pad125 pad150 pad200
"""
import argparse
import json
import pathlib
import re
import sys
from collections import Counter

# Numerals, percentages, years, and formatted figures -- the surface form of a
# "specific fact" as this project's interventions define it.
NUMERIC = re.compile(r"\b\d+(?:\.\d+)?\s*%|\b(?:19|20)\d{2}\b|\b\d+(?:,\d{3})+\b|\b\d+(?:\.\d+)?\b")

# Function words carry no topical surface, so they are excluded from leak
# checks. Deliberately generous: a false negative here costs a real-model spot
# check, a false positive costs a rebuilt corpus.
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "of", "to", "in", "on", "for",
    "with", "as", "at", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "it", "its", "this", "that", "these", "those", "you", "your",
    "they", "their", "them", "we", "our", "us", "can", "will", "would",
    "should", "could", "may", "might", "must", "has", "have", "had", "do",
    "does", "did", "not", "no", "nor", "so", "than", "then", "there", "here",
    "what", "which", "who", "whom", "when", "where", "how", "why", "all",
    "any", "some", "most", "more", "less", "much", "many", "few", "own",
    "same", "other", "another", "each", "every", "both", "one", "two", "up",
    "down", "out", "over", "under", "about", "into", "through", "after",
    "before", "between", "while", "during", "because", "just", "only", "also",
    "very", "too", "still", "even", "well", "way", "ways", "thing", "things",
    "make", "makes", "made", "get", "gets", "got", "take", "takes", "come",
    "comes", "go", "goes", "want", "wants", "need", "needs", "use", "used",
    "using", "s", "t", "re", "ve", "ll", "d", "m",
}


def content_words(text):
    """Lowercased content tokens: what could carry topical surface."""
    toks = re.findall(r"[a-z']+", text.lower())
    return {w for w in toks if w not in STOPWORDS and len(w) > 2}


def numerals(text):
    return NUMERIC.findall(text)


def check_document(doc, question, base, variants):
    """Check one document's variants against its base variant.

    Returns a list of failure strings; empty means the document passed.
    """
    v = doc["variants"]
    if base not in v:
        return [f"missing base variant {base!r}"]

    base_words = content_words(v[base])
    base_nums = len(numerals(v[base]))
    q_terms = content_words(question)
    # Language unique to the treatment variant is, by construction, the wording
    # that answers the question. A no-facts variant must not acquire any of it.
    answer_terms = (content_words(v["treatment"]) - base_words) if "treatment" in v else set()

    failures = []
    for name in variants:
        if name not in v:
            failures.append(f"{name}: variant missing")
            continue
        text = v[name]
        added = content_words(text) - base_words
        n_added = len(numerals(text)) - base_nums

        if n_added > 0:
            failures.append(f"{name}: added {n_added} numeric token(s) -- "
                            f"{numerals(text)[base_nums:][:4]}")
        leaked_q = sorted(added & q_terms)
        if leaked_q:
            failures.append(f"{name}: introduced question term(s) {leaked_q[:6]}")
        leaked_a = sorted(added & answer_terms)
        if leaked_a:
            failures.append(f"{name}: introduced treatment-only term(s) {leaked_a[:6]}")
    return failures


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--base", default="control",
                    help="variant every other variant is compared against")
    ap.add_argument("--expect-no-facts", nargs="+", required=True,
                    help="variants that must add words but no facts")
    ap.add_argument("--targets-only", action="store_true", default=True)
    args = ap.parse_args(argv)

    corpus = json.loads(pathlib.Path(args.corpus).read_text())
    questions = {p["prompt_id"]: p["question"] for p in corpus["prompts"]}
    docs = [d for d in corpus["documents"]
            if d.get("is_target") or not args.targets_only]

    print(f"checking {len(docs)} target documents in {args.corpus}")
    print(f"  base variant: {args.base}")
    print(f"  must add no facts: {', '.join(args.expect_no_facts)}\n")

    failed = 0
    reasons = Counter()
    for doc in docs:
        problems = check_document(doc, questions.get(doc["prompt_id"], ""),
                                  args.base, args.expect_no_facts)
        if problems:
            failed += 1
            print(f"FAIL {doc['doc_id']}")
            for p in problems:
                print(f"       {p}")
                reasons[p.split(":")[1].strip().split(" ")[0]] += 1

    # Length report: the independent variable, so it is described, not gated.
    print(f"\nlength ratios vs {args.base} (target documents):")
    for name in args.expect_no_facts:
        ratios = []
        for d in docs:
            v = d["variants"]
            if name in v and args.base in v:
                b = len(v[args.base].split())
                if b:
                    ratios.append(len(v[name].split()) / b)
        if ratios:
            ratios.sort()
            print(f"  {name:10s} min={ratios[0]:.2f} median={ratios[len(ratios)//2]:.2f} "
                  f"max={ratios[-1]:.2f}  n={len(ratios)}")

    if failed:
        print(f"\n{failed}/{len(docs)} documents FAILED. "
              f"Most common: {dict(reasons.most_common(3))}")
        print("Fix the builder and regenerate; do not hand-edit the JSON.")
        return 1

    print(f"\nall {len(docs)} target documents passed.")
    print("This clears only the coarse failures. A real-model spot check before "
          "the full round is still required -- see CLAUDE.md, process lesson.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
