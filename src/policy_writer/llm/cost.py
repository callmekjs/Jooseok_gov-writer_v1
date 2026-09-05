USD_TO_KRW = 1400
TYPICAL_INPUT_TOKENS = 4000      # 프롬프트 L1~L5
TYPICAL_OUTPUT_TOKENS = 1500     # 1,500자


def won_for_usage(model_meta: dict, input_tokens: int, output_tokens: int) -> int:
    usd = (
        input_tokens * model_meta["in"] / 1_000_000
        + output_tokens * model_meta["out"] / 1_000_000
    )
    return round(usd * USD_TO_KRW)


def won_per_doc(model_meta: dict) -> int:
    """말씀자료 1건당 대략 얼마인지. 사용자에게 $0.000123 은 의미가 없다."""
    return won_for_usage(model_meta, TYPICAL_INPUT_TOKENS, TYPICAL_OUTPUT_TOKENS)
