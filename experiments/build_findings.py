#!/usr/bin/env python3
"""
OpenGEO -- build the public pages from the findings ledger.

    python3 build_findings.py                  # results/findings.json -> ../docs/index.html
                                               #   (the story) and ../docs/findings.html,
                                               #   plus the findings in ../README.md
    python3 build_findings.py --check          # validate the ledger, write nothing
    python3 build_findings.py --fragment -o x  # findings page body only, for embedding

docs/index.html is the plain-language story (build_story.py, design/story-page.md);
docs/findings.html is the full technical findings page, built here. Both follow the
rules below.

The pages are a pure function of results/findings.json -- plus, for the story's worked
examples, the committed raw results those examples quote. Figures are never typed into this
file or into page copy: prose in the ledger carries {placeholders} filled from the
entry's own data at build time, and every public entry cites the committed report its
numbers come from. When a round closes, its entry is added and the page is rebuilt;
there is no second place to update.

What is public is decided in the ledger, not here. Entries marked "public": false (the
metric-validity checks) stay in the record and off the page. An entry whose status is
"in_progress" shows its question and nothing else -- pre-registered rounds forbid
interim analysis, so the page has no interim numbers to show, and the build refuses an
in-progress entry that carries result data.

Sentences a reader would take as statements of fact -- "every model", "no engine went
the other way", "an order of magnitude" -- are tied to named assertions in the ledger
that the build checks against the data. If a new round would make one false, the build
stops instead of publishing it.

Standard library only.
"""
import argparse, html, json, math, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent      # the ledger's paths are relative to the repository root, as is docs/
MINUS = "−"
MONO = 'font-family="IBM Plex Mono, monospace"'


def esc(s):
    return html.escape(str(s), quote=True)


# ------------------------------------------------------------------ formatting
def r0(x):
    """Round half away from zero. format() rounds half to even, which turns 13.5 into
    14 but 12.5 into 12 -- fine for arithmetic, surprising on a published page."""
    return int(math.floor(abs(x) + 0.5)) * (1 if x >= 0 else -1)

def signed(v, nd=1):
    body = f"{abs(v):.{nd}f}" if nd else str(abs(r0(v)))
    return ("+" if v >= 0 else MINUS) + body

def pts(p, nd=1):
    return signed(p * 100, nd)

def ci_pts(ci):
    return f"[{pts(ci[0])}, {pts(ci[1])}]"

def pct(p, nd=0):
    return f"{r0(p * 100)}%" if nd == 0 else f"{p * 100:.{nd}f}%"

def num(n):
    return f"{n:,}"

def p_text(p):
    p = str(p)
    return f"p < {p[1:]}" if p.startswith("<") else f"p = {p}"

WORDS = "zero one two three four five six seven eight nine ten".split()

def word(n):
    return WORDS[n] if 0 <= n < len(WORDS) else str(n)

def join_and(xs):
    xs = list(xs)
    return "".join(xs) if len(xs) < 2 else ", ".join(xs[:-1]) + " and " + xs[-1]

def fmt(template, ctx):
    try:
        return template.format_map(ctx)
    except KeyError as e:
        sys.exit(f"ledger prose uses {{{e.args[0]}}}, which nothing provides:\n  {template[:90]}")


# ------------------------------------------------------------------ ledger helpers
def panel(L):
    return sorted(L["engines"], key=lambda e: -e["share"])

def model_name(L, mid):
    for e in L["engines"]:
        if e["model"] == mid:
            return e["name"]
    return L.get("model_names", {}).get(mid, mid)

def sig(ci):
    return ci[0] > 0 or ci[1] < 0

def spans_zero(ci):
    return ci[0] <= 0 <= ci[1]

def colour(delta, ci):
    if not sig(ci):
        return "var(--nil)"
    return "var(--pos)" if delta > 0 else "var(--neg)"

def social_meta(L, title, description, path=""):
    """What a shared link shows on LinkedIn, X, Slack and the rest: title, summary and the
    preview image (build_story.preview_svg, rendered by render_preview.py)."""
    import build_story
    S, url = L["story"], L["site"] + path
    tags = [("og:type", "website"), ("og:site_name", "OpenGEO"), ("og:title", title),
            ("og:description", description), ("og:url", url),
            ("og:image", L["site"] + build_story.PREVIEW_PNG.removeprefix("docs/")),
            ("og:image:width", build_story.PREVIEW_SIZE[0]), ("og:image:height", build_story.PREVIEW_SIZE[1]),
            ("og:image:alt", f'{S["headline"]} {S["preview"]["alt"]}')]
    return ("".join(f'<meta property="{k}" content="{esc(v)}">' for k, v in tags)
            + f'<meta name="twitter:card" content="summary_large_image"><link rel="canonical" href="{esc(url)}">')


def png_text(path, key):
    """A tEXt value from a PNG, or None: the preview records the hash of the SVG it was made from."""
    data, i = path.read_bytes(), 8
    while i + 8 <= len(data):
        n, kind = int.from_bytes(data[i:i + 4], "big"), data[i + 4:i + 8]
        if kind == b"tEXt":
            k, _, v = data[i + 8:i + 8 + n].partition(b"\0")
            if k.decode("latin-1") == key:
                return v.decode("latin-1")
        i += 12 + n
    return None


def repo_url(L, path, tree=False):
    if not path:
        return L["repo"]
    return f'{L["repo"]}/{"tree" if tree else "blob"}/main/{path}'


# ------------------------------------------------------------------ contexts
def ctx_common(f, L, A):
    pv, c = f.get("provenance", {}), {}
    for k in ("prompts", "domains"):
        if k in pv:
            c[k] = str(pv[k])
    if "calls" in pv:
        c["calls"] = num(pv["calls"])
    return c

