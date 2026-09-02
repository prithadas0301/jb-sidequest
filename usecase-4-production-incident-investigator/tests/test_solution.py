"""Trusted test suite for use case 4. This IS the spec - do not edit (see
'Protecting the autoscoring engine' in the root README).

Spec being tested (see ../README.md for the candidate-facing version):

  investigate(query, corpus) -> dict with:
    "root_cause"            str, non-empty
    "supporting_evidence"   list[dict], each {"source": <filename>, "excerpt": <str>}
    "impacted_systems"      list[str]
    "mttr_minutes"          int | None
    "remediation"           str
    "confidence_score"      float, 0-100
    "needs_human_review"    bool, must equal (confidence_score < 50)

No exact wording is required anywhere except where explicitly checked
below (component name, MTTR value, and confidence crossing 50 the right
way for each incident) - free-text fields are graded for the presence of
key terms, not exact phrasing.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # this usecase dir

from data.loader import load_incident  # noqa: E402
from scoring.submission_loader import load_module  # noqa: E402

REQUIRED_KEYS = {
    "root_cause", "supporting_evidence", "impacted_systems",
    "mttr_minutes", "remediation", "confidence_score", "needs_human_review",
}


def _investigate(incident_name: str) -> dict:
    query, corpus = load_incident(incident_name)
    solution = load_module("solution.py")
    return solution.investigate(query, corpus)


def _assert_well_formed(report: dict, incident_name: str) -> None:
    missing = REQUIRED_KEYS - set(report)
    assert not missing, f"[{incident_name}] report is missing keys: {missing}"
    assert isinstance(report["confidence_score"], (int, float))
    assert 0 <= report["confidence_score"] <= 100, (
        f"[{incident_name}] confidence_score must be in [0, 100], got {report['confidence_score']}"
    )
    assert isinstance(report["needs_human_review"], bool)
    assert report["needs_human_review"] == (report["confidence_score"] < 50), (
        f"[{incident_name}] needs_human_review ({report['needs_human_review']}) is inconsistent "
        f"with confidence_score ({report['confidence_score']}) - it must be exactly "
        f"(confidence_score < 50), not independently decided"
    )
    assert isinstance(report["supporting_evidence"], list)
    for item in report["supporting_evidence"]:
        assert isinstance(item, dict) and "source" in item and "excerpt" in item, (
            f"[{incident_name}] each supporting_evidence entry must be "
            '{"source": <filename>, "excerpt": <str>}, got: {item!r}'
        )
    assert isinstance(report["root_cause"], str) and report["root_cause"].strip(), (
        f"[{incident_name}] root_cause must be a non-empty string, even when confidence is low - "
        "a low-confidence report is still a report, not a blank one"
    )


def test_incident_a_report_is_well_formed():
    report = _investigate("incident_a_pool_exhaustion")
    _assert_well_formed(report, "incident_a")


def test_incident_a_is_high_confidence_and_not_flagged():
    report = _investigate("incident_a_pool_exhaustion")
    assert report["confidence_score"] >= 50, (
        f"multiple independent sources corroborate the same root cause in this incident "
        f"(logs, deployment history, known issues, runbook, and a previous incident all agree) - "
        f"expected confidence_score >= 50, got {report['confidence_score']}"
    )
    assert report["needs_human_review"] is False


def test_incident_a_identifies_the_impacted_component():
    report = _investigate("incident_a_pool_exhaustion")
    systems = " ".join(report["impacted_systems"]).lower()
    assert "payment-gateway-adapter" in systems or "payment gateway adapter" in systems, (
        f"impacted_systems should name the actual component in the failure path "
        f"(payment-gateway-adapter), got: {report['impacted_systems']}"
    )


def test_incident_a_mttr_matches_the_runbook():
    report = _investigate("incident_a_pool_exhaustion")
    mttr = report["mttr_minutes"]
    assert mttr is not None, "mttr_minutes should be extracted from RB-014 ('Typical MTTR: 20 minutes')"
    assert abs(mttr - 20) <= 5, f"expected mttr_minutes close to 20 (per RB-014), got {mttr}"


def test_incident_a_root_cause_mentions_the_pool():
    report = _investigate("incident_a_pool_exhaustion")
    combined = (report["root_cause"] + " " + " ".join(e["excerpt"] for e in report["supporting_evidence"])).lower()
    assert "pool" in combined, (
        "root_cause / supporting_evidence should reference the connection pool - "
        "that's the actual root cause across every corroborating source"
    )


def test_incident_a_cites_multiple_independent_sources():
    report = _investigate("incident_a_pool_exhaustion")
    distinct_sources = {e["source"] for e in report["supporting_evidence"]}
    assert len(distinct_sources) >= 3, (
        f"a high-confidence conclusion here should be backed by evidence from several document "
        f"types (logs, deployment history, known issues, runbook, previous incident all support "
        f"it) - only cited {len(distinct_sources)} distinct source(s): {distinct_sources}"
    )


def test_incident_b_report_is_well_formed():
    report = _investigate("incident_b_ambiguous_delay")
    _assert_well_formed(report, "incident_b")


def test_incident_b_is_low_confidence_and_flagged_for_review():
    report = _investigate("incident_b_ambiguous_delay")
    assert report["confidence_score"] < 50, (
        f"this incident has no matching known issue, no correlated deployment, no precedent "
        f"incident, and no error-level logs - a single unconfirmed WARN entry is not enough "
        f"corroborating evidence for a confident conclusion. Expected confidence_score < 50, "
        f"got {report['confidence_score']}"
    )
    assert report["needs_human_review"] is True
