from fastapi import APIRouter, Depends
from app.services.groq_service import chat_completion
from app.services.supabase_client import get_latest_resume_by_user
from app.prompts.loader import load_prompt
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/recommend")
async def recommend_paths(user=Depends(get_current_user)):
    resume = get_latest_resume_by_user(user["id"])
    if not resume or not resume.get("content"):
        return {"error": "No resume content found. Please upload again."}

    template = load_prompt("career_recommendation.md")
    prompt_text = template.replace("{{ resume_text }}", resume["content"])

    messages = [
        {"role": "system", "content": "You are an expert career strategist with up‑to‑the‑minute knowledge of labor‑market trends, compensation data, and emerging skills demands."},
        {"role": "user", "content": prompt_text}
    ]

    response = await chat_completion(messages)
    return {"recommendations": response}