def ctx_paired(f, L, A):
    d, c = f["data"], ctx_common(f, L, A)
    P, pm = d["pooled"], d["per_model"]
    deltas = [m["delta"] for m in pm.values()]
    c.update(
        pooled_delta_pts=pts(P["delta"]),
        pooled_delta_abs=f"{abs(P['delta']) * 100:.1f}",
        pooled_ci_pts=ci_pts(P["ci"]),
        pooled_control_pct0=pct(P["control"]),
        pooled_control_pct1=pct(P["control"], 1),
        pooled_treatment_pct1=pct(P["treatment"], 1),
        n_models=str(P["n_models"]),
        p_text=p_text(P["p"]),
        delta_min_abs=str(abs(r0(min(deltas) * 100))),
        delta_max_abs=str(abs(r0(max(deltas) * 100))),
        n_negative=word(sum(1 for m in pm.values() if m["ci"][1] < 0)),
        n_positive=word(sum(1 for m in pm.values() if m["ci"][0] > 0)),
    )
    if d.get("replications"):
        c["replication_prompts"] = str(d["replications"][0]["prompts"])

    in_panel = {e["model"] for e in L["engines"]}
    others = [(mid, m) for mid, m in pm.items() if mid not in in_panel and not m.get("excluded")]
    same_dir = (lambda m: m["ci"][0] > 0) if P["delta"] >= 0 else (lambda m: m["ci"][1] < 0)
    yes = [model_name(L, mid) for mid, m in others if same_dir(m)]
    no = [model_name(L, mid) for mid, m in others if not same_dir(m)]
    c["others_effect_sentence"] = "; ".join(s for s in (
        yes and f"{join_and(yes)} showed the same effect",
        no and f"{join_and(no)} did not") if s)

    listed = [f"{model_name(L, mid)} ({pts(m['delta'])})" for mid, m in others]
    n_clear = sum(sig(m["ci"]) for _, m in others)
    verb = "is" if len(others) == 1 else "are"
    if not others:
        pool = "every model in it is shown above"
    elif n_clear == 0:
        tail = ("its interval does not clear zero" if len(others) == 1 else
                "neither of their intervals clears zero" if len(others) == 2 else
                "none of their intervals clears zero")
        pool = f"{join_and(listed)} {verb} in it, and {tail}"
    else:
        pool = f"{join_and(listed)} {verb} in it; {word(n_clear)} of them clear{'s' if n_clear == 1 else ''} zero"
    c["others_pool_sentence"] = pool

    c["excluded_sentence"] = " ".join(
        f"{model_name(L, mid)} was excluded for {m['excluded']}."
        for mid, m in pm.items() if m.get("excluded"))

    spans = [e["name"] for e in panel(L) if e["model"] in pm and spans_zero(pm[e["model"]]["ci"])]
    c["panel_spans_zero_clause"] = f", but on {join_and(spans)} the interval includes zero" if spans else ""

    if d.get("compare_to"):
        c["ratio_vs_compare"] = str(r0(A[d["compare_to"]]["data"]["pooled"]["delta"] / P["delta"]))
    if d.get("fidelity"):
        fp = d["fidelity"]["primary"]
        c.update(fidelity_delta_pts=pts(fp["delta"]), fidelity_ci_pts=ci_pts(fp["ci"]))
    return c

def ctx_agreement(f, L, A):
    c, rs = ctx_common(f, L, A), f["data"]["rounds"]
    c.update(latest_label=rs[0]["label"], cross=f"{rs[0]['cross']:.2f}", within=f"{rs[0]['within']:.2f}")
    if len(rs) > 1:
        c.update(earlier_label=rs[1]["label"], earlier_cross=f"{rs[1]['cross']:.3f}",
                 earlier_within=f"{rs[1]['within']:.3f}")
    return c

def ctx_misattribution(f, L, A):
    c = ctx_common(f, L, A)
    js = sorted(f["data"]["judges"], key=lambda j: j["rate"])
    lo, hi = js[0], js[-1]
    span = lambda ci: f"{ci[0] * 100:.1f}–{ci[1] * 100:.1f}"
    c.update(low_pct=pct(lo["rate"]), high_pct=pct(hi["rate"]),
             low_n=str(r0(lo["rate"] * 100)), high_n=str(r0(hi["rate"] * 100)),
             low_judge=lo["judge"], high_judge=hi["judge"],
             low_ci=span(lo["ci"]), high_ci=span(hi["ci"]),
             sentences=num(sum(j["sentences"] for j in js)))
    return c

def ctx_calibration(f, L, A):
    c, d = ctx_common(f, L, A), f["data"]
    qs = d["questions"]
    web_only = sum(1 for q in qs if q["web"] and not q["api"])
    api_only = sum(1 for q in qs if q["api"] and not q["web"])
    c.update(
        n_questions=str(len(qs)), n_web_only=str(web_only),
        reverse_phrase=("never happened" if api_only == 0 else
                        "happened once" if api_only == 1 else f"happened {word(api_only)} times"),
        divergence=f"{d['divergence']:.2f}",
        divergence_ci=f"[{d['divergence_ci'][0]:.2f}, {d['divergence_ci'][1]:.2f}]",
        api_runs_word=word(d["api_runs"]), ui_runs_word=word(d["ui_runs"]))
    return c

def ctx_reliability(f, L, A):
    d = f["data"]
    return {"low": f"{d['split_half_min']:.2f}", "high": f"{d['split_half_max']:.2f}"}

CTX = {"paired_effect": ctx_paired, "agreement": ctx_agreement,
       "misattribution": ctx_misattribution, "calibration": ctx_calibration,
       "reliability": ctx_reliability}

def contexts(L):
    A = {f["alias"]: f for f in L["findings"]}
    own = {a: CTX.get(f.get("kind"), ctx_common)(f, L, A) for a, f in A.items()}
    page = {f"{a}_{k}": v for a, c in own.items() for k, v in c.items()}
    page["engine_names"] = join_and(e["name"] for e in panel(L))
    page["share_source"] = L["traffic_share"]["label"]
    ctrls = [r0(A[a]["data"]["pooled"]["control"] * 100) for a in L["page"]["hero_levers"]]
    page["baseline_range"] = (f"{min(ctrls)}–{max(ctrls)}%" if min(ctrls) != max(ctrls)
                              else f"{ctrls[0]}%")
    page.update({k: str(v) for k, v in L["page"].get("design", {}).items()})
    return A, page, {a: {**page, **c} for a, c in own.items()}


# ------------------------------------------------------------------ assertions
def _pm(f):
    return f["data"]["per_model"].values()

