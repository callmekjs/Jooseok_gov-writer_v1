from fastapi import FastAPI

from policy_writer.config import get_settings

app = FastAPI(title="말씀자료 작성기", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/info")
def info() -> dict:
    settings = get_settings()
    return {
        "name": "policy-writer",
        "version": "0.1.0",
        "environment": settings.environment,
    }
