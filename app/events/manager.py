import asyncio
from collections import defaultdict


class WorkspaceEventManager:

    def __init__(self):
        self._subscribers: dict[int, set[asyncio.Queue]] = defaultdict(set)
        self._insights_generating: set[tuple[int, int]] = set()
        self._insights_lock = asyncio.Lock()

    async def subscribe(self, workspace_id: int) -> asyncio.Queue:
        queue = asyncio.Queue()
        self._subscribers[workspace_id].add(queue)
        return queue

    async def unsubscribe(
        self,
        workspace_id: int,
        queue: asyncio.Queue,
    ) -> None:
        subscribers = self._subscribers.get(workspace_id)

        if subscribers is None:
            return

        subscribers.discard(queue)

        if not subscribers:
            self._subscribers.pop(workspace_id, None)

    async def publish(
        self,
        workspace_id: int,
        event: dict,
    ) -> None:
        subscribers = self._subscribers.get(workspace_id)

        if not subscribers:
            return

        for queue in subscribers:
            await queue.put(event)

    async def start_insights_generation(
        self,
        workspace_id: int,
        document_id: int,
    ) -> bool:
        key = (workspace_id, document_id)

        async with self._insights_lock:
            if key in self._insights_generating:
                return False

            self._insights_generating.add(key)
            return True

    async def finish_insights_generation(
        self,
        workspace_id: int,
        document_id: int,
    ) -> None:
        key = (workspace_id, document_id)

        async with self._insights_lock:
            self._insights_generating.discard(key)


workspace_event_manager = WorkspaceEventManager()