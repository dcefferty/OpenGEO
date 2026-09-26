#!/usr/bin/env python3
"""
OpenGEO -- test whether a change to your page makes AI engines more likely to cite it.

    export OPENROUTER_API_KEY=sk-or-...
    python3 opengeo.py test \\
        --question "How much does a home energy audit cost?" \\
        --page     https://mysite.com/energy-audit \\
        --edit     ./energy-audit-v2.md \\
        --against  https://competitor-a.com/audits https://competitor-b.com/pricing

It runs a paired, controlled experiment -- the design every published OpenGEO round uses --
on your own page: your current version and your edited version, each placed among your
competitors' pages, across the five engines that carry 98.9% of AI-assistant traffic. It
reports whether your change moved citation, by how much, with an interval, per engine.

It is a measurement, not advice. It never tells you what to change. Design and the
evidence behind every default: `design/opengeo-test.md`.

Standard library for everything except the analysis, which uses numpy.
"""
import argparse
import difflib
import hashlib
import json
import os
import pathlib
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "corpus"))

import engine_weights  # noqa: E402
import run_pilot as rp  # noqa: E402
import sources as src  # noqa: E402

TOOL_VERSION = "0.1.0"

# ---------------------------------------------------------------------- defaults ----
# Every value here is argued for in design/opengeo-test.md. The first group has no flag,
# because there is no evidence that relaxing any of them leaves a result unbiased.
RUNS = 24                       # split-half reliability of a difference: 0.21 at 10, 0.75 at 24
TEMPERATURE = 1.0               # the answers a real user sees
PANEL = [m for _, (_, m) in engine_weights.ENGINES.items() if m]   # 98.9% of traffic

LENGTH_TOLERANCE = 3            # METHODOLOGY 9; relaxable only with --allow-length-change (H7)
WINDOW_MIN, WINDOW_TARGET, WINDOW_MAX = 50, 80, 110   # the regime every published effect used
CEILING = 21 / 24               # current page cited this often: no room left to improve
SATURATED = 23 / 24             # edited page cited this often: the effect is a lower bound
MIN_COMPETITORS, RECOMMENDED_COMPETITORS = 2, 4
CONCURRENCY = 6


class ToolError(Exception):
    """A problem with the inputs, explained in plain language. Printed, never traced."""


# ------------------------------------------------------------------- reading pages ----
def read_source(ref):
    """Text of a page given a URL or a local file. Returns (text, provenance).

    Pages are read into memory and written only to this test's own results folder --
    never into corpus/sources/, which is the benchmark's committed snapshot store and has
    no business holding anyone's competitor pages.
    """
    if re.match(r"https?://", ref):
        status, body = src._curl(ref)
        if status != 200:
            why = "timed out" if status is None else f"returned HTTP {status}"
            raise ToolError(
                f"Could not fetch {ref} -- it {why}.\n"
                "  Some sites refuse automated requests. Save the page in your browser "
                "(File > Save As) and pass the saved file instead.")
        text = src.visible_text(body)
        prov = {"ref": ref, "kind": "url", "http_status": status}
    else:
        p = pathlib.Path(ref).expanduser()
        if not p.is_file():
            raise ToolError(f"No such file: {ref}")
        raw = p.read_text(encoding="utf-8", errors="replace")
        looks_html = bool(re.search(r"<(html|body|p|div|h[1-6])[\s>]", raw, re.I))
        text = src.visible_text(raw) if looks_html else raw
        prov = {"ref": str(p), "kind": "file"}
    text = src.norm(text)
    if len(text.split()) < 20:
        raise ToolError(
            f"{ref} has almost no readable text ({len(text.split())} words).\n"
            "  If it is a JavaScript-rendered page, save it from your browser and pass the "
            "saved file instead.")
    prov["sha256"] = hashlib.sha256(text.encode()).hexdigest()[:16]
    prov["words"] = len(text.split())
    return text, prov


# --------------------------------------------------------------------- edit region ----
_SENTENCE_END = re.compile(r"[.!?][\"')\]]*$")


def _ends_sentence(word):
    return bool(_SENTENCE_END.search(word))


def edit_region(original, edited, target=WINDOW_TARGET):
    """The section of your page that your edit changed, as it reads before and after.

    Compares the two versions word by word, finds the first and last point where they
    differ, and widens that span with the context the two versions share -- the same words
    on both sides -- until it is about `target` words long, then to sentence boundaries so
    each excerpt reads as prose. Because the widening only ever uses shared context, the
    two excerpts differ in exactly your change and nothing else: that is what makes the
    comparison paired.
    """
    a, b = original.split(), edited.split()
    changes = [op for op in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes()
               if op[0] != "equal"]
    if not changes:
        raise ToolError("Your edited page is identical to your current page, so there is "
                        "nothing to test.")
    i1, i2 = min(o[1] for o in changes), max(o[2] for o in changes)
    j1, j2 = min(o[3] for o in changes), max(o[4] for o in changes)
    # a[:i1] == b[:j1] and a[i2:] == b[j2:], with equal lengths, by construction.
    prefix, suffix = i1, len(a) - i2

    budget = max(0, target - max(i2 - i1, j2 - j1))
    before, after = budget // 2, budget - budget // 2
    if before > prefix:
        after, before = after + before - prefix, prefix
    if after > suffix:
        before, after = min(prefix, before + after - suffix), suffix

    # widen to sentence boundaries, but only through shared context and only so far
    start = i1 - before
    k = 0
    while start > 0 and k < 30 and not _ends_sentence(a[start - 1]):
        start, k = start - 1, k + 1
    end_a = i2 + after
    k = 0
    while end_a < len(a) and k < 30 and not _ends_sentence(a[end_a - 1]):
        end_a, k = end_a + 1, k + 1
    tail = end_a - i2                      # shared words kept after the change

    shift = i1 - start                     # shared words kept before the change
    control = " ".join(a[start:end_a])
    treatment = " ".join(b[j1 - shift:j2 + tail])
    return control, treatment, {
        "words_changed_before": i2 - i1,
        "words_changed_after": j2 - j1,
        "shared_context_words": shift + tail,
        "position_in_page": round(i1 / max(len(a), 1), 2),
    }


