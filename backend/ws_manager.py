"""
WebSocket connection manager — extracted here so both main.py and
orchestrator.py can import it without a circular dependency.
"""

from typing import Any, Dict, Set

from fastapi import WebSocket


class ConnectionManager:
    """Tracks active WebSocket connections keyed by pipeline_id."""

    def __init__(self) -> None:
        self._connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, pipeline_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.setdefault(pipeline_id, set()).add(ws)

    def disconnect(self, pipeline_id: str, ws: WebSocket) -> None:
        if pipeline_id in self._connections:
            self._connections[pipeline_id].discard(ws)

    async def broadcast(self, pipeline_id: str, message: Dict[str, Any]) -> None:
        dead: Set[WebSocket] = set()
        for ws in self._connections.get(pipeline_id, set()):
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        if dead:
            self._connections[pipeline_id] -= dead


# Singleton used by both main.py and orchestrator.py
ws_manager = ConnectionManager()
