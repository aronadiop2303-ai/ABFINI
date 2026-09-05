from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from core import ActionResult, OmniMemory, OmniOrchestrator, OmniPermissionEngine, OmniPlanner, OmniToolRouter, ToolSpec


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

    def answer(goal):
        return f"Réponse vérifiée pour: {goal}", "test-model"

    orchestrator = OmniOrchestrator(planner(), router, answer, memory=memory, permissions=permissions)
    result = orchestrator.run("Qu'est-ce qu'ABFINI ?", tool="lookup", tool_arguments={"query": "ABFINI"})

    assert calls == [{"query": "ABFINI"}]
    assert result.tool_results == [ActionResult(result.task.id, True, output={"ok": True, "value": 42})]
    assert result.answer
    assert result.model == "test-model"
    types = {entry.kind for entry in memory.search("ABFINI")}
    assert "task" in types
    assert "answer" in types


def test_permission_denies_unknown_tool():
    router = OmniToolRouter([ToolSpec("lookup", lambda _: "ok")])
    permissions = OmniPermissionEngine({"lookup"})
    orchestrator = OmniOrchestrator(planner(), router, lambda _: ("", None), permissions=permissions)

    result = orchestrator.run("action interdite", tool="delete_everything")

    assert result.answer == ""
    assert result.tool_results == [ActionResult(result.task.id, False, error="tool is not permitted")]


def test_confirmation_is_required_before_confirmed_execution():
    router = OmniToolRouter([ToolSpec("write", lambda args: args, requires_confirmation=True)])
    permissions = OmniPermissionEngine({"write"}, {"write"})
    orchestrator = OmniOrchestrator(planner(), router, lambda _: ("done", "test-model"), permissions=permissions)

    unconfirmed = orchestrator.run("écrire un fichier", tool="write", tool_arguments={"path": "a.txt"})
    assert unconfirmed.tool_results == [
        ActionResult(unconfirmed.task.id, False, error="user confirmation required")
    ]
    assert unconfirmed.answer == ""

    confirmed = orchestrator.run(
        "écrire un fichier", tool="write", tool_arguments={"path": "a.txt"}, confirmed=True
    )
    assert confirmed.tool_results == [ActionResult(confirmed.task.id, True, output={"path": "a.txt"})]
    assert confirmed.answer == "done"


def test_memory_search_and_recent():
    memory = OmniMemory()
    memory.remember("ABFINI knowledge", kind="context")
    memory.remember("ABFINI answer", kind="answer")
    assert memory.search("ABFINI", limit=2)
    assert memory.recent(limit=1)[0].kind == "answer"
