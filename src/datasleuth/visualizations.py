"""Deterministic, read-only data-quality visualization preparation."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from pandas.api.types import (
    is_bool_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_string_dtype,
)

from .models import DatasetContext
from .tools import analyze_missing_values, detect_duplicates


_TYPE_ORDER = ["Numeric", "Text / categorical", "Boolean", "Date/time", "Other"]
_TYPE_COLORS = ["#38BDF8", "#34D399", "#F59E0B", "#818CF8", "#94A3B8"]
_FONT_FAMILY = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"


def _column_type(series: pd.Series) -> str:
    """Classify only from the existing Pandas dtype; do not parse values."""

    dtype = series.dtype
    if is_bool_dtype(dtype):
        return "Boolean"
    if is_datetime64_any_dtype(dtype):
        return "Date/time"
    if is_numeric_dtype(dtype):
        return "Numeric"
    if isinstance(dtype, pd.CategoricalDtype) or is_string_dtype(dtype):
        return "Text / categorical"
    return "Other"


def dataset_composition(context: DatasetContext) -> pd.DataFrame:
    """Return actual column counts grouped by recognized Pandas types."""

    grouped: dict[str, list[str]] = {label: [] for label in _TYPE_ORDER}
    for column in context.dataframe.columns:
        label = _column_type(context.dataframe[column])
        grouped[label].append(str(column))
    return pd.DataFrame(
        {
            "type_group": _TYPE_ORDER,
            "column_count": [len(grouped[label]) for label in _TYPE_ORDER],
            "columns": [grouped[label] for label in _TYPE_ORDER],
        }
    )


def dataset_composition_figure(context: DatasetContext) -> go.Figure:
    """Build the deterministic dataset-composition bar chart."""

    data = dataset_composition(context)
    figure = go.Figure(
        go.Bar(
            x=data["type_group"],
            y=data["column_count"],
            customdata=data[["columns"]],
            text=data["column_count"],
            textposition="auto",
            textfont={"family": _FONT_FAMILY, "color": "#F1F5F9", "size": 12},
            hovertemplate="<b>%{x}</b><br>Count: %{y}<br>Columns: %{customdata[0]}<extra></extra>",
            marker_color=_TYPE_COLORS,
            marker_line={"color": "rgba(38, 52, 73, 0.8)", "width": 1},
        )
    )
    figure.update_layout(
        title="Dataset Composition",
        xaxis_title="Pandas-inferred type",
        yaxis_title="Column count",
        yaxis={"rangemode": "tozero", "dtick": 1, "gridcolor": "rgba(38, 52, 73, 0.6)"},
        xaxis={"tickfont": {"family": _FONT_FAMILY, "color": "#94A3B8", "size": 11}},
        height=315,
        margin={"l": 48, "r": 16, "t": 54, "b": 60},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": _FONT_FAMILY, "color": "#F1F5F9"},
        hoverlabel={"bgcolor": "#162033", "bordercolor": "#263449", "font": {"family": _FONT_FAMILY, "color": "#F1F5F9"}},
        showlegend=False,
    )
    figure.update_xaxes(showgrid=False)
    figure.update_yaxes(gridcolor="rgba(38, 52, 73, 0.6)")
    return figure


def issue_counts(context: DatasetContext) -> dict[str, int]:
    """Return the two issue counts used by the conditional issue chart."""

    missing = analyze_missing_values(context).metrics
    duplicates = detect_duplicates(context, columns=None).metrics
    return {
        "Missing cells": int(sum(missing.get("missing_counts", {}).values())),
        "Duplicate rows": int(duplicates.get("duplicate_row_count", 0)),
    }


def issue_breakdown_figure(counts: dict[str, int]) -> go.Figure | None:
    """Build a clean-legend donut only when both issue categories are positive."""

    labels = [label for label in ("Missing cells", "Duplicate rows") if counts.get(label, 0) > 0]
    if len(labels) < 2:
        return None
    values = [int(counts[label]) for label in labels]
    figure = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.5,
            textinfo="value",
            textfont={"family": _FONT_FAMILY, "color": "#F1F5F9", "size": 13},
            hovertemplate="<b>%{label}</b>: %{value}<extra></extra>",
            marker_colors=["#38BDF8", "#F59E0B"],
            marker_line={"color": "#111827", "width": 2},
            sort=False,
        )
    )
    figure.update_layout(
        title="Breakdown of Detected Issues",
        height=315,
        margin={"l": 16, "r": 16, "t": 54, "b": 24},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": _FONT_FAMILY, "color": "#F1F5F9"},
        hoverlabel={"bgcolor": "#162033", "bordercolor": "#263449", "font": {"family": _FONT_FAMILY, "color": "#F1F5F9"}},
        showlegend=True,
        legend={"orientation": "h", "y": -0.05, "x": 0.5, "xanchor": "center", "font": {"family": _FONT_FAMILY, "color": "#94A3B8", "size": 11}},
    )
    return figure
