from __future__ import annotations

from core.gemini_client import GeminiClient
from core.models import EvaluationResult, MarketSnapshot, Portfolio, RuleSet, TradeDecision, TradeExecution


class EvaluationAgent:
    def __init__(self) -> None:
        self.client = GeminiClient()

    async def evaluate(
        self,
        rules: RuleSet,
        decision: TradeDecision,
        execution: TradeExecution,
        snapshot: MarketSnapshot,
        portfolio: Portfolio,
    ) -> EvaluationResult:
        pnl_impact = portfolio.realized_pnl
        prompt = (
            "You are the evaluation agent. Score the decision on rule compliance and outcome. "
            "Return JSON with keys: score (0-1), rule_compliance (0-1), notes (list).\n\n"
            f"Rules: {rules.model_dump()}\n"
            f"Decision: {decision.model_dump()}\n"
            f"Execution: {execution.model_dump()}\n"
            f"Portfolio: {portfolio.model_dump()}\n"
            f"MarketSnapshot: {snapshot.model_dump()}\n"
            f"PnLImpact: {pnl_impact}"
        )
        data = await self.client.generate_json(prompt)
        return EvaluationResult(
            score=float(data.get("score", 0.5)),
            rule_compliance=float(data.get("rule_compliance", 0.5)),
            pnl_impact=pnl_impact,
            notes=list(data.get("notes", [])),
        )
