"""프롬프트를 고치기 전/후에 같은 유형을 N 번 돌려 결함 횟수를 센다.

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
  MEASURE_OUT=... TRY_MODEL=gpt-5.6-terra ... (환경변수로 저장 위치·모델 변경)
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
    lumped_ordinal_paragraphs,
    ordinal_count,
    reads_like_a_congratulation,
    speaker_named_in_body,
)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EVENT_TYPE = sys.argv[1] if len(sys.argv) > 1 else "축사"
RUNS = int(sys.argv[2]) if len(sys.argv) > 2 else 6
TAG = sys.argv[3] if len(sys.argv) > 3 else EVENT_TYPE

PROVIDER = os.environ.get("TRY_PROVIDER", "openai")
MODEL = os.environ.get("TRY_MODEL", "gpt-4o-mini")   # 1건 1원. 가장 많이 실패해 개선이 잘 보인다
OUT_DIR = Path(os.environ.get("MEASURE_OUT", "docs/measure")) / TAG

# API 기본값과 같아야 측정값이 실제 사용과 같아진다 (api/speech.py 의 DraftIn).
MAX_TOKENS = 4000
TEMPERATURE = 0.7
CONCURRENCY = 4


async def one_run(index: int, api_key: str, model_meta: dict) -> dict:
    fields = sample_input(EVENT_TYPE)
    system_prompt, user_prompt = build_speech_prompt(SpeechInput(**fields))
    text, meta = await call_llm(
        provider=PROVIDER, model_meta=model_meta, api_key=api_key,
        system_prompt=system_prompt, user_prompt=user_prompt,
        max_tokens=MAX_TOKENS, temperature=TEMPERATURE,
    )
    lumped = lumped_ordinal_paragraphs(text)
    return {
        "index": index,
        "text": text,
        "chars": len(text.strip()),
        "output_tokens": meta["output_tokens"],
        "input_tokens": meta["input_tokens"],
        "b1_reads_like_congratulation": reads_like_a_congratulation(text),
        "b2_lumped": len(lumped) > 0,
        "b2_ordinals": ordinal_count(text),
        "b3_speaker_named": speaker_named_in_body(
            text, fields["speaker_name"], has_signature=EVENT_TYPE == "서면축사"),
    }


async def main() -> None:
    settings_keys = {"openai": "openai_api_key", "anthropic": "anthropic_api_key"}
    from policy_writer.config import get_settings
    api_key = getattr(get_settings(), settings_keys[PROVIDER])
    if not api_key:
        raise SystemExit(f".env 에 {settings_keys[PROVIDER].upper()} 가 없습니다.")
    model_meta = catalog.resolve(PROVIDER, MODEL)

    gate = asyncio.Semaphore(CONCURRENCY)

    async def guarded(i: int) -> dict:
        async with gate:
            return await one_run(i, api_key, model_meta)

    results = await asyncio.gather(*(guarded(i) for i in range(1, RUNS + 1)))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for r in results:
        (OUT_DIR / f"{r['index']:02d}.md").write_text(r["text"], encoding="utf-8")

    b1 = sum(r["b1_reads_like_congratulation"] for r in results)
    b2 = sum(r["b2_lumped"] for r in results)
    b3 = sum(r["b3_speaker_named"] for r in results)
    no_ordinals = sum(r["b2_ordinals"] == 0 for r in results)
    chars = [r["chars"] for r in results]
    outs = [r["output_tokens"] for r in results]

    header = (
        f"# {TAG} — {EVENT_TYPE} × {RUNS}회 ({PROVIDER}/{MODEL})\n\n"
        f"| # | 글자수 | out토큰 | B1 축사같음 | B2 첫째뭉침 | B2 서수종류 | B3 발화자이름 |\n"
        f"|---|---:|---:|---|---|---:|---|\n"
    )
    rows = "".join(
        f"| {r['index']} | {r['chars']} | {r['output_tokens']} | "
        f"{'❌' if r['b1_reads_like_congratulation'] else '✅'} | "
        f"{'❌' if r['b2_lumped'] else '✅'} | {r['b2_ordinals']} | "
        f"{'❌' if r['b3_speaker_named'] else '✅'} |\n"
        for r in results
    )
    summary = (
        f"\n**실패 횟수 / {RUNS}회**\n\n"
        f"- B1 이임 어휘 하나도 없음: **{b1}/{RUNS}**\n"
        f"- B2 첫째·둘째가 한 문단에: **{b2}/{RUNS}** (서수가 아예 없던 표본 {no_ordinals}건)\n"
        f"- B3 발화자 이름이 본문에: **{b3}/{RUNS}**\n\n"
        f"글자수 {min(chars)}~{max(chars)} (평균 {sum(chars) // len(chars)}) · "
        f"output_tokens {min(outs)}~{max(outs)} (평균 {sum(outs) // len(outs)})\n"
    )
    (OUT_DIR / "summary.md").write_text(header + rows + summary, encoding="utf-8")
    print(header + rows + summary)
    print(f"→ {OUT_DIR}")


asyncio.run(main())
