from fastapi import FastAPI

from app.api.users import router as users_router

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI application!"}

app.include_router(users_router, prefix="/users", tags=["Users"])