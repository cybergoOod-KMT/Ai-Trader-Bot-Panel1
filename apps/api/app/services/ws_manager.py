from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class WSManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._topic_connections: dict[str, dict[str, set[WebSocket]]] = defaultdict(lambda: defaultdict(set))
        self._lock = asyncio.Lock()

    async def connect(self, channel: str, websocket: WebSocket, topic: str | None = None) -> None:
        await websocket.accept()
        async with self._lock:
            if topic:
                self._topic_connections[channel][topic].add(websocket)
            else:
                self._connections[channel].add(websocket)

    async def disconnect(self, channel: str, websocket: WebSocket, topic: str | None = None) -> None:
        async with self._lock:
            if topic:
                subscribers = self._topic_connections[channel].get(topic, set())
                subscribers.discard(websocket)
                if not subscribers and topic in self._topic_connections[channel]:
                    self._topic_connections[channel].pop(topic, None)
            else:
                self._connections[channel].discard(websocket)

    async def publish(self, channel: str, event: str, payload: Any, topic: str | None = None) -> None:
        message = {"channel": channel, "event": event, "payload": payload}
        async with self._lock:
            sockets = set(self._connections[channel])
            if topic:
                sockets |= set(self._topic_connections[channel].get(topic, set()))
        dead: list[tuple[WebSocket, str | None]] = []
        for websocket in sockets:
            try:
                await websocket.send_json(message)
            except Exception:  # noqa: BLE001
                dead.append((websocket, topic))
        for websocket, ws_topic in dead:
            await self.disconnect(channel, websocket, topic=ws_topic)

    def snapshot(self) -> dict[str, Any]:
        return {
            "channels": {name: len(items) for name, items in self._connections.items()},
            "topics": {
                channel: {topic: len(items) for topic, items in topics.items()}
                for channel, topics in self._topic_connections.items()
            },
        }


ws_manager = WSManager()
