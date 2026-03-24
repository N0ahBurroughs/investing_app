from __future__ import annotations

from typing import List

from core.gemini_client import GeminiClient
from core.learning_state import LearningState
from core.models import MarketSnapshot, Portfolio, RuleSet, TradeDecision


class ExecutionAgent:
    def __init__(self) -> None:
        try:
            self.client = GeminiClient()
        except Exception:
            self.client = None
        self.learning_state = LearningState()

    async def decide(self, rules: RuleSet, snapshot: MarketSnapshot, portfolio: Portfolio) -> List[TradeDecision]:
        if not self.client:
            return self._fallback_decisions(rules, snapshot, portfolio)
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
        try:
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
        except Exception:
            return self._fallback_decisions(rules, snapshot, portfolio)

    @staticmethod
    def _fallback_decisions(rules: RuleSet, snapshot: MarketSnapshot, portfolio: Portfolio) -> List[TradeDecision]:
        decisions: List[TradeDecision] = []
        bought = False
        for symbol, indicator in snapshot.indicators.items():
            action = "HOLD"
            quantity = 0
            reasons = ["LLM unavailable; using fallback decisioning"]
            if symbol in rules.prohibited:
                reasons.append("Symbol prohibited")
            else:
                max_position_value = portfolio.cash * rules.max_position_pct
                max_qty = int(max_position_value // indicator.price) if indicator.price > 0 else 0
                if not bought and max_qty > 0:
                    action = "BUY"
                    quantity = min(1, max_qty)
                    bought = True
                    reasons.append("Fallback BUY of 1 share")
            decisions.append(
                TradeDecision(
                    symbol=symbol,
                    action=action,
                    quantity=quantity,
                    confidence=0.4,
                    reasons=reasons,
                    explanation="Fallback execution due to LLM error.",
                )
            )
        return decisions
