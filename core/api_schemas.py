from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class UserCreateRequest(BaseModel):
    email: EmailStr
    name: str
    initial_capital: float = Field(default=100000.0, ge=0)


class StrategyRequest(BaseModel):
    user_id: int
    content: str


class StartRequest(BaseModel):
    user_id: int


class StopRequest(BaseModel):
    user_id: int


class BacktestRequest(BaseModel):
    user_id: int
    symbol: str
    days: int = 60


class TradeRunRequest(BaseModel):
    user_id: int
    content: str
    provider: str = "marketwatch"
