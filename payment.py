import stripe
from datetime import datetime, timedelta
from config import settings
from database import SessionLocal, User, SubscriptionStatus

stripe.api_key = settings.STRIPE_SECRET_KEY

async def create_checkout_session(telegram_id: int) -> str:
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{"price": settings.PREMIUM_PRICE_ID, "quantity": 1}],
        mode="subscription",
        success_url=f"{settings.APP_URL}/success",
        cancel_url=f"{settings.APP_URL}/cancel",
        metadata={"telegram_id": str(telegram_id)},
    )
    return session.url

async def handle_webhook(payload: bytes, sig_header: str):
    event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        telegram_id = int(session["metadata"]["telegram_id"])
        db = SessionLocal()
        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        if user:
            user.subscription_status = SubscriptionStatus.premium
            user.subscription_end = datetime.utcnow() + timedelta(days=30)
            db.commit()
