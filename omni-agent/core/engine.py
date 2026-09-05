from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import ActionRequest, ActionResult, Task, TaskState

_TERMINAL_STATES = frozenset({TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED})


@dataclass
class OmniCore:
    """Provider-agnostic first foundation of OMNI Agent.

    The Core does not call an LLM or external service directly. Those capabilities
    will be injected through the Model, Tool and Agent routers in later bricks.
    """

    tasks: dict[str, Task] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    def create_task(self, goal: str, metadata: dict[str, Any] | None = None) -> Task:
        if not goal.strip():
            raise ValueError("Task goal cannot be empty")
        task = Task(goal=goal.strip(), metadata=metadata or {})
        self.tasks[task.id] = task
        self._event("task.created", task.id, {"goal": task.goal})
        return task

    def plan(self, task_id: str, steps: list[str]) -> Task:
        task = self._get_task(task_id)
        if not steps:
            raise ValueError("A task plan requires at least one step")
        task.plan = [step.strip() for step in steps if step.strip()]
        task.state = TaskState.PLANNING
        self._event("task.planned", task.id, {"steps": task.plan})
        return task

    def request_action(
        self,
        task_id: str,
        action: str,
        tool: str | None = None,
        arguments: dict[str, Any] | None = None,
        requires_confirmation: bool = False,
    ) -> ActionRequest:
        task = self._get_task(task_id)
        task.state = TaskState.WAITING_TOOL
        request = ActionRequest(
            task_id=task.id,
            action=action,
            tool=tool,
            arguments=arguments or {},
            requires_confirmation=requires_confirmation,
        )
        self._event("action.requested", task.id, {"action": action, "tool": tool})
        return request

    def apply_result(self, result: ActionResult) -> Task:
        task = self._get_task(result.task_id)
        task.state = TaskState.COMPLETED if result.success else TaskState.FAILED
        self._event(
            "action.completed" if result.success else "action.failed",
            task.id,
            {"output": result.output, "error": result.error},
        )
        return task

    def wait_for_confirmation(self, task_id: str) -> Task:
        task = self._get_task(task_id)
        task.state = TaskState.WAITING_CONFIRMATION
        self._event("action.waiting_confirmation", task.id, {})
        return task

    def start_execution(self, task_id: str) -> Task:
        task = self._get_task(task_id)
        task.state = TaskState.EXECUTING
        self._event("action.executing", task.id, {})
        return task

    def cancel(self, task_id: str) -> Task:
        task = self._get_task(task_id)
        if task.state in _TERMINAL_STATES:
            raise ValueError(f"cannot cancel a task in terminal state: {task.state.value}")
        task.state = TaskState.CANCELLED
        self._event("task.cancelled", task.id, {})
        return task

    def _get_task(self, task_id: str) -> Task:
        try:
            return self.tasks[task_id]
        except KeyError as exc:
            raise KeyError(f"Unknown OMNI task: {task_id}") from exc

    def _event(self, event_type: str, task_id: str, data: dict[str, Any]) -> None:
        self.events.append({"type": event_type, "task_id": task_id, "data": data})
