from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))

from core import OmniAgent, OmniPlanner, OmniToolRouter


def test_agent_run_creates_task_plans_and_answers():
    agent = OmniAgent(OmniPlanner(), OmniToolRouter(), lambda goal: (f"Réponse: {goal}", "test-model"))

    run = agent.run("Qu'est-ce qu'ABFINI ?")

    assert run.task.goal == "Qu'est-ce qu'ABFINI ?"
    assert run.task.plan
    assert run.answer == "Réponse: Qu'est-ce qu'ABFINI ?"
    assert run.model == "test-model"
    assert run.tool_results == []


def test_agent_run_raises_on_empty_answer():
    agent = OmniAgent(OmniPlanner(), OmniToolRouter(), lambda _: ("   ", None))

    with pytest.raises(ValueError):
        agent.run("action sans réponse")
