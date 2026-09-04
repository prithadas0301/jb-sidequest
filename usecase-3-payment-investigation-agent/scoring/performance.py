"""Runs a use case's benchmark (scoring_hooks.run_benchmark) and scores the
result against declared floor/target thresholds per metric. A metric at or
below floor (for higher-is-better) scores 0; at or above target scores 100;
linear in between. This is where a naive-but-"correct" solution (right
answer, wrong complexity) actually loses points - correctness tests alone
can't catch an O(n*k) solution passing on small inputs.
"""
from __future__ import annotations

from collections.abc import Callable

from .report import Component


def _metric_score(value: float, floor: float, target: float, higher_is_better: bool) -> float:
    if higher_is_better:
        if target == floor:
            return 100.0 if value >= target else 0.0
        pct = (value - floor) / (target - floor)
    else:
        if target == floor:
            return 100.0 if value <= target else 0.0
        pct = (floor - value) / (floor - target)
    return max(0.0, min(100.0, pct * 100))


def score_performance(run_benchmark: Callable[[], dict], thresholds: dict, weight: float) -> Component:
    if not thresholds:
        return Component(name="Performance", weight=weight, score=100.0,
                          detail="No performance thresholds declared for this use case.")

    try:
        results = run_benchmark()
    except Exception as exc:  # noqa: BLE001 - a crashing benchmark is a hard 0, not a scoring-engine bug
        return Component(
            name="Performance", weight=weight, score=0.0, passed=False,
            detail=f"Benchmark raised {type(exc).__name__}: {exc}",
        )

    lines = []
    metric_scores = []
    for metric, cfg in thresholds.items():
        value = results.get(metric)
        if value is None:
            lines.append(f"- `{metric}`: MISSING from benchmark result")
            metric_scores.append(0.0)
            continue
        s = _metric_score(value, cfg["floor"], cfg["target"], cfg["higher_is_better"])
        metric_scores.append(s)
        direction = "higher is better" if cfg["higher_is_better"] else "lower is better"
        lines.append(
            f"- `{metric}`: {value:.4g} (floor {cfg['floor']}, target {cfg['target']}, "
            f"{direction}) -> {s:.0f}/100"
        )

    total = sum(metric_scores) / len(metric_scores)
    return Component(name="Performance", weight=weight, score=round(total, 1), detail="\n".join(lines))
