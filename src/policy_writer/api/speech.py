import json

from fastapi import APIRouter, File, Form, Header, HTTPException, Request, UploadFile
from pydantic import BaseModel

from policy_writer.common.keys import norm_provider, resolve_user_key
from policy_writer.common.quality import check_output
from policy_writer.extractors.files import extract_text, is_unsupported
from policy_writer.llm import catalog, cost
from policy_writer.llm.client import call_llm
from policy_writer.prompts.builder import SpeechInput, build_speech_prompt

router = APIRouter()


class DraftIn(BaseModel):
    input: SpeechInput
    reference_texts: list[str] = []
    max_tokens: int = 4000
    temperature: float = 0.7


async def _run_draft(request, payload: DraftIn, contexts: list[str],
                     provider_header: str, model_header: str | None) -> dict:
    provider = norm_provider(provider_header)
    api_key = resolve_user_key(request, provider)
    model_meta = catalog.resolve(provider, model_header)

    system_prompt, user_prompt = build_speech_prompt(payload.input, contexts=contexts)
    text, meta = await call_llm(
        provider=provider, model_meta=model_meta, api_key=api_key,
        system_prompt=system_prompt, user_prompt=user_prompt,
        max_tokens=payload.max_tokens, temperature=payload.temperature,
    )
    meta["cost_won"] = cost.won_for_usage(model_meta, meta["input_tokens"], meta["output_tokens"])
    return {
        "generated_text": text,
        "char_count": len(text.strip()),
        "draft_id": None,
        "warnings": check_output(text, payload.input.target_chars),
        "save_warning": None,
        "meta": meta,
    }


@router.post("/draft")
async def draft(
    payload: DraftIn,
    request: Request,
    x_llm_provider: str = Header(default=catalog.DEFAULT_PROVIDER),   # G4
    x_llm_model: str | None = Header(default=None),
) -> dict:
    return await _run_draft(request, payload, payload.reference_texts, x_llm_provider, x_llm_model)


async def _read_contexts(files: list[UploadFile]) -> tuple[list[str], list[str]]:
    """(프롬프트에 넣을 텍스트, 사용자에게 보여줄 경고)"""
    texts, warnings = [], []
    for f in files:
        if not f or not f.filename:
            continue
        text = extract_text(f.filename, await f.read())
        if is_unsupported(text):
            warnings.append(f"{f.filename}: {text}")   # ★ 프롬프트에는 안 넣는다
        elif text:
            texts.append(text)
    return texts, warnings


@router.post("/draft-with-docs")
async def draft_with_docs(
    request: Request,
    input_json: str = Form(...),
    plan_file: UploadFile | None = File(default=None),
    reference_files: list[UploadFile] = File(default=[]),
    x_llm_provider: str = Header(default=catalog.DEFAULT_PROVIDER),
    x_llm_model: str | None = Header(default=None),
) -> dict:
    payload = DraftIn(input=SpeechInput(**json.loads(input_json)))
    uploads = ([plan_file] if plan_file else []) + list(reference_files)
    contexts, file_warnings = await _read_contexts(uploads)

    result = await _run_draft(request, payload, contexts, x_llm_provider, x_llm_model)
    result["warnings"] = file_warnings + result["warnings"]
    return result


@router.post("/auto-draft")
async def auto_draft(
    request: Request,
    plan_file: UploadFile = File(...),
    event_name: str = Form(default=""),
    x_llm_provider: str = Header(default=catalog.DEFAULT_PROVIDER),
    x_llm_model: str | None = Header(default=None),
) -> dict:
    contexts, file_warnings = await _read_contexts([plan_file])
    if not contexts:
        raise HTTPException(400, file_warnings[0] if file_warnings else "파일에서 글자를 뽑지 못했습니다.")

    name = event_name.strip() or plan_file.filename.rsplit(".", 1)[0]
    payload = DraftIn(input=SpeechInput(event_name=name, target_chars=1500))
    result = await _run_draft(request, payload, contexts, x_llm_provider, x_llm_model)
    result["warnings"] = file_warnings + result["warnings"]
    return result
