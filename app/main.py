from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI

from app.api.users import router as users_router
from app.core.database import engine
from app.models.base import Base



app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI application!"}

app.include_router(users_router, prefix="/users", tags=["Users"])