from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from policy_writer.common.auth import (
    NON_ASCII_PASSWORD_MESSAGE,
    UNSAFE_SERVER_PASSWORD_MESSAGE,
    is_ascii_only,
    is_safe_header_value,
    password_matches,
)
from policy_writer.config import get_settings
from policy_writer.llm import catalog, cost

router = APIRouter()

# ── 삭제 (2026-09-07 컨트롤러 추가지시 Fix 1) ──────────────────────────────
# POST /api/validate-key ("연결 시험") 를 지웠다. payload.api_key 를 JSON 바디에서
# 그대로 받아 resolve_user_key()·is_safe_header_value() 를 거치지 않고 곧장
# call_llm() 에 넘기고 있었다 — 헤더 경로의 키 검증(2026-09-07 컨트롤러 추가지시
# §3)이 있어도 이 라우트는 그걸 비껴갔다. JSON 바디는 애초에 ASCII 제약이 없어
# 헤더 경로보다 더 뚫기 쉬웠고,
# h11 의 예외 메시지가 키 값을 그대로 담아(`Illegal header value b'Bearer
# sk-...'`) uvicorn 로그로 흘러갈 수 있었다(G12 위반). frontend/src 전체·
# tests·scripts 를 grep 해 이 라우트를 부르는 곳이 하나도 없음을 확인했다 —
# SettingsPage.tsx 의 "API 키" 섹션은 이미 "서버에 키가 설정돼 있어 직접
# 입력하지 않아도 됩니다"만 보여줄 뿐 입력칸도 [연결 시험] 버튼도 없다.
# 클라이언트가 키를 들고 있던 옛 모델의 마지막 흔적이라 가드를 추가하는 대신
# 라우트 자체를 지웠다(G10: 만들어놓고 안 부르는 함수 금지 — 같은 원칙을
# "아무도 안 부르는 라우트"에도 적용). call_llm() 도달 지점이 하나 줄어
# resolve_user_key() 가 유일한 통로가 됐다.


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
      2) APP_PASSWORD 자체가 outbound/inbound HTTP 헤더로 안전하게 왕복할 수
         없는 형태(수정 라운드 2·Fix 4) — 비-ASCII 문자(한글 등)는 애초에
         ISO-8859-1 제약으로 헤더에 실을 수 없고, 앞뒤 공백·개행은 h11 이
         인바운드 헤더를 파싱할 때 자동으로 잘라내므로(RFC 7230 OWS) 어떤
         사용자가 무엇을 입력해도 저장된 값과 절대 일치하지 않는다. 둘 다
         `is_safe_header_value()`(common/auth.py) 하나로 함께 잡는다."""
    settings = get_settings()
    password = settings.app_password
    unset_in_production = settings.environment == "production" and not password
    unsafe_server_password = bool(password) and not is_safe_header_value(password)
    if unset_in_production or unsafe_server_password:
        return {"required": True, "misconfigured": True}
    return {"required": bool(password)}


@router.post("/api/auth/check")
def auth_check(payload: AuthCheckIn) -> dict:
    """화면이 입력받은 암호를 확인하는 창구. AI 를 부르지 않으므로 암호 게이트 자체는 걸지 않는다.

    비-ASCII(한글 등) 암호는 401(암호 틀림)이 아니라 400(쓸 수 없는 형식)으로
    먼저 거부한다(수정 라운드 2) — X-App-Password 헤더로 왕복할 수 없어, 이걸
    걸러내지 않으면 이 화면을 거치지 않고 API 를 직접 호출했을 때 로그인은
    "성공"하고 그 뒤 모든 요청만 조용히 실패하는 상태가 된다.

    사용자가 입력한 값이 아니라 **서버에 설정된** APP_PASSWORD 자체가 깨진
    경우(앞뒤 공백·개행·비-ASCII)는 503 이다(Fix 4) — candidate 가 무엇이든
    password_matches() 는 절대 True 를 반환할 수 없으므로(h11 이 인바운드
    헤더의 앞뒤 공백을 잘라내 후속 요청에서도 재현 불가능), 그대로 두면
    사용자에게는 "계속 틀린 암호"로만 보이고 운영자는 원인을 알 길이 없다.
    이 검사를 password_matches() 호출보다 먼저 해서, 애초에 맞을 수 없는
    비교로 사용자를 401 미로에 몰아넣지 않는다."""
    if not is_ascii_only(payload.password):
        raise HTTPException(400, NON_ASCII_PASSWORD_MESSAGE)
    server_password = get_settings().app_password
    if server_password and not is_safe_header_value(server_password):
        raise HTTPException(503, UNSAFE_SERVER_PASSWORD_MESSAGE)
    if not password_matches(payload.password):
        raise HTTPException(401, "접속 암호가 올바르지 않습니다.")
    return {"ok": True}
