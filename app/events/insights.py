from app.events.manager import workspace_event_manager


async def publish_insights_status(
    workspace_id: int,
    document_id: int,
    status: str,
    error: str | None = None,
) -> None:
    await workspace_event_manager.publish(
        workspace_id=workspace_id,
        event={
            "type": "insights.status",
            "document_id": document_id,
            "status": status,
            "error": error,
        },
    )