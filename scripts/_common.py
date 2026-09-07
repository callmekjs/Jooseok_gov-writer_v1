"""시험용 스크립트 세 개가 함께 쓰는 접속 설정.

compare_models.py 가 먼저 이 형태로 고쳐졌고, try_draft.py · try_all_types.py
· measure_defects.py 도 똑같은 게 필요했다. 같은 8줄을 네 번 복사하는 대신
여기 한 곳에 둔다 (G9). 특히 아래 포트 가드는 이 PC 에서 안전 문제라
복사본이 여럿 돌아다니면 안 된다.

왜 이 파일이 필요한가 — 원본 PLAN 의 스크립트를 그대로 돌리면 두 번 실패한다:

1. 기본 주소가 http://localhost:8010 이었다.
   🔴 8010 과 5173 은 이 PC 의 다른 프로젝트 전용 포트다. 쓰지도, 죽이지도
   않는다. 기본값을 127.0.0.1:8011 로 바꾸고, 환경변수로 넘어온 주소도
   아래 가드로 막는다.
2. X-App-Password 헤더가 없었다. 접속암호 게이트(common/auth.py)가 나중에
   추가돼서 헤더 없이는 전부 401 이다.

API 키는 헤더로 보내지 않는다 — 서버가 이미 .env 에 OPENAI_API_KEY /
ANTHROPIC_API_KEY 를 갖고 있어서, 헤더가 없으면 common/keys.resolve_user_key()
가 서버 키로 자동 대체한다. 스크립트라 G7(설정 직접 읽기 금지) 대상이 아니다.
"""
import os
from urllib.parse import urlsplit

from policy_writer.config import get_settings

DEFAULT_BASE_URL = "http://127.0.0.1:8011"

# 포트 번호로만 판단한다 — 문자열 부분일치는 대소문자(LOCALHOST)·표기 차이
# ([::1], 0.0.0.0, 127.1)에 뚫리고 80100 같은 무관한 포트에 오탐도 난다.
# 8010/5173 금지는 예외 없는 규칙이라 호스트를 따지지 않고 포트만 막는다.
FORBIDDEN_PORTS = {8010, 5173}


def check_port(base_url: str) -> None:
    """8010·5173 이면 SystemExit. 그 외에는 조용히 통과한다."""
    try:
        port = urlsplit(base_url).port   # 범위 밖 포트(예: 80100)는 여기서 ValueError
    except ValueError:
        port = None                      # 8010/5173 일 수 없으니 이 가드에서는 통과시킨다
    if port in FORBIDDEN_PORTS:
        raise SystemExit(
            f"8010/5173 은 다른 프로젝트 전용 포트입니다 — 이 스크립트에서 쓸 수 없습니다: {base_url}"
        )


def resolve_base_url(env_var: str) -> str:
    """환경변수로 주소를 바꿀 수 있게 하되, 금지 포트는 여기서 막는다."""
    base_url = os.environ.get(env_var, DEFAULT_BASE_URL).rstrip("/")
    check_port(base_url)
    return base_url


def base_headers() -> dict[str, str]:
    """접속암호가 .env 에 있으면 X-App-Password 로 넣는다. 없으면 빈 dict."""
    password = get_settings().app_password
    return {"X-App-Password": password} if password else {}


# ── 시험 입력 ────────────────────────────────────────────────────────────
# try_all_types.py 와 measure_defects.py 가 같은 입력을 써야 "8종 회귀 확인"과
# "N 회 반복 측정"의 숫자를 나란히 비교할 수 있다. 그래서 여기 한 벌만 둔다 (G9).
TYPES = ["축사", "기념사", "신년사", "격려사", "환영사", "개회사", "이임사", "서면축사"]
TARGET_CHARS = {"격려사": 900, "환영사": 600}      # 짧은 유형은 목표를 낮춘다
DEFAULT_TARGET_CHARS = 1500


def sample_input(event_type: str) -> dict:
    """시험용 행사 정보 한 벌. SpeechInput 의 필드 이름 그대로다."""
    return {
        "event_name": "청년 주거지원 정책 설명회",
        "event_type": event_type,
        "event_date": "2026년 9월 12일",
        "event_location": "정부세종청사 대강당",
        "speaker_name": "김민수",
        "speaker_role": "장관",
        "speaker_organization": "국토교통부",
        "audience": "청년, 공무원",
        "target_chars": TARGET_CHARS.get(event_type, DEFAULT_TARGET_CHARS),
        "key_messages": ["청년 월세 지원 확대"],
        "avoid_phrases": ["만감이 교차"],
    }
