from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PermissionDecision:
    allowed: bool
    requires_confirmation: bool = False
    reason: str = ""


class OmniPermissionEngine:
    """Minimal deny-by-default permission layer for OMNI V0.2."""

    def __init__(self, allowed_tools: set[str] | None = None, confirmation_tools: set[str] | None = None) -> None:
        self._allowed = set(allowed_tools or set())
        self._confirmation = set(confirmation_tools or set())

    def allow_tool(self, tool: str, *, requires_confirmation: bool = False) -> None:
        name = tool.strip()
        if not name:
            raise ValueError("tool cannot be empty")
        self._allowed.add(name)
        if requires_confirmation:
            self._confirmation.add(name)

    def decide(self, tool: str | None, arguments: dict[str, Any] | None = None) -> PermissionDecision:
        if not tool or tool not in self._allowed:
            return PermissionDecision(False, reason="tool is not permitted")
        if tool in self._confirmation:
            return PermissionDecision(True, True, "user confirmation required")
        return PermissionDecision(True, False, "tool permitted")

    def is_allowed(self, tool: str | None) -> bool:
        return self.decide(tool).allowed
