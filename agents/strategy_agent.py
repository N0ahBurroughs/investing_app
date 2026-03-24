from __future__ import annotations

from core.gemini_client import GeminiClient
from core.models import RuleSet
from core.rules import parse_rules
from core.security import validate_strategy_input


class StrategyAgent:
    def __init__(self) -> None:
        try:
            self.client = GeminiClient()
        except Exception:
            self.client = None

    async def parse(self, raw_rules: str) -> tuple[RuleSet, str]:
        cleaned = validate_strategy_input(raw_rules)
        if not self.client:
            rules, mode = parse_rules(cleaned)
            return rules, f"{mode}_fallback"
        prompt = (
            "You are a trading strategy parser. Convert the user rules into JSON with keys: "
            "name, universe (list), max_position_pct (float), max_risk_score (float), trade_frequency, "
            "entry_rules (list), exit_rules (list), prohibited (list), constraints (object), rationale (string). "
            "Return only JSON.\n\nRules:\n"
            f"{cleaned}"
        )
        try:
            data = await self.client.generate_json(prompt)
            rules = RuleSet(
                name=data.get("name", "Unnamed Strategy"),
                universe=[s.upper() for s in data.get("universe", [])],
                max_position_pct=float(data.get("max_position_pct", 0.1)),
                max_risk_score=float(data.get("max_risk_score", 0.7)),
                trade_frequency=data.get("trade_frequency", "daily"),
                entry_rules=list(data.get("entry_rules", [])),
                exit_rules=list(data.get("exit_rules", [])),
                prohibited=[s.upper() for s in data.get("prohibited", [])],
                constraints=dict(data.get("constraints", {})),
                rationale=data.get("rationale", ""),
            )
            return rules, "gemini"
        except Exception:
            rules, mode = parse_rules(cleaned)
            return rules, f"{mode}_fallback"

    async def detect_conflicts(self, rules: RuleSet) -> list[str]:
        if not self.client:
            return []
        prompt = (
            "You are a strategy reviewer. Identify conflicts or ambiguities in the rules. "
            "Return JSON array of short conflict descriptions.\\n\\n"
            f"Rules: {rules.model_dump()}"
        )
        try:
            data = await self.client.generate_json(prompt)
            return list(data)
        except Exception:
            return []
