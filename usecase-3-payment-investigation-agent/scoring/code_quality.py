"""Static analysis (ruff) findings per line of submitted code, scored as a
0-100 band. Only the candidate's own submission files are linted - never
the shared tests/scoring code.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from .report import Component

# findings per 100 lines -> score. A handful of style nits shouldn't tank
# an otherwise-correct, well-designed solution.
_BANDS = [
    (0.0, 100),
    (2.0, 90),
    (5.0, 75),
    (10.0, 55),
    (20.0, 30),
]


def score_code_quality(submission_dir: Path, weight: float) -> Component:
    py_files = sorted(submission_dir.glob("*.py"))
    if not py_files:
        return Component(name="Code quality", weight=weight, score=0.0,
                          detail="No .py files found in submission folder.", passed=False)

    total_lines = sum(len(f.read_text(errors="ignore").splitlines()) for f in py_files) or 1

    proc = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--output-format=json", *[str(f) for f in py_files]],
        capture_output=True, text=True,
    )
    try:
        findings = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        findings = []

    rate = (len(findings) / total_lines) * 100
    score = 10
    for threshold, band_score in _BANDS:
        if rate <= threshold:
            score = band_score
            break

    lines = [f"{len(findings)} ruff finding(s) across {total_lines} lines "
             f"({rate:.2f} findings/100 lines)."]
    for f in findings[:25]:
        loc = f.get("location", {})
        lines.append(f"- `{Path(f['filename']).name}:{loc.get('row')}` "
                      f"[{f.get('code')}] {f.get('message')}")
    if len(findings) > 25:
        lines.append(f"- ... and {len(findings) - 25} more")

    return Component(name="Code quality", weight=weight, score=float(score), detail="\n".join(lines))
