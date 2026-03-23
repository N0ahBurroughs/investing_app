from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class DecisionLogger:
    def __init__(self, log_path: str = "logs/decisions.jsonl"):
        self.path = Path(log_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, payload: Dict[str, Any]) -> None:
        with self.path.open("a") as handle:
            handle.write(json.dumps(payload, default=str) + "\n")
