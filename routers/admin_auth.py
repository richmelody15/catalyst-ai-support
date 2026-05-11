import os
import jwt
import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Header, Request, Response, Body
from pydantic import BaseModel
from database import SessionLocal, AdminUser, AdminSession, AdminActivityLog
from config import settings

router = APIRouter(prefix="/api/admin", tags=["admin_auth"])

# JWT configuration — persist generated secret to file so it survives restarts
_SECRET_FILE = os.path.join(os.path.dirname(__file__), "..", ".jwt_secret")

def _get_jwt_secret() -> str:
    """Get or create a persistent JWT secret."""
    # 1. Environment variable takes priority
    env_secret = os.environ.get("JWT_SECRET")
    if env_secret:
        return env_secret
    # 2. Config setting
    if settings.JWT_SECRET:
        return settings.JWT_SECRET
    # 3. Persisted file
    if os.path.exists(_SECRET_FILE):
        with open(_SECRET_FILE, "r") as f:
            return f.read().strip()
    # 4. Generate new and persist
    new_secret = secrets.token_hex(32)
    with open(_SECRET_FILE, "w") as f:
        f.write(new_secret)
    return new_secret

JWT_SECRET = _get_jwt_secret()
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
REFRESH_TOKEN_EXPIRE_DAYS_REMEMBER = 30


# ---------- Request / Response Models ----------

class LoginRequest(BaseModel):
    email: str
    password: str
    remember_me: bool = False
    platform: str = "web"
    device_info: str = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    admin_id: int
    email: str
    full_name: str


# ---------- Helper Functions ----------

def create_access_token(admin_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(admin_id), "exp": expire, "type": "access"}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def create_refresh_token(admin_id: int, remember: bool = False) -> str:
    days = REFRESH_TOKEN_EXPIRE_DAYS_REMEMBER if remember else REFRESH_TOKEN_EXPIRE_DAYS
    expire = datetime.utcnow() + timedelta(days=days)
    return jwt.encode({"sub": str(admin_id), "exp": expire, "type": "refresh"}, JWT_SECRET, algorithm="HS256")


def verify_token(token: str, expected_type: str = "access") -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("type") != expected_type:
            raise ValueError("Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except Exception:
        raise HTTPException(401, "Invalid token")


def log_activity(admin_id: int, action: str, details: str = None, ip_address: str = None):
    """Helper to log admin activity."""
    db = SessionLocal()
    try:
        log = AdminActivityLog(
            admin_id=admin_id,
            action=action,
            details=details,
            ip_address=ip_address
        )
        db.add(log)
        db.commit()
    except Exception:
        pass
    finally:
        db.close()


# ---------- Login ----------

@router.post("/login", response_model=TokenResponse)
async def admin_login(request: Request, response: Response, data: LoginRequest):
    db = SessionLocal()
    admin = db.query(AdminUser).filter_by(email=data.email).first()
    if not admin or not admin.verify_password(data.password):
        raise HTTPException(401, "Invalid email or password")

    access_token = create_access_token(admin.id)
    refresh_token = create_refresh_token(admin.id, data.remember_me)

    # Save session
    days = REFRESH_TOKEN_EXPIRE_DAYS_REMEMBER if data.remember_me else REFRESH_TOKEN_EXPIRE_DAYS
    session = AdminSession(
        admin_id=admin.id,
        refresh_token=refresh_token,
        user_agent=request.headers.get("user-agent", "unknown"),
        ip_address=request.client.host,
        platform=data.platform,
        device_info=data.device_info,
        expires_at=datetime.utcnow() + timedelta(days=days)
    )
    db.add(session)

    # Update last login
    admin.last_login = datetime.utcnow()
    db.commit()

    # For web, set refresh token in a secure httpOnly cookie
    if data.platform == "web":
        response.set_cookie(
            key="admin_refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=60 * 60 * 24 * days,
            path="/"
        )

    # Log activity
    log_activity(
        admin.id, "login",
        f"Logged in via {data.platform}" + (f" on {data.device_info}" if data.device_info else ""),
        request.client.host
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        admin_id=admin.id,
        email=admin.email,
        full_name=admin.full_name or "Admin"
    )


# ---------- Refresh ----------

@router.post("/refresh")
async def refresh_token(request: Request, response: Response, refresh_token_body: str = Body(None)):
    """Accept refresh token from cookie (web) OR request body (mobile)."""
    refresh_token_val = request.cookies.get("admin_refresh_token")
    if not refresh_token_val and refresh_token_body:
        refresh_token_val = refresh_token_body

    if not refresh_token_val:
        raise HTTPException(401, "No refresh token provided")

    payload = verify_token(refresh_token_val, "refresh")
    admin_id = payload["sub"]

    db = SessionLocal()
    session = db.query(AdminSession).filter_by(
        refresh_token=refresh_token_val, is_active=True
    ).first()
    if not session:
        raise HTTPException(401, "Session expired or invalid")

    if datetime.utcnow() > session.expires_at:
        session.is_active = False
        db.commit()
        raise HTTPException(401, "Session expired")

    access_token = create_access_token(admin_id)

    log_activity(admin_id, "token_refresh", "Access token refreshed", request.client.host)

    return {"access_token": access_token, "admin_id": admin_id}


# ---------- Logout ----------

@router.post("/logout")
async def admin_logout(request: Request, response: Response, refresh_token_body: str = Body(None)):
    refresh_token_val = request.cookies.get("admin_refresh_token") or refresh_token_body
    if refresh_token_val:
        db = SessionLocal()
        session = db.query(AdminSession).filter_by(
            refresh_token=refresh_token_val, is_active=True
        ).first()
        if session:
            session.is_active = False
            db.commit()
            log_activity(session.admin_id, "logout", "Admin logged out", request.client.host)
    response.delete_cookie("admin_refresh_token")
    return {"status": "logged out"}


# ---------- Verify Admin Token Dependency ----------

def verify_admin_token(authorization: str = Header(None)) -> int:
    """Dependency for protected admin routes. Returns admin_id (int)."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Admin token required")
    token = authorization[7:]
    payload = verify_token(token, "access")
    return int(payload["sub"])


# ---------- Activity Log ----------

@router.get("/activity")
def get_activity(limit: int = 20, admin_id: int = Depends(verify_admin_token)):
    db = SessionLocal()
    logs = db.query(AdminActivityLog).order_by(
        AdminActivityLog.timestamp.desc()
    ).limit(limit).all()
    result = [
        {
            "action": l.action,
            "details": l.details,
            "timestamp": str(l.timestamp),
            "ip": l.ip_address
        }
        for l in logs
    ]
    db.close()
    return result