# ------------------------------------------------------------- competitor sections ----
_STOP = set("""a an and are as at be been but by can do does for from has have how i if in
into is it its of on or should so than that the their them then there these they this to
was what when where which who why will with would you your yours my me our we get
about much many more most""".split())


def _terms(text):
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in _STOP and len(w) > 2}


def best_section(text, question, lo=WINDOW_MIN, target=WINDOW_TARGET):
    """The run of consecutive sentences, about `target` words long, sharing the most terms
    with the question. This stands in for what a retrieval step would plausibly hand an
    engine from that page. Ties go to the earliest section on the page."""
    sents = src.sentences(text)
    q = _terms(question)
    best = None
    for i in range(len(sents)):
        words, j = 0, i
        while j < len(sents) and words < target:
            words += len(sents[j].split())
            j += 1
        if words < lo:
            continue
        chunk = " ".join(sents[i:j])
        score = len(q & _terms(chunk))
        if best is None or score > best[0]:
            best = (score, chunk)
    if best is None:                                 # the whole page is shorter than `lo`
        return text, len(q & _terms(text))
    return best[1], best[0]


# ------------------------------------------------------------------ corpus assembly ----
def slugify(s, n=40):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:n].rstrip("-") or "test"


def build_corpus(questions, page, edit, competitors):
    """One paired test per question: your excerpt, as it is and as edited, among the most
    relevant section of each competitor page. Only your excerpt differs between arms."""
    original, page_prov = read_source(page)
    edited, edit_prov = read_source(edit)
    control, treatment, region = edit_region(original, edited)

    comp_texts = []
    for ref in competitors:
        text, prov = read_source(ref)
        comp_texts.append((ref, text, prov))

    documents, prompts = [], []
    for k, question in enumerate(questions, 1):
        pid = f"q{k}"
        target = f"{pid}__yours"
        ids = [target]
        documents.append({"doc_id": target, "prompt_id": pid, "is_target": True,
                          "source": {"yours": page_prov, "edit": edit_prov},
                          "variants": {"control": control, "treatment": treatment}})
        for c, (ref, text, prov) in enumerate(comp_texts, 1):
            section, overlap = best_section(text, question)
            did = f"{pid}__competitor{c}"
            ids.append(did)
            documents.append({"doc_id": did, "prompt_id": pid, "is_target": False,
                              "source": {**prov, "question_term_overlap": overlap},
                              "variants": {"control": section, "treatment": section}})
        prompts.append({"prompt_id": pid, "question": question, "domain": "user",
                        "target_doc_id": target, "target_format": "user", "doc_ids": ids})

    body = {"prompts": prompts, "documents": documents}
    digest = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:12]
    return {"corpus_version": f"opengeo-test-{digest}", "corpus_sha256": digest,
            "tool_version": TOOL_VERSION, "edit_region": region,
            "n_prompts": len(prompts), "n_docs": len(documents), **body}


# ------------------------------------------------------------------- preflight ----
def preflight(corpus, n_competitors, allow_length_change):
    """Checks that need no API calls. Returns (blocks, warnings, passes), each a list of
    plain-language strings. Any block stops the run before anything is spent."""
    blocks, warns, oks = [], [], []
    t = next(d for d in corpus["documents"] if d["is_target"])
    cw = len(t["variants"]["control"].split())
    tw = len(t["variants"]["treatment"].split())
    diff = tw - cw

    if abs(diff) <= LENGTH_TOLERANCE:
        oks.append(f"Your edit is within {LENGTH_TOLERANCE} words of the original length "
                   f"({cw} -> {tw} words)")
    elif allow_length_change:
        warns.append(
            f"Your edit changes the length by {diff:+d} words ({cw} -> {tw}). Allowed by "
            "--allow-length-change: OpenGEO's H7 round measured doubling a page's length at "
            "+0.004 (CI -0.023 to +0.031), so length alone is not expected to explain an "
            "effect. The report records that this flag was used.")
    else:
        blocks.append(
            f"Your edit changes the length by {diff:+d} words ({cw} -> {tw}).\n"
            "    A length change can masquerade as an effect, so by default the edit must stay "
            f"within {LENGTH_TOLERANCE} words. Two ways forward:\n"
            "      - make the edit replace wording rather than add it, or\n"
            "      - re-run with --allow-length-change. OpenGEO measured padding a page to twice "
            "its length at +0.004,\n"
            "        so length alone does not move citation; the report will say you used it.")

    if n_competitors < MIN_COMPETITORS:
        blocks.append(f"At least {MIN_COMPETITORS} competitor pages are needed (--against). With "
                      "fewer, your page has almost nothing to compete with and gets cited by "
                      "default.")
    elif n_competitors < RECOMMENDED_COMPETITORS:
        warns.append(f"{n_competitors} competitors given. Every published OpenGEO round used 5 "
                     f"other documents; {RECOMMENDED_COMPETITORS}-5 makes the test closer to "
                     "real conditions.")
    else:
        oks.append(f"{n_competitors} competitor pages")

    if corpus["n_prompts"] == 1:
        warns.append("One question. The result will be true for this question; test 3-5 "
                     "questions your customers actually ask before generalising.")
    if max(cw, tw) > WINDOW_MAX * 1.5:
        warns.append(f"Your edit is large: the tested excerpt is {max(cw, tw)} words, against "
                     f"about {WINDOW_TARGET} in every published round. Smaller, focused edits "
                     "give clearer answers.")
    return blocks, warns, oks


