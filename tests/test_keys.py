import pytest
from fastapi import HTTPException
from starlette.datastructures import Headers
from starlette.requests import Request

from policy_writer.common import keys


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
