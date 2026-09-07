"""프롬프트를 고치기 전/후에 같은 입력을 N 번 돌려 결함 횟수를 센다.

Task 13 의 교훈이 이 파일의 존재 이유다. 프롬프트 수정은 눈으로 봐서 좋아졌는지
알 수 없다. 이전 세션은 몇 번 읽어 보고 "좋아졌다"고 판단해 발화자 결함
실패율을 33% → 83% 로 올렸고, 측정했기 때문에 그걸 알아내 되돌릴 수 있었다.
한두 번 돌려 본 인상으로는 이 판단을 할 수 없다 — 그래서 N ≥ 6 이다.

HTTP 서버를 거치지 않고 build_speech_prompt + call_llm 을 그대로 호출한다:
  - 8011 로컬 서버는 --reload 없이 떠 있다. 프롬프트를 고쳐도 반영되지 않아서,
    재시작을 한 번만 잊어도 옛 프롬프트를 측정하는 사고가 난다.
  - /api/speech/draft 는 결과를 Supabase 작성 이력에 저장한다. 측정용 수십 건이
    사용자 이력에 쌓이면 안 된다.
프롬프트 조립 경로(L1~L5)는 API 와 완전히 같다 — 재려는 대상이 바로 그것이다.

사용:
  .\\.venv\\Scripts\\python.exe scripts\\measure_defects.py 이임사 6 before-b1

환경변수:
  TRY_MODEL      기본 gpt-4o-mini (1건 1원, 가장 많이 실패해 개선이 잘 보인다)
  MEASURE_OUT    표본을 저장할 폴더 (기본 docs/measure — .gitignore 에 있다)
  MEASURE_RICH   1 이면 vip_list·일화·말투가 든 긴 입력을 쓴다
  MEASURE_DOC    행사계획서 파일 경로. 주면 L4 참고자료 경로를 잰다 —
                 발화자 항목을 비우고 문서에서 발화자를 추론하게 하는,
                 발화자 결함(B3)이 실제로 나타나는 경로다.
  MEASURE_SPEAKER  B3 에서 찾을 정규식 (기본: 입력의 발화자 이름).
                 MEASURE_DOC 을 쓸 때는 문서 속 발화자 직책을 넘긴다.
  MEASURE_CASE   stat 이면 아래 STAT_CASE(통계 결함 재현 입력)를 쓴다.
  MEASURE_STAT   0 이면 대조군 — 같은 입력에서 "인용할 통계" 칸만 비운다.
                 이때 B4 는 잴 수 없고 "지어낸 수치" 쪽만 본다.
  MEASURE_CHARS  MEASURE_CASE=stat 일 때 목표 글자수를 바꾼다 (화면의 분량 선택).
"""
import asyncio
import os
import sys
from pathlib import Path

from policy_writer.llm import catalog
from policy_writer.llm.client import call_llm
from policy_writer.prompts.builder import SpeechInput, build_speech_prompt

from _common import sample_input
from _defects import (
    honorific_after,
    invented_figures,
    lumped_ordinal_paragraphs,
    ordinal_count,
    reads_like_a_congratulation,
    stat_used,
    thanked_as_guest,
)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EVENT_TYPE = sys.argv[1] if len(sys.argv) > 1 else "축사"
RUNS = int(sys.argv[2]) if len(sys.argv) > 2 else 6
TAG = sys.argv[3] if len(sys.argv) > 3 else EVENT_TYPE

PROVIDER = os.environ.get("TRY_PROVIDER", "openai")
MODEL = os.environ.get("TRY_MODEL", "gpt-4o-mini")
OUT_DIR = Path(os.environ.get("MEASURE_OUT", "docs/measure")) / TAG
RICH = os.environ.get("MEASURE_RICH") == "1"
DOC = os.environ.get("MEASURE_DOC", "")
CASE = os.environ.get("MEASURE_CASE", "")
STAT_ON = os.environ.get("MEASURE_STAT", "1") != "0"
CHARS = os.environ.get("MEASURE_CHARS", "")

