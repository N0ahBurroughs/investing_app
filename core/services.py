from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Portfolio as PortfolioModel, Position as PositionModel
from core.user import Portfolio, Position, Trade, User


async def get_portfolio_model(session: AsyncSession, user_id: int) -> PortfolioModel:
    portfolio = await session.scalar(select(Portfolio).where(Portfolio.user_id == user_id))
    if not portfolio:
        raise ValueError("Portfolio not found")
    positions = await session.execute(select(Position).where(Position.portfolio_id == portfolio.id))
    position_map: dict[str, PositionModel] = {}
    for position in positions.scalars():
        position_map[position.symbol] = PositionModel(
            symbol=position.symbol,
            quantity=position.quantity,
            avg_price=position.avg_price,
        )
    return PortfolioModel(cash=portfolio.cash, positions=position_map, realized_pnl=portfolio.realized_pnl)


async def sync_portfolio(session: AsyncSession, user_id: int, portfolio_model: PortfolioModel) -> None:
    portfolio = await session.scalar(select(Portfolio).where(Portfolio.user_id == user_id))
    if not portfolio:
        raise ValueError("Portfolio not found")
    portfolio.cash = portfolio_model.cash
    portfolio.realized_pnl = portfolio_model.realized_pnl
    portfolio.updated_at = datetime.utcnow()

    existing_positions = await session.execute(select(Position).where(Position.portfolio_id == portfolio.id))
    existing_by_symbol = {pos.symbol: pos for pos in existing_positions.scalars()}

    for symbol, pos_model in portfolio_model.positions.items():
        if symbol in existing_by_symbol:
            pos = existing_by_symbol[symbol]
            pos.quantity = pos_model.quantity
            pos.avg_price = pos_model.avg_price
        else:
            session.add(
                Position(
                    portfolio_id=portfolio.id,
                    symbol=symbol,
                    quantity=pos_model.quantity,
                    avg_price=pos_model.avg_price,
                )
            )

    for symbol, pos in existing_by_symbol.items():
        if symbol not in portfolio_model.positions:
            session.delete(pos)


async def record_trade(
    session: AsyncSession,
    user_id: int,
    decision: dict,
    executed_price: float | None,
) -> None:
    session.add(
        Trade(
            user_id=user_id,
            symbol=decision.get("symbol"),
            action=decision.get("action"),
            quantity=int(decision.get("quantity", 0)),
            price=float(executed_price or 0.0),
            confidence=float(decision.get("confidence", 0.0)),
            reasoning=decision.get("explanation", ""),
            raw_decision=decision,
        )
    )
