import os
import secrets
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/api/admin", tags=["admin_auth"])

# The admin password is stored in an environment variable
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")  # CHANGE THIS!

# In-memory token store (for simplicity; use DB in production)
active_tokens: set = set()


class LoginRequest(BaseModel):
    password: str


@router.post("/login")
def admin_login(req: LoginRequest):
    """Authenticate admin with password and return a bearer token."""
    if req.password != ADMIN_PASSWORD:
        raise HTTPException(401, "Incorrect password")
    # Generate a random token
    token = secrets.token_hex(32)
    active_tokens.add(token)
    return {"token": token}


@router.post("/logout")
def admin_logout(authorization: str = Header(None)):
    """Invalidate the current admin token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    token = authorization[7:]
    active_tokens.discard(token)
    return {"status": "logged out"}


def verify_admin_token(authorization: str = Header(None)):
    """Dependency to protect admin routes — validates the bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Admin token required")
    token = authorization[7:]
    if token not in active_tokens:
        raise HTTPException(403, "Invalid or expired admin token")
    return token
