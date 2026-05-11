from fastapi import APIRouter, HTTPException
from database import SessionLocal, Tournament, TournamentParticipant, User
from datetime import datetime

router = APIRouter(prefix="/api/tournaments", tags=["tournaments"])

@router.post("/create")
def create(name: str, start: str, end: str, entry_fee: float = 0, prize_pool: float = 0, admin_id: int = None):
    db = SessionLocal()
    t = Tournament(
        name=name,
        start_time=datetime.fromisoformat(start),
        end_time=datetime.fromisoformat(end),
        entry_fee=entry_fee,
        prize_pool=prize_pool,
        created_by=admin_id
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    db.close()
    return {"tournament_id": t.id}

@router.post("/join")
def join(tournament_id: int, user_id: int):
    db = SessionLocal()
    t = db.query(Tournament).filter_by(id=tournament_id).first()
    if not t:
        db.close()
        raise HTTPException(404, "Tournament not found")
    now = datetime.utcnow()
    if now < t.start_time or now > t.end_time:
        db.close()
        raise HTTPException(400, "Tournament is not active")
    # Check if already joined
    existing = db.query(TournamentParticipant).filter_by(tournament_id=tournament_id, user_id=user_id).first()
    if existing:
        db.close()
        return {"status": "already_joined"}
    participant = TournamentParticipant(tournament_id=tournament_id, user_id=user_id)
    db.add(participant)
    # Auto-activate tournament if start time reached
    if t.status == "upcoming" and now >= t.start_time:
        t.status = "active"
    db.commit()
    db.close()
    return {"status": "joined"}

@router.get("/leaderboard/{tournament_id}")
def leaderboard(tournament_id: int):
    db = SessionLocal()
    participants = db.query(TournamentParticipant).filter_by(
        tournament_id=tournament_id
    ).order_by(TournamentParticipant.score.desc()).all()
    result = [{"user_id": p.user_id, "score": p.score, "rank": i + 1} for i, p in enumerate(participants)]
    db.close()
    return result

@router.get("/list")
def list_tournaments(status: str = None):
    db = SessionLocal()
    query = db.query(Tournament)
    if status:
        query = query.filter_by(status=status)
    tournaments = query.order_by(Tournament.start_time.desc()).all()
    result = [
        {
            "id": t.id, "name": t.name,
            "start_time": str(t.start_time), "end_time": str(t.end_time),
            "entry_fee": t.entry_fee, "prize_pool": t.prize_pool,
            "status": t.status,
            "participants": db.query(TournamentParticipant).filter_by(tournament_id=t.id).count()
        }
        for t in tournaments
    ]
    db.close()
    return result

@router.post("/update-score")
def update_score(tournament_id: int, user_id: int, score: float):
    db = SessionLocal()
    p = db.query(TournamentParticipant).filter_by(tournament_id=tournament_id, user_id=user_id).first()
    if not p:
        db.close()
        raise HTTPException(404, "Participant not found")
    p.score = score
    db.commit()
    db.close()
    return {"status": "updated"}
