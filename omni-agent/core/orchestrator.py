from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .engine import OmniCore
from .memory import OmniMemory
from .models import ActionRequest, ActionResult, Task
from .permissions import OmniPermissionEngine
from .planner import OmniPlanner
from .tool_router import OmniToolRouter


@dataclass(frozen=True)
class OrchestrationResult:
    task: Task
    answer: str
    model: str | None
    tool_results: list[ActionResult]


class OmniOrchestrator:
    """First complete OMNI V0.2 cycle: task -> plan -> permission -> tool -> answer."""

    def __init__(self, planner: OmniPlanner, tools: OmniToolRouter, answer_fn: Callable[[str], tuple[str, str | None]], *, memory: OmniMemory | None = None, permissions: OmniPermissionEngine | None = None) -> None:
        self.core = OmniCore()
        self.planner = planner
        self.tools = tools
        self.answer_fn = answer_fn
        self.memory = memory or OmniMemory()
        self.permissions = permissions or OmniPermissionEngine()

    def run(self, goal: str, *, action: ActionRequest | None = None, confirmed: bool = False, metadata: dict[str, Any] | None = None) -> OrchestrationResult:
        task = self.core.create_task(goal, metadata)
        self.memory.remember(task.goal, kind="task", metadata={"task_id": task.id})
        plan = self.planner.create_plan(task.goal)
        self.core.plan(task.id, plan.steps)

        tool_results: list[ActionResult] = []
        if action is not None:
            if action.task_id != task.id:
                raise ValueError("action task_id does not match current task")
            decision = self.permissions.decide(action.tool, action.arguments)
            if not decision.allowed:
                result = ActionResult(task.id, False, error=decision.reason)
            elif (decision.requires_confirmation or action.requires_confirmation) and not confirmed:
                result = ActionResult(task.id, False, error="user confirmation required")
            else:
                result = self.tools.execute(action, confirmed=confirmed)
            tool_results.append(result)
            self.core.apply_result(result)
            if not result.success:
                return OrchestrationResult(task, "", None, tool_results)

        answer, model = self.answer_fn(task.goal)
        answer = answer.strip()
        if not answer:
            failed = ActionResult(task.id, False, error="empty agent answer")
            self.core.apply_result(failed)
            return OrchestrationResult(task, "", model, tool_results + [failed])
        self.memory.remember(answer, kind="answer", metadata={"task_id": task.id, "model": model})
        task.state = task.state.COMPLETED
        return OrchestrationResult(task, answer, model, tool_results)
