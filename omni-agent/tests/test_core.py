from core import ActionResult, OmniCore, TaskState


def test_core_task_lifecycle():
    core = OmniCore()

    task = core.create_task("Vérifier le stock d'un produit BARDEC")
    assert task.state == TaskState.CREATED

    core.plan(task.id, ["Identifier le produit", "Vérifier le stock"])
    request = core.request_action(
        task.id,
        action="check_stock",
        tool="bardec.check_stock",
        arguments={"product_id": "demo"},
    )

    assert request.tool == "bardec.check_stock"
    assert task.state == TaskState.WAITING_TOOL

    core.apply_result(ActionResult(task.id, success=True, output={"stock": 4}))
    assert task.state == TaskState.COMPLETED
    assert [event["type"] for event in core.events] == [
        "task.created",
        "task.planned",
        "action.requested",
        "action.completed",
    ]
