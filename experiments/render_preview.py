#!/usr/bin/env python3
"""
OpenGEO -- render the link-preview image, ../docs/assets/preview.png, from the ledger.

    python3 render_preview.py

It is what LinkedIn, X, Slack and the rest show when someone shares the site. The image is
drawn as SVG from the ledger (build_story.preview_svg); turning that into the PNG those
sites need takes a browser, which the build itself does not depend on, so it is a separate
step. The PNG records the hash of the SVG it was made from, and build_findings.py says so
when the ledger has moved on without it. Run this after a round changes the results.

Needs Google Chrome or Chromium. Standard library only.
"""
import json
import os
import pathlib
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import zlib

import build_findings as bf
import build_story as bs

BROWSERS = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "google-chrome", "chromium", "chromium-browser"]


def browser():
    for b in BROWSERS:
        path = b if "/" in b else shutil.which(b)
        if path and pathlib.Path(path).exists():
            return path
    sys.exit("No Chrome or Chromium found; one is needed to turn the preview SVG into a PNG.")


def wait_for_png(shot, proc, limit=90):
    """The screenshot, once it is complete. Chrome writes it within seconds but can linger
    afterwards (its updater keeps the process alive), so the screenshot is the signal, not
    the exit -- and the browser started here, with its helpers, is stopped once it is in."""
    try:
        deadline = time.monotonic() + limit
        while time.monotonic() < deadline:
            if shot.exists() and shot.read_bytes().endswith(b"IEND\xaeB`\x82"):
                return shot.read_bytes()
            if proc.poll() is not None and not shot.exists():
                sys.exit("Chrome exited without writing the screenshot; nothing written.")
            time.sleep(0.5)
        sys.exit(f"Chrome wrote no screenshot within {limit} seconds; nothing written.")
    finally:
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)


def with_text(png, key, value):
    """The PNG with a tEXt chunk added just before IEND."""
    body = key.encode("latin-1") + b"\0" + value.encode("latin-1")
    chunk = (len(body).to_bytes(4, "big") + b"tEXt" + body
             + zlib.crc32(b"tEXt" + body).to_bytes(4, "big"))
    end = png.rindex(b"IEND") - 4
    return png[:end] + chunk + png[end:]


def main():
    L = json.loads((bf.HERE / "results" / "findings.json").read_text())
    W, H = bs.PREVIEW_SIZE
    page = (f'<!doctype html><html><head><meta charset="utf-8">{bf.FONTS}'
            '<style>html,body{margin:0}svg{display:block}</style></head>'
            f'<body>{bs.preview_svg(L)}</body></html>')
    with tempfile.TemporaryDirectory() as tmp:
        src, shot = pathlib.Path(tmp) / "preview.html", pathlib.Path(tmp) / "preview.png"
        src.write_text(page)
        # A throwaway profile, so a Chrome the user has open is never touched; the time budget
        # lets the web fonts load before the screenshot is taken.
        proc = subprocess.Popen([browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                                 "--no-first-run", "--no-default-browser-check",
                                 f"--user-data-dir={tmp}/profile", f"--window-size={W},{H}",
                                 "--virtual-time-budget=10000", f"--screenshot={shot}", src.as_uri()],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                start_new_session=True)
        png = wait_for_png(shot, proc)
    size = (int.from_bytes(png[16:20], "big"), int.from_bytes(png[20:24], "big"))
    if size != (W, H):
        sys.exit(f"The browser produced a {size[0]}x{size[1]} image, not {W}x{H}; nothing written.")
    dest = bf.ROOT / bs.PREVIEW_PNG
    dest.write_bytes(with_text(png, bs.PREVIEW_KEY, bs.preview_hash(L)))
    print(f"wrote {bs.PREVIEW_PNG}  ({W}x{H}, {len(png) // 1024} KB)")


if __name__ == "__main__":
    main()
