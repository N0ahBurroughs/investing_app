from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from core.models import RuleSet


def _split_csv(value: str) -> List[str]:
    return [v.strip().upper() for v in value.split(",") if v.strip()]


def _parse_key_value_lines(lines: List[str]) -> Dict[str, str]:
    parsed: Dict[str, str] = {}
    for line in lines:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        parsed[key.strip().lower()] = value.strip()
    return parsed


def _normalize_from_mapping(data: Dict[str, Any]) -> RuleSet:
    return RuleSet(
        name=data.get("name", "Unnamed Strategy"),
        universe=[s.upper() for s in data.get("universe", [])],
        max_position_pct=float(data.get("max_position_pct", 0.1)),
        max_risk_score=float(data.get("max_risk_score", 0.7)),
        trade_frequency=data.get("trade_frequency", "daily"),
        entry_rules=list(data.get("entry_rules", [])),
        exit_rules=list(data.get("exit_rules", [])),
        prohibited=[s.upper() for s in data.get("prohibited", [])],
        constraints=dict(data.get("constraints", {})),
        rationale=data.get("rationale", ""),
    )


def parse_rules(raw_input: str) -> Tuple[RuleSet, str]:
    path = Path(raw_input)
    if path.exists() and path.is_file():
        raw_text = path.read_text()
    else:
        raw_text = raw_input

    raw_text = raw_text.strip()
    if not raw_text:
        return RuleSet(), "empty"

    if raw_text.startswith("{"):
        try:
            payload = json.loads(raw_text)
            return _normalize_from_mapping(payload), "json"
        except json.JSONDecodeError:
            pass

    lines = [line.strip("- ") for line in raw_text.splitlines() if line.strip()]
    parsed = _parse_key_value_lines(lines)

    universe = _split_csv(parsed.get("universe", ""))
    prohibited = _split_csv(parsed.get("prohibited", ""))

    entry_rules = []
    exit_rules = []
    for line in lines:
        lower = line.lower()
        if lower.startswith("entry") and ":" in line:
            entry_rules.append(line.split(":", 1)[1].strip())
        if lower.startswith("exit") and ":" in line:
            exit_rules.append(line.split(":", 1)[1].strip())

    constraints: Dict[str, str] = {}
    for key, value in parsed.items():
        if key.startswith("constraint"):
            constraints[key] = value

    rules = RuleSet(
        name=parsed.get("name", "Unnamed Strategy"),
        universe=universe,
        max_position_pct=float(parsed.get("max_position_pct", 0.1)),
        max_risk_score=float(parsed.get("max_risk_score", 0.7)),
        trade_frequency=parsed.get("trade_frequency", "daily"),
        entry_rules=entry_rules,
        exit_rules=exit_rules,
        prohibited=prohibited,
        constraints=constraints,
        rationale=parsed.get("rationale", ""),
    )

    return rules, "text"
