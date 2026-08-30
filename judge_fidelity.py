#!/usr/bin/env python3
"""
OpenGEO fidelity judge — Group C metrics (METRICS.md): C1 Claim Fidelity Rate,
C2 Distortion Rate, C3 Verbatim Retention.

"Nobody in the GEO industry reports this." Every prior round in this project measured
*whether* a document gets cited; this measures whether the citation is honest — does
the cited document actually support what the model claims from it. Follows ALCE's
citation-precision construction (arXiv 2305.14627): entailment of each attributed
sentence against its cited source, judged model-vs-model since there is no cheap
ground truth at this scale.

Standard library only except the judge call, which reuses run_pilot.py's OpenRouter
pattern. Operates on an EXISTING results file — no new answers are generated, only
judged, so this is retrospective analysis on data already collected, not a new causal
intervention. It does not need its own pre-registration; it needs the same standards
of honesty applied to the interventions it's checking, which is why the judge model is
required to be outside the 8-model test panel (avoids a model favorably judging its own
family's outputs) and why C1/C2/C3 are reported for kwstuff-v3's own two conditions,
not just pooled — the same "publish nulls" and "equal prominence" discipline as
everywhere else in this project.

    export OPENROUTER_API_KEY=sk-or-...
    python3 judge_fidelity.py --runs results/runs_kwstuff_v3.jsonl \
        --corpus corpus/corpus_kwstuff_v3.json --sample 500 --dry-run
    python3 judge_fidelity.py --runs results/runs_kwstuff_v3.jsonl \
        --corpus corpus/corpus_kwstuff_v3.json --sample 500 \
        --out results/fidelity_kwstuff_v3_qwen_pilot.jsonl
    python3 judge_fidelity.py --runs results/runs_kwstuff_v3.jsonl \
        --corpus corpus/corpus_kwstuff_v3.json --resume \
        --out results/fidelity_kwstuff_v3_qwen_full.jsonl   # no --sample = every item

Design notes
------------
C3 (verbatim n-gram overlap) is computed for every extracted item unconditionally and
for free — no API call needed, so it always covers the full dataset even when C1/C2 are
only judged on a --sample subset. C1/C2 require a judge-model call per sentence; use
--judge-model to run a second, different-vendor judge over the same --sample seed for a
judge-sensitivity check (ROADMAP.md item 4).
"""
import argparse, json, os, pathlib, random, re, sys, threading, time
import urllib.request, urllib.error
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

HERE = pathlib.Path(__file__).parent
API_URL = "https://openrouter.ai/api/v1/chat/completions"
HARNESS_VERSION = "0.1.0"

# Deliberately outside the 8-model test panel (anthropic/openai/google/x-ai/
# moonshotai/deepseek/meta-llama/mistralai) to avoid a judge favoring its own
# family's answers. Two different vendors, not two tiers of one, for the
# judge-sensitivity cross-check.
DEFAULT_JUDGE = "qwen/qwen3.8-max"
CROSSCHECK_JUDGE = "z-ai/glm-5.3"

JUDGE_SYSTEM = (
    "You are a strict fact-checker. You will be given a SOURCE PASSAGE and a CLAIM "
    "that was attributed to it by someone else. Judge whether the SOURCE PASSAGE, on "
    "its own and without any outside knowledge, supports the CLAIM.\n\n"
    "Respond with exactly one label and nothing else:\n"
    "SUPPORTED — every factual assertion in the claim is stated or directly implied "
    "by the passage.\n"
    "PARTIAL — the claim is broadly consistent with the passage but adds a specific "
    "detail (a number, a comparison, a causal claim) that the passage does not state.\n"
    "NOT_SUPPORTED — the claim contradicts the passage, or asserts something the "
    "passage does not address at all."
)

JUDGE_USER_TMPL = """SOURCE PASSAGE:
{passage}

CLAIM:
{claim}

Label:"""

LABEL_RE = re.compile(r"\b(SUPPORTED|PARTIAL|NOT_SUPPORTED)\b", re.IGNORECASE)


def parse_label(text):
    """Last label-word match, not first: when falling back to a reasoning trace
    (content came back empty), the model mentions all three candidate labels
    while thinking through the decision ("So PARTIAL? ... Could be PARTIAL"), and
    the first mention is frequently a tentative one it later reconsiders. The
    *last* mention is the closest available proxy for its conclusion. For a
    clean `content` string (the normal case) there is exactly one match, so this
    makes no difference there."""
    matches = LABEL_RE.findall(text or "")
    return matches[-1].upper() if matches else None


_WORD_RE = re.compile(r"[a-z0-9']+")


def tokenize(text):
    return _WORD_RE.findall((text or "").lower())


