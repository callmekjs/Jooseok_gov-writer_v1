"""접속 암호 게이트(common/auth.py)와 /api/auth/* 엔드포인트.

AI 는 호출하지 않는다 — 접속 암호 검사는 LLM 호출보다 훨씬 앞선 단계(라우터
의존성)에서 끝나므로, 암호가 맞아도 이 테스트 환경에는 키가 없어(conftest.py)
그 다음 단계인 키 검사에서 끝난다. 그래도 상관없다 — 여기서 확인할 것은
"암호 검사를 통과했는가"뿐이다.
"""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.requests import Request

from policy_writer.common import auth
from policy_writer.config import get_settings
from policy_writer.server import app

client = TestClient(app)

VALID_DRAFT_BODY = {"input": {"event_name": "테스트 행사"}}


def _req(headers: dict) -> Request:
    raw = [(k.lower().encode(), v.encode()) for k, v in headers.items()]
    return Request({"type": "http", "headers": raw})


def _is_password_401(resp) -> bool:
    return resp.status_code == 401 and "접속 암호" in resp.json().get("detail", "")


# ── common/auth.py 단위 테스트 ──────────────────────────────────────────


def test_require_app_password_passes_through_when_unset():
    """app_password 가 빈 문자열이면 헤더 없이도 통과한다 (conftest.py 가 이미 비워 둔다)."""
    assert get_settings().app_password == ""
    assert auth.require_app_password(_req({})) is None


def test_require_app_password_raises_401_when_header_missing(monkeypatch):
    monkeypatch.setattr(get_settings(), "app_password", "right-pw")
    with pytest.raises(HTTPException) as e:
        auth.require_app_password(_req({}))
    assert e.value.status_code == 401
    assert "접속 암호" in e.value.detail


def test_require_app_password_raises_401_when_header_wrong(monkeypatch):
    monkeypatch.setattr(get_settings(), "app_password", "right-pw")
    with pytest.raises(HTTPException) as e:
        auth.require_app_password(_req({"X-App-Password": "wrong-pw"}))
    assert e.value.status_code == 401


def test_require_app_password_passes_when_header_correct(monkeypatch):
    monkeypatch.setattr(get_settings(), "app_password", "right-pw")
    assert auth.require_app_password(_req({"X-App-Password": "right-pw"})) is None


# ── /api/speech/draft 를 통한 통합 테스트 ───────────────────────────────


def test_draft_without_header_is_401_when_password_set(monkeypatch):
    monkeypatch.setattr(get_settings(), "app_password", "right-pw")
    resp = client.post("/api/speech/draft", json=VALID_DRAFT_BODY)
    assert resp.status_code == 401
    assert "접속 암호" in resp.json()["detail"]


def test_draft_with_wrong_password_is_401(monkeypatch):
    monkeypatch.setattr(get_settings(), "app_password", "right-pw")
    resp = client.post(
        "/api/speech/draft",
        json=VALID_DRAFT_BODY,
        headers={"X-App-Password": "wrong-pw"},
    )
    assert resp.status_code == 401
    assert "접속 암호" in resp.json()["detail"]


def test_draft_with_correct_password_is_not_blocked_by_the_gate(monkeypatch):
    """암호가 맞으면 암호 때문에 막히지는 않는다. 이 테스트 환경엔 키가 없으므로
    (conftest.py) 그 뒤 키 검사 401 이 나는 것은 정상 — "접속 암호" 401 만 아니면 된다."""
    monkeypatch.setattr(get_settings(), "app_password", "right-pw")
    resp = client.post(
        "/api/speech/draft",
        json=VALID_DRAFT_BODY,
        headers={"X-App-Password": "right-pw"},
    )
    assert not _is_password_401(resp)


def test_draft_without_header_passes_gate_when_password_empty():
    # conftest.py 의 autouse fixture 가 app_password 를 이미 "" 로 비워 둔다.
    assert get_settings().app_password == ""
    resp = client.post("/api/speech/draft", json=VALID_DRAFT_BODY)
    assert not _is_password_401(resp)


# ── /api/auth/required, /api/auth/check ─────────────────────────────────


def test_auth_required_reflects_unset_password():
    resp = client.get("/api/auth/required")
    assert resp.status_code == 200
    assert resp.json() == {"required": False}


def test_auth_required_reflects_set_password(monkeypatch):
    monkeypatch.setattr(get_settings(), "app_password", "right-pw")
    resp = client.get("/api/auth/required")
    assert resp.json() == {"required": True}


def test_auth_check_ok_with_correct_password(monkeypatch):
    monkeypatch.setattr(get_settings(), "app_password", "right-pw")
    resp = client.post("/api/auth/check", json={"password": "right-pw"})
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_auth_check_401_with_wrong_password(monkeypatch):
    monkeypatch.setattr(get_settings(), "app_password", "right-pw")
    resp = client.post("/api/auth/check", json={"password": "wrong-pw"})
    assert resp.status_code == 401


