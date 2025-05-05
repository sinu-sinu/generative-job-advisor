from fastapi import FastAPI
from app.api.endpoints import health

app = FastAPI(title="Generative AI Job Advisor")

app.include_router(health.router, tags=["Health"], prefix="/health")
