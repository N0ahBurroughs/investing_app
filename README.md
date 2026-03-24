# AI-Powered Investing Platform

This is a real-time, end-to-end AI investing system with multi-agent orchestration, Gemini Flash integration, Finnhub market data, paper trading, backtesting, and a full React dashboard.

## Features
- Multi-agent coordinator (Strategy, Execution, Risk, Evaluation, Learning).
- Real-time market polling loop (async).
- Finnhub price + historical data integration (free tier supported).
- Gemini Flash LLM integration for all agent decisions.
- Backtesting engine with P&L, win rate, drawdown.
- Postgres-backed user accounts, portfolios, strategies, and trades.
- Structured logs + training data updates.
- React + Tailwind dashboard UI.

## Setup

### 1) Environment
Create `.env` based on `.env.example`:
```
GEMINI_API_KEY=your_api_key
FINNHUB_API_KEY=your_api_key
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/investing
MARKET_POLL_SECONDS=30
MARKET_DATA_PROVIDER=finnhub
```

### 2) Backend
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn main:app --reload
```

### 3) Frontend
```bash
cd /Users/noahburroughs/Desktop/AI POC/investing_app/frontend
npm install
npm run dev
```

## Usage Flow
1. Create or log in a user via `POST /user/ensure`.
2. Save a strategy via `POST /strategy`.
3. Start the real-time loop via `POST /start`.
4. Watch the dashboard update in real time.

Example run (one-off decision):
```bash
curl -X POST http://localhost:8000/trade/run \\
  -H \"Content-Type: application/json\" \\
  -d '{\"user_id\":1,\"content\":\"Name: Momentum Daily\\nUniverse: AAPL, MSFT\"}'
```

## API Endpoints
- `POST /user/create`
- `POST /user/ensure`
- `POST /auth/register`
- `POST /auth/login`
- `POST /user/setup`
- `POST /strategy`
- `POST /trade/run`
- `POST /start`
- `POST /stop`
- `GET /portfolio`
- `GET /trades`
- `GET /market`
- `GET /history`
- `GET /strategies`
- `POST /backtest`

## Logging & Learning
- Structured logs: `logs/decisions.jsonl`
- Learning log: `training.md`
- Learning state: `data/learning_state.json`

## Example Strategy
```
Name: Momentum Daily
Universe: AAPL, MSFT, NVDA
Max_Position_Pct: 0.1
Max_Risk_Score: 0.6
Entry: Buy when price above 20-day SMA and RSI < 70
Exit: Sell when price below 20-day SMA or RSI > 75
```

## Strategy Presets
Safe:
```
Name: Defensive Core
Universe: AAPL, MSFT, JNJ, PG
Max_Position_Pct: 0.08
Max_Risk_Score: 0.4
Entry: Buy when price above 20-day SMA and RSI < 65
Exit: Sell when price below 20-day SMA or RSI > 70
```
Balanced:
```
Name: Balanced Trend
Universe: AAPL, MSFT, NVDA, AMZN
Max_Position_Pct: 0.12
Max_Risk_Score: 0.6
Entry: Buy when price above 20-day SMA and RSI between 45 and 70
Exit: Sell when price below 20-day SMA or RSI > 75
```
Risky:
```
Name: Aggressive Momentum
Universe: NVDA, TSLA, AMD, COIN
Max_Position_Pct: 0.2
Max_Risk_Score: 0.8
Entry: Buy when price above 20-day SMA and RSI < 75
Exit: Sell when price below 20-day SMA or RSI > 80
```

## Notes
- Finnhub free tier is rate-limited; the app caches snapshots for 30s and reuses the latest snapshot on temporary errors.
- All agent decisions include reasoning and confidence scoring.
