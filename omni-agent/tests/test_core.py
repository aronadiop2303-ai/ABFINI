from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))

from core import ActionResult, OmniCore, TaskState


def test_core_task_lifecycle():
    core = OmniCore()
    task = core.create_task("Vérifier le stock d'un produit BARDEC")
    assert task.state == TaskState.CREATED
    core.plan(task.id, ["Identifier le produit", "Vérifier le stock"])
    request = core.request_action(task.id, action="check_stock", tool="bardec.check_stock", arguments={"product_id": "demo"})
    assert request.tool == "bardec.check_stock"
    assert task.state == TaskState.WAITING_TOOL
    core.apply_result(ActionResult(task.id, success=True, output={"stock": 4}))
    assert task.state == TaskState.COMPLETED
    assert [event["type"] for event in core.events] == ["task.created", "task.planned", "action.requested", "action.completed"]


def test_core_confirmation_cycle_states():
    core = OmniCore()
    task = core.create_task("Envoyer un email sensible")
    core.plan(task.id, ["Rédiger", "Envoyer"])
    core.request_action(task.id, action="send_email", tool="email.send", requires_confirmation=True)

    core.wait_for_confirmation(task.id)
    assert task.state == TaskState.WAITING_CONFIRMATION

    core.start_execution(task.id)
    assert task.state == TaskState.EXECUTING

    core.apply_result(ActionResult(task.id, success=True, output={"sent": True}))
    assert task.state == TaskState.COMPLETED
    assert [event["type"] for event in core.events] == [
        "task.created",
        "task.planned",
        "action.requested",
        "action.waiting_confirmation",
        "action.executing",
        "action.completed",
    ]


def test_core_cancel_from_waiting_confirmation():
    core = OmniCore()
    task = core.create_task("Supprimer un enregistrement")
    core.plan(task.id, ["Identifier", "Supprimer"])
    core.request_action(task.id, action="delete_record", tool="db.delete", requires_confirmation=True)
    core.wait_for_confirmation(task.id)

    core.cancel(task.id)

    assert task.state == TaskState.CANCELLED


def test_core_cancel_rejects_terminal_states():
    core = OmniCore()
    task = core.create_task("Tâche déjà terminée")
    core.plan(task.id, ["Étape unique"])
    core.apply_result(ActionResult(task.id, success=True))

    with pytest.raises(ValueError):
        core.cancel(task.id)