def _overlap(a, b):
    return a[0] <= b[1] and b[0] <= a[1]

ASSERTS = {
    "pooled_ci_excludes_zero": lambda f, A: sig(f["data"]["pooled"]["ci"]),
    "pooled_ci_spans_zero": lambda f, A: spans_zero(f["data"]["pooled"]["ci"]),
    "some_model_ci_below_zero": lambda f, A: any(m["ci"][1] < 0 for m in _pm(f)),
    "no_model_ci_above_zero": lambda f, A: all(m["ci"][0] <= 0 for m in _pm(f)),
    "all_models_ci_above_zero": lambda f, A: all(m["ci"][0] > 0 for m in _pm(f)),
    "no_model_ci_below_zero": lambda f, A: all(m["ci"][1] >= 0 for m in _pm(f)),
    "replications_ci_exclude_zero": lambda f, A: all(sig(r["ci"]) for r in f["data"]["replications"]),
    "at_least_10x_smaller_than_compare": lambda f, A:
        A[f["data"]["compare_to"]]["data"]["pooled"]["delta"] >= 10 * f["data"]["pooled"]["delta"],
    "fidelity_null_under_both_judges": lambda f, A: all(
        spans_zero(j["ci"]) for j in (f["data"]["fidelity"]["primary"], f["data"]["fidelity"]["crosscheck"])),
    "cross_and_within_intervals_overlap": lambda f, A: _overlap(
        f["data"]["rounds"][0]["cross_ci"], f["data"]["rounds"][0]["within_ci"]),
    "both_cited_rows_share_a_domain": lambda f, A: all(
        set(q["api"]) & set(q["web"]) for q in f["data"]["questions"] if q["api"] and q["web"]),
}

PLACEHOLDER = re.compile(r"\{[^{}]*\}")
TAG = re.compile(r"<[^>]+>")

def prose(L):
    pg = L["page"]
    for key in ("headline", "standfirst", "hero_note", "footer"):
        yield f"page.{key}", pg[key]
    for i, s in enumerate(pg["limits"]):
        yield f"page.limits[{i}]", s
    for i, m in enumerate(pg["method"]):
        yield f"page.method[{i}]", m["text"]
    for f in L["findings"]:
        if not f.get("public"):
            continue
        for part in ("text", "chart"):
            for k, v in f.get(part, {}).items():
                for i, s in enumerate(v if isinstance(v, list) else [v]):
                    if isinstance(s, str):
                        yield f"{f['alias']}.{part}.{k}[{i}]", s

def validate(L, root):
    errors, warnings = [], []
    A = {f["alias"]: f for f in L["findings"]}
    if len(A) != len(L["findings"]):
        errors.append("two entries share an alias")
    for f in L["findings"]:
        for name in f.get("asserts", []):
            fn = ASSERTS.get(name)
            if fn is None:
                errors.append(f"{f['alias']}: unknown assertion '{name}'")
            elif not fn(f, A):
                errors.append(f"{f['alias']}: assertion no longer holds -- {name}")
        pv = f.get("provenance", {})
        for key in ("report", "preregistration"):
            if pv.get(key) and not (root / pv[key]).exists():
                errors.append(f"{f['alias']}: {key} not found: {pv[key]}")
        for p in pv.get("data", []):
            if not (root / p).exists():
                errors.append(f"{f['alias']}: data file not found: {p}")
        if f.get("public") and f["status"] != "in_progress" and not pv.get("report"):
            errors.append(f"{f['alias']}: public result with no report to cite")
        if f["status"] == "in_progress" and f.get("data"):
            errors.append(f"{f['alias']}: in-progress entries may not carry result data")
    import build_story
    story_errors, _ = build_story.check(L)
    errors += story_errors
    png = root / build_story.PREVIEW_PNG
    if L.get("story") and (not png.exists() or png_text(png, build_story.PREVIEW_KEY) != build_story.preview_hash(L)):
        warnings.append(f"{build_story.PREVIEW_PNG}, the image shared links show, does not match the "
                        "ledger -- run python3 render_preview.py")
    allow = L["page"].get("literal_numbers", [])
    for where, s in list(prose(L)) + list(build_story.prose(L)):
        t = TAG.sub("", PLACEHOLDER.sub("", s))
        for a in allow:
            t = t.replace(a, "")
        hits = re.findall(r"\S*\d\S*", t)
        if hits:
            warnings.append(f"{where}: typed number(s) {hits}")
    return errors, warnings


# ------------------------------------------------------------------ charts
def grid_line(x, y1, y2):
    return f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}" stroke="var(--line)" stroke-width="1"/>'

def zero_line(x, y1, y2):
    return (f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}" stroke="var(--line-2)" '
            f'stroke-width="1.5" stroke-dasharray="3 3"/>')

def tick(x, y, label):
    return (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" fill="var(--muted)" {MONO} '
            f'font-size="10.5">{esc(label)}</text>')

def engine_label(name, sub, y):
    return (f'<text x="0" y="{y + 1:.1f}" fill="var(--ink)" font-size="14" font-weight="600">{esc(name)}</text>'
            f'<text x="0" y="{y + 16:.1f}" fill="var(--muted)" {MONO} font-size="10">{esc(sub)}</text>')

def hit(tip, y, h, W=760):
    return f'<g data-tip="{esc(tip)}"><rect x="0" y="{y:.1f}" width="{W}" height="{h}" fill="transparent"/>'

