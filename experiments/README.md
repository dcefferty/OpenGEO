# The benchmark

Everything behind the published rounds: each round's corpus, pre-registration, raw model
responses and report, and the code that builds, runs, analyses and publishes it. The
standard all of it follows is [`METHODOLOGY.md`](../METHODOLOGY.md).

Commands run from this folder, and paths in the scripts, pre-registrations and reports are
relative to it:

```bash
cd experiments
python3 run_pilot.py --dry-run          # cost estimate, no API calls
python3 build_findings.py --check       # validate the findings ledger
```

The one exception is the findings ledger, `results/findings.json`: it also points at files
outside this folder, so its paths are relative to the repository root.

Rounds published before October 2026 were written when these files sat at the repository
root. Nothing in here moved relative to anything else, so their commands work as written
from this folder. `git log --follow <file>` traces a file's history across the move,
including when each pre-registration was committed.

| Path | What it is |
|---|---|
| `corpus/` | The corpus builders and the corpora they generate. Document text lives in the builders; the JSON is generated and hashed |
| `preregistrations/` | One file per round, committed **before** collection. The git timestamp is the evidence |
| `results/` | Raw responses, the findings ledger (`findings.json`), and the published reports (`published/`) |
| `run_pilot.py` | Tier 1 runner: queries the engines through OpenRouter, resumable, logs full provenance per call |
| `analyze.py` | Metrics and hypothesis tests — permutation and bootstrap only |
| `analyze_*.py` | Analyses for single rounds and probes: length-only (H7), public/private, the item-11 probes, the tactic pilot and the length ladder |
| `make_mock.py` | Synthetic runs with known planted effects, which `analyze.py` must recover before any money is spent |
| `size_round1.py` | Power sizing |
| `check_variants.py`, `screen.py` | Corpus checks: variant manipulation checks, and target screening for rankable corpora |
| `engine_weights.py` | The engine panel and its market-share weights |
| `judge_fidelity.py`, `fidelity_baseline.py` | Group C fidelity judging and its baseline |
| `calibration_api.py`, `calibration_prompts.py` | Calibration study, API plane |
| `build_findings.py`, `build_story.py` | Build the public pages in [`../docs/`](../docs/) and the README chart from `results/findings.json` |
| `check_private.py` | Leak check for the held-out private split — must pass before any publication (`METHODOLOGY.md` §10.1) |
| `private/` | The held-out private split. Gitignored: it exists only on the machine that holds it |

`opengeo test` ([`../opengeo.py`](../opengeo.py)) runs on this same harness, so a test of
your own page is made the way every round is.
