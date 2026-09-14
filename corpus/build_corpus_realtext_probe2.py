#!/usr/bin/env python3
"""
OpenGEO -- second feasibility probe for ROADMAP item 11, different question and domain.

Probe 1 (`build_corpus_realtext_probe.py`, nutrition / added sugars) found that
per-document CPR falls from 0.778 at six candidates to 0.561 at ten, and concluded the
regime item 11 needs is reachable with a larger candidate set. That rested on two points
from one document pool on one question. This probe repeats the design on consumer
finance to see whether the relationship generalises or was a property of that topic.

Two things differ on purpose:

- **Domain.** Credit reporting, not nutrition. Sources are CFPB, FTC, FDIC.
- **Composition of what gets added.** Probe 1 added mostly strong answerers going from
  six to ten. Here the four added documents are all topically adjacent rather than
  answering, which is what a real candidate set for this question would actually look
  like. If per-document CPR falls in both, the crowding effect is not an artifact of
  which documents happen to be added.

The primary reading in both probes is **not** the mean over all documents, which moves
partly by arithmetic when weak documents join the pool. It is whether the *same six*
documents lose citations when four more candidates appear alongside them.

Sources are US federal works, public domain under 17 U.S.C. Sec 105, quoted verbatim
with source URLs recorded per document. Retrieved 2026-09-12.

    python3 corpus/build_corpus_realtext_probe2.py
"""
import hashlib
import json
import pathlib

OUTDIR = pathlib.Path(__file__).parent

# Derived from the documents after collection, not chosen in advance.
QUESTION = "How long does negative information stay on my credit report?"

# Order matters: the first six are the N=6 set, so they must be identical in both runs.
DOCS = [
    {
        "key": "cfpb_howlong",
        "answers": "direct",
        "agency": "CFPB",
        "title": "How long does information stay on my credit report?",
        "url": "https://www.consumerfinance.gov/ask-cfpb/how-long-does-information-stay-on-my-credit-report-en-323/",
        "format": "reference",
        "text": (
            "A credit reporting company generally can report most negative information "
            "for seven years. Information about a lawsuit or a judgment against you can "
            "be reported for seven years or until the statute of limitations runs out, "
            "whichever is longer. Bankruptcies can stay on your report for up to ten "
            "years. Credit reporting companies may still keep the information on file "
            "after they stop reporting it."
        ),
    },
    {
        "key": "ftc_fixing",
        "answers": "direct",
        "agency": "FTC",
        "title": "Fixing Your Credit FAQs",
        "url": "https://consumer.ftc.gov/articles/fixing-your-credit-faqs",
        "format": "blog",
        "text": (
            "Most negative information will stay on your report for seven years, and "
            "bankruptcy information will stay on for 10 years. And in some cases, like "
            "when you're being considered for a job paying more than $75,000 a year, or "
            "you're trying to get a loan or insurance valued at more than $150,000, a "
            "credit bureau may include older negative information that wouldn't show up "
            "otherwise."
        ),
    },
    {
        "key": "fdic_reports",
        "answers": "direct",
        "agency": "FDIC",
        "title": "Credit Reports",
        "url": "https://www.fdic.gov/consumer-resource-center/credit-reports",
        "format": "docs",
        "text": (
            "In most cases, a credit bureau may not report negative information that is "
            "more than seven years old or bankruptcies that are more than 10 years old. "
            "Consumers should review their reports from each nationwide bureau, because "
            "the three do not always hold identical information and an item may appear "
            "on one report without appearing on the others."
        ),
    },
    {
        "key": "cfpb_bankruptcy",
        "answers": "direct",
        "agency": "CFPB",
        "title": "How long does a bankruptcy appear on credit reports?",
        "url": "https://www.consumerfinance.gov/ask-cfpb/how-long-does-a-bankruptcy-appear-on-credit-reports-en-325/",
        "format": "reference",
        "text": (
            "If you filed for bankruptcy protection, that information will remain in "
            "your credit report up to 10 years from the date of entry of the order or "
            "the date of adjudication. Your bankruptcy will stay on your credit report "
            "up to 10 years if it is filed under one of the following chapters of the "
            "Bankruptcy Code: Chapter 7, Chapter 11, Chapter 12, Chapter 13."
        ),
    },
    {
        "key": "cfpb_remove",
        "answers": "direct",
        "agency": "CFPB",
        "title": "Is it possible to remove accurate but negative information?",
        "url": "https://www.consumerfinance.gov/ask-cfpb/is-it-possible-to-remove-accurate-negative-information-from-my-credit-report-en-1249/",
        "format": "reference",
        "text": (
            "You generally cannot have negative information removed from your credit "
            "report if it is accurate. Most negative information will remain in your "
            "report for seven years. Some types of information remain longer. Anyone "
            "promising to remove accurate negative items before that period expires is "
            "describing something the law does not allow."
        ),
    },
    {
        "key": "cfpb_whatis",
        "answers": "adjacent",
        "agency": "CFPB",
        "title": "What is a credit report?",
        "url": "https://www.consumerfinance.gov/ask-cfpb/what-is-a-credit-report-en-309/",
        "format": "reference",
        "text": (
            "A credit report is a statement that has information about your credit "
            "activity and current credit situation such as loan paying history and the "
            "status of your credit accounts. Most people have more than one credit "
            "report. Credit reporting companies, also known as credit bureaus, collect "
            "and store financial data submitted to them by creditors."
        ),
    },
    # --- the four added at N=10, all topically adjacent rather than answering ---
    {
        "key": "ftc_disputing",
        "answers": "adjacent",
        "agency": "FTC",
        "title": "Disputing Errors on Your Credit Reports",
        "url": "https://consumer.ftc.gov/articles/disputing-errors-your-credit-reports",
        "format": "blog",
        "text": (
            "Both the credit bureau and the business that supplied the information to a "
            "credit bureau have to correct information that is wrong or incomplete in "
            "your report. And they have to do it for free. To correct mistakes in your "
            "report, contact the credit bureau and the business that reported the "
            "inaccurate information, and tell them you want to dispute it."
        ),
    },
    {
        "key": "cfpb_getcopy",
        "answers": "adjacent",
        "agency": "CFPB",
        "title": "How do I get a free copy of my credit reports?",
        "url": "https://www.consumerfinance.gov/ask-cfpb/how-do-i-get-a-copy-of-my-credit-reports-en-5/",
        "format": "reference",
        "text": (
            "You have the right to request one free copy of your credit report each year "
            "from each of the three major consumer reporting companies, Equifax, "
            "Experian and TransUnion, by visiting AnnualCreditReport.com. Checking your "
            "own report does not affect your credit score, and reviewing all three is "
            "the only way to see everything being reported about you."
        ),
    },
    {
        "key": "cfpb_score",
        "answers": "adjacent",
        "agency": "CFPB",
        "title": "What is a credit score?",
        "url": "https://www.consumerfinance.gov/ask-cfpb/what-is-a-credit-score-en-315/",
        "format": "reference",
        "text": (
            "A credit score is a prediction of your credit behavior, such as how likely "
            "you are to pay a loan back on time, based on information from your credit "
            "reports. Companies use credit scores to make decisions on whether to offer "
            "you a mortgage, credit card, auto loan, and other credit products, as well "
            "as for tenant screening and insurance."
        ),
    },
    {
        "key": "ftc_free",
        "answers": "adjacent",
        "agency": "FTC",
        "title": "Free Credit Reports",
        "url": "https://consumer.ftc.gov/articles/free-credit-reports",
        "format": "blog",
        "text": (
            "All three nationwide credit bureaus have permanently extended a program "
            "that lets you check your credit report from each once a week for free at "
            "AnnualCreditReport.com. In addition, federal law requires each nationwide "
            "credit bureau to give you a free copy of your credit report once every 12 "
            "months if you ask for it."
        ),
    },
]

