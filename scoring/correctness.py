"""Runs a use case's trusted pytest suite against a submission and turns
the result into a 0-100 score: pass rate * 100, with partial credit so a
submission that gets most of it right isn't zeroed out by one edge case.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from .report import Component


def score_correctness(tests_dir: Path, submission_dir: Path, out_dir: Path, weight: float) -> Component:
    out_dir.mkdir(parents=True, exist_ok=True)
    junit_path = out_dir / "junit.xml"
    json_path = out_dir / "pytest_report.json"

    env = {**os.environ, "SUBMISSION_DIR": str(submission_dir)}
    proc = subprocess.run(
        [
            sys.executable, "-m", "pytest", str(tests_dir), "-v",
            f"--junitxml={junit_path}",
            "--json-report", f"--json-report-file={json_path}",
        ],
        capture_output=True, text=True,
        env=env,
        cwd=str(_repo_root()),
    )

    summary = _summarize(json_path)
    if summary is None:
        detail = (
            "Could not parse pytest output (tests likely errored before "
            "collection - e.g. a missing solution.py, or a syntax error in "
            "your submission).\n\n```\n"
            + (proc.stdout[-4000:] + "\n" + proc.stderr[-2000:]) + "\n```"
        )
        return Component(name="Correctness", weight=weight, score=0.0, detail=detail, passed=False)

    total, passed_n = summary
    pct = 0.0 if total == 0 else (passed_n / total) * 100
    detail = f"{passed_n}/{total} tests passed.\n\n```\n{proc.stdout[-4000:]}\n```"
    return Component(name="Correctness", weight=weight, score=round(pct, 1), detail=detail, passed=passed_n == total)


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _summarize(json_path: Path) -> tuple[int, int] | None:
    if not json_path.exists():
        return None
    try:
        data = json.loads(json_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    summary = data.get("summary", {})
    return summary.get("total", 0), summary.get("passed", 0)
