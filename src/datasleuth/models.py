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
