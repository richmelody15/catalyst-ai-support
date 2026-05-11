from fastapi import APIRouter, Query
from database import SessionLocal, SignalHistory
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/summary")
def summary(days: int = 7):
    db = SessionLocal()
    cutoff = datetime.utcnow() - timedelta(days=days)
    records = db.query(SignalHistory).filter(SignalHistory.entry_time >= cutoff).all()
    total = len(records)
    wins = sum(1 for r in records if r.outcome == 'win')
    losses = sum(1 for r in records if r.outcome == 'loss')
    ignored = sum(1 for r in records if r.outcome == 'ignored')
    wr = round(wins / (wins + losses) * 100, 1) if (wins + losses) else 0
    # Per pair stats
    pairs = {}
    for r in records:
        if r.symbol not in pairs:
            pairs[r.symbol] = {"total": 0, "wins": 0, "losses": 0}
        pairs[r.symbol]["total"] += 1
        if r.outcome == 'win':
            pairs[r.symbol]["wins"] += 1
        elif r.outcome == 'loss':
            pairs[r.symbol]["losses"] += 1
    db.close()
    return {
        "period_days": days,
        "total_signals": total,
        "wins": wins, "losses": losses, "ignored": ignored,
        "win_rate": wr,
        "by_pair": {
            sym: {
                "total": d["total"],
                "win_rate": round(d["wins"] / (d["wins"] + d["losses"]) * 100, 1) if (d["wins"] + d["losses"]) else 0
            }
            for sym, d in pairs.items()
        }
    }

@router.get("/weekly-report")
def weekly_report():
    db = SessionLocal()
    cutoff = datetime.utcnow() - timedelta(days=7)
    records = db.query(SignalHistory).filter(SignalHistory.entry_time >= cutoff).all()
    total = len(records)
    wins = sum(1 for r in records if r.outcome == 'win')
    losses = sum(1 for r in records if r.outcome == 'loss')
    wr = round(wins / (wins + losses) * 100, 1) if (wins + losses) else 0
    # Per platform stats
    platforms = {}
    for r in records:
        p = r.platform or "unknown"
        if p not in platforms:
            platforms[p] = {"total": 0, "wins": 0, "losses": 0}
        platforms[p]["total"] += 1
        if r.outcome == 'win':
            platforms[p]["wins"] += 1
        elif r.outcome == 'loss':
            platforms[p]["losses"] += 1
    db.close()
    return {
        "period": "7 days",
        "total_signals": total,
        "wins": wins,
        "losses": losses,
        "win_rate": wr,
        "by_platform": {
            p: {
                "total": d["total"],
                "win_rate": round(d["wins"] / (d["wins"] + d["losses"]) * 100, 1) if (d["wins"] + d["losses"]) else 0
            }
            for p, d in platforms.items()
        }
    }

@router.get("/export")
def export(format: str = "json"):
    db = SessionLocal()
    records = db.query(SignalHistory).all()
    data = [
        {
            "id": r.id, "symbol": r.symbol, "direction": r.direction,
            "timeframe": r.timeframe, "platform": r.platform,
            "entry_time": str(r.entry_time), "outcome": r.outcome,
            "rsi": r.rsi, "adx": r.adx, "confidence": r.confidence, "accuracy": r.accuracy,
        }
        for r in records
    ]
    db.close()
    return data

@router.post("/record")
def record_signal(
    symbol: str, direction: str, timeframe: str, platform: str,
    rsi: float = 0, adx: float = 0, confidence: float = 0, accuracy: float = 0
):
    db = SessionLocal()
    s = SignalHistory(
        symbol=symbol, direction=direction, timeframe=timeframe, platform=platform,
        entry_time=datetime.utcnow(), rsi=rsi, adx=adx, confidence=confidence, accuracy=accuracy
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    db.close()
    return {"status": "recorded", "id": s.id}

@router.patch("/outcome/{signal_id}")
def update_outcome(signal_id: int, outcome: str):
    db = SessionLocal()
    s = db.query(SignalHistory).filter_by(id=signal_id).first()
    if not s:
        db.close()
        from fastapi import HTTPException
        raise HTTPException(404, "Signal not found")
    s.outcome = outcome
    db.commit()
    db.close()
    return {"status": "updated"}
