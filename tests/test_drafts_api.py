"""Task 11-D: 잘못된 draft_id(uuid 아님)가 500 이 아니라 400 으로 끝나는지 확인한다.

get_one·delete_one 이 draft_id 를 검증 없이 그대로 PostgREST 에 넘기면, uuid 가
아닌 값에 대해 PostgREST 가 22P02(잘못된 입력 형식) 로 400 을 주고, 그 응답에
res.raise_for_status() 를 호출하는 db.drafts 쪽 예외가 아무도 잡지 못한 채 새어
FastAPI 가 500 으로 감싼다 — 서버 잘못이 아닌데 서버 잘못처럼 보인다.
_require_valid_uuid() 가 PostgREST 에 보내기 전에 먼저 걸러야 한다.

Supabase 는 실제로 호출하지 않는다 — _require_db() 를 통과시키기 위한 테스트만
supabase_url·supabase_service_role_key 에 가짜 값을 넣어 두고, uuid 검증에서
곧바로 끝나 실제 HTTP 호출까지 가지 않는 것을 이용한다(느리거나 네트워크에
좌우되는 테스트가 되지 않는다).

_require_db() 가 uuid 검증보다 먼저 실행되는 기존 순서는 이 작업에서 바꾸지
않는다 — 그래서 Supabase 미설정 상태에서는 uuid 형식과 무관하게 503 이 먼저
나온다는 것도 함께 확인해 둔다(이 리포의 로컬 .env 에는 실제 Supabase 값이
있으므로, 두 테스트 모두 값을 명시적으로 monkeypatch 해서 로컬 .env 내용과
무관하게 만든다 — conftest.py 의 autouse fixture 는 app_password·LLM 키만
비우고 supabase 값은 건드리지 않는다)."""

from fastapi.testclient import TestClient

from policy_writer.config import get_settings
from policy_writer.server import app

client = TestClient(app)


def _configure_supabase(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "supabase_url", "https://example.supabase.co")
    monkeypatch.setattr(settings, "supabase_service_role_key", "dummy-service-role-key")


def test_get_one_invalid_uuid_is_400_not_500(monkeypatch):
    _configure_supabase(monkeypatch)
    resp = client.get("/api/drafts/not-a-uuid")
    assert resp.status_code == 400
    assert resp.json() == {"detail": "잘못된 문서 ID 형식입니다."}


def test_delete_one_invalid_uuid_is_400_not_500(monkeypatch):
    _configure_supabase(monkeypatch)
    resp = client.delete("/api/drafts/not-a-uuid")
    assert resp.status_code == 400
    assert resp.json() == {"detail": "잘못된 문서 ID 형식입니다."}


def test_invalid_uuid_without_supabase_configured_is_503_not_400(monkeypatch):
    """Supabase 미설정이면 uuid 형식과 무관하게 _require_db() 의 503 이 먼저 나온다
    — 이 작업이 그 우선순위를 바꾸지 않았음을 확인한다."""
    settings = get_settings()
    monkeypatch.setattr(settings, "supabase_url", "")
    monkeypatch.setattr(settings, "supabase_service_role_key", "")
    resp = client.get("/api/drafts/not-a-uuid")
    assert resp.status_code == 503
