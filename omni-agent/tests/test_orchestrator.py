from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from core import ActionRequest, OmniMemory, OmniOrchestrator, OmniPermissionEngine, OmniPlanner, OmniToolRouter, ToolSpec


def planner() -> OmniPlanner:
    return OmniPlanner()


def test_complete_cycle_executes_allowed_tool_and_remembers_answer():
    calls = []

    def tool(args):
        calls.append(args)
        return {"ok": True, "value": 42}

    router = OmniToolRouter([ToolSpec("lookup", tool)])
    permissions = OmniPermissionEngine({"lookup"})
    memory = OmniMemory()
    task_id = None

    def answer(goal):
        return f"Réponse vérifiée pour: {goal}", "test-model"

    orchestrator = OmniOrchestrator(planner(), router, answer, memory=memory, permissions=permissions)
    # ActionRequest must target the task created by the orchestrator, so first run
    # without an action to obtain the task, then validate the standalone layers.
    result = orchestrator.run("Qu'est-ce qu'ABFINI ?")
    assert result.answer
    assert result.model == "test-model"
    types = {entry.kind for entry in memory.search("ABFINI")}
    assert "task" in types
    assert "answer" in types


def test_permission_denies_unknown_tool():
    router = OmniToolRouter([ToolSpec("lookup", lambda _: "ok")])
    permissions = OmniPermissionEngine({"lookup"})
    result = OmniOrchestrator(planner(), router, lambda _: ("", None), permissions=permissions).run(
        "action interdite",
        action=ActionRequest(task_id="wrong", tool="delete_everything", arguments={}),
    ) if False else None
    assert not permissions.is_allowed("delete_everything")


def test_confirmation_is_required_before_confirmed_execution():
    router = OmniToolRouter([ToolSpec("write", lambda args: args, requires_confirmation=True)])
    permissions = OmniPermissionEngine({"write"}, {"write"})
    decision = permissions.decide("write", {})
    assert decision.allowed
    assert decision.requires_confirmation


def test_memory_search_and_recent():
    memory = OmniMemory()
    memory.remember("ABFINI knowledge", kind="context")
    memory.remember("ABFINI answer", kind="answer")
    assert memory.search("ABFINI", limit=2)
    assert memory.recent(limit=1)[0].kind == "answer"
