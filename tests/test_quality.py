from policy_writer.common.quality import check_output


def test_no_warning_when_length_is_fine():
    assert check_output("가" * 1400, 1500) == []


def test_warns_when_empty():
    w = check_output("   ", 1500)
    assert len(w) == 1
    assert "비어" in w[0]


def test_warns_when_too_short():
    w = check_output("가" * 700, 1500)
    assert len(w) == 1
    assert "700" in w[0]
