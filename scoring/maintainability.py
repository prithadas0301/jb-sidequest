"""Maintainability index (radon) over the candidate's own submitted files."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from .report import Component


def score_maintainability(submission_dir: Path, weight: float) -> Component:
    py_files = sorted(submission_dir.glob("*.py"))
    if not py_files:
        return Component(name="Maintainability", weight=weight, score=0.0,
                          detail="No .py files found in submission folder.", passed=False)

    proc = subprocess.run(
        [sys.executable, "-m", "radon", "mi", "-j", *[str(f) for f in py_files]],
        capture_output=True, text=True,
    )
    try:
        mi_data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        mi_data = {}

    scores = [v["mi"] for v in mi_data.values() if isinstance(v, dict) and "mi" in v]
    if not scores:
        return Component(name="Maintainability", weight=weight, score=50.0,
                          detail="radon produced no maintainability-index data; defaulting to 50.")

    avg_mi = sum(scores) / len(scores)  # radon MI is already ~0-100
    score = max(0.0, min(100.0, avg_mi))

    detail_lines = [f"Average maintainability index: {avg_mi:.1f}/100 across {len(scores)} file(s)."]
    for path, v in mi_data.items():
        if isinstance(v, dict) and "mi" in v:
            detail_lines.append(f"- `{Path(path).name}`: MI={v['mi']:.1f} rank={v.get('rank', '?')}")

    return Component(name="Maintainability", weight=weight, score=round(score, 1), detail="\n".join(detail_lines))
