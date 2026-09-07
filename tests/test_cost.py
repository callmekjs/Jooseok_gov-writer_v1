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
    # 리터럴 3000/1400 으로 고정한다 (일부러 하드코딩). cost.TYPICAL_* 상수를
    # 그대로 참조해 비교하면 won_per_doc() 의 정의를 그대로 되풀이하는 것뿐이라
    # 상수가 어떤 값으로 바뀌어도 항상 참인 tautology 가 되어 회귀를 못 잡는다.
    # 리터럴이면 상수가 바뀔 때 이 줄이 깨지고, 그 churn 자체가 "바뀐 상수로도
    # 계산이 여전히 맞는지" 사람이 다시 확인하게 만드는 게 목적이다.
    assert cost.won_for_usage(m, 3000, 1400) == cost.won_per_doc(m)


def test_won_per_doc_for_opus():
    # 3,000 x $5/1M + 1,400 x $25/1M = $0.050 → 70.0, 정확히 나눠져 반올림 경계가 없다.
    m = catalog.resolve("anthropic", "claude-opus-4-5-20251101")
    assert cost.won_per_doc(m) == 70
