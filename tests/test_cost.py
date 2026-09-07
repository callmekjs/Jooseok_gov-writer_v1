from policy_writer.llm import catalog, cost


def test_won_per_doc_for_sonnet():
    # 3,000 x $3/1M + 1,400 x $15/1M = $0.030 → 42원
    m = catalog.resolve("anthropic", "claude-sonnet-4-5-20250929")
    assert cost.won_per_doc(m) == 42


def test_won_per_doc_for_mini_is_cheapest():
    m = catalog.resolve("openai", "gpt-4o-mini")
    assert cost.won_per_doc(m) == 2


def test_won_per_doc_for_sol():
    # 3,000 x $4/1M + 1,400 x $20/1M = $0.040 → 56원
    m = catalog.resolve("openai", "gpt-5.6-sol")
    assert cost.won_per_doc(m) == 56


def test_won_for_usage_uses_actual_tokens():
    m = catalog.resolve("openai", "gpt-4o-mini")
    assert cost.won_for_usage(m, 0, 0) == 0
    # 리터럴 4000/1500 을 다시 박아두면 상수가 또 바뀔 때 이 테스트가 또 깨진다 —
    # won_per_doc() 이 실제로 쓰는 상수를 그대로 참조해 "won_per_doc == 그 상수로
    # 계산한 값"이라는 관계 자체를 검증한다.
    assert (
        cost.won_for_usage(m, cost.TYPICAL_INPUT_TOKENS, cost.TYPICAL_OUTPUT_TOKENS)
        == cost.won_per_doc(m)
    )


def test_won_per_doc_for_opus():
    # 3,000 x $5/1M + 1,400 x $25/1M = $0.050 → 70.0, 정확히 나눠져 반올림 경계가 없다.
    m = catalog.resolve("anthropic", "claude-opus-4-5-20251101")
    assert cost.won_per_doc(m) == 70
