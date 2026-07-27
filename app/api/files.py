from fastapi import APIRouter, Depends, File, UploadFile,status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.documents.service import save_document
from app.schemas.document import DocumentResponse
from app.services.documents.processing_service import process_document

router = APIRouter()


#imports below it is for dummy end points
from app.models.document import Document, DocumentText
from fastapi import HTTPException




@router.post("/upload", response_model=DocumentResponse,status_code=status.HTTP_201_CREATED) 
async def upload_file(file: UploadFile = File(...),current_user: User = Depends(get_current_user),db: Session = Depends(get_db)):
    document = await save_document(file, current_user,db)
    process_document(document, db)
    return document



#dummy end points
@router.post("/upload-demo", response_model=DocumentResponse,status_code=status.HTTP_201_CREATED) 
async def upload_file(file: UploadFile = File(...),current_user= User(id=1),db: Session = Depends(get_db)):
    document = await save_document(file, current_user,db)
    process_document(document, db)
    return document

@router.get("/{document_id}")
async def get_document(document_id: int, db: Session = Depends(get_db)):
    document = db.get(Document, document_id)

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    document_content = (
        db.query(DocumentText)
        .filter(DocumentText.document_id == document.id)
        .first()
    )

    return {
        "document": {
            "id": document.id,
            "original_filename": document.original_filename,
            "stored_filename": document.stored_filename,
            "storage_path": document.storage_path,
            "content_type": document.content_type,
            "file_size": document.file_size,
            "status": document.status,
            "created_at": document.created_at,
            "updated_at": document.updated_at,
        },
        "content": document_content.content if document_content else None,
    }