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
        때문이다 — 운영자가 무엇을 해야 하는지 알 수 있는 메시지여야 한다."""
    settings = get_settings()
    if not settings.app_password:
        if settings.environment == "production":
            raise HTTPException(
                503,
                "서버에 접속 암호가 설정되지 않았습니다. 관리자는 APP_PASSWORD 환경변수를 설정해 주세요.",
            )
        return
    if not password_matches(request.headers.get(APP_PASSWORD_HEADER) or ""):
        raise HTTPException(401, "접속 암호가 올바르지 않습니다.")
