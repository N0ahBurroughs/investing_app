from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from core.models import MarketSnapshot, Portfolio, Position, TradeDecision, TradeExecution


@dataclass
class FillResult:
    executed: bool
    executed_price: float
    notes: list[str]


class PaperBroker:
    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio

    def execute(self, decision: TradeDecision, snapshot: MarketSnapshot) -> TradeExecution:
        price = snapshot.indicators[decision.symbol].price
        notes: list[str] = []

        if decision.action == "HOLD" or decision.quantity == 0:
            return TradeExecution(
                decision=decision,
                executed=False,
                executed_price=None,
                timestamp=datetime.utcnow(),
                notes=["No execution for HOLD/zero quantity"],
            )

        if decision.action == "BUY":
            cost = price * decision.quantity
            if cost > self.portfolio.cash:
                notes.append("Insufficient cash")
                return TradeExecution(
                    decision=decision,
                    executed=False,
                    executed_price=None,
                    timestamp=datetime.utcnow(),
                    notes=notes,
                )
            self.portfolio.cash -= cost
            position = self.portfolio.positions.get(decision.symbol)
            if position:
                total_qty = position.quantity + decision.quantity
                position.avg_price = ((position.avg_price * position.quantity) + cost) / total_qty
                position.quantity = total_qty
            else:
                self.portfolio.positions[decision.symbol] = Position(
                    symbol=decision.symbol,
                    quantity=decision.quantity,
                    avg_price=price,
                )
            return TradeExecution(
                decision=decision,
                executed=True,
                executed_price=price,
                timestamp=datetime.utcnow(),
                notes=notes,
            )

        if decision.action == "SELL":
            position = self.portfolio.positions.get(decision.symbol)
            if not position or position.quantity < decision.quantity:
                notes.append("Insufficient holdings")
                return TradeExecution(
                    decision=decision,
                    executed=False,
                    executed_price=None,
                    timestamp=datetime.utcnow(),
                    notes=notes,
                )
            proceeds = price * decision.quantity
            self.portfolio.cash += proceeds
            position.quantity -= decision.quantity
            pnl = (price - position.avg_price) * decision.quantity
            self.portfolio.realized_pnl += pnl
            if position.quantity == 0:
                del self.portfolio.positions[decision.symbol]
            return TradeExecution(
                decision=decision,
                executed=True,
                executed_price=price,
                timestamp=datetime.utcnow(),
                notes=notes,
            )

        notes.append("Unknown action")
        return TradeExecution(
            decision=decision,
            executed=False,
            executed_price=None,
            timestamp=datetime.utcnow(),
            notes=notes,
        )


def portfolio_value(portfolio: Portfolio, snapshot: MarketSnapshot) -> float:
    total = portfolio.cash
    for symbol, position in portfolio.positions.items():
        price = snapshot.indicators.get(symbol)
        if price:
            total += price.price * position.quantity
    return total
