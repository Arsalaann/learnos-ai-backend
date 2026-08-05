from fastapi import FastAPI

import app.core.logging
from app.api.router import register_routes
from app.core.exceptions import register_exception_handlers
from app.core.lifespan import lifespan
from app.core.middleware import register_middlewares

app = FastAPI(lifespan=lifespan)

register_exception_handlers(app)
register_middlewares(app)
register_routes(app)


@app.get("/")
def read_root():
    return {"message": "Welcome to LearnOS AI"}