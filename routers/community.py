from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from database import SessionLocal, CommunityMessage, User
import json
import asyncio
from datetime import datetime

router = APIRouter(tags=["community"])


class CommunityRoom:
    """Simple in-memory community chat room with WebSocket connections."""

    def __init__(self):
        self.connections: list[WebSocket] = []
        self.user_map: dict[WebSocket, dict] = {}   # ws → {user_id, username}

    async def connect(self, ws: WebSocket, user_id: int, username: str):
        await ws.accept()
        self.connections.append(ws)
        self.user_map[ws] = {"user_id": user_id, "username": username}
        # Send last 50 messages as history
        history = self._get_history()
        await ws.send_text(json.dumps({"type": "history", "messages": history}))
        # Broadcast join
        await self.broadcast(system=True, text=f"{username} joined the room")

    def disconnect(self, ws: WebSocket):
        if ws in self.connections:
            self.connections.remove(ws)
        user_info = self.user_map.pop(ws, {})
        username = user_info.get("username", "Someone")
        # Schedule broadcast of leave (fire and forget)
        if self.connections:
            asyncio.create_task(self._broadcast_leave(username))

    async def _broadcast_leave(self, username: str):
        await self.broadcast(system=True, text=f"{username} left the room")

    async def broadcast(self, system: bool = False, text: str = None, user_id: int = None,
                        username: str = None, msg_id: int = None):
        message = {
            "type": "system" if system else "message",
            "text": text,
            "user_id": user_id,
            "username": username,
            "message_id": msg_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        raw = json.dumps(message)
        disconnected = []
        for ws in self.connections:
            try:
                await ws.send_text(raw)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.connections.remove(ws)
            self.user_map.pop(ws, None)

    def _get_history(self, limit: int = 50) -> list:
        """Fetch recent messages from the database."""
        db = SessionLocal()
        try:
            rows = db.query(CommunityMessage).order_by(
                CommunityMessage.created_at.desc()
            ).limit(limit).all()
            return [
                {
                    "id": m.id,
                    "user_id": m.user_id,
                    "username": m.username,
                    "content": m.content,
                    "timestamp": str(m.created_at)
                }
                for m in reversed(rows)
            ]
        finally:
            db.close()

    def save_message(self, user_id: int, username: str, content: str) -> int:
        """Persist a message to the database."""
        db = SessionLocal()
        try:
            msg = CommunityMessage(user_id=user_id, username=username, content=content)
            db.add(msg)
            db.commit()
            db.refresh(msg)
            return msg.id
        finally:
            db.close()


# Global community room instance
community_room = CommunityRoom()


@router.websocket("/ws/community/{user_id}")
async def ws_community(websocket: WebSocket, user_id: int):
    """WebSocket endpoint for the community chat room.

    All connected users share the same room. Messages are persisted to the
    CommunityMessage table and broadcast to everyone in real-time.
    """
    # Look up username
    db = SessionLocal()
    user = db.query(User).filter_by(id=user_id).first()
    db.close()
    username = user.username or user.full_name or f"User#{user_id}" if user else f"User#{user_id}"

    await community_room.connect(websocket, user_id, username)
    try:
        while True:
            data = await websocket.receive_text()
            # Parse message (expect plain text or JSON)
            try:
                parsed = json.loads(data)
                content = parsed.get("message", data).strip()
            except (json.JSONDecodeError, AttributeError):
                content = data.strip()

            if not content:
                continue

            # Save to DB
            msg_id = community_room.save_message(user_id, username, content)

            # Broadcast to all
            await community_room.broadcast(
                system=False,
                text=content,
                user_id=user_id,
                username=username,
                msg_id=msg_id
            )
    except WebSocketDisconnect:
        community_room.disconnect(websocket)
    except Exception:
        community_room.disconnect(websocket)


# ---------- REST endpoints for community ----------

@router.get("/api/community/messages")
def get_community_messages(limit: int = 50):
    """REST endpoint to fetch recent community messages (for initial load or fallback)."""
    db = SessionLocal()
    rows = db.query(CommunityMessage).order_by(
        CommunityMessage.created_at.desc()
    ).limit(limit).all()
    result = [
        {
            "id": m.id,
            "user_id": m.user_id,
            "username": m.username,
            "content": m.content,
            "timestamp": str(m.created_at)
        }
        for m in reversed(rows)
    ]
    db.close()
    return {"messages": result}