def estimate_cost(corpus):
    """(calls, low, high) in US dollars. Tokens are estimated from the text actually sent;
    prices bracket the panel's current rates rather than pretending to one exact figure."""
    per_q_chars = {}
    for p in corpus["prompts"]:
        docs = [d for d in corpus["documents"] if d["prompt_id"] == p["prompt_id"]]
        per_q_chars[p["prompt_id"]] = (len(rp.SYSTEM) + len(p["question"])
                                       + sum(len(d["variants"]["control"]) for d in docs) + 200)
    calls = corpus["n_prompts"] * 2 * len(PANEL) * RUNS
    tok_in = sum(per_q_chars.values()) / 4 * 2 * len(PANEL) * RUNS
    tok_out = 220 * calls
    low = tok_in / 1e6 * 0.15 + tok_out / 1e6 * 0.60
    high = tok_in / 1e6 * 0.50 + tok_out / 1e6 * 1.50
    return calls, low, high


# ---------------------------------------------------------------------- running ----
def _load_rows(path):
    rows = []
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return rows


def run_calls(corpus, condition, prompt_ids, outp, api_key, label):
    """Run every (question, engine, repeat) cell for one arm that is not already done.
    Resumable: a cell counts as done only when it has a successful response on disk."""
    prompts = [p for p in corpus["prompts"] if p["prompt_id"] in prompt_ids]
    docs = {d["doc_id"]: d for d in corpus["documents"]}
    done = {r["run_key"] for r in _load_rows(outp) if not r.get("error")}
    cells = [(m, p, rep) for p in prompts for m in PANEL for rep in range(RUNS)
             if rp.run_key(m, p["prompt_id"], condition, rep) not in done]
    if not cells:
        print(f"  {label}: already complete, nothing to send")
        return 0
    already = len(prompts) * len(PANEL) * RUNS - len(cells)
    print(f"  {label}: {len(cells)} calls" + (f" ({already} already done, resuming)"
                                               if already else ""))
    lock, state = threading.Lock(), {"n": 0, "err": 0}
    total, t0 = len(cells), time.time()
    # Overwriting one line with \r is right in a terminal and unreadable anywhere else --
    # piped into a log, or into the Claude skill, it piles up into one long line. So a
    # terminal gets a live counter and everything else gets a few whole lines.
    tty = sys.stdout.isatty()
    step = 20 if tty else max(total // 4, 1)

    def work(cell):
        model, prompt, rep = cell
        key = rp.run_key(model, prompt["prompt_id"], condition, rep)
        order = list(prompt["doc_ids"])
        random.Random(rp.order_seed(corpus["corpus_version"], key)).shuffle(order)
        texts = [docs[d]["variants"][condition] for d in order]
        resp = rp.call_openrouter(model, rp.build_messages(prompt["question"],
                                                           list(enumerate(texts, 1))),
                                  api_key, TEMPERATURE)
        rec = {"run_key": key, "tool_version": TOOL_VERSION,
               "timestamp_utc": datetime.now(timezone.utc).isoformat(),
               "corpus_version": corpus["corpus_version"], "model": model,
               "prompt_id": prompt["prompt_id"], "condition": condition, "rep": rep,
               "temperature": TEMPERATURE, "presentation_order": order,
               "target_doc_id": prompt["target_doc_id"],
               "target_slot": order.index(prompt["target_doc_id"]), "n_docs": len(order)}
        if "error" in resp:
            rec["error"] = resp["error"]           # never contains the key: see call_openrouter
        else:
            cites = rp.parse_citations(resp["text"], len(order))
            ids = [order[i - 1] for i in cites]
            rec.update({"response_text": resp["text"], "model_returned": resp["model_returned"],
                        "finish_reason": resp.get("finish_reason"), "usage": resp.get("usage", {}),
                        "cited_display_idx": cites, "cited_doc_ids": ids,
                        "target_cited": prompt["target_doc_id"] in ids,
                        "sentence_citations": rp.sentence_citations(resp["text"], len(order))})
        with lock:
            with outp.open("a") as fh:
                fh.write(json.dumps(rec) + "\n")
            state["n"] += 1
            state["err"] += "error" in rec
            n = state["n"]
            if n % step == 0 or n == total:
                rate = n / max(time.time() - t0, 1e-9)
                left = (total - n) / max(rate, 1e-9)
                eta = ("done" if n == total else f"about {left / 60:.0f} min left"
                       if left >= 90 else f"about {left:.0f}s left")
                msg = f"  {label}: {n}/{total}   {eta}"
                print(f"\r{msg}      " if tty else msg, end="" if tty else "\n", flush=True)

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        list(ex.map(work, cells))
    if tty:
        print()
    return state["err"]


def run_arm(corpus, condition, prompt_ids, outp, api_key, label, passes=3):
    """Run an arm, then re-run anything that failed, up to `passes` times. An arm is never
    analysed short: design/opengeo-test.md, 'Interrupted runs'."""
    for attempt in range(passes):
        errs = run_calls(corpus, condition, prompt_ids, outp, api_key,
                         label if attempt == 0 else f"{label} (retrying {errs} failed calls)")
        if errs == 0:
            return
    raise ToolError(
        f"Some calls kept failing after {passes} attempts. Nothing has been analysed, because "
        "a result built on missing runs looks confident and is not.\n"
        "    Re-run the same command to resume where it stopped. If it keeps failing, check "
        "your OpenRouter balance.")


# ---------------------------------------------------------------------- analysis ----
def _latest(rows):
    last = {}
    for r in rows:
        last[r["run_key"]] = r
    return [r for r in last.values() if not r.get("error")]


def control_gate(corpus, rows):
    """Share-weighted control rate per question. A question at or above CEILING has no room
    for an edit to show an improvement, so its treatment arm is not run."""
    w = engine_weights.weights(PANEL)
    out = {}
    for p in corpus["prompts"]:
        num = den = 0.0
        per = {}
        for m in PANEL:
            s = [r["target_cited"] for r in rows
                 if r["prompt_id"] == p["prompt_id"] and r["model"] == m
                 and r["condition"] == "control"]
            if s:
                per[m] = sum(s) / len(s)
                num += w.get(m, 0) * per[m]
                den += w.get(m, 0)
        out[p["prompt_id"]] = (num / den if den else None, per)
    return out


def _two_arm(c, t, rng, B=10000, P=20000):
    """Effect of the edit on one engine for one question: difference in citation rate,
    a percentile bootstrap interval, and a permutation p-value. The two arms are
    independent samples -- each repeat uses a fresh random document order -- so they are
    resampled independently. Bootstrap and permutation only, per CLAUDE.md."""
    import numpy as np
    d = t.mean() - c.mean()
    bc = c[rng.integers(0, len(c), (B, len(c)))].mean(1)
    bt = t[rng.integers(0, len(t), (B, len(t)))].mean(1)
    ci = np.percentile(bt - bc, [2.5, 97.5])
    pool = np.concatenate([c, t])
    perm = pool[np.argsort(rng.random((P, len(pool))), axis=1)]
    dp = perm[:, len(c):].mean(1) - perm[:, :len(c)].mean(1)
    p = float((np.abs(dp) >= abs(d) - 1e-12).mean())
    return float(d), (float(ci[0]), float(ci[1])), p, bt - bc


def _verdict(ci):
    if ci[0] > 0:
        return "raised"
    if ci[1] < 0:
        return "lowered"
    return "no detectable change"


def analyse(corpus, rows, gated_out):
    """The result, per question and per engine, with the guardrails applied."""
    import numpy as np
    from analyze import no_cite_report

    rows = _latest(rows)
    # Exclusion is decided on the arm where your edited page is present, not pooled across
    # arms: an engine that cites nothing only when nothing answers is abstaining, which is
    # correct behaviour, not a failure. METHODOLOGY.md 3, "the no-cite rule".
    nc = no_cite_report(rows)
    excluded = sorted(m for m, d in nc.items() if d["exclude"])
    engines = [m for m in PANEL if m not in excluded]
    w = engine_weights.weights(engines)
    rng = np.random.default_rng(20260926)

    questions = []
    for p in corpus["prompts"]:
        pid = p["prompt_id"]
        if pid in gated_out:
            questions.append({"prompt_id": pid, "question": p["question"], "skipped": True,
                              "control_rate": gated_out[pid]})
            continue
        per, draws = {}, {}
        for m in engines:
            sel = lambda cond: np.array([r["target_cited"] for r in rows
                                         if r["prompt_id"] == pid and r["model"] == m
                                         and r["condition"] == cond], float)
            c, t = sel("control"), sel("treatment")
            if not len(c) or not len(t):
                continue
            d, ci, pv, bs = _two_arm(c, t, rng)
            draws[m] = bs
            per[m] = {"control": float(c.mean()), "treatment": float(t.mean()),
                      "delta": d, "ci": ci, "p": pv, "n": (len(c), len(t)),
                      "no_room": c.mean() >= CEILING,
                      "saturated": t.mean() >= SATURATED}
        tw = sum(w[m] for m in per)
        pooled = sum(w[m] * per[m]["delta"] for m in per) / tw
        pbs = sum(w[m] * draws[m] for m in per) / tw
        pci = tuple(float(x) for x in np.percentile(pbs, [2.5, 97.5]))
        verdict = _verdict(pci)
        sign = 1 if pooled >= 0 else -1
        held = sum(1 for m in per if (per[m]["ci"][0] > 0 if sign > 0 else per[m]["ci"][1] < 0))
        questions.append({
            "prompt_id": pid, "question": p["question"], "skipped": False,
            "per_engine": per, "delta": pooled, "ci": pci, "verdict": verdict,
            "control": sum(w[m] * per[m]["control"] for m in per) / tw,
            "treatment": sum(w[m] * per[m]["treatment"] for m in per) / tw,
            "engines_held": held, "engines_total": len(per),
            "saturated_engines": [m for m in per if per[m]["saturated"]],
            "no_room_engines": [m for m in per if per[m]["no_room"]]})

    ran = [q for q in questions if not q["skipped"]]
    across = None
    if len(ran) >= 2:
        deltas = np.array([q["delta"] for q in ran])
        across = {"n": len(ran), "mean": float(deltas.mean()),
                  "raised": sum(q["verdict"] == "raised" for q in ran),
                  "lowered": sum(q["verdict"] == "lowered" for q in ran)}
        if len(ran) >= 5:
            # Resampling questions is what captures question-to-question variation -- the
            # thing a single question cannot tell you. Below 25 it is a rough estimate,
            # matching the floor OpenGEO holds its own published rounds to.
            bs = deltas[rng.integers(0, len(ran), (10000, len(ran)))].mean(1)
            across["ci"] = tuple(float(x) for x in np.percentile(bs, [2.5, 97.5]))
            across["rough"] = len(ran) < 25

    return {"questions": questions, "across": across, "engines": engines,
            "excluded": excluded, "no_cite": nc,
            "coverage": engine_weights.coverage(engines)}


# ------------------------------------------------------------------------ output ----
NAME = {m: n for n, (_, m) in engine_weights.ENGINES.items() if m}


def _pts(v):
    """Signed percentage points with a true minus sign; a change that rounds to zero is
    shown as 0 rather than a signed zero, which reads as a direction it does not have."""
    n = round(v * 100)
    return "0" if n == 0 else f"{'+' if n > 0 else chr(0x2212)}{abs(n)}"


def _pct(v):
    return f"{v * 100:.0f}%"


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


# Palette: one hue, two shades, validated with the dataviz skill's validator in both modes
# (ordinal ramp: monotone lightness, visible step gap, light end clears the surface).
# "Before" recedes and "after" carries the result -- which in dark mode means the lighter
# step, since light is what stands out on a dark surface.
_SVG_STYLE = """
.c{--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--grid:#e1e0d9;
   --base:#c3c2b7;--before:#86b6ef;--after:#1c5cab}
@media (prefers-color-scheme:dark){.c{--surface:#1a1a19;--ink:#ffffff;--ink2:#c3c2b7;
   --muted:#898781;--grid:#2c2c2a;--base:#383835;--before:#1c5cab;--after:#86b6ef}}
.c{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
.bg{fill:var(--surface)} .t1{fill:var(--ink)} .t2{fill:var(--ink2)} .tm{fill:var(--muted)}
.grid{stroke:var(--grid);stroke-width:1} .base{stroke:var(--base);stroke-width:1}
.before{fill:var(--before)} .after{fill:var(--after)}
.link{stroke:var(--before);stroke-width:2;stroke-linecap:round}
.ring{stroke:var(--surface);stroke-width:2}
.num{font-variant-numeric:tabular-nums}
"""


def write_chart(q, path):
    """Before -> after per engine: a dumbbell, the form for 'before and after per item'.
    Each row's change and interval sit in the right-hand column; the before and after
    values ride the tooltip and the report's table, and are labelled directly only on the
    pooled row, which is the headline."""
    per = q["per_engine"]
    rows = [(NAME.get(m, m), m.split("/")[-1], per[m], False) for m in PANEL if m in per]
    rows.append(("All engines", "share-weighted", {"control": q["control"],
                 "treatment": q["treatment"], "delta": q["delta"], "ci": q["ci"],
                 "saturated": False, "no_room": False}, True))
    # RB leaves room for the pooled row's endpoint label beside the change column even
    # when the edited page reaches 100%, which edits that add a missing fact often do
    W, LB, RB, rowH, top = 760, 176, 172, 42, 96
    PL, PR = LB, W - RB
    H = top + len(rows) * rowH + 70
    x = lambda v: PL + v * (PR - PL)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
         f'height="{H}" role="img" class="c" aria-label="Citation rate before and after '
         f'your edit, per engine. {_esc(q["question"])}"><style>{_SVG_STYLE}</style>',
         f'<rect class="bg" width="{W}" height="{H}" rx="8"/>',
         f'<text class="t1" x="24" y="34" font-size="17" font-weight="600">'
         f'How often AI answers cite your page, before and after your edit</text>',
         f'<text class="t2" x="24" y="56" font-size="13">{_esc(q["question"])}</text>']
    # legend: two states, so a legend is required; identity never by colour alone
    lx = 24
    for cls, label in (("before", "Before"), ("after", "After your edit")):
        o.append(f'<circle class="{cls} ring" cx="{lx + 5}" cy="76" r="5"/>'
                 f'<text class="t2" x="{lx + 16}" y="80" font-size="12">{label}</text>')
        lx += 22 + len(label) * 7
    # hairline grid, solid, recessive
    for t in (0, 0.25, 0.5, 0.75, 1.0):
        o.append(f'<line class="grid" x1="{x(t):.1f}" y1="{top - 10}" x2="{x(t):.1f}" '
                 f'y2="{top + len(rows) * rowH - 6}"/>')
        o.append(f'<text class="tm num" x="{x(t):.1f}" y="{top + len(rows) * rowH + 12}" '
                 f'font-size="11" text-anchor="middle">{int(t * 100)}%</text>')
    notes = set()
    for i, (name, sub, s, pooled) in enumerate(rows):
        y = top + i * rowH + rowH / 2 - 4
        if pooled:
            o.append(f'<line class="base" x1="0" y1="{y - rowH / 2 + 2:.1f}" x2="{W}" '
                     f'y2="{y - rowH / 2 + 2:.1f}"/>')
        tip = (f"{name}: {_pct(s['control'])} before, {_pct(s['treatment'])} after\n"
               f"change {_pts(s['delta'])} points, 95% CI {_pts(s['ci'][0])} to "
               f"{_pts(s['ci'][1])}")
        mark = ""
        if s.get("saturated"):
            mark = " ^"
            notes.add("^ cited in almost every run after the edit, so the true change may be "
                      "larger: read it as a lower bound")
        if s.get("no_room"):
            mark += " *"
            notes.add("* already cited almost every time before the edit: little room to rise")
        o.append(f'<g><title>{_esc(tip)}</title>'
                 f'<rect x="0" y="{y - rowH / 2 + 4:.1f}" width="{W}" height="{rowH - 2}" '
                 f'fill="transparent"/>')
        o.append(f'<text class="t1" x="24" y="{y + 1:.1f}" font-size="14" '
                 f'font-weight="{600 if pooled else 500}">{_esc(name)}</text>'
                 f'<text class="tm" x="24" y="{y + 15:.1f}" font-size="10.5">{_esc(sub)}</text>')
        x0, x1 = x(s["control"]), x(s["treatment"])
        o.append(f'<line class="link" x1="{x0:.1f}" y1="{y:.1f}" x2="{x1:.1f}" y2="{y:.1f}"/>')
        r = 6 if pooled else 5
        if pooled:   # the headline row is the one row labelled directly
            d = lambda cx: (f'M {cx:.1f} {y - r - 1:.1f} L {cx + r + 1:.1f} {y:.1f} '
                            f'L {cx:.1f} {y + r + 1:.1f} L {cx - r - 1:.1f} {y:.1f} Z')
            o.append(f'<path class="before ring" d="{d(x0)}"/><path class="after ring" '
                     f'd="{d(x1)}"/>')
            lo, hi = sorted((x0, x1))
            o.append(f'<text class="t2 num" x="{lo - 12:.1f}" y="{y + 4:.1f}" font-size="12" '
                     f'text-anchor="end">{_pct(min(s["control"], s["treatment"]))}</text>'
                     f'<text class="t1 num" x="{hi + 12:.1f}" y="{y + 4:.1f}" font-size="12" '
                     f'font-weight="600">{_pct(max(s["control"], s["treatment"]))}</text>')
        else:
            o.append(f'<circle class="before ring" cx="{x0:.1f}" cy="{y:.1f}" r="{r}"/>'
                     f'<circle class="after ring" cx="{x1:.1f}" cy="{y:.1f}" r="{r}"/>')
        o.append(f'<text class="t1 num" x="{W - 24}" y="{y + 1:.1f}" font-size="14" '
                 f'font-weight="{600 if pooled else 500}" text-anchor="end">'
                 f'{_pts(s["delta"])} pts{mark}</text>'
                 f'<text class="tm num" x="{W - 24}" y="{y + 15:.1f}" font-size="10.5" '
                 f'text-anchor="end">95% CI {_pts(s["ci"][0])} to {_pts(s["ci"][1])}</text></g>')
    fy = top + len(rows) * rowH + 36
    for n in sorted(notes):
        o.append(f'<text class="tm" x="24" y="{fy}" font-size="11">{_esc(n)}</text>')
        fy += 15
    o.append("</svg>")
    path.write_text("\n".join(o) + "\n")


