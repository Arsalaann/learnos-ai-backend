from fastapi import FastAPI

from app.api.conversations import router as conversations_router
from app.api.document_ai import router as document_ai_router
from app.api.documents import router as documents_router
from app.api.events import router as events_router
from app.api.messages import router as messages_router
from app.api.users import router as users_router
from app.api.workspaces import router as workspaces_router


def register_routes(app: FastAPI):
    app.include_router(users_router, prefix="/users", tags=["Users"])
    
    app.include_router(workspaces_router, prefix="/workspaces", tags=["Workspaces"])
    app.include_router(conversations_router, prefix="/workspaces", tags=["Conversations"])
    app.include_router(documents_router, prefix="/workspaces", tags=["Documents"])
    app.include_router(document_ai_router, prefix="/workspaces", tags=["Document_AI"])
    app.include_router(events_router,prefix="/workspaces",tags=["Events"])
    
    app.include_router(messages_router, prefix="/conversations", tags=["Messages"])
    
    