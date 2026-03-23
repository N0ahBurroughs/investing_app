# Agent Roles

## Strategy Agent
- Ingests user rules from text, markdown, or JSON.
- Normalizes rules into a structured `RuleSet`.
- Uses Gemini Flash for parsing and conflict detection.

## Execution Agent
- Uses market indicators and rules to generate trade signals.
- Sizes positions based on portfolio constraints.
- Provides explainable reasons for each decision.
- Uses Gemini Flash for decision making and confidence scoring.

## Risk Agent
- Validates trade decisions against risk constraints.
- Blocks or reduces trades that violate max risk or sizing rules.

## Evaluation Agent
- Scores decisions based on rule compliance and P&L impact.
- Produces evaluation metadata for feedback loops.

## Learning Agent
- Persists training records after each cycle.
- Appends structured entries to `training.md`.
- Enables prompt/rule refinement over time.
