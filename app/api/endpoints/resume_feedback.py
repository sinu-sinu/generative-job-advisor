from fastapi import APIRouter, Depends
from app.services.supabase_client import get_latest_resume_by_user
from app.services.groq_service import chat_completion
from app.prompts.loader import load_prompt
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/feedback")
async def get_resume_feedback(user=Depends(get_current_user)):
    resume = get_latest_resume_by_user(user["id"])

    if not resume or not resume.get("content"):
        return {"error": "No resume content found. Please upload your resume first."}

    template = load_prompt("resume_feedback.md")
    prompt_text = template.replace("{{ resume_text }}", resume["content"])

    messages = [
        {"role": "system", "content": "You are a resume expert who provides line-by-line critique and improvement suggestions."},
        {"role": "user", "content": prompt_text}
    ]

    response = await chat_completion(messages)
    return {"feedback": response}
