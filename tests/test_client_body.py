import httpx
import pytest
import respx

from policy_writer.llm import catalog
from policy_writer.llm.client import call_llm

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

OPENAI_OK = {
    "choices": [{"message": {"content": "본문"}}],
    "usage": {"prompt_tokens": 10, "completion_tokens": 5},
}
ANTHROPIC_OK = {
    "content": [{"text": "본문"}],
    "usage": {"input_tokens": 10, "output_tokens": 5},
}


@respx.mock
async def test_openai_omits_temperature_for_top_tier():
    route = respx.post(OPENAI_URL).mock(return_value=httpx.Response(200, json=OPENAI_OK))
    await call_llm(
        provider="openai",
        model_meta=catalog.resolve("openai", "gpt-5.6-sol"),
        api_key="sk-x", system_prompt="S", user_prompt="U",
    )
    body = route.calls[0].request.content.decode()
    assert "temperature" not in body
    assert "max_completion_tokens" in body   # 함정 4번
    assert "max_tokens" not in body


@respx.mock
async def test_openai_includes_temperature_for_economy_tier():
    route = respx.post(OPENAI_URL).mock(return_value=httpx.Response(200, json=OPENAI_OK))
    await call_llm(
        provider="openai",
        model_meta=catalog.resolve("openai", "gpt-4o-mini"),
        api_key="sk-x", system_prompt="S", user_prompt="U",
    )
    assert "temperature" in route.calls[0].request.content.decode()


@respx.mock
async def test_anthropic_puts_system_at_top_level():
    route = respx.post(ANTHROPIC_URL).mock(return_value=httpx.Response(200, json=ANTHROPIC_OK))
    await call_llm(
        provider="anthropic",
        model_meta=catalog.resolve("anthropic", "claude-haiku-4-5"),
        api_key="sk-ant-x", system_prompt="SYSTEM_MARK", user_prompt="U",
    )
    payload = route.calls[0].request.content.decode()
    assert '"system"' in payload
    assert '"max_tokens"' in payload


@respx.mock
async def test_returns_text_and_normalized_meta():
    respx.post(OPENAI_URL).mock(return_value=httpx.Response(200, json=OPENAI_OK))
    text, meta = await call_llm(
        provider="openai",
        model_meta=catalog.resolve("openai", "gpt-4o-mini"),
        api_key="sk-x", system_prompt="S", user_prompt="U",
    )
    assert text == "본문"
    assert meta["input_tokens"] == 10
    assert meta["output_tokens"] == 5
    assert meta["model"] == "gpt-4o-mini"
    assert meta["elapsed_ms"] >= 0


@respx.mock
async def test_upstream_401_becomes_401_with_korean_message():
    from fastapi import HTTPException
    respx.post(OPENAI_URL).mock(return_value=httpx.Response(401, json={"error": {"message": "bad key"}}))
    with pytest.raises(HTTPException) as e:
        await call_llm(
            provider="openai",
            model_meta=catalog.resolve("openai", "gpt-4o-mini"),
            api_key="sk-bad", system_prompt="S", user_prompt="U",
        )
    assert e.value.status_code == 401
    assert "인증 실패" in e.value.detail
