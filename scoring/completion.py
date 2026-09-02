"""Checks that a submission is actually complete: the required solution
file(s) exist and aren't empty stubs, and the personal README (name,
contact, design write-up) is present and substantive.
"""
from __future__ import annotations

import re
from pathlib import Path

from .report import Component

_MIN_README_WORDS = 80
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_RE = re.compile(r"(\+?\d[\d\s\-().]{6,}\d)")


def _readme_content_issues(text: str) -> list[str]:
    issues = []
    words = len(text.split())
    if words < _MIN_README_WORDS:
        issues.append(f"README.md too short ({words} words, need {_MIN_README_WORDS}+) "
                       f"to actually contain a design write-up")
    if "name" not in text.lower():
        issues.append("README.md doesn't appear to state your name")
    if not _EMAIL_RE.search(text):
        issues.append("README.md doesn't appear to contain an email address")
    if not _PHONE_RE.search(text):
        issues.append("README.md doesn't appear to contain a phone number")
    return issues


def score_completion(submission_dir: Path, required_files: list[str], weight: float) -> Component:
    missing, empty = [], []
    for name in required_files:
        path = submission_dir / name
        if not path.is_file():
            missing.append(name)
            continue
        text = path.read_text(errors="ignore").strip()
        if name.endswith(".py") and len(text) < 20:
            empty.append(name)

    readme_path = submission_dir / "README.md"
    if not readme_path.is_file():
        readme_issues = ["README.md missing"]
    else:
        readme_issues = _readme_content_issues(readme_path.read_text(errors="ignore"))

    n_required = len(required_files) + 1  # +1 for README.md
    n_ok = n_required - len(missing) - len(empty) - (1 if readme_issues else 0)
    score = 0.0 if n_required == 0 else (n_ok / n_required) * 100

    lines = [f"{n_ok}/{n_required} required item(s) present and non-trivial."]
    if missing:
        lines.append(f"Missing: {', '.join(missing)}")
    if empty:
        lines.append(f"Present but too small/trivial to be a real attempt: {', '.join(empty)}")
    lines.extend(readme_issues)

    return Component(name="Completion", weight=weight, score=round(score, 1), detail="\n".join(lines),
                      passed=not missing and not empty and not readme_issues)
