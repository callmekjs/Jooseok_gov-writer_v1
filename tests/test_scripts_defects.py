"""scripts/_defects.py — Task 13 의 측정 도구가 실제로 결함을 잡는지.

이 검사들이 틀리면 보고서의 모든 숫자가 틀린다. 실제로 관측된 출력을 표본으로
넣어, 결함이 있는 글과 없는 글을 가르는지 확인한다.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import _defects  # noqa: E402

# docs/type-check.md 에 남아 있던 실제 gpt-4o-mini 이임사 출력의 앞부분.
# 이임을 가리키는 낱말이 하나도 없어 축사와 구분되지 않는다 — 이게 B1 결함이다.
REAL_BAD_FAREWELL = (
    "존경하는 청년 여러분, 그리고 공무원 여러분, 반갑습니다.\n\n"
    "오늘 「청년 주거지원 정책 설명회」를 맞이하여, 여러분과 함께 할 수 있게 되어 매우 기쁩니다.\n\n"
    "이 자리를 빛내 주신 모든 분께 감사드립니다."
)


def test_farewell_without_departure_words_is_flagged():
    assert _defects.reads_like_a_congratulation(REAL_BAD_FAREWELL)
    assert _defects.departure_markers(REAL_BAD_FAREWELL) == []


def test_farewell_with_departure_words_passes():
    text = REAL_BAD_FAREWELL + "\n\n지난 3년의 재임 기간을 돌아봅니다. 후임에게 소임을 넘깁니다."
    assert not _defects.reads_like_a_congratulation(text)
    assert set(_defects.departure_markers(text)) == {"재임", "후임", "소임"}


def test_ordinals_in_separate_paragraphs_are_not_lumped():
    text = "첫째, 월세를 넓힙니다.\n\n둘째, 공급을 늘립니다.\n\n셋째, 소통합니다."
    assert _defects.lumped_ordinal_paragraphs(text) == []
    assert _defects.ordinal_count(text) == 3


def test_ordinals_in_one_paragraph_are_lumped():
    text = "본론입니다. 첫째, 월세를 넓힙니다. 둘째, 공급을 늘립니다. 셋째, 소통합니다."
    assert len(_defects.lumped_ordinal_paragraphs(text)) == 1


def test_a_paragraph_with_one_ordinal_is_not_lumped():
    """문단마다 서수가 하나씩이면 정상이다 — 뭉친 것만 잡아야 한다."""
    text = "첫째, 월세를 넓힙니다. 부담을 줄이겠습니다.\n\n둘째, 공급을 늘립니다."
    assert _defects.lumped_ordinal_paragraphs(text) == []


def test_speaker_name_in_the_thanks_list_is_flagged():
    text = "존경하는 여러분.\n\n이 자리를 빛내 주신 국토교통부 장관 김민수님께 감사드립니다."
    assert _defects.speaker_named_in_body(text, "김민수", has_signature=False)


def test_first_person_draft_without_the_speaker_name_passes():
    text = "존경하는 여러분.\n\n이 자리를 빛내 주신 모든 분께 감사드립니다."
    assert not _defects.speaker_named_in_body(text, "김민수", has_signature=False)


def test_signature_line_is_not_counted_as_a_failure():
    """서면축사는 마지막 줄에 이름이 반드시 들어간다 — 그건 결함이 아니다."""
    text = "「행사」 개최를 축하합니다.\n\n감사합니다.\n\n2026년 9월 12일\n국토교통부 장관 김민수"
    assert not _defects.speaker_named_in_body(text, "김민수", has_signature=True)
    assert _defects.speaker_named_in_body(text, "김민수", has_signature=False)
