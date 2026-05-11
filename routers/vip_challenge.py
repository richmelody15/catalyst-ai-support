from fastapi import APIRouter, Depends, HTTPException
from routers.admin_auth import verify_admin_token, log_activity
from database import SessionLocal, VIPChallenge, VIPChallengeParticipant, User, SignalHistory
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/vip-challenge", tags=["vip_challenge"])


# ---------- Request Models ----------

class CreateChallengeRequest(BaseModel):
    name: str
    description: str = ""
    start_time: str
    end_time: str
    entry_fee: float = 0.0
    prize_pool: float = 0.0


# ---------- Admin Endpoints ----------

@router.post("/create")
def create_challenge(data: CreateChallengeRequest, admin_id: int = Depends(verify_admin_token)):
    """Admin-only: create a new VIP challenge."""
    db = SessionLocal()
    ch = VIPChallenge(
        name=data.name,
        description=data.description,
        start_time=datetime.fromisoformat(data.start_time),
        end_time=datetime.fromisoformat(data.end_time),
        entry_fee=data.entry_fee,
        prize_pool=data.prize_pool,
        created_by=admin_id,
        status="upcoming"
    )
    db.add(ch)
    db.commit()
    db.refresh(ch)
    log_activity(admin_id, "create_vip_challenge", f"Created VIP challenge '{data.name}' (id={ch.id})")
    db.close()
    return {"challenge_id": ch.id, "status": "created"}


@router.put("/{challenge_id}/status")
def update_status(challenge_id: int, status: str, admin_id: int = Depends(verify_admin_token)):
    """Admin-only: update challenge status (upcoming/active/ended)."""
    if status not in ("upcoming", "active", "ended"):
        raise HTTPException(400, "Status must be upcoming, active, or ended")
    db = SessionLocal()
    ch = db.query(VIPChallenge).filter_by(id=challenge_id).first()
    if not ch:
        db.close()
        raise HTTPException(404, "Challenge not found")
    ch.status = status
    db.commit()
    log_activity(admin_id, "update_vip_challenge_status", f"Challenge #{challenge_id} → {status}")
    db.close()
    return {"status": status}


@router.delete("/{challenge_id}")
def delete_challenge(challenge_id: int, admin_id: int = Depends(verify_admin_token)):
    """Admin-only: delete a VIP challenge."""
    db = SessionLocal()
    ch = db.query(VIPChallenge).filter_by(id=challenge_id).first()
    if not ch:
        db.close()
        raise HTTPException(404, "Challenge not found")
    # Remove participants first
    db.query(VIPChallengeParticipant).filter_by(challenge_id=challenge_id).delete()
    db.delete(ch)
    db.commit()
    log_activity(admin_id, "delete_vip_challenge", f"Deleted challenge #{challenge_id}")
    db.close()
    return {"status": "deleted"}


@router.get("/admin/list")
def admin_list_challenges(admin_id: int = Depends(verify_admin_token)):
    """Admin-only: list all VIP challenges with full details."""
    db = SessionLocal()
    challenges = db.query(VIPChallenge).order_by(VIPChallenge.created_at.desc()).all()
    result = []
    for c in challenges:
        participants = db.query(VIPChallengeParticipant).filter_by(challenge_id=c.id).all()
        result.append({
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "start": str(c.start_time),
            "end": str(c.end_time),
            "entry_fee": c.entry_fee,
            "prize_pool": c.prize_pool,
            "status": c.status,
            "participants_count": len(participants),
            "created_at": str(c.created_at)
        })
    db.close()
    return result


# ---------- User Endpoints ----------

@router.post("/{challenge_id}/join")
def join_challenge(challenge_id: int, user_id: int):
    """Join a VIP challenge. Only premium users can join."""
    db = SessionLocal()
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        db.close()
        raise HTTPException(404, "User not found")
    if user.subscription_status.value != "premium":
        db.close()
        raise HTTPException(403, "Only premium users can join VIP challenges. Use /subscribe to upgrade.")

    challenge = db.query(VIPChallenge).filter_by(id=challenge_id).first()
    if not challenge:
        db.close()
        raise HTTPException(404, "Challenge not found")

    now = datetime.utcnow()
    # Allow joining if challenge is upcoming or active and within time range
    if challenge.status not in ("upcoming", "active"):
        db.close()
        raise HTTPException(400, "Challenge is not available for joining")
    if now > challenge.end_time:
        db.close()
        raise HTTPException(400, "Challenge has ended")

    # Already joined?
    existing = db.query(VIPChallengeParticipant).filter_by(
        challenge_id=challenge_id, user_id=user_id
    ).first()
    if existing:
        db.close()
        return {"status": "already_joined"}

    participant = VIPChallengeParticipant(challenge_id=challenge_id, user_id=user_id)
    db.add(participant)

    # Auto-activate if start time reached
    if challenge.status == "upcoming" and now >= challenge.start_time:
        challenge.status = "active"

    db.commit()
    db.close()
    return {"status": "joined"}


@router.get("/active")
def active_challenges():
    """List all currently active VIP challenges (public)."""
    now = datetime.utcnow()
    db = SessionLocal()
    challenges = db.query(VIPChallenge).filter(
        VIPChallenge.end_time >= now,
        VIPChallenge.status.in_(["active", "upcoming"])
    ).all()
    result = []
    for c in challenges:
        p_count = db.query(VIPChallengeParticipant).filter_by(challenge_id=c.id).count()
        result.append({
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "start": str(c.start_time),
            "end": str(c.end_time),
            "prize_pool": c.prize_pool,
            "entry_fee": c.entry_fee,
            "status": c.status,
            "participants_count": p_count
        })
    db.close()
    return result


@router.get("/{challenge_id}/leaderboard")
def leaderboard(challenge_id: int):
    """Get the leaderboard for a VIP challenge."""
    db = SessionLocal()
    challenge = db.query(VIPChallenge).filter_by(id=challenge_id).first()
    if not challenge:
        db.close()
        raise HTTPException(404, "Challenge not found")

    participants = db.query(VIPChallengeParticipant).filter_by(
        challenge_id=challenge_id
    ).order_by(VIPChallengeParticipant.score.desc()).all()

    result = []
    for i, p in enumerate(participants, 1):
        user = db.query(User).filter_by(id=p.user_id).first()
        wr = round(p.wins / (p.wins + p.losses) * 100, 1) if (p.wins + p.losses) else 0
        result.append({
            "rank": i,
            "user_id": p.user_id,
            "username": user.username if user else "Unknown",
            "full_name": user.full_name if user else "",
            "score": round(p.score, 1),
            "total_trades": p.total_trades,
            "wins": p.wins,
            "losses": p.losses,
            "win_rate": wr,
            "joined_at": str(p.joined_at)
        })
    db.close()
    return {"challenge": challenge.name, "leaderboard": result}


@router.post("/{challenge_id}/update-score")
def update_vip_score(challenge_id: int, user_id: int, outcome: str):
    """Update a participant's score after a trade outcome. Called internally after signal outcome."""
    db = SessionLocal()
    participant = db.query(VIPChallengeParticipant).filter_by(
        challenge_id=challenge_id, user_id=user_id
    ).first()
    if not participant:
        db.close()
        raise HTTPException(404, "Participant not found in this challenge")

    if outcome == "win":
        participant.score += 1.0
        participant.wins += 1
    elif outcome == "loss":
        participant.score -= 0.5
        participant.losses += 1

    participant.total_trades += 1
    db.commit()
    db.close()
    return {"status": "updated", "score": participant.score}
