from fastapi import APIRouter, UploadFile, Depends
from app.services.pdf_parser import extract_text_from_pdf
from app.services.supabase_client import upsert_resume
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/upload")
async def upload_resume(file: UploadFile, user=Depends(get_current_user)):
    content = extract_text_from_pdf(await file.read())
    resume_id = upsert_resume(user_id=user["id"], filename=file.filename, content=content)
    return {"resume_id": resume_id, "message": "Resume uploaded"}