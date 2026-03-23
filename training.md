# Training Log

This file is appended by the Learning Agent after each trade cycle.

## Schema
```json
{
  "timestamp": "ISO-8601 timestamp",
  "rule_set": {"name": "..."},
  "snapshot": {"provider": "..."},
  "decision": {"symbol": "...", "action": "BUY|SELL|HOLD", "explanation": "..."},
  "execution": {"executed": true, "executed_price": 0.0},
  "risk_check": {"approved": true},
  "evaluation": {"score": 0.0}
}
```

## Trade Record
- Recorded: 2026-03-23T22:38:54.530356
```json
{
  "timestamp": "2026-03-23T22:38:54.530107",
  "rule_set": {
    "name": "Momentum Daily",
    "universe": [
      "AAPL",
      "MSFT",
      "NVDA"
    ],
    "max_position_pct": 0.1,
    "max_risk_score": 0.6,
    "trade_frequency": "daily",
    "entry_rules": [
      "Buy when price above 20-day SMA and RSI < 70"
    ],
    "exit_rules": [
      "Sell when price below 20-day SMA or RSI > 75"
    ],
    "prohibited": [
      "GME"
    ],
    "constraints": {},
    "rationale": "Focus on liquid mega-cap momentum."
  },
  "snapshot": {
    "as_of": "2026-03-23 22:38:54.529826",
    "indicators": {
      "AAPL": {
        "price": 169.52,
        "sma_20": 164.77,
        "rsi_14": 46.0,
        "volatility_20": 0.2116
      },
      "MSFT": {
        "price": 183.11,
        "sma_20": 184.87,
        "rsi_14": 70.69,
        "volatility_20": 0.1435
      },
      "NVDA": {
        "price": 139.07,
        "sma_20": 134.37,
        "rsi_14": 43.75,
        "volatility_20": 0.3527
      }
    },
    "provider": "mock"
  },
  "decision": {
    "symbol": "AAPL",
    "action": "BUY",
    "quantity": 58,
    "confidence": 0.65,
    "reasons": [
      "Price above 20-day SMA"
    ]
  },
  "execution": {
    "decision": {
      "symbol": "AAPL",
      "action": "BUY",
      "quantity": 58,
      "confidence": 0.65,
      "reasons": [
        "Price above 20-day SMA"
      ]
    },
    "executed": true,
    "executed_price": 169.52,
    "timestamp": "2026-03-23 22:38:54.530096",
    "notes": []
  },
  "risk_check": {
    "approved": true,
    "reasons": [],
    "adjusted_quantity": null
  },
  "evaluation": {
    "score": 1.0,
    "rule_compliance": 1.0,
    "pnl_impact": 0.0,
    "notes": []
  }
}
```
