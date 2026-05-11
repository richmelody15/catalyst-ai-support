from fastapi import APIRouter, Header, HTTPException, Depends
from database import SessionLocal, User, Ticket, Message, SignalHistory
from routers.admin_auth import verify_admin_token

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats", dependencies=[Depends(verify_admin_token)])
def admin_stats():
    """Admin-only: get system statistics."""
    db = SessionLocal()
    stats = {
        "total_users": db.query(User).count(),
        "premium_users": db.query(User).filter_by(subscription_status="premium").count(),
        "open_tickets": db.query(Ticket).filter_by(status="open").count(),
        "total_messages": db.query(Message).count(),
        "total_signals": db.query(SignalHistory).count(),
    }
    db.close()
    return stats
