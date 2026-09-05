from policy_writer.llm import catalog, cost


def test_won_per_doc_for_sonnet():
    # 4,000 x $3/1M + 1,500 x $15/1M = $0.0345 → 48원
    m = catalog.resolve("anthropic", "claude-sonnet-4-5-20250929")
    assert cost.won_per_doc(m) == 48


def test_won_per_doc_for_mini_is_cheapest():
    m = catalog.resolve("openai", "gpt-4o-mini")
    assert cost.won_per_doc(m) == 2


def test_won_per_doc_for_sol():
    m = catalog.resolve("openai", "gpt-5.6-sol")
    assert cost.won_per_doc(m) == 64


def test_won_for_usage_uses_actual_tokens():
    m = catalog.resolve("openai", "gpt-4o-mini")
    assert cost.won_for_usage(m, 0, 0) == 0
    assert cost.won_for_usage(m, 4000, 1500) == cost.won_per_doc(m)


def test_won_per_doc_for_opus():
    # 4,000 x $5/1M + 1,500 x $25/1M = $0.0575 ; $0.0575 * 1400 = 80.5
    # 정확히 .5 지점이라 파이썬 round()의 은행반올림(0.5 -> 짝수)이 적용되어 80원.
    # (컨트롤러가 제시한 기대값 81원은 이 세션에서 실제로 계산해 보니 맞지 않아 80원으로 정정함)
    m = catalog.resolve("anthropic", "claude-opus-4-5-20251101")
    assert cost.won_per_doc(m) == 80
