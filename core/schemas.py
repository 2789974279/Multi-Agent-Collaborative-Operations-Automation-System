from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ValidationError(ValueError):
    pass


@dataclass(frozen=True)
class TaskInput:
    title: str
    scenario: str
    objective: str
    audience: str
    constraints: str


@dataclass(frozen=True)
class AgentResult:
    agent: str
    title: str
    summary: str
    output: dict[str, Any]
    score: int


def parse_task_payload(payload: dict[str, Any], workflows: dict[str, Any]) -> TaskInput:
    required = ["title", "scenario", "objective", "audience", "constraints"]
    missing = [field for field in required if not str(payload.get(field, "")).strip()]
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")

    scenario = str(payload["scenario"]).strip()
    if scenario not in workflows:
        raise ValidationError(f"Unsupported scenario: {scenario}")

    return TaskInput(
        title=str(payload["title"]).strip(),
        scenario=scenario,
        objective=str(payload["objective"]).strip(),
        audience=str(payload["audience"]).strip(),
        constraints=str(payload["constraints"]).strip(),
    )
