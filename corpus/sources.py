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
urllib's TLS fingerprint but not curl's). For pages curl cannot reach, extract the
rendered text in a real browser (`document.body.innerText`) and store it with
`save_text`, recording how it was obtained. Do not use a summarising fetch tool: its
output passes through a model, and paraphrase is exactly what this module exists to
catch.

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


def save_text(url, text, method, http_status=None):
    """Store a snapshot. `method` records how the text was obtained, so a reader can
    tell a curl fetch from a browser extraction."""
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
        "text": text,
    }
    path = SOURCES / f"{key_for(url)}.json"
    path.write_text(json.dumps(snap, indent=1, ensure_ascii=False) + "\n")
    return path


def fetch(url, min_chars=400):
    """Fetch with curl and snapshot the visible text. Returns (path, None) on success or
    (None, reason) -- a 403, a timeout, or a page too thin to be real content (the
    JavaScript-shell case), which would otherwise pass as an empty but valid fetch."""
    try:
        r = subprocess.run(
            ["curl", "-s", "-L", "--compressed", "--max-time", "25", "-A", UA,
             "-H", "Accept: text/html,application/xhtml+xml",
             "-H", "Accept-Language: en-US,en;q=0.9",
             "-w", "\n__HTTP_STATUS__%{http_code}", url],
            capture_output=True, timeout=40)
    except subprocess.TimeoutExpired:
        return None, "timeout"
    body = r.stdout.decode("utf-8", errors="replace")
    body, _, status = body.rpartition("\n__HTTP_STATUS__")
    status = int(status) if status.isdigit() else None
    if status != 200:
        return None, f"HTTP {status}"
    text = visible_text(body)
    if len(text) < min_chars:
        return None, f"only {len(text)} visible chars -- likely a JavaScript shell"
    try:
        return save_text(url, text, "curl", status), None
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
