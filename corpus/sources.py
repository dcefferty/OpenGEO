#!/usr/bin/env python3
"""
OpenGEO -- source snapshots and the verbatim check for real-text corpora.

A real-text corpus attributes every document to a named agency. That attribution is
only honest if each excerpt is the agency's words, character for character. The
item-11 feasibility probes did not meet that bar: excerpts were extended with
sentences written to reach a target length, and the builders still labelled them
"verbatim US federal text". This module makes the bar mechanical instead of a matter
of care, so it cannot be missed the same way twice.

Two pieces:

  snapshot   fetch a page once, keep its visible text with URL, retrieval time and
             sha256 under corpus/sources/. The snapshot, not the live page, is what
             an excerpt is checked against -- live pages change, and a check that
             depends on today's version of a URL is not reproducible.

  verbatim   an excerpt passes only if it appears in its snapshot as a contiguous
             run of text, after normalising whitespace and typographic punctuation
             (which HTML extraction mangles). Case, words and word order must match.
             A failing excerpt reports which of its sentences are not in the source.

## Fetching

Federal sites differ in what they block. Measured 2026-09-13 with a browser
User-Agent: fda.gov, ers.usda.gov, ncbi.nlm.nih.gov, consumer.ftc.gov, myplate.gov
and consumerfinance.gov serve curl; cdc.gov and nhtsa.gov return 403 to any
non-browser client; studentaid.gov serves a JavaScript shell with no content.

`fetch` uses curl, which reaches more of these than urllib does (CFPB rejects
urllib's TLS fingerprint but not curl's), and falls back to the Internet Archive for
the rest. Measured 2026-09-15, captures exist and serve curl for cdc.gov, ssa.gov,
fsis.usda.gov, ods.od.nih.gov and nhtsa.gov; energy.gov 403s at the Archive too. An
archived capture also gives a permanently citable, timestamped URL, which is better
provenance than a local snapshot alone -- but it may predate the live page, so the
capture date is recorded per document. Do not use a summarising fetch tool: its output
passes through a model, and paraphrase is exactly what this module exists to catch.

    python3 corpus/sources.py fetch URL [URL ...]
    python3 corpus/sources.py find URL KEYWORD [KEYWORD ...]
    python3 corpus/sources.py check          # verify every registered corpus
"""
import hashlib
import html
import html.parser
import json
import pathlib
import re
import subprocess
import sys
import time
import urllib.parse
from datetime import datetime, timezone

SOURCES = pathlib.Path(__file__).parent / "sources"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

SKIP = {"script", "style", "noscript", "svg", "template"}
BLOCK = {"p", "div", "li", "br", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "td",
         "th", "section", "article", "header", "footer", "dd", "dt", "blockquote"}


