#!/usr/bin/env python3
"""
OpenGEO -- the story page: what the experiment found, in plain language, for the people
`opengeo test` is for. Built from the `story` block of results/findings.json and written
by build_findings.py to docs/index.html, beside the technical findings page.

Same rules as the findings page (design/story-page.md). Every figure is read from the
ledger; prose carries {placeholders}; sentences a reader would take as fact carry named
assertions. The worked examples are quoted from the committed raw results, and their
counts are recomputed from them at every build -- if the ledger and the data disagree,
the build stops.

Charts are HTML rather than SVG so their labels stay legible at phone width: positions
are percentages of the plot, text is real text. Standard library only.
"""
import base64
import json
import re

import build_findings as bf

HERE = bf.HERE
esc, fmt = bf.esc, bf.fmt


# ------------------------------------------------------------------ numbers for plain readers
def _nd(v):
    """Decimals for an effect in points: none from ten up, one below, so an interval such
    as +0.4 to +7.5 never rounds into "0 to +8" and looks as if it included zero."""
    return 0 if abs(v * 100) >= 10 else 1


def spts(v, nd):
    return bf.signed(v * 100, nd)


def sci(ci, nd):
    return f"{spts(ci[0], nd)} to {spts(ci[1], nd)}"


def context(L):
    A, P, _ = bf.contexts(L)
    c = dict(P)
    for a in ("facts", "heldout", "stuffing", "length", "presentation"):
        pool = A[a]["data"]["pooled"]
        nd = _nd(pool["delta"])
        c[f"s_{a}_pts"], c[f"s_{a}_ci"] = spts(pool["delta"], nd), sci(pool["ci"], nd)
    f = A["facts"]["data"]["pooled"]
    c["s_facts_before"], c["s_facts_after"] = bf.pct(f["control"]), bf.pct(f["treatment"])
    c["chatgpt_model"] = next(e["short"] for e in L["engines"] if e["name"] == "ChatGPT")
    return A, c


# ------------------------------------------------------------------ checks
def prose(L):
    """Every story string a reader sees, for the typed-number scan."""
    S = L.get("story")
    if not S:
        return
    for k in ("headline", "standfirst", "footer"):
        yield f"story.{k}", S[k]

    def walk(o, where):
        if isinstance(o, str):
            yield where, o
        elif isinstance(o, list):
            for i, v in enumerate(o):
                yield from walk(v, f"{where}[{i}]")
        elif isinstance(o, dict):
            for k, v in o.items():
                if k not in ("asserts", "cases", "corpus", "runs", "demo", "command", "links", "alias"):
                    yield from walk(v, f"{where}.{k}")
    for sec in ("hero", "example", "all", "rest", "more", "limits", "test", "method"):
        yield from walk(S.get(sec, {}), f"story.{sec}")


def load_example(L):
    """The worked examples as tested: texts from the corpus, answers and counts from the
    raw runs, deduplicated by run key the way analyze.py reads them."""
    ex = L["story"]["example"]
    corpus = json.loads((HERE / ex["corpus"]).read_text())
    want = {c["prompt_id"] for c in ex["cases"]}
    rows = {}
    with open(HERE / ex["runs"]) as fh:
        for line in fh:
            if not any(f'"{pid}"' in line for pid in want):
                continue
            r = json.loads(line)
            if r.get("prompt_id") not in want:
                continue
            ok = "target_cited" in r and bool(r.get("response_text")) and not r.get("error")
            if r["run_key"] not in rows or (ok and not rows[r["run_key"]][1]):
                rows[r["run_key"]] = (r, ok)
    cases = []
    for c in ex["cases"]:
        p = next(p for p in corpus["prompts"] if p["prompt_id"] == c["prompt_id"])
        docs = {d["doc_id"]: d for d in corpus["documents"] if d["prompt_id"] == c["prompt_id"]}
        t = docs[p["target_doc_id"]]
        counts = {}
        for (r, ok) in rows.values():
            if ok and r["prompt_id"] == c["prompt_id"]:
                k = counts.setdefault(r["model"], {"control": [0, 0], "treatment": [0, 0]})[r["condition"]]
                k[0] += bool(r["target_cited"])
                k[1] += 1
        answers = {}
        for side in ("before", "after"):
            r, ok = rows.get(c[f"answer_{side}"], (None, False))
            answers[side] = {"ok": ok, "text": r["response_text"] if ok else "",
                             "cited": bool(r and r.get("target_cited")),
                             "slot": (r["target_slot"] + 1) if r else None,
                             "model": r["model"] if r else None}
        cases.append({**c, "question": p.get("question") or p.get("text"),
                      "vague": t["variants"]["control"], "specific": t["variants"]["treatment"],
                      "counts": counts, "answers": answers})
    return cases


