from fastapi import APIRouter, HTTPException
from database import SessionLocal, User
from pydantic import BaseModel
from email_utils import send_email
from config import settings

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class UserInfoRequest(BaseModel):
    telegram_id: int
    email: str
    full_name: str


@router.post("/save-user-info")
async def save_user_info(info: UserInfoRequest):
    """Save user email and full name, then send a welcome email."""
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=info.telegram_id).first()
    if not user:
        db.close()
        raise HTTPException(404, "User not found")
    user.email = info.email
    user.full_name = info.full_name
    db.commit()

    # Send welcome email (non-blocking, graceful failure)
    await send_email(
        to=info.email,
        subject="Your profile is updated — Catalyst AI",
        body=(
            f"Hi {info.full_name},\n\n"
            f"Your email has been saved. You will now receive trading signals and alerts.\n\n"
            f"Team Catalyst AI"
        )
    )
    db.close()
    return {"status": "ok"}


@router.post("/alert-unauthorized")
async def alert_unauthorized(telegram_id: int = None, username: str = None, path: str = "/"):
    """Send admin an email alert when someone tries to bypass the paywall."""
    admin_email = settings.ADMIN_EMAIL
    if not admin_email:
        return {"status": "no_admin_email"}

    # Build user identity string
    user_info = "Unknown user"
    if telegram_id:
        db = SessionLocal()
        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        if user:
            user_info = f"{user.full_name or user.username} (ID: {user.telegram_id})"
            if user.email:
                user_info += f" [{user.email}]"
        else:
            user_info = f"User ID: {telegram_id}"
        db.close()
    elif username:
        user_info = username

    await send_email(
        to=admin_email,
        subject="Paywall Bypass Attempt",
        body=f"User {user_info} tried to access '{path}' without a subscription."
    )
    return {"status": "ok"}