PROMPT_ID = "finance_creditreport"
DOMAIN = "finance"


def build(n, out):
    documents = []
    for d in DOCS[:n]:
        documents.append({
            "doc_id": f"{PROMPT_ID}__{d['key']}",
            "prompt_id": PROMPT_ID,
            "format": d["format"],
            "domain": DOMAIN,
            "is_target": d["key"] == DOCS[0]["key"],
            "source": {"agency": d["agency"], "title": d["title"], "url": d["url"],
                       "rights": "US federal work, public domain (17 U.S.C. 105)"},
            "answers": d["answers"],
            "words": len(d["text"].split()),
            "variants": {"control": d["text"]},
        })

    prompt = {
        "prompt_id": PROMPT_ID,
        "domain": DOMAIN,
        "question": QUESTION,
        "target_doc_id": documents[0]["doc_id"],
        "target_format": documents[0]["format"],
        "doc_ids": [d["doc_id"] for d in documents],
    }

    corpus = {
        "corpus_version": f"realtext-probe2-v0-n{n}",
        "intervention": "none -- baseline regime probe for ROADMAP item 11",
        "n_prompts": 1,
        "n_docs": len(documents),
        "formats": sorted({d["format"] for d in documents}),
        "domains": [DOMAIN],
        "prompts": [prompt],
        "documents": documents,
    }
    blob = json.dumps(corpus, sort_keys=True, separators=(",", ":")).encode()
    corpus["corpus_sha256"] = hashlib.sha256(blob).hexdigest()
    out.write_text(json.dumps(corpus, indent=2) + "\n")

    print(f"wrote {out}  sha256 {corpus['corpus_sha256'][:16]}")
    w = [d["words"] for d in documents]
    print(f"  {n} docs, {sum(1 for d in DOCS[:n] if d['answers'] == 'direct')} answering "
          f"directly, {min(w)}-{max(w)} words (spread {max(w) - min(w)})")


if __name__ == "__main__":
    print(f"question: {QUESTION}\n")
    for n in (6, len(DOCS)):
        build(n, OUTDIR / f"corpus_realtext_probe2_{n}.json")
    print("\nThe four documents added at N=10 are all topically adjacent, not answering.")
    print("Probe 1 added mostly answering documents. If per-document CPR falls in both,")
    print("crowding is not an artifact of what happens to be added.")
