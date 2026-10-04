# Pre-registrations

One file per benchmark round, committed **before** data collection begins.

Each must state: hypotheses, corpus version and hash, model list, runs per cell,
primary metric, analysis plan, and stopping rule.

The git timestamp on the commit is the evidence. A pre-registration committed after
the first row of `results/runs.jsonl` is not a pre-registration.

Two rules that exist because a round went wrong first. Both are in `METHODOLOGY.md` §5.3:

- A **pre-committed spot check** runs after the pre-registration and before the full round:
  a few hundred calls confirming the baseline is not at a ceiling or floor. It is a go/no-go
  gate on the design, never a look at the result.
- **Deviations are logged in the pre-registration itself**, dated, before analysis —
  including the uncomfortable ones, such as outcome data having been seen before a decision.
