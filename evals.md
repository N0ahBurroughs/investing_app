# Evaluation Criteria

## Rule Compliance
- Trade symbol is in the strategy universe.
- Trade does not violate prohibited symbols.
- Position sizing respects `max_position_pct`.
- Risk score stays below `max_risk_score`.

## Decision Quality
- Confidence aligned to signal strength.
- Clear reasoning trace in logs.
- Consistent with entry/exit rules.

## Outcome Metrics
- Realized P&L impact.
- Portfolio value change per cycle.
- Risk-adjusted performance (placeholder for future metrics).
