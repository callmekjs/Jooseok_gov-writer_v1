import time

import httpx
from fastapi import HTTPException

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


def _build_openai(model_meta: dict, api_key: str, system_prompt: str,
                  user_prompt: str, max_tokens: int, temperature: float):
    body = {
        "model": model_meta["id"],
        "max_completion_tokens": max_tokens,          # ⚠️ max_tokens 아님 (G6)
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    if model_meta["temperature"]:                      # G5
        body["temperature"] = temperature
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    return OPENAI_URL, headers, body


def _build_anthropic(model_meta: dict, api_key: str, system_prompt: str,
                     user_prompt: str, max_tokens: int, temperature: float):
    body = {
        "model": model_meta["id"],
        "max_tokens": max_tokens,                      # Anthropic 은 max_tokens
        "system": system_prompt,                       # 최상위 필드
        "messages": [{"role": "user", "content": user_prompt}],
    }
    if model_meta["temperature"]:
        body["temperature"] = temperature
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    return ANTHROPIC_URL, headers, body


BUILDERS = {"openai": _build_openai, "anthropic": _build_anthropic}


def _extract(provider: str, data: dict) -> tuple[str, int, int]:
    if provider == "openai":
        text = data["choices"][0]["message"]["content"]
        u = data.get("usage", {})
        return text, u.get("prompt_tokens", 0), u.get("completion_tokens", 0)
    text = "".join(b.get("text", "") for b in data.get("content", []))
    u = data.get("usage", {})
    return text, u.get("input_tokens", 0), u.get("output_tokens", 0)


async def call_llm(
    *,
    provider: str,
    model_meta: dict,
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4000,
    temperature: float = 0.7,
    timeout: float = 120.0,
) -> tuple[str, dict]:
    url, headers, body = BUILDERS[provider](
        model_meta, api_key, system_prompt, user_prompt, max_tokens, temperature
    )

    started = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            res = await client.post(url, headers=headers, json=body)
    except httpx.TimeoutException:
        raise HTTPException(504, "시간이 초과되었습니다. 분량을 줄이거나 다시 시도해 주세요.")
    elapsed_ms = int((time.monotonic() - started) * 1000)

    if res.status_code in (401, 403):
        raise HTTPException(401, "인증 실패 — API 키를 다시 확인해 주세요.")
    if res.status_code >= 400:
        raise HTTPException(502, f"AI 서버 오류 ({res.status_code}). 잠시 후 다시 시도해 주세요.")

    text, in_tok, out_tok = _extract(provider, res.json())
    meta = {
        "provider": provider,
        "model": model_meta["id"],
        "elapsed_ms": elapsed_ms,
        "input_tokens": in_tok,
        "output_tokens": out_tok,
    }
    return text, meta