# 실제 사용에서 B4 가 관찰된 입력을 그대로 옮긴 것: 숫자·연도가 든 핵심 메시지
# 3개와 통계 한 줄. 핵심 메시지 3개는 전부 원문 그대로 쓰이고 통계만 빠졌다.
# 핵심 메시지가 3개인 것이 중요하다 — L3 4단이 "첫째/둘째/셋째"로 세 자리를
# 이미 채워 버려서 통계가 들어갈 자리가 남지 않는다.
STAT_CASE = {
    "event_name": "사관학교 교육 통합 발전 토론회",
    "event_type": "축사",
    "event_date": "2026년 9월 12일",
    "event_location": "국방컨벤션센터",
    "speaker_name": "김민수",
    "speaker_role": "장관",
    "speaker_organization": "국방부",
    "audience": "생도, 교수, 군 관계자",
    "target_chars": 1500,
    "key_messages": [
        "2027년까지 3개 사관학교 공통 교육과정을 통합한다",
        "2026년 하반기부터 공동 강의 20개 과목을 시범 운영한다",
        "생도 교류 프로그램을 연 2회로 늘린다",
    ],
    "quotes_or_anecdotes": ["3개 사관학교 중복 과목이 연간 1,200시간"],
    "avoid_phrases": ["만감이 교차"],
}
# 통계를 구별하는 숫자. 핵심 메시지에는 없는 수라 겹치지 않는다.
STAT_TOKEN = r"1,?200"

# API 기본값과 같아야 측정값이 실제 사용과 같아진다 (api/speech.py 의 DraftIn).
MAX_TOKENS = 4000
TEMPERATURE = 0.7
CONCURRENCY = 4


def build_case() -> tuple[SpeechInput, list[str], list[str], bool]:
    """(입력, 참고자료, B3 에서 찾을 정규식, 서명이 있는 유형인가)"""
    if DOC:
        # Task 9 의 자동 작성 경로. 발화자 항목을 비워 두면 모델이 행사계획서에서
        # 발화자를 읽어내야 한다 — 발화자를 감사 명단에 넣는 결함이 여기서 난다.
        from policy_writer.extractors.files import extract_text

        path = Path(DOC)
        contexts = [extract_text(path.name, path.read_bytes())]
        fields = {"event_name": path.stem, "event_type": EVENT_TYPE, "target_chars": 1500}
        patterns = [os.environ["MEASURE_SPEAKER"]]
        return SpeechInput(**fields), contexts, patterns, False

    if CASE == "stat":
        fields = dict(STAT_CASE, event_type=EVENT_TYPE)
        if CHARS:
            fields["target_chars"] = int(CHARS)      # 화면의 분량 선택(600·900·1500·2400)
        if not STAT_ON:
            fields["quotes_or_anecdotes"] = []      # 대조군: 통계 칸을 비운다
        patterns = [os.environ.get("MEASURE_SPEAKER") or fields["speaker_name"]]
        return SpeechInput(**fields), [], patterns, EVENT_TYPE == "서면축사"

    fields = sample_input(EVENT_TYPE, rich=RICH)
    patterns = [os.environ.get("MEASURE_SPEAKER") or fields["speaker_name"]]
    return SpeechInput(**fields), [], patterns, EVENT_TYPE == "서면축사"


async def one_run(index: int, api_key: str, model_meta: dict) -> dict:
    speech_input, contexts, patterns, has_signature = build_case()
    system_prompt, user_prompt = build_speech_prompt(speech_input, contexts=contexts)
    text, meta = await call_llm(
        provider=PROVIDER, model_meta=model_meta, api_key=api_key,
        system_prompt=system_prompt, user_prompt=user_prompt,
        max_tokens=MAX_TOKENS, temperature=TEMPERATURE,
    )
    body = text
    if has_signature:
        body = "\n\n".join(text.strip().split("\n\n")[:-1])   # 서명 줄은 B3 대상이 아니다
    return {
        "index": index,
        "text": text,
        "chars": len(text.strip()),
        "output_tokens": meta["output_tokens"],
        "input_tokens": meta["input_tokens"],
        "b1": reads_like_a_congratulation(text),
        "b2": bool(lumped_ordinal_paragraphs(text)),
        "b2_ordinals": ordinal_count(text),
        "b3": bool(thanked_as_guest(body, patterns)) or any(
            honorific_after(body, p) for p in patterns if p.isalnum()),
        "b4": STAT_ON and not stat_used(text, STAT_TOKEN),
        "invented": invented_figures(text, system_prompt + "\n" + user_prompt),
    }


