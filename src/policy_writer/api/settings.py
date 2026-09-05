from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from policy_writer.config import get_settings
from policy_writer.llm import catalog
from policy_writer.llm.client import call_llm

router = APIRouter()


class ValidateKeyIn(BaseModel):
    provider: str
    api_key: str


@router.post("/api/validate-key")
async def validate_key(payload: ValidateKeyIn) -> dict:
    """가장 싼 모델로 1토큰만 불러서 키가 살아 있는지 본다."""
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
