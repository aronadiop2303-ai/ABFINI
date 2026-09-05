from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class TaskState(str, Enum):
    CREATED = "created"
    PLANNING = "planning"
    WAITING_TOOL = "waiting_tool"
    WAITING_CONFIRMATION = "waiting_confirmation"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    goal: str
    id: str = field(default_factory=lambda: str(uuid4()))
    state: TaskState = TaskState.CREATED
    plan: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionRequest:
    task_id: str
    action: str
    tool: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)
    requires_confirmation: bool = False


@dataclass
class ActionResult:
    task_id: str
    success: bool
    output: Any = None
    error: str | None = None