def check(L):
    """Errors that stop the build: a story assertion that no longer holds, or a worked
    example whose counts, answers or claim of typicality the raw data contradicts."""
    S = L.get("story")
    if not S:
        return [], None
    errors = []
    A = {f["alias"]: f for f in L["findings"]}
    for sec in ("all", "rest"):
        for name in S[sec].get("asserts", []):
            alias, fn = name.split(":")
            if fn not in bf.ASSERTS:
                errors.append(f"story.{sec}: unknown assertion '{fn}'")
            elif not bf.ASSERTS[fn](A[alias], A):
                errors.append(f"story.{sec}: assertion no longer holds -- {name}")
    cases = load_example(L)
    w = {e["model"]: e["share"] for e in L["engines"]}
    facts = A["facts"]["data"]["pooled"]["delta"]
    for c in cases:
        for m, (ctl, trt, n) in c["cited"].items():
            got = c["counts"].get(m, {"control": [0, 0], "treatment": [0, 0]})
            if got["control"] != [ctl, n] or got["treatment"] != [trt, n]:
                errors.append(f"story example {c['key']}: {m} is {got} in the data, {[ctl, trt, n]} in the ledger")
        if not (c["answers"]["before"]["ok"] and not c["answers"]["before"]["cited"]):
            errors.append(f"story example {c['key']}: the 'before' answer must exist and not cite the page")
        if not (c["answers"]["after"]["ok"] and c["answers"]["after"]["cited"]):
            errors.append(f"story example {c['key']}: the 'after' answer must exist and cite the page")
        # The page says both examples sit close to the average; hold it to that.
        d = sum(w[m] * (trt - ctl) / n for m, (ctl, trt, n) in c["cited"].items()) / sum(w.values())
        if abs(d - facts) > 0.05:
            errors.append(f"story example {c['key']}: effect {d:+.3f} is not close to the average {facts:+.3f}")
    return errors, cases


# ------------------------------------------------------------------ pieces
FIGURE = re.compile(r"\$?\d+(?:[.,]\d+)*(?:[–-]\d+(?:[.,]\d+)*)?%?(?:/month)?")
CITE = re.compile(r"\[(\d{1,2})\]")


def mark_figures(text):
    return FIGURE.sub(lambda m: f"<mark>{m.group(0)}</mark>", esc(text))


def mark_cites(text, slot):
    return CITE.sub(lambda m: (f'<span class="cite you" title="the page under test">[{m.group(1)}]</span>'
                               if int(m.group(1)) == slot else f'<span class="cite">[{m.group(1)}]</span>'),
                    esc(text))


def numbers_table(head, rows):
    return ('<details class="numbers"><summary>The numbers</summary><div class="scroll"><table>'
            "<thead><tr>" + "".join(f"<th>{esc(h)}</th>" for h in head) + "</tr></thead><tbody>"
            + "".join("<tr>" + "".join(f"<td>{esc(v)}</td>" for v in r) + "</tr>" for r in rows)
            + "</tbody></table></div></details>")


def dumbbell(rows, scale_label):
    """Before -> after per row, one hue in two steps. rows: (name, sub, before, after, tip,
    right_label, pooled)."""
    out = ['<div class="db">']
    for name, sub, a, b, tip, right, pooled in rows:
        lo, hi = sorted((a, b))
        out.append(
            f'<div class="db-row{" pooled" if pooled else ""}" tabindex="0" data-tip="{esc(tip)}">'
            f'<div class="db-name"><b>{esc(name)}</b><span>{esc(sub)}</span></div>'
            f'<div class="db-plot"><span class="db-link" style="left:{lo * 100:.2f}%;width:{(hi - lo) * 100:.2f}%"></span>'
            f'<span class="dot before" style="left:{a * 100:.2f}%"></span>'
            f'<span class="dot after" style="left:{b * 100:.2f}%"></span></div>'
            f'<div class="db-val">{right}</div></div>')
    ticks = "".join(f'<span style="left:{t}%">{t}%</span>' for t in (0, 25, 50, 75, 100))
    out.append(f'<div class="db-axis"><div></div><div class="ticks">{ticks}</div><div class="unit">{esc(scale_label)}</div></div></div>')
    return "".join(out)


def legend_before_after(before, after):
    return (f'<div class="legend"><span><i class="key before"></i>{esc(before)}</span>'
            f'<span><i class="key after"></i>{esc(after)}</span></div>')


