#!/usr/bin/env python3
"""
OpenGEO pilot runner — queries models via OpenRouter over a fixed candidate corpus.

Standard library only. Resumable. Logs full provenance per run.

    export OPENROUTER_API_KEY=sk-or-...
    python3 run_pilot.py --dry-run          # cost estimate, no API calls
    python3 run_pilot.py --runs 10          # the real thing
    python3 run_pilot.py --runs 10 --resume # continue an interrupted run

Design notes
------------
Document order is randomised per run from a seed derived from the run key, so the
whole experiment is reproducible from (corpus_version, seed) alone while still
decorrelating position from document identity. The target's 0-indexed slot is
recorded on every run, which is what makes the Position Sensitivity Index
estimable at no additional cost.
"""
import argparse, hashlib, json, os, pathlib, random, re, sys, threading, time
import urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

HERE = pathlib.Path(__file__).parent
API_URL = "https://openrouter.ai/api/v1/chat/completions"
HARNESS_VERSION = "0.1.0"

# Deliberately mid/low-cost tiers. Frontier flagships blow a $20 pilot budget on
# input tokens alone; the pilot is about metric validity, not model ranking.
DEFAULT_MODELS = [
    "anthropic/claude-haiku-4.5",
    "openai/gpt-5.2-mini",
    "google/gemini-3-flash",
    "x-ai/grok-4-mini",
    "moonshotai/kimi-k2",
    "deepseek/deepseek-chat",
    "meta-llama/llama-4-maverick",
    "mistralai/mistral-medium-3",
]

SYSTEM = (
    "You answer questions using only the numbered sources provided. "
    "Write a concise answer of 3-6 sentences. "
    "Cite sources inline using square brackets like [1] or [3] immediately after "
    "the claim they support. Cite every source you actually use, and do not cite "
    "sources you did not use. Do not add information beyond the sources."
)

USER_TMPL = """Question: {question}

Sources:
{sources}

Answer the question using the sources above, citing inline with [n]."""


def build_messages(question, docs):
    """docs: list of (display_index, text) already in presentation order."""
    src = "\n\n".join(f"[{i}] {t}" for i, t in docs)
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": USER_TMPL.format(question=question, sources=src)},
    ]


CITE_RE = re.compile(r"\[(\d{1,2})\]")


def parse_citations(text, n_docs):
    """Ordered, de-duplicated 1-based citation indices that are in range."""
    seen, out = set(), []
    for m in CITE_RE.finditer(text or ""):
        i = int(m.group(1))
        if 1 <= i <= n_docs and i not in seen:
            seen.add(i)
            out.append(i)
    return out


def sentence_citations(text, n_docs):
    """Map each sentence to the citation indices appearing in it."""
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    res = []
    for s in parts:
        if not s.strip():
            continue
        idx = sorted({int(m.group(1)) for m in CITE_RE.finditer(s)
                      if 1 <= int(m.group(1)) <= n_docs})
        res.append({"sentence": s.strip(), "cites": idx})
    return res


def call_openrouter(model, messages, api_key, temperature, timeout=120, retries=3):
    body = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 700,
    }).encode()
    req = urllib.request.Request(
        API_URL, data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/opengeo/benchmark",
            "X-Title": "OpenGEO Pilot",
        },
    )
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.loads(r.read())
            if "choices" not in d:
                raise RuntimeError(f"no choices: {str(d)[:200]}")
            return {
                "text": d["choices"][0]["message"]["content"],
                "usage": d.get("usage", {}),
                "model_returned": d.get("model", model),
                "finish_reason": d["choices"][0].get("finish_reason"),
            }
        except Exception as e:  # noqa: BLE001 - retry on anything transient
            last = e
            if attempt < retries - 1:
                time.sleep(2 ** attempt + random.random())
    return {"error": f"{type(last).__name__}: {last}"}


def run_key(model, prompt_id, condition, rep):
    return f"{model}|{prompt_id}|{condition}|{rep}"


