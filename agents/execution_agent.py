from __future__ import annotations

from typing import List

from core.gemini_client import GeminiClient
from core.learning_state import LearningState
from core.models import MarketSnapshot, Portfolio, RuleSet, TradeDecision


class ExecutionAgent:
    def __init__(self) -> None:
        self.client = GeminiClient()
        self.learning_state = LearningState()

    async def decide(self, rules: RuleSet, snapshot: MarketSnapshot, portfolio: Portfolio) -> List[TradeDecision]:
        bias = float(self.learning_state.data.get("confidence_bias", 0.0))
        prompt = (
            "You are the execution agent for a trading system. "
            "Given strategy rules and market indicators, decide an action for each symbol. "
            "Return JSON array of decisions with keys: symbol, action (BUY|SELL|HOLD), quantity, "
            "confidence (0-1), reasons (list of strings), explanation (one sentence). "
            "Respect max_position_pct and avoid prohibited symbols. Use portfolio cash and holdings for sizing.\n\n"
            f"Rules: {rules.model_dump()}\n"
            f"Portfolio: {portfolio.model_dump()}\n"
            f"MarketSnapshot: {snapshot.model_dump()}\n"
            f"ConfidenceBias: {bias}"
        )
        data = await self.client.generate_json(prompt)
        decisions: List[TradeDecision] = []
        for item in data:
            decisions.append(
                TradeDecision(
                    symbol=item.get("symbol"),
                    action=item.get("action", "HOLD"),
                    quantity=int(item.get("quantity", 0)),
                    confidence=float(item.get("confidence", 0.5)),
                    reasons=list(item.get("reasons", [])),
                    explanation=item.get("explanation", ""),
                )
            )
        return decisions
