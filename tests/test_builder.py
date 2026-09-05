import pytest
from pydantic import ValidationError

from policy_writer.prompts.builder import SpeechInput, build_speech_prompt


def _base(**kw) -> SpeechInput:
    return SpeechInput(event_name="청년 주거지원 정책 설명회", **kw)


def test_event_name_is_required():
    with pytest.raises(ValidationError):
        SpeechInput()


def test_defaults_match_spec():
    s = _base()
    assert s.event_type == "축사"
    assert s.target_chars == 1400
    assert s.vip_list == []
    assert s.persona_block == ""


def test_system_prompt_contains_all_three_layers():
    system, _ = build_speech_prompt(_base())
    assert "6단" in system            # L2
    assert "경어체" in system          # L3


def test_user_prompt_contains_event_facts():
    _, user = build_speech_prompt(_base(event_location="세종청사", speaker_role="장관"))
    assert "청년 주거지원 정책 설명회" in user
    assert "세종청사" in user
    assert "장관" in user


def test_persona_block_is_inserted_between_l4_and_l5():
    _, user = build_speech_prompt(
        _base(persona_block="현장에서 답을 찾겠습니다"),
        contexts=["행사계획서 발췌 내용"],
    )
    i_l4 = user.index("행사계획서 발췌 내용")
    i_persona = user.index("현장에서 답을 찾겠습니다")
    i_l5 = user.index("청년 주거지원 정책 설명회")
    assert i_l4 < i_persona < i_l5


def test_empty_persona_block_is_omitted():
    _, user = build_speech_prompt(_base(persona_block="   "))
    assert user.count("---") == 0     # L5 하나뿐이라 구분선이 없다


def test_l4_omitted_when_no_contexts():
    _, user = build_speech_prompt(_base())
    assert "참고자료" not in user


def test_seomyeon_chuksa_switches_to_four_part_structure():
    system, _ = build_speech_prompt(_base(event_type="서면축사"))
    assert "서면축사" in system
    assert "4단" in system
