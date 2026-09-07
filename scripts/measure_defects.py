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
    lumped_ordinal_paragraphs,
    ordinal_count,
    reads_like_a_congratulation,
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
    no_ordinals = sum(r["b2_ordinals"] == 0 for r in results)
    chars = [r["chars"] for r in results]
    outs = [r["output_tokens"] for r in results]

    variant = f" · 참고자료 {Path(DOC).name}" if DOC else (" · 긴 입력" if RICH else "")
    header = (
        f"# {TAG} — {EVENT_TYPE} × {RUNS}회 ({PROVIDER}/{MODEL}{variant})\n\n"
        f"| # | 글자수 | out토큰 | B1 이임어휘없음 | B2 서수뭉침 | B2 서수종류 | B3 발화자감사 |\n"
        f"|---|---:|---:|---|---|---:|---|\n"
    )
    rows = "".join(
        f"| {r['index']} | {r['chars']} | {r['output_tokens']} | "
        f"{'X' if r['b1'] else 'o'} | {'X' if r['b2'] else 'o'} | {r['b2_ordinals']} | "
        f"{'X' if r['b3'] else 'o'} |\n"
        for r in results
    )
    summary = (
        f"\n**실패 횟수 / {RUNS}회**\n\n"
        f"- B1 이임 어휘 하나도 없음: **{b1}/{RUNS}**\n"
        f"- B2 첫째·둘째가 한 문단에: **{b2}/{RUNS}** (서수가 아예 없던 표본 {no_ordinals}건)\n"
        f"- B3 발화자가 감사 대상으로: **{b3}/{RUNS}**\n\n"
        f"글자수 {min(chars)}~{max(chars)} (평균 {sum(chars) // len(chars)}) · "
        f"output_tokens {min(outs)}~{max(outs)} (평균 {sum(outs) // len(outs)})\n"
    )
    (OUT_DIR / "summary.md").write_text(header + rows + summary, encoding="utf-8")
    print(header + rows + summary)
    print(f"-> {OUT_DIR}")


asyncio.run(main())
