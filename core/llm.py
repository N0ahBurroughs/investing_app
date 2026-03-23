from __future__ import annotations

from typing import List

from core.models import RuleSet, TradeDecision


class RuleBasedLLM:
    """
    Lightweight stand-in for an LLM. Uses heuristics and the rules to
    generate a decision payload with traceable reasons.
    """

    def decide(self, symbol: str, signal: str, confidence: float, rules: RuleSet, reasons: List[str]) -> TradeDecision:
        action = signal

        if symbol in rules.prohibited:
            action = "HOLD"
            reasons.append("Symbol prohibited by rule set")

        return TradeDecision(
            symbol=symbol,
            action=action,
            quantity=0,
            confidence=confidence,
            reasons=reasons,
        )
