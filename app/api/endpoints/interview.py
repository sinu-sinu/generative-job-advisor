from fastapi import APIRouter, Depends
from app.services.groq_service import chat_completion
from app.prompts.loader import load_prompt
from app.api.deps import get_current_user
from app.services.supabase_client import log_mock_interview

router = APIRouter()

@router.post("/question")
async def generate_question(job_title: str):
    template = load_prompt("mock_question.md")
    prompt_text = template.replace("{{ job_title }}", job_title)
    messages = [
        {"role": "system", "content": "You are a job interviewer."},
        {"role": "user", "content": prompt_text}
    ]
    question = await chat_completion(messages)
    return {"question": question.strip()}

@router.post("/critique")
async def critique_answer(data: dict, user=Depends(get_current_user)):
    template = load_prompt("mock_critique.md")
    filled = template.replace("{{ question }}", data["question"]).replace("{{ answer }}", data["answer"])
    messages = [
        {"role": "system", "content": "You are a skilled interview coach."},
        {"role": "user", "content": filled}
    ]
    result = await chat_completion(messages)

    # Extract score (rudimentary)
    score_line = [line for line in result.splitlines() if "Score:" in line]
    score = int(score_line[0].split(":")[-1].strip()) if score_line else None

    # Log in Supabase
    log_mock_interview(user_id=user["id"], question=data["question"], answer=data["answer"], critique=result, score=score)

    return {"critique": result, "score": score}