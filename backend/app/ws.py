from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio

router = APIRouter()


class CountdownManager:
    """Gère les connexions WS par room (mission_id)."""

    def __init__(self):
        self._rooms: dict[str, list[WebSocket]] = {}

    async def connect(self, ws: WebSocket, room: str) -> None:
        await ws.accept()
        self._rooms.setdefault(room, []).append(ws)

    def disconnect(self, ws: WebSocket, room: str) -> None:
        if room in self._rooms:
            self._rooms[room] = [c for c in self._rooms[room] if c is not ws]

    async def broadcast(self, room: str, payload: dict) -> None:
        dead: list[WebSocket] = []
        for ws in self._rooms.get(room, []):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, room)

    def room_size(self, room: str) -> int:
        return len(self._rooms.get(room, []))


manager = CountdownManager()


@router.websocket("/countdown/{mission_id}/{session_id}")
async def countdown_ws(ws: WebSocket, mission_id: int, session_id: int):
    """
    Diffuse le ticker de compte à rebours toutes les secondes.
    Le client envoie {"action": "start", "duration_seconds": N} pour démarrer.
    Le serveur répond {type, remaining_seconds, percent} chaque seconde.
    """
    room = f"mission_{mission_id}_session_{session_id}"
    await manager.connect(ws, room)
    try:
        data = await ws.receive_json()
        duration = int(data.get("duration_seconds", 2700))
        remaining = duration

        while remaining >= 0:
            await manager.broadcast(room, {
                "type": "tick",
                "remaining_seconds": remaining,
                "percent": round((remaining / duration) * 100, 1),
            })
            if remaining == 0:
                await manager.broadcast(room, {"type": "timeout"})
                break
            await asyncio.sleep(1)
            remaining -= 1

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(ws, room)
