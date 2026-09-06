import pytest

from policy_writer.config import get_settings


@pytest.fixture(autouse=True)
def _clean_server_settings(monkeypatch):
    """모든 테스트를 로컬 .env 의 실제 값과 무관하게 만든다.

    `get_settings()`는 `@lru_cache` 싱글턴이라 프로세스가 뜰 때 실제 `.env`를 한 번
    읽어 캐시해 둔다. 이 리포의 `.env`에는 개발/실측용 진짜 OPENAI_API_KEY·
    ANTHROPIC_API_KEY·APP_PASSWORD 값이 들어 있으므로, 손대지 않으면 pytest 가 그
    값을 그대로 물려받는다. 기존 테스트들(test_keys.py·test_speech_api.py 등)은
    전부 "서버에 키도 암호도 없다"는 전제로 짜여 있으므로, 매 테스트 시작 전에
    이 세 값을 강제로 비운다. 접속 암호 자체를 확인하는 테스트(test_auth.py)는
    이 fixture 위에 monkeypatch 로 필요한 값만 다시 켠다."""
    settings = get_settings()
    monkeypatch.setattr(settings, "app_password", "")
    monkeypatch.setattr(settings, "openai_api_key", "")
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    yield
