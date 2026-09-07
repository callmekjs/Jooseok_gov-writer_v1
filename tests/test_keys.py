import h11
import httpx
import pytest
from fastapi import HTTPException
from starlette.datastructures import Headers
from starlette.requests import Request

from policy_writer.common import keys
from policy_writer.config import get_settings


def _req(headers: dict) -> Request:
    raw = [(k.lower().encode(), v.encode()) for k, v in headers.items()]
    return Request({"type": "http", "headers": raw})


def test_norm_provider_accepts_known():
    assert keys.norm_provider("anthropic") == "anthropic"
    assert keys.norm_provider("  OpenAI ") == "openai"


def test_norm_provider_falls_back_to_openai():
    assert keys.norm_provider(None) == "openai"
    assert keys.norm_provider("gemini") == "openai"


def test_resolve_user_key_reads_correct_header():
    r = _req({"X-OpenAI-Key": "sk-abc", "X-Anthropic-Key": "sk-ant-xyz"})
    assert keys.resolve_user_key(r, "openai") == "sk-abc"
    assert keys.resolve_user_key(r, "anthropic") == "sk-ant-xyz"


def test_resolve_user_key_raises_401_when_missing():
    with pytest.raises(HTTPException) as e:
        keys.resolve_user_key(_req({}), "openai")
    assert e.value.status_code == 401
    assert "키" in e.value.detail


def test_resolve_user_key_falls_back_to_clean_server_key(monkeypatch):
    """헤더가 없고 서버 설정에 정상 형식의 키가 있으면 그 값을 그대로 돌려준다.
    지금까지 이 폴백 경로(서버 키가 '멀쩡한' 경우) 자체를 확인하는 테스트가 없었다 —
    아래의 '깨진 서버 키' 테스트들과 짝을 이루려면 '깨끗한 서버 키는 여전히 통과한다'는
    회귀 방지 확인이 먼저 있어야 한다."""
    monkeypatch.setattr(get_settings(), "openai_api_key", "sk-clean-server-key-123")
    assert keys.resolve_user_key(_req({}), "openai") == "sk-clean-server-key-123"


# ── 수정 (2026-09-07 컨트롤러 추가지시 §3) ──────────────────────────────────
# 🔴 Critical: resolve_user_key() 는 서버/헤더 키 값을 검증 없이 그대로 돌려줬다.
# 반환값은 곧장 llm/client.py 가 outbound HTTP 헤더(Authorization / x-api-key)를
# 만드는 데 쓰인다. 아래 첫 그룹(test_dirty_value_*)은 "고치기 전이라면 정말 500 이
# 났을 상황"이라는 것 자체를 증명한다 — call_llm()이 실제 네트워크 호출 없이도 이
# 값들이 outbound 헤더 계층에서 지금도 예외를 던진다는 것을, httpx·h11(둘 다
# call_llm 이 실제로 쓰는 라이브러리)의 공개 API 로 직접 확인한다. call_llm 은
# `except httpx.TimeoutException` 만 잡으므로(llm/client.py), 이 예외들은 잡히지
# 않고 그대로 튀어 사용자에게 맨 500 이 됐을 것이다.
#
# 값 4가지, 문제 지점이 서로 다르다:
#   - 개행·CR: httpx.Request() 생성 자체는 통과하지만, h11 이 실제 전송 시점에
#     "Illegal header value" 로 거부한다(개발 중 h11.Connection.send() 로 직접 확인).
#   - 트레일링 스페이스만(개행 없음): 인쇄 가능 ASCII 라 눈으로는 멀쩡해 보이지만,
#     h11 이 이것도 "Illegal header value" 로 거부한다 — is_safe_header_value 가
#     is_ascii_only 만으로는 못 잡고 앞뒤 공백을 별도로 확인하는 이유다.
#   - 비-ASCII(한글): h11 까지 갈 필요도 없이 httpx.Request() 생성 시점에 이미
#     UnicodeEncodeError.


def test_dirty_value_with_newline_breaks_h11_send():
    conn = h11.Connection(our_role=h11.CLIENT)
    with pytest.raises(h11.LocalProtocolError, match="Illegal header value"):
        conn.send(h11.Request(
            method="POST", target="/v1/chat/completions",
            headers=[(b"host", b"api.openai.com"), (b"authorization", b"Bearer sk-test\ndummy")],
        ))


def test_dirty_value_with_trailing_space_only_breaks_h11_send():
    """개행이 전혀 없어도(순수 트레일링 스페이스만) h11 은 거부한다 — is_ascii_only
    하나만으로는 이 값을 못 잡는 이유(스페이스 0x20 은 인쇄 가능 ASCII)를 보여준다."""
    conn = h11.Connection(our_role=h11.CLIENT)
    with pytest.raises(h11.LocalProtocolError, match="Illegal header value"):
        conn.send(h11.Request(
            method="POST", target="/v1/chat/completions",
            headers=[(b"host", b"api.openai.com"), (b"authorization", b"Bearer sk-test-dummy ")],
        ))


