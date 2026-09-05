from fastapi import HTTPException, Request

from policy_writer.llm.catalog import DEFAULT_PROVIDER

HEADER_BY_PROVIDER = {
    "openai": "X-OpenAI-Key",
    "anthropic": "X-Anthropic-Key",
}


def norm_provider(raw: str | None) -> str:
    p = (raw or "").strip().lower()
    return p if p in HEADER_BY_PROVIDER else DEFAULT_PROVIDER


def resolve_user_key(request: Request, provider: str) -> str:
    header = HEADER_BY_PROVIDER[provider]
    key = (request.headers.get(header) or "").strip()
    if not key:
        raise HTTPException(401, "설정에서 API 키를 먼저 입력해 주세요.")
    return key
