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


# ── B3: 발화자가 감사 대상이 되는가 ────────────────────────────────────────
# 이 검사는 한 번 틀렸다가 고쳤다. 처음엔 "이름이 본문에 나오면 실패"로 셌는데,
# 실제 정상 출력 6건 중 3건이 "국토교통부 장관 김민수입니다" 라는 자기소개를
# 갖고 있어서 전부 거짓 실패가 났다. 아래 두 표본이 그 경계를 지킨다.
REAL_SELF_INTRODUCTION = (
    "존경하는 청년 여러분, 그리고 공무원과 전문가 여러분, 반갑습니다.\n"
    "국토교통부 장관 김민수입니다.\n\n"
    "이 자리를 빛내 주신 ○○시장님과 △△협회장님께 깊이 감사드립니다."
)
REAL_SPEAKER_IN_THANKS = (
    "존경하는 청년 여러분, 반갑습니다.\n\n"
    "이 자리를 빛내 주신 국토교통부 장관 김민수님을 비롯한 모든 분께 감사드립니다."
)


def test_self_introduction_is_not_a_failure():
    assert _defects.thanked_as_guest(REAL_SELF_INTRODUCTION, ["김민수"]) == []
    assert not _defects.honorific_after(REAL_SELF_INTRODUCTION, "김민수")


def test_speaker_in_the_thanks_sentence_is_flagged():
    assert _defects.thanked_as_guest(REAL_SPEAKER_IN_THANKS, ["김민수"]) == ["김민수"]
    assert _defects.honorific_after(REAL_SPEAKER_IN_THANKS, "김민수")


def test_thanks_in_a_different_sentence_is_not_a_failure():
    """감사 문장과 자기소개가 다른 문장이면 결함이 아니다 — 문장 단위로 본다."""
    text = "국토교통부 장관 김민수입니다. 오늘 함께해 주신 여러분께 감사드립니다."
    assert _defects.thanked_as_guest(text, ["김민수"]) == []


def test_bugunsu_does_not_match_gunsu():
    """행사계획서 경로에서 부군수는 정당한 감사 대상이다. 군수만 잡아야 한다."""
    fine = "오늘 함께해 주신 부군수님과 군의회 의장님께 감사드립니다."
    bad = "오늘 이 자리를 빛내 주신 군수님께 깊이 감사드립니다."
    assert _defects.thanked_as_guest(fine, [r"(?<!부)군수"]) == []
    assert _defects.thanked_as_guest(bad, [r"(?<!부)군수"]) == [r"(?<!부)군수"]
