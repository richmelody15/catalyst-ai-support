from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from database import SessionLocal, User, AppSettings
from datetime import datetime
import asyncio
import logging

from config import settings

logger = logging.getLogger(__name__)


async def paywall_middleware(request: Request, call_next):
    """Middleware that enforces paywall on protected routes.

    - Skips admin routes, static files, API docs, and public endpoints
    - Checks AppSettings.paywall_enabled flag
    - Validates user subscription status via user_token cookie
    - Sends email alert to admin on unauthorized access attempts (if enabled)
    """
    path = request.url.path

    # Skip admin routes, static, docs, and public endpoints
    skip_prefixes = (
        "/api/admin", "/api/paywall/plans", "/api/auth",
        "/api/notifications", "/static", "/docs", "/openapi",
        "/redoc", "/login", "/plans", "/"
    )
    if any(path.startswith(p) for p in skip_prefixes):
        return await call_next(request)

    # Also skip root and dashboard if user is just browsing
    if path == "/" or path == "/dashboard":
        return await call_next(request)

    db = SessionLocal()
    try:
        # Get app settings
        app_settings = db.query(AppSettings).first()
        if not app_settings or not app_settings.paywall_enabled:
            return await call_next(request)  # paywall off — allow

        # Check if current path is protected
        protected = [p.strip() for p in app_settings.protected_routes.split(",") if p.strip()]
        if not any(path.startswith(p) for p in protected):
            return await call_next(request)  # not a protected route

        # Check user subscription
        token = request.cookies.get("user_token")
        if not token:
            if path.startswith("/api/"):
                raise HTTPException(401, "Login required")
            return RedirectResponse("/login")

        try:
            tg_id = int(token)
        except ValueError:
            if path.startswith("/api/"):
                raise HTTPException(401, "Invalid user token")
            return RedirectResponse("/login")

        user = db.query(User).filter_by(telegram_id=tg_id).first()
        if not user:
            if path.startswith("/api/"):
                raise HTTPException(401, "Invalid user")
            return RedirectResponse("/login")

        now = datetime.utcnow()
        if user.subscription_status.value != "premium":
            # Check if subscription has expired but wasn't updated
            if user.subscription_end and user.subscription_end > now:
                from database import SubscriptionStatus
                user.subscription_status = SubscriptionStatus.premium
                db.commit()
            else:
                # Send admin alert (non-blocking) if email alerts enabled
                if app_settings.email_alerts and settings.ADMIN_EMAIL:
                    user_identity = user.full_name or user.username or str(user.telegram_id)
                    from email_utils import send_email
                    asyncio.create_task(
                        send_email(
                            to=settings.ADMIN_EMAIL,
                            subject="Paywall Bypass Attempt",
                            body=f"User {user_identity} (ID: {user.telegram_id}) tried to access '{path}' without a subscription."
                        )
                    )

                if path.startswith("/api/"):
                    raise HTTPException(402, "Subscription required")
                return RedirectResponse("/plans")
    finally:
        db.close()

    return await call_next(request)
