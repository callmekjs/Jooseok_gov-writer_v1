import pytest
from fastapi import HTTPException

from policy_writer.llm import catalog


def test_resolve_returns_model_meta():
    m = catalog.resolve("openai", "gpt-4o-mini")
    assert m["id"] == "gpt-4o-mini"
    assert m["tier"] == "인턴"
    assert m["temperature"] is True


def test_resolve_uses_default_when_model_missing():
    m = catalog.resolve("openai", None)
    assert m["id"] == catalog.DEFAULTS["openai"]


def test_resolve_rejects_unknown_model():
    with pytest.raises(HTTPException) as e:
        catalog.resolve("openai", "gpt-6-astra")
    assert e.value.status_code == 400


def test_resolve_rejects_unknown_provider():
    with pytest.raises(HTTPException) as e:
        catalog.resolve("gemini", None)
    assert e.value.status_code == 400


def test_default_provider_is_openai():
    assert catalog.DEFAULT_PROVIDER == "openai"


def test_top_tier_models_do_not_accept_temperature():
    assert catalog.resolve("openai", "gpt-5.6-sol")["temperature"] is False
    assert catalog.resolve("openai", "gpt-5.6-terra")["temperature"] is False


def test_anthropic_has_three_verified_tiers():
    tiers = [m["tier"] for m in catalog.MODELS["anthropic"]]
    assert tiers == ["인턴", "비서", "선임비서"]
