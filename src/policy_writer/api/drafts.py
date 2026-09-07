import uuid

from fastapi import APIRouter, HTTPException

from policy_writer.db import drafts as db

router = APIRouter()


def _require_db() -> None:
    if not db.is_configured():
        raise HTTPException(503, "이력 기능이 설정되지 않았습니다 (Supabase 미설정).")


def _require_valid_uuid(draft_id: str) -> str:
    """draft_id 를 PostgREST 에 넘기기 전에 검증하고 표준형으로 정규화한다.

    uuid.UUID() 는 PostgreSQL 의 uuid_in 보다 관대하다 — `urn:uuid:` 접두사가
    붙어 있어도 파싱에 성공한다. 검증만 하고 원본 문자열을 그대로 넘기면,
    Python 은 받아들이지만 PostgREST 는 거부하는 값(예: `urn:uuid:...`)이 그대로
    새어나가 22P02 → raise_for_status() → 아무도 못 잡음 → FastAPI 가 500 으로
    감싼다 — 서버 잘못이 아닌데 서버 잘못처럼 보인다. 그래서 검증에 성공한
    값은 str(uuid.UUID(...)) 로 정규화한 표준형(하이픈 포함 36자)을 돌려주고,
    호출자가 원본이 아니라 그 정규화된 값을 DB 계층에 넘긴다."""
    try:
        return str(uuid.UUID(draft_id))
    except ValueError:
        raise HTTPException(400, "잘못된 문서 ID 형식입니다.")


@router.get("")
async def list_all(limit: int = 20) -> dict:
    _require_db()
    return {"drafts": await db.list_drafts(limit)}


@router.get("/{draft_id}")
async def get_one(draft_id: str) -> dict:
    _require_db()
    row = await db.get_draft(_require_valid_uuid(draft_id))
    if not row:
        raise HTTPException(404, "해당 이력을 찾을 수 없습니다.")
    return row


@router.delete("/{draft_id}")
async def delete_one(draft_id: str) -> dict:
    _require_db()
    await db.delete_draft(_require_valid_uuid(draft_id))
    return {"ok": True}
