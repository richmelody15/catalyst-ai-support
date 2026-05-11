# Catalyst AI Support & Subscription System

## Features
- AI auto-replies via Z.AI
- Telegram private/group chat support
- Support ticket system
- Premium subscriptions (Stripe)
- Admin dashboard API
- Real-time WebSocket chat
- Broadcast system
- Rate limiting & anti-spam
- Shared memory between website & Telegram

## Quick Start
1. Clone repo
2. Create `.env` from `.env.example` and fill values
3. `pip install -r requirements.txt`
4. `uvicorn main:app --reload`
5. Set Telegram webhook: `https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://your-domain.com/api/telegram/webhook`

## Deploy to Railway
1. Push to GitHub
2. New project on Railway → Deploy from GitHub
3. Add environment variables from `.env.example`
4. Railway starts the app automatically
