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
    """한글 암호로도 맞으면 통과하고 틀리면 401. 500 이 나면 안 된다.

    "맞는 암호" 쪽은 헤더가 아니라 /api/auth/check(JSON 바디)로 확인한다 — ASGI
    서버는 헤더 바이트를 항상 latin-1 로 디코드하므로(Starlette datastructures.
    Headers, RFC 계열 관례) 다중 바이트 UTF-8 헤더 값은 애초에 원래 문자로 왕복되지
    않는다(실제 브라우저의 fetch Headers 도 라틴-1 밖의 문자는 담지 못해 이 경로 자체를
    쓸 수 없다). JSON 바디는 이 제약이 없고, /api/auth/check 도 같은 password_matches
    를 쓰므로(G9) 고친 비교 로직 자체는 그대로 검증된다.
    "틀린 암호" 쪽은 헤더 경로(/api/speech/draft)로 확인한다 — 원래 버그는 candidate
    가 무엇이든(흔한 ASCII 오타여도) expected 하나만 비-ASCII 면 즉시 TypeError 였다는
    것이 핵심이라, 가장 흔한 헤더 경로에서 그 부분이 고쳐졌는지를 함께 본다."""
    monkeypatch.setattr(get_settings(), "app_password", "말씀자료2026")

    # 맞는 암호 -> 통과 (500 도 401 도 아님)
    resp = client.post("/api/auth/check", json={"password": "말씀자료2026"})
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}

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
