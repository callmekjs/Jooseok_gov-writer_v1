"""8종을 한 번씩 돌려 결과를 docs/type-check.md 에 쌓는다.

접속 주소·포트 가드·접속암호 헤더는 _common.py 에 모여 있다 (G9).
API_BASE 환경변수로 주소를, OUT 환경변수로 저장 파일을 바꿀 수 있다.
Task 13 의 수정 전/후 비교는 OUT 을 바꿔 두 파일을 나란히 남기는 식으로 쓴다.
"""
import os
import time
from pathlib import Path

import httpx

from _common import TYPES, base_headers, resolve_base_url, sample_input

API_BASE = resolve_base_url("API_BASE")
PROVIDER = os.environ.get("TRY_PROVIDER", "openai")
MODEL = os.environ.get("TRY_MODEL", "gpt-5.6-sol")

# 키는 헤더로 보내지 않는다 — 서버가 .env 의 키로 대체한다 (_common.py 설명 참고).
headers = {**base_headers(), "X-LLM-Provider": PROVIDER, "X-LLM-Model": MODEL}

out = Path(os.environ.get("OUT", "docs/type-check.md"))
out.parent.mkdir(exist_ok=True)
lines = [f"# 유형 8종 검증 ({MODEL})\n"]

for t in TYPES:
    # 입력은 _common.sample_input 한 곳에만 있다 — measure_defects.py 의 반복
    # 측정과 같은 입력이어야 두 결과를 나란히 비교할 수 있다 (G9).
    fields = sample_input(t)
    target = fields["target_chars"]
    payload = {"input": fields}
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
