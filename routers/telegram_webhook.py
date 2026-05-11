from fastapi import APIRouter, Request
from telegram_bot import setup_bot
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/telegram", tags=["telegram"])
bot_app = setup_bot()

@router.post("/webhook")
async def telegram_webhook(request: Request):
    if not bot_app:
        return {"status": "disabled", "detail": "Telegram bot not configured"}
    data = await request.json()
    from telegram import Update
    update = Update.de_json(data, bot_app.bot)
    try:
        if not bot_app._initialized:
            await bot_app.initialize()
        await bot_app.process_update(update)
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}")
        return {"status": "error", "detail": str(e)}
    return {"status": "ok"}
