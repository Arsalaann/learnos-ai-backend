from fastapi import UploadFile, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.workspace import Workspace

from app.models.document import Document, DocumentContent
from app.models.workspace import Workspace

from app.services.documents.validation import validate_upload
from app.services.documents.storage import delete_upload, save_file
from app.services.documents.extraction.extractor import extract_document

def find_document_by_filename(db: Session, workspace: Workspace, filename: str):

    statement = (
        select(Document)
        .where(Document.workspace_id == workspace.id)
        .where(Document.original_filename == filename)
    )

    result = db.execute(statement)

    return result.scalar_one_or_none()


def find_document_by_id(db: Session, document_id: int):

    statement = select(Document).where(Document.id == document_id)

    result = db.execute(statement)

    return result.scalar_one_or_none()


def find_documents_by_workspace(db: Session, workspace: Workspace):

    statement = (
        select(Document)
        .where(Document.workspace_id == workspace.id)
        .order_by(Document.created_at.asc())
    )

    result = db.execute(statement)

    return result.scalars().all()



def get_document_by_id(db: Session, document_id: int):

    document = find_document_by_id(db, document_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    return document


def get_document(db: Session, document_id: int, workspace: Workspace):

    document = get_document_by_id(db, document_id)

    if document.workspace_id != workspace.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    return document


def get_documents(db: Session, workspace: Workspace):

    return find_documents_by_workspace(db, workspace)






async def create_document(db: Session, file: UploadFile, workspace: Workspace) -> Document:

    await validate_upload(file)

    stored_file = await save_file(file=file, workspace_id=workspace.id)

    try:

        extraction_result = extract_document(
            content_type=file.content_type,
            storage_path=stored_file.storage_path,
            upload_directory=stored_file.upload_directory,
        )

        document = Document(
            workspace_id=workspace.id,
            original_filename=file.filename,
            storage_path=stored_file.storage_path,
            upload_directory=stored_file.upload_directory,
            content_type=file.content_type,
            file_size=file.size,
        )

        db.add(document)
        db.flush()

        if extraction_result.texts:
            db.add(
                DocumentContent(
                    document_id=document.id,
                    content=extraction_result.texts,
                )
            )

        db.commit()
        db.refresh(document)

        return document

    except Exception:

        db.rollback()
        delete_upload(stored_file.upload_directory)
        raise
    


def delete_document(db: Session, document_id: int, workspace: Workspace):

    document = get_document_by_id(db, document_id)

    if document.workspace_id != workspace.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    upload_directory = document.upload_directory

    db.delete(document)

    db.commit()

    delete_upload(upload_directory)