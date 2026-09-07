USD_TO_KRW = 1400

# ── Task 12 비용 보정 (2026-09-07) ──────────────────────────────────────────
# 실측 근거: scripts/compare_models.py 로 6개 모델 전부 동일 프롬프트를 1회씩
# 새로 호출한 결과 (docs/model-comparison.md).
#
#   provider    model                          input_tokens   output_tokens
#   openai      gpt-4o-mini                         1,986            416
#   openai      gpt-5.6-terra                        1,985            892
#   openai      gpt-5.6-sol                          1,985          1,912
#   anthropic   claude-haiku-4-5                     3,143          1,066
#   anthropic   claude-sonnet-4-5-20250929           3,143          1,367
#   anthropic   claude-opus-4-5-20251101             3,143          1,204
#
# input 은 같은 L1~L5 프롬프트인데도 회사(토크나이저)별로만 갈린다 — Anthropic
# 쪽이 OpenAI보다 한글을 더 잘게 쪼개 토큰이 ~58% 더 많다. 이전 세션 실측치
# (컨트롤러 추가지시: 1,811~2,807)와 합치면 관측 범위는 1,811~3,143.
# 이전 상수 4,000 은 이 범위보다 항상 크다 — 이게 "모든 등급 과대 표시"의 원인.
#
# output 은 각 등급이 목표 분량(1,500자)에 얼마나 다가가는지에 따라 416~1,912
# 로 편차가 크다 — 인턴 등급이 목표에 못 미치고 멈추는 현상은 이미 알려진
# 한계다 (README 「모델 비교 실측」). 상위 네 모델(892~1,912)은 1,000~1,400대에
# 몰려 있어 그 근방을 "전형적인 1건"으로 잡는다.
#
# 아래 두 값은 "실제보다 조금 높게, 2배는 넘지 않게"라는 지침에 맞춰 골랐다.
# 3,000 / 1,400 으로 위 실측 6건의 won_for_usage() 를 역산한 표시값과, 이번에
# 실제로 청구된(=실측 토큰 그대로 계산한) 금액을 비교하면:
#
#   모델                          표시(신규)   실측 청구   배율   비고
#   gpt-4o-mini                        2원         1원     2.00x  반올림 특성(1원 단위) — 컨트롤러 표에도 이미 2원/1원으로 명시된 값
#   gpt-5.6-terra                     32원        21원     1.52x
#   gpt-5.6-sol                       56원        65원     0.86x  과거 실제 청구 범위 40~56원의 상단과 일치
#   claude-haiku-4-5                  14원        12원     1.17x
#   claude-sonnet-4-5-20250929        42원        42원     1.00x
#   claude-opus-4-5-20251101          70원        64원     1.09x
#
# gpt-4o-mini 를 빼면(원 단위 반올림 때문에 구조적으로 못 피하는 경우) 전부
# 0.86~1.52배 — "조금 높게, 2배 미만" 조건을 만족한다. gpt-5.6-sol 만 0.86배로
# 약간 낮게 나오지만, 그 모델 자체의 실제 청구가 세션마다 40~56원으로 크게
# 흔들리는 모델이라(컨트롤러 추가지시 표) 56원은 그 변동 폭 안에 있다.
TYPICAL_INPUT_TOKENS = 3000      # 프롬프트 L1~L5, 실측 1,985~3,143(+과거 1,811~2,807) 상단 근처
TYPICAL_OUTPUT_TOKENS = 1400     # 실측 416~1,912. 목표에 근접한 상위 등급들의 대표값


def won_for_usage(model_meta: dict, input_tokens: int, output_tokens: int) -> int:
    usd = (
        input_tokens * model_meta["in"] / 1_000_000
        + output_tokens * model_meta["out"] / 1_000_000
    )
    return round(usd * USD_TO_KRW)


def won_per_doc(model_meta: dict) -> int:
    """말씀자료 1건당 대략 얼마인지. 사용자에게 $0.000123 은 의미가 없다."""
    return won_for_usage(model_meta, TYPICAL_INPUT_TOKENS, TYPICAL_OUTPUT_TOKENS)
