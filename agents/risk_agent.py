from __future__ import annotations

from core.gemini_client import GeminiClient
from core.models import MarketSnapshot, Portfolio, RiskCheckResult, RuleSet, TradeDecision


class RiskAgent:
    def __init__(self) -> None:
        try:
            self.client = GeminiClient()
        except Exception:
            self.client = None

    async def validate(
        self,
        rules: RuleSet,
        decision: TradeDecision,
        snapshot: MarketSnapshot,
        portfolio: Portfolio,
    ) -> RiskCheckResult:
        prompt = (
            "You are the risk agent. Validate the trade decision against risk constraints. "
            "Return JSON with keys: approved (boolean), reasons (list), adjusted_quantity (int or null).\n\n"
            f"Rules: {rules.model_dump()}\n"
            f"Portfolio: {portfolio.model_dump()}\n"
            f"MarketSnapshot: {snapshot.model_dump()}\n"
            f"Decision: {decision.model_dump()}"
        )
        approved = True
        reasons: list[str] = []
        adjusted = None
        if self.client:
            try:
                data = await self.client.generate_json(prompt)
                approved = bool(data.get("approved", True))
                reasons = list(data.get("reasons", []))
                adjusted = data.get("adjusted_quantity")
            except Exception:
                reasons.append("LLM unavailable; using fallback risk checks")

        indicator = snapshot.indicators.get(decision.symbol)
        if not indicator:
            return RiskCheckResult(approved=False, reasons=["Missing market data"], adjusted_quantity=None)
        if decision.symbol in rules.prohibited:
            approved = False
            reasons.append("Symbol is prohibited")
        if indicator.volatility_20 is not None and indicator.volatility_20 > rules.max_risk_score:
            approved = False
            reasons.append("Volatility exceeds max risk score")
        if decision.action == "BUY":
            max_position_value = portfolio.cash * rules.max_position_pct
            max_qty = int(max_position_value // indicator.price)
            if decision.quantity > max_qty:
                adjusted = max_qty
                reasons.append("Quantity reduced to max position size")

        return RiskCheckResult(approved=approved, reasons=reasons, adjusted_quantity=adjusted)
