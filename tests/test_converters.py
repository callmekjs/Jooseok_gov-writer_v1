import io
import zipfile
from xml.etree import ElementTree

from policy_writer.exporters.converters import split_paragraphs, to_hwpx_bytes, to_markdown


def test_splits_on_blank_lines():
    text = "첫 단락입니다.\n\n둘째 단락입니다.\n\n\n셋째 단락입니다."
    assert split_paragraphs(text) == ["첫 단락입니다.", "둘째 단락입니다.", "셋째 단락입니다."]


def test_joins_single_newlines_inside_a_paragraph():
    text = "존경하는 여러분,\n반갑습니다.\n\n다음 단락."
    assert split_paragraphs(text) == ["존경하는 여러분, 반갑습니다.", "다음 단락."]


def test_ignores_leading_and_trailing_whitespace():
    assert split_paragraphs("\n\n  본문  \n\n") == ["본문"]


def test_markdown_has_title_heading():
    md = to_markdown("청년 정책 축사", "본문입니다.")
    assert md.startswith("# 청년 정책 축사")
    assert "본문입니다." in md


# ── hwpx: 한글 프로그램에서 단락이 떨어져 보이는지 ─────────────────────────
# add_paragraph 호출 횟수를 세는 대신, 실제로 만들어진 hwpx(=zip) 안의
# section0.xml 을 열어 문단 순서를 읽는다. 구현을 그대로 옮겨 적으면 구현이
# 틀려도 테스트가 같이 틀리기 때문이다.
HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"


def _hwpx_paragraph_texts(data: bytes) -> list[str]:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        root = ElementTree.fromstring(z.read("Contents/section0.xml"))
    return ["".join(t.text or "" for t in p.iter(f"{HP}t")) for p in root.iter(f"{HP}p")]


def test_hwpx_separates_body_paragraphs_with_a_blank_line():
    data = to_hwpx_bytes("청년 정책 축사", "첫 단락입니다.\n\n둘째 단락입니다.\n\n셋째 단락입니다.")
    paras = _hwpx_paragraph_texts(data)
    start = paras.index("첫 단락입니다.")      # 제목·머리 문단은 건너뛰고 본문부터
    assert paras[start:] == [
        "첫 단락입니다.", "", "둘째 단락입니다.", "", "셋째 단락입니다."
    ]


def test_hwpx_keeps_the_blank_line_under_the_title():
    paras = _hwpx_paragraph_texts(to_hwpx_bytes("청년 정책 축사", "본문입니다."))
    i = paras.index("청년 정책 축사")
    assert paras[i + 1:i + 3] == ["", "본문입니다."]


def test_hwpx_leaves_no_trailing_blank_paragraph():
    """단락마다 뒤에 빈 줄을 붙이는 방식이면 파일 끝에 빈 문단이 남는다."""
    paras = _hwpx_paragraph_texts(to_hwpx_bytes("청년 정책 축사", "본문입니다."))
    assert paras[-1] == "본문입니다."
