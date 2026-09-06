import httpx

from policy_writer.config import get_settings

TABLE = "drafts"
TIMEOUT = 15.0


def is_configured() -> bool:
    s = get_settings()
    return bool(s.supabase_url and s.supabase_service_role_key)


def _base() -> tuple[str, dict]:
    s = get_settings()
    url = f"{s.supabase_url.rstrip('/')}/rest/v1/{TABLE}"
    headers = {
        "apikey": s.supabase_service_role_key,
        "Authorization": f"Bearer {s.supabase_service_role_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    return url, headers


async def create_draft(*, event_type: str, title: str, form_data: dict,
                       generated_text: str, llm_meta: dict) -> str:
    url, headers = _base()
    row = {
        "event_type": event_type,
        "title": title,
        "form_data": form_data,
        "generated_text": generated_text,
        "llm_meta": llm_meta,
    }
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        res = await c.post(url, headers=headers, json=row)
    res.raise_for_status()
    return res.json()[0]["id"]


async def list_drafts(limit: int = 20) -> list[dict]:
    url, headers = _base()
    params = {"order": "created_at.desc", "limit": str(limit),
              "select": "id,event_type,title,llm_meta,created_at"}
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        res = await c.get(url, headers=headers, params=params)
    res.raise_for_status()
    return res.json()


async def get_draft(draft_id: str) -> dict | None:
    url, headers = _base()
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        res = await c.get(url, headers=headers, params={"id": f"eq.{draft_id}"})
    res.raise_for_status()
    rows = res.json()
    return rows[0] if rows else None


async def delete_draft(draft_id: str) -> None:
    url, headers = _base()
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        res = await c.delete(url, headers=headers, params={"id": f"eq.{draft_id}"})
    res.raise_for_status()
