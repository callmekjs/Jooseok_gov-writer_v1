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
비우고 supabase 값은 건드리지 않는다).

--- 리뷰 Finding 1 (재발방지) ---
위 가드는 uuid.UUID() 로 "검증만" 하고 원본 문자열을 그대로 db 계층에 넘겼다.
uuid.UUID() 는 PostgreSQL 의 uuid_in 보다 관대해서 `urn:uuid:` 접두사가 붙은
문자열도 파싱에 성공한다 — 그래서 `/api/drafts/urn:uuid:<정상uuid>` 는 가드를
그대로 통과해 원본("urn:uuid:...")이 PostgREST 로 나가고, Postgres 가 22P02 로
거부하면서 다시 500 이 샌다(narrowed, but not eliminated). 아래 테스트들은
PostgREST 를 respx 로 흉내내어 "가드를 통과한 값이 실제로 정규화된 표준형인지"
를 확인한다 — db.get_draft/db.delete_draft 가 받는 draft_id 자체(=PostgREST 에
보내는 `id=eq.<값>` 쿼리 파라미터)를 검사한다."""

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from policy_writer.config import get_settings
from policy_writer.server import app

client = TestClient(app)
# raise_server_exceptions=False: 고친 전 코드에서 uncaught HTTPStatusError 가
# 그대로 파이썬 예외로 테스트를 터뜨리지 않고, 실사용자가 실제로 받는 500
# 응답 그대로(status_code) 관찰할 수 있게 한다.
no_raise_client = TestClient(app, raise_server_exceptions=False)

CANONICAL_UUID = "12345678-1234-5678-1234-567812345678"
URN_UUID = f"urn:uuid:{CANONICAL_UUID}"
BRACED_UUID = f"{{{CANONICAL_UUID}}}"
NO_HYPHEN_UUID = CANONICAL_UUID.replace("-", "")

DRAFTS_URL = "https://example.supabase.co/rest/v1/drafts"


def _postgrest_uuid_response(request: httpx.Request) -> httpx.Response:
    """실제 PostgREST/Postgres 의 uuid_in 을 흉내낸다: 표준형(하이픈 포함 36자,
    소문자)만 성공(200)으로 받아들이고, 그 외 표현(예: `urn:uuid:` 접두사가
    그대로 남아 있는 값)은 22P02 로 거부(400)한다 — 정규화가 실제로 일어났는지
    "PostgREST 에 보낸 쿼리 파라미터"로 직접 확인하기 위한 가짜 서버다."""
    sent = request.url.params.get("id", "")
    if sent == f"eq.{CANONICAL_UUID}":
        return httpx.Response(200, json=[{"id": CANONICAL_UUID, "title": "t"}])
    return httpx.Response(
        400,
        json={"code": "22P02", "message": f'invalid input syntax for type uuid: "{sent}"'},
    )


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


# ── Finding 1 회귀 테스트 ──────────────────────────────────────────────
# uuid.UUID() 가 받아들이지만 Postgres 의 uuid_in 은 거부하는 `urn:uuid:` 접두사가
# 확인된 실패 사례다: 정규화 없이 그대로 넘기면(고친 전) PostgREST 가 400 을 주고
# raise_for_status() 가 그대로 던져 500 이 샌다. 고친 뒤에는 str(uuid.UUID(...))
# 로 정규화된 표준형이 PostgREST 로 나가 200 이 된다.

@respx.mock
def test_get_one_urn_uuid_prefix_is_normalized_before_reaching_postgrest(monkeypatch):
    _configure_supabase(monkeypatch)
    route = respx.get(DRAFTS_URL).mock(side_effect=_postgrest_uuid_response)

    resp = no_raise_client.get(f"/api/drafts/{URN_UUID}")

    assert resp.status_code == 200, resp.text
    assert route.calls.last.request.url.params["id"] == f"eq.{CANONICAL_UUID}"


@respx.mock
def test_delete_one_urn_uuid_prefix_is_normalized_before_reaching_postgrest(monkeypatch):
    _configure_supabase(monkeypatch)
    route = respx.delete(DRAFTS_URL).mock(side_effect=_postgrest_uuid_response)

    resp = no_raise_client.delete(f"/api/drafts/{URN_UUID}")

    assert resp.status_code == 200, resp.text
    assert resp.json() == {"ok": True}
    assert route.calls.last.request.url.params["id"] == f"eq.{CANONICAL_UUID}"


@pytest.mark.parametrize("alt_form", [BRACED_UUID, NO_HYPHEN_UUID])
@respx.mock
def test_get_one_accepts_alternate_uuid_forms_and_still_reaches_db(monkeypatch, alt_form):
    """중괄호로 감싼 형태와 하이픈 없는 32자 형태는 Postgres 의 uuid_in 도 실제로
    받아들인다 — 우리 가드가 이런 값을 400 으로 걷어차면 과잉 차단이다. 표준형
    으로 정규화되어 DB 계층까지 정상 도달하는지만 확인한다(400 이 아니어야 함)."""
    _configure_supabase(monkeypatch)
    route = respx.get(DRAFTS_URL).mock(side_effect=_postgrest_uuid_response)

    resp = no_raise_client.get(f"/api/drafts/{alt_form}")

    assert resp.status_code == 200, resp.text
    assert route.calls.last.request.url.params["id"] == f"eq.{CANONICAL_UUID}"


# ── 재검토 Fix A (2026-09-07) ────────────────────────────────────────────
# 🔴 Important: 고치기 전에는 이 router(api/drafts.py)에 Depends 가 전혀 없었다 —
# speech_router 는 라우터 단위로 require_app_password 를 걸어 두면서 이 라우터만
# 빠뜨려서, APP_PASSWORD 가 설정된 배포에서도 X-App-Password 헤더 없이 GET
# /api/drafts 를 부르면 실제 행사명·날짜·장소가 담긴 이력이 그대로 200 으로
# 나갔다(컨트롤러가 배포 환경에서 직접 재현해 확인). 아래 첫 테스트는 이
# 재발을 막는다 — Supabase 설정 여부와 무관하게, 암호가 설정된 상태에서 헤더가
# 없으면 (구 코드라면 도달했을 _require_db()/PostgREST 호출보다 먼저) 401 이
# 나야 한다. 두 번째 테스트는 올바른 헤더를 보내면 게이트 때문에 막히지
# 않고 실제로 이력이 돌아온다는 것까지 확인한다(단순히 "401 이 아니다"가
# 아니라 200 + 실제 데이터로 증명한다).


def test_list_drafts_requires_app_password_when_set(monkeypatch):
    """헤더 없이 보내면 (Supabase 를 설정하지 않아도) 401 — require_app_password 가
    _require_db() 보다 먼저 실행되는 라우터 단위 Depends 이기 때문이다."""
    monkeypatch.setattr(get_settings(), "app_password", "right-pw")
    resp = client.get("/api/drafts")
    assert resp.status_code == 401
    assert "접속 암호" in resp.json()["detail"]


def test_get_one_requires_app_password_when_set(monkeypatch):
    """상세 조회(HistoryPage.tsx 가 문서를 열 때 부르는 경로)도 같은 라우터 단위
    게이트를 그대로 받는다."""
    monkeypatch.setattr(get_settings(), "app_password", "right-pw")
    resp = client.get(f"/api/drafts/{CANONICAL_UUID}")
    assert resp.status_code == 401
    assert "접속 암호" in resp.json()["detail"]


@respx.mock
def test_list_drafts_with_correct_password_still_succeeds(monkeypatch):
    """올바른 X-App-Password 헤더를 보내면 게이트가 막지 않고 실제 이력이 돌아온다
    — frontend/src/lib/api.ts 의 getJson() 이 이미 모든 호출에 이 헤더를 붙이므로
    (HistoryPage.tsx 가 목록·상세 조회 모두 getJson 을 씀), 이 게이트를 추가해도
    화면은 그대로 동작한다는 전제를 실제로 증명한다."""
    _configure_supabase(monkeypatch)
    monkeypatch.setattr(get_settings(), "app_password", "right-pw")
    respx.get(DRAFTS_URL).mock(
        return_value=httpx.Response(
            200,
            json=[{"id": CANONICAL_UUID, "event_type": "축사", "title": "테스트 행사",
                   "llm_meta": {}, "created_at": "2026-09-07T00:00:00Z"}],
        )
    )
    resp = client.get("/api/drafts", headers={"X-App-Password": "right-pw"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["drafts"][0]["title"] == "테스트 행사"