class _Text(html.parser.HTMLParser):
    """Visible text of a page. Deliberately keeps everything outside script/style:
    the check needs the excerpt to be findable, and trimming to a guessed 'main
    content' region risks dropping the very paragraph being quoted."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            self.skip += 1
        elif tag in BLOCK:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in SKIP and self.skip:
            self.skip -= 1
        elif tag in BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)


def visible_text(raw_html):
    p = _Text()
    p.feed(raw_html)
    text = html.unescape("".join(p.out))
    return re.sub(r"[ \t\r\f\v]+", " ", re.sub(r"\n\s*\n+", "\n\n", text)).strip()


def key_for(url):
    return hashlib.sha256(url.encode()).hexdigest()[:16]


# Known non-federal content served from federal domains. The snapshot store is committed,
# so saving one of these redistributes copyrighted text even if no corpus ever quotes it.
# This is a guard against the traps already found, NOT a rights check: a page that passes
# it still needs its rights established per document in the corpus builder.
NOT_FEDERAL = {
    "A.D.A.M., Inc": "MedlinePlus Medical Encyclopedia content licensed from A.D.A.M., Inc.",
}


class RightsError(ValueError):
    pass


def save_text(url, text, method, http_status=None, extra=None):
    """Store a snapshot. `method` records how the text was obtained, so a reader can
    tell a curl fetch from a browser extraction. `extra` carries method-specific
    provenance, such as the URL a browser actually landed on after redirects."""
    for marker, why in NOT_FEDERAL.items():
        if marker in text:
            raise RightsError(f"not snapshotting {url}: {why}")
    SOURCES.mkdir(exist_ok=True)
    snap = {
        "url": url,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "method": method,
        "http_status": http_status,
        "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "chars": len(text),
        **(extra or {}),
        "text": text,
    }
    path = SOURCES / f"{key_for(url)}.json"
    path.write_text(json.dumps(snap, indent=1, ensure_ascii=False) + "\n")
    return path


def _curl(url, timeout=25):
    """(status, body). status is None if curl itself failed."""
    try:
        r = subprocess.run(
            ["curl", "-s", "-L", "--compressed", "--max-time", str(timeout), "-A", UA,
             "-H", "Accept: text/html,application/xhtml+xml",
             "-H", "Accept-Language: en-US,en;q=0.9",
             "-w", "\n__HTTP_STATUS__%{http_code}", url],
            capture_output=True, timeout=timeout + 15)
    except subprocess.TimeoutExpired:
        return None, ""
    body = r.stdout.decode("utf-8", errors="replace")
    body, _, status = body.rpartition("\n__HTTP_STATUS__")
    return (int(status) if status.isdigit() else None), body


# The Internet Archive is the fallback for federal sites that refuse non-browser clients:
# cdc.gov, ssa.gov, fsis.usda.gov, ods.od.nih.gov and nhtsa.gov all serve captures even
# though they 403 a direct fetch, and between them they carry health, retirement, food
# safety and automotive -- domains the corpus otherwise cannot reach at all.
#
# Two details matter. The capture must be requested with the "id_" modifier, which
# returns the originally archived bytes; without it the Archive injects its own toolbar
# into the HTML, and that banner would land inside the snapshot and could be quoted into
# an excerpt. And the CDX index, not the availability API, is used to find a capture --
# the availability API rate-limits almost immediately and reports "no snapshot" when it
# does, which reads as a missing page rather than a throttled request.
WAYBACK_CDX = "https://web.archive.org/cdx/search/cdx"
ARCHIVE_PAUSE = 3.0
_last_archive_call = [0.0]


def _archive_wait():
    delta = time.monotonic() - _last_archive_call[0]
    if delta < ARCHIVE_PAUSE:
        time.sleep(ARCHIVE_PAUSE - delta)
    _last_archive_call[0] = time.monotonic()


def wayback_capture(url):
    """Most recent archived capture that returned 200, as (timestamp, fetch URL), or None."""
    _archive_wait()
    q = urllib.parse.urlencode({"url": url, "output": "json", "filter": "statuscode:200",
                                "collapse": "digest", "limit": "-1"})
    status, body = _curl(f"{WAYBACK_CDX}?{q}", timeout=30)
    if status != 200 or not body.strip():
        return None
    try:
        rows = json.loads(body)
    except ValueError:
        return None
    if len(rows) < 2:                      # row 0 is the header
        return None
    ts = rows[-1][1]
    return ts, f"https://web.archive.org/web/{ts}id_/{url}"


def fetch(url, min_chars=400, allow_archive=True):
    """Snapshot a page's visible text, preferring a direct fetch and falling back to the
    Internet Archive. Returns (path, None) on success or (None, reason).

    Rejected: a non-200, a timeout, or a page too thin to be real content -- the
    JavaScript-shell case, which would otherwise be saved as an empty but valid snapshot.

    The snapshot is always keyed by the ORIGINAL url, so a document refers to the agency's
    page whether the text came from the live site or an archived capture; where it came
    from is recorded in the snapshot's method and archive fields."""
    status, body = _curl(url)
    direct_problem = (f"HTTP {status}" if status is not None else "timeout")
    if status == 200:
        text = visible_text(body)
        if len(text) >= min_chars:
            try:
                return save_text(url, text, "curl", status), None
            except RightsError as e:
                return None, str(e)
        direct_problem = f"only {len(text)} visible chars -- likely a JavaScript shell"

    if not allow_archive:
        return None, direct_problem

    cap = wayback_capture(url)
    if cap is None:
        return None, f"{direct_problem}; no archived capture"
    ts, archive_url = cap
    _archive_wait()
    a_status, a_body = _curl(archive_url, timeout=45)
    if a_status != 200:
        return None, f"{direct_problem}; archive returned HTTP {a_status}"
    text = visible_text(a_body)
    if len(text) < min_chars:
        return None, f"{direct_problem}; archived capture only {len(text)} visible chars"
    try:
        path = save_text(url, text, "wayback id_",
                         extra={"archive_url": archive_url, "archive_timestamp": ts,
                                "direct_fetch_failed": direct_problem})
        return path, None
    except RightsError as e:
        return None, str(e)


def load(url):
    path = SOURCES / f"{key_for(url)}.json"
    return json.loads(path.read_text()) if path.exists() else None


# ---------------------------------------------------------------- verbatim check

_PUNCT = str.maketrans({
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2032": "'",
    "\u2013": "-", "\u2014": "-", "\u2212": "-", "\u00a0": " ", "\u2009": " ",
    "\u202f": " ", "\u2026": "...",
})


def norm(s):
    return re.sub(r"\s+", " ", s.translate(_PUNCT)).strip()


def sentences(s):
    return [x for x in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])", norm(s)) if x]


