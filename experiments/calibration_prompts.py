"""
OpenGEO calibration study — shared prompt set (METHODOLOGY.md §3, ROADMAP.md item 8).

Deliberately NOT reused from corpus/build_corpus.py: those 48 prompts were engineered
for a closed, 6-candidate-document context (Tier 1, retrieval held constant). This
study is the opposite — real open-web queries against real consumer AI answer engines
with live search, comparing how citation behavior diverges across query planes (API /
logged-out UI / logged-in UI) for the SAME question. The prompts are ordinary,
citation-likely, everyday questions across a few domains, asked verbatim on every
plane so the only thing that varies is the plane itself.

Small by design (12), per METHODOLOGY.md: "Manual or lightly-assisted collection is
acceptable here because n is small and the study runs quarterly."
"""

PROMPTS = [
    ("finance_fedrate", "finance", "What is the current federal funds rate in the US?"),
    ("finance_ira", "finance", "What's the difference between a Roth IRA and a traditional IRA?"),
    ("health_creatine", "health", "What are the health benefits of creatine monohydrate?"),
    ("health_allergies", "health", "What are the symptoms of seasonal allergies versus a common cold?"),
    ("auto_evcharger", "consumer", "How much does it cost to install a Level 2 EV charger at home?"),
    ("photo_lens", "consumer", "What's the best beginner camera lens for portrait photography?"),
    ("tech_keyboard", "consumer", "What's a good budget mechanical keyboard under $100 right now?"),
    ("pets_vaccine", "pets", "What's the recommended core vaccine schedule for puppies?"),
    ("nutrition_chipotle", "consumer", "How many calories are in a Chipotle chicken burrito bowl?"),
    ("sports_f1", "news", "Who won the most recent Formula 1 race?"),
    ("news_weather_sea", "news", "What's the weather forecast for Seattle this week?"),
    ("ref_mortgage", "finance", "How long does a 5-year adjustable-rate mortgage typically stay fixed?"),
]
