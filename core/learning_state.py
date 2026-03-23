from __future__ import annotations

import json
from pathlib import Path


class LearningState:
    def __init__(self, path: str = "data/learning_state.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = {"trade_count": 0, "avg_score": 0.0, "confidence_bias": 0.0}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text())
            except json.JSONDecodeError:
                self.data = {"trade_count": 0, "avg_score": 0.0, "confidence_bias": 0.0}

    def update(self, score: float) -> None:
        count = int(self.data.get("trade_count", 0))
        avg = float(self.data.get("avg_score", 0.0))
        new_avg = ((avg * count) + score) / (count + 1)
        confidence_bias = max(-0.1, min(0.1, (new_avg - 0.5) * 0.2))
        self.data = {
            "trade_count": count + 1,
            "avg_score": new_avg,
            "confidence_bias": confidence_bias,
        }
        self.path.write_text(json.dumps(self.data, indent=2))
