from fastapi import APIRouter, Request
from telegram import Update
from telegram_bot import setup_bot
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/telegram", tags=["telegram"])
bot_app = setup_bot()

@router.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    try:
        if not bot_app._initialized:
            await bot_app.initialize()
        await bot_app.process_update(update)
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}")
        return {"status": "error", "detail": str(e)}
    return {"status": "ok"}
