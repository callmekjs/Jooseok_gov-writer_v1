from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from policy_writer.common.auth import (
    NON_ASCII_PASSWORD_MESSAGE,
    is_ascii_only,
    password_matches,
    require_app_password,
)
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

    서버 설정 자체가 잘못돼 아무도 로그인할 수 없는 두 경우를 misconfigured
    플래그로 알린다(둘 다 그냥 {"required": False}나 평범한 "암호 틀림"으로
    보이면 안 된다 — 화면이 오해하거나 사용자가 자기 탓으로 여기게 된다):
      1) production 인데 APP_PASSWORD 가 비어 있음(배포자의 설정 누락) — 이
         상태에서는 require_app_password 가 모든 유료 라우트를 503 으로 막는다.
      2) APP_PASSWORD 자체에 비-ASCII 문자(한글 등)가 있음(수정 라운드 2) —
         그 값을 X-App-Password 헤더로 보낼 방법이 없어(ISO-8859-1 제약) 어떤
         사용자가 무엇을 입력해도 로그인 유지가 안 된다."""
    settings = get_settings()
    password = settings.app_password
    unset_in_production = settings.environment == "production" and not password
    non_ascii_server_password = bool(password) and not is_ascii_only(password)
    if unset_in_production or non_ascii_server_password:
        return {"required": True, "misconfigured": True}
    return {"required": bool(password)}


@router.post("/api/auth/check")
def auth_check(payload: AuthCheckIn) -> dict:
    """화면이 입력받은 암호를 확인하는 창구. AI 를 부르지 않으므로 암호 게이트 자체는 걸지 않는다.

    비-ASCII(한글 등) 암호는 401(암호 틀림)이 아니라 400(쓸 수 없는 형식)으로
    먼저 거부한다(수정 라운드 2) — X-App-Password 헤더로 왕복할 수 없어, 이걸
    걸러내지 않으면 이 화면을 거치지 않고 API 를 직접 호출했을 때 로그인은
    "성공"하고 그 뒤 모든 요청만 조용히 실패하는 상태가 된다."""
    if not is_ascii_only(payload.password):
        raise HTTPException(400, NON_ASCII_PASSWORD_MESSAGE)
    if not password_matches(payload.password):
        raise HTTPException(401, "접속 암호가 올바르지 않습니다.")
    return {"ok": True}