def svg_hero(levers, fctx):
    W, LB, rowH, top = 760, 350, 52, 18
    PL, PR = LB, W - 70
    H = top + len(levers) * rowH + 40
    cis = [f["data"]["pooled"]["ci"] for f in levers]
    hi = math.ceil((max(c[1] for c in cis) * 100 + 3) / 10) * 10
    lo = min(-5, math.floor((min(c[0] for c in cis) * 100 - 3) / 5) * 5)
    x = lambda v: PL + (v - lo) / (hi - lo) * (PR - PL)
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" '
           f'aria-label="Effect of each tested change on citation rate, in percentage points">']
    for t in range(math.ceil(lo / 10) * 10, hi + 1, 10):
        out.append(grid_line(x(t), top - 6, H - 30) + tick(x(t), H - 12, "0" if t == 0 else signed(t, 0)))
    out.append(zero_line(x(0), top - 6, H - 30))
    for i, f in enumerate(levers):
        P, c = f["data"]["pooled"], fctx[f["alias"]]
        y = top + i * rowH + rowH / 2
        why = " · ".join([f'{P["n_models"]} models'] + [fmt(e["label"], c).lower() for e in f["evidence"]])
        col = colour(P["delta"], P["ci"])
        tip = f'{f["lever"]}\n{pts(P["delta"])} points  {ci_pts(P["ci"])}\n{why}'
        out.append(
            hit(tip, y - rowH / 2, rowH) +
            f'<text x="0" y="{y - 3:.1f}" fill="var(--ink)" font-size="14" font-weight="600">{esc(f["lever"])}</text>'
            f'<text x="0" y="{y + 15:.1f}" fill="var(--muted)" {MONO} font-size="10.5">{esc(why)}</text>'
            f'<line x1="{x(P["ci"][0] * 100):.1f}" y1="{y}" x2="{x(P["ci"][1] * 100):.1f}" y2="{y}" '
            f'stroke="{col}" stroke-width="2.5" stroke-linecap="round"/>'
            f'<circle cx="{x(P["delta"] * 100):.1f}" cy="{y}" r="7" fill="{col}" stroke="var(--raised)" stroke-width="2"/>'
            f'<text x="{x(P["ci"][1] * 100) + 10:.1f}" y="{y + 5:.1f}" fill="var(--ink)" {MONO} '
            f'font-size="14" font-weight="600">{pts(P["delta"])}</text></g>')
    out.append(f'<text x="{W - 8}" y="{H - 12}" text-anchor="end" fill="var(--muted)" {MONO} '
               f'font-size="9.5">pts</text></svg>')
    return "".join(out)

def svg_dumbbell(f, L, c):
    pm, ch = f["data"]["per_model"], f["chart"]
    rows = [e for e in panel(L) if e["model"] in pm]
    W, LB, rowH, top = 760, 170, 46, 16
    PL, PR = LB, W - 20
    H = top + len(rows) * rowH + 36
    x = lambda v: PL + v * (PR - PL)
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(ch["aria"])}">']
    for t in (0, .25, .5, .75, 1):
        out.append(grid_line(x(t), top - 6, H - 28) + tick(x(t), H - 10, f"{int(t * 100)}%"))
    for i, e in enumerate(rows):
        m = pm[e["model"]]
        a, b = m["control"], m["treatment"]
        y = top + i * rowH + rowH / 2 - 6
        tip = (f'{e["name"]} · {e["short"]}\n{ch["arm_short"][0]} {pct(a, 1)}  →  '
               f'{ch["arm_short"][1]} {pct(b, 1)}\nΔ {pts(m["delta"])} pts  {ci_pts(m["ci"])}')
        out.append(
            hit(tip, y - rowH / 2 + 6, rowH) + engine_label(e["name"], e["short"], y) +
            f'<line x1="{x(a) + 7:.1f}" y1="{y}" x2="{x(b) - 7:.1f}" y2="{y}" stroke="var(--ochre)" '
            f'stroke-width="2" opacity=".55"/>'
            f'<circle cx="{x(a):.1f}" cy="{y}" r="6" fill="var(--raised)" stroke="var(--ochre)" stroke-width="2.5"/>'
            f'<circle cx="{x(b):.1f}" cy="{y}" r="6.5" fill="var(--ochre)" stroke="var(--raised)" stroke-width="2"/>'
            f'<text x="{x(a) - 12:.1f}" y="{y + 4:.1f}" text-anchor="end" fill="var(--ink-2)" {MONO} '
            f'font-size="11">{r0(a * 100)}%</text></g>')
    legend = (f'<div class="legend"><span><i class="sw" style="border:2px solid var(--ochre)"></i>'
              f'{esc(ch["arms"][0])}</span><span><i class="sw" style="background:var(--ochre)"></i>'
              f'{esc(ch["arms"][1])}</span></div>')
    return figure(legend + "".join(out) + "</svg>", f, c)

def svg_forest(f, L, c):
    d, ch = f["data"], f["chart"]
    pm, P = d["per_model"], d["pooled"]
    rows = [(e["name"], e["short"], pm[e["model"]], False) for e in panel(L) if e["model"] in pm]
    rows.append((ch["pooled_label"], fmt(ch["pooled_sublabel"], c), P, True))
    W, LB, rowH, top = 760, 170, 44, 26
    PL, PR = LB, W - 70
    H = top + len(rows) * rowH + 38
    lo = min(0, min(r[2]["ci"][0] for r in rows)) * 100
    hi = max(0, max(r[2]["ci"][1] for r in rows)) * 100
    pad = (hi - lo) * 0.12 or 2
    lo, hi = lo - pad, hi + pad
    step = 5 if hi - lo <= 40 else 10
    x = lambda v: PL + (v - lo) / (hi - lo) * (PR - PL)
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(ch["aria"])}">']
    for t in range(math.ceil(lo / step) * step, math.floor(hi / step) * step + 1, step):
        out.append(grid_line(x(t), top - 8, H - 28) + tick(x(t), H - 10, "0" if t == 0 else signed(t, 0)))
    out.append(zero_line(x(0), top - 8, H - 28) +
               f'<text x="{x(0):.1f}" y="{top - 13}" text-anchor="middle" fill="var(--muted)" {MONO} '
               f'font-size="9.5" letter-spacing="1">NO EFFECT</text>')
    for i, (name, sub, m, pooled) in enumerate(rows):
        dv, ci = m["delta"], m["ci"]
        y = top + i * rowH + rowH / 2 - 6
        col = colour(dv, ci)
        X = x(dv * 100)
        tip = (f"{name} · {sub}\n{pts(dv)} pts  {ci_pts(ci)}\n{p_text(m['p'])}"
               + ("" if sig(ci) else "\ninterval includes zero"))
        glyph = (f'<path d="M {X:.1f} {y - 8} L {X + 9:.1f} {y} L {X:.1f} {y + 8} L {X - 9:.1f} {y} Z" '
                 f'fill="{col}" stroke="var(--raised)" stroke-width="2"/>' if pooled else
                 f'<circle cx="{X:.1f}" cy="{y}" r="6" fill="{col}" stroke="var(--raised)" stroke-width="2"/>')
        if pooled:
            out.append(f'<line x1="0" y1="{y - rowH / 2 + 4:.1f}" x2="{W}" y2="{y - rowH / 2 + 4:.1f}" '
                       f'stroke="var(--line-2)" stroke-width="1"/>')
        out.append(
            hit(tip, y - rowH / 2 + 6, rowH) + engine_label(name, sub, y) +
            f'<line x1="{x(ci[0] * 100):.1f}" y1="{y}" x2="{x(ci[1] * 100):.1f}" y2="{y}" stroke="{col}" '
            f'stroke-width="2" stroke-linecap="round"/>' + glyph +
            (f'<text x="{x(ci[1] * 100) + 10:.1f}" y="{y + 5:.1f}" fill="var(--ink)" {MONO} font-size="13" '
             f'font-weight="600">{pts(dv)}</text>' if pooled else "") + "</g>")
    out.append(f'<text x="{W - 8}" y="{H - 10}" text-anchor="end" fill="var(--muted)" {MONO} '
               f'font-size="9.5">pts</text></svg>')
    return figure("".join(out), f, c)

