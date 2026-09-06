from fastapi import APIRouter, HTTPException

from policy_writer.db import drafts as db

router = APIRouter()


def _require_db() -> None:
    if not db.is_configured():
        raise HTTPException(503, "이력 기능이 설정되지 않았습니다 (Supabase 미설정).")


@router.get("")
async def list_all(limit: int = 20) -> dict:
    _require_db()
    return {"drafts": await db.list_drafts(limit)}


@router.get("/{draft_id}")
async def get_one(draft_id: str) -> dict:
    _require_db()
    row = await db.get_draft(draft_id)
    if not row:
        raise HTTPException(404, "해당 이력을 찾을 수 없습니다.")
    return row


@router.delete("/{draft_id}")
async def delete_one(draft_id: str) -> dict:
    _require_db()
    await db.delete_draft(draft_id)
    return {"ok": True}
