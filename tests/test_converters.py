from policy_writer.exporters.converters import split_paragraphs, to_markdown


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
