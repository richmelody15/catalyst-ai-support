from fastapi import APIRouter, HTTPException, Depends, Header
from database import SessionLocal, Giveaway, GiveawayParticipant, User
from datetime import datetime
import random

from config import settings

router = APIRouter(prefix="/api/giveaways", tags=["giveaways"])

# Admin verification
def verify_admin(x_admin_id: int = Header(None)):
    if x_admin_id != settings.ADMIN_CHAT_ID:
        raise HTTPException(403, "Admin access required")
    return x_admin_id


# ── Admin endpoints ──────────────────────────────────────────────────

@router.post("/create")
def create_giveaway(
    title: str, description: str, start_time: str, end_time: str,
    prize: str, winners_count: int = 1,
    admin_id: int = Depends(verify_admin)
):
    db = SessionLocal()
    g = Giveaway(
        title=title, description=description,
        start_time=datetime.fromisoformat(start_time),
        end_time=datetime.fromisoformat(end_time),
        prize=prize, winners_count=winners_count,
        created_by=admin_id,
        status="upcoming"
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    db.close()
    return {"giveaway_id": g.id}

@router.put("/update/{giveaway_id}")
def update_giveaway(giveaway_id: int, fields: dict, admin_id: int = Depends(verify_admin)):
    db = SessionLocal()
    g = db.query(Giveaway).filter_by(id=giveaway_id).first()
    if not g:
        db.close()
        raise HTTPException(404, "Giveaway not found")
    for f in ['title', 'description', 'start_time', 'end_time', 'prize', 'winners_count', 'status']:
        if f in fields:
            if f in ('start_time', 'end_time'):
                setattr(g, f, datetime.fromisoformat(fields[f]))
            else:
                setattr(g, f, fields[f])
    db.commit()
    db.close()
    return {"status": "updated"}

@router.post("/draw/{giveaway_id}")
def draw_winners(giveaway_id: int, admin_id: int = Depends(verify_admin)):
    db = SessionLocal()
    g = db.query(Giveaway).filter_by(id=giveaway_id).first()
    if not g:
        db.close()
        raise HTTPException(404, "Giveaway not found")
    if g.status != "active":
        db.close()
        raise HTTPException(400, "Giveaway is not active")
    participants = db.query(GiveawayParticipant).filter_by(giveaway_id=giveaway_id).all()
    user_ids = [p.user_id for p in participants]
    if len(user_ids) < g.winners_count:
        db.close()
        raise HTTPException(400, "Not enough participants")
    winners = random.sample(user_ids, g.winners_count)
    g.status = "ended"
    db.commit()
    winner_users = db.query(User).filter(User.id.in_(winners)).all()
    result = {
        "winners": [
            {"id": u.id, "username": u.username, "telegram_id": u.telegram_id}
            for u in winner_users
        ]
    }
    db.close()
    return result


# ── Public endpoints ─────────────────────────────────────────────────

@router.get("/active")
def active_giveaways():
    db = SessionLocal()
    now = datetime.utcnow()
    giveaways = db.query(Giveaway).filter(
        Giveaway.start_time <= now,
        Giveaway.end_time >= now,
        Giveaway.status == "active"
    ).all()
    result = [
        {
            "id": g.id, "title": g.title,
            "description": g.description, "prize": g.prize,
            "end_time": str(g.end_time),
            "participants": db.query(GiveawayParticipant).filter_by(giveaway_id=g.id).count()
        }
        for g in giveaways
    ]
    db.close()
    return result

@router.get("/list")
def list_giveaways(status: str = None):
    db = SessionLocal()
    query = db.query(Giveaway)
    if status:
        query = query.filter_by(status=status)
    giveaways = query.order_by(Giveaway.start_time.desc()).all()
    result = [
        {
            "id": g.id, "title": g.title, "description": g.description,
            "prize": g.prize, "status": g.status,
            "start_time": str(g.start_time), "end_time": str(g.end_time),
            "winners_count": g.winners_count,
            "participants": db.query(GiveawayParticipant).filter_by(giveaway_id=g.id).count()
        }
        for g in giveaways
    ]
    db.close()
    return result

@router.post("/join/{giveaway_id}")
def join_giveaway(giveaway_id: int, user_id: int):
    db = SessionLocal()
    g = db.query(Giveaway).filter_by(id=giveaway_id).first()
    if not g:
        db.close()
        raise HTTPException(404, "Giveaway not found")
    now = datetime.utcnow()
    if now < g.start_time or now > g.end_time:
        db.close()
        raise HTTPException(400, "Giveaway not active")
    existing = db.query(GiveawayParticipant).filter_by(giveaway_id=giveaway_id, user_id=user_id).first()
    if existing:
        db.close()
        return {"status": "already_joined"}
    participant = GiveawayParticipant(giveaway_id=giveaway_id, user_id=user_id)
    db.add(participant)
    # Auto-activate if start time reached
    if g.status == "upcoming" and now >= g.start_time:
        g.status = "active"
    db.commit()
    db.close()
    return {"status": "joined"}
