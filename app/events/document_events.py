from app.events.manager import workspace_event_manager


async def publish_document_status(
    workspace_id: int,
    document_id: int,
    status: str,
    stage: str | None = None,
    progress: int | None = None,
    processing_error: str | None = None,
) -> None:
    await workspace_event_manager.publish(
        workspace_id=workspace_id,
        event={
            "type": "document.status",
            "document_id": document_id,
            "status": status,
            "stage": stage,
            "progress": progress,
            "processing_error": processing_error,
        },
    )