def longest_shared_ngram(sentence, passage, min_n=4):
    """Longest run of consecutive words shared between sentence and passage,
    case/punctuation-insensitive. Returns (length, ngram_text) or (0, None)."""
    s_toks = tokenize(sentence)
    p_toks = tokenize(passage)
    if len(s_toks) < min_n:
        return 0, None
    p_ngrams = {}
    for n in range(min_n, len(p_toks) + 1):
        for i in range(len(p_toks) - n + 1):
            p_ngrams.setdefault(n, set()).add(tuple(p_toks[i:i + n]))
    best_n, best_span = 0, None
    for n in range(len(s_toks), min_n - 1, -1):
        pset = p_ngrams.get(n)
        if not pset:
            continue
        for i in range(len(s_toks) - n + 1):
            span = tuple(s_toks[i:i + n])
            if span in pset:
                best_n, best_span = n, " ".join(span)
                break
        if best_span:
            break
    return best_n, best_span


def extract_items(rows, docs_by_id):
    """One item per (run, sentence) where the sentence cites the target document
    and the target was cited at all in that run."""
    items = []
    for r in rows:
        if r.get("error") or not r.get("target_cited"):
            continue
        target_display_idx = r["target_slot"] + 1  # 1-based, matches [n] citations
        scites = r.get("sentence_citations") or []
        target_text = docs_by_id[r["target_doc_id"]]["variants"][r["condition"]]
        for i, s in enumerate(scites):
            if target_display_idx not in s.get("cites", []):
                continue
            items.append({
                "run_key": r["run_key"], "item_key": f"{r['run_key']}#{i}",
                "model": r["model"], "prompt_id": r["prompt_id"],
                "domain": r["domain"], "condition": r["condition"],
                "sentence": s["sentence"],
                "target_doc_id": r["target_doc_id"], "target_text": target_text,
            })
    return items


