from fastapi import APIRouter, HTTPException
from database import SessionLocal, User, Referral
import uuid

router = APIRouter(prefix="/api/referrals", tags=["referrals"])

@router.get("/link/{user_id}")
def get_referral_link(user_id: int):
    db = SessionLocal()
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        db.close()
        raise HTTPException(404, "User not found")
    code = str(uuid.uuid4())[:8]
    db.close()
    return {"link": f"https://catalyst-signals.up.railway.app/signup?ref={code}", "code": code}

@router.post("/register-referral")
def register_referral(referrer_id: int, name: str, email: str):
    db = SessionLocal()
    referrer = db.query(User).filter_by(id=referrer_id).first()
    if not referrer:
        db.close()
        raise HTTPException(404, "Referrer not found")
    ref = Referral(referrer_id=referrer_id, referred_name=name, referred_email=email)
    db.add(ref)
    db.commit()
    db.close()
    return {"status": "recorded"}

@router.get("/stats/{user_id}")
def referral_stats(user_id: int):
    db = SessionLocal()
    refs = db.query(Referral).filter_by(referrer_id=user_id).all()
    total = len(refs)
    joined = sum(1 for r in refs if r.status == "joined")
    db.close()
    return {"total_referrals": total, "joined": joined, "pending": total - joined}

@router.get("/list/{user_id}")
def list_referrals(user_id: int):
    db = SessionLocal()
    refs = db.query(Referral).filter_by(referrer_id=user_id).all()
    result = [
        {
            "id": r.id, "referred_name": r.referred_name,
            "referred_email": r.referred_email,
            "signup_date": str(r.signup_date), "status": r.status
        }
        for r in refs
    ]
    db.close()
    return result
