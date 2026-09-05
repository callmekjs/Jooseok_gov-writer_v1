# ─────────────────────────────────────────────────────────────
# 확인일: 2026-09-05
# ⚠️ 모델 id 와 가격은 바뀐다. 이 파일이 가장 빨리 낡는 곳이다.
#    수정할 때마다 위 날짜를 갱신할 것.
#
# 검증 상태:
#   OpenAI  경제형/최상위 → [실측] 직접 호출해 200 확인
#   OpenAI  표준형        → [조사] 문서상 존재, 미호출
#   Anthropic 전부        → 키가 없어 미호출
#   Anthropic 최상위      → 비워 뒀다 (아래 주석 참고)
# ─────────────────────────────────────────────────────────────
from fastapi import HTTPException

MODELS: dict[str, list[dict]] = {
    "openai": [
        {"id": "gpt-4o-mini",   "tier": "경제형", "temperature": True,
         "in": 0.15, "out": 0.60},
        {"id": "gpt-5.6-terra", "tier": "표준형", "temperature": False,
         "in": 2.00, "out": 12.00},
        {"id": "gpt-5.6-sol",   "tier": "최상위", "temperature": False,
         "in": 4.00, "out": 20.00},
    ],
    "anthropic": [
        {"id": "claude-haiku-4-5",           "tier": "경제형", "temperature": True,
         "in": 1.00, "out": 5.00},
        {"id": "claude-sonnet-4-5-20250929", "tier": "표준형", "temperature": True,
         "in": 3.00, "out": 15.00},
        # 최상위 없음 — Anthropic 키가 없어 검증 못 했다.
        # 키가 생기면 후보를 한 번 호출해 200 을 확인한 뒤 이 줄을 추가한다.
    ],
}

# ⚠️ 이 DEFAULTS 는 "헤더에 X-LLM-Model 이 아예 없을 때 서버가 쓰는 값"이다.
#    화면이 처음 보여주는 등급(localStorage 초기값)과는 다른 개념이다.
DEFAULTS: dict[str, str] = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-sonnet-4-5-20250929",
}

DEFAULT_PROVIDER = "openai"   # ★ 원본 기본값은 "gemini" 였다 (G4)


def resolve(provider: str, model: str | None) -> dict:
    """허용목록에서 찾는다. 없으면 400."""
    table = MODELS.get(provider)
    if not table:
        raise HTTPException(400, f"지원하지 않는 회사: {provider}")
    if not model:
        model = DEFAULTS[provider]
    for m in table:
        if m["id"] == model:
            return m
    raise HTTPException(400, f"{provider}에서 지원하지 않는 모델: {model}")
