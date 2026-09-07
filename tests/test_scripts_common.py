"""scripts/_common.py — 시험용 스크립트 세 개가 쓰는 접속 설정.

🔴 이 파일을 테스트하는 이유는 포트 가드 때문이다. 8010·5173 은 이 PC 의 다른
프로젝트 전용 포트라, 스크립트가 실수로 거기에 붙으면 남의 서버를 건드린다.
스크립트는 `python scripts\\try_draft.py` 로 실행돼 sys.path[0] 이 scripts/ 가
되므로, 테스트도 같은 경로로 불러와 실제와 같은 방식으로 검사한다.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import _common  # noqa: E402


@pytest.mark.parametrize("url", [
    "http://localhost:8010",
    "http://127.0.0.1:8010/",
    "http://LOCALHOST:8010",          # 대소문자
    "http://[::1]:8010",              # IPv6 표기
    "http://0.0.0.0:5173",
    "https://example.test:5173",      # 호스트를 따지지 않는다 — 포트만 본다
])
def test_forbidden_ports_are_refused(monkeypatch, url):
    monkeypatch.setenv("API_BASE", url)
    with pytest.raises(SystemExit):
        _common.resolve_base_url("API_BASE")


@pytest.mark.parametrize("url", [
    "http://127.0.0.1:8011",
    "http://127.0.0.1:8099",
    "http://127.0.0.1:80100",   # 범위 밖 포트 — urlsplit().port 가 ValueError 를 낸다
    "http://127.0.0.1",         # 포트 없음
])
def test_other_ports_pass(monkeypatch, url):
    monkeypatch.setenv("API_BASE", url)
    assert _common.resolve_base_url("API_BASE") == url.rstrip("/")


def test_default_is_8011_when_env_is_unset(monkeypatch):
    monkeypatch.delenv("API_BASE", raising=False)
    assert _common.resolve_base_url("API_BASE") == "http://127.0.0.1:8011"


def test_password_header_is_sent_when_configured(monkeypatch):
    from policy_writer.config import get_settings
    monkeypatch.setattr(get_settings(), "app_password", "열려라참깨")
    assert _common.base_headers() == {"X-App-Password": "열려라참깨"}


def test_no_password_header_when_unset():
    # conftest 의 autouse fixture 가 app_password 를 비워 둔다
    assert _common.base_headers() == {}
