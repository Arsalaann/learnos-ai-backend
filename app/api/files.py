from fastapi import APIRouter, Depends, File, UploadFile,status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.document_service import upload_document
from app.schemas.document import DocumentResponse


router = APIRouter()

@router.post("/upload", response_model=DocumentResponse,status_code=status.HTTP_201_CREATED) 
async def upload_file(file: UploadFile = File(...),current_user: User = Depends(get_current_user),db: Session = Depends(get_db)):
    return await upload_document(file, current_user, db)





#dummy code

from fastapi import HTTPException
from app.models.document import DocumentContent


@router.post(
    "/upload-test",
    status_code=status.HTTP_201_CREATED,
)
async def upload_file_test(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    current_user = db.get(User, 1)

    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test user with id=1 not found.",
        )

    return await upload_document(
        file=file,
        current_user=current_user,
        db=db,
    )
    
@router.get("/{document_id}")
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    document = db.get(DocumentContent, document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    return document