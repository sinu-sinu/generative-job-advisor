# app/services/groq_service.py

import os
import httpx
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama3-70b-8192"

if not GROQ_API_KEY:
    raise EnvironmentError("Missing GROQ_API_KEY in environment variables.")

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
        except httpx.HTTPStatusError as e:
            print("[Groq ERROR]", e.response.status_code)
            print("[Groq BODY]", e.response.text)
            raise RuntimeError(f"Groq API call failed: {e.response.status_code} {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"Groq API call failed: {str(e)}")
