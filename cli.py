from __future__ import annotations

import argparse
import asyncio

from core.db import SessionLocal, init_db
from core.orchestrator import TradingOrchestrator
from data.marketwatch import MarketWatchProvider
from data.mock_provider import MockMarketDataProvider


def main() -> None:
    parser = argparse.ArgumentParser(description="AI-powered trading assistant")
    parser.add_argument("rules", help="Rules text or path to rules file")
    parser.add_argument("user_id", type=int, help="User ID")
    parser.add_argument("--provider", default="marketwatch", choices=["mock", "marketwatch"])
    args = parser.parse_args()

    async def run() -> None:
        await init_db()
        provider = MarketWatchProvider() if args.provider == "marketwatch" else MockMarketDataProvider()
        orchestrator = TradingOrchestrator(provider=provider)
        async with SessionLocal() as session:
            record = await orchestrator.run_cycle(session, args.user_id, args.rules)
            await session.commit()
            print("Decision:")
            print(record.decision.model_dump())
            print("Risk:")
            print(record.risk_check.model_dump())
            print("Evaluation:")
            print(record.evaluation.model_dump())
            print("Execution:")
            print(record.execution.model_dump())

    asyncio.run(run())


if __name__ == "__main__":
    main()