def effects(rows, c):
    """Every tested change on one scale. Emphasis: the one result that is the story in the
    accent, the rest in gray -- 'one tall bar and a row of near-zero ones'."""
    lo, hi = -10, 60
    x = lambda v: (v * 100 - lo) / (hi - lo) * 100
    out = ['<div class="fx">']
    for r in rows:
        P = r["pooled"]
        nd = _nd(P["delta"])
        tip = f'{r["label"]}\n{spts(P["delta"], nd)} points, 95% interval {sci(P["ci"], nd)}\n{fmt(r["tag"], c)}'
        out.append(
            f'<div class="fx-row{" em" if r.get("emphasis") else ""}" tabindex="0" data-tip="{esc(tip)}">'
            f'<div class="fx-name"><b>{esc(r["label"])}</b><span>{esc(fmt(r["tag"], c))}</span></div>'
            f'<div class="fx-plot"><span class="zero" style="left:{x(0):.2f}%"></span>'
            f'<span class="ci" style="left:{x(P["ci"][0]):.2f}%;width:{x(P["ci"][1]) - x(P["ci"][0]):.2f}%"></span>'
            f'<span class="pt" style="left:{x(P["delta"]):.2f}%"></span>'
            f'<span class="val" style="left:{x(P["ci"][1]):.2f}%">{spts(P["delta"], nd)}</span></div></div>')
    ticks = "".join(f'<span style="left:{x(t / 100):.2f}%">{"0" if t == 0 else bf.signed(t, 0)}</span>'
                    for t in range(lo, hi + 1, 10))
    out.append(f'<div class="fx-axis"><div></div><div class="ticks">{ticks}</div></div>'
               '<p class="axis-label">points</p></div>')
    return "".join(out)


def pipeline(S, c):
    lim = S["limits"]
    steps = []
    for i, s in enumerate(lim["steps"]):
        cls = " measured" if i == lim["measured"] else (" unmeasured" if i == lim["measured"] - 1 else "")
        tag = (f'<span class="tag">{esc(lim["measured_label"])}</span>' if i == lim["measured"] else
               f'<span class="tag">{esc(lim["unmeasured_label"])}</span>' if i == lim["measured"] - 1 else "")
        steps.append(f'<li class="step{cls}">{tag}<span class="n">{i + 1}</span>{esc(s)}</li>')
    return f'<ol class="pipe">{"".join(steps)}</ol>'


def demo(S, c):
    t = S["test"]
    folder = HERE / t["demo"]
    report = (folder / "report.md").read_text()
    m = re.search(r"^\*\*(.+?)\*\* — (.+?)\.$", report, re.M)
    verdict = f"{m.group(1)} — {m.group(2)}" if m else ""
    svg = base64.b64encode((folder / "chart.svg").read_bytes()).decode()
    return (f'<figure class="demo"><div class="term"><div class="bar"><i></i><i></i><i></i></div>'
            f'<pre><span class="pr">$</span> {esc(t["command"])}\n\n<span class="ok">RESULT</span>  {esc(verdict)}</pre></div>'
            f'<img src="data:image/svg+xml;base64,{svg}" alt="{esc("Before and after, per engine: " + verdict)}" loading="lazy">'
            f'<figcaption>{fmt(t["demo_caption"], c)}</figcaption></figure>')


# ------------------------------------------------------------------ the README's chart
SVG_THEMES = {
    "light": {"bg": "#fffdf8", "ink": "#191610", "muted": "#7c746a", "line": "#e0d9cb", "line2": "#cec5b3",
              "accent": "#a86c14", "gray": "#8a8276"},
    "dark": {"bg": "#1e1b15", "ink": "#f0ebe0", "muted": "#948b7d", "line": "#302b22", "line2": "#433c30",
             "accent": "#d9a04a", "gray": "#7e776c"},
}


