from fastapi import BackgroundTasks, HTTPException, UploadFile, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.embeddings.service import EmbeddingService
from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk
from app.models.document_embedding import DocumentEmbedding
from app.models.workspace import Workspace
from app.schemas.document import DocumentUpdate
from app.services.conversation_service import (
    create_document_conversation,
    get_document_conversation,
)
from app.services.documents.background_processor import (
    process_document_background,
)
from app.services.documents.storage import delete_upload, save_file
from app.services.documents.validation import validate_upload


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



async def create_document(
    db: Session,
    file: UploadFile,
    workspace: Workspace,
    embedding_service: EmbeddingService,
    background_tasks: BackgroundTasks,
) -> Document:

    await validate_upload(file)

    stored_file = await save_file(
        file=file,
        workspace_id=workspace.id,
    )

    try:

        document = Document(
            workspace_id=workspace.id,
            original_filename=file.filename,
            storage_path=stored_file.storage_path,
            upload_directory=stored_file.upload_directory,
            content_type=file.content_type,
            file_size=file.size,
            status=DocumentStatus.PROCESSING,
        )

        db.add(document)
        db.flush()

        create_document_conversation(
            db=db,
            workspace=workspace,
            document=document,
        )

        db.commit()
        db.refresh(document)

    except Exception:
        db.rollback()
        delete_upload(stored_file.upload_directory)
        raise

    background_tasks.add_task(
        process_document_background,
        document.id,
        embedding_service,
    )

    return to_document_response(
        db=db,
        workspace=workspace,
        document=document,
    )
    
    
    
def reprocess_document(
    db: Session,
    workspace: Workspace,
    document_id: int,
    embedding_service: EmbeddingService,
    background_tasks: BackgroundTasks,
) -> Document:

    document = get_document(
        db=db,
        document_id=document_id,
        workspace=workspace,
    )

    if document.status == DocumentStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document is already being processed.",
        )

    chunk_ids_statement = (
        select(DocumentChunk.id)
        .where(DocumentChunk.document_id == document.id)
    )

    chunk_ids = db.scalars(chunk_ids_statement).all()

    if chunk_ids:
        db.execute(
            delete(DocumentEmbedding).where(
                DocumentEmbedding.document_chunk_id.in_(chunk_ids)
            )
        )

    db.execute(
        delete(DocumentChunk).where(
            DocumentChunk.document_id == document.id
        )
    )

    document.status = DocumentStatus.PROCESSING
    document.processing_error = None

    db.commit()
    db.refresh(document)

    background_tasks.add_task(
        process_document_background,
        document.id,
        embedding_service,
    )

    return document
    

def update_document(
    db: Session,
    workspace: Workspace,
    document_id: int,
    document_update: DocumentUpdate,
) -> Document:

    document = get_document(
        db=db,
        document_id=document_id,
        workspace=workspace,
    )

    update_data = document_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(document, field, value)

    db.commit()
    db.refresh(document)

    return document


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
    




def to_document_response(
    db: Session,
    workspace: Workspace,
    document: Document,
):

    conversation = get_document_conversation(
        db=db,
        workspace=workspace,
        document=document,
    )

    return {
        "id": document.id,
        "original_filename": document.original_filename,
        "conversation_id": conversation.id,
        "content_type": document.content_type,
        "file_size": document.file_size,
        "status": document.status,
        "stage": document.stage,
        "progress": document.progress,
        "processing_error": document.processing_error,
        "include_in_workspace_context": document.include_in_workspace_context,
        "created_at": document.created_at,
        "updated_at": document.updated_at,
    }
    
    