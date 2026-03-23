from datetime import datetime

import pytest

from agents.execution_agent import ExecutionAgent
from agents.risk_agent import RiskAgent
from agents.strategy_agent import StrategyAgent
from core.models import MarketIndicator, MarketSnapshot, Portfolio, RuleSet, TradeDecision


@pytest.mark.asyncio
async def test_strategy_agent_parse(monkeypatch):
    async def fake_generate_json(self, prompt):
        return {
            "name": "Test",
            "universe": ["AAPL"],
            "max_position_pct": 0.1,
            "max_risk_score": 0.6,
            "trade_frequency": "daily",
            "entry_rules": ["buy"],
            "exit_rules": ["sell"],
            "prohibited": [],
            "constraints": {},
            "rationale": "",
        }

    monkeypatch.setattr("core.gemini_client.GeminiClient.generate_json", fake_generate_json)
    monkeypatch.setattr("core.gemini_client.GeminiClient.__init__", lambda self, api_key=None: None)

    agent = StrategyAgent()
    rules, mode = await agent.parse("Name: Test")
    assert rules.name == "Test"
    assert mode == "gemini"


@pytest.mark.asyncio
async def test_execution_agent_decide(monkeypatch):
    async def fake_generate_json(self, prompt):
        return [
            {
                "symbol": "AAPL",
                "action": "BUY",
                "quantity": 10,
                "confidence": 0.7,
                "reasons": ["test"],
                "explanation": "test explanation",
            }
        ]

    monkeypatch.setattr("core.gemini_client.GeminiClient.generate_json", fake_generate_json)
    monkeypatch.setattr("core.gemini_client.GeminiClient.__init__", lambda self, api_key=None: None)

    agent = ExecutionAgent()
    snapshot = MarketSnapshot(
        as_of=datetime.utcnow(),
        indicators={"AAPL": MarketIndicator(price=100.0)},
        provider="test",
    )
    decisions = await agent.decide(RuleSet(universe=["AAPL"]), snapshot, Portfolio())
    assert decisions[0].action == "BUY"


@pytest.mark.asyncio
async def test_risk_agent_validate(monkeypatch):
    async def fake_generate_json(self, prompt):
        return {"approved": True, "reasons": [], "adjusted_quantity": None}

    monkeypatch.setattr("core.gemini_client.GeminiClient.generate_json", fake_generate_json)
    monkeypatch.setattr("core.gemini_client.GeminiClient.__init__", lambda self, api_key=None: None)

    agent = RiskAgent()
    snapshot = MarketSnapshot(
        as_of=datetime.utcnow(),
        indicators={"AAPL": MarketIndicator(price=100.0, volatility_20=0.2)},
        provider="test",
    )
    decision = TradeDecision(symbol="AAPL", action="BUY", quantity=1, confidence=0.5)
    result = await agent.validate(RuleSet(universe=["AAPL"], max_risk_score=0.6), decision, snapshot, Portfolio())
    assert result.approved is True
