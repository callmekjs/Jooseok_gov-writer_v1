import json

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Request, UploadFile
from pydantic import BaseModel, ValidationError

from policy_writer.common.auth import require_app_password
from policy_writer.common.keys import norm_provider, resolve_user_key
from policy_writer.common.quality import check_output
from policy_writer.extractors.files import extract_text, is_unsupported
from policy_writer.llm import catalog, cost
from policy_writer.llm.client import call_llm
from policy_writer.prompts.builder import SpeechInput, build_speech_prompt

# 이 라우터의 세 엔드포인트는 전부 AI 를 호출해 돈을 쓴다 — 라우터 단위로 접속 암호를 검사한다 (G9).
router = APIRouter(dependencies=[Depends(require_app_password)])


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

    from policy_writer.db import drafts as drafts_db

    draft_id, save_warning = None, None
    if drafts_db.is_configured():
        try:
            draft_id = await drafts_db.create_draft(
                event_type=payload.input.event_type,
                title=payload.input.event_name,
                form_data=payload.input.model_dump(),
                generated_text=text,
                llm_meta=meta,                      # ★ 모델·비용·소요시간
            )
        except Exception as e:
            save_warning = f"이력 저장에 실패했습니다: {e}"   # 삼키지 않는다

    return {
        "generated_text": text,
        "char_count": len(text.strip()),
        "draft_id": draft_id,
        "warnings": check_output(text, payload.input.target_chars),
        "save_warning": save_warning,
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
    try:
        payload = DraftIn(input=SpeechInput(**json.loads(input_json)))
    except json.JSONDecodeError:
        raise HTTPException(400, "input_json 을 읽을 수 없습니다. 올바른 JSON 형식인지 확인해 주세요.")
    except ValidationError as e:
        first = e.errors()[0]
        field = ".".join(str(x) for x in first.get("loc", ())) or "입력값"
        raise HTTPException(400, f"입력값이 올바르지 않습니다 ({field}): {first.get('msg', '')}")
    except TypeError:
        raise HTTPException(400, "input_json 은 객체(JSON object) 여야 합니다.")
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

    name = event_name.strip() or (plan_file.filename or "").rsplit(".", 1)[0].strip()
    if not name:
        name = "행사"          # 진짜 행사명은 L4 참고자료에서 모델이 읽는다
    payload = DraftIn(input=SpeechInput(event_name=name, target_chars=1500))
    result = await _run_draft(request, payload, contexts, x_llm_provider, x_llm_model)
    result["warnings"] = file_warnings + result["warnings"]
    return result