def _bar(c, t, width=28):
    """A text dumbbell: o before, * after, joined by a rule. After is drawn last, so a
    change of zero shows one mark rather than two overlapping ones."""
    a, b = round(c * (width - 1)), round(t * (width - 1))
    row = [" "] * width
    for i in range(min(a, b), max(a, b) + 1):
        row[i] = "━"
    row[a], row[b] = "○", "●"
    return "".join(row)


def _headline(q):
    if q["verdict"] == "raised":
        return f"Your edit raised citation from {_pct(q['control'])} to {_pct(q['treatment'])}"
    if q["verdict"] == "lowered":
        return (f"Your edit LOWERED citation from {_pct(q['control'])} to "
                f"{_pct(q['treatment'])}")
    return (f"No detectable change: {_pct(q['control'])} before, {_pct(q['treatment'])} after")


def _engines(k):
    return f"{k} engine" if k == 1 else f"{k} engines"


def _meaning(res, q, flags, n_questions):
    """The caveats, written as advice. Two appear on every result, because they are the two
    ways this tool's output is most likely to be over-read (design/opengeo-test.md)."""
    out = []
    if q["verdict"] == "raised":
        out.append("For this question, against these competitors, your edit made AI answers "
                   "more likely to cite your page.")
    elif q["verdict"] == "lowered":
        out.append("For this question, against these competitors, your edit made AI answers "
                   "LESS likely to cite your page.")
    else:
        out.append("The interval includes zero: this test could not tell your edit apart "
                   "from no change. That is a real result, not a failed test.")
    if n_questions == 1:
        out.append("One question is one question. About 1 in 20 tests shows a change by "
                   "chance alone, so test 3-5 questions your customers actually ask before "
                   "rewriting your site.")
    if q["saturated_engines"]:
        out.append(f"{_engines(len(q['saturated_engines']))} cited your edited page in almost "
                   "every run, so the true change there may be larger than shown.")
    if q["no_room_engines"]:
        out.append(f"{_engines(len(q['no_room_engines']))} already cited your current page "
                   "almost every time, leaving little room to show an improvement.")
    if res["excluded"]:
        names = ", ".join(NAME.get(m, m) for m in res["excluded"])
        out.append(f"Left out of the pooled figure: {names} -- it cited nothing in too many "
                   "answers even when your edited page was present, which is a failure to "
                   "follow the instructions, not a visibility signal.")
    if flags.get("allow_length_change"):
        out.append("--allow-length-change was used: your edit changed the length. OpenGEO "
                   "measured doubling a page's length at +0.004, so length alone is not "
                   "expected to explain this.")
    out.append("This measures what happens once an AI engine has your page. It does not tell "
               "you whether an engine will find your page in the first place.")
    return out


