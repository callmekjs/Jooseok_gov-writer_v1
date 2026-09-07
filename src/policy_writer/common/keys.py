from fastapi import HTTPException, Request

from policy_writer.common.auth import is_safe_header_value
from policy_writer.config import get_settings
from policy_writer.llm.catalog import DEFAULT_PROVIDER

HEADER_BY_PROVIDER = {
    "openai": "X-OpenAI-Key",
    "anthropic": "X-Anthropic-Key",
}

# provider -> Settings 의 서버 키 필드 이름. 헤더에 키가 없을 때의 폴백에 쓴다 (G7: get_settings() 만).
# resolve_user_key() 가 503 메시지에 쓸 환경변수 이름도 이 딕셔너리에서 그대로 뽑는다
# (pydantic-settings 의 기본 규칙: 필드 openai_api_key ↔ 환경변수 OPENAI_API_KEY) — 매핑을
# 두 벌 두지 않는다 (G9).
SETTINGS_ATTR_BY_PROVIDER = {
    "openai": "openai_api_key",
    "anthropic": "anthropic_api_key",
}


def norm_provider(raw: str | None) -> str:
    p = (raw or "").strip().lower()
    return p if p in HEADER_BY_PROVIDER else DEFAULT_PROVIDER


# ── 수정 (2026-09-07 컨트롤러 추가지시 §3) ──────────────────────────────────
# 🔴 Critical: resolve_user_key() 가 돌려주는 값은 곧장 llm/client.py 가 outbound
# HTTP 헤더(Authorization / x-api-key)를 만드는 데 쓰인다. 값에 비-ASCII 문자가 있으면
# httpx 가 그 헤더 딕셔너리를 만드는 순간 UnicodeEncodeError 를 던지고, 앞뒤에 공백만
# 남아 있어도(개행이 없어도) 실제 전송 시점에 h11(httpx 가 쓰는 HTTP/1.1 계층)이
# "Illegal header value" LocalProtocolError 를 던진다 — 둘 다 llm/client.py 의
# `except httpx.TimeoutException` 에 걸리지 않고 그대로 위로 튀어 올라가 사용자에게는
# 맨 500 이 된다. 실제로 겪은 결함이다: 운영자가 Render 대시보드에 키를 붙여 넣을 때
# 뒤에 개행이나 공백이 섞여 들어가는 흔한 실수가 원인이었다.
#
# is_safe_header_value() 는 common/auth.py 에 있다(2026-09-07 Fix 4 로 그리 옮김) —
# require_app_password() 도 같은 예측("이 값을 HTTP 헤더로 안전하게 왕복시킬 수
# 있나")이 필요해졌는데, keys.py 가 이미 auth.py 를 import 하므로 auth.py 가 거꾸로
# keys.py 를 import 하면 순환 참조가 된다. 의존 방향이 맞는 auth.py 에 함수를 두고
# 여기서는 그대로 가져다 쓴다(G9) — 아래 resolve_user_key() 의 로직·근거는 옮기기
# 전과 동일하다.


def resolve_user_key(request: Request, provider: str) -> str:
    """1) 헤더에 키가 있으면 그것을 쓴다.
    2) 없으면 서버 설정(.env 로컬 / Render 배포)의 키로 대신한다.
    3) 둘 다 없으면 401.

    두 경로 모두, 값이 있으면 반환 전에 is_safe_header_value() 로 형식을 검사한다 —
    이 함수의 반환값이 그대로 outbound HTTP 헤더가 되기 때문이다. 두 실패를 다른
    상태 코드·다른 청중으로 구분한다:

      - 헤더로 들어온 사용자 키가 깨져 있으면 401. 사용자 자신이 보낸 값이 문제이므로
        이미 있는 "키 없음"·"인증 실패"(llm/client.py)와 같은 401 계열로 묶는다 —
        사용자에게 "키를 다시 확인해 달라"고 말하는 것이 맞는 상황이다.
      - 서버에 설정된 키가 깨져 있으면 503. 요청한 사람의 잘못이 아니라 운영자가 키를
        잘못 넣은 것이므로, common/auth.require_app_password 가 "운영자가 APP_PASSWORD
        를 안 넣었을 때" 이미 쓰고 있는 503(서버 설정 오류) 관례를 그대로 따른다(G9) —
        401 로 묶으면 "네가 키를 잘못 보냈다"처럼 읽혀 사용자를 탓하는 모양이 된다.
        메시지에 어떤 환경변수를 봐야 하는지 이름을 직접 박아 준다 — 이 역시
        require_app_password 가 "APP_PASSWORD 환경변수를 설정해 주세요"로 이름을
        박아 주는 것과 같은 패턴이다.

    🔴 두 메시지 모두 키 값 자체는 절대 담지 않는다(G12) — 어떤 문자가 문제인지만
    말하고, 값은 로그에도 남기지 않는다."""
    header = HEADER_BY_PROVIDER[provider]
    key = (request.headers.get(header) or "").strip()
    if key:
        if not is_safe_header_value(key):
            raise HTTPException(401, "제공한 API 키 형식이 올바르지 않습니다. 키를 다시 확인해 주세요.")
        return key

    server_key = getattr(get_settings(), SETTINGS_ATTR_BY_PROVIDER[provider], "")
    if server_key:
        if not is_safe_header_value(server_key):
            env_var = SETTINGS_ATTR_BY_PROVIDER[provider].upper()
            raise HTTPException(
                503,
                f"서버에 설정된 {env_var} 형식이 올바르지 않습니다. "
                "관리자는 값 앞뒤에 공백·줄바꿈이 섞이지 않았는지, 한글 등 비-ASCII 문자가 "
                "섞이지 않았는지(예: 복사·붙여넣기 중 섞여 들어간 특수 따옴표·전각 문자) 확인해 주세요.",
            )
        return server_key

    raise HTTPException(401, "이 회사의 API 키가 서버에 설정되어 있지 않습니다. 관리자에게 문의해 주세요.")