def order_seed(corpus_version, key):
    h = hashlib.sha256(f"{corpus_version}|{key}".encode()).hexdigest()
    return int(h[:12], 16)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=str(HERE / "corpus" / "corpus_v0.2.json"))
    ap.add_argument("--out", default=str(HERE / "results" / "runs.jsonl"))
    ap.add_argument("--runs", type=int, default=24,
                    help="repetitions per cell. 24 is not arbitrary: the mock-data "
                         "reliability curve shows split-half reliability crossing the "
                         "usable threshold between n=16 and n=24. Do not use 10.")
    ap.add_argument("--models", nargs="*", default=DEFAULT_MODELS)
    ap.add_argument("--conditions", nargs="*", default=["control", "treatment"])
    ap.add_argument("--temperature", type=float, default=1.0,
                    help="1.0 samples the model's natural distribution, which is what "
                         "a real user gets; do not lower this to reduce variance")
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    corpus = json.loads(pathlib.Path(args.corpus).read_text())
    docs_by_id = {d["doc_id"]: d for d in corpus["documents"]}
    prompts = corpus["prompts"]

    cells = [(m, p, c, r)
             for m in args.models
             for p in prompts
             for c in args.conditions
             for r in range(args.runs)]

    outp = pathlib.Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)

    done = set()
    if args.resume and outp.exists():
        for line in outp.read_text().splitlines():
            try:
                rec = json.loads(line)
                if not rec.get("error"):
                    done.add(rec["run_key"])
            except Exception:
                pass
        cells = [c for c in cells if run_key(c[0], c[1]["prompt_id"], c[2], c[3]) not in done]
        print(f"resume: {len(done)} already complete, {len(cells)} remaining")

    if args.dry_run:
        p = prompts[0]
        texts = [docs_by_id[d]["variants"]["control"] for d in p["doc_ids"]]
        msgs = build_messages(p["question"], list(enumerate(texts, 1)))
        approx_in = len(msgs[0]["content"] + msgs[1]["content"]) / 4
        tot_in = approx_in * len(cells)
        tot_out = 250 * len(cells)
        print(f"corpus      : v{corpus['corpus_version']} "
              f"({corpus['n_prompts']} prompts x {corpus['n_docs']} docs)")
        print(f"models      : {len(args.models)}")
        print(f"cells       : {len(cells):,} calls "
              f"({len(args.models)}m x {len(prompts)}p x "
              f"{len(args.conditions)}c x {args.runs}r)")
        print(f"tokens      : ~{tot_in/1e6:.2f}M in, ~{tot_out/1e6:.2f}M out")
        for lbl, ci, co in (("low  ($0.15/$0.60 per M)", .15, .60),
                            ("mid  ($0.50/$1.50 per M)", .50, 1.50),
                            ("high ($2.00/$8.00 per M)", 2.0, 8.0)):
            print(f"  est {lbl}: ${tot_in/1e6*ci + tot_out/1e6*co:6.2f}")
        print("\nsample prompt sent to the model:\n" + "-" * 60)
        print(msgs[1]["content"][:900] + "\n...")
        return

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        sys.exit("OPENROUTER_API_KEY not set")

    lock = threading.Lock()
    fh = outp.open("a")
    counter = {"n": 0, "err": 0}
    total = len(cells)
    t0 = time.time()

    def work(cell):
        model, prompt, condition, rep = cell
        key = run_key(model, prompt["prompt_id"], condition, rep)

        # deterministic-but-decorrelated presentation order
        order = list(prompt["doc_ids"])
        random.Random(order_seed(corpus["corpus_version"], key)).shuffle(order)
        texts = [docs_by_id[d]["variants"][condition] for d in order]
        target_slot = order.index(prompt["target_doc_id"])  # 0-indexed

        msgs = build_messages(prompt["question"], list(enumerate(texts, 1)))
        t = time.time()
        resp = call_openrouter(model, msgs, api_key, args.temperature)
        elapsed = time.time() - t

        rec = {
            "run_key": key, "harness_version": HARNESS_VERSION,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "corpus_version": corpus["corpus_version"],
            "model": model, "prompt_id": prompt["prompt_id"],
            "domain": prompt["domain"], "condition": condition, "rep": rep,
            "temperature": args.temperature,
            "presentation_order": order,
            "target_doc_id": prompt["target_doc_id"],
            "target_format": prompt["target_format"],
            "target_slot": target_slot, "n_docs": len(order),
            "latency_s": round(elapsed, 2),
        }
        if "error" in resp:
            rec["error"] = resp["error"]
        else:
            txt = resp["text"]
            cites = parse_citations(txt, len(order))
            # map 1-based display index -> doc_id
            cited_ids = [order[i - 1] for i in cites]
            rec.update({
                "response_text": txt,
                "model_returned": resp["model_returned"],
                "finish_reason": resp.get("finish_reason"),
                "usage": resp.get("usage", {}),
                "cited_display_idx": cites,
                "cited_doc_ids": cited_ids,
                "target_cited": prompt["target_doc_id"] in cited_ids,
                "target_cite_rank": (cited_ids.index(prompt["target_doc_id"])
                                     if prompt["target_doc_id"] in cited_ids else None),
                "sentence_citations": sentence_citations(txt, len(order)),
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
                print(f"  {n}/{total}  err={counter['err']}  "
                      f"{rate:.1f}/s  eta {eta/60:.1f}m", flush=True)

    print(f"running {total:,} calls across {len(args.models)} models "
          f"(concurrency {args.concurrency})")
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        list(ex.map(work, cells))
    fh.close()
    print(f"done in {(time.time()-t0)/60:.1f}m -> {outp}  ({counter['err']} errors)")


if __name__ == "__main__":
    main()
