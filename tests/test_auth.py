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