def test_dirty_value_with_non_ascii_breaks_httpx_request_construction():
    """한글 등 비-ASCII 는 h11 까지 갈 필요도 없다 — httpx.Request() 를 만드는
    순간(call_llm 이 실제 전송 전에 항상 거치는 단계) UnicodeEncodeError 로 죽는다."""
    with pytest.raises(UnicodeEncodeError):
        httpx.Request(
            "POST", "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": "Bearer sk-테스트더미"},
        )


# ── is_safe_header_value() 단위 테스트 — 순수 함수라 직접 검사한다 (auth.is_ascii_only
# ·auth.password_matches 와 같은 스타일). 값 앞에 노출된 실제 오탈자를 흉내내지만
# "sk-test-dummy"류 가짜 값만 쓴다 — G12 와 무관하게 테스트에도 진짜 키를 적지 않는다.


DIRTY_VALUES = [
    "sk-test-dummy\nafter-newline",
    "sk-test-dummy\r\nafter-crlf",
    "sk-test-dummy\tafter-tab",
    "sk-test-dummy-with-trailing-space ",
    " sk-test-dummy-with-leading-space",
    "sk-테스트더미",
]


@pytest.mark.parametrize("dirty", DIRTY_VALUES)
def test_is_safe_header_value_rejects_dirty(dirty):
    assert keys.is_safe_header_value(dirty) is False


def test_is_safe_header_value_accepts_clean():
    assert keys.is_safe_header_value("sk-abcDEF123-_.") is True


# ── resolve_user_key() — 서버 키가 깨진 경우: 503, 관리자를 향한 메시지 ──────────


@pytest.mark.parametrize("dirty", DIRTY_VALUES)
def test_resolve_user_key_rejects_dirty_server_key_with_503(monkeypatch, dirty):
    """서버에 저장된 키가 깨진 형식이면 500(맨 크래시)이 아니라 503 으로, 운영자를
    향한 메시지로 막는다 — 요청한 사람의 잘못이 아니라 서버 설정 문제이므로."""
    monkeypatch.setattr(get_settings(), "openai_api_key", dirty)
    with pytest.raises(HTTPException) as e:
        keys.resolve_user_key(_req({}), "openai")
    assert e.value.status_code == 503
    assert "관리자" in e.value.detail
    assert "OPENAI_API_KEY" in e.value.detail   # 운영자가 어떤 환경변수를 볼지 바로 안다
    assert dirty not in e.value.detail          # G12: 키 값 자체를 메시지에 담지 않는다


def test_resolve_user_key_dirty_server_key_message_names_anthropic_env_var(monkeypatch):
    """회사별로 다른 환경변수 이름을 메시지에 정확히 담는다 — openai 전용이 아니다."""
    monkeypatch.setattr(get_settings(), "anthropic_api_key", "sk-ant-dummy\n")
    with pytest.raises(HTTPException) as e:
        keys.resolve_user_key(_req({}), "anthropic")
    assert e.value.status_code == 503
    assert "ANTHROPIC_API_KEY" in e.value.detail


# ── resolve_user_key() — 헤더로 들어온 사용자 키가 깨진 경우: 401 ────────────────
# 트레일링/리딩 스페이스만 있는 값은 헤더 경로에서 제외한다 — resolve_user_key 의
# 첫 줄이 이미 .strip() 을 하므로 그 두 값은 여기 도달하기 전에 이미 깨끗해진다
# (그래서 실제로도 "깨진 값"이 아니게 된다). 이 두 값이 여전히 깨지는 경로는
# "서버 설정 키"(위 그룹) 뿐이다 — 서버 키는 어디서도 strip 되지 않기 때문이다.


HEADER_DIRTY_VALUES = [v for v in DIRTY_VALUES if v.strip() == v]


@pytest.mark.parametrize("dirty", HEADER_DIRTY_VALUES)
def test_resolve_user_key_rejects_dirty_header_key_with_401(dirty):
    """사용자가 헤더로 보낸 키가 깨진 형식이면 401 로 막는다 — 서버 설정 문제가
    아니라 사용자 자신이 보낸 값이 문제이므로 503 이 아니다."""
    with pytest.raises(HTTPException) as e:
        keys.resolve_user_key(_req({"X-OpenAI-Key": dirty}), "openai")
    assert e.value.status_code == 401
    assert dirty not in e.value.detail          # G12
