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
