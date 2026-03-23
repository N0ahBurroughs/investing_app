# Strategy Examples

## Markdown Example
```
Name: Momentum Daily
Universe: AAPL, MSFT, NVDA
Max_Position_Pct: 0.1
Max_Risk_Score: 0.6
Trade_Frequency: daily
Entry: Buy when price above 20-day SMA and RSI < 70
Exit: Sell when price below 20-day SMA or RSI > 75
Prohibited: GME
Rationale: Focus on liquid mega-cap momentum.
```

## JSON Example
```json
{
  "name": "Mean Reversion",
  "universe": ["TSLA", "AMZN"],
  "max_position_pct": 0.08,
  "max_risk_score": 0.5,
  "trade_frequency": "daily",
  "entry_rules": ["Buy when RSI < 35"],
  "exit_rules": ["Sell when RSI > 55"],
  "prohibited": [],
  "constraints": {
    "max_open_positions": "3"
  },
  "rationale": "Short-term mean reversion on volatile names."
}
```
