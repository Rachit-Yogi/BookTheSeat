import asyncio
from collections import defaultdict
from fastapi import WebSocket

class SeatSocketManager:
    def __init__(self):
        self.connections: dict[int, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, showtime_id: int, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            self.connections[showtime_id].add(ws)

    async def disconnect(self, showtime_id: int, ws: WebSocket):
        async with self._lock:
            self.connections[showtime_id].discard(ws)
            if not self.connections[showtime_id]:
                self.connections.pop(showtime_id, None)

    async def broadcast(self, showtime_id: int, payload: dict):
        async with self._lock:
            sockets = list(self.connections.get(showtime_id, set()))
        stale = []
        for ws in sockets:
            try:
                await ws.send_json(payload)
            except Exception:
                stale.append(ws)
        for ws in stale:
            await self.disconnect(showtime_id, ws)

manager = SeatSocketManager()
