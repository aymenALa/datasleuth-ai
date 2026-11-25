"""Presentation-only view models and deterministic derived metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from datasleuth.models import DatasetContext
from datasleuth.visualizations import issue_counts
from .formatters import (
    format_classification_label,
    format_confidence_label,
    format_observed_label,
    format_count,
)


@dataclass(frozen=True)
class DashboardMetrics:
    """Consolidated KPI metrics derived deterministically from existing analytical counts."""

    row_count: int
    column_count: int
    total_cells: int
    missing_cells: int
    missing_cell_rate: float
    duplicate_rows: int
    duplicate_row_rate: float
    findings_count: int | None
    outlier_candidate_count: int | None
    is_investigated: bool


@dataclass(frozen=True)
class ColumnQualitySummary:
    """Column-level completeness and type profile for exploration."""

    name: str
    inferred_type: str
    non_missing_count: int
    missing_count: int
    completeness_percentage: float


@dataclass(frozen=True)
class FindingViewModel:
    """Human-readable view representation of a verified finding."""

    finding_id: str
    title: str
    classification: str
    classification_label: str
    confidence: str
    confidence_label: str
    tool_name: str
    metric_path: str
    value: Any
    observed_label: str
    columns: list[str]
    evidence_summary: str
    evidence_payload: list[Any] = field(default_factory=list)


def build_dashboard_metrics(
    context: DatasetContext,
    report: dict[str, Any] | None = None,
) -> DashboardMetrics:
    """Compute verified KPI rates without modifying or querying the database or agent."""
    rows = len(context.dataframe)
    cols = len(context.dataframe.columns)
    total_cells = rows * cols

    counts = issue_counts(context)
    missing = counts.get("Missing cells", 0)
    duplicates = counts.get("Duplicate rows", 0)

    missing_rate = (missing / total_cells * 100.0) if total_cells > 0 else 0.0
    duplicate_rate = (duplicates / rows * 100.0) if rows > 0 else 0.0

    findings_count: int | None = None
    outlier_count: int | None = None
    is_investigated = False

    if report is not None:
        is_investigated = True
        findings = report.get("verified_findings", [])
        findings_count = len(findings)

        # Count outlier candidates across verified findings if present
        outlier_total = 0
        has_outlier_finding = False
        for f in findings:
            if "outlier" in f.get("metric_path", ""):
                has_outlier_finding = True
                val = f.get("value")
                if isinstance(val, (int, float)):
                    outlier_total += int(val)
        outlier_count = outlier_total if has_outlier_finding else 0

    return DashboardMetrics(
        row_count=rows,
        column_count=cols,
        total_cells=total_cells,
        missing_cells=missing,
        missing_cell_rate=missing_rate,
        duplicate_rows=duplicates,
        duplicate_row_rate=duplicate_rate,
        findings_count=findings_count,
        outlier_candidate_count=outlier_count,
        is_investigated=is_investigated,
    )


def build_column_summaries(context: DatasetContext) -> list[ColumnQualitySummary]:
    """Compile deterministic column quality metrics from the active dataframe."""
    rows = len(context.dataframe)
    summaries: list[ColumnQualitySummary] = []

    for col in context.dataframe.columns:
        series = context.dataframe[col]
        missing = int(series.isna().sum())
        non_missing = rows - missing
        completeness = (non_missing / rows * 100.0) if rows > 0 else 100.0

        summaries.append(
            ColumnQualitySummary(
                name=str(col),
                inferred_type=str(series.dtype),
                non_missing_count=non_missing,
                missing_count=missing,
                completeness_percentage=completeness,
            )
        )

    return summaries


def build_finding_view_models(report: dict[str, Any] | None) -> list[FindingViewModel]:
    """Format verified findings for readable search, filter, and card presentation."""
    if not report:
        return []

    raw_findings = report.get("verified_findings", [])
    view_models: list[FindingViewModel] = []

    for idx, f in enumerate(raw_findings, start=1):
        classification = str(f.get("classification", "measured_fact"))
        metric_path = str(f.get("metric_path", ""))
        value = f.get("value")
        columns = [str(c) for c in f.get("columns", [])]
        evidence_list = f.get("evidence", [])

        # Build natural language evidence summary
        summary_parts = []
        if evidence_list and isinstance(evidence_list, list):
            for ev in evidence_list:
                if isinstance(ev, dict):
                    examples = ev.get("examples", [])
                    if examples and isinstance(examples[0], dict):
                        ex = examples[0]
                        if "missing_percentage" in ex:
                            pct = ex.get("missing_percentage")
                            cnt = ex.get("missing_count", value)
                            summary_parts.append(
                                f"{cnt} missing cell{'s' if cnt != 1 else ''} ({pct:.2f}% of column)"
                            )
                        elif "duplicate_percentage" in ex:
                            dup_pct = ex.get("duplicate_percentage")
                            group_cnt = ex.get("duplicate_group_row_count", value)
                            sub_ex = ex.get("examples", [])
                            positions = [
                                str(r.get("row_position"))
                                for r in sub_ex
                                if isinstance(r, dict) and "row_position" in r
                            ]
                            pos_str = f" at row positions [{', '.join(positions)}]" if positions else ""
                            summary_parts.append(
                                f"{group_cnt} matching rows ({dup_pct}% redundant){pos_str}"
                            )

        evidence_summary = " · ".join(summary_parts) if summary_parts else ""

        view_models.append(
            FindingViewModel(
                finding_id=str(f.get("finding_id", f"finding_{idx}")),
                title=str(f.get("title", f"Finding {idx}")),
                classification=classification,
                classification_label=format_classification_label(classification),
                confidence=str(f.get("confidence", "context required")),
                confidence_label=format_confidence_label(f.get("confidence")),
                tool_name=str(f.get("tool_name", "")),
                metric_path=metric_path,
                value=value,
                observed_label=format_observed_label(classification, metric_path, value),
                columns=columns,
                evidence_summary=evidence_summary,
                evidence_payload=evidence_list,
            )
        )

    return view_models
