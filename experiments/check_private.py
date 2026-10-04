#!/usr/bin/env python3
"""
OpenGEO -- leak check for the held-out private split (ROADMAP item 10).

The private split is a contamination defence: questions the public corpus does not
contain, so a result that holds on both is not an artefact of the public set having been
seen. Its entire value rests on never being published, and publication here is
irreversible in a way most mistakes are not -- **git history is permanent, and this
project's history is its pre-registration evidence.** A private question committed once
cannot be made private again without rewriting the history that proves when each round was
pre-registered, and that evidence is not tradeable.

So the split lives outside the repo, under `experiments/private/`, which is gitignored. This script is
the thing that notices when that has gone wrong. It runs three checks:

  ignored     `private/` is actually matched by .gitignore
  untracked   nothing under `private/` is tracked by git, now or in HEAD
  no leak     no private prompt_id appears in any tracked file

The third is the one that catches real mistakes. A private question leaks by being
*mentioned* -- in a roadmap note, a pre-registration, a probe write-up, a commit message --
far more easily than by having its corpus committed.

Run it before any publish, and before making the repository public:

    python3 check_private.py

Exits non-zero on a leak. Says so plainly and exits zero when no split exists yet.
"""
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent              # a leak anywhere in the repository counts, not only in here
PRIVATE = HERE / "private"
PRIVATE_REL = PRIVATE.relative_to(ROOT).as_posix()
MANIFEST = PRIVATE / "MANIFEST.json"


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args],
                          capture_output=True, text=True).stdout.splitlines()


def main():
    problems, notes = [], []

    if not PRIVATE.exists():
        print(f"no {PRIVATE_REL}/ directory -- no split exists yet.")
        print("ROADMAP item 10 is open; this check passes vacuously.")
        return 0

    # 1. gitignore actually covers it
    ignored = subprocess.run(["git", "-C", str(ROOT), "check-ignore", "-q",
                              f"{PRIVATE_REL}/x"])
    if ignored.returncode != 0:
        problems.append(f"{PRIVATE_REL}/ is NOT matched by .gitignore -- add it before "
                        "anything else, then re-run")

    # 2. nothing under private/ is tracked
    tracked = [p for p in git("ls-files", PRIVATE_REL) if p.strip()]
    if tracked:
        problems.append(f"{len(tracked)} file(s) under {PRIVATE_REL}/ are TRACKED BY GIT: "
                        + ", ".join(tracked[:5]))

    # 3. no private prompt_id appears in a tracked file
    if not MANIFEST.exists():
        notes.append(f"no {MANIFEST.relative_to(HERE)} -- cannot check for id leaks. "
                     "Create it listing the private prompt_ids.")
    else:
        man = json.loads(MANIFEST.read_text())
        ids = [str(i) for i in man.get("prompt_ids", [])]
        if not ids:
            notes.append("MANIFEST.json lists no prompt_ids yet")
        all_tracked = [p for p in git("ls-files") if p.strip()]
        for pid in ids:
            hits = []
            for path in all_tracked:
                f = ROOT / path
                try:
                    if pid in f.read_text(errors="ignore"):
                        hits.append(path)
                except (OSError, UnicodeDecodeError):
                    continue
            if hits:
                problems.append(f"private prompt_id {pid!r} appears in tracked file(s): "
                                + ", ".join(hits[:4]))
        # commit messages leak just as effectively as files
        for pid in ids:
            if git("log", "--all", "--oneline", f"--grep={pid}"):
                problems.append(f"private prompt_id {pid!r} appears in a COMMIT MESSAGE; "
                                "history is permanent, so this id is burned -- replace "
                                "that question in the split")
        if ids and not problems:
            notes.append(f"{len(ids)} private prompt_id(s) checked against "
                         f"{len(all_tracked)} tracked files and all commit messages")

    for n in notes:
        print(f"note: {n}")
    if problems:
        print("\nPRIVATE SPLIT LEAK:")
        for p in problems:
            print(f"  - {p}")
        print("\nDo not publish until these are clear.")
        return 1
    print("private split: no leaks found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
