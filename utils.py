import time
from collections import defaultdict
from database import SessionLocal, Message

# ── Rate Limiter ─────────────────────────────────────────────────────

_rate_store: dict = defaultdict(list)

def check_rate_limit(key: str, limit: int = 10, window: int = 60) -> bool:
    """Returns True if allowed, False if rate-limited."""
    now = time.time()
    _rate_store[key] = [t for t in _rate_store[key] if now - t < window]
    if len(_rate_store[key]) >= limit:
        return False
    _rate_store[key].append(now)
    return True


# ── Context Builder ──────────────────────────────────────────────────

def build_user_context(user_id: int, db) -> dict:
    """Build recent message context for AI conversations."""
    recent = db.query(Message).filter_by(user_id=user_id).order_by(
        Message.created_at.desc()
    ).limit(5).all()
    return {
        "recent_messages": [m.content for m in reversed(recent)],
        "message_count": db.query(Message).filter_by(user_id=user_id).count(),
    }


# ── Broadcast ────────────────────────────────────────────────────────

async def broadcast_to_all_users(bot, text: str, db) -> int:
    """Send a message to all registered users via Telegram."""
    from database import User
    users = db.query(User).filter(User.telegram_id.isnot(None)).all()
    sent = 0
    for user in users:
        try:
            await bot.send_message(chat_id=user.telegram_id, text=text)
            sent += 1
        except Exception:
            pass
    return sent