# ── 수정 라운드 1 ─────────────────────────────────────────────────────────
# 🔴 Critical: 한글 등 비-ASCII 암호를 쓰면 hmac.compare_digest 가 str 인자를 그대로
# 받아 TypeError 를 던지고, 잡는 곳이 없어 그대로 500 이 된다 — expected(서버 쪽 값)
# 하나만 비-ASCII 여도 candidate 가 무엇이든(빈 문자열이어도) 즉시 터진다. 비교 전에
# 양쪽을 UTF-8 bytes 로 바꾸면 해결된다.


def test_non_ascii_password_works(monkeypatch):
    """한글 암호 비교 자체는 500 으로 죽지 않는다 — 맞으면 맞다고, 틀리면 401.

    [수정 라운드 2 에 따른 갱신] 이 테스트는 원래 "맞는 한글 암호는 POST
    /api/auth/check(JSON 바디)까지 통과한다(200)"는 것을 HTTP 레벨에서 확인했다.
    그런데 수정 라운드 2 가 /api/auth/check 에 "candidate 가 비-ASCII 면 맞고
    틀리고를 따지기 전에 400 으로 거부"하는 검사를 추가했다 — 서버가 맞다고
    판단해도 로그인 이후 그 값을 X-App-Password 헤더로 왕복시킬 방법이 없어
    조용히 막히는 것을 막기 위해서다(라운드 2 브리프, common/auth.is_ascii_only).
    그래서 이제 "맞는 한글 암호"는 200 이 아니라 400 이 나오는 것이 올바른
    동작이다 — 아래에서 그렇게 확인한다. 이 테스트가 원래 증명하려던 것("비교
    로직 자체가 non-ASCII 를 크래시 없이 올바르게 맞다고 인식하는가")은 라운드 2 의
    사전 검사를 우회해 auth.password_matches 를 직접 호출하는 방식으로 그대로
    유지한다.
    "틀린 암호" 쪽은 헤더 경로(/api/speech/draft)로 확인한다 — 원래 버그는 candidate
    가 무엇이든(흔한 ASCII 오타여도) expected 하나만 비-ASCII 면 즉시 TypeError 였다는
    것이 핵심이라, 가장 흔한 헤더 경로에서 그 부분이 고쳐졌는지를 함께 본다.
    require_app_password(헤더 게이트)·password_matches 자체는 라운드 2 에서 손대지
    않았으므로 이 두 확인은 라운드 1 때와 동일하게 유효하다."""
    monkeypatch.setattr(get_settings(), "app_password", "말씀자료2026")

    # 비교 로직 자체: 맞는 한글 암호는 500 없이 올바르게 "맞다"고 인식한다.
    assert auth.password_matches("말씀자료2026") is True

    # [수정 라운드 2] API 로 보내면 맞는 암호라도 비-ASCII 라 400(형식 거부)이다 —
    # 401(틀림)도 200(통과)도 아니다.
    resp = client.post("/api/auth/check", json={"password": "말씀자료2026"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == auth.NON_ASCII_PASSWORD_MESSAGE

    # 틀린 암호 -> 401 (500 아님)
    resp = client.post(
        "/api/speech/draft",
        json=VALID_DRAFT_BODY,
        headers={"X-App-Password": "wrong-pw"},
    )
    assert resp.status_code == 401
    assert "접속 암호" in resp.json()["detail"]


# 🟠 설계: production 인데 APP_PASSWORD 가 비어 있으면 require_app_password 가 지금까지
# 조용히 통과시켰다 — 배포자가 Render 에 APP_PASSWORD 설정을 빼먹으면, 이미 세팅된
# 진짜 유료 키를 쓰는 서버가 주소를 아는 누구에게나 완전히 열린다. fail-closed 로
# 바꿔서 이 상태에서는 유료 라우트를 503 으로 막는다(401 이 아닌 이유: 사용자가 암호를
# 틀린 게 아니라 서버 설정이 안 된 상태이므로).


def test_production_without_password_refuses_paid_routes(monkeypatch):
    """production 인데 APP_PASSWORD 가 없으면 503. 조용히 열리면 안 된다."""
    monkeypatch.setattr(get_settings(), "environment", "production")
    assert get_settings().app_password == ""  # conftest.py 가 이미 비워 둔다

    resp = client.post("/api/speech/draft", json=VALID_DRAFT_BODY)
    assert resp.status_code == 503
    assert "APP_PASSWORD" in resp.json()["detail"]

    # 유료 라우트만 막힌다 — 화면·헬스체크·로컬 키 폴백(G9 절대 규칙)은 그대로 살아
    # 있어야 한다. local_llm_keys 자체는 이번 작업에서 손대지 않았다.
    assert client.get("/health").status_code == 200
    assert client.get("/api/models").status_code == 200
    assert client.get("/api/local-keys").json() == {"keys": {}}


def test_development_without_password_still_passes(monkeypatch):
    """로컬 개발 편의는 유지된다."""
    monkeypatch.setattr(get_settings(), "environment", "development")
    assert get_settings().app_password == ""

    resp = client.post("/api/speech/draft", json=VALID_DRAFT_BODY)
    assert resp.status_code != 503
    assert not _is_password_401(resp)


def test_auth_required_flags_misconfiguration_when_production_has_no_password(monkeypatch):
    """production 인데 암호가 없으면 화면이 '암호 불필요'로 오해하면 안 된다 —
    /api/auth/required 가 misconfigured 플래그로 알려준다."""
    monkeypatch.setattr(get_settings(), "environment", "production")
    resp = client.get("/api/auth/required")
    assert resp.status_code == 200
    assert resp.json() == {"required": True, "misconfigured": True}


# 🟠 Important: POST /api/validate-key 는 유일하게 라우터 단위가 아니라 엔드포인트
# 단위 Depends 로 암호 게이트가 걸려 있다 — 리팩터 중 _auth 파라미터가 빠져도 잡아낼
# 테스트가 여태 없었다.


def test_validate_key_requires_password(monkeypatch):
    """암호 없이 POST /api/validate-key -> 401 (암호 사유)"""
    monkeypatch.setattr(get_settings(), "app_password", "right-pw")
    resp = client.post(
        "/api/validate-key",
        json={"provider": "openai", "api_key": "sk-test-dummy-not-real"},
    )
    assert resp.status_code == 401
    assert "접속 암호" in resp.json()["detail"]


# ── 수정 라운드 2 ─────────────────────────────────────────────────────────
# 🔴 Critical: 라운드 1 은 "한글 암호가 서버를 500 으로 죽이는" 문제를 고쳤지만,
# 더 근본적인 제약이 남아 있었다 — HTTP 커스텀 헤더 값은 규격상 ISO-8859-1 이라
# 한글 등 비-ASCII 문자는 X-App-Password 헤더로 애초에 왕복이 안 된다(실제
# 브라우저 fetch 도 TypeError 를 던진다). 그 결과 POST /api/auth/check(JSON
# 바디)에서는 로그인이 "성공"하지만, 그 뒤 모든 요청이 담는 헤더에서는 같은 값이
# 조용히 실패한다 — "성공했다가 조용히 망가지는" 최악의 실패 방식이다. 그래서
# 비-ASCII 암호는 401(틀림)이 아니라 400(쓸 수 없는 형식)으로 입력 시점에 명확히
# 거부하고, 운영자가 서버 쪽 APP_PASSWORD 자체를 비-ASCII 로 설정한 경우에도
# /api/auth/required 의 misconfigured 플래그로 알린다.


def test_auth_check_rejects_non_ascii_password_with_400(monkeypatch):
    """한글 암호는 401(틀림)이 아니라 400(쓸 수 없는 형식)이다.

    candidate(사용자가 입력한 값) 자체가 비-ASCII 면 맞고 틀리고를 따지기 전에
    거부해야 한다 — 설령 서버의 APP_PASSWORD 와 글자 그대로 같더라도, 로그인 이후
    그 값을 X-App-Password 헤더에 담을 방법이 없어 곧바로 조용히 막히기 때문이다."""
    monkeypatch.setattr(get_settings(), "app_password", "right-pw")
    resp = client.post("/api/auth/check", json={"password": "말씀자료2026"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == auth.NON_ASCII_PASSWORD_MESSAGE


def test_auth_required_flags_non_ascii_server_password_as_misconfigured(monkeypatch):
    """운영자가 한글 암호를 설정하면 아무도 로그인 못 한다. 화면이 알 수 있어야 한다.

    APP_PASSWORD 자체가 비-ASCII 면 그 값을 X-App-Password 헤더로 보낼 방법이
    없으므로, 사용자가 무엇을 입력해도 로그인 유지가 안 된다 — 사용자는 자기
    암호가 틀린 줄 알겠지만 실제로는 서버 설정 문제다. environment 는 건드리지
    않는다 — production 에 암호가 비어 있는 라운드 1 케이스와는 원인이 다른데도
    같은 misconfigured 신호로 알린다는 것을 보이기 위해서다."""
    monkeypatch.setattr(get_settings(), "app_password", "말씀자료2026")
    resp = client.get("/api/auth/required")
    assert resp.status_code == 200
    assert resp.json() == {"required": True, "misconfigured": True}
