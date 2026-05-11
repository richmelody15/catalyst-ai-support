from fastapi import APIRouter, Depends, HTTPException
from database import SessionLocal, AppSettings
from routers.admin_auth import verify_admin_token, log_activity
from pydantic import BaseModel
import json

router = APIRouter(prefix="/api/admin/settings", tags=["admin_settings"])


# ── Helper ──────────────────────────────────────────────────────────

def _get_app_settings():
    """Get or create the singleton AppSettings row."""
    db = SessionLocal()
    app_settings = db.query(AppSettings).first()
    if not app_settings:
        app_settings = AppSettings()
        db.add(app_settings)
        db.commit()
        db.refresh(app_settings)
    return app_settings, db


# ── Admin Paywall Settings ──────────────────────────────────────────

@router.get("/paywall")
def get_paywall_settings(admin_id: int = Depends(verify_admin_token)):
    """Admin-only: get current paywall settings including plans and protected routes."""
    app_settings, db = _get_app_settings()
    try:
        plans = json.loads(app_settings.plans_json)
    except (json.JSONDecodeError, TypeError):
        plans = {}
    result = {
        "paywall_enabled": app_settings.paywall_enabled,
        "plans": plans,
        "protected_routes": [r.strip() for r in app_settings.protected_routes.split(",") if r.strip()],
        "email_alerts": app_settings.email_alerts,
    }
    db.close()
    return result


@router.put("/paywall/toggle")
def toggle_paywall(enabled: bool, admin_id: int = Depends(verify_admin_token)):
    """Admin-only: enable or disable the paywall."""
    app_settings, db = _get_app_settings()
    app_settings.paywall_enabled = enabled
    db.commit()
    log_activity(admin_id, "toggle_paywall", f"Paywall {'enabled' if enabled else 'disabled'}")
    db.close()
    return {"paywall_enabled": enabled}


@router.put("/paywall/plans")
def update_plans(plans: dict, admin_id: int = Depends(verify_admin_token)):
    """Admin-only: update subscription plans. Each plan must have name, price, and days."""
    for key, plan in plans.items():
        if not isinstance(plan, dict):
            raise HTTPException(400, f"Invalid plan format for {key}")
        if 'price' not in plan or 'days' not in plan or 'name' not in plan:
            raise HTTPException(400, f"Plan '{key}' must have name, price, and days")
        try:
            float(plan['price'])
            int(plan['days'])
        except (ValueError, TypeError):
            raise HTTPException(400, f"Plan '{key}' has invalid price or days value")
    app_settings, db = _get_app_settings()
    app_settings.plans_json = json.dumps(plans)
    db.commit()
    log_activity(admin_id, "update_plans", f"Updated {len(plans)} subscription plans")
    db.close()
    return {"plans": plans}


@router.put("/paywall/routes")
def update_routes(routes: str, admin_id: int = Depends(verify_admin_token)):
    """Admin-only: update protected routes (comma-separated)."""
    app_settings, db = _get_app_settings()
    app_settings.protected_routes = routes
    db.commit()
    log_activity(admin_id, "update_routes", f"Protected routes: {routes}")
    db.close()
    return {"protected_routes": [r.strip() for r in routes.split(",") if r.strip()]}


@router.put("/paywall/email-alerts")
def toggle_email_alerts(data: dict, admin_id: int = Depends(verify_admin_token)):
    """Admin-only: toggle email alerts on paywall bypass attempts."""
    enabled = data.get("enabled", True)
    app_settings, db = _get_app_settings()
    app_settings.email_alerts = enabled
    db.commit()
    log_activity(admin_id, "toggle_email_alerts", f"Email alerts {'enabled' if enabled else 'disabled'}")
    db.close()
    return {"email_alerts": enabled}


# ── Public Endpoint ─────────────────────────────────────────────────

@router.get("/public/plans")
def get_plans_public():
    """Public: list available subscription plans (no auth required)."""
    db = SessionLocal()
    app_settings = db.query(AppSettings).first()
    if not app_settings:
        db.close()
        return {"paywall_enabled": False, "plans": []}
    try:
        plans = json.loads(app_settings.plans_json)
    except (json.JSONDecodeError, TypeError):
        plans = {}
    result = {
        "paywall_enabled": app_settings.paywall_enabled,
        "plans": [
            {"key": k, "name": v["name"], "price": v["price"], "days": v["days"]}
            for k, v in plans.items()
        ]
    }
    db.close()
    return result
