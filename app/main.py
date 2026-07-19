from fastapi import FastAPI

app = FastAPI(title="LearnOS AI")


@app.get("/")
def root():
    return {"message": "Welcome to LearnOS AI"}
