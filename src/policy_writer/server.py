from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from policy_writer.config import get_settings

app = FastAPI(title="말씀자료 작성기", version="0.1.0")
settings = get_settings()

STATIC_DIR = Path(__file__).resolve().parents[2] / "static"

# ── 1) CORS — 개발일 때만 ────────────────────────────────
if settings.environment == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],     # X-LLM-Provider 등 커스텀 헤더 통과에 필요
    )

# ── 2) 라우터 — Task 3·5·7·10 에서 여기에 추가된다 ────────
# app.include_router(...)

# ── 3) 기본 엔드포인트 ───────────────────────────────────
@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/info")
def info() -> dict:
    return {
        "name": "policy-writer",
        "version": "0.1.0",
        "environment": settings.environment,
    }


# ── 4) ★ SPA 폴백 — 반드시 맨 마지막 (G8) ────────────────
if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str) -> FileResponse:
        # /api/* 는 SPA 폴백이 잡지 않는다.
        # 라우터에 없는 API 경로는 HTML 이 아니라 404 JSON 으로 답해야
        # 라우터 등록 누락을 바로 알아챌 수 있다.
        if full_path.startswith("api/"):
            raise HTTPException(404, "존재하지 않는 API 경로입니다.")
        return FileResponse(STATIC_DIR / "index.html")
