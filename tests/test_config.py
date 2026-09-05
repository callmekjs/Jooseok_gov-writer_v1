from policy_writer.config import Settings


def test_local_llm_keys_returns_filled_keys_in_development():
    s = Settings(environment="development", openai_api_key="sk-test", anthropic_api_key="")
    assert s.local_llm_keys == {"openai": "sk-test"}


def test_local_llm_keys_is_empty_in_production():
    s = Settings(environment="production", openai_api_key="sk-test", anthropic_api_key="sk-ant-test")
    assert s.local_llm_keys == {}
