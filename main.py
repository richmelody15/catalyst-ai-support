from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, subscription, tickets, admin, chat, telegram_webhook
from database import init_db

app = FastAPI(title="Catalyst AI Support", version="2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router)
app.include_router(subscription.router)
app.include_router(tickets.router)
app.include_router(admin.router)
app.include_router(chat.router)
app.include_router(telegram_webhook.router)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def root():
    return {"status": "AI Support System Active"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
