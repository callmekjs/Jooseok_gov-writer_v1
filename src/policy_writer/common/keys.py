from fastapi import HTTPException, Request

from policy_writer.common.auth import is_ascii_only
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
# common/auth.is_ascii_only 를 그대로 재사용한다(G9) — 이유는 다르지만("암호가 헤더를
# 왕복할 수 있나" vs "키가 outbound 헤더를 만들 수 있나") 둘 다 "HTTP 헤더 값은 인쇄
# 가능 ASCII 만 안전하게 왕복된다"는 같은 제약에서 나온다. 개행·탭 등 제어문자는
# is_ascii_only 가 이미 걸러낸다(0x20~0x7E 밖이라서). 다만 트레일링 스페이스만 남은
# 경우(예: "sk-abcdef ")는 인쇄 가능 ASCII 라 is_ascii_only 만으로는 통과해 버리는데,
# 실제로 h11 에 넣어 보면 이것도 "Illegal header value" 로 거부된다(개발 중 직접 확인) —
# 그래서 앞뒤 공백 여부를 별도로 확인한다.
def is_safe_header_value(value: str) -> bool:
    """value 를 그대로 outbound HTTP 요청 헤더에 넣어도 안전한지 검사한다.

    인쇄 가능 ASCII(0x20~0x7E)만 허용하고, 앞뒤 공백도 거부한다. 빈 문자열은 이
    함수의 관심사가 아니다 — "키가 없음"과 "키 형식이 깨짐"은 다른 문제이므로
    호출부가 따로 다룬다(resolve_user_key 는 이미 값이 있을 때만 이 함수를 부른다)."""
    return is_ascii_only(value) and value == value.strip()


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
                "관리자는 값 앞뒤에 공백·줄바꿈이 섞이지 않았는지 확인해 주세요.",
            )
        return server_key

    raise HTTPException(401, "이 회사의 API 키가 서버에 설정되어 있지 않습니다. 관리자에게 문의해 주세요.")
