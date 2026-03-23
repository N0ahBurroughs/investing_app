from __future__ import annotations

from datetime import datetime

from agents.evaluation_agent import EvaluationAgent
from agents.execution_agent import ExecutionAgent
from agents.learning_agent import LearningAgent
from agents.risk_agent import RiskAgent
from agents.strategy_agent import StrategyAgent
from core.logging import DecisionLogger
from core.models import TrainingRecord
from core.services import get_portfolio_model, record_trade, sync_portfolio
from core.trading import PaperBroker, portfolio_value
from data.provider import MarketDataProvider
from sqlalchemy.ext.asyncio import AsyncSession


class TradingOrchestrator:
    def __init__(
        self,
        provider: MarketDataProvider,
        log_path: str = "logs/decisions.jsonl",
        training_path: str = "training.md",
    ):
        self.provider = provider
        self.logger = DecisionLogger(log_path)
        self.strategy_agent = StrategyAgent()
        self.execution_agent = ExecutionAgent()
        self.risk_agent = RiskAgent()
        self.evaluation_agent = EvaluationAgent()
        self.learning_agent = LearningAgent(training_path)

    async def run_cycle(self, session: AsyncSession, user_id: int, raw_rules: str) -> TrainingRecord:
        rules, _ = await self.strategy_agent.parse(raw_rules)
        symbols = rules.universe
        if not symbols:
            raise ValueError("Strategy universe is empty")
        snapshot = await self.provider.get_snapshot(symbols)

        portfolio = await get_portfolio_model(session, user_id)
        broker = PaperBroker(portfolio)

        decisions = await self.execution_agent.decide(rules, snapshot, portfolio)
        if not decisions:
            raise ValueError("Execution agent produced no decisions")

        final_decision = decisions[0]
        risk_check = await self.risk_agent.validate(rules, final_decision, snapshot, portfolio)
        if not risk_check.approved:
            final_decision.action = "HOLD"
            final_decision.quantity = 0
        if risk_check.adjusted_quantity is not None:
            final_decision.quantity = risk_check.adjusted_quantity

        execution = broker.execute(final_decision, snapshot)
        evaluation = await self.evaluation_agent.evaluate(rules, final_decision, execution, snapshot, portfolio)

        record = TrainingRecord(
            timestamp=datetime.utcnow(),
            rule_set=rules,
            snapshot=snapshot,
            decision=final_decision,
            execution=execution,
            evaluation=evaluation,
            risk_check=risk_check,
        )

        self.logger.log(
            {
                "timestamp": record.timestamp,
                "rules": rules.model_dump(),
                "decision": final_decision.model_dump(),
                "risk": risk_check.model_dump(),
                "execution": execution.model_dump(),
                "evaluation": evaluation.model_dump(),
                "portfolio_value": portfolio_value(portfolio, snapshot),
            }
        )
        self.learning_agent.append(record)
        await sync_portfolio(session, user_id, portfolio)
        await record_trade(session, user_id, final_decision.model_dump(), execution.executed_price)
        return record
