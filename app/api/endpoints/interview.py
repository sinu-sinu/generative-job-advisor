from fastapi import APIRouter, Depends, HTTPException
from app.services.supabase_client import get_latest_resume_by_user
from app.services.groq_service import chat_completion
from app.prompts.loader import load_prompt
from app.api.deps import get_current_user

router = APIRouter()

# 1. Résumé feedback
@router.post("/feedback")
async def get_resume_feedback(user=Depends(get_current_user)):
    resume = get_latest_resume_by_user(user["id"])
    if not resume or not resume.get("content"):
        raise HTTPException(400, "No résumé content found. Upload one first.")

    template = load_prompt("resume_feedback.md")
    prompt_text = template.replace("{{ resume_text }}", resume["content"])

    messages = [
        {
            "role": "system",
            "content": (
                "You are a senior résumé coach for technical roles. "
            ),
        },
        {"role": "user", "content": prompt_text},
    ]

    response = await chat_completion(messages)
    return {"feedback": response}   

# 2. Generate interview question
@router.get("/question")
async def generate_interview_question(job_title: str):
    template = load_prompt("interview_question.md")
    prompt_text = template.replace("{{ job_title }}", job_title.strip())

    messages = [
        {
            "role": "system",
            "content": "You are a technical interviewer for top tech firms.",
        },
        {"role": "user", "content": prompt_text},
    ]

    response = await chat_completion(messages)
    return {"question": response.strip()}

# 3. Critique interview answer
@router.post("/critique")
async def critique_interview_answer(payload: dict):
    question = payload.get("question", "").strip()
    answer = payload.get("answer", "").strip()
    if not question or not answer:
        raise HTTPException(400, "Both question and answer are required.")

    template = load_prompt("interview_critique.md")
    prompt_text = (
        template.replace("{{ question }}", question)
                .replace("{{ answer }}", answer)
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are a hiring manager"
            ),
        },
        {"role": "user", "content": prompt_text},
    ]

    response = await chat_completion(messages)
    return {"critique": response}  