def print_result(res, flags):
    ran = [q for q in res["questions"] if not q["skipped"]]
    for q in res["questions"]:
        print(f"\n{'=' * 78}\n{q['question']}\n{'=' * 78}")
        if q["skipped"]:
            print(f"  Not tested: your current page is already cited {_pct(q['control_rate'])} "
                  "of the time,\n  so there is no room for an edit to show an improvement. "
                  "Try a question where\n  your page is not the obvious answer yet.")
            continue
        print(f"\nRESULT  {_headline(q)}")
        print(f"        {_pts(q['delta'])} points, 95% CI {_pts(q['ci'][0])} to "
              f"{_pts(q['ci'][1])}, held on {q['engines_held']} of {q['engines_total']} "
              "engines\n")
        for m in PANEL:
            if m not in q["per_engine"]:
                continue
            s = q["per_engine"][m]
            tag = ("  ^ lower bound" if s["saturated"] else "") + ("  * no room" if s["no_room"] else "")
            print(f"  {NAME.get(m, m):<9}{_pct(s['control']):>5} {_bar(s['control'], s['treatment'])} "
                  f"{_pct(s['treatment']):<5}{_pts(s['delta']):>5} pts  "
                  f"({_pts(s['ci'][0])} to {_pts(s['ci'][1])}){tag}")
        print("\nWhat this means")
        for line in _meaning(res, q, flags, len(res["questions"])):
            words, cur = line.split(), ""
            for w in words:
                if len(cur) + len(w) > 74:
                    print(f"  {cur}")
                    cur = w
                else:
                    cur = f"{cur} {w}".strip()
            print(f"  {cur}\n")
    a = res["across"]
    if a:
        print(f"{'=' * 78}\nACROSS {a['n']} QUESTIONS\n{'=' * 78}")
        print(f"  Your edit raised citation on {a['raised']} of {a['n']} questions"
              + (f" and lowered it on {a['lowered']}" if a["lowered"] else "") + ".")
        print(f"  Average change: {_pts(a['mean'])} points"
              + (f", 95% CI {_pts(a['ci'][0])} to {_pts(a['ci'][1])}" if "ci" in a else ""))
        if a.get("rough"):
            print(f"  With {a['n']} questions this is a rough estimate for questions like these;"
                  " OpenGEO's own\n  published rounds use at least 25 before calling a result "
                  "general.")


