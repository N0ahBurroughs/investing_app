from __future__ import annotations

import logging
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.api_schemas import BacktestRequest, StartRequest, StopRequest, StrategyRequest, TradeRunRequest, UserCreateRequest
from core.coordinator import Coordinator
from core.db import SessionLocal, init_db
from core.logger import configure_logging
from core.models import Portfolio as PortfolioModel
from core.orchestrator import TradingOrchestrator
from core.security import validate_strategy_input
from core.services import get_portfolio_model
from core.user import Portfolio, Strategy, Trade, User
from data.marketwatch import MarketWatchProvider
from data.mock_provider import MockMarketDataProvider
from evaluation.backtester import Backtester

configure_logging()
logger = logging.getLogger("api")

app = FastAPI(title="AI Investing Assistant", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
coordinator = Coordinator()


async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


@app.on_event("startup")
async def startup() -> None:
    await init_db()


@app.post("/user/create")
async def create_user(payload: UserCreateRequest, session: AsyncSession = Depends(get_session)):
    existing = await session.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    user = User(email=payload.email, name=payload.name)
    session.add(user)
    await session.flush()
    portfolio = Portfolio(user_id=user.id, cash=payload.initial_capital)
    session.add(portfolio)
    await session.commit()
    return {"user_id": user.id, "portfolio_id": portfolio.id}


@app.post("/strategy")
async def set_strategy(payload: StrategyRequest, session: AsyncSession = Depends(get_session)):
    try:
        cleaned = validate_strategy_input(payload.content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    orchestrator = TradingOrchestrator(provider=MockMarketDataProvider())
    rules, _ = await orchestrator.strategy_agent.parse(cleaned)
    conflicts = await orchestrator.strategy_agent.detect_conflicts(rules)
    strategy = Strategy(user_id=payload.user_id, name=rules.name, raw_text=cleaned, normalized=rules.model_dump())
    session.add(strategy)
    await session.commit()
    return {"strategy_id": strategy.id, "rules": rules.model_dump(), "conflicts": conflicts}


@app.post("/trade/run")
async def run_trade(payload: TradeRunRequest, session: AsyncSession = Depends(get_session)):
    provider = MarketWatchProvider() if payload.provider == "marketwatch" else MockMarketDataProvider()
    orchestrator = TradingOrchestrator(provider=provider)
    record = await orchestrator.run_cycle(session, payload.user_id, payload.content)
    refinements = await orchestrator.learning_agent.suggest_refinements(record)
    await session.commit()
    return {
        "decision": record.decision.model_dump(),
        "risk": record.risk_check.model_dump(),
        "execution": record.execution.model_dump(),
        "evaluation": record.evaluation.model_dump(),
        "refinements": refinements,
    }


@app.post("/start")
async def start_loop(payload: StartRequest, session: AsyncSession = Depends(get_session)):
    strategy = await session.scalar(
        select(Strategy).where(Strategy.user_id == payload.user_id, Strategy.active == True).order_by(Strategy.created_at.desc())
    )
    if not strategy:
        raise HTTPException(status_code=400, detail="No active strategy found")
    await coordinator.start(payload.user_id, strategy.raw_text)
    return {"status": "started"}


@app.post("/stop")
async def stop_loop(payload: StopRequest):
    await coordinator.stop(payload.user_id)
    return {"status": "stopped"}


@app.get("/portfolio")
async def get_portfolio(user_id: int, session: AsyncSession = Depends(get_session)):
    portfolio = await get_portfolio_model(session, user_id)
    return portfolio.model_dump()


@app.get("/trades")
async def get_trades(user_id: int, session: AsyncSession = Depends(get_session)):
    trades = await session.execute(
        select(Trade).where(Trade.user_id == user_id).order_by(Trade.created_at.desc()).limit(50)
    )
    return [
        {
            "symbol": trade.symbol,
            "action": trade.action,
            "quantity": trade.quantity,
            "price": trade.price,
            "confidence": trade.confidence,
            "reasoning": trade.reasoning,
            "created_at": trade.created_at.isoformat(),
        }
        for trade in trades.scalars()
    ]


@app.get("/strategies")
async def list_strategies(user_id: int, session: AsyncSession = Depends(get_session)):
    strategies = await session.execute(
        select(Strategy).where(Strategy.user_id == user_id).order_by(Strategy.created_at.desc())
    )
    return [
        {
            "id": strategy.id,
            "name": strategy.name,
            "active": strategy.active,
            "created_at": strategy.created_at.isoformat(),
            "normalized": strategy.normalized,
        }
        for strategy in strategies.scalars()
    ]


@app.get("/market")
async def get_market(symbols: str = "AAPL,MSFT,NVDA"):
    provider = MarketWatchProvider()
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    snapshot = await provider.get_snapshot(symbol_list)
    return snapshot.model_dump()


@app.post("/backtest")
async def backtest(payload: BacktestRequest, session: AsyncSession = Depends(get_session)):
    provider = MarketWatchProvider()
    history = await provider.get_history(payload.symbol, days=payload.days)
    orchestrator = TradingOrchestrator(provider=provider)
    strategy = await session.scalar(
        select(Strategy).where(Strategy.user_id == payload.user_id, Strategy.active == True).order_by(Strategy.created_at.desc())
    )
    if not strategy:
        raise HTTPException(status_code=400, detail="No active strategy found")
    rules, _ = await orchestrator.strategy_agent.parse(strategy.raw_text)
    backtester = Backtester(orchestrator.execution_agent, orchestrator.risk_agent, orchestrator.evaluation_agent)
    result = await backtester.run(rules, history)
    return {
        "pnl": result.pnl,
        "win_rate": result.win_rate,
        "max_drawdown": result.max_drawdown,
        "equity_curve": result.equity_curve,
    }
