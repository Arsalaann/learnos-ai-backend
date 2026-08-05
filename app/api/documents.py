from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.embedding import get_embedding_service
from app.dependencies.workspace import get_current_workspace
from app.embeddings.service import EmbeddingService
from app.models.workspace import Workspace
from app.schemas.document import DocumentResponse, DocumentUpdate
from app.services.document_service import (
    create_document,
    delete_document,
    find_document_by_filename,
    get_document,
    get_documents,
    reprocess_document,
    to_document_response,
    update_document,
)

router = APIRouter()






@router.get("/{workspace_id}/documents/{document_id}", response_model=DocumentResponse)
def get_document_endpoint(document_id: int, workspace: Workspace = Depends(get_current_workspace), db: Session = Depends(get_db)):
    document = get_document(db, document_id, workspace)
    return to_document_response( db=db, workspace=workspace, document=document, )


@router.get("/{workspace_id}/documents", response_model=list[DocumentResponse])
def get_documents_endpoint(workspace: Workspace = Depends(get_current_workspace), db: Session = Depends(get_db)):
    documents = get_documents(db, workspace)

    return [ to_document_response( db=db, workspace=workspace, document=document, ) for document in documents ]






        
@router.post(
    "/{workspace_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),  # noqa: B008
    workspace: Workspace = Depends(get_current_workspace),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    db: Session = Depends(get_db),
):
    existing_document = find_document_by_filename(
        db,
        workspace,
        file.filename,
    )

    if existing_document is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document already exists in this workspace.",
        )

    return await create_document(
        db=db,
        file=file,
        workspace=workspace,
        embedding_service=embedding_service,
        background_tasks=background_tasks,
    )
    
    
    
    
    
    
    
    
@router.post(
    "/{workspace_id}/documents/{document_id}/reprocess",
    response_model=DocumentResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def reprocess_document_endpoint(
    document_id: int,
    background_tasks: BackgroundTasks,
    workspace: Workspace = Depends(get_current_workspace),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    db: Session = Depends(get_db),
):
    document = reprocess_document(
        db=db,
        workspace=workspace,
        document_id=document_id,
        embedding_service=embedding_service,
        background_tasks=background_tasks,
    )

    return to_document_response(
        db=db,
        workspace=workspace,
        document=document
    )

    
@router.patch( "/{workspace_id}/documents/{document_id}", response_model=DocumentResponse, )
def update_document_endpoint(
    document_id: int,
    document_update: DocumentUpdate,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    document = update_document(
        db=db,
        workspace=workspace,
        document_id=document_id,
        document_update=document_update,
    )

    return to_document_response( db=db, workspace=workspace, document=document )



@router.delete("/{workspace_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_endpoint(document_id: int, workspace: Workspace = Depends(get_current_workspace), db: Session = Depends(get_db)):
    delete_document(db, document_id, workspace)