def verbatim(excerpt, source_text):
    """(True, []) if the excerpt is a contiguous run of the source; otherwise
    (False, [sentences not found in the source at all]). A failure with an empty list
    means every sentence exists but not as one contiguous run -- stitched from
    separate places -- which is still not a quotation."""
    src = norm(source_text)
    if norm(excerpt) in src:
        return True, []
    return False, [s for s in sentences(excerpt) if s not in src]


class SpanError(ValueError):
    pass


def _flatten(text):
    """Punctuation-normalised text on one line, plus the positions where a block
    boundary (paragraph, list item, heading) was joined into a space."""
    lines = [re.sub(r"\s+", " ", ln.translate(_PUNCT)).strip() for ln in text.split("\n")]
    flat, breaks, pos = [], set(), 0
    for ln in lines:
        if not ln:
            continue
        if flat:
            breaks.add(pos)
            pos += 1                      # the joining space
        flat.append(ln)
        pos += len(ln)
    return " ".join(flat), breaks


def span(url, start, end, multi_block=False):
    """Extract an excerpt from a source snapshot as the run of text from `start` through
    `end`, inclusive. The excerpt is sliced out of the snapshot, never retyped, so it
    cannot drift from the source.

    Fails if the snapshot is missing, if `start` is absent or appears more than once
    (an ambiguous anchor could silently select the wrong passage), if `end` does not
    follow it, or -- unless `multi_block` -- if the span crosses a block boundary, which
    is how headings, navigation and list debris end up inside an excerpt unnoticed.

    The returned text has whitespace collapsed and typographic punctuation normalised
    to ASCII. Words, numbers, case and order are exactly the source's."""
    snap = load(url)
    if snap is None:
        raise SpanError(f"no snapshot for {url} -- fetch it first")
    flat, breaks = _flatten(snap["text"])
    a, b = norm(start), norm(end)
    n = flat.count(a)
    if n != 1:
        raise SpanError(f"start anchor found {n} times in {url}: {start[:60]!r}")
    i = flat.index(a)
    j = flat.find(b, i + len(a) - len(b) if b in a else i)
    if j < 0:
        raise SpanError(f"end anchor not found after start in {url}: {end[:60]!r}")
    j += len(b)
    excerpt = flat[i:j]
    marker = re.search(r"\[\s*\d+(?:\s*[,\u2013-]\s*\d+)*\s*\]", excerpt)
    if marker:
        # run_pilot.py asks engines to cite as [1], [3]. A source reference marker left
        # in an excerpt is one an engine can copy into its answer, crediting a document
        # with a citation it did not earn. Reject rather than strip: stripping would
        # alter the source text, and a span that avoids the marker is almost always
        # available.
        raise SpanError(f"span contains a bracketed reference marker {marker.group()!r}, "
                        f"which collides with the harness's [n] citation syntax: {start[:50]!r}")
    if not multi_block and any(i < k < j for k in breaks):
        raise SpanError(f"span crosses a block boundary in {url}; choose a passage within "
                        f"one paragraph or pass multi_block=True: {start[:50]!r}")
    return excerpt


def passages(url, *keywords, min_words=12):
    """Blocks of a snapshot containing any keyword (case-insensitive), for choosing an
    excerpt. Returned as they will be sliced by span(), so an anchor copied from here
    resolves. Short blocks -- navigation, labels, table cells -- are skipped."""
    snap = load(url)
    if snap is None:
        return []
    flat, breaks = _flatten(snap["text"])
    edges = [0] + sorted(breaks) + [len(flat)]
    blocks = [flat[a:b].strip() for a, b in zip(edges, edges[1:])]
    kws = [k.lower() for k in keywords]
    return [b for b in blocks
            if len(b.split()) >= min_words and any(k in b.lower() for k in kws)]


def check_documents(docs):
    """docs: iterable of dicts with 'doc_id', 'url', 'text'. Returns a list of
    (doc_id, status, detail) for every document that does not pass."""
    problems = []
    for d in docs:
        snap = load(d["url"])
        if snap is None:
            problems.append((d["doc_id"], "NO SNAPSHOT", d["url"]))
            continue
        ok, missing = verbatim(d["text"], snap["text"])
        if not ok:
            detail = missing or ["all sentences present, but not as one contiguous passage"]
            problems.append((d["doc_id"], "NOT VERBATIM", detail))
    return problems


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "find":
        for i, b in enumerate(passages(sys.argv[2], *sys.argv[3:])):
            print(f"[{i}] ({len(b.split())} words) {b}\n")
    elif len(sys.argv) >= 3 and sys.argv[1] == "fetch":
        for u in sys.argv[2:]:
            path, err = fetch(u)
            print(f"  {'ok  ' if path else 'FAIL'}  {u}" + (f"  ({err})" if err else ""))
    else:
        print(__doc__)
