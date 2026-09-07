import hmac

from fastapi import HTTPException, Request

from policy_writer.config import get_settings

APP_PASSWORD_HEADER = "X-App-Password"


def password_matches(candidate: str) -> bool:
    """설정된 접속 암호와 candidate 를 타이밍 공격에 안전하게 비교한다.
    APP_PASSWORD 가 비어 있으면(=잠그지 않음) 항상 True — require_app_password 와
    /api/auth/check 가 같은 비교 로직을 쓰도록 여기 한 곳에 모은다 (G9).

    비교 전에 반드시 UTF-8 바이트로 바꾼다 — hmac.compare_digest 는 str 인자에
    비-ASCII 문자가 하나라도 있으면(한글 암호 등) TypeError 를 던진다(파이썬 hmac
    모듈 자체의 제약). bytes 로 바꾸면 어떤 유니코드 문자열도 안전하게 비교된다."""
    expected = get_settings().app_password
    if not expected:
        return True
    return hmac.compare_digest(expected.encode("utf-8"), (candidate or "").encode("utf-8"))


def require_app_password(request: Request) -> None:
    """APP_PASSWORD 가 설정돼 있으면 X-App-Password 헤더를 검사한다.

    APP_PASSWORD 가 비어 있으면:
      - production 이 아니면(로컬 개발 등) 통과시킨다 — 기존 동작과 동일.
      - production 이면 503 으로 거부한다 — 배포자가 Render 등에 APP_PASSWORD 를
        설정하는 것을 빼먹었을 때, 이미 세팅된 진짜 유료 키를 쓰는 서버가 조용히
        완전 개방되는 것을 막는다. 401(암호 오류)이 아니라 503(서버 설정 오류)인
        이유는 사용자가 암호를 틀린 게 아니라 서버가 아직 설정되지 않은 상태이기
        때문이다 — 운영자가 무엇을 해야 하는지 알 수 있는 메시지여야 한다.

    APP_PASSWORD 에 값은 있지만 HTTP 헤더로 안전하게 왕복할 수 없는 형태(비-ASCII
    또는 앞뒤 공백·개행)면 마찬가지로 503 이다(2026-09-07 Fix 4) — h11 이 인바운드
    헤더 값의 앞뒤 공백을 자동으로 잘라내므로(RFC 7230 OWS), 예를 들어 Render
    대시보드에 `" pw "`처럼 공백이 섞여 들어가면 어떤 사용자가 무엇을 입력해도
    저장된 값과 절대 일치할 수 없다 — password_matches() 로 흘려보내면 매번 401
    "접속 암호가 올바르지 않습니다"만 반복되고, 사용자는 자기 탓인 줄 알지만
    실제로는 아무도 로그인할 수 없는 서버 설정 오류다. 그래서 비교를 시도하기
    전에 먼저 걸러 misconfigured 로 분류한다."""
    settings = get_settings()
    if not settings.app_password:
        if settings.environment == "production":
            raise HTTPException(
                503,
                "서버에 접속 암호가 설정되지 않았습니다. 관리자는 APP_PASSWORD 환경변수를 설정해 주세요.",
            )
        return
    if not is_safe_header_value(settings.app_password):
        raise HTTPException(503, UNSAFE_SERVER_PASSWORD_MESSAGE)
    if not password_matches(request.headers.get(APP_PASSWORD_HEADER) or ""):
        raise HTTPException(401, "접속 암호가 올바르지 않습니다.")


# ── 수정 라운드 2 ─────────────────────────────────────────────────────────
# 🔴 Critical: 라운드 1 이 hmac.compare_digest 를 bytes 비교로 고쳐 "한글 암호가
# 서버를 500 으로 죽이는" 문제는 막았지만, 더 근본적인 제약이 남아 있다 —
# HTTP 커스텀 헤더 값은 규격상 ISO-8859-1(라틴-1)이라 한글 등 비-ASCII 문자는
# X-App-Password 헤더로 애초에 왕복이 안 된다(실제 브라우저 fetch 도 헤더에
# 비-Latin1 문자를 넣으면 TypeError 를 던진다). 그 결과 POST /api/auth/check
# (JSON 바디)에서는 로그인이 "성공"하지만, 그 뒤 모든 요청이 담는 헤더에서는
# 같은 값이 조용히 실패한다 — 로그인 성공 후 원인 불명으로 아무것도 안 되는
# 최악의 실패 방식이다. 그래서 왕복 불가능한 암호는 입력·설정 시점에 명확히
# 거부한다. NON_ASCII_PASSWORD_MESSAGE 와 is_ascii_only 를 여기 한 곳에 모아
# /api/auth/check(입력 검사)와 /api/auth/required(서버 설정 검사)가 함께 쓴다.

