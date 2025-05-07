from fastapi import FastAPI
from app.api.endpoints import health ,career, resume , resume_feedback, interview

app = FastAPI(title="Generative AI Job Advisor")

app.include_router(health.router, tags=["Health"], prefix="/health")
app.include_router(resume.router, tags=["Resume"], prefix="/resume")
app.include_router(career.router, tags=["Career"], prefix="/career")
app.include_router(resume_feedback.router, tags=["Resume_Feedback"], prefix="/resume_feedback")
app.include_router(interview.router, tags=["Interview"], prefix="/interview")
