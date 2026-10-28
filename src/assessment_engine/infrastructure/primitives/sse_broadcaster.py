import asyncio
import json
from typing import Any, AsyncGenerator
from dataclasses import dataclass


@dataclass
class SseEvent:
    event_name: str
    data_json: str


class SseBroadcaster:
    def __init__(self) -> None:
        self._subscribers: list[asyncio.Queue[Any]] = []

    def subscribe(self) -> asyncio.Queue[Any]:
        """Register a new subscriber and return its event queue."""
        q: asyncio.Queue[Any] = asyncio.Queue()
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[Any]) -> None:
        """Remove the specified subscriber queue from active subscriptions."""
        if q in self._subscribers:
            self._subscribers.remove(q)

    async def broadcast(self, event_name: str, payload: dict[str, Any]) -> None:
        """Broadcast an event and its payload to all active subscribers."""
        data_str = json.dumps(payload, ensure_ascii=False)
        ev = SseEvent(event_name, data_str)
        for q in list(self._subscribers):
            await q.put(ev)

    async def stream_for_client(self, q: asyncio.Queue[Any]) -> AsyncGenerator[str, None]:
        """Stream events from the subscriber queue for client consumption."""
        try:
            while True:
                ev: SseEvent = await q.get()
                yield f"event: {ev.event_name}\ndata: {ev.data_json}\n\n"
        except asyncio.CancelledError:
            self.unsubscribe(q)
