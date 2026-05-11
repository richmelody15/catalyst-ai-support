from fastapi import APIRouter
from database import SessionLocal, UserSettings

router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.get("/{user_id}")
def get_settings(user_id: int):
    db = SessionLocal()
    settings = db.query(UserSettings).filter_by(user_id=user_id).first()
    if not settings:
        settings = UserSettings(user_id=user_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    result = {
        "user_id": settings.user_id,
        "telegram_alerts": settings.telegram_alerts,
        "email_alerts": settings.email_alerts,
        "timezone": settings.timezone,
        "risk_level": settings.risk_level,
    }
    db.close()
    return result

@router.put("/{user_id}")
def update_settings(user_id: int, data: dict):
    db = SessionLocal()
    settings = db.query(UserSettings).filter_by(user_id=user_id).first()
    if not settings:
        settings = UserSettings(user_id=user_id)
        db.add(settings)
    for field in ["telegram_alerts", "email_alerts", "timezone", "risk_level"]:
        if field in data:
            setattr(settings, field, data[field])
    db.commit()
    db.close()
    return {"status": "updated"}
