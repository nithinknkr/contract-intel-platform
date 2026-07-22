from fastapi import FastAPI

import app.models  # noqa: F401 — registers all models on Base.metadata

from app.routers import auth, documents

app = FastAPI()
app.include_router(auth.router)
app.include_router(documents.router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "FastAPI is running!"
    }