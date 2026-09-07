from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from policy_writer.config import get_settings

app = FastAPI(title="말씀자료 작성기", version="1.0.0")
settings = get_settings()

STATIC_DIR = Path(__file__).resolve().parents[2] / "static"

# ── 1) CORS — 개발일 때만 ────────────────────────────────
# ★ 5174 는 frontend/vite.config.ts 의 server.port 와 일치해야 한다. 8010·5173 은
#   이 PC 의 다른 프로젝트 전용 포트라 이 저장소는 8011·5174 를 쓴다.
if settings.environment == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5174"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],     # X-LLM-Provider 등 커스텀 헤더 통과에 필요
    )

# ── 2) 라우터 — Task 3·5·7·10 에서 여기에 추가된다 ────────
from policy_writer.api import download_router, drafts_router, settings_router, speech_router

app.include_router(speech_router, prefix="/api/speech")
app.include_router(download_router, prefix="/api/download")
app.include_router(drafts_router, prefix="/api/drafts")
app.include_router(settings_router)

# ── 3) 검증 오류 → 400 (Task 11-C) ───────────────────────
# pydantic 이 요청 바디를 검증하다 실패하면 FastAPI 는 기본적으로 422 를 내는데,
# PLAN 의 API 계약은 400 이다(프론트 HINT 맵에도 422 가 없다 — ErrorBanner.tsx).
# 위치는 G8 과 무관 — G8 은 SPA 폴백 라우트 순서에만 해당한다.
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """pydantic 의 영문 오류 원문을 그대로 노출하지 않고 한글 문구로 바꾼다.
    본문은 api.ts:57 의 `detail.detail` 이 읽는 모양과 같은 {"detail": "<str>"} 이어야
    한다 — FastAPI 기본 422 응답의 {"detail": [...]} (리스트) 모양이 아니다.

    일반 문구는 ErrorBanner.tsx 의 400 HINT("입력값을 확인해 주세요.")와 다른
    문장이어야 한다 — 같으면 배너에 같은 문장이 메시지 줄과 힌트 줄에 두 번
    찍힌다. 이 메시지는 "무엇이 문제인지", 힌트는 "어떻게 하면 되는지"를
    말하도록 나눈다."""
    errors = exc.errors()
    loc = errors[0].get("loc", ()) if errors else ()
    field = loc[-1] if loc else None
    message = "행사명은 필수입니다." if field == "event_name" else "입력하신 값이 올바르지 않습니다."
    return JSONResponse(status_code=400, content={"detail": message})


# ── 4) 기본 엔드포인트 ───────────────────────────────────
@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/info")
def info() -> dict:
    return {
        "name": "policy-writer",
        "version": "1.0.0",
        "environment": settings.environment,
    }


# ── 5) ★ SPA 폴백 — 반드시 맨 마지막 (G8) ────────────────
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
