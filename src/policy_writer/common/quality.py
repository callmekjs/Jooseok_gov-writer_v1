def check_output(text: str, target_chars: int) -> list[str]:
    """경고만 담는다. 절대 막지 않는다 — 짧아도 사용자가 손보면 쓸 수 있다."""
    warnings: list[str] = []
    stripped = text.strip()
    if not stripped:
        warnings.append("응답이 비어 있습니다. 다시 시도해 주세요.")
        return warnings
    if len(stripped) < target_chars * 0.6:
        warnings.append(
            f"목표({target_chars}자)보다 짧습니다. 현재 {len(stripped)}자. "
            f"더 높은 등급의 모델을 쓰면 분량이 늘어납니다."
        )
    return warnings
