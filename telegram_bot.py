from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from database import SessionLocal, User, Message, Ticket, VIPChallenge, VIPChallengeParticipant
from ai_engine import ask_ai
from utils import build_user_context, check_rate_limit
from payment import create_checkout_session
from config import settings
from datetime import datetime


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


# ── VIP Challenge Commands ──────────────────────────────────────────

async def vip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show active VIP challenges and allow joining."""
    db = SessionLocal()
    now = datetime.utcnow()
    active = db.query(VIPChallenge).filter(
        VIPChallenge.end_time >= now,
        VIPChallenge.status.in_(["active", "upcoming"])
    ).all()

    if not active:
        await update.message.reply_text("No active VIP challenges at the moment. Stay tuned! 🔜")
        db.close()
        return

    keyboard = []
    for c in active:
        p_count = db.query(VIPChallengeParticipant).filter_by(challenge_id=c.id).count()
        keyboard.append([InlineKeyboardButton(
            f"🏆 {c.name} (Prize: ${c.prize_pool} | {p_count} players)",
            callback_data=f"vip_join_{c.id}"
        )])

    await update.message.reply_text(
        "🔱 Active VIP Challenges (Premium only):",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    db.close()


async def vip_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle VIP challenge join button press."""
    query = update.callback_query
    await query.answer()
    challenge_id = int(query.data.split("_")[2])
    user = update.effective_user

    db = SessionLocal()
    db_user = db.query(User).filter_by(telegram_id=user.id).first()
    if not db_user or db_user.subscription_status.value != "premium":
        await query.edit_message_text("❌ Only premium users can join VIP challenges. Use /subscribe to upgrade.")
        db.close()
        return

    existing = db.query(VIPChallengeParticipant).filter_by(
        challenge_id=challenge_id, user_id=db_user.id
    ).first()
    if existing:
        await query.edit_message_text("✅ You're already in this challenge!")
        db.close()
        return

    participant = VIPChallengeParticipant(challenge_id=challenge_id, user_id=db_user.id)
    db.add(participant)
    db.commit()
    await query.edit_message_text("✅ You've joined the VIP challenge! Your trades from now on will count. 🏆")
    db.close()


async def leaderboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show leaderboard for a VIP challenge. Usage: /leaderboard <challenge_id>"""
    args = context.args
    if not args:
        # If no args, show available challenges to pick from
        db = SessionLocal()
        now = datetime.utcnow()
        active = db.query(VIPChallenge).filter(
            VIPChallenge.end_time >= now,
            VIPChallenge.status.in_(["active", "upcoming"])
        ).all()
        if not active:
            await update.message.reply_text("No active challenges. Usage: /leaderboard <challenge_id>")
        else:
            msg = "Active challenges:\n\n"
            for c in active:
                msg += f"  #{c.id} — {c.name} (Prize: ${c.prize_pool})\n"
            msg += "\nUse: /leaderboard <id>"
            await update.message.reply_text(msg)
        db.close()
        return

    try:
        challenge_id = int(args[0])
    except ValueError:
        await update.message.reply_text("Usage: /leaderboard <challenge_id>")
        return

    db = SessionLocal()
    challenge = db.query(VIPChallenge).filter_by(id=challenge_id).first()
    if not challenge:
        await update.message.reply_text("Challenge not found.")
        db.close()
        return

    participants = db.query(VIPChallengeParticipant).filter_by(
        challenge_id=challenge_id
    ).order_by(VIPChallengeParticipant.score.desc()).limit(10).all()
    if not participants:
        await update.message.reply_text("No participants yet.")
        db.close()
        return

    msg = f"🏆 VIP Challenge Leaderboard — {challenge.name}\n\n"
    for i, p in enumerate(participants, 1):
        user = db.query(User).filter_by(id=p.user_id).first()
        name = user.username or user.full_name or str(p.user_id) if user else f"User#{p.user_id}"
        wr = round(p.wins / (p.wins + p.losses) * 100, 1) if (p.wins + p.losses) else 0
        msg += f"{i}. {name} – Score: {p.score:.1f} | W/L: {p.wins}/{p.losses} | WR: {wr}%\n"
    await update.message.reply_text(msg)
    db.close()


def setup_bot() -> Application:
    if not settings.TELEGRAM_BOT_TOKEN:
        return None
    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("ticket", new_ticket))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("vip", vip_cmd))
    app.add_handler(CommandHandler("leaderboard", leaderboard_cmd))
    app.add_handler(CallbackQueryHandler(upgrade_callback, pattern="upgrade"))
    app.add_handler(CallbackQueryHandler(vip_join_callback, pattern="vip_join_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app
