from fastapi import APIRouter, Header, Request
from pydantic import BaseModel

from policy_writer.common.keys import norm_provider, resolve_user_key
from policy_writer.common.quality import check_output
from policy_writer.llm import catalog, cost
from policy_writer.llm.client import call_llm
from policy_writer.prompts.builder import SpeechInput, build_speech_prompt

router = APIRouter()


class DraftIn(BaseModel):
    input: SpeechInput
    reference_texts: list[str] = []
    max_tokens: int = 4000
    temperature: float = 0.7


@router.post("/draft")
async def draft(
    payload: DraftIn,
    request: Request,
    x_llm_provider: str = Header(default=catalog.DEFAULT_PROVIDER),   # G4
    x_llm_model: str | None = Header(default=None),
) -> dict:
    provider = norm_provider(x_llm_provider)
    api_key = resolve_user_key(request, provider)          # 없으면 401
    model_meta = catalog.resolve(provider, x_llm_model)    # 허용목록 밖이면 400

    system_prompt, user_prompt = build_speech_prompt(
        payload.input, contexts=payload.reference_texts
    )
    text, meta = await call_llm(
        provider=provider,
        model_meta=model_meta,
        api_key=api_key,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=payload.max_tokens,
        temperature=payload.temperature,
    )

    meta["cost_won"] = cost.won_for_usage(
        model_meta, meta["input_tokens"], meta["output_tokens"]
    )

    return {
        "generated_text": text,
        "char_count": len(text.strip()),
        "draft_id": None,                # Task 10 에서 채운다
        "warnings": check_output(text, payload.input.target_chars),
        "save_warning": None,            # Task 10 에서 채운다
        "meta": meta,
    }
