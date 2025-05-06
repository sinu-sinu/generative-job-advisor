# app/api/deps.py

from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPBearer
from app.services.supabase_client import get_user_from_token

security = HTTPBearer()

async def get_current_user(authorization: str = Depends(security)):
    token = authorization.credentials
    user = await get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return user
