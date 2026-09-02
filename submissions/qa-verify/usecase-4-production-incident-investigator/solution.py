"""Production incident investigator - TF-IDF retrieval plus a rule-based
correlation/confidence step. See README.md for design rationale.
"""
from __future__ import annotations

import re
from collections import Counter

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_EXCEPTION_RE = re.compile(r"\b([A-Z][a-zA-Z]*Exception)\b")
_COMPONENT_RE = re.compile(r"\b([a-z][a-z0-9]*(?:-[a-z][a-z0-9]*)+)\b")
_MTTR_RE = re.compile(r"MTTR[:\s]*[:\-]?\s*(\d+)\s*minutes", re.IGNORECASE)
_REMEDIATION_RE = re.compile(r"\*\*Remediation\*\*:\s*(.+)")

_FALLBACK_CONFIDENCE = 15.0
_BASE_CONFIDENCE = 20.0
_CONFIDENCE_PER_SOURCE = 15.0


def rank_documents(query: str, corpus: dict) -> list[tuple[str, float]]:
    """Rank every document in corpus against query by TF-IDF cosine
    similarity, most relevant first."""
    filenames = list(corpus)
    vectorizer = TfidfVectorizer(stop_words="english")
    doc_vectors = vectorizer.fit_transform([corpus[name] for name in filenames])
    query_vector = vectorizer.transform([query])
    scores = cosine_similarity(query_vector, doc_vectors)[0]
    return sorted(zip(filenames, scores), key=lambda pair: -pair[1])


def _dominant_exception(logs_text: str) -> str | None:
    names = _EXCEPTION_RE.findall(logs_text)
    return Counter(names).most_common(1)[0][0] if names else None


def _components_in_error_lines(logs_text: str) -> set[str]:
    error_lines = [line for line in logs_text.splitlines() if "ERROR" in line]
    components: set[str] = set()
    for line in error_lines:
        components.update(_COMPONENT_RE.findall(line.lower()))
    return components


def identify_error_signature(logs_text: str) -> tuple[str | None, set[str]]:
    """The dominant exception name and the set of components that appear
    in ERROR-level log lines, if any."""
    return _dominant_exception(logs_text), _components_in_error_lines(logs_text)


def resolve_impacted_components(
    error_components: set[str], ranked: list[tuple[str, float]], corpus: dict
) -> set[str]:
    """When ERROR lines gave us nothing to anchor on, fall back to the
    components mentioned in the single most relevant document - a hedge,
    not a confident finding (confidence_score reflects that separately)."""
    if error_components:
        return error_components
    top_doc_name, _score = ranked[0]
    return set(_COMPONENT_RE.findall(corpus[top_doc_name].lower()))


def correlate_evidence(
    corpus: dict, dominant_exception: str | None, components: set[str]
) -> tuple[set[str], float]:
    """Which non-log documents corroborate the error signature, and the
    confidence that follows from how many independently do."""
    if not dominant_exception:
        return set(), _FALLBACK_CONFIDENCE

    corroborating = {
        name
        for name, text in corpus.items()
        if name != "logs.md"
        and (dominant_exception.lower() in text.lower() or any(c in text.lower() for c in components))
    }
    confidence = min(100.0, _BASE_CONFIDENCE + len(corroborating) * _CONFIDENCE_PER_SOURCE)
    return corroborating, confidence


def _find_excerpt(text: str, keywords: set[str]) -> str:
    for line in text.splitlines():
        if any(keyword.lower() in line.lower() for keyword in keywords):
            return line.strip()
    return text.strip().splitlines()[0][:200] if text.strip() else ""


def _relevant_runbook_section(runbook_text: str, keywords: set[str]) -> str | None:
    sections = re.split(r"\n(?=##\s)", runbook_text) or [runbook_text]
    return next((s for s in sections if any(k.lower() in s.lower() for k in keywords)), None)


def extract_mttr_and_remediation(runbook_text: str, keywords: set[str]) -> tuple[int | None, str]:
    """Pull MTTR and remediation text from whichever runbook section
    actually mentions the evidence keywords, not just the first one."""
    section = _relevant_runbook_section(runbook_text, keywords)
    if not section:
        return None, "Escalate to the on-call owner of the affected components for manual review."

    mttr_match = _MTTR_RE.search(section)
    mttr_minutes = int(mttr_match.group(1)) if mttr_match else None

    remediation_match = _REMEDIATION_RE.search(section)
    remediation = (
        remediation_match.group(1).strip()
        if remediation_match
        else "Escalate to the on-call owner of the affected components for manual review."
    )
    return mttr_minutes, remediation


def build_supporting_evidence(
    corpus: dict, corroborating_sources: set[str], ranked: list[tuple[str, float]], keywords: set[str]
) -> list[dict]:
    """One {"source", "excerpt"} entry per corroborating document, or the
    single top-ranked document as a hedge when nothing corroborates."""
    if corroborating_sources:
        return [
            {"source": name, "excerpt": _find_excerpt(corpus[name], keywords)}
            for name in sorted(corroborating_sources)
        ]
    top_doc_name, _score = ranked[0]
    return [{"source": top_doc_name, "excerpt": _find_excerpt(corpus[top_doc_name], keywords)}]


def describe_root_cause(
    dominant_exception: str | None, components: set[str], corroborating_sources: set[str]
) -> str:
    """A human-readable root-cause statement - confident and specific when
    there's a corroborated error signature, honestly hedged when there isn't."""
    if dominant_exception:
        return (
            f"{dominant_exception} recurring in {', '.join(sorted(components))}, "
            f"corroborated by {len(corroborating_sources)} independent source(s): "
            f"{', '.join(sorted(corroborating_sources)) or 'none'}."
        )
    return (
        "No error-level log signal, no correlated deployment, no matching known-issue "
        "signature, and no precedent incident were found for this symptom. The evidence "
        "is insufficient to confidently identify a single root cause; likely-relevant "
        f"components based on document relevance: {', '.join(sorted(components)) or 'unclear'}."
    )


def investigate(query: str, corpus: dict) -> dict:
    """Retrieve, correlate evidence across the corpus, and return a
    structured incident report - see ../README.md for the exact contract.
    """
    ranked = rank_documents(query, corpus)
    dominant_exception, error_components = identify_error_signature(corpus.get("logs.md", ""))
    components = resolve_impacted_components(error_components, ranked, corpus)
    keywords = components | ({dominant_exception} if dominant_exception else set())

    corroborating_sources, confidence_score = correlate_evidence(corpus, dominant_exception, components)
    mttr_minutes, remediation = extract_mttr_and_remediation(corpus.get("runbooks.md", ""), keywords)

    return {
        "root_cause": describe_root_cause(dominant_exception, components, corroborating_sources),
        "supporting_evidence": build_supporting_evidence(corpus, corroborating_sources, ranked, keywords),
        "impacted_systems": sorted(components),
        "mttr_minutes": mttr_minutes,
        "remediation": remediation,
        "confidence_score": confidence_score,
        "needs_human_review": confidence_score < 50,
    }
