#!/usr/bin/env python3
"""
OpenGEO corpus -- length-only intervention (lengthonly-v1).

Every corpus version in this project is length-matched within +/-3 words,
because length is assumed to be a confound. That assumption has never been
measured here. This corpus measures it.

The design is the sibling of kwstuff-v3. That round isolated *repetition*,
holding length and facts constant. This one isolates *length*, holding facts
constant:

    control    -- corpus v0.4's `control` text, reused VERBATIM, loaded
                  programmatically from corpus_v0.4.json at build time. The one
                  baseline this project has directly measured against real
                  models and confirmed is not at a ceiling (pooled CPR 0.503,
                  per-model range 0.383-0.591).
    pad125     -- the same text, padded to ~1.25x its length
    pad150     -- ~1.50x
    pad200     -- ~2.00x

Padding is discourse filler: sentences that state no fact, name no entity,
contain no numeral, and carry no topical surface ("This is a question that
comes up often."). Drawn from a fixed bank, selected deterministically per
document so the corpus is reproducible, and appended without disturbing the
original sentences.

**Why a dose-response ladder rather than a binary contrast.** A single padded
condition answers "does padding move citation"; a ladder answers "how much, and
does it scale" -- and a monotone trend across three doses is far harder to
explain as an artifact than one significant contrast. It also costs nothing
extra in design complexity: run_pilot.py already takes arbitrary --conditions.

**Why this matters beyond housekeeping.** The Princeton GEO paper's headline
numbers, quoted industry-wide, come from interventions that add material --
statistics, quotations, citations -- to a document without holding length
fixed. If padding alone moves citation, some unknown share of every one of
those figures is word count. If padding alone does nothing, CPR is robust to
length in a way position-adjusted word count provably is not, which is a
concrete argument for the metric choice METRICS.md already makes on principle.

Either result is worth having, and the null is the more useful one.

The baseline variant keeps the JSON key `control`, matching every other corpus
version in this project -- run_pilot.py's cost estimator reads
`variants["control"]` directly, and kwstuff-v3 follows the same convention while
calling the variant `orthogonal` in prose. The pre-registration refers to it as
`control` to avoid the ambiguity.

Reuses build_corpus.py's 48 prompts wholesale -- same questions, same domains,
same 5 non-target distractor documents per prompt, same target format balance.
Only the target document's variants differ.
"""
import hashlib
import json
import pathlib
import sys

# Python puts this script's own directory on the path, not the repo root, so
# the shared leak-check vocabulary has to be reached explicitly.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from check_variants import content_words as _content_words  # noqa: E402

# ---------------------------------------------------------------------------
# `orthogonal` baseline: corpus v0.4's real `control` text, reused verbatim.
# Loaded from corpus_v0.4.json at build time rather than hand-copied, so there
# is no transcription drift from the text already measured at real models.
# ---------------------------------------------------------------------------
_HERE = pathlib.Path(__file__).parent
_V04 = json.loads((_HERE / "corpus_v0.4.json").read_text())

# ---------------------------------------------------------------------------
# Filler bank.
#
# Every sentence must satisfy all four, or it leaks topical surface and the
# whole design collapses into "we added a bit of an answer":
#   1. states no fact
#   2. names no entity
#   3. contains no numeral
#   4. shares no content word with any prompt question or treatment variant
#
# check_variants.py enforces 1, 3 and 4 mechanically against the built corpus.
# ---------------------------------------------------------------------------
FILLER = [
    "This is something that comes up fairly often.",
    "It is worth thinking through rather than rushing.",
    "No one answer here suits everybody equally.",
    "Different readers will weigh these considerations differently.",
    "Reasonable arguments exist on more than one side of it.",
    "The particulars tend to matter more than the general rule.",
    "It helps to be clear about what you are actually after.",
    "Plenty of people have found themselves asking the same thing.",
    "None of this has to be settled in a single sitting.",
    "A little patience tends to reward the reader.",
    "Opinions on the subject vary, and that is to be expected.",
    "It is as easy to overthink as to underthink.",
    "Circumstances differ enough that caution is sensible.",
    "Most who look into it come away with a clearer picture.",
    "The broad shape of it is easier to grasp than the fine print.",
    "Worth revisiting later once the situation is clearer.",
    "Few decisions of this kind are ever truly final.",
    "Being honest about the trade-offs tends to help.",
    "There is rarely any harm in taking a second look.",
    "Context shapes the conclusion more than anything else does.",
]


