import uuid

from fastapi import APIRouter, HTTPException

from policy_writer.db import drafts as db

router = APIRouter()


def _require_db() -> None:
    if not db.is_configured():
        raise HTTPException(503, "이력 기능이 설정되지 않았습니다 (Supabase 미설정).")


def _require_valid_uuid(draft_id: str) -> None:
    """draft_id 를 PostgREST 에 그대로 넘기기 전에 형식을 검증한다.
    uuid 가 아니면 PostgREST 가 22P02 로 400 을 주고 raise_for_status() 가 그대로
    던져 아무도 잡지 못한 채 FastAPI 가 500 으로 감싼다 — 서버 잘못이 아닌데
    서버 잘못처럼 보인다. 여기서 먼저 걸러 400 으로 끝낸다."""
    try:
        uuid.UUID(draft_id)
    except ValueError:
        raise HTTPException(400, "잘못된 문서 ID 형식입니다.")


@router.get("")
async def list_all(limit: int = 20) -> dict:
    _require_db()
    return {"drafts": await db.list_drafts(limit)}


@router.get("/{draft_id}")
async def get_one(draft_id: str) -> dict:
    _require_db()
    _require_valid_uuid(draft_id)
    row = await db.get_draft(draft_id)
    if not row:
        raise HTTPException(404, "해당 이력을 찾을 수 없습니다.")
    return row


@router.delete("/{draft_id}")
async def delete_one(draft_id: str) -> dict:
    _require_db()
    _require_valid_uuid(draft_id)
    await db.delete_draft(draft_id)
    return {"ok": True}
