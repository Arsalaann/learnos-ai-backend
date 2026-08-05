import asyncio
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.dependencies.workspace import get_current_workspace
from app.events.manager import workspace_event_manager
from app.models.workspace import Workspace

router = APIRouter()


@router.get("/{workspace_id}/events")
async def workspace_events( workspace: Workspace = Depends(get_current_workspace), ):
    queue = await workspace_event_manager.subscribe(workspace.id)

    async def event_stream():
        try:
            while True:
                try:
                    event = await asyncio.wait_for(
                        queue.get(),
                        timeout=30,
                    )

                    event_type = event["type"]

                    yield (
                        f"event: {event_type}\n"
                        f"data: {json.dumps(event)}\n\n"
                    )

                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"

        finally:
            await workspace_event_manager.unsubscribe(
                workspace.id,
                queue,
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )