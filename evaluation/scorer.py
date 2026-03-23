from __future__ import annotations

from core.models import EvaluationResult


def summarize(result: EvaluationResult) -> str:
    return f"Score={result.score:.2f} Compliance={result.rule_compliance:.2f} PnL={result.pnl_impact:.2f}"
