from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentStatus
from app.models.user import User
from app.services.documents.validation import validate_pdf
from app.services.documents.storage import delete_file, save_file


async def save_document(file: UploadFile, current_user: User, db: Session) -> Document:
    await validate_pdf(file)

    stored_path = await save_file(file)

    document = Document(
        user_id=current_user.id,
        original_filename=file.filename,
        stored_filename=stored_path.filename,
        storage_path=stored_path.storage_path,
        content_type=file.content_type,
        file_size=file.size,
        status=DocumentStatus.UPLOADED,
    )

    db.add(document)

    try:
        db.commit()
        db.refresh(document)
        return document

    except Exception:
        db.rollback()
        delete_file(stored_path.storage_path)
        raise