def effects_svg(L, mode):
    """The story's one-scale chart as a standalone SVG for the README, one per colour mode
    (GitHub picks with <picture>). An image can't load the page's fonts or variables, so
    colours are literal and the type is the system's."""
    A, c = context(L)
    T = SVG_THEMES[mode]
    rows = [{**r, "pooled": A[r["alias"]]["data"]["pooled"]} for r in L["story"]["rest"]["rows"]]

    def lines(label, width=32):
        """A label too long for the column splits at the comma nearest its middle."""
        if len(label) <= width or "," not in label:
            return [label]
        cuts = [i for i, ch in enumerate(label) if ch == ","]
        k = min(cuts, key=lambda i: abs(i - len(label) / 2))
        return [label[:k + 1], label[k + 1:].strip()]

    W, LB, top, rowH = 760, 300, 58, 54
    heights = [rowH + 16 * (len(lines(r["label"])) - 1) for r in rows]
    lo, hi, PL, PR = -10, 60, LB + 14, W - 64
    H = top + sum(heights) + 40
    x = lambda v: PL + (v * 100 - lo) / (hi - lo) * (PR - PL)
    sans = 'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif"'
    mono = 'font-family="SFMono-Regular,Menlo,Consolas,monospace"'
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="What each tested change did to how often AI answers cited a page, in percentage points">',
         f'<rect width="{W}" height="{H}" rx="8" fill="{T["bg"]}"/>',
         f'<text x="20" y="32" {sans} font-size="16" font-weight="600" fill="{T["ink"]}">'
         f'What each change did to how often AI answers cited a page</text>'
         f'<text x="20" y="49" {mono} font-size="10.5" fill="{T["muted"]}">'
         f'change in percentage points, with 95% intervals</text>']
    for t in range(lo, hi + 1, 10):
        X = x(t / 100)
        o.append(f'<line x1="{X:.1f}" y1="{top - 2}" x2="{X:.1f}" y2="{H - 34}" stroke="{T["line2"] if t == 0 else T["line"]}" '
                 f'stroke-width="{1.5 if t == 0 else 1}"/>'
                 f'<text x="{X:.1f}" y="{H - 16}" {mono} font-size="11" text-anchor="middle" fill="{T["muted"]}">'
                 f'{"0" if t == 0 else bf.signed(t, 0)}</text>')
    y0 = top
    for r, h in zip(rows, heights):
        P, y = r["pooled"], y0 + h / 2
        y0 += h
        col = T["accent"] if r.get("emphasis") else T["gray"]
        nd = _nd(P["delta"])
        ls = lines(r["label"])
        ty = y - 2 - 8 * (len(ls) - 1)
        label = "".join(f'<tspan x="20" dy="{0 if j == 0 else 16}">{esc(s)}</tspan>' for j, s in enumerate(ls))
        o.append(f'<text x="20" y="{ty:.1f}" {sans} font-size="14" font-weight="600" fill="{T["ink"]}">{label}</text>'
                 f'<text x="20" y="{ty + 16 * len(ls) + 1:.1f}" {mono} font-size="10.5" fill="{T["muted"]}">{esc(fmt(r["tag"], c))}</text>'
                 f'<line x1="{x(P["ci"][0]):.1f}" y1="{y:.1f}" x2="{x(P["ci"][1]):.1f}" y2="{y:.1f}" stroke="{col}" '
                 f'stroke-width="2.5" stroke-linecap="round"/>'
                 f'<circle cx="{x(P["delta"]):.1f}" cy="{y:.1f}" r="7" fill="{col}" stroke="{T["bg"]}" stroke-width="2"/>'
                 f'<text x="{x(P["ci"][1]) + 10:.1f}" y="{y + 4.5:.1f}" {mono} font-size="13" font-weight="600" '
                 f'fill="{T["ink"]}">{spts(P["delta"], nd)}</text>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


# ------------------------------------------------------------------ the page
def build(L, cases):
    S = L["story"]
    A, c = context(L)
    ex = S["example"]
    eng = bf.panel(L)
    facts = A["facts"]["data"]
    parts = []

    nav = ('<nav class="top"><a class="brand" href="index.html">OpenGEO</a><span>'
           '<a href="index.html" aria-current="page">Overview</a><a href="findings.html">Findings</a>'
           f'<a href="{esc(L["repo"])}">Repository</a></span></nav>')

    # hero
    h = S["hero"]
    parts.append(
        '<header class="story">' + '<div class="eyebrow">' + "<span>·</span>".join(f"<span>{e}</span>" for e in S["eyebrow"])
        + f'</div><h1>{esc(S["headline"])}</h1><p class="standfirst">{fmt(S["standfirst"], c)}</p>'
        f'<div class="figs"><div class="fig"><span class="l">{esc(h["before"])}</span><span class="v">{c["s_facts_before"]}</span>'
        f'<span class="u">{esc(h["unit"])}</span></div><div class="arrow" aria-hidden="true">→</div>'
        f'<div class="fig after"><span class="l">{esc(h["after"])}</span><span class="v">{c["s_facts_after"]}</span>'
        f'<span class="u">{esc(h["unit"])}</span></div></div><p class="note">{fmt(h["note"], c)}</p></header>')

    # worked example, as tabs
    lab = ex["labels"]
    tabs, panes = [], []
    for i, case in enumerate(cases):
        tabs.append(f'<input type="radio" name="ex" id="ex-{case["key"]}"{" checked" if i == 0 else ""}>'
                    f'<label for="ex-{case["key"]}">{esc(case["tab"])}</label>')
        rows = []
        for e in eng:
            ctl, trt, n = case["cited"][e["model"]]
            rows.append((e["name"], e["short"], ctl / n, trt / n,
                         f'{e["name"]} · {e["short"]}\nbefore: {ctl} of {n} answers cited the page\nafter: {trt} of {n}',
                         f'{ctl} → <b>{trt}</b> <span>of {n}</span>', False))
        ab, aa = case["answers"]["before"], case["answers"]["after"]
        panes.append(
            f'<div class="pane" id="pane-{case["key"]}"><p class="q"><span class="k">The question</span>{esc(case["question"])}</p>'
            f'<div class="pair"><div class="card before"><span class="k">{esc(lab["before"])}</span><p>{esc(case["vague"])}</p></div>'
            f'<div class="card after"><span class="k">{esc(lab["after"])}</span><p>{mark_figures(case["specific"])}</p></div></div>'
            f'<p class="sub">{esc(lab["said"])}</p>'
            f'<div class="pair"><div class="card answer"><span class="k">{esc(lab["before"].split(":")[0])}</span>'
            f'<p>{mark_cites(ab["text"], ab["slot"])}</p><span class="foot">Your page was [{ab["slot"]}]; not cited</span></div>'
            f'<div class="card answer after"><span class="k">{esc(lab["after"].split(":")[0])}</span>'
            f'<p>{mark_cites(aa["text"], aa["slot"])}</p><span class="foot">Your page was [{aa["slot"]}]; cited</span></div></div>'
            f'<p class="sub">{fmt(lab["engines"], c)}</p>'
            + legend_before_after("Before", "After") + dumbbell(rows, "of answers")
            + numbers_table(["Engine", "Model", "Before", "After", "Answers"],
                            [(e["name"], e["short"], case["cited"][e["model"]][0], case["cited"][e["model"]][1],
                              case["cited"][e["model"]][2]) for e in eng])
            + "</div>")
    parts.append(
        f'<section class="s" id="example"><p class="kicker">{fmt(ex["kicker"], c)}</p><h2>{esc(ex["heading"])}</h2>'
        f'<p class="lead">{fmt(ex["lead"], c)}</p><div class="tabs" role="group" aria-label="Examples">{"".join(tabs)}'
        f'{"".join(panes)}</div><p class="after">{fmt(ex["after"], c)}</p></section>')

    # across all questions
    al = S["all"]
    P = facts["pooled"]
    pm = facts["per_model"]
    rows = [(e["name"], e["short"], pm[e["model"]]["control"], pm[e["model"]]["treatment"],
             f'{e["name"]} · {e["short"]}\n{bf.pct(pm[e["model"]]["control"])} → {bf.pct(pm[e["model"]]["treatment"])}\n'
             f'{spts(pm[e["model"]]["delta"], 0)} points, 95% interval {sci(pm[e["model"]]["ci"], 0)}',
             f'<b>{spts(pm[e["model"]]["delta"], 0)}</b>', False)
            for e in eng if e["model"] in pm]
    how = "averaged" if P.get("weighting") == "equal" else "weighted by traffic share"
    rows.append(("All models", f'{P["n_models"]} models, {how}', P["control"], P["treatment"],
                 f'All {P["n_models"]} models, {how}\n{bf.pct(P["control"])} → {bf.pct(P["treatment"])}\n'
                 f'{c["s_facts_pts"]} points, 95% interval {c["s_facts_ci"]}', f'<b>{c["s_facts_pts"]}</b>', True))
    parts.append(
        f'<section class="s" id="all"><p class="kicker">{fmt(al["kicker"], c)}</p><h2>{esc(al["heading"])}</h2>'
        + "".join(f"<p>{fmt(b, c)}</p>" for b in al["body"])
        + "<figure>" + legend_before_after("Talks around the question", "States the specific answer")
        + dumbbell(rows, "of answers") + f'<figcaption>{fmt(al["caption"], c)}</figcaption>'
        + numbers_table(["Engine", "Model", "Before", "After", "Change (points)", "95% interval"],
                        [(e["name"], e["short"], bf.pct(pm[e["model"]]["control"]), bf.pct(pm[e["model"]]["treatment"]),
                          spts(pm[e["model"]]["delta"], 0), sci(pm[e["model"]]["ci"], 0)) for e in eng if e["model"] in pm]
                        + [("All models", f'{P["n_models"]} models', bf.pct(P["control"]), bf.pct(P["treatment"]),
                            c["s_facts_pts"], c["s_facts_ci"])])
        + f'</figure><div class="caveat">{fmt(al["caveat"], c)}</div></section>')

    # everything else on one scale
    rs = S["rest"]
    frows = [{**r, "pooled": A[r["alias"]]["data"]["pooled"]} for r in rs["rows"]]
    parts.append(
        f'<section class="s" id="rest"><p class="kicker">{fmt(rs["kicker"], c)}</p><h2>{esc(rs["heading"])}</h2>'
        + "".join(f"<p>{fmt(b, c)}</p>" for b in rs["body"])
        + f'<figure>{effects(frows, c)}<figcaption>{fmt(rs["caption"], c)}</figcaption>'
        + numbers_table(["Change", "Effect (points)", "95% interval", "Evidence"],
                        [(r["label"], spts(r["pooled"]["delta"], _nd(r["pooled"]["delta"])),
                          sci(r["pooled"]["ci"], _nd(r["pooled"]["delta"])), fmt(r["tag"], c)) for r in frows])
        + "</figure>" + "".join(f'<p class="after">{fmt(b, c)}</p>' for b in rs["after"]) + "</section>")

    # worth knowing
    mo = S["more"]
    cards = []
    for k in mo["cards"]:
        f = A[k["alias"]]
        fc = {**c, **bf.CTX[f["kind"]](f, L, A)} if f.get("kind") in bf.CTX else c
        extra = bf.units(f, L, fc) if k["alias"] == "misattribution" else ""
        wide = " wide" if extra else ""
        cards.append(f'<div class="kcard{wide}"><div class="kt"><h3>{esc(k["title"])}</h3><p>{fmt(k["text"], c)}</p>'
                     f'<a class="more" href="findings.html#{esc(k["alias"])}">The full finding</a></div>{extra}</div>')
    parts.append(f'<section class="s" id="more"><p class="kicker">{fmt(mo["kicker"], c)}</p><h2>{esc(mo["heading"])}</h2>'
                 f'<div class="kcards">{"".join(cards)}</div></section>')

    # where it stops
    li = S["limits"]
    parts.append(f'<section class="s" id="limits"><p class="kicker">{fmt(li["kicker"], c)}</p><h2>{esc(li["heading"])}</h2>'
                 + pipeline(S, c) + '<ul class="limits">' + "".join(f"<li>{fmt(s, c)}</li>" for s in li["items"]) + "</ul></section>")

    # your turn
    t = S["test"]
    parts.append(
        f'<section class="s" id="test"><p class="kicker">{fmt(t["kicker"], c)}</p><h2>{esc(t["heading"])}</h2>'
        + "".join(f"<p>{fmt(b, c)}</p>" for b in t["body"]) + demo(S, c)
        + f'<p class="skill">{fmt(t["skill"], c)}</p><div class="links">'
        + "".join(f'<a href="{esc(bf.repo_url(L, l["path"], l.get("tree", False)))}">{esc(l["label"])}</a>' for l in t["links"])
        + "</div></section>")

    # how we know
    pg, me = L["page"], S["method"]
    parts.append(
        f'<section class="s" id="method"><p class="kicker">{fmt(me["kicker"], c)}</p><h2>{esc(me["heading"])}</h2><div class="method">'
        + "".join(f'<div><div class="k">{esc(m["k"])}</div><p>{fmt(m["text"], c)}</p></div>' for m in pg["method"])
        + '</div><div class="links"><a class="primary" href="findings.html">Every finding, with per-engine charts</a>'
        + "".join(f'<a href="{esc(bf.repo_url(L, l["path"], l.get("tree", False)))}">{esc(l["label"])}</a>' for l in pg["links"])
        + "</div></section>")

    body = (f'<div class="wrap">{nav}{"".join(parts)}<footer>{fmt(S["footer"], c)}</footer></div>'
            f'<div class="tip" id="tip" role="status" aria-live="polite"></div><script>{JS}</script>')
    return ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(S["title"])}</title><meta name="description" content="{esc(S["description"])}">'
            f'{bf.FONTS}<style>{bf.CSS}{CSS}</style></head><body>{body}</body></html>\n')


