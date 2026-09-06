"""PowerShell ConvertTo-Json 은 한글을 깨뜨린다. 이 스크립트로 시험한다."""
import json
import os
import sys

import httpx

API_BASE = os.environ.get("API_BASE", "http://localhost:8010")
PROVIDER = os.environ.get("TRY_PROVIDER", "openai")
MODEL = os.environ.get("TRY_MODEL", "gpt-5.6-sol")
KEY = os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")

if not KEY:
    sys.exit("환경변수 OPENAI_API_KEY 또는 ANTHROPIC_API_KEY 를 설정하세요.")

payload = {
    "input": {
        "event_name": "청년 주거지원 정책 설명회",
        "event_type": sys.argv[1] if len(sys.argv) > 1 else "축사",
        "event_date": "2026년 9월 12일",
        "event_location": "정부세종청사 대강당",
        "speaker_name": "김민수",
        "speaker_role": "장관",
        "speaker_organization": "국토교통부",
        "audience": "청년, 공무원, 전문가",
        "vip_list": ["○○시장", "△△협회장"],
        "target_chars": 1500,
        "key_messages": ["청년 월세 지원 확대", "공공임대 공급 물량 확대"],
        "quotes_or_anecdotes": ["작년 신청자 12만 명"],
        "avoid_phrases": ["만감이 교차"],
        "persona_block": "현장에서 답을 찾겠습니다",
    }
}
headers = {
    "X-LLM-Provider": PROVIDER,
    "X-LLM-Model": MODEL,
    "X-OpenAI-Key" if PROVIDER == "openai" else "X-Anthropic-Key": KEY,
}

res = httpx.post(
    f"{API_BASE}/api/speech/draft",
    json=payload, headers=headers, timeout=180.0,
)
print("HTTP", res.status_code)
data = res.json()
if res.status_code != 200:
    print(json.dumps(data, ensure_ascii=False, indent=2))
    sys.exit(1)

print(data["generated_text"])
print("─" * 50)
print("글자수:", data["char_count"], "/ 경고:", data["warnings"])
print("meta:", json.dumps(data["meta"], ensure_ascii=False))
