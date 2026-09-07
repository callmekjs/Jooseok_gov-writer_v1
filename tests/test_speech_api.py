"""잘못된 입력이 500 이 아니라 400(또는 401)으로 끝나는지 확인한다.

AI 호출은 하지 않는다 — 아래 세 시나리오 모두 LLM 을 부르기 전(입력 파싱/검증
단계 또는 키 검사 단계)에서 요청이 끝난다. 핵심 어서션은 "500 이 아니다"이다.
정확한 코드가 400 이든 401 이든 상관없다.
"""

from fastapi.testclient import TestClient

from policy_writer.server import app

client = TestClient(app)


def test_draft_with_docs_rejects_broken_json_with_400():
    """input_json 이 JSON 조차 아니면(평문) 400 이어야 한다."""
    resp = client.post("/api/speech/draft-with-docs", data={"input_json": "{{{"})
    assert resp.status_code != 500
    assert resp.status_code == 400
    assert "input_json" in resp.json()["detail"]


def test_draft_with_docs_rejects_missing_event_name_with_400():
    """event_name 이 없으면(JSON 은 정상) pydantic ValidationError 가 그대로
    새지 않고 400 으로 변환되어야 한다."""
    resp = client.post(
        "/api/speech/draft-with-docs",
        data={"input_json": '{"event_type":"축사"}'},
    )
    assert resp.status_code != 500
    assert resp.status_code == 400
    assert "event_name" in resp.json()["detail"]


def test_auto_draft_survives_a_filename_with_no_stem():
    """파일명이 확장자만 있으면(예: ".txt") 기존 코드는
    `event_name=""`을 만들어 SpeechInput 검증 오류가 그대로 새어 500 이 났다.
    API 키 헤더를 일부러 넣지 않았으므로(AI 호출 없이 확인하기 위해),
    고친 뒤에는 이름 계산 단계를 무사히 통과해 그 다음 단계인 키 검사에서
    401 로 끝난다 — 어느 쪽이든 500 만 아니면 통과.
    """
    resp = client.post(
        "/api/speech/auto-draft",
        files={"plan_file": (".txt", "행사 축사 순서 군수".encode("utf-8"), "text/plain")},
    )
    assert resp.status_code != 500


# ── Task 11-C: /api/speech/draft 는 pydantic 기본 422 가 아니라 400 이어야 한다 ──
# draft-with-docs·auto-draft 는 SpeechInput 을 라우트 안에서 직접 만들어 ValidationError
# 를 손으로 잡지만(위 테스트들), /api/speech/draft 는 `payload: DraftIn` 시그니처로
# FastAPI 가 자동으로 검증한다 — 실패하면 손으로 잡을 기회 없이 FastAPI 가 곧장
# RequestValidationError(422) 를 던진다. PLAN 의 API 계약은 400 이므로
# server.py 의 전역 핸들러(validation_exception_handler)가 이를 바꿔야 한다.
# 이 라우트는 접속 암호 게이트 뒤에 있지만, conftest.py 의 autouse fixture 가 매
# 테스트마다 app_password 를 비워 두므로(+ 기본 environment 는 "development") 별도
# 헤더 없이도 게이트를 통과한다 — test_auth.py 의 VALID_DRAFT_BODY 케이스들과 동일한
# 전제다.


def test_draft_rejects_empty_event_name_with_400_not_422():
    """event_name 이 빈 문자열이면(Field min_length=1 위반) 422 가 아니라 400,
    본문은 프론트(api.ts 의 detail.detail)가 읽는 {"detail": "<str>"} 모양이어야 한다."""
    resp = client.post("/api/speech/draft", json={"input": {"event_name": ""}})
    assert resp.status_code == 400
    assert resp.json() == {"detail": "행사명은 필수입니다."}


def test_draft_rejects_missing_event_name_with_400_not_422():
    """event_name 자체가 없어도(필드 누락) 마찬가지로 400 이어야 한다."""
    resp = client.post("/api/speech/draft", json={"input": {}})
    assert resp.status_code == 400
    assert resp.json() == {"detail": "행사명은 필수입니다."}


def test_draft_other_field_validation_error_is_400_with_generic_message():
    """event_name 이 아닌 다른 필드의 검증 오류는 pydantic 영문 원문을 노출하지
    않는 일반 한글 문구로 400 을 낸다."""
    resp = client.post(
        "/api/speech/draft",
        json={"input": {"event_name": "정상 행사명", "target_chars": "숫자아님"}},
    )
    assert resp.status_code == 400
    assert resp.json() == {"detail": "입력값을 확인해 주세요."}
