from __future__ import annotations

import re

MAX_STRATEGY_LENGTH = 8000
INJECTION_PATTERNS = [
    r"ignore\s+previous",
    r"system\s+prompt",
    r"developer\s+message",
    r"jailbreak",
    r"exfiltrate",
]


def validate_strategy_input(text: str) -> str:
    if not text or not text.strip():
        raise ValueError("Strategy input cannot be empty")
    if len(text) > MAX_STRATEGY_LENGTH:
        raise ValueError("Strategy input too long")
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            raise ValueError("Potential prompt injection detected")
    return text.strip()
