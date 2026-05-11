from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from database import SessionLocal, User, Message, Ticket
from ai_engine import ask_ai
from utils import build_user_context, check_rate_limit
from payment import create_checkout_session
from config import settings

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = SessionLocal()
    db_user = db.query(User).filter_by(telegram_id=user.id).first()
    if not db_user:
        db_user = User(telegram_id=user.id, username=user.username, full_name=user.full_name)
        db.add(db_user); db.commit()
    await update.message.reply_text(f"👋 Welcome, {user.first_name}! I'm your AI assistant. Use /help for commands.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    db = SessionLocal()
    db_user = db.query(User).filter_by(telegram_id=user.id).first()
    if not db_user: return
    check_rate_limit(f"msg:{user.id}", limit=10)
    # Build context
    ctx = build_user_context(db_user.id, db)
    premium = db_user.subscription_status.value == "premium"
    reply = await ask_ai(text, ctx, premium)
    # Save
    msg = Message(user_id=db_user.id, content=text, from_ai=False)
    ai_msg = Message(user_id=db_user.id, content=reply, from_ai=True)
    db.add_all([msg, ai_msg])
    db.commit()
    await update.message.reply_text(reply)

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("💳 Go Premium ($5/month)", callback_data="upgrade")]]
    await update.message.reply_text("Unlock priority support & exclusive signals.", reply_markup=InlineKeyboardMarkup(keyboard))

async def upgrade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    url = await create_checkout_session(query.from_user.id)
    await query.edit_message_text(f"👉 Click to upgrade: {url}")

async def new_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=update.effective_user.id).first()
    if not user: return
    subject = " ".join(context.args) if context.args else "General Inquiry"
    ticket = Ticket(user_id=user.id, subject=subject)
    db.add(ticket)
    db.commit()
    await update.message.reply_text(f"✅ Ticket #{ticket.id} opened: {subject}")

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != settings.ADMIN_CHAT_ID:
        return
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Please provide a message.")
        return
    db = SessionLocal()
    from utils import broadcast_to_all_users
    await broadcast_to_all_users(context.bot, text, db)
    await update.message.reply_text("Broadcast sent.")

def setup_bot() -> Application:
    if not settings.TELEGRAM_BOT_TOKEN:
        return None
    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("ticket", new_ticket))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CallbackQueryHandler(upgrade_callback, pattern="upgrade"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app