def stratified_sample(items, n, seed=0):
    """Sample ~n items, stratified by (model, condition) so every cell is
    represented in a pilot rather than leaving it to chance."""
    if n is None or n >= len(items):
        return items
    groups = defaultdict(list)
    for it in items:
        groups[(it["model"], it["condition"])].append(it)
    rng = random.Random(seed)
    for g in groups.values():
        rng.shuffle(g)
    per_group = max(1, n // len(groups))
    out = []
    for g in groups.values():
        out.extend(g[:per_group])
    # top up to n from leftovers if per-group floor undershot due to rounding
    if len(out) < n:
        taken = {it["item_key"] for it in out}
        leftovers = [it for g in groups.values() for it in g[per_group:]
                     if it["item_key"] not in taken]
        rng.shuffle(leftovers)
        out.extend(leftovers[:n - len(out)])
    return out[:n] if len(out) > n else out


def call_judge(judge_model, passage, claim, api_key, timeout=60, retries=3):
    body = json.dumps({
        "model": judge_model,
        "messages": [
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": JUDGE_USER_TMPL.format(passage=passage, claim=claim)},
        ],
        "temperature": 0.0,
        # Several 2026-era flagships (qwen3.8-max included) reason by default and
        # cannot have it disabled on this endpoint ("Reasoning is mandatory for
        # this endpoint"); reasoning tokens count against max_tokens, so a small
        # budget starves the actual label and finish_reason comes back "length"
        # with content=null. 900 still truncated 23% of a 500-item pilot, and
        # NOT SYMMETRICALLY: judging an orthogonal (no-fact) passage against a
        # claim needs more deliberation than a keyword-stuffed one (27% vs 18%
        # truncation), which would confound exactly the condition comparison
        # this metric exists to make. 1500 was chosen after the 900-token pilot
        # showed real items using up to ~900+ reasoning tokens on the harder
        # (orthogonal, absence-reasoning) cases.
        "max_tokens": 1500,
    }).encode()
    req = urllib.request.Request(
        API_URL, data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/opengeo/benchmark",
            "X-Title": "OpenGEO Fidelity Judge",
        },
    )
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                d = json.loads(resp.read())
            if "choices" not in d:
                raise RuntimeError(f"no choices: {str(d)[:200]}")
            msg = d["choices"][0]["message"]
            # Fall back to the reasoning trace if content came back empty (e.g. a
            # reasoning model that still got truncated before emitting content) —
            # parse_label() extracts the label from whichever text is present.
            text = msg.get("content") or msg.get("reasoning") or ""
            return {
                "text": text,
                "model_returned": d.get("model", judge_model),
                "finish_reason": d["choices"][0].get("finish_reason"),
                "usage": d.get("usage", {}),
            }
        except Exception as e:  # noqa: BLE001 - retry on anything transient
            last = e
            if attempt < retries - 1:
                time.sleep(2 ** attempt + random.random())
    return {"error": f"{type(last).__name__}: {last}"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True, help="results JSONL to judge (already collected)")
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--judge-model", default=DEFAULT_JUDGE)
    ap.add_argument("--sample", type=int, default=None,
                     help="stratified sample size for C1/C2 judging (by model, condition). "
                          "C3 always runs on every item regardless of --sample.")
    ap.add_argument("--seed", type=int, default=0, help="sampling seed, for reproducibility "
                                                          "and for matching a cross-judge run to the same subsample")
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    corpus = json.loads(pathlib.Path(args.corpus).read_text())
    docs_by_id = {d["doc_id"]: d for d in corpus["documents"]}
    rows = [json.loads(line) for line in pathlib.Path(args.runs).read_text().splitlines() if line.strip()]

    all_items = extract_items(rows, docs_by_id)
    judged_items = stratified_sample(all_items, args.sample, seed=args.seed)
    judged_keys = {it["item_key"] for it in judged_items}

    if args.dry_run:
        approx_in = sum(len(it["target_text"]) + len(it["sentence"]) for it in judged_items) / 4
        approx_in += len(JUDGE_SYSTEM) / 4 * len(judged_items)
        approx_out = 280 * len(judged_items)  # reasoning tokens dominate; see call_judge()
        print(f"runs file        : {args.runs} ({len(rows):,} rows)")
        print(f"target-cited attributed sentences (C3, free) : {len(all_items):,}")
        print(f"judged subsample (C1/C2, seed={args.seed})   : {len(judged_items):,}"
              + (" (= all items, no --sample)" if args.sample is None else ""))
        print(f"judge model      : {args.judge_model}")
        print(f"tokens           : ~{approx_in/1e6:.3f}M in, ~{approx_out/1e6:.3f}M out")
        for lbl, ci, co in (("low  ($0.10/$0.40 per M)", .10, .40),
                            ("mid  ($1.00/$4.00 per M)", 1.0, 4.0),
                            ("high ($2.50/$8.00 per M)", 2.5, 8.0)):
            print(f"  est {lbl}: ${approx_in/1e6*ci + approx_out/1e6*co:6.2f}")
        by_cell = defaultdict(int)
        for it in judged_items:
            by_cell[(it["model"], it["condition"])] += 1
        print("\nsample coverage by (model, condition):")
        for k in sorted(by_cell):
            print(f"  {k[0]:35} {k[1]:10} n={by_cell[k]}")
        return

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        sys.exit("OPENROUTER_API_KEY not set")

    outp = pathlib.Path(args.out or f"results/fidelity_{corpus['corpus_version']}_{args.judge_model.split('/')[-1]}.jsonl")
    outp.parent.mkdir(parents=True, exist_ok=True)

    done = set()
    if args.resume and outp.exists():
        for line in outp.read_text().splitlines():
            try:
                rec = json.loads(line)
                if not rec.get("error"):
                    done.add(rec["item_key"])
            except Exception:
                pass
        print(f"resume: {len(done)} already complete")

    lock = threading.Lock()
    fh = outp.open("a")
    counter = {"n": 0, "err": 0}
    total = len(all_items)
    t0 = time.time()

    def work(item):
        if item["item_key"] in done:
            return
        n_shared, ngram_text = longest_shared_ngram(item["sentence"], item["target_text"])
        rec = {
            "item_key": item["item_key"], "harness_version": HARNESS_VERSION,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "run_key": item["run_key"], "model": item["model"],
            "prompt_id": item["prompt_id"], "domain": item["domain"],
            "condition": item["condition"], "sentence": item["sentence"],
            "target_doc_id": item["target_doc_id"],
            "verbatim_overlap_words": n_shared,
            "verbatim_overlap_ngram": ngram_text,
        }
        if item["item_key"] in judged_keys:
            resp = call_judge(args.judge_model, item["target_text"], item["sentence"], api_key)
            if "error" in resp:
                rec["error"] = resp["error"]
            else:
                rec.update({
                    "judge_model": args.judge_model,
                    "judge_model_returned": resp["model_returned"],
                    "judge_finish_reason": resp.get("finish_reason"),
                    "judge_raw": resp["text"],
                    "judge_label": parse_label(resp["text"]),
                })
        with lock:
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            counter["n"] += 1
            if "error" in rec:
                counter["err"] += 1
            n = counter["n"]
            if n % 25 == 0 or n == total:
                rate = n / max(time.time() - t0, 1e-9)
                eta = (total - n) / max(rate, 1e-9)
                print(f"  {n}/{total}  err={counter['err']}  {rate:.1f}/s  eta {eta/60:.1f}m", flush=True)

    print(f"processing {total:,} items ({len(judged_items):,} judged by {args.judge_model}, "
          f"rest C3-only), concurrency {args.concurrency}")
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        list(ex.map(work, all_items))
    fh.close()


if __name__ == "__main__":
    main()
