from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from policy_writer.common.auth import password_matches, require_app_password
from policy_writer.config import get_settings
from policy_writer.llm import catalog, cost
from policy_writer.llm.client import call_llm

router = APIRouter()


class ValidateKeyIn(BaseModel):
    provider: str
    api_key: str


@router.post("/api/validate-key")
async def validate_key(payload: ValidateKeyIn, _auth: None = Depends(require_app_password)) -> dict:
    """가장 싼 모델로 1토큰만 불러서 키가 살아 있는지 본다. AI 를 호출해 돈을 쓰므로 접속 암호로 막는다."""
    if payload.provider not in catalog.MODELS:
        raise HTTPException(400, f"지원하지 않는 회사: {payload.provider}")
    cheapest = catalog.MODELS[payload.provider][0]
    await call_llm(
        provider=payload.provider,
        model_meta=cheapest,
        api_key=payload.api_key,
        system_prompt="ping",
        user_prompt="ping",
        max_tokens=16,
        timeout=30.0,
    )
    return {"ok": True, "message": "정상 연결되었습니다."}


@router.get("/api/local-keys")
def local_keys() -> dict:
    """🔴 development 에서만 값이 나온다. production 이면 빈 dict."""
    return {"keys": get_settings().local_llm_keys}


@router.get("/api/models")
def list_models() -> dict:
    """화면이 이걸 받아 그린다. 목록이 두 벌이 되지 않게 한다."""
    return {
        provider: [
            {"id": m["id"], "tier": m["tier"], "won_per_doc": cost.won_per_doc(m)}
            for m in models
        ]
        for provider, models in catalog.MODELS.items()
    }


class AuthCheckIn(BaseModel):
    password: str


@router.get("/api/auth/required")
def auth_required() -> dict:
    """화면이 초기 렌더에 부른다 — 암호를 안 건 환경에서는 입력 화면을 띄우지 않아야 한다.

    production 인데 APP_PASSWORD 가 비어 있으면(배포자의 설정 누락) 그냥
    {"required": False}를 내려주지 않는다 — 화면이 "암호 불필요"로 오해해 곧장 앱을
    보여주면 안 되기 때문이다. 이 상태에서는 require_app_password 가 모든 유료
    라우트를 503 으로 막고 있으므로, misconfigured 플래그로 화면에 문제를 알린다."""
    settings = get_settings()
    if settings.environment == "production" and not settings.app_password:
        return {"required": True, "misconfigured": True}
    return {"required": bool(settings.app_password)}


@router.post("/api/auth/check")
def auth_check(payload: AuthCheckIn) -> dict:
    """화면이 입력받은 암호를 확인하는 창구. AI 를 부르지 않으므로 암호 게이트 자체는 걸지 않는다."""
    if not password_matches(payload.password):
        raise HTTPException(401, "접속 암호가 올바르지 않습니다.")
    return {"ok": True}
