import pytest

from agents.execution_agent import ExecutionAgent
from agents.risk_agent import RiskAgent
from agents.evaluation_agent import EvaluationAgent
from core.models import RuleSet
from evaluation.backtester import Backtester


@pytest.mark.asyncio
async def test_backtester(monkeypatch):
    async def fake_generate_json(self, prompt):
        if "execution agent" in prompt.lower():
            return [
                {
                    "symbol": "TEST",
                    "action": "HOLD",
                    "quantity": 0,
                    "confidence": 0.5,
                    "reasons": [],
                    "explanation": "hold",
                }
            ]
        return {"approved": True, "reasons": [], "adjusted_quantity": None}

    monkeypatch.setattr("core.gemini_client.GeminiClient.generate_json", fake_generate_json)
    monkeypatch.setattr("core.gemini_client.GeminiClient.__init__", lambda self, api_key=None: None)

    backtester = Backtester(ExecutionAgent(), RiskAgent(), EvaluationAgent())
    history = [{"date": "2024-01-01", "close": 100.0, "volume": 1000} for _ in range(30)]
    result = await backtester.run(RuleSet(universe=["TEST"]), history)
    assert result.win_rate >= 0
