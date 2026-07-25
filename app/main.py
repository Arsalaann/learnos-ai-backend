from fastapi import FastAPI

import app.core.logging #let it be for logging configuration
from app.core.exceptions import register_exception_handlers
from app.core.middleware import register_middlewares

from app.api.users import router as users_router
from app.api.files import router as files_router

app = FastAPI()
register_exception_handlers(app)
register_middlewares(app)

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI application!"}

app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(files_router, prefix="/files", tags=["Files"])