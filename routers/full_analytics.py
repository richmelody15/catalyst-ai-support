from fastapi import APIRouter, Query, Depends
from database import SessionLocal, SignalHistory, User, AdminActivityLog
from sqlalchemy import func
from datetime import datetime, timedelta

from routers.admin_auth import verify_admin_token

router = APIRouter(prefix="/api/analytics/full", tags=["full_analytics"])


# ---------- HELPER ----------
def get_date_range(days: int = 7):
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    return start, end


# ---------- EQUITY CURVE ----------
@router.get("/equity-curve")
def equity_curve(days: int = Query(30, ge=1, le=365)):
    """Generate a simple equity curve based on signal outcomes over N days."""
    start, end = get_date_range(days)
    db = SessionLocal()
    rows = db.query(SignalHistory).filter(
        SignalHistory.entry_time >= start,
        SignalHistory.outcome.in_(["win", "loss"])
    ).order_by(SignalHistory.entry_time).all()
    db.close()

    balance = 100.0
    curve = []
    for r in rows:
        if r.outcome == "win":
            balance *= 1.01   # 1% growth per win
        elif r.outcome == "loss":
            balance *= 0.99   # 1% loss per loss
        curve.append({
            "date": r.entry_time.strftime("%Y-%m-%d %H:%M"),
            "balance": round(balance, 2)
        })
    return {"days": days, "points": len(curve), "final_balance": round(balance, 2), "curve": curve[-100:]}


# ---------- TRADE ANALYTICS ----------
@router.get("/trade-overview")
def trade_overview(days: int = Query(7, ge=1, le=365)):
    start, end = get_date_range(days)
    db = SessionLocal()
    rows = db.query(SignalHistory).filter(SignalHistory.entry_time >= start).all()
    total = len(rows)
    wins = sum(1 for r in rows if r.outcome == "win")
    losses = sum(1 for r in rows if r.outcome == "loss")
    ignored = sum(1 for r in rows if r.outcome == "ignored")
    wr = round(wins / (wins + losses) * 100, 1) if (wins + losses) else 0

    # Trades per day
    daily_trades = {}
    for r in rows:
        day = r.entry_time.strftime("%Y-%m-%d")
        daily_trades[day] = daily_trades.get(day, 0) + 1

    # Skipped days
    all_days = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
    skipped_days = [d for d in all_days if d not in daily_trades]

    # Best / worst performing pair
    pair_stats = {}
    for r in rows:
        if not r.symbol:
            continue
        if r.symbol not in pair_stats:
            pair_stats[r.symbol] = {"wins": 0, "losses": 0}
        if r.outcome == "win":
            pair_stats[r.symbol]["wins"] += 1
        elif r.outcome == "loss":
            pair_stats[r.symbol]["losses"] += 1

    def pair_wr(sym):
        s = pair_stats[sym]
        total_t = s["wins"] + s["losses"]
        return s["wins"] / total_t if total_t else 0

    best_pair = max(pair_stats, key=pair_wr, default="N/A")
    worst_pair = min(pair_stats, key=pair_wr, default="N/A")

    # Simulated equity curve
    balance = 100.0
    equity_curve = []
    for r in sorted(rows, key=lambda x: x.entry_time):
        if r.outcome == "win":
            balance *= 1.01
        elif r.outcome == "loss":
            balance *= 0.99
        equity_curve.append({"time": str(r.entry_time), "balance": round(balance, 2)})

    db.close()
    return {
        "period_days": days,
        "total_signals": total,
        "wins": wins, "losses": losses, "ignored": ignored,
        "win_rate": wr,
        "daily_trades": daily_trades,
        "skipped_days": skipped_days,
        "best_pair": best_pair,
        "worst_pair": worst_pair,
        "equity_curve": equity_curve[-50:],
        "final_balance": round(balance, 2)
    }


# ---------- SUBSCRIBER ANALYTICS ----------
@router.get("/subscribers")
def subscriber_analytics(days: int = Query(30, ge=1, le=365)):
    start, end = get_date_range(days)
    db = SessionLocal()
    total_users = db.query(User).count()
    new_users = db.query(User).filter(User.created_at >= start).count()
    premium_users = db.query(User).filter(User.subscription_status == "premium").count()

    # Active users (traded at least once in period)
    active_user_ids = db.query(SignalHistory.user_id).filter(
        SignalHistory.entry_time >= start,
        SignalHistory.user_id.isnot(None)
    ).distinct().all() if hasattr(SignalHistory, 'user_id') else []

    active_users = len(active_user_ids)

    # Average trades per active user
    total_new_signals = db.query(SignalHistory).filter(SignalHistory.entry_time >= start).count()
    avg_trades_per_user = round(total_new_signals / active_users, 1) if active_users else 0

    db.close()
    return {
        "total_users": total_users,
        "new_users_last_30d": new_users,
        "premium_users": premium_users,
        "active_users_last_30d": active_users,
        "avg_trades_per_active_user": avg_trades_per_user
    }


# ---------- RISK MANAGEMENT SNAPSHOT ----------
@router.get("/risk-snapshot")
def risk_snapshot():
    db = SessionLocal()
    recent = db.query(SignalHistory).order_by(SignalHistory.entry_time.desc()).limit(100).all()
    if not recent:
        db.close()
        return {"message": "No trades yet"}

    wins = sum(1 for r in recent if r.outcome == "win")
    losses = sum(1 for r in recent if r.outcome == "loss")
    wr = wins / (wins + losses) * 100 if (wins + losses) else 0

    # Drawdown: worst losing streak
    max_loss_streak = 0
    current_streak = 0
    for r in recent:
        if r.outcome == "loss":
            current_streak += 1
            max_loss_streak = max(max_loss_streak, current_streak)
        else:
            current_streak = 0

    # Capital protection recommendation
    if max_loss_streak >= 3:
        advice = "Consider reducing stake to 0.5% until streak ends."
    elif wr < 70:
        advice = "Win rate below target - review filters or tighten entry rules."
    else:
        advice = "System is healthy. Continue 1% risk."

    db.close()
    return {
        "recent_win_rate": round(wr, 1),
        "max_loss_streak": max_loss_streak,
        "risk_advice": advice
    }


# ---------- TRADING JOURNAL ----------
@router.get("/journal")
def trading_journal(days: int = Query(30, ge=1, le=365), page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100)):
    start, _ = get_date_range(days)
    db = SessionLocal()
    query = db.query(SignalHistory).filter(SignalHistory.entry_time >= start).order_by(SignalHistory.entry_time.desc())
    total = query.count()
    rows = query.offset((page - 1) * per_page).limit(per_page).all()
    db.close()
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
        "trades": [{
            "id": r.id,
            "symbol": r.symbol,
            "direction": r.direction,
            "timeframe": r.timeframe,
            "platform": r.platform,
            "entry_time": str(r.entry_time),
            "outcome": r.outcome,
            "confidence": r.confidence,
            "accuracy": r.accuracy
        } for r in rows]
    }
