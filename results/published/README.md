# Published rounds

Immutable, dated result sets backing a publication. Never overwrite one — engines drift, so
a round is a snapshot, not a dashboard.

Raw responses live in `results/` as `runs_*.jsonl` and are referenced by each report rather
than copied in here, to avoid carrying a second 50MB+ copy of the same data. The raw data
being downloadable is the differentiator over every commercial competitor.

The list below is generated from `results/findings.json` by `build_findings.py` — don't edit
it by hand.

<!-- rounds:start -->

- **2026-09-22 — public-private** · [report](2026-09-22-public-private/REPORT.md) · H8
- **2026-09-20 — tier1-scope** · [report](2026-09-20-tier1-scope/REPORT.md) · null
- **2026-09-11 — lengthonly** · [report](2026-09-11-lengthonly/REPORT.md) · H7
- **2026-08-30 — calibration-v1** · [report](2026-08-30-calibration-v1/REPORT.md) · CAL-1
- **2026-08-29 — kwstuff-v3** · [report](2026-08-29-kwstuff-v3/REPORT.md) · H6, H3, C2 baseline
- **2026-08-25 — corpus-v0.4-exploratory** · [report](2026-08-25-corpus-v0.4-exploratory/REPORT.md) · H4

<!-- rounds:end -->
