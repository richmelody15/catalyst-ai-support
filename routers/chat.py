from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from ai_engine import ask_ai
from database import SessionLocal, Message

router = APIRouter()

@router.websocket("/ws/chat/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: int):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            db = SessionLocal()
            msg = Message(user_id=user_id, content=data, from_ai=False)
            db.add(msg); db.commit()
            reply = await ask_ai(data)
            ai_msg = Message(user_id=user_id, content=reply, from_ai=True)
            db.add(ai_msg); db.commit()
            await websocket.send_text(reply)
    except WebSocketDisconnect:
        pass
