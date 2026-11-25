"""UI package for DataSleuth AI."""

from .theme import inject_custom_styles
from .view_models import (
    DashboardMetrics,
    ColumnQualitySummary,
    FindingViewModel,
    build_dashboard_metrics,
    build_column_summaries,
    build_finding_view_models,
)
from .formatters import (
    format_percentage,
    format_count,
    format_classification_label,
    format_confidence_label,
    sanitize_model_markdown,
)

__all__ = [
    "inject_custom_styles",
    "DashboardMetrics",
    "ColumnQualitySummary",
    "FindingViewModel",
    "build_dashboard_metrics",
    "build_column_summaries",
    "build_finding_view_models",
    "format_percentage",
    "format_count",
    "format_classification_label",
    "format_confidence_label",
    "sanitize_model_markdown",
]
