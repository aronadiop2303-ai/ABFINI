from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Plan:
    """A deterministic, inspectable plan produced from an OMNI task goal."""

    goal: str
    steps: list[str]


class OmniPlanner:
    """Provider-agnostic planner for OMNI V0.2.

    Planning is deliberately separated from LLM inference. A future model/router
    can be injected through ``planner_fn`` without changing the Core contract.
    """

    def __init__(self, planner_fn: Callable[[str], list[str]] | None = None) -> None:
        self._planner_fn = planner_fn

    def create_plan(self, goal: str) -> Plan:
        normalized = goal.strip()
        if not normalized:
            raise ValueError("Task goal cannot be empty")
        steps = self._planner_fn(normalized) if self._planner_fn else self._default_plan(normalized)
        clean = [step.strip() for step in steps if step and step.strip()]
        if not clean:
            raise ValueError("Planner produced an empty plan")
        return Plan(goal=normalized, steps=clean)

    @staticmethod
    def _default_plan(goal: str) -> list[str]:
        return [
            f"Understand the task: {goal}",
            "Identify the required information and authorized tools",
            "Execute the minimum required actions",
            "Verify the result",
            "Return a concise result and execution trace",
        ]
