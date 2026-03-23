from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from core.gemini_client import GeminiClient
from core.learning_state import LearningState
from core.models import TrainingRecord


class LearningAgent:
    def __init__(self, training_path: str = "training.md"):
        self.training_path = Path(training_path)
        self.learning_state = LearningState()
        self.client = GeminiClient()
        if not self.training_path.exists():
            self.training_path.write_text("# Training Log\n\n")

    def append(self, record: TrainingRecord) -> None:
        entry = {
            "timestamp": record.timestamp.isoformat(),
            "rule_set": record.rule_set.model_dump(),
            "snapshot": record.snapshot.model_dump(),
            "decision": record.decision.model_dump(),
            "execution": record.execution.model_dump(),
            "risk_check": record.risk_check.model_dump(),
            "evaluation": record.evaluation.model_dump(),
        }
        with self.training_path.open("a") as handle:
            handle.write("\n## Trade Record\n")
            handle.write(f"- Recorded: {datetime.utcnow().isoformat()}\n")
            handle.write("```json\n")
            handle.write(json.dumps(entry, indent=2, default=str))
            handle.write("\n```\n")
        self.learning_state.update(record.evaluation.score)

    async def suggest_refinements(self, record: TrainingRecord) -> list[str]:
        prompt = (
            "You are the learning agent. Suggest strategy refinements based on the trade record. "
            "Return JSON array of short suggestions.\n\n"
            f"Record: {record.model_dump()}"
        )
        data = await self.client.generate_json(prompt)
        return list(data)