def svg_pair(f, L, c):
    r, ch = f["data"]["rounds"][0], f["chart"]
    rows = [(ch["labels"][0], r["cross"], r["cross_ci"], True),
            (ch["labels"][1], r["within"], r["within_ci"], False)]
    W, LB, rowH, top = 760, 340, 40, 12
    PL, PR = LB, W - 70
    H = top + len(rows) * rowH + 36
    x = lambda v: PL + v * (PR - PL)
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(ch["aria"])}">']
    for t in (0, .2, .4, .6, .8, 1):
        out.append(grid_line(x(t), top - 4, H - 28) + tick(x(t), H - 10, f"{t:.1f}"))
    for i, (label, w, ci, solid) in enumerate(rows):
        y = top + i * rowH + rowH / 2
        out.append(
            hit(f"{label}\nW {w:.3f}  [{ci[0]:.3f}, {ci[1]:.3f}]", y - rowH / 2, rowH) +
            f'<text x="0" y="{y + 5:.1f}" fill="var(--ink)" font-size="14">{esc(label)}</text>'
            f'<line x1="{x(ci[0]):.1f}" y1="{y}" x2="{x(ci[1]):.1f}" y2="{y}" stroke="var(--ochre)" '
            f'stroke-width="2.5" stroke-linecap="round"/>'
            f'<circle cx="{x(w):.1f}" cy="{y}" r="6" fill="{"var(--ochre)" if solid else "var(--raised)"}" '
            f'stroke="var(--ochre)" stroke-width="2.5"/>'
            f'<text x="{x(ci[1]) + 10:.1f}" y="{y + 5:.1f}" fill="var(--ink)" {MONO} font-size="13" '
            f'font-weight="600">{w:.2f}</text></g>')
    return figure("".join(out) + "</svg>", f, c)

