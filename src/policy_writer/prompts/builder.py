from pydantic import BaseModel, Field

from policy_writer.prompts.l1_identity import L1_SPEECH
from policy_writer.prompts.l2_domain import L2_SPEECH
from policy_writer.prompts.l3_rules import L3_SPEECH


class SpeechInput(BaseModel):
    event_name: str = Field(..., min_length=1, description="행사명. 비면 400")
    event_type: str = "축사"
    event_date: str = ""
    event_location: str = ""
    speaker_name: str = ""
    speaker_role: str = ""
    speaker_organization: str = ""
    audience: str = ""
    vip_list: list[str] = Field(default_factory=list)
    target_chars: int = 1400
    key_messages: list[str] = Field(default_factory=list)
    quotes_or_anecdotes: list[str] = Field(default_factory=list)
    avoid_phrases: list[str] = Field(default_factory=list)
    persona_block: str = ""


def build_l4_speech(contexts: list[str] | None) -> str:
    """업로드한 행사계획서 발췌. 없으면 빈 문자열."""
    usable = [c.strip() for c in (contexts or []) if c and c.strip()]
    if not usable:
        return ""
    body = "\n\n".join(f"[자료 {i}]\n{c}" for i, c in enumerate(usable, 1))
    return f"# 참고자료\n\n아래는 이번 행사의 참고자료입니다. 사실관계는 이 자료를 따릅니다.\n\n{body}"


def _line(label: str, value: str) -> str:
    return f"- {label}: {value}" if value else ""


def _list_block(label: str, items: list[str]) -> str:
    if not items:
        return ""
    body = "\n".join(f"  - {i}" for i in items)
    return f"- {label}:\n{body}"


def build_l5_speech(input: SpeechInput) -> str:
    rows = [
        _line("행사명", input.event_name),
        _line("문서 유형", input.event_type),
        _line("일시", input.event_date),
        _line("장소", input.event_location),
        _line("발화자", " ".join(x for x in [input.speaker_organization, input.speaker_role, input.speaker_name] if x)),
        _line("청중", input.audience),
        _list_block("주요 참석자 (직급 순)", input.vip_list),
        _line("목표 글자수", f"{input.target_chars}자"),
        _list_block("반드시 넣을 핵심 메시지", input.key_messages),
        _list_block("쓸 수 있는 통계·일화", input.quotes_or_anecdotes),
        _list_block("피할 표현 (어떤 형태로도 쓰지 말 것)", input.avoid_phrases),
    ]
    facts = "\n".join(r for r in rows if r)
    return (
        f"# 이번 행사 정보\n\n{facts}\n\n"
        f"위 정보로 「{input.event_name}」 {input.event_type}를 "
        f"{input.target_chars}자 내외로 작성하십시오."
    )


def build_speech_prompt(input: SpeechInput, *, contexts: list[str] | None = None) -> tuple[str, str]:
    system_prompt = "\n\n".join([L1_SPEECH, L2_SPEECH, L3_SPEECH])

    user_parts: list[str] = []
    l4 = build_l4_speech(contexts)
    if l4:
        user_parts.append(l4)
    if input.persona_block.strip():          # 저장소 없이 폼 값만
        user_parts.append(
            "# 발화자의 말투·표현\n\n"
            "아래는 이 발화자가 평소 쓰는 표현과 말투입니다.\n"
            "본문에 자연스럽게 녹여 쓰십시오. 문장을 그대로 옮겨 써도 좋습니다.\n\n"
            + input.persona_block.strip()
        )
    user_parts.append(build_l5_speech(input))

    return system_prompt, "\n\n---\n\n".join(user_parts)