NON_ASCII_PASSWORD_MESSAGE = "암호는 영문·숫자·기호만 사용할 수 있습니다. (한글은 사용할 수 없습니다)"


def is_ascii_only(value: str) -> bool:
    """value 가 인쇄 가능 ASCII(0x20~0x7E)만으로 이루어져 있는지 검사한다.

    이 범위 밖의 문자(한글 등)가 하나라도 있으면 False — HTTP 헤더 값(ISO-8859-1)
    으로 왕복할 수 없는 문자라는 뜻이다. 빈 문자열은 True(all()의 공허참) —
    "비어 있음"과 "쓸 수 없는 문자를 포함함"은 서로 다른 문제이므로, 빈 값을
    이 함수로 거부하지 않는다(호출부가 필요하면 따로 빈 값을 검사한다)."""
    return all("\x20" <= ch <= "\x7e" for ch in value)


# ── 이동 (2026-09-07 컨트롤러 추가지시 Fix 4) ───────────────────────────────
# is_safe_header_value() 는 원래 common/keys.py 에 있었다(2026-09-07 컨트롤러
# 추가지시 §3, resolve_user_key() 가 outbound LLM 키 헤더를 만들기 전에 검사하려고
# 추가함 — 오늘 이 세션의 "Fix 3"(PLAN.md G-표)와는 다른, 그 이전 세션의 항목이다).
# 여기 auth.py 로 옮긴 이유: require_app_password() 에도 **같은 예측**이
# 필요해졌는데("이 값을 HTTP 헤더로 안전하게 왕복시킬 수 있나"), keys.py 는
# 이미 auth.py 를 import 하고 있어(is_ascii_only) auth.py 가 거꾸로 keys.py 를
# import 하면 순환 참조가 된다. 함수를 의존 방향이 맞는 이 파일로 옮기고,
# keys.py 는 (이미 하던 대로) auth.py 에서 가져다 쓴다 — resolve_user_key() 의
# 로직·근거는 전혀 바뀌지 않았다.
def is_safe_header_value(value: str) -> bool:
    """value 를 그대로 HTTP 헤더 값(요청 헤더 인바운드 또는 outbound 요청 헤더)으로
    써도 안전한지 검사한다.

    인쇄 가능 ASCII(0x20~0x7E)만 허용하고, 앞뒤 공백도 거부한다. 개행·탭 등
    제어문자는 is_ascii_only 가 이미 걸러낸다. 앞뒤 공백만 남은 값(예: " pw ")은
    인쇄 가능 ASCII 라 is_ascii_only 만으로는 통과하지만, h11 이 아웃바운드
    전송 시점에 "Illegal header value" 로 거부하거나(LLM 키 경로) 인바운드 파싱
    시점에 값을 잘라내(RFC 7230 OWS, 접속 암호 경로) 저장된 값과 무엇을 보내도
    맞을 수 없게 만든다 — 그래서 앞뒤 공백 여부를 별도로 확인한다.

    빈 문자열은 이 함수의 관심사가 아니다 — "값이 없음"과 "값 형식이 깨짐"은
    다른 문제이므로 호출부가 따로 다룬다(resolve_user_key·require_app_password
    모두 이미 값이 있을 때만 이 함수를 부른다)."""
    return is_ascii_only(value) and value == value.strip()


UNSAFE_SERVER_PASSWORD_MESSAGE = (
    "서버에 설정된 APP_PASSWORD 형식이 올바르지 않습니다. 관리자는 값 앞뒤에 "
    "공백·줄바꿈이 섞이지 않았는지, 한글 등 비-ASCII 문자가 섞이지 않았는지 확인해 주세요."
)