def units(f, L, c):
    ch = f["chart"]
    low, high = int(c["low_n"]), int(c["high_n"])
    cell, gap = 17, 4
    W = 10 * cell + 9 * gap
    rects = []
    for i in range(100):
        X, Y = (i % 10) * (cell + gap), (i // 10) * (cell + gap)
        fill = "var(--neg)" if i < low else "url(#hatch)" if i < high else "var(--raised)"
        stroke = "none" if i < high else "var(--line-2)"
        rects.append(f'<rect x="{X}" y="{Y}" width="{cell}" height="{cell}" rx="2" fill="{fill}" '
                     f'stroke="{stroke}" stroke-width="1"/>')
    grid = (f'<svg class="unitgrid" viewBox="0 0 {W} {W}" role="img" aria-label="{esc(fmt(ch["aria"], c))}">'
            '<defs><pattern id="hatch" width="5" height="5" patternUnits="userSpaceOnUse" '
            'patternTransform="rotate(45)"><rect width="5" height="5" fill="var(--neg-soft)"/>'
            '<line x1="0" y1="0" x2="0" y2="5" stroke="var(--neg)" stroke-width="2.2"/></pattern></defs>'
            + "".join(rects) + "</svg>")
    key_hatch = ('<svg class="ubox" viewBox="0 0 13 13" aria-hidden="true">'
                 '<rect width="13" height="13" rx="2" fill="url(#hatch)"/></svg>')
    legend = ('<div class="ulegend">'
              f'<div><i class="ubox" style="background:var(--neg)"></i><span>{fmt(ch["legend_low"], c)}</span></div>'
              f'<div>{key_hatch}<span>{fmt(ch["legend_high"], c)}</span></div>'
              f'<div><i class="ubox" style="border:1px solid var(--line-2)"></i>'
              f'<span>{fmt(ch["legend_rest"], c)}</span></div></div>')
    return f'<div class="units">{grid}{legend}</div>'

def calibration(f, L, c):
    ch, qs = f["chart"], f["data"]["questions"]
    group = lambda q: ("both" if q["api"] and q["web"] else "web" if q["web"] else
                       "api" if q["api"] else "none")
    cell = lambda ds: (f'<span class="cell"><i class="dot on"></i>{esc(", ".join(ds))}</span>' if ds else
                       f'<span class="cell"><i class="dot"></i><span class="none">{esc(ch["empty"])}</span></span>')
    out = ["<thead><tr>" + "".join(f"<th>{esc(h)}</th>" for h in ch["columns"]) + "</tr></thead><tbody>"]
    for g in ("both", "web", "api", "none"):
        members = [q for q in qs if group(q) == g]
        if not members:
            continue
        out.append(f'<tr class="grp"><td colspan="3">{esc(ch["groups"][g])} · {len(members)}</td></tr>')
        for q in members:
            cls = ' class="diff"' if g in ("web", "api") else ""
            out.append(f'<tr{cls}><td>{esc(q["q"])}</td><td>{cell(q["api"])}</td><td>{cell(q["web"])}</td></tr>')
    note = f["text"].get("note")
    return (f'<div class="scroll"><table class="cal">{"".join(out)}</tbody></table></div>'
            + (f'<p class="tnote">{fmt(note, c)}</p>' if note else ""))

def figure(inner, f, c):
    cap = f["text"].get("caption")
    return f"<figure>{inner}" + (f"<figcaption>{fmt(cap, c)}</figcaption>" if cap else "") + "</figure>"

CHARTS = {"dumbbell": svg_dumbbell, "forest": svg_forest, "interval_pair": svg_pair,
          "units": units, "calibration": calibration}


# ------------------------------------------------------------------ page
def chip(e, c):
    cls = {"strong": " strong", "early": " early"}.get(e.get("style"), "")
    return f'<span class="chip{cls}">{esc(fmt(e["label"], c))}</span>'

def prov_line(f, L, c):
    items = [f"<span>{fmt(s, c)}</span>" for s in f["text"].get("prov", [])]
    pv = f.get("provenance", {})
    links = [("full report", pv.get("report")), ("pre-registration", pv.get("preregistration"))]
    links += [(l["label"], l["path"]) for l in pv.get("links", [])]
    items += [f'<a href="{esc(repo_url(L, p))}">{esc(label)}</a>' for label, p in links if p]
    return f'<div class="prov">{"".join(items)}</div>'

def article(f, L, c):
    t = f["text"]
    parts = [f'<article class="finding" id="{esc(f["alias"])}"><div class="fhead">'
             f'{"".join(chip(e, c) for e in f["evidence"])}</div>',
             f'<h2>{esc(f["title"])}</h2>']
    parts += [f"<p>{fmt(s, c)}</p>" for s in t.get("body", [])]
    parts.append(CHARTS[f["chart"]["type"]](f, L, c))
    parts += [f'<p class="after">{fmt(s, c)}</p>' for s in t.get("after", [])]
    if t.get("for_you"):
        parts.append(f'<div class="foryou"><span class="k">For your content</span>'
                     f'<span class="v">{fmt(t["for_you"], c)}</span></div>')
    parts.append(prov_line(f, L, c) + "</article>")
    return "".join(parts)

def build(L, fragment=False):
    A, P, fctx = contexts(L)
    pg = L["page"]
    shown = sorted((f for f in L["findings"] if f.get("public") and f["status"] != "in_progress"),
                   key=lambda f: f["order"])
    pending = [f for f in L["findings"] if f.get("public") and f["status"] == "in_progress"]
    levers = [A[a] for a in pg["hero_levers"]]

    nav = ('<nav class="top"><a class="brand" href="index.html">OpenGEO</a><span>'
           '<a href="index.html">Overview</a><a href="findings.html" aria-current="page">Findings</a>'
           f'<a href="{esc(L["repo"])}">Repository</a></span></nav>')
    head = (nav + '<header><div class="eyebrow">' + "<span>·</span>".join(f"<span>{e}</span>" for e in pg["eyebrow"])
            + f'</div><h1>{esc(pg["headline"])}</h1><p class="standfirst">{fmt(pg["standfirst"], P)}</p></header>')
    hero = (f'<div class="hero"><p class="cap">{esc(pg["hero_caption"])}</p>{svg_hero(levers, fctx)}'
            f'<p class="note">{fmt(pg["hero_note"], P)}</p></div>')
    body = "".join(article(f, L, fctx[f["alias"]]) for f in shown)
    limits = (f'<section class="block"><h2>{esc(pg["limits_heading"])}</h2><ul class="limits">'
              + "".join(f"<li>{fmt(s, P)}</li>" for s in pg["limits"]) + "</ul></section>")
    method = (f'<section class="block"><h2>{esc(pg["method_heading"])}</h2><div class="method">'
              + "".join(f'<div><div class="k">{esc(m["k"])}</div><p>{fmt(m["text"], P)}</p></div>'
                        for m in pg["method"])
              + '</div><div class="links">'
              + "".join(f'<a href="{esc(repo_url(L, l["path"], l.get("tree", False)))}">{esc(l["label"])}</a>'
                        for l in pg["links"])
              + "</div>"
              + "".join(f'<p class="next"><b>Testing now</b>{esc(f["question_public"])}</p>' for f in pending)
              + "</section>")
    content = (f'<div class="wrap">{head}{hero}{body}{limits}{method}'
               f'<footer>{fmt(pg["footer"], P)}</footer></div>'
               f'<div class="tip" id="tip" role="status" aria-live="polite"></div><script>{TIP_JS}</script>')
    if fragment:
        return f'<title>{esc(pg["title"])}</title>{FONTS}<style>{CSS}</style>{content}\n'
    return ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(pg["title"])}</title><meta name="description" content="{esc(pg["description"])}">'
            f'{social_meta(L, pg["title"], pg["description"], "findings.html")}'
            f'{FONTS}<style>{CSS}</style></head><body>{content}</body></html>\n')


FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1'
         '&family=Public+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap">')

