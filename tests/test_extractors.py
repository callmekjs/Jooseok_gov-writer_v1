from policy_writer.extractors.files import MAX_CHARS, extract_text, is_unsupported


def test_utf8_text():
    assert "한글" in extract_text("a.txt", "한글 본문".encode("utf-8"))


def test_cp949_fallback():
    assert "한글" in extract_text("a.txt", "한글 본문".encode("cp949"))


def test_truncates_to_max_chars():
    assert len(extract_text("a.txt", ("가" * 9999).encode("utf-8"))) <= MAX_CHARS


def test_hwp_returns_guidance_not_exception():
    out = extract_text("a.hwp", b"\x00\x01")
    assert "HWPX" in out
    assert is_unsupported(out)


def test_pptx_returns_guidance():
    out = extract_text("a.pptx", b"\x00\x01")
    assert is_unsupported(out)


def test_normal_text_is_not_flagged_unsupported():
    assert is_unsupported("존경하는 여러분") is False
