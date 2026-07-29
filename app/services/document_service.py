from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.document import Document,DocumentContent
from app.models.user import User

from app.services.documents.validation import validate_upload
from app.services.documents.storage import delete_upload,save_file
from app.services.documents.extraction.extractor import extract_document


async def upload_document(file: UploadFile,current_user: User,db: Session) -> Document:

    await validate_upload(file)

    stored_file = await save_file(file=file,user_id=current_user.id)

    try:
        extraction_result = extract_document(
            content_type=file.content_type,
            storage_path=stored_file.storage_path,
            upload_directory=stored_file.upload_directory
        )

        document = Document(
            user_id=current_user.id,
            original_filename=file.filename,
            storage_path=stored_file.storage_path,
            upload_directory=stored_file.upload_directory,
            content_type=file.content_type,
            file_size=file.size,
        )

        db.add(document)
        db.flush()

        if extraction_result.texts:
            db.add(DocumentContent(document_id=document.id,content=extraction_result.texts))

        db.commit()
        db.refresh(document)

        return document

    except Exception:

        db.rollback()
        delete_upload(stored_file.upload_directory)
        raise