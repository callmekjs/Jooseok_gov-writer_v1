"""출력에서 결함을 기계적으로 세는 검사들.

프롬프트 수정은 눈으로 봐서는 좋아졌는지 알 수 없다. 그래서 "이 결함이
있다/없다"를 사람 판단 없이 판정할 수 있게 만들어 두고, 수정 전후로 각각
여러 번 돌려 횟수를 센다.

⚠️ 이 검사들은 근사치다. 글이 좋은지를 재는 게 아니라, Task 13 이 지목한
세 가지 결함이 있는지만 본다. 판정 기준은 측정을 시작하기 전에 고정한다 —
측정 결과를 보고 기준을 옮기면 원하는 답이 나올 때까지 자를 바꾸는 셈이다.
"""
import re

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


# 감사·예우를 뜻하는 낱말. "반갑습니다"는 넣지 않는다 — 자기소개 문장에 늘
# 붙어 있어서 넣으면 정상 원고를 전부 실패로 세게 된다.
THANKS_MARKERS = ("감사", "고맙", "노고", "빛내", "모시", "환영")

_SENTENCE = re.compile(r"(?<=[.!?])\s+|\n+")


def thanked_as_guest(text: str, patterns: list[str]) -> list[str]:
    """발화자 결함(B3): 원고를 읽는 본인이 감사 대상·내빈 명단에 들어갔다.

    ⚠️ "이름이 본문에 나오는가"로 재면 안 된다. 실제 원고는 거의 언제나
    "국토교통부 장관 김민수입니다" 로 자기소개를 하고, 그건 결함이 아니다
    (docs/samples/ 의 정상 출력 6건 중 3건이 이 문장을 갖고 있다).
    그래서 감사·예우 낱말이 **같은 문장 안에** 있을 때만 실패로 센다.

    patterns 는 정규식이다 — 예를 들어 "군수"를 찾을 때 "부군수"까지 걸리면
    안 되므로 호출하는 쪽에서 `(?<!부)군수` 처럼 넘긴다.
    """
    hits = []
    for sentence in _SENTENCE.split(text):
        if not any(m in sentence for m in THANKS_MARKERS):
            continue
        for pattern in patterns:
            if re.search(pattern, sentence) and pattern not in hits:
                hits.append(pattern)
    return hits


def honorific_after(text: str, name: str) -> bool:
    """이름 뒤에 "님"이 붙었다 = 남을 부르는 말이다. 자기소개는 "님"을 안 쓴다."""
    return bool(name) and bool(re.search(rf"{re.escape(name)}\s*님", text))
