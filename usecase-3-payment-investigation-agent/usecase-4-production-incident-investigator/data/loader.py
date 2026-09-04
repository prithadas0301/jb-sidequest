"""Loads one incident's query + document corpus from its data folder.
Used by tests, benchmark, and candidates alike - not something you need
to modify.
"""
from __future__ import annotations

from pathlib import Path

DATA_DIR = Path(__file__).parent


def load_incident(name: str) -> tuple[str, dict[str, str]]:
    """Returns (query, corpus) where corpus maps filename -> full document
    text, for every *.md file in data/<name>/.
    """
    incident_dir = DATA_DIR / name
    query = (incident_dir / "query.txt").read_text(encoding="utf-8").strip()
    corpus = {p.name: p.read_text(encoding="utf-8") for p in sorted(incident_dir.glob("*.md"))}
    return query, corpus