def _forbidden_for(doc, question):
    """Content words this document's filler may not introduce.

    Scoped to the document's own prompt, not to the corpus as a whole. A
    sentence containing "often" only leaks if *this* prompt's question or
    treatment text uses "often"; pooling the vocabulary of all 48 prompts
    forbids most of ordinary English and leaves nothing usable to pad with.
    """
    v = doc["variants"]
    forbidden = _content_words(question)
    if "treatment" in v and "control" in v:
        forbidden |= _content_words(v["treatment"]) - _content_words(v["control"])
    return forbidden


def _bank_for(doc, question):
    """The filler sentences safe to use in this document."""
    forbidden = _forbidden_for(doc, question)
    return [s for s in FILLER if not (_content_words(s) & forbidden)]


def pad_to(text, ratio, seed_key, bank):
    """Append filler until `text` reaches ~`ratio` times its original length.

    Selection is deterministic in `seed_key`, so rebuilding the corpus from the
    same inputs reproduces it byte-for-byte -- required by the immutability
    rule in CLAUDE.md.
    """
    words = len(text.split())
    target = int(round(words * ratio))
    # A stable per-document offset so every document does not open with the
    # same filler sentence, which would be an obvious artifact to a model.
    offset = int(hashlib.sha256(seed_key.encode()).hexdigest()[:8], 16)

    out = [text]
    total = words
    i = 0
    while total < target and i < len(bank) * 4:
        sentence = bank[(offset + i) % len(bank)]
        out.append(sentence)
        total += len(sentence.split())
        i += 1
    return " ".join(out)


DOSES = {"pad125": 1.25, "pad150": 1.50, "pad200": 2.00}


def build():
    prompts_out = _V04["prompts"]
    questions = {p["prompt_id"]: p["question"] for p in prompts_out}
    thin = []
    docs_out = []

    for doc in _V04["documents"]:
        variants = {"control": doc["variants"]["control"]}
        if doc["is_target"]:
            bank = _bank_for(doc, questions.get(doc["prompt_id"], ""))
            if len(bank) < 6:
                thin.append((doc["doc_id"], len(bank)))
            for name, ratio in DOSES.items():
                variants[name] = pad_to(doc["variants"]["control"], ratio,
                                        f"{doc['doc_id']}|{name}", bank)
        else:
            # Paired design: the five distractors are byte-identical across
            # every condition. run_pilot.py indexes variants by condition for
            # all six documents, so each still needs the key.
            for name in DOSES:
                variants[name] = doc["variants"]["control"]
        docs_out.append({**doc, "variants": variants})

    corpus = {
        "corpus_version": "lengthonly-v1",
        "intervention": "length-only",
        "base_corpus_version": "v0.4",
        "supersedes": None,
        "n_prompts": len(prompts_out),
        "n_docs": len(docs_out),
        "formats": _V04["formats"],
        "domains": _V04["domains"],
        "conditions": ["control"] + list(DOSES),
        "prompts": prompts_out,
        "documents": docs_out,
    }
    payload = json.dumps(corpus, indent=2, sort_keys=True, ensure_ascii=False)
    corpus["corpus_sha256"] = hashlib.sha256(payload.encode()).hexdigest()[:16]

    out = _HERE / "corpus_lengthonly.json"
    out.write_text(json.dumps(corpus, indent=2, ensure_ascii=False))

    if thin:
        print(f"  ! {len(thin)} document(s) had fewer than 6 safe filler "
              f"sentences, so their padding repeats: {thin[:4]}")
        print(f"    Add more topic-neutral sentences to FILLER if this grows.")
    print(f"wrote {out}")
    print(f"  prompts={len(prompts_out)} docs={len(docs_out)} "
          f"sha={corpus['corpus_sha256']}")
    targets = [d for d in docs_out if d["is_target"]]
    base_words = [len(d["variants"]["control"].split()) for d in targets]
    print(f"  control length words: min={min(base_words)} "
          f"median={sorted(base_words)[len(base_words)//2]} max={max(base_words)}")
    for name, ratio in DOSES.items():
        r = sorted(len(d["variants"][name].split())
                   / len(d["variants"]["control"].split()) for d in targets)
        print(f"  {name} ratio (target {ratio:.2f}): min={r[0]:.2f} "
              f"median={r[len(r)//2]:.2f} max={r[-1]:.2f}")
    print("\nNow run: python3 check_variants.py --corpus corpus/corpus_lengthonly.json \\")
    print("           --base control --expect-no-facts pad125 pad150 pad200")


if __name__ == "__main__":
    build()
