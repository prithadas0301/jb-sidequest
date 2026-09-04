"""Dynamically imports a candidate's solution.py from their
submissions/<name>/<usecase>/ folder, without adding it to sys.path (so a
submission can't shadow stdlib/project modules by naming a file e.g.
`json.py`).
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType


class SubmissionNotFoundError(RuntimeError):
    pass


def submission_dir() -> Path:
    raw = os.environ.get("SUBMISSION_DIR")
    if not raw:
        raise SubmissionNotFoundError(
            "SUBMISSION_DIR is not set - point it at your "
            "submissions/<name>/<usecase>/ folder before running pytest "
            "directly, or use `python -m scoring.cli` which sets it for you."
        )
    path = Path(raw).resolve()
    if not path.is_dir():
        raise SubmissionNotFoundError(f"SUBMISSION_DIR does not exist: {path}")
    return path


def load_module(filename: str) -> ModuleType:
    """Load submissions/<name>/<usecase>/<filename> as an isolated module."""
    path = submission_dir() / filename
    if not path.is_file():
        raise SubmissionNotFoundError(
            f"Expected {filename} in your submission folder, not found at {path}"
        )
    module_name = f"jbsidequest_submission.{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise SubmissionNotFoundError(f"Could not load {path} as a Python module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
