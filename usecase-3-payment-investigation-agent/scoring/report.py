"""Shared score report model used by every component scorer + scoring/cli.py."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Component:
    name: str
    weight: float          # 0..1, this component's share of the total
    score: float            # 0..100, this component's own score
    detail: str = ""
    passed: bool | None = None

    @property
    def weighted(self) -> float:
        return round(self.score * self.weight, 2)


@dataclass
class ScoreReport:
    usecase: str
    submission: str
    components: list[Component] = field(default_factory=list)
    disqualified: bool = False
    disqualified_reason: str = ""

    @property
    def total(self) -> float:
        if self.disqualified:
            return 0.0
        return round(sum(c.weighted for c in self.components), 2)

    def to_dict(self) -> dict:
        return {
            "usecase": self.usecase,
            "submission": self.submission,
            "disqualified": self.disqualified,
            "disqualified_reason": self.disqualified_reason,
            "total": self.total,
            "components": [
                {
                    "name": c.name,
                    "weight": c.weight,
                    "score": c.score,
                    "weighted": c.weighted,
                    "passed": c.passed,
                    "detail": c.detail,
                }
                for c in self.components
            ],
        }

    def to_markdown(self) -> str:
        lines = [f"# Score report: `{self.submission}` / `{self.usecase}`", ""]
        if self.disqualified:
            lines += [
                "## DISQUALIFIED",
                "",
                f"**{self.disqualified_reason}**",
                "",
                "No further scoring was run. See 'Protecting the autoscoring "
                "engine' in the root README.",
            ]
            return "\n".join(lines)

        lines += ["| Component | Weight | Score /100 | Weighted |", "|---|---|---|---|"]
        for c in self.components:
            lines.append(f"| {c.name} | {c.weight:.0%} | {c.score:.1f} | {c.weighted:.1f} |")
        lines += ["", f"**Total: {self.total:.1f} / 100**", "", "## Detail", ""]
        for c in self.components:
            status = "" if c.passed is None else (" (PASS)" if c.passed else " (FAIL)")
            lines.append(f"### {c.name}{status}\n\n{c.detail}\n")
        return "\n".join(lines)

    def write(self, out_dir: Path) -> None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "score_report.json").write_text(json.dumps(self.to_dict(), indent=2))
        (out_dir / "score_report.md").write_text(self.to_markdown())
