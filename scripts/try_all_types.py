"""8종을 한 번씩 돌려 결과를 docs/type-check.md 에 쌓는다."""
import os
import sys
import time
from pathlib import Path

import httpx

TYPES = ["축사", "기념사", "신년사", "격려사", "환영사", "개회사", "이임사", "서면축사"]
TARGET = {"격려사": 900, "환영사": 600}      # 짧은 유형은 목표를 낮춘다

API_BASE = os.environ.get("API_BASE", "http://localhost:8010")
PROVIDER = os.environ.get("TRY_PROVIDER", "openai")
MODEL = os.environ.get("TRY_MODEL", "gpt-5.6-sol")
KEY = os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
if not KEY:
    sys.exit("환경변수에 키를 설정하세요.")

headers = {
    "X-LLM-Provider": PROVIDER,
    "X-LLM-Model": MODEL,
    "X-OpenAI-Key" if PROVIDER == "openai" else "X-Anthropic-Key": KEY,
}

out = Path("docs/type-check.md")
out.parent.mkdir(exist_ok=True)
lines = [f"# 유형 8종 검증 ({MODEL})\n"]

for t in TYPES:
    target = TARGET.get(t, 1500)
    payload = {"input": {
        "event_name": "청년 주거지원 정책 설명회",
        "event_type": t,
        "event_date": "2026년 9월 12일",
        "event_location": "정부세종청사 대강당",
        "speaker_name": "김민수", "speaker_role": "장관",
        "speaker_organization": "국토교통부",
        "audience": "청년, 공무원",
        "target_chars": target,
        "key_messages": ["청년 월세 지원 확대"],
        "avoid_phrases": ["만감이 교차"],
    }}
    started = time.time()
    res = httpx.post(f"{API_BASE}/api/speech/draft",
                     json=payload, headers=headers, timeout=180.0)
    if res.status_code != 200:
        lines.append(f"\n## {t}\n\n❌ HTTP {res.status_code} — {res.text[:200]}\n")
        print(f"{t}: FAIL {res.status_code}")
        continue
    d = res.json()
    text = d["generated_text"]
    lines.append(
        f"\n## {t}\n\n"
        f"- 목표 {target}자 / 실제 {d['char_count']}자 "
        f"({round(d['char_count'] / target * 100)}%)\n"
        f"- 소요 {time.time() - started:.1f}초 · {d['meta']['cost_won']}원\n"
        f"- 금지어 '만감이 교차' 포함: {'❌ 있음' if '만감이 교차' in text else '✅ 없음'}\n\n"
        f"```\n{text}\n```\n"
    )
    print(f"{t}: {d['char_count']}/{target}자")

out.write_text("\n".join(lines), encoding="utf-8")
print(f"\n→ {out}")