CSS = r"""
:root{--before:#cf9a4e;--after:#a86c14;--accent:#a86c14;--gray:#8a8276}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--before:#8a5a1a;--after:#d9a04a;--accent:#d9a04a;--gray:#7e776c}}
:root[data-theme="dark"]{--before:#8a5a1a;--after:#d9a04a;--accent:#d9a04a;--gray:#7e776c}
header.story h1{max-width:20ch}
.figs{display:grid;grid-template-columns:1fr auto 1fr;gap:18px;align-items:center;margin:34px 0 0;
  padding:22px 24px;background:var(--raised);border:1px solid var(--line);border-radius:4px}
.fig{display:flex;flex-direction:column;gap:4px}
.fig .l{font-size:13.5px;color:var(--ink-2);line-height:1.4;max-width:24ch}
.fig .v{font-family:"Public Sans",sans-serif;font-weight:600;font-size:clamp(48px,9vw,72px);line-height:1;
  letter-spacing:-.03em;color:var(--muted)}
.fig.after .v{color:var(--accent)}
.fig .u{font-size:12.5px;color:var(--muted)}
.figs .arrow{font-size:30px;color:var(--muted)}
header.story .note{font-size:12.5px;color:var(--muted);margin:10px 0 0;max-width:72ch}
section.s{margin:72px 0 0;padding:34px 0 0;border-top:1px solid var(--line-2)}
section.s h2{max-width:26ch}
section.s>p,section.s .lead{max-width:64ch;color:var(--ink-2);margin:0 0 12px}
section.s>p.kicker{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--accent);font-weight:600;margin:0 0 10px;max-width:none}
section.s p b{color:var(--ink)}
section.s>p.after{margin-top:16px}
section.s>p.skill{margin-top:26px}
.tabs{margin:22px 0 0}
.tabs>input{position:absolute;opacity:0;pointer-events:none}
.tabs>label{display:inline-block;font-family:"IBM Plex Mono",monospace;font-size:12px;padding:8px 13px;margin:0 6px 8px 0;
  border:1px solid var(--line-2);border-radius:3px;cursor:pointer;color:var(--ink-2);background:var(--raised)}
.tabs>input:checked+label{border-color:var(--accent);color:var(--ink);box-shadow:inset 0 -2px 0 var(--accent)}
.tabs>input:focus-visible+label{outline:2px solid var(--accent);outline-offset:2px}
.pane{display:none;margin-top:10px}
#ex-hvac:checked~#pane-hvac,#ex-saas:checked~#pane-saas{display:block}
.q{font-size:17px;color:var(--ink);margin:6px 0 16px;max-width:60ch;line-height:1.5}
.q .k,.card .k{display:block;font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.12em;
  text-transform:uppercase;color:var(--muted);font-weight:600;margin-bottom:6px}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.card{background:var(--raised);border:1px solid var(--line);border-radius:4px;padding:14px 16px;font-size:14px;line-height:1.6}
.card p{margin:0;color:var(--ink-2)}
.card.after{border-color:var(--accent)}
.card.after .k{color:var(--accent)}
.card mark{background:var(--ochre-soft);color:var(--ink);padding:0 2px;border-radius:2px}
.card.answer{font-family:"IBM Plex Mono",monospace;font-size:12.5px;line-height:1.65}
.card .foot{display:block;margin-top:10px;font-family:"IBM Plex Mono",monospace;font-size:10.5px;color:var(--muted)}
.cite{color:var(--muted)}
.cite.you{color:var(--ink);background:var(--ochre-soft);font-weight:600;padding:0 2px;border-radius:2px}
p.sub{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;
  color:var(--muted);font-weight:600;margin:26px 0 10px}
.legend .key{width:11px;height:11px;border-radius:50%;display:inline-block}
.key.before{background:var(--before)}.key.after{background:var(--after)}
.db,.fx{margin:6px 0 0}
.db-row,.fx-row{display:grid;grid-template-columns:170px 1fr 92px;gap:14px;align-items:center;padding:7px 0;
  border-radius:3px;outline:none}
.fx-row{grid-template-columns:250px 1fr}
.db-row:hover,.db-row:focus-visible,.fx-row:hover,.fx-row:focus-visible{background:var(--sunk)}
.db-row.pooled{border-top:1px solid var(--line-2);margin-top:4px;padding-top:11px}
.db-name,.fx-name{display:flex;flex-direction:column;line-height:1.3}
.db-name b,.fx-name b{font-size:14px;font-weight:600;color:var(--ink)}
.db-name span,.fx-name span{font-family:"IBM Plex Mono",monospace;font-size:10.5px;color:var(--muted)}
.db-plot,.fx-plot{position:relative;height:22px;background:linear-gradient(var(--line),var(--line)) 0 50%/100% 1px no-repeat}
.db-link{position:absolute;top:50%;height:2px;margin-top:-1px;background:var(--before)}
.dot{position:absolute;top:50%;width:13px;height:13px;margin:-6.5px 0 0 -6.5px;border-radius:50%;
  box-shadow:0 0 0 2px var(--raised)}
.dot.before{background:var(--before)}.dot.after{background:var(--after)}
.db-val{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--ink-2);text-align:right;white-space:nowrap}
.db-val b{color:var(--ink);font-size:13px}
.db-val span{color:var(--muted)}
.db-axis,.fx-axis{display:grid;grid-template-columns:170px 1fr 92px;gap:14px;margin-top:4px}
.fx-axis{grid-template-columns:250px 1fr}
.ticks{position:relative;height:16px;font-family:"IBM Plex Mono",monospace;font-size:10px;color:var(--muted)}
.ticks span{position:absolute;transform:translateX(-50%);white-space:nowrap}
.db-axis .unit{font-family:"IBM Plex Mono",monospace;font-size:10px;color:var(--muted);text-align:right}
.fx-plot{height:30px}
.fx-plot .zero{position:absolute;top:-4px;bottom:-4px;width:1px;background:var(--line-2)}
.fx-plot .ci{position:absolute;top:50%;height:2px;margin-top:-1px;background:var(--gray);border-radius:1px}
.fx-plot .pt{position:absolute;top:50%;width:13px;height:13px;margin:-6.5px 0 0 -6.5px;border-radius:50%;
  background:var(--gray);box-shadow:0 0 0 2px var(--raised)}
.fx-row.em .ci,.fx-row.em .pt{background:var(--accent)}
.fx-plot .val{position:absolute;top:50%;transform:translate(10px,-50%);font-family:"IBM Plex Mono",monospace;
  font-size:12.5px;font-weight:600;color:var(--ink);white-space:nowrap}
.axis-label{font-family:"IBM Plex Mono",monospace;font-size:10px;color:var(--muted);margin:6px 0 0;text-align:right}
details.numbers{margin:12px 0 0;font-size:12.5px}
details.numbers summary{cursor:pointer;font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--muted)}
details.numbers table{border-collapse:collapse;margin-top:8px;min-width:420px}
details.numbers th,details.numbers td{padding:5px 12px 5px 0;border-bottom:1px solid var(--line);text-align:left;
  font-variant-numeric:tabular-nums}
details.numbers th{font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.caveat{margin:24px 0 0;padding:14px 16px;border-left:3px solid var(--accent);background:var(--raised);
  max-width:66ch;font-size:14.5px;color:var(--ink-2)}
.caveat b{color:var(--ink)}
.kcards{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:18px}
.kcard{background:var(--raised);border:1px solid var(--line);border-radius:4px;padding:16px 18px;display:flex;gap:26px}
.kcard.wide{grid-column:1 / -1}
.kcard .kt{display:flex;flex-direction:column;flex:1;min-width:0}
.kcard h3{font-family:"Instrument Serif",Georgia,serif;font-weight:400;font-size:21px;line-height:1.2;margin:0 0 8px}
.kcard p{font-size:14px;color:var(--ink-2);margin:0 0 10px;max-width:52ch}
.kcard .units{margin:0;gap:18px;flex:none;align-items:flex-start}
.kcard .unitgrid{width:150px}
.kcard .ulegend{font-size:12px;gap:6px;max-width:30ch}
.kcard .more{margin-top:auto;font-family:"IBM Plex Mono",monospace;font-size:11.5px}
.pipe{list-style:none;padding:0;margin:22px 0 22px;display:grid;grid-template-columns:repeat(4,1fr);gap:10px;counter-reset:s}
.pipe .step{position:relative;background:var(--raised);border:1px solid var(--line);border-radius:4px;
  padding:30px 14px 14px;font-size:14px;color:var(--ink-2);line-height:1.4}
.pipe .step .n{position:absolute;top:10px;left:14px;font-family:"IBM Plex Mono",monospace;font-size:10.5px;color:var(--muted)}
.pipe .step:not(:last-child)::after{content:"→";position:absolute;right:-5px;top:50%;transform:translate(50%,-50%);
  color:var(--muted);font-size:13px;line-height:1;background:var(--paper);padding:2px 0;z-index:1}
.pipe .step .tag{position:absolute;top:-10px;right:10px;font-family:"IBM Plex Mono",monospace;font-size:9.5px;
  letter-spacing:.1em;text-transform:uppercase;font-weight:600;padding:2px 7px;border-radius:2px;background:var(--paper)}
.pipe .step.measured{border:2px solid var(--accent);color:var(--ink)}
.pipe .step.measured .tag{color:var(--accent);border:1px solid var(--accent)}
.pipe .step.unmeasured{background:var(--sunk);border-style:solid}
.pipe .step.unmeasured .tag{color:var(--muted);border:1px solid var(--line-2)}
.demo{margin:22px 0 0}
.term{background:#191610;border-radius:6px;overflow:hidden;border:1px solid var(--line-2)}
.term .bar{display:flex;gap:6px;padding:9px 12px;background:#24201a}
.term .bar i{width:10px;height:10px;border-radius:50%;background:#4a4339}
.term pre{margin:0;padding:14px 16px;color:#e8e1d3;font:12.5px/1.6 "IBM Plex Mono",monospace;overflow-x:auto;white-space:pre}
.term .pr{color:#8f877a}.term .ok{color:#d9a04a;font-weight:600}
.demo img{display:block;width:100%;height:auto;margin-top:14px;border:1px solid var(--line);border-radius:4px}
.demo figcaption{margin-top:10px}
.links a.primary{border-color:var(--accent);color:var(--ink)}
@media (max-width:640px){
  .figs{grid-template-columns:1fr;gap:10px}.figs .arrow{transform:rotate(90deg);justify-self:start}
  .pair{grid-template-columns:1fr}
  .db-row,.db-axis{grid-template-columns:1fr 64px;gap:4px 10px}
  .db-name{grid-column:1 / -1}
  .db-axis>div:first-child{display:none}
  .fx-row,.fx-axis{grid-template-columns:1fr;gap:6px}
  .fx-axis>div:first-child{display:none}
  .fx-plot,.fx-axis .ticks{margin-right:44px}
  .db-axis .unit{display:none}
  .pipe{grid-template-columns:1fr 1fr;row-gap:18px}
  .pipe .step:not(:last-child)::after{display:none}
  .kcards{grid-template-columns:1fr}
  .kcard{flex-direction:column;gap:14px}
}
"""

JS = r"""
(function(){var t=document.getElementById("tip");
function show(g,x,y){t.textContent=g.dataset.tip;t.style.opacity=1;place(x,y)}
function place(x,y){var w=t.offsetWidth,h=t.offsetHeight;
  t.style.left=Math.max(8,Math.min(x+14,innerWidth-w-8))+"px";t.style.top=Math.max(y-h-14,8)+"px"}
document.addEventListener("mouseover",function(e){var g=e.target.closest("[data-tip]");
  if(!g){t.style.opacity=0;return}show(g,e.clientX,e.clientY)});
document.addEventListener("mousemove",function(e){if(t.style.opacity==="1")place(e.clientX,e.clientY)});
document.addEventListener("focusin",function(e){var g=e.target.closest("[data-tip]");if(!g)return;
  var r=g.getBoundingClientRect();show(g,r.left+r.width/2,r.top)});
document.addEventListener("focusout",function(){t.style.opacity=0})})();
"""
