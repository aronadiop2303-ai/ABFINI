from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .models import ActionRequest, ActionResult


class ToolRouterError(RuntimeError):
    pass


@dataclass(frozen=True)
class ToolSpec:
    name: str
    handler: Callable[[dict[str, Any]], Any]
    requires_confirmation: bool = False


class OmniToolRouter:
    """Allowlisted, provider-agnostic tool execution layer for OMNI V0.2."""

    def __init__(self, tools: list[ToolSpec] | None = None) -> None:
        self._tools: dict[str, ToolSpec] = {}
        for spec in tools or []:
            self.register(spec)

    def register(self, spec: ToolSpec) -> None:
        name = spec.name.strip()
        if not name:
            raise ValueError("Tool name cannot be empty")
        if name in self._tools:
            raise ValueError(f"Tool already registered: {name}")
        self._tools[name] = ToolSpec(name, spec.handler, spec.requires_confirmation)

    def available_tools(self) -> tuple[str, ...]:
        return tuple(self._tools)

    def execute(self, request: ActionRequest, *, confirmed: bool = False) -> ActionResult:
        if not request.tool:
            return ActionResult(request.task_id, False, error="action has no tool")
        spec = self._tools.get(request.tool)
        if spec is None:
            return ActionResult(request.task_id, False, error="tool is not allowlisted")
        if spec.requires_confirmation and not (confirmed or request.requires_confirmation is False):
            return ActionResult(request.task_id, False, error="tool requires confirmation")
        try:
            output = spec.handler(dict(request.arguments))
        except Exception:
            return ActionResult(request.task_id, False, error="tool execution failed")
        return ActionResult(request.task_id, True, output=output)
