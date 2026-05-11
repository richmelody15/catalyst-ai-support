from fastapi import APIRouter, Request, HTTPException
from payment import handle_webhook

router = APIRouter(prefix="/api/subscription", tags=["subscription"])

@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    if not sig_header:
        raise HTTPException(400, "Missing Stripe signature")
    try:
        await handle_webhook(payload, sig_header)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(400, str(e))
