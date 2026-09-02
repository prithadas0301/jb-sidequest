"""Figures out which candidate + which use case(s) a PR/push touches, from
a list of changed file paths under submissions/. Candidates only ever add
files under submissions/<their-name>/<usecase-dir>/, so that's all the
workflow needs to dispatch scoring correctly without a per-usecase workflow.

Refuses to guess: a PR must touch exactly one candidate folder.
"""
from __future__ import annotations

import sys
from pathlib import Path


def known_usecase_dirs(repo_root: Path) -> set[str]:
    return {p.name for p in repo_root.iterdir() if p.is_dir() and p.name.startswith("usecase-")}


def detect(repo_root: Path, changed_paths: list[str]) -> tuple[str, list[str]]:
    """Returns (candidate_name, sorted list of usecase dirs touched)."""
    submission_paths = [p for p in changed_paths if p.startswith("submissions/")]
    if not submission_paths:
        raise ValueError("No changed files under submissions/ - nothing to score.")

    candidates = set()
    usecases = set()
    valid_usecases = known_usecase_dirs(repo_root)

    for p in submission_paths:
        parts = Path(p).parts
        if len(parts) < 2:
            continue
        candidates.add(parts[1])
        if len(parts) >= 3:
            if parts[2] not in valid_usecases:
                raise ValueError(
                    f"'{p}' is under an unrecognized use case folder name "
                    f"'{parts[2]}'. It must exactly match one of: {sorted(valid_usecases)}"
                )
            usecases.add(parts[2])

    if len(candidates) != 1:
        raise ValueError(
            f"This PR touches {len(candidates)} candidate folder(s) under submissions/: "
            f"{sorted(candidates)}. Exactly one candidate per PR - don't mix submissions."
        )
    if not usecases:
        raise ValueError(
            f"Files changed under submissions/{next(iter(candidates))}/ but none inside "
            "a recognized usecase-*/ subfolder - nothing to score."
        )

    return next(iter(candidates)), sorted(usecases)


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("changed_files", nargs="*")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    changed = args.changed_files or [line.strip() for line in sys.stdin if line.strip()]

    try:
        candidate, usecases = detect(repo_root, changed)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"candidate={candidate}")
    print(f"usecases={','.join(usecases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
