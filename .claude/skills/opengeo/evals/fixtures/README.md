# Test fixtures

Fictional pages written to test the `opengeo` skill. Any resemblance to a real business is
coincidental.

- `current.html` and `edited.html`: a Tucson plumber's water-heater page, and the same page
  with prices added. `comp1-4.html` are four competitor pages. `edited_length_block.html`
  deliberately changes the length by more than three words, to test how the skill handles
  the tool's length check.
- `emergency.html` and `em_comp1-3.html`: a local, "near me" case, the kind of query the
  benchmark never covered.
- `running-store/`: a running-shoe store's fitting page, the same page with one sentence
  swapped for specific replacement guidance, and five competitor pages.
- `results-running-shoes/`: the real output of `opengeo test` 0.2.0 on `running-store/`,
  for the question "How often should I replace my running shoes?", run 2026-09-30 for
  $0.29. Every file is as the tool wrote it, including `runs.jsonl`. The report was
  regenerated from those same runs, with no new calls, after the tool's interval method
  changed (`design/opengeo-test.md`, 0.2.0).

Every page has a `<title>`, as real pages do; the tool shows each page's title to the
engines with its excerpt.
