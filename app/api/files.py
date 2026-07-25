from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.document_service import save_document
from app.schemas.document import DocumentResponse

router = APIRouter()


@router.post("/upload", response_model=DocumentResponse)
async def upload_file(file: UploadFile = File(...),current_user: User = Depends(get_current_user),db: Session = Depends(get_db)):
    return await save_document(file, current_user,db)