def write_report(res, corpus, folder, flags, started):
    L = [f"# OpenGEO test — {res['questions'][0]['question']}", "",
         f"Run {started} with `opengeo.py` {TOOL_VERSION}. "
         f"Corpus `{corpus['corpus_version']}`. {RUNS} runs per version per engine, "
         f"temperature {TEMPERATURE}, document order randomised per run.", "",
         f"Engines: {', '.join(NAME.get(m, m) for m in res['engines'])} — "
         f"{res['coverage']:.1%} of measured AI-assistant traffic.", ""]
    for q in res["questions"]:
        L += [f"## {q['question']}", ""]
        if q["skipped"]:
            L += [f"**Not tested.** Your current page was already cited {_pct(q['control_rate'])} "
                  "of the time, which leaves no room for an edit to show an improvement.", ""]
            continue
        L += [f"**{_headline(q)}** — {_pts(q['delta'])} points, 95% CI {_pts(q['ci'][0])} to "
              f"{_pts(q['ci'][1])}, held on {q['engines_held']} of {q['engines_total']} "
              "engines.", "",
              "| Engine | Before | After | Change | 95% CI | p | Note |",
              "|---|---|---|---|---|---|---|"]
        for m in PANEL:
            if m not in q["per_engine"]:
                continue
            s = q["per_engine"][m]
            note = "; ".join(n for n, on in (("lower bound", s["saturated"]),
                                             ("no room", s["no_room"])) if on)
            L.append(f"| {NAME.get(m, m)} | {_pct(s['control'])} | {_pct(s['treatment'])} | "
                     f"{_pts(s['delta'])} | {_pts(s['ci'][0])} to {_pts(s['ci'][1])} | "
                     f"{s['p']:.3f} | {note} |")
        L += [f"| **All engines** (share-weighted) | {_pct(q['control'])} | "
              f"{_pct(q['treatment'])} | **{_pts(q['delta'])}** | {_pts(q['ci'][0])} to "
              f"{_pts(q['ci'][1])} | | |", "",
              "What this means:", ""] + [f"- {m}" for m in _meaning(res, q, flags,
                                                                   len(res["questions"]))] + [""]
    if res["across"]:
        a = res["across"]
        L += ["## Across questions", "",
              f"Raised on {a['raised']} of {a['n']}, lowered on {a['lowered']}. Mean change "
              f"{_pts(a['mean'])} points"
              + (f", 95% CI {_pts(a['ci'][0])} to {_pts(a['ci'][1])}" if "ci" in a else "")
              + ("" if not a.get("rough") else ". With fewer than 25 questions this is a rough "
                 "estimate, not a general rule."), ""]
    L += ["## Method", "",
          "A paired, controlled experiment. Your page appears twice — as it is and as edited — "
          "each time among the same excerpts of your competitors' pages. Only your excerpt "
          "differs between the two versions, so a difference in citation is caused by your "
          "edit. Intervals are percentile bootstraps over runs; p-values are permutation "
          "tests. No distributional assumptions.", "",
          "Every default is argued for, with its evidence, in `design/opengeo-test.md`.", "",
          "## Files", "",
          "- `runs.jsonl` — every raw model response",
          "- `corpus.json` — the exact text of every document tested",
          "- `manifest.json` — versions, settings and flags, enough to re-run this test",
          "- `chart*.svg` — before and after, per engine", ""]
    (folder / "report.md").write_text("\n".join(L))


