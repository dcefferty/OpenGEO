#!/usr/bin/env python3
"""
OpenGEO -- engine market-share weights.

This benchmark exists to tell someone what to change about their content. That
person does not care equally about every model: their traffic is not split
evenly across engines, so an unweighted pool over the panel silently asserts an
equal split that is false by roughly an order of magnitude.

**Per-engine results remain primary.** They are what this project actually
measures and the only part that is reproducible from its own data. The weighted
pool below is a convenience for the "what should I do" question, and it is a
*parameter*, not a finding.

## The epistemic problem, stated plainly

`CLAUDE.md` rejects vendor-panel numbers because nobody outside the vendor can
verify them. These weights are vendor-panel numbers. Similarweb's AI Studio
series is third-party, dated, methodologically described, and covers all seven
platforms on one consistent basis -- which makes it the best available, not
verifiable. Using it to weight a benchmark built on reproducibility is a real
tension, and the resolution is: the weights live in this file, carry their
source and date, and can be replaced in one edit. A reader who distrusts them
can supply their own or read the per-engine table and ignore the pool entirely.

Do not treat a weighted pooled figure as more authoritative than the per-engine
numbers it is computed from.

## Source

Similarweb Gen AI worldwide all-device website traffic share, August 2026.
Copilot is folded into the GPT family because it is OpenAI-backed, so a content
change that moves GPT moves Copilot too.

Perplexity (1.1%) is listed but unmeasurable in this harness: `perplexity/sonar`
performs live web search and ignores supplied sources, which breaks the Tier 1
constraint that retrieval is held constant. See the 2026-09-11 deviation entry
in `preregistrations/2026-09-lengthonly.md`.
"""

SOURCE = "Similarweb Gen AI worldwide traffic share, August 2026"
AS_OF = "2026-08"

# engine label -> (share %, OpenRouter model id or None if unmeasurable here)
ENGINES = {
    "ChatGPT":    (54.7, "openai/gpt-5.4-mini"),          # 52.7 + 2.0 Copilot
    "Gemini":     (27.8, "google/gemini-3-flash-preview"),
    "Claude":     (9.2,  "anthropic/claude-haiku-4.5"),
    "DeepSeek":   (3.6,  "deepseek/deepseek-chat"),
    "Grok":       (2.5,  "x-ai/grok-4.3"),
    "Perplexity": (1.1,  None),                            # live search; Tier 2 only
}


def weights(models_present):
    """Normalised weights over the models actually in a run.

    Renormalising over what was measured, rather than over the full market,
    keeps the pooled figure interpretable as "averaged over the engines this
    round covers" instead of quietly assuming the missing ones behave like the
    present ones.
    """
    present = {m: s for _, (s, m) in ENGINES.items()
               if m is not None and m in set(models_present)}
    total = sum(present.values())
    if total <= 0:
        n = len(models_present) or 1
        return {m: 1.0 / n for m in models_present}
    return {m: s / total for m, s in present.items()}


def coverage(models_present):
    """Share of measured gen-AI traffic the run's panel accounts for."""
    total_market = sum(s for s, _ in ENGINES.values())
    covered = sum(s for _, (s, m) in ENGINES.items()
                  if m is not None and m in set(models_present))
    return covered / total_market


def describe(models_present=None):
    lines = [f"engine weights -- {SOURCE}", ""]
    lines.append(f"  {'engine':<12}{'share':>8}   model")
    for name, (share, model) in sorted(ENGINES.items(), key=lambda kv: -kv[1][0]):
        tag = model or "(not measurable in Tier 1 -- live search)"
        mark = ""
        if models_present is not None and model:
            mark = "" if model in set(models_present) else "   [not in run]"
        lines.append(f"  {name:<12}{share:7.1f}%   {tag}{mark}")
    if models_present is not None:
        lines.append("")
        lines.append(f"  panel covers {coverage(models_present):.1%} of measured "
                     f"gen-AI traffic")
    return "\n".join(lines)


if __name__ == "__main__":
    print(describe())
