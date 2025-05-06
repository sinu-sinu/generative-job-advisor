# app/services/supabase_client.py

from supabase import create_client
import httpx
import os
import uuid

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

async def get_user_from_token(token: str):
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {token}"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{url}/auth/v1/user", headers=headers)
    if resp.status_code == 200:
        return resp.json() 
    return None

def insert_resume(user_id: str, filename: str, content: str) -> str:
    resume_id = str(uuid.uuid4())
    supabase.table("resumes").insert({
        "id": resume_id,
        "user_id": user_id,
        "filename": filename,
        "content": content
    }).execute()
    return resume_id

def get_latest_resume_by_user(user_id: str):
    res = supabase.table("resumes") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .limit(1).execute()
    return res.data[0]

def log_mock_interview(user_id: str, question: str, answer: str, critique: str, score: int):
    supabase.table("mock_interviews").insert({
        "user_id": user_id,
        "question": question,
        "answer": answer,
        "critique": critique,
        "score": score
    }).execute()
