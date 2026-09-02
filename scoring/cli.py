"""Entry point used by CI (and candidates locally) to score one submission
against one use case.

Usage:
    python -m scoring.cli \
        --usecase usecase-1-streaming-topk-anomaly \
        --submission submissions/jane-doe/usecase-1-streaming-topk-anomaly \
        --out-dir score-output

Each usecase-*/ directory must contain a `scoring_hooks.py` exposing:
    WEIGHTS: dict[str, float]              (6 keys, sum to 1.0)
    REQUIRED_FILES: list[str]
    PERFORMANCE_THRESHOLDS: dict
    run_benchmark: Callable[[], dict[str, float]]

Note: this only scores. It does NOT check whether the submission modified
anything outside submissions/ - that's scoring/integrity.py, run as a
separate, earlier CI step so a tampered PR never reaches this module.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from pathlib import Path

from .code_quality import score_code_quality
from .completion import score_completion
from .correctness import score_correctness
from .maintainability import score_maintainability
from .performance import score_performance
from .report import ScoreReport
from .reusability import score_reusability


def _load_hooks(usecase_dir: Path):
    hooks_path = usecase_dir / "scoring_hooks.py"
    spec = importlib.util.spec_from_file_location("scoring_hooks", hooks_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--usecase", required=True, help="e.g. usecase-1-streaming-topk-anomaly")
    parser.add_argument("--submission", required=True, help="Path to submissions/<name>/<usecase>/")
    parser.add_argument("--out-dir", default=None, help="Where to write score_report.{json,md}")
    parser.add_argument("--fail-under", type=float, default=None, help="Exit non-zero if total < this")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    usecase_dir = (repo_root / args.usecase).resolve()
    submission_dir = Path(args.submission).resolve()
    out_dir = Path(args.out_dir) if args.out_dir else repo_root / args.usecase / ".score"

    report = ScoreReport(usecase=args.usecase, submission=str(submission_dir.relative_to(repo_root)))

    if not usecase_dir.is_dir():
        report.disqualified = True
        report.disqualified_reason = f"Unknown use case directory: {args.usecase}"
        report.write(out_dir)
        print(report.to_markdown())
        return 1

    if not submission_dir.is_dir():
        report.disqualified = True
        report.disqualified_reason = f"Submission folder not found: {submission_dir}"
        report.write(out_dir)
        print(report.to_markdown())
        return 1

    hooks = _load_hooks(usecase_dir)
    weights = hooks.WEIGHTS
    tests_dir = usecase_dir / "tests"

    os.environ["SUBMISSION_DIR"] = str(submission_dir)
    os.environ.setdefault("PYTHONPATH", str(repo_root))

    report.components.append(
        score_completion(submission_dir, hooks.REQUIRED_FILES, weight=weights["completion"])
    )
    report.components.append(
        score_correctness(tests_dir, submission_dir, out_dir, weight=weights["correctness"])
    )
    report.components.append(score_code_quality(submission_dir, weight=weights["code_quality"]))
    report.components.append(score_maintainability(submission_dir, weight=weights["maintainability"]))
    report.components.append(score_reusability(submission_dir, weight=weights["reusability"]))
    report.components.append(
        score_performance(hooks.run_benchmark, hooks.PERFORMANCE_THRESHOLDS, weight=weights["performance"])
    )

    report.write(out_dir)
    print(report.to_markdown())

    if args.fail_under is not None and report.total < args.fail_under:
        print(f"\nScore {report.total} is below --fail-under {args.fail_under}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
