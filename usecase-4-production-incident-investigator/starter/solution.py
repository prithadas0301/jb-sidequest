"""Copy this file into your
submissions/<your-name>/usecase-4-production-incident-investigator/ folder
and implement investigate(). See ../README.md for the full brief.

Required interface - do not change the signature:

    def investigate(query: str, corpus: dict) -> dict:
        # corpus: filename -> full document text, e.g.
        #   {"logs.md": "...", "architecture.md": "...", "api_specs.md": "...",
        #    "deployment_history.md": "...", "previous_incidents.md": "...",
        #    "runbooks.md": "...", "known_issues.md": "..."}
        ...

Return a dict with exactly these keys:
    "root_cause"          str, non-empty
    "supporting_evidence" list[dict], each {"source": <filename>, "excerpt": <str>}
    "impacted_systems"    list[str]
    "mttr_minutes"        int | None
    "remediation"         str
    "confidence_score"    float, 0-100
    "needs_human_review"  bool - MUST equal (confidence_score < 50)

The retrieval half is scaffolded below (rank every document against the
query with TF-IDF cosine similarity - this is the "R" in RAG). The part
that's actually graded is what you do with the retrieved evidence:

1. Correlate across documents. A confident conclusion here isn't "the
   top-ranked document says X" - it's "logs, deployment history, known
   issues, the runbook, and a previous incident all point at the same
   thing." Count how many *distinct source types* actually corroborate
   your leading hypothesis.
2. Calibrate confidence_score from that corroboration count, not from how
   relevant the top document felt. A single weak signal with no
   deployment correlation, no known-issue match, and no precedent should
   score low - and reporting a confident-sounding root cause anyway when
   the evidence doesn't support it is worse than correctly saying "I'm
   not sure."
3. Extract mttr_minutes and impacted component names from the retrieved
   text (a runbook's "Typical MTTR: N minutes" line, an architecture
   doc's component name) - simple pattern matching is fine, you don't
   need anything fancier.
"""
from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _rank_documents(query: str, corpus: dict) -> list[tuple[str, float]]:
    """Returns [(filename, relevance_score), ...] sorted most relevant first."""
    filenames = list(corpus)
    documents = [corpus[name] for name in filenames]
    vectorizer = TfidfVectorizer(stop_words="english")
    doc_vectors = vectorizer.fit_transform(documents)
    query_vector = vectorizer.transform([query])
    scores = cosine_similarity(query_vector, doc_vectors)[0]
    ranked = sorted(zip(filenames, scores), key=lambda pair: -pair[1])
    return ranked


def investigate(query: str, corpus: dict) -> dict:
    ranked = _rank_documents(query, corpus)

    # TODO: everything below is a stub. Use `ranked` (and the raw corpus
    # text) to actually correlate evidence across documents, extract a
    # root cause, MTTR, and impacted systems, and calibrate a genuine
    # confidence score - see the module docstring above.
    raise NotImplementedError
