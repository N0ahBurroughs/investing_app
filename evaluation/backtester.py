from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

from core.models import MarketIndicator, MarketSnapshot, Portfolio, RuleSet, TradeDecision
from core.trading import PaperBroker, portfolio_value


def _sma(values: List[float], window: int) -> float | None:
    if len(values) < window:
        return None
    return sum(values[-window:]) / window


def _rsi(values: List[float], window: int = 14) -> float | None:
    if len(values) < window + 1:
        return None
    gains = []
    losses = []
    for i in range(-window, 0):
        delta = values[i] - values[i - 1]
        if delta >= 0:
            gains.append(delta)
        else:
            losses.append(abs(delta))
    if not gains and not losses:
        return 50.0
    avg_gain = sum(gains) / window if gains else 0.0
    avg_loss = sum(losses) / window if losses else 0.0
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


@dataclass
class BacktestResult:
    pnl: float
    win_rate: float
    max_drawdown: float
    equity_curve: List[float]


class Backtester:
    def __init__(self, execution_agent, risk_agent, evaluation_agent):
        self.execution_agent = execution_agent
        self.risk_agent = risk_agent
        self.evaluation_agent = evaluation_agent

    async def run(self, rules: RuleSet, history: list[dict]) -> BacktestResult:
        portfolio = Portfolio()
        broker = PaperBroker(portfolio)
        equity_curve: List[float] = []
        wins = 0
        trades = 0
        peak = portfolio.cash
        max_drawdown = 0.0
        closes: List[float] = []

        for bar in history:
            closes.append(bar["close"])
            indicator = MarketIndicator(
                price=bar["close"],
                sma_20=_sma(closes, 20),
                rsi_14=_rsi(closes, 14),
                volatility_20=None,
            )
            snapshot = MarketSnapshot(
                as_of=datetime.utcnow(),
                indicators={bar.get("symbol", "TEST"): indicator},
                provider="backtest",
            )
            decisions = await self.execution_agent.decide(rules, snapshot, portfolio)
            if not decisions:
                continue
            decision = decisions[0]
            risk = await self.risk_agent.validate(rules, decision, snapshot, portfolio)
            if not risk.approved:
                decision.action = "HOLD"
                decision.quantity = 0
            execution = broker.execute(decision, snapshot)
            if execution.executed:
                trades += 1
                if portfolio.realized_pnl >= 0:
                    wins += 1
            equity = portfolio_value(portfolio, snapshot)
            equity_curve.append(equity)
            peak = max(peak, equity)
            drawdown = (peak - equity) / peak if peak else 0.0
            max_drawdown = max(max_drawdown, drawdown)

        pnl = portfolio.realized_pnl
        win_rate = wins / trades if trades else 0.0
        return BacktestResult(pnl=pnl, win_rate=win_rate, max_drawdown=max_drawdown, equity_curve=equity_curve)
