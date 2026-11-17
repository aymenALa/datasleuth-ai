"""Shared domain models for DataSleuth AI."""

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass
class DatasetContext:
    """Validated input dataset and metadata used by later pipeline stages."""

    dataset_id: str
    filename: str
    dataframe: pd.DataFrame
    row_count: int
    column_count: int
    column_names: list[str]
    warnings: list[str] = field(default_factory=list)


@dataclass
class ToolResult:
    """Compact, JSON-compatible result returned by an analysis tool."""

    tool_name: str
    status: str
    parameters: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    evidence: list[Any] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return the result in the shape intended for future tool calling."""

        return {
            "tool_name": self.tool_name,
            "status": self.status,
            "parameters": self.parameters,
            "metrics": self.metrics,
            "evidence": self.evidence,
            "warnings": self.warnings,
            "error": self.error,
        }


@dataclass
class InvestigationStep:
    """One locally executed tool call in an investigation trace."""

    tool_name: str
    arguments: dict[str, Any]
    result: dict[str, Any]
    call_id: str


@dataclass
class InvestigationState:
    """Mutable, UI-friendly state for one bounded investigation."""

    dataset_id: str
    goal: str
    steps: list[InvestigationStep] = field(default_factory=list)
    observations: list[dict[str, Any]] = field(default_factory=list)
    model_response: str | None = None
    completed: bool = False
    error: str | None = None
    turns: int = 0
    tool_calls: int = 0
    usage: dict[str, int] = field(default_factory=dict)


@dataclass
class InvestigationResult:
    """Final structured result returned by the investigation agent."""

    dataset_id: str
    goal: str
    status: str
    summary: str | None
    steps: list[InvestigationStep] = field(default_factory=list)
    observations: list[dict[str, Any]] = field(default_factory=list)
    model_response: str | None = None
    error: str | None = None
    usage: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "goal": self.goal,
            "status": self.status,
            "summary": self.summary,
            "steps": [
                {
                    "tool_name": step.tool_name,
                    "arguments": step.arguments,
                    "result": step.result,
                    "call_id": step.call_id,
                }
                for step in self.steps
            ],
            "observations": self.observations,
            "model_response": self.model_response,
            "error": self.error,
            "usage": self.usage,
        }
