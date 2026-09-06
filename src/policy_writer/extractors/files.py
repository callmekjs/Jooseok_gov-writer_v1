import io
import zipfile
from xml.etree import ElementTree

MAX_CHARS = 5000
UNSUPPORTED_PREFIX = "(미지원)"


def is_unsupported(text: str) -> bool:
    """추출 실패 안내 문자열인지. 이게 프롬프트에 실려 들어가면 안 된다."""
    return text.startswith(UNSUPPORTED_PREFIX)


def _decode(data: bytes) -> str:
    for enc in ("utf-8", "cp949", "euc-kr"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _from_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    pages = reader.pages[:20]
    return "\n".join((p.extract_text() or "") for p in pages)


def _from_docx(data: bytes) -> str:
    import docx

    doc = docx.Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs)


def _from_hwpx(data: bytes) -> str:
    """ZIP 을 열어 Contents/section*.xml 의 <hp:t> 노드를 모은다."""
    texts: list[str] = []
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = [n for n in z.namelist() if n.startswith("Contents/section") and n.endswith(".xml")]
        for n in sorted(names):
            root = ElementTree.fromstring(z.read(n))
            for el in root.iter():
                if el.tag.endswith("}t") and el.text:
                    texts.append(el.text)
    return " ".join(texts)


def extract_text(filename: str, data: bytes) -> str:
    """실패해도 예외를 던지지 않고 안내 문자열을 돌려준다."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "hwp":
        return f"{UNSUPPORTED_PREFIX} .hwp 는 읽을 수 없습니다. HWPX 로 변환 후 업로드 부탁드립니다."
    if ext in {"doc", "ppt", "pptx"}:
        return f"{UNSUPPORTED_PREFIX} .{ext} 는 현재 텍스트 추출을 지원하지 않습니다."

    try:
        if ext == "txt":
            text = _decode(data)
        elif ext == "pdf":
            text = _from_pdf(data)
        elif ext == "docx":
            text = _from_docx(data)
        elif ext == "hwpx":
            text = _from_hwpx(data)
        else:
            return f"{UNSUPPORTED_PREFIX} .{ext or '알 수 없는 형식'} 은 지원하지 않습니다."
    except Exception as e:
        return f"{UNSUPPORTED_PREFIX} 파일을 읽는 중 오류가 발생했습니다: {e}"

    return text.strip()[:MAX_CHARS]
