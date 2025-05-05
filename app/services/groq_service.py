import os
import httpx
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "mixtral-8x7b-32768"

HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

async def chat_completion(messages: List[Dict], model: str = DEFAULT_MODEL, temperature: float = 0.5) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(GROQ_API_URL, headers=HEADERS, json=payload)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except httpx.HTTPError as e:
            raise RuntimeError(f"Groq API call failed: {e}")