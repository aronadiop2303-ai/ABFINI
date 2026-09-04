from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .engine import OmniCore
from .models import ActionResult, Task
from .planner import OmniPlanner
from .tool_router import OmniToolRouter


@dataclass(frozen=True)
class AgentRun:
    task: Task
    answer: str
    model: str | None
    tool_results: list[ActionResult]


class OmniAgent:
    """Small, deterministic OMNI orchestration loop.

    Knowledge retrieval and generation remain injected so OMNI can use ABFINI's
    RAG and Model Router without coupling the agent Core to concrete providers.
    """

    def __init__(
        self,
        planner: OmniPlanner,
        tool_router: OmniToolRouter,
        answer_fn: Callable[[str], tuple[str, str | None]],
    ) -> None:
        self.core = OmniCore()
        self.planner = planner
        self.tool_router = tool_router
        self.answer_fn = answer_fn

    def run(self, goal: str, *, metadata: dict[str, Any] | None = None) -> AgentRun:
        task = self.core.create_task(goal, metadata)
        plan = self.planner.create_plan(task.goal)
        self.core.plan(task.id, plan.steps)

        tool_results: list[ActionResult] = []
        answer, model = self.answer_fn(task.goal)
        if not answer.strip():
            raise ValueError("agent answer cannot be empty")
        return AgentRun(task=self.core.tasks[task.id], answer=answer.strip(), model=model, tool_results=tool_results)