CSS = r"""
:root{--paper:#f6f2ea;--raised:#fffdf8;--sunk:#efe9dd;--ink:#191610;--ink-2:#3d372d;--muted:#7c746a;
  --line:#e0d9cb;--line-2:#cec5b3;--ochre:#a86c14;--ochre-soft:#f0e2c9;
  --pos:#0a7d60;--neg:#ab3e20;--nil:#7c746a;--pos-soft:#dceae4;--neg-soft:#f4ded6}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --paper:#14120e;--raised:#1e1b15;--sunk:#100e0b;--ink:#f0ebe0;--ink-2:#c9c1b2;--muted:#948b7d;
  --line:#302b22;--line-2:#433c30;--ochre:#d9a04a;--ochre-soft:#3a2f1a;
  --pos:#35ab8d;--neg:#d4704f;--nil:#948b7d;--pos-soft:#1a3029;--neg-soft:#33201a}}
:root[data-theme="dark"]{
  --paper:#14120e;--raised:#1e1b15;--sunk:#100e0b;--ink:#f0ebe0;--ink-2:#c9c1b2;--muted:#948b7d;
  --line:#302b22;--line-2:#433c30;--ochre:#d9a04a;--ochre-soft:#3a2f1a;
  --pos:#35ab8d;--neg:#d4704f;--nil:#948b7d;--pos-soft:#1a3029;--neg-soft:#33201a}
*{box-sizing:border-box}
html{color-scheme:light dark}
body{margin:0;background:var(--paper);color:var(--ink);
  font:15.5px/1.62 "Public Sans",ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  -webkit-font-smoothing:antialiased}
.wrap{max-width:900px;margin:0 auto;padding:44px 24px 90px}
nav.top{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;
  font-family:"IBM Plex Mono",monospace;font-size:12px;margin:0 0 36px}
nav.top a{color:var(--muted);text-decoration:none;margin-left:16px}
nav.top a:first-child{margin-left:0}
nav.top a[aria-current],nav.top a:hover{color:var(--ink)}
nav.top .brand{color:var(--ink);font-weight:600;letter-spacing:.04em}
a{color:var(--ochre);text-underline-offset:2px}
a:focus-visible{outline:2px solid var(--ochre);outline-offset:2px}
.eyebrow{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.15em;text-transform:uppercase;
  color:var(--muted);display:flex;flex-wrap:wrap;gap:9px}
.eyebrow b{color:var(--ochre);font-weight:600}
h1{font-family:"Instrument Serif",Georgia,serif;font-weight:400;font-size:clamp(34px,5.6vw,50px);
  line-height:1.04;letter-spacing:-.015em;margin:16px 0 0;text-wrap:balance;max-width:18ch}
.standfirst{font-size:17px;line-height:1.56;color:var(--ink-2);max-width:62ch;margin:18px 0 0}
.hero{margin:34px 0 0;padding:20px 22px 16px;background:var(--raised);border:1px solid var(--line);border-radius:4px}
.hero .cap{font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.13em;text-transform:uppercase;
  color:var(--muted);margin:0 0 6px}
.hero .note{font-size:12.5px;color:var(--muted);margin:8px 0 0;max-width:72ch;line-height:1.55}
.finding{padding:48px 0 0;margin:48px 0 0;border-top:1px solid var(--line-2)}
.fhead{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:0 0 12px}
h2{font-family:"Instrument Serif",Georgia,serif;font-weight:400;font-size:clamp(25px,3.4vw,31px);
  line-height:1.14;letter-spacing:-.01em;margin:0 0 12px;text-wrap:balance;max-width:24ch}
.finding p{max-width:64ch;margin:0 0 12px;color:var(--ink-2)}
.finding p b{color:var(--ink)}
.finding p.after{margin-top:18px}
.chip{display:inline-flex;align-items:center;gap:6px;font-family:"IBM Plex Mono",monospace;font-size:10px;
  letter-spacing:.08em;text-transform:uppercase;font-weight:600;padding:3px 8px;border-radius:2px;
  border:1px solid var(--line-2);color:var(--ink-2);background:var(--raised)}
.chip.strong{border-color:var(--pos);color:var(--pos);background:var(--pos-soft)}
.chip.early{border-style:dashed}
.chip::before{content:"";width:6px;height:6px;border-radius:50%;background:currentColor}
figure{margin:20px 0 0}
figcaption{font-size:12.5px;color:var(--muted);margin:10px 0 0;max-width:70ch;line-height:1.55}
svg{display:block;width:100%;height:auto;overflow:visible}
.legend{display:flex;gap:18px;flex-wrap:wrap;font-size:12px;color:var(--ink-2);margin:0 0 6px;
  font-family:"IBM Plex Mono",monospace}
.legend span{display:inline-flex;align-items:center;gap:7px}
.sw{width:11px;height:11px;border-radius:50%;display:inline-block}
.foryou{margin:20px 0 0;display:grid;grid-template-columns:auto 1fr;gap:4px 14px;max-width:66ch}
.foryou .k{font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.13em;text-transform:uppercase;
  color:var(--ochre);font-weight:600;padding-top:3px;white-space:nowrap}
.foryou .v{color:var(--ink);font-size:15px}
.prov{margin:16px 0 0;font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--muted);
  display:flex;flex-wrap:wrap;gap:6px 14px;line-height:1.5}
.units{display:flex;gap:26px;flex-wrap:wrap;align-items:center;margin:20px 0 0}
.unitgrid{width:210px;flex:none}
.ulegend{display:flex;flex-direction:column;gap:10px;font-size:13.5px;color:var(--ink-2);max-width:40ch}
.ulegend div{display:flex;gap:10px;align-items:flex-start}
.ulegend .big{font-family:"IBM Plex Mono",monospace;font-size:22px;font-weight:600;color:var(--ink);
  letter-spacing:-.02em;line-height:1}
.ubox{width:13px;height:13px;flex:none;margin-top:3px;border-radius:2px;display:inline-block}
.scroll{overflow-x:auto;margin:20px 0 0}
table.cal{border-collapse:collapse;width:100%;min-width:620px;font-size:13px}
table.cal th{font-family:"IBM Plex Mono",monospace;font-size:9.5px;letter-spacing:.11em;text-transform:uppercase;
  color:var(--muted);text-align:left;font-weight:600;padding:0 10px 8px;border-bottom:1px solid var(--line-2)}
table.cal td{padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:middle}
table.cal tr.grp td{font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.1em;
  text-transform:uppercase;color:var(--muted);padding-top:16px;border-bottom:1px solid var(--line-2)}
table.cal tr.diff td{background:var(--ochre-soft)}
.cell{display:inline-flex;align-items:center;gap:8px;font-family:"IBM Plex Mono",monospace;font-size:11.5px;
  color:var(--ink-2)}
.dot{width:10px;height:10px;border-radius:50%;flex:none;border:2px solid var(--ochre)}
.dot.on{background:var(--ochre)}
.none{color:var(--muted);font-style:italic;font-family:"Public Sans",sans-serif;font-size:12.5px}
.tnote{font-size:12.5px;color:var(--muted);margin:10px 0 0;max-width:70ch}
section.block{margin:64px 0 0;padding:28px 0 0;border-top:1px solid var(--line-2)}
section.block h2{font-size:26px;max-width:none}
.limits{list-style:none;padding:0;margin:14px 0 0;display:grid;gap:14px}
.limits li{max-width:66ch;color:var(--ink-2);padding-left:22px;position:relative}
.limits li::before{content:"";position:absolute;left:2px;top:.62em;width:9px;height:2px;background:var(--neg)}
.limits b{color:var(--ink)}
.method{display:grid;gap:1px;background:var(--line);border:1px solid var(--line);border-radius:4px;
  overflow:hidden;margin:18px 0 0;grid-template-columns:repeat(auto-fit,minmax(200px,1fr))}
.method>div{background:var(--raised);padding:15px 16px}
.method .k{font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.12em;text-transform:uppercase;
  color:var(--ochre);font-weight:600;margin-bottom:6px}
.method p{margin:0;font-size:13.5px;line-height:1.55;color:var(--ink-2)}
.num{font-family:"IBM Plex Mono",monospace;color:var(--ink);font-weight:600}
.links{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0 0}
.links a{font-family:"IBM Plex Mono",monospace;font-size:12px;padding:7px 11px;border:1px solid var(--line-2);
  border-radius:3px;text-decoration:none;color:var(--ink-2);background:var(--raised)}
.links a:hover{border-color:var(--ochre);color:var(--ochre)}
.next{margin:30px 0 0;font-size:14.5px;color:var(--ink-2);max-width:66ch}
.next b{font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.12em;text-transform:uppercase;
  color:var(--muted);font-weight:600;margin-right:8px}
footer{margin-top:56px;padding-top:18px;border-top:1px solid var(--line);color:var(--muted);font-size:12px;
  line-height:1.65;max-width:74ch}
.tip{position:fixed;pointer-events:none;z-index:9;background:var(--ink);color:var(--paper);
  font-family:"IBM Plex Mono",monospace;font-size:11px;line-height:1.5;padding:7px 9px;border-radius:3px;
  opacity:0;transition:opacity .09s;max-width:260px;white-space:pre-line}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
"""