def write_manifest(res, corpus, folder, flags, started, rows):
    """Enough to re-run the identical test. Built from explicit fields only, never from the
    environment, so the API key cannot end up in it."""
    returned = sorted({r.get("model_returned") for r in _latest(rows) if r.get("model_returned")})
    (folder / "manifest.json").write_text(json.dumps({
        "tool": "opengeo.py", "tool_version": TOOL_VERSION, "harness": "run_pilot.py",
        "started_utc": started, "corpus_version": corpus["corpus_version"],
        "corpus_sha256": corpus["corpus_sha256"],
        "settings": {"runs_per_version": RUNS, "temperature": TEMPERATURE,
                     "length_tolerance_words": LENGTH_TOLERANCE, "ceiling": CEILING,
                     "saturated": SATURATED, "panel": PANEL},
        "flags": {k: v for k, v in flags.items() if v},
        "engines_analysed": res["engines"], "engines_excluded": res["excluded"],
        "models_returned": returned, "edit_region": corpus["edit_region"],
        "questions": [p["question"] for p in corpus["prompts"]],
    }, indent=2) + "\n")


# ----------------------------------------------------------------------- command ----
def cmd_test(args):
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    flags = {"allow_length_change": args.allow_length_change}
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key and not args.dry_run:
        raise ToolError("OPENROUTER_API_KEY is not set.\n"
                        "    export OPENROUTER_API_KEY=sk-or-...   (from openrouter.ai/keys)\n"
                        "    It is read from the environment only, never written anywhere.")

    print("Reading pages...")
    corpus = build_corpus(args.question, args.page, args.edit, args.against)
    blocks, warns, oks = preflight(corpus, len(args.against), args.allow_length_change)
    print("\nChecks")
    for m in oks:
        print(f"  ✓ {m}")
    for m in warns:
        print(f"  ! {m}")
    for m in blocks:
        print(f"  ✗ {m}")
    if blocks:
        raise ToolError("Stopped before spending anything: fix the check marked ✗ above.")

    calls, low, high = estimate_cost(corpus)
    nq = corpus["n_prompts"]
    print(f"\nThis test makes {calls:,} calls ({nq} question{'' if nq == 1 else 's'} x 2 versions x "
          f"{len(PANEL)} engines x {RUNS} runs).")
    print(f"Estimated cost: ${low:.2f} to ${high:.2f} on your OpenRouter account.")
    if args.dry_run:
        print("\nDry run: nothing was sent.")
        return 0
    if not args.yes and input("Continue? [y/N] ").strip().lower() not in ("y", "yes"):
        print("Nothing was sent.")
        return 0

    folder = pathlib.Path(args.out) / f"{slugify(args.question[0])}-{corpus['corpus_sha256'][:8]}"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "corpus.json").write_text(json.dumps(corpus, indent=2, ensure_ascii=False) + "\n")
    runs = folder / "runs.jsonl"
    all_q = [p["prompt_id"] for p in corpus["prompts"]]

    # Phase 1: your current page only. It is also the gate -- a page that is already cited
    # almost every time has no room to show an improvement, and running the edited version
    # for it would spend money on an answer that cannot be informative.
    print("\nTesting your current page...")
    run_arm(corpus, "control", all_q, runs, key, "current page")
    gate = control_gate(corpus, _latest(_load_rows(runs)))
    gated_out = {pid: rate for pid, (rate, _) in gate.items() if rate is not None and rate >= CEILING}
    go = [pid for pid in all_q if pid not in gated_out]
    for pid, rate in gated_out.items():
        print(f"  {pid}: current page already cited {_pct(rate)} of the time -- no room to "
              "improve, so its edited version is not run.")
    if go:
        print("\nTesting your edited page...")
        run_arm(corpus, "treatment", go, runs, key, "edited page")

    rows = _load_rows(runs)
    res = analyse(corpus, rows, gated_out)
    print_result(res, flags)
    for q in res["questions"]:
        if not q["skipped"]:
            name = "chart.svg" if len(res["questions"]) == 1 else f"chart-{q['prompt_id']}.svg"
            write_chart(q, folder / name)
    write_report(res, corpus, folder, flags, started)
    write_manifest(res, corpus, folder, flags, started, rows)
    print(f"\nFull results: {folder}/")
    print("  report.md, chart.svg, runs.jsonl (every raw response), corpus.json, manifest.json")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="opengeo.py",
        description="Test whether a change to your page makes AI engines more likely to cite "
                    "it. A measurement, not advice: design/opengeo-test.md.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("test", help="run a paired test of your edit against your competitors")
    t.add_argument("--question", action="append", required=True,
                   help="a question your customers ask; repeat for 3-5 of them")
    t.add_argument("--page", required=True, help="your page as it is now (URL or file)")
    t.add_argument("--edit", required=True, help="your page with the change (file)")
    t.add_argument("--against", nargs="+", required=True, metavar="PAGE",
                   help=f"competitor pages (URL or file), {MIN_COMPETITORS}+ needed, "
                        f"{RECOMMENDED_COMPETITORS}-5 recommended")
    t.add_argument("--allow-length-change", action="store_true",
                   help="permit an edit that changes the length by more than "
                        f"{LENGTH_TOLERANCE} words; recorded in the report")
    t.add_argument("--dry-run", action="store_true", help="checks and cost only; send nothing")
    t.add_argument("--yes", action="store_true", help="skip the cost confirmation")
    t.add_argument("--out", default="opengeo-results", help="where results are written")
    args = ap.parse_args(argv)
    try:
        return cmd_test(args)
    except ToolError as e:
        # stdout is block-buffered when piped -- into a log, or into the Claude skill -- and
        # stderr is not, so without this flush the error prints above the checks it refers to
        sys.stdout.flush()
        print(f"\n{e}\n", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        sys.stdout.flush()
        print("\nStopped. Re-run the same command to pick up where it left off.",
              file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
