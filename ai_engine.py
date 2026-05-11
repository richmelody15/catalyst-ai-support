import httpx
from config import settings

ZAI_URL = "https://api.z.ai/api/v1/chat/completions"

async def ask_ai(question: str, user_context: dict = None, premium: bool = False) -> str:
    headers = {"Authorization": f"Bearer {settings.ZAI_API_KEY}"}
    system_prompt = "You are a friendly support assistant for Catalyst AI Signals. Be concise, helpful."
    if premium:
        system_prompt += " The user is a premium member – give them extra detailed help."
    messages = [{"role": "system", "content": system_prompt}]
    if user_context:
        messages.append({"role": "assistant", "content": f"User history: {user_context}"})
    messages.append({"role": "user", "content": question})
    payload = {
        "model": "zai-large",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 500
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(ZAI_URL, json=payload, headers=headers)
        data = resp.json()
        return data["choices"][0]["message"]["content"]