TIP_JS = r"""
(function(){var t=document.getElementById("tip");
document.addEventListener("mouseover",function(e){var g=e.target.closest("[data-tip]");
  if(!g){t.style.opacity=0;return}t.textContent=g.dataset.tip;t.style.opacity=1});
document.addEventListener("mousemove",function(e){if(t.style.opacity==="0")return;
  var w=t.offsetWidth,h=t.offsetHeight;
  t.style.left=Math.min(e.clientX+14,innerWidth-w-8)+"px";t.style.top=Math.max(e.clientY-h-14,8)+"px"})})();
"""


ROUND_MARKERS = ("<!-- rounds:start -->", "<!-- rounds:end -->")


def write_round_index(L, root):
    """Refresh the generated round list inside results/published/README.md.

    Same rule as the page: the index of what has been published is derived from the
    ledger, so it cannot drift out of step with the rounds themselves."""
    path = root / "results" / "published" / "README.md"
    if not path.exists():
        return None
    text = path.read_text()
    start, end = ROUND_MARKERS
    if start not in text or end not in text:
        return None

    by_report = {}
    for f in L["findings"]:
        report = f.get("provenance", {}).get("report")
        if f.get("public") and report:
            by_report.setdefault(report, []).append(f)

    lines = []
    for report in sorted(by_report, reverse=True):
        folder = report.rsplit("/", 2)[-2]
        date, name = folder[:10], folder[11:]
        # Not every published result tests a numbered hypothesis. Probe-level work --
        # below the prompt floor, design committed but no H-number -- is indexed by its
        # status instead. Inventing an H-number for it would imply a pre-registered
        # hypothesis test it never was.
        entries = sorted(by_report[report], key=lambda x: x["order"])
        ids = ", ".join(dict.fromkeys(
            f.get("hypothesis") or f["status"] for f in entries))
        lines.append(f"- **{date} — {name}** · [report]({folder}/REPORT.md) · {ids}")

    body = "\n".join(lines)
    path.write_text(re.sub(re.escape(start) + r".*?" + re.escape(end),
                           f"{start}\n\n{body}\n\n{end}", text, flags=re.S))
    return len(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--ledger", default=str(HERE / "results" / "findings.json"))
    ap.add_argument("-o", "--out", default=str(ROOT / "docs" / "findings.html"),
                    help="where the findings page goes; the story always goes to docs/index.html")
    ap.add_argument("--check", action="store_true", help="validate only; write nothing")
    ap.add_argument("--fragment", action="store_true", help="findings page only, without <html>/<head>/<body>")
    args = ap.parse_args()

    L = json.loads(pathlib.Path(args.ledger).read_text())
    errors, warnings = validate(L, ROOT)
    for w in warnings:
        print(f"  note  {w}")
    if errors:
        for e in errors:
            print(f"  FAIL  {e}")
        sys.exit(f"{len(errors)} problem(s) in {args.ledger}; nothing written.")
    n_asserts = sum(len(f.get("asserts", [])) for f in L["findings"])
    print(f"ledger ok: {len(L['findings'])} entries, {n_asserts} assertions hold, {len(warnings)} note(s)")
    if args.check:
        return

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(L, fragment=args.fragment))
    n_rounds = None if args.fragment else write_round_index(L, HERE)
    shown = sum(1 for f in L["findings"] if f.get("public") and f["status"] != "in_progress")
    print(f"wrote {out}  ({shown} findings public, "
          f"{sum(1 for f in L['findings'] if not f.get('public'))} kept off the page)")
    if not args.fragment and L.get("story"):
        import build_story
        _, cases = build_story.check(L)
        story = ROOT / "docs" / "index.html"
        story.write_text(build_story.build(L, cases))
        print(f"wrote {story}  (the story; {len(cases)} worked examples checked against the raw runs)")
        assets = ROOT / "docs" / "assets"
        assets.mkdir(exist_ok=True)
        for mode in ("light", "dark"):
            (assets / f"effects-{mode}.svg").write_text(build_story.effects_svg(L, mode))
        print(f"wrote {assets}/effects-{{light,dark}}.svg  (the README's chart)")
        if build_story.write_readme(L, ROOT / "README.md"):
            print("wrote README.md  (the findings section between its markers)")
    if n_rounds:
        print(f"wrote experiments/results/published/README.md  ({n_rounds} published rounds indexed)")


if __name__ == "__main__":
    main()
