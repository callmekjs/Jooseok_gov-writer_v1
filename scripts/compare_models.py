"""같은 축사를 모델별로 돌려 비교표를 만든다. 원본 gov-writer 에 없는 데이터다.

🔴 컨트롤러 추가지시(2026-09-07) 반영판 — PLAN 의 원본 스크립트를 그대로 쓰면
접속암호 게이트가 나중에 추가된 탓에 전부 401 로 실패한다. 달라진 점:

  - base URL 기본값을 8011 로 바꿈. 8010·5173 은 이 PC 의 다른 프로젝트 전용
    포트라 절대 쓰면 안 된다 (죽이는 것도 금지). 필요하면 COMPARE_BASE_URL
    환경변수로 다른 포트를 가리킬 수 있다 — 단 8010/5173 은 아래에서 막는다.
  - X-App-Password 헤더를 추가했다. 로컬 .env 의 APP_PASSWORD 를
    get_settings() 로 읽는다 (스크립트라 G7 대상이 아니다).
  - 키는 헤더로 보내지 않는다 — 서버가 이미 .env 에 OPENAI_API_KEY /
    ANTHROPIC_API_KEY 를 갖고 있어서, 헤더가 없으면 keys.resolve_user_key()
    가 서버 키로 자동 대체한다 (헤더 전달 / 서버 폴백 중 더 간단한 후자만 씀).
  - 응답 필드는 meta 다 (llm_meta 는 이력 저장 응답 쪽 이름이라 다르다).

콘솔에 모델별 input_tokens/output_tokens 를 함께 찍는다 — llm/cost.py 의
TYPICAL_INPUT_TOKENS/TYPICAL_OUTPUT_TOKENS 상수를 실측치로 보정하는 근거 자료다.
"""
import os
import time
from pathlib import Path

import httpx

from policy_writer.config import get_settings

BASE_URL = os.environ.get("COMPARE_BASE_URL", "http://127.0.0.1:8011").rstrip("/")
_FORBIDDEN = ("://localhost:8010", "://127.0.0.1:8010", "://localhost:5173", "://127.0.0.1:5173")
if any(bad in BASE_URL for bad in _FORBIDDEN):
    raise SystemExit(f"8010/5173 은 다른 프로젝트 전용 포트입니다 — 이 스크립트에서 쓸 수 없습니다: {BASE_URL}")

TARGET = 1500
PAYLOAD = {"input": {
    "event_name": "청년 주거지원 정책 설명회",
    "event_type": "축사",
    "event_date": "2026년 9월 12일",
    "event_location": "정부세종청사 대강당",
    "speaker_name": "김민수", "speaker_role": "장관",
    "speaker_organization": "국토교통부",
    "audience": "청년, 공무원, 전문가",
    "vip_list": ["○○시장", "△△협회장"],
    "target_chars": TARGET,
    "key_messages": ["청년 월세 지원 확대", "공공임대 공급 물량 확대"],
    "quotes_or_anecdotes": ["작년 신청자 12만 명"],
    "avoid_phrases": ["만감이 교차"],
    "persona_block": "현장에서 답을 찾겠습니다",
}}

APP_PASSWORD = get_settings().app_password
BASE_HEADERS = {"X-App-Password": APP_PASSWORD} if APP_PASSWORD else {}

CATALOG = httpx.get(f"{BASE_URL}/api/models", timeout=10).json()

rows = ["| 회사 | 등급 | 모델 | 글자수 | 소요 | 1건당 | 6단 | 분량준수 |",
        "|---|---|---|---:|---:|---:|:---:|---:|"]
token_log: list[tuple[str, str, int, int]] = []   # (provider, model_id, input_tokens, output_tokens)

for provider, models in CATALOG.items():
    for m in models:
        headers = {**BASE_HEADERS, "X-LLM-Provider": provider, "X-LLM-Model": m["id"]}
        started = time.time()
        try:
            res = httpx.post(f"{BASE_URL}/api/speech/draft",
                             json=PAYLOAD, headers=headers, timeout=180.0)
            res.raise_for_status()
        except httpx.HTTPStatusError as e:
            detail = e.response.text[:150]
            rows.append(f"| {provider} | {m['tier']} | `{m['id']}` | ❌ HTTP {e.response.status_code} | — | — | — | — |")
            print(f"{m['id']}: FAIL HTTP {e.response.status_code} — {detail}")
            continue
        except Exception as e:
            rows.append(f"| {provider} | {m['tier']} | `{m['id']}` | ❌ {str(e)[:30]} | — | — | — | — |")
            print(f"{m['id']}: FAIL {e}")
            continue
        d = res.json()
        chars = d["char_count"]
        secs = time.time() - started
        meta = d["meta"]
        token_log.append((provider, m["id"], meta["input_tokens"], meta["output_tokens"]))
        rows.append(
            f"| {provider} | {m['tier']} | `{m['id']}` | {chars:,} | {secs:.0f}초 | "
            f"{meta['cost_won']}원 | ✅ | {round(chars / TARGET * 100)}% |"
        )
        print(f"{m['id']}: {chars}자 / {secs:.0f}초 / in={meta['input_tokens']} out={meta['output_tokens']} / {meta['cost_won']}원")
        Path("docs/samples").mkdir(parents=True, exist_ok=True)
        Path(f"docs/samples/{m['id']}.md").write_text(d["generated_text"], encoding="utf-8")

out = Path("docs/model-comparison.md")
out.write_text(
    f"# 모델 비교 실측\n\n행사: 청년 주거지원 정책 설명회 · 유형: 축사 · 목표 {TARGET}자\n\n"
    + "\n".join(rows) + "\n", encoding="utf-8")
print(f"\n→ {out}")

if token_log:
    ins = [t[2] for t in token_log]
    outs = [t[3] for t in token_log]
    print(f"\ninput_tokens 범위: {min(ins)}~{max(ins)} / output_tokens 범위: {min(outs)}~{max(outs)}")
    for provider, mid, i, o in token_log:
        print(f"  {mid}: in={i} out={o}")
