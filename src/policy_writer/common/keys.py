from fastapi import HTTPException, Request

from policy_writer.config import get_settings
from policy_writer.llm.catalog import DEFAULT_PROVIDER

HEADER_BY_PROVIDER = {
    "openai": "X-OpenAI-Key",
    "anthropic": "X-Anthropic-Key",
}

# provider -> Settings 의 서버 키 필드 이름. 헤더에 키가 없을 때의 폴백에 쓴다 (G7: get_settings() 만).
SETTINGS_ATTR_BY_PROVIDER = {
    "openai": "openai_api_key",
    "anthropic": "anthropic_api_key",
}


def norm_provider(raw: str | None) -> str:
    p = (raw or "").strip().lower()
    return p if p in HEADER_BY_PROVIDER else DEFAULT_PROVIDER


def resolve_user_key(request: Request, provider: str) -> str:
    """1) 헤더에 키가 있으면 그것을 쓴다.
    2) 없으면 서버 설정(.env 로컬 / Render 배포)의 키로 대신한다.
    3) 둘 다 없으면 401."""
    header = HEADER_BY_PROVIDER[provider]
    key = (request.headers.get(header) or "").strip()
    if key:
        return key

    server_key = getattr(get_settings(), SETTINGS_ATTR_BY_PROVIDER[provider], "")
    if server_key:
        return server_key

    raise HTTPException(401, "이 회사의 API 키가 서버에 설정되어 있지 않습니다. 관리자에게 문의해 주세요.")
