#!/usr/bin/env python3
"""
OpenGEO calibration study — API plane collector (METHODOLOGY.md §3, ROADMAP.md item 8).

Queries real, live-search-enabled consumer engines via their actual APIs (through
OpenRouter, same infra as run_pilot.py) on the shared prompt set in
calibration_prompts.py. This is the reproducible, ToS-clean plane of the three-plane
calibration design; the logged-out and logged-in UI planes are collected separately
(manually / browser-assisted, per METHODOLOGY.md's sanctioned small-n method) and
compared against this plane's cited-domain sets to compute the divergence coefficient.

Standard library only. Resumable.

    export OPENROUTER_API_KEY=sk-or-...
    python3 calibration_api.py --dry-run
    python3 calibration_api.py --runs 3
"""
import argparse, hashlib, json, os, pathlib, sys, threading, time
import urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.parse import urlparse

import calibration_prompts as cp

HERE = pathlib.Path(__file__).parent
API_URL = "https://openrouter.ai/api/v1/chat/completions"
HARNESS_VERSION = "0.1.0"

# The "API plane" — each engine's actual live-search product, reached via the same
# OpenRouter key as the rest of this project rather than four separate vendor keys.
# openai/gpt-5.4-mini + the `web` plugin gives OpenAI's real web_search tool
# (verified: returns proper url_citation annotations with real URLs). Perplexity's
# sonar-pro-search is natively search-grounded, no plugin needed.
ENGINES = {
    "openai": {"model": "openai/gpt-5.4-mini", "plugins": [{"id": "web"}]},
    "perplexity": {"model": "perplexity/sonar-pro-search", "plugins": None},
}


def extract_cited(text_annotations):
    urls, domains = [], []
    seen_d = set()
    for a in text_annotations or []:
        if a.get("type") != "url_citation":
            continue
        url = a.get("url_citation", {}).get("url")
        if not url:
            continue
        urls.append(url)
        try:
            d = urlparse(url).netloc.lower().removeprefix("www.")
        except Exception:
            d = None
        if d and d not in seen_d:
            seen_d.add(d)
            domains.append(d)
    return urls, domains


def call_openrouter(model, prompt, api_key, plugins=None, temperature=1.0, timeout=90, retries=3):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": 600,
    }
    if plugins:
        body["plugins"] = plugins
    req = urllib.request.Request(
        API_URL, data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/opengeo/benchmark",
            "X-Title": "OpenGEO Calibration Study",
        },
    )
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.loads(r.read())
            if "choices" not in d:
                raise RuntimeError(f"no choices: {str(d)[:200]}")
            msg = d["choices"][0]["message"]
            return {
                "text": msg.get("content"),
                "annotations": msg.get("annotations"),
                "model_returned": d.get("model", model),
                "provider": d.get("provider"),
                "finish_reason": d["choices"][0].get("finish_reason"),
                "usage": d.get("usage", {}),
            }
        except Exception as e:  # noqa: BLE001 - retry on anything transient
            last = e
            if attempt < retries - 1:
                time.sleep(2 ** attempt + 0.5)
    return {"error": f"{type(last).__name__}: {last}"}


def run_key(engine, prompt_id, rep):
    return f"{engine}|{prompt_id}|{rep}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "results" / "calibration_api.jsonl"))
    ap.add_argument("--engines", nargs="*", default=list(ENGINES))
    ap.add_argument("--runs", type=int, default=3,
                     help="reps per (engine, prompt) cell. Small by design (see "
                          "METHODOLOGY.md's calibration-study rationale) -- this "
                          "measures divergence between planes, not the reliability "
                          "curve the main experiment's 24 runs are calibrated for.")
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    cells = [(eng, p, r) for eng in args.engines for p in cp.PROMPTS for r in range(args.runs)]

    if args.dry_run:
        print(f"engines: {args.engines}")
        print(f"prompts: {len(cp.PROMPTS)}  runs/cell: {args.runs}")
        print(f"cells  : {len(cells)} calls ({len(args.engines)}e x {len(cp.PROMPTS)}p x {args.runs}r)")
        print("\nsample prompt:")
        print(f"  [{cp.PROMPTS[0][0]}] {cp.PROMPTS[0][2]}")
        print("\n(no per-token cost estimate here -- web-search-tool cost is a flat")
        print(" per-call server_tool_use fee on top of tokens, vendor-dependent;")
        print(f" run a single real call per engine to check actual `usage.cost` first.)")
        return

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        sys.exit("OPENROUTER_API_KEY not set")

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
        cells = [c for c in cells if run_key(c[0], c[1][0], c[2]) not in done]
        print(f"resume: {len(done)} already complete, {len(cells)} remaining")

    lock = threading.Lock()
    fh = outp.open("a")
    counter = {"n": 0, "err": 0}
    total = len(cells)
    t0 = time.time()

    def work(cell):
        engine, prompt, rep = cell
        pid, domain, text = prompt
        key = run_key(engine, pid, rep)
        spec = ENGINES[engine]

        t = time.time()
        resp = call_openrouter(spec["model"], text, api_key, plugins=spec["plugins"],
                                temperature=args.temperature)
        elapsed = time.time() - t

        rec = {
            "run_key": key, "harness_version": HARNESS_VERSION,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "plane": "api", "engine": engine, "model": spec["model"],
            "prompt_id": pid, "domain": domain, "question": text, "rep": rep,
            "temperature": args.temperature, "latency_s": round(elapsed, 2),
        }
        if "error" in resp:
            rec["error"] = resp["error"]
        else:
            urls, doms = extract_cited(resp.get("annotations"))
            rec.update({
                "response_text": resp["text"],
                "model_returned": resp["model_returned"],
                "provider": resp.get("provider"),
                "finish_reason": resp.get("finish_reason"),
                "usage": resp.get("usage", {}),
                "cited_urls": urls,
                "cited_domains": doms,
            })

        with lock:
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            counter["n"] += 1
            if "error" in rec:
                counter["err"] += 1
            n = counter["n"]
            if n % 5 == 0 or n == total:
                rate = n / max(time.time() - t0, 1e-9)
                eta = (total - n) / max(rate, 1e-9)
                print(f"  {n}/{total}  err={counter['err']}  {rate:.1f}/s  eta {eta/60:.1f}m", flush=True)

    print(f"running {total} calls across {len(args.engines)} engines (concurrency {args.concurrency})")
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        list(ex.map(work, cells))
    fh.close()


if __name__ == "__main__":
    main()
