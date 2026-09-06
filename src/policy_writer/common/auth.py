import hmac

from fastapi import HTTPException, Request

from policy_writer.config import get_settings

APP_PASSWORD_HEADER = "X-App-Password"


def password_matches(candidate: str) -> bool:
    """설정된 접속 암호와 candidate 를 타이밍 공격에 안전하게 비교한다.
    APP_PASSWORD 가 비어 있으면(=잠그지 않음) 항상 True — require_app_password 와
    /api/auth/check 가 같은 비교 로직을 쓰도록 여기 한 곳에 모은다 (G9)."""
    expected = get_settings().app_password
    if not expected:
        return True
    return hmac.compare_digest(candidate or "", expected)


def require_app_password(request: Request) -> None:
    """APP_PASSWORD 가 설정돼 있으면 X-App-Password 헤더를 검사한다.
    설정돼 있지 않으면(로컬 개발 등) 통과시킨다."""
    if not password_matches(request.headers.get(APP_PASSWORD_HEADER) or ""):
        raise HTTPException(401, "접속 암호가 올바르지 않습니다.")
