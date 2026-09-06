from urllib.parse import quote

from fastapi import APIRouter, Response
from pydantic import BaseModel

from policy_writer.exporters.converters import to_hwpx_bytes, to_markdown

router = APIRouter()


class DownloadIn(BaseModel):
    title: str = "말씀자료"
    generated_text: str


def _disposition(filename: str) -> dict:
    # RFC 5987 — filename="..." 로 하면 한글이 깨진다
    return {"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"}


@router.post("/speech/md")
def download_md(payload: DownloadIn) -> Response:
    body = to_markdown(payload.title, payload.generated_text)
    return Response(
        content=body.encode("utf-8"),
        media_type="text/markdown; charset=utf-8",
        headers=_disposition(f"{payload.title}.md"),
    )


@router.post("/speech/hwpx")
def download_hwpx(payload: DownloadIn) -> Response:
    return Response(
        content=to_hwpx_bytes(payload.title, payload.generated_text),
        media_type="application/vnd.hancom.hwpx",
        headers=_disposition(f"{payload.title}.hwpx"),
    )
