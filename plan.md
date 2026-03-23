# Implementation Roadmap

## Phase 1: Foundation
- Establish modular directory layout (`/agents`, `/core`, `/data`, `/evaluation`, `/strategies`, `/tests`).
- Implement data models, rule parsing, and base interfaces.
- Create mock data provider and MarketWatch provider abstraction.

## Phase 2: Agent Workflow
- Strategy Agent parses rules into structured `RuleSet`.
- Execution Agent generates trade signals and sizing.
- Risk Agent enforces risk constraints.
- Evaluation Agent scores outcomes.
- Learning Agent appends results to `training.md`.

## Phase 3: Trading Engine
- Paper trading broker, portfolio tracking, P&L accounting.
- Decision logging to JSONL.
- Orchestrator to run an end-to-end cycle.

## Phase 4: Interfaces
- FastAPI endpoints for parsing rules and running trades.
- CLI entrypoint for quick runs.

## Phase 5: Iteration
- Expand evaluation metrics, backtesting support, provider plugins.
- Add tests and performance dashboards.
