from fastapi import APIRouter, HTTPException
from database import SessionLocal, User
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["auth"])

class UserResponse(BaseModel):
    id: int
    telegram_id: int
    username: str | None
    full_name: str | None = None
    email: str | None = None
    subscription_status: str
    is_admin: bool
    class Config:
        from_attributes = True

@router.get("/me/{telegram_id}", response_model=UserResponse)
def get_user(telegram_id: int):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    return user
