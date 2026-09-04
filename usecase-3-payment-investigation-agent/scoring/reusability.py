"""Reusability score: does the submission read like something a teammate
could import and extend, or one long script that happens to produce the
right numbers. Three independent, cheap-to-game-individually signals
combined so gaming all three at once isn't worth the effort:

  - cyclomatic complexity per function (radon) - a god-function is not
    reusable regardless of how well-named it is
  - function length (AST statement count) - a proxy independent of
    complexity for "does one function do one thing"
  - docstring + type-hint coverage on public (non-underscore) top-level
    functions - a function nobody can read the contract of isn't reusable
    even if it's short and simple
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

from .report import Component

MAX_REASONABLE_FUNCTION_LINES = 40


def _complexity_score(submission_dir: Path, py_files: list[Path]) -> tuple[float, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "radon", "cc", "-j", *[str(f) for f in py_files]],
        capture_output=True, text=True,
    )
    try:
        cc_data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        cc_data = {}

    complexities = [
        block["complexity"]
        for blocks in cc_data.values()
        for block in blocks
        if block.get("type") in ("function", "method")
    ]
    if not complexities:
        return 50.0, "no functions found to measure complexity on"

    avg_cc = sum(complexities) / len(complexities)
    worst = max(complexities)
    # radon's own rank bands: A<=5 B<=10 C<=20 D<=30 E<=40 F>40
    if avg_cc <= 5:
        score = 100.0
    elif avg_cc <= 10:
        score = 80.0
    elif avg_cc <= 20:
        score = 55.0
    elif avg_cc <= 30:
        score = 30.0
    else:
        score = 10.0
    return score, f"avg cyclomatic complexity {avg_cc:.1f} (worst function: {worst}) across {len(complexities)} function(s)"


def _function_length_score(py_files: list[Path]) -> tuple[float, str]:
    lengths = []
    for f in py_files:
        try:
            tree = ast.parse(f.read_text(errors="ignore"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if hasattr(node, "end_lineno") and node.end_lineno:
                    lengths.append(node.end_lineno - node.lineno + 1)

    if not lengths:
        return 50.0, "no functions found to measure length on"

    over_limit = [n for n in lengths if n > MAX_REASONABLE_FUNCTION_LINES]
    frac_over = len(over_limit) / len(lengths)
    score = max(0.0, 100.0 - frac_over * 150)  # each over-long function costs real points
    detail = (
        f"{len(over_limit)}/{len(lengths)} function(s) exceed "
        f"{MAX_REASONABLE_FUNCTION_LINES} lines (longest: {max(lengths)})"
    )
    return score, detail


def _docstring_typehint_score(py_files: list[Path]) -> tuple[float, str]:
    public_funcs = []
    for f in py_files:
        try:
            tree = ast.parse(f.read_text(errors="ignore"))
        except SyntaxError:
            continue
        for node in tree.body:  # top-level only - internal helpers can be terse
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
                has_docstring = ast.get_docstring(node) is not None
                has_annotation = node.returns is not None or any(
                    arg.annotation is not None for arg in node.args.args
                )
                public_funcs.append(has_docstring and has_annotation)

    if not public_funcs:
        return 50.0, "no public top-level functions found"

    coverage = sum(public_funcs) / len(public_funcs)
    return coverage * 100, (
        f"{sum(public_funcs)}/{len(public_funcs)} public function(s) have both a docstring "
        f"and at least one type annotation"
    )


def score_reusability(submission_dir: Path, weight: float) -> Component:
    py_files = sorted(submission_dir.glob("*.py"))
    if not py_files:
        return Component(name="Reusability", weight=weight, score=0.0,
                          detail="No .py files found in submission folder.", passed=False)

    cc_score, cc_detail = _complexity_score(submission_dir, py_files)
    len_score, len_detail = _function_length_score(py_files)
    doc_score, doc_detail = _docstring_typehint_score(py_files)

    # Equal thirds - no single signal can be gamed into a good score alone.
    total = (cc_score + len_score + doc_score) / 3

    detail = (
        f"Complexity: {cc_score:.0f}/100 - {cc_detail}\n"
        f"Function length: {len_score:.0f}/100 - {len_detail}\n"
        f"Docstrings + type hints on public functions: {doc_score:.0f}/100 - {doc_detail}"
    )
    return Component(name="Reusability", weight=weight, score=round(total, 1), detail=detail)
