"""출력에서 결함을 기계적으로 세는 검사들.

프롬프트 수정은 눈으로 봐서는 좋아졌는지 알 수 없다. 그래서 "이 결함이
있다/없다"를 사람 판단 없이 판정할 수 있게 만들어 두고, 수정 전후로 각각
여러 번 돌려 횟수를 센다.

⚠️ 이 검사들은 근사치다. 글이 좋은지를 재는 게 아니라, Task 13 이 지목한
세 가지 결함이 있는지만 본다. 판정 기준은 측정을 시작하기 전에 고정한다 —
측정 결과를 보고 기준을 옮기면 원하는 답이 나올 때까지 자를 바꾸는 셈이다.
"""
from policy_writer.exporters.converters import split_paragraphs

# 축사에는 나올 이유가 없고 이임사에는 나와야 하는 낱말만 골랐다.
# "그동안"·"함께해" 같은 낱말은 축사에도 흔해서 뺐다 — 넣으면 축사도
# 이임사로 통과해 버려 검사가 무의미해진다.
DEPARTURE_WORDS = ("이임", "퇴임", "재임", "후임", "소임", "떠나", "물러나", "몸담", "작별")

ORDINALS = ("첫째", "둘째", "셋째", "넷째")


def departure_markers(text: str) -> list[str]:
    return [w for w in DEPARTURE_WORDS if w in text]


def reads_like_a_congratulation(text: str) -> bool:
    """이임사 결함(B1): 이임을 가리키는 낱말이 하나도 없다.

    이러면 글이 축사와 구분되지 않는다 — 문서 종류 자체가 틀린 것처럼 보인다.
    """
    return not departure_markers(text)


def lumped_ordinal_paragraphs(text: str) -> list[str]:
    """4단 결함(B2): 첫째·둘째가 한 문단에 같이 들어간 문단들.

    낭독용 원고라 항목마다 문단이 나뉘어야 숨을 쉴 수 있다.
    """
    return [p for p in split_paragraphs(text) if sum(o in p for o in ORDINALS) >= 2]


def ordinal_count(text: str) -> int:
    """첫째~넷째 중 몇 종류가 나왔는가. 0 이면 B2 를 관찰할 수 없는 표본이다."""
    return sum(1 for o in ORDINALS if o in text)


def speaker_named_in_body(text: str, speaker_name: str, *, has_signature: bool) -> bool:
    """발화자 결함(B3): 원고를 읽는 본인 이름이 본문에 나온다.

    1인칭 원고라 발화자가 자기 이름을 부를 일은 없다. 이름이 나왔다면 거의
    언제나 감사 대상·내빈 명단에 자기를 넣은 경우다.
    서면축사만 예외 — 마지막 서명 줄에는 이름이 반드시 들어가야 하므로 뺀다.
    """
    if not speaker_name:
        return False
    paragraphs = split_paragraphs(text)
    if has_signature and paragraphs:
        paragraphs = paragraphs[:-1]        # 마지막 문단(서명 줄)은 검사에서 뺀다
    return any(speaker_name in p for p in paragraphs)
