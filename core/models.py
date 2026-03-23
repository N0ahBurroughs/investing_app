from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class RuleSet(BaseModel):
    name: str = "Unnamed Strategy"
    universe: List[str] = Field(default_factory=list)
    max_position_pct: float = 0.1
    max_risk_score: float = 0.7
    trade_frequency: str = "daily"
    entry_rules: List[str] = Field(default_factory=list)
    exit_rules: List[str] = Field(default_factory=list)
    prohibited: List[str] = Field(default_factory=list)
    constraints: Dict[str, str] = Field(default_factory=dict)
    rationale: str = ""


class MarketIndicator(BaseModel):
    price: float
    sma_20: Optional[float] = None
    rsi_14: Optional[float] = None
    volatility_20: Optional[float] = None
    volume: Optional[float] = None


class MarketSnapshot(BaseModel):
    as_of: datetime
    indicators: Dict[str, MarketIndicator]
    provider: str


class TradeDecision(BaseModel):
    symbol: str
    action: str  # BUY, SELL, HOLD
    quantity: int
    confidence: float
    reasons: List[str] = Field(default_factory=list)
    explanation: str = ""


class RiskCheckResult(BaseModel):
    approved: bool
    reasons: List[str] = Field(default_factory=list)
    adjusted_quantity: Optional[int] = None


class TradeExecution(BaseModel):
    decision: TradeDecision
    executed: bool
    executed_price: Optional[float] = None
    timestamp: datetime
    notes: List[str] = Field(default_factory=list)


class Position(BaseModel):
    symbol: str
    quantity: int
    avg_price: float


class Portfolio(BaseModel):
    cash: float = 100000.0
    positions: Dict[str, Position] = Field(default_factory=dict)
    realized_pnl: float = 0.0


class EvaluationResult(BaseModel):
    score: float
    rule_compliance: float
    pnl_impact: float
    notes: List[str] = Field(default_factory=list)


class TrainingRecord(BaseModel):
    timestamp: datetime
    rule_set: RuleSet
    snapshot: MarketSnapshot
    decision: TradeDecision
    execution: TradeExecution
    evaluation: EvaluationResult
    risk_check: RiskCheckResult
