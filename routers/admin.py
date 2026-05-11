from fastapi import APIRouter, Header, HTTPException, Depends
from database import SessionLocal, User, Ticket, Message
from config import settings

router = APIRouter(prefix="/api/admin", tags=["admin"])

def admin_required(x_admin_id: int = Header(None)):
    if x_admin_id != settings.ADMIN_CHAT_ID:
        raise HTTPException(403, "Admin access only")
    return x_admin_id

@router.get("/stats", dependencies=[Depends(admin_required)])
def admin_stats():
    db = SessionLocal()
    return {
        "total_users": db.query(User).count(),
        "premium_users": db.query(User).filter_by(subscription_status="premium").count(),
        "open_tickets": db.query(Ticket).filter_by(status="open").count(),
        "total_messages": db.query(Message).count()
    }
