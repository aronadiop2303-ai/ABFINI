from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from core import ActionRequest, OmniToolRouter, ToolSpec


def test_execute_runs_allowlisted_tool():
    router = OmniToolRouter([ToolSpec("lookup", lambda args: {"echo": args})])
    result = router.execute(ActionRequest(task_id="t1", action="lookup", tool="lookup", arguments={"q": "x"}))
    assert result.success
    assert result.output == {"echo": {"q": "x"}}


def test_execute_denies_tool_not_allowlisted():
    router = OmniToolRouter()
    result = router.execute(ActionRequest(task_id="t1", action="lookup", tool="lookup"))
    assert not result.success
    assert result.error == "tool is not allowlisted"


def test_execute_denies_action_without_tool():
    router = OmniToolRouter()
    result = router.execute(ActionRequest(task_id="t1", action="noop", tool=None))
    assert not result.success
    assert result.error == "action has no tool"


def test_execute_blocks_confirmation_required_tool_by_default():
    router = OmniToolRouter([ToolSpec("write", lambda args: "written", requires_confirmation=True)])
    request = ActionRequest(task_id="t1", action="write", tool="write")

    denied = router.execute(request)
    assert not denied.success
    assert denied.error == "tool requires confirmation"

    allowed = router.execute(request, confirmed=True)
    assert allowed.success
    assert allowed.output == "written"


def test_execute_catches_tool_exceptions():
    def boom(_args):
        raise RuntimeError("kaboom")

    router = OmniToolRouter([ToolSpec("boom", boom)])
    result = router.execute(ActionRequest(task_id="t1", action="boom", tool="boom"))
    assert not result.success
    assert result.error == "tool execution failed"
