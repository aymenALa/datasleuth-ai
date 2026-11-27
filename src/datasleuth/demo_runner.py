"""Guided deterministic investigation workflow (no LLM / no API key required)."""

from __future__ import annotations

from typing import Any

from pandas.api.types import is_bool_dtype, is_numeric_dtype

from .agent import execute_tool
from .config import MAX_AGENT_TOOL_CALLS
from .models import DatasetContext, InvestigationResult, InvestigationState, InvestigationStep


def run_guided_investigation(
    context: DatasetContext,
    goal: str,
    max_tool_calls: int = MAX_AGENT_TOOL_CALLS,
) -> InvestigationResult:
    """Execute a bounded, predefined deterministic tool sequence without any LLM call.

    This runner uses the exact same allowlisted local tools and produces a standard
    ``InvestigationResult`` for ``build_report()``, while keeping ``model_response``
    and ``summary`` as ``None`` so no AI reasoning is fabricated.
    """

    baseline: list[tuple[str, dict[str, Any]]] = [
        ("profile_dataset", {}),
        ("analyze_missing_values", {}),
        ("detect_duplicates", {"columns": None}),
    ]
    state = InvestigationState(
        dataset_id=context.dataset_id,
        goal=goal,
        required_tools=[name for name, _ in baseline],
    )

    for index, (name, arguments) in enumerate(baseline, start=1):
        result = execute_tool(context, name, arguments)
        state.baseline_tool_calls += 1
        state.steps.append(InvestigationStep(name, arguments, result, f"guided-baseline-{index}"))
        state.observations.append(result)

    # Bounded deterministic follow-up: inspect candidate mixed-type object columns
    # and check numeric columns for IQR outlier candidates.
    dataframe = context.dataframe
    follow_ups: list[tuple[str, dict[str, Any]]] = []

    non_numeric_cols = [
        str(col)
        for col in dataframe.columns
        if not (is_numeric_dtype(dataframe[col]) and not is_bool_dtype(dataframe[col]))
        and not is_bool_dtype(dataframe[col])
    ]
    numeric_cols = [
        str(col)
        for col in dataframe.columns
        if is_numeric_dtype(dataframe[col]) and not is_bool_dtype(dataframe[col])
    ]

    # Prioritize object columns that have some digit-like values (mixed-type candidates)
    prioritized_non_numeric = sorted(
        non_numeric_cols,
        key=lambda c: _looks_mixed_candidate(dataframe[c]),
        reverse=True,
    )
    for col in prioritized_non_numeric[:2]:
        follow_ups.append(("inspect_column", {"column": col}))

    for col in numeric_cols[:3]:
        follow_ups.append(("detect_outliers", {"column": col, "method": "iqr"}))

    budget = max(0, max_tool_calls - state.baseline_tool_calls)
    for index, (name, arguments) in enumerate(follow_ups[:budget], start=1):
        result = execute_tool(context, name, arguments)
        state.tool_calls += 1
        state.steps.append(InvestigationStep(name, arguments, result, f"guided-step-{index}"))
        state.observations.append(result)

    state.completed = True
    return InvestigationResult(
        dataset_id=state.dataset_id,
        goal=state.goal,
        status="complete",
        summary=None,
        steps=state.steps,
        observations=state.observations,
        model_response=None,
        error=None,
        usage={},
        required_tools=state.required_tools,
        baseline_tool_calls=state.baseline_tool_calls,
    )


def _looks_mixed_candidate(series: Any) -> int:
    """Return a deterministic priority score for non-numeric columns that may hold numbers."""

    non_null = series.dropna()
    if len(non_null) == 0:
        return 0
    sample = non_null.astype(str).head(50)
    digit_hits = sum(1 for val in sample if any(ch.isdigit() for ch in val))
    if 0 < digit_hits < len(sample):
        return 2
    if digit_hits > 0:
        return 1
    return 0
