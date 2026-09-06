# ─────────────────────────────────────────────────────────────
# 확인일: 2026-09-05
# ⚠️ 모델 id 와 가격은 바뀐다. 이 파일이 가장 빨리 낡는 곳이다.
#    수정할 때마다 위 날짜를 갱신할 것.
#
# 표기 규칙
#   [실측] 이 저장소의 call_llm() 으로 직접 호출해 200 을 받아 봤다
#   [조사] 공급사 문서·모델 목록으로만 확인했다. 호출해 보지 않았다
#
# 모델 검증 상태
#   OpenAI    인턴      gpt-4o-mini                 [실측] 200
#   OpenAI    비서      gpt-5.6-terra               [조사] GET /v1/models 에 존재. 호출 미확인
#   OpenAI    선임비서  gpt-5.6-sol                 [실측] 200
#   Anthropic 인턴      claude-haiku-4-5            [실측] 200
#   Anthropic 비서      claude-sonnet-4-5-20250929  [실측] 200
#   Anthropic 선임비서  claude-opus-4-5-20251101    [실측] 200 (temperature 포함/제외 양쪽)
#
# 가격(in/out)은 여섯 개 전부 [조사] 다 — 공급사 문서 값이며 청구서로 대조하지 않았다.
# 따라서 화면에 보이는 "1건당 N원"은 추정치다.
# ─────────────────────────────────────────────────────────────
from fastapi import HTTPException

MODELS: dict[str, list[dict]] = {
    "openai": [
        {"id": "gpt-4o-mini",   "tier": "인턴", "temperature": True,
         "in": 0.15, "out": 0.60},
        {"id": "gpt-5.6-terra", "tier": "비서", "temperature": False,
         "in": 2.00, "out": 12.00},
        {"id": "gpt-5.6-sol",   "tier": "선임비서", "temperature": False,
         "in": 4.00, "out": 20.00},
    ],
    "anthropic": [
        {"id": "claude-haiku-4-5",           "tier": "인턴", "temperature": True,
         "in": 1.00, "out": 5.00},
        {"id": "claude-sonnet-4-5-20250929", "tier": "비서", "temperature": True,
         "in": 3.00, "out": 15.00},
        {"id": "claude-opus-4-5-20251101",   "tier": "선임비서", "temperature": True,
         "in": 5.00, "out": 25.00},   # [실측] 200 확인 (2026-09-05). 가격은 [조사] — 미검증
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
