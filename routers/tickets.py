from fastapi import APIRouter, HTTPException
from database import SessionLocal, User, Ticket
from typing import List

router = APIRouter(prefix="/api/tickets", tags=["tickets"])

@router.get("/user/{telegram_id}")
def user_tickets(telegram_id: int):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    tickets = db.query(Ticket).filter_by(user_id=user.id).all()
    return [{"id": t.id, "subject": t.subject, "status": t.status, "created_at": str(t.created_at)} for t in tickets]

@router.post("/create")
def create_ticket(telegram_id: int, subject: str):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    ticket = Ticket(user_id=user.id, subject=subject)
    db.add(ticket)
    db.commit()
    return {"ticket_id": ticket.id}
