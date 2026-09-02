#!/usr/bin/env python3
"""Scans submissions/ and scores every candidate x use-case pair found,
producing one consolidated report (name, use case attempted, total score,
per-component breakdown). Admin-only - run from the repo root, after
pulling the latest merged submissions.

Usage:
    python scripts/generate_candidate_report.py
    python scripts/generate_candidate_report.py --out-dir reports/2026-09-03

This re-runs scoring/cli.py for every submission found (same engine CI
uses per-PR) rather than trusting any score already written under a use
case's own .score/ scratch directory, which only ever holds the most
recently scored submission for that use case.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
COMPONENT_COLUMNS = [
    "Correctness", "Performance", "Reusability",
    "Code quality", "Maintainability", "Completion",
]


def discover_submissions() -> list[tuple[str, str, Path]]:
    """Returns (candidate, usecase, submission_dir) for every
    submissions/<candidate>/<usecase>/ folder containing a solution.py.
    """
    results = []
    submissions_dir = REPO_ROOT / "submissions"
    if not submissions_dir.is_dir():
        return results
    for candidate_dir in sorted(submissions_dir.iterdir()):
        if not candidate_dir.is_dir():
            continue
        for usecase_dir in sorted(candidate_dir.iterdir()):
            if not usecase_dir.is_dir() or not usecase_dir.name.startswith("usecase-"):
                continue
            if (usecase_dir / "solution.py").is_file():
                results.append((candidate_dir.name, usecase_dir.name, usecase_dir))
    return results


def score_one(candidate: str, usecase: str, submission_dir: Path, out_dir: Path) -> dict:
    report_out = out_dir / candidate / usecase
    proc = subprocess.run(
        [sys.executable, "-m", "scoring.cli",
         "--usecase", usecase, "--submission", str(submission_dir),
         "--out-dir", str(report_out)],
        cwd=str(REPO_ROOT), capture_output=True, text=True,
    )
    report_json_path = report_out / "score_report.json"
    if not report_json_path.exists():
        return {
            "candidate": candidate, "usecase": usecase, "total": None, "disqualified": True,
            "disqualified_reason": f"scoring.cli produced no report (exit {proc.returncode}): "
                                    f"{proc.stderr[-500:]}",
        }
    data = json.loads(report_json_path.read_text())
    row = {
        "candidate": candidate,
        "usecase": usecase,
        "total": data["total"],
        "disqualified": data["disqualified"],
        "disqualified_reason": data.get("disqualified_reason", ""),
    }
    for component in data.get("components", []):
        row[component["name"]] = component["score"]
    return row


def _fmt(value) -> str:
    return f"{value:.1f}" if isinstance(value, (int, float)) else "-"


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["candidate", "usecase", "total", "disqualified", "disqualified_reason", *COMPONENT_COLUMNS]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Candidate score report", "", f"{len(rows)} submission(s) scored.", ""]
    header = ["Candidate", "Use case", "Total", *COMPONENT_COLUMNS]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "---|" * len(header))
    for row in sorted(rows, key=lambda r: (r["candidate"], r["usecase"])):
        if row.get("disqualified"):
            lines.append(f"| {row['candidate']} | {row['usecase']} | **DISQUALIFIED** | "
                          + f"{row.get('disqualified_reason', '')} " + "| |" * (len(COMPONENT_COLUMNS) - 1))
            continue
        cells = [row["candidate"], row["usecase"], _fmt(row["total"])]
        cells += [_fmt(row.get(name)) for name in COMPONENT_COLUMNS]
        lines.append("| " + " | ".join(cells) + " |")

    by_candidate: dict[str, list[dict]] = {}
    for row in rows:
        by_candidate.setdefault(row["candidate"], []).append(row)
    lines += ["", "## By candidate", ""]
    for candidate, candidate_rows in sorted(by_candidate.items()):
        attempted = ", ".join(sorted(r["usecase"] for r in candidate_rows))
        scores = [r["total"] for r in candidate_rows if not r.get("disqualified") and r["total"] is not None]
        best = f"{max(scores):.1f}" if scores else "-"
        lines.append(f"- **{candidate}** — attempted: {attempted}; best score: {best}")

    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(REPO_ROOT / "reports" / "latest"))
    args = parser.parse_args()
    out_dir = Path(args.out_dir)

    submissions = discover_submissions()
    if not submissions:
        print("No submissions found under submissions/*/usecase-*/solution.py")
        return 0

    rows = []
    for candidate, usecase, submission_dir in submissions:
        print(f"Scoring {candidate} / {usecase}...")
        rows.append(score_one(candidate, usecase, submission_dir, out_dir))

    write_csv(rows, out_dir / "candidate_report.csv")
    write_markdown(rows, out_dir / "candidate_report.md")
    print(f"\nWrote {out_dir / 'candidate_report.csv'}")
    print(f"Wrote {out_dir / 'candidate_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
