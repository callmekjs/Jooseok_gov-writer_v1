import re


def split_paragraphs(text: str) -> list[str]:
    """AI 출력은 빈 줄로 단락이 나뉜다. 단락 안의 단일 줄바꿈은 공백으로 합친다."""
    chunks = re.split(r"\n\s*\n+", text.strip())
    out = []
    for c in chunks:
        joined = re.sub(r"\s*\n\s*", " ", c).strip()
        if joined:
            out.append(joined)
    return out


def to_markdown(title: str, text: str) -> str:
    body = "\n\n".join(split_paragraphs(text))
    return f"# {title}\n\n{body}\n"


def to_hwpx_bytes(title: str, text: str) -> bytes:
    """python-hwpx 는 add_paragraph 와 save_to_path 만 쓴다.
    표·이미지·도형은 시도하면 파일이 깨진다."""
    import tempfile
    from pathlib import Path

    from hwpx import HwpxDocument

    doc = HwpxDocument.new()
    doc.add_paragraph(title)
    doc.add_paragraph("")
    for p in split_paragraphs(text):
        doc.add_paragraph(p)

    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "out.hwpx"
        doc.save_to_path(str(path))
        return path.read_bytes()
