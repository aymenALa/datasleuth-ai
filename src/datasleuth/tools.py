"""Deterministic, read-only data-quality analysis tools."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype

from .models import DatasetContext, ToolResult

_MAX_EVIDENCE = 10
_MAX_COMMON_VALUES = 10


def _safe_value(value: Any) -> Any:
    """Convert Pandas/NumPy values into bounded JSON-compatible values."""

    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, np.generic):
        return _safe_value(value.item())
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (np.integer, np.bool_)):
        return value.item()
    if isinstance(value, (pd.Timestamp, pd.Timedelta)):
        return value.isoformat()
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _safe_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe_value(item) for item in value]
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def _result(
    tool_name: str,
    parameters: dict[str, Any] | None = None,
    metrics: dict[str, Any] | None = None,
    evidence: list[Any] | None = None,
    warnings: list[str] | None = None,
) -> ToolResult:
    return ToolResult(
        tool_name=tool_name,
        status="success",
        parameters=_safe_value(parameters or {}),
        metrics=_safe_value(metrics or {}),
        evidence=_safe_value(evidence or []),
        warnings=warnings or [],
    )


def _error(tool_name: str, message: str, parameters: dict[str, Any] | None = None) -> ToolResult:
    return ToolResult(
        tool_name=tool_name,
        status="error",
        parameters=_safe_value(parameters or {}),
        error=message,
    )


def _common_values(series: pd.Series) -> list[dict[str, Any]]:
    counts = series.value_counts(dropna=False).head(_MAX_COMMON_VALUES)
    return [
        {"value": _safe_value(value), "count": int(count)}
        for value, count in counts.items()
    ]


def _numeric_statistics(series: pd.Series) -> dict[str, Any]:
    finite_series = series.replace([np.inf, -np.inf], np.nan)
    stats = finite_series.describe()
    names = ("count", "mean", "std", "min", "25%", "50%", "75%", "max")
    return {name: _safe_value(stats[name]) for name in names if name in stats}


def _validate_column(context: DatasetContext, column: str, tool_name: str) -> bool | ToolResult:
    if column not in context.dataframe.columns:
        return _error(tool_name, f"Column '{column}' does not exist", {"column": column})
    return True


def profile_dataset(context: DatasetContext) -> ToolResult:
    """Return bounded structural, missingness, type, and summary metrics."""

    dataframe = context.dataframe
    per_column: dict[str, Any] = {}
    numerical_statistics: dict[str, Any] = {}
    categorical_cardinality: dict[str, Any] = {}

    for column in dataframe.columns:
        series = dataframe[column]
        dtype = str(series.dtype)
        per_column[column] = {
            "inferred_dtype": dtype,
            "non_null_count": int(series.notna().sum()),
            "missing_count": int(series.isna().sum()),
        }
        if is_numeric_dtype(series) and not is_bool_dtype(series):
            numerical_statistics[column] = _numeric_statistics(series)
        else:
            categorical_cardinality[column] = {
                "unique_count": int(series.nunique(dropna=True)),
                "common_values": _common_values(series),
            }

    return _result(
        "profile_dataset",
        metrics={
            "row_count": int(len(dataframe)),
            "column_count": int(len(dataframe.columns)),
            "column_names": [str(column) for column in dataframe.columns],
            "missing_value_count": int(dataframe.isna().sum().sum()),
            "per_column": per_column,
            "numerical_statistics": numerical_statistics,
            "categorical_cardinality": categorical_cardinality,
        },
    )


def analyze_missing_values(context: DatasetContext) -> ToolResult:
    """Summarize Pandas-parsed missingness without changing the DataFrame."""

    dataframe = context.dataframe
    missing = dataframe.isna()
    row_count = len(dataframe)
    missing_counts = {str(column): int(value) for column, value in missing.sum().items()}
    missing_percentages = {
        column: (count / row_count * 100 if row_count else 0.0)
        for column, count in missing_counts.items()
    }
    affected_positions = np.flatnonzero(missing.any(axis=1)).tolist()[:_MAX_EVIDENCE]
    affected_row_count = int(missing.any(axis=1).sum())

    return _result(
        "analyze_missing_values",
        metrics={
            "missing_counts": missing_counts,
            "missing_percentages": missing_percentages,
            "rows_with_missing_count": affected_row_count,
            "rows_with_missing_percentage": (
                affected_row_count / row_count * 100 if row_count else 0.0
            ),
            "fully_empty_columns": [
                str(column) for column, count in missing_counts.items() if count == row_count
            ],
            "affected_row_positions": affected_positions,
        },
        warnings=["Missingness follows Pandas' existing CSV parsing semantics."],
    )


def detect_duplicates(
    context: DatasetContext, columns: list[str] | tuple[str, ...] | None = None
) -> ToolResult:
    """Find duplicate groups, counting redundant occurrences in the main metric."""

    dataframe = context.dataframe
    selected = list(dataframe.columns) if columns is None else list(columns)
    invalid = [column for column in selected if column not in dataframe.columns]
    if invalid or not selected:
        return _error(
            "detect_duplicates",
            f"Unknown or empty duplicate columns: {invalid or selected}",
            {"columns": selected},
        )

    duplicate_groups = dataframe.duplicated(subset=selected, keep=False)
    redundant = dataframe.duplicated(subset=selected, keep="first")
    examples = []
    duplicate_positions = np.flatnonzero(duplicate_groups.to_numpy())[:_MAX_EVIDENCE]
    for position in duplicate_positions:
        row = dataframe.iloc[position]
        record = {"row_position": int(position), **row[selected].to_dict()}
        examples.append(_safe_value(record))

    duplicate_row_count = int(redundant.sum())
    group_row_count = int(duplicate_groups.sum())
    total = len(dataframe)
    return _result(
        "detect_duplicates",
        parameters={"columns": [str(column) for column in selected]},
        metrics={
            "duplicate_row_count": duplicate_row_count,
            "duplicate_percentage": duplicate_row_count / total * 100 if total else 0.0,
            "duplicate_group_row_count": group_row_count,
            "total_row_count": total,
        },
        evidence=examples,
        warnings=[
            "duplicate_row_count counts redundant occurrences after the first row; "
            "duplicate_group_row_count counts every row in duplicate groups.",
            "Null equality follows Pandas duplicated() behavior.",
        ],
    )


def inspect_column(context: DatasetContext, column: str) -> ToolResult:
    """Inspect one column without applying semantic validation or conversion."""

    valid = _validate_column(context, column, "inspect_column")
    if valid is not True:
        return valid
    series = context.dataframe[column]
    non_null = series.dropna()
    metrics: dict[str, Any] = {
        "column": column,
        "inferred_dtype": str(series.dtype),
        "missing_count": int(series.isna().sum()),
        "non_missing_count": int(series.notna().sum()),
        "unique_value_count": int(series.nunique(dropna=True)),
        "common_values": _common_values(series),
    }
    warnings = []
    if is_numeric_dtype(series) and not is_bool_dtype(series):
        metrics["numerical_statistics"] = _numeric_statistics(series)
    else:
        type_counts = non_null.map(lambda value: type(value).__name__).value_counts()
        metrics["observed_python_types"] = {
            str(name): int(count) for name, count in type_counts.items()
        }
        metrics["mixed_types_detected"] = len(type_counts) > 1
        numeric_probe = pd.to_numeric(non_null, errors="coerce")
        metrics["numeric_conversion_failure_count"] = int(numeric_probe.isna().sum())
        warnings.append("Inferred dtype is descriptive; no domain-specific validity rules were applied.")
    return _result("inspect_column", {"column": column}, metrics=metrics, warnings=warnings)


def detect_outliers(
    context: DatasetContext, column: str, method: str = "iqr"
) -> ToolResult:
    """Return conservative IQR outlier candidates for a numeric column."""

    if method != "iqr":
        return _error("detect_outliers", f"Unsupported outlier method: {method}", {"column": column, "method": method})
    valid = _validate_column(context, column, "detect_outliers")
    if valid is not True:
        return valid
    series = context.dataframe[column]
    if not is_numeric_dtype(series) or is_bool_dtype(series):
        return _error(
            "detect_outliers",
            f"Column '{column}' is not an appropriate numeric column",
            {"column": column, "method": method},
        )

    numeric = pd.to_numeric(series, errors="coerce")
    eligible = numeric.notna() & np.isfinite(numeric)
    values = numeric[eligible]
    if len(values) < 4:
        return _error(
            "detect_outliers",
            "At least 4 finite numeric observations are required",
            {"column": column, "method": method},
        )

    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    warnings = ["Outlier candidates are statistical signals, not confirmed data-quality errors."]
    if iqr == 0:
        candidates = pd.Series(False, index=values.index)
        warnings.append("IQR is zero; no candidates were flagged conservatively.")
    else:
        candidates = (values < lower) | (values > upper)
    eligible_positions = np.flatnonzero(eligible.to_numpy())
    candidate_offsets = np.flatnonzero(candidates.to_numpy())[:_MAX_EVIDENCE]
    examples = [
        {
            "row_position": int(eligible_positions[offset]),
            "value": _safe_value(values.iloc[offset]),
        }
        for offset in candidate_offsets
    ]
    count = int(candidates.sum())
    return _result(
        "detect_outliers",
        {"column": column, "method": method},
        metrics={
            "column": column,
            "method": method,
            "q1": q1,
            "q3": q3,
            "iqr": iqr,
            "lower_bound": lower,
            "upper_bound": upper,
            "eligible_numeric_count": int(len(values)),
            "outlier_candidate_count": count,
            "outlier_candidate_percentage": count / len(values) * 100,
        },
        evidence=examples,
        warnings=warnings,
    )
