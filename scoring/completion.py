"""Checks that a submission is actually complete: the required solution
file(s) exist and aren't empty stubs, and the personal README (name,
contact, design write-up) is present and substantive.
"""
from __future__ import annotations

from pathlib import Path

from .report import Component

_MIN_README_WORDS = 80
_REQUIRED_README_MARKERS = ("name", "email", "phone", "contact")


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
    readme_issues = []
    if not readme_path.is_file():
        readme_issues.append("README.md missing")
    else:
        text = readme_path.read_text(errors="ignore")
        words = len(text.split())
        if words < _MIN_README_WORDS:
            readme_issues.append(f"README.md too short ({words} words, need {_MIN_README_WORDS}+) "
                                  f"to actually contain a design write-up")
        lower = text.lower()
        missing_markers = [m for m in _REQUIRED_README_MARKERS if m not in lower]
        if missing_markers:
            readme_issues.append(f"README.md doesn't appear to mention: {', '.join(missing_markers)} "
                                  f"(name/contact info required per the submission brief)")

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