async def main() -> None:
    from policy_writer.config import get_settings

    key_field = {"openai": "openai_api_key", "anthropic": "anthropic_api_key"}[PROVIDER]
    api_key = getattr(get_settings(), key_field)
    if not api_key:
        raise SystemExit(f".env 에 {key_field.upper()} 가 없습니다.")
    model_meta = catalog.resolve(PROVIDER, MODEL)

    gate = asyncio.Semaphore(CONCURRENCY)

    async def guarded(i: int) -> dict:
        async with gate:
            return await one_run(i, api_key, model_meta)

    results = await asyncio.gather(*(guarded(i) for i in range(1, RUNS + 1)))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for r in results:
        (OUT_DIR / f"{r['index']:02d}.md").write_text(r["text"], encoding="utf-8")

    b1 = sum(r["b1"] for r in results)
    b2 = sum(r["b2"] for r in results)
    b3 = sum(r["b3"] for r in results)
    b4 = sum(r["b4"] for r in results)
    made_up = sum(bool(r["invented"]) for r in results)
    made_up_total = sum(len(r["invented"]) for r in results)
    no_ordinals = sum(r["b2_ordinals"] == 0 for r in results)
    chars = [r["chars"] for r in results]
    outs = [r["output_tokens"] for r in results]

    if CASE == "stat":
        variant = " · 통계 결함 입력" + ("" if STAT_ON else " (대조군: 통계 칸 비움)")
    elif DOC:
        variant = f" · 참고자료 {Path(DOC).name}"
    else:
        variant = " · 긴 입력" if RICH else ""
    header = (
        f"# {TAG} — {EVENT_TYPE} × {RUNS}회 ({PROVIDER}/{MODEL}{variant})\n\n"
        f"| # | 글자수 | out토큰 | B1 이임어휘없음 | B2 서수뭉침 | B2 서수종류 | "
        f"B3 발화자감사 | B4 통계누락 | 지어낸 수치 |\n"
        f"|---|---:|---:|---|---|---:|---|---|---|\n"
    )
    rows = "".join(
        f"| {r['index']} | {r['chars']} | {r['output_tokens']} | "
        f"{'X' if r['b1'] else 'o'} | {'X' if r['b2'] else 'o'} | {r['b2_ordinals']} | "
        f"{'X' if r['b3'] else 'o'} | {'X' if r['b4'] else 'o'} | "
        f"{', '.join(r['invented']) or '-'} |\n"
        for r in results
    )
    stat_line = (
        f"- B4 통계가 원고에 안 쓰임: **{b4}/{RUNS}**  "
        f"(통계 사용 **{RUNS - b4}/{RUNS}**)\n" if STAT_ON else
        f"- B4 대조군이라 잴 수 없음 (통계 칸 비움)\n"
    )
    summary = (
        f"\n**실패 횟수 / {RUNS}회**\n\n"
        f"- B1 이임 어휘 하나도 없음: **{b1}/{RUNS}**\n"
        f"- B2 첫째·둘째가 한 문단에: **{b2}/{RUNS}** (서수가 아예 없던 표본 {no_ordinals}건)\n"
        f"- B3 발화자가 감사 대상으로: **{b3}/{RUNS}**\n"
        + stat_line +
        f"- 지어낸 수치가 있던 표본: **{made_up}/{RUNS}** (수치 종류 합계 {made_up_total}개)\n\n"
        f"글자수 {min(chars)}~{max(chars)} (평균 {sum(chars) // len(chars)}) · "
        f"output_tokens {min(outs)}~{max(outs)} (평균 {sum(outs) // len(outs)})\n"
    )
    (OUT_DIR / "summary.md").write_text(header + rows + summary, encoding="utf-8")
    print(header + rows + summary)
    print(f"-> {OUT_DIR}")


asyncio.run(main())
