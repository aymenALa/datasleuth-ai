"""Deterministic validation of investigation observations and findings."""

from __future__ import annotations

from numbers import Number
from typing import Any

from .models import InvestigationResult

_TOOLS = {
    "profile_dataset",
    "analyze_missing_values",
    "detect_duplicates",
    "inspect_column",
    "detect_outliers",
}
_CLASSIFICATIONS = {"measured_fact", "statistical_candidate", "interpretation"}


def validate_finding(finding: dict[str, Any], investigation: InvestigationResult) -> dict[str, Any]:
    """Validate one finding against a directly executed tool metric.

    Numerical claims are accepted only when ``tool_name`` and ``metric_path``
    resolve to an observed value in a successful investigation step.
    """

    required = {"tool_name", "metric_path", "value", "classification"}
    missing = sorted(required - set(finding))
    if missing:
        return {"status": "invalid", "errors": [f"Missing finding fields: {', '.join(missing)}"]}
    if finding["classification"] not in _CLASSIFICATIONS:
        return {"status": "invalid", "errors": ["Unsupported finding classification"]}

    observed = _find_metric(investigation, finding["tool_name"], finding["metric_path"])
    if observed is _MISSING:
        return {"status": "invalid", "errors": ["Finding metric was not observed by the referenced tool"]}
    if isinstance(finding["value"], Number) and not _same_number(finding["value"], observed):
        return {"status": "invalid", "errors": ["Reported numerical value does not match tool observation"]}
    if "evidence" not in finding or not finding["evidence"]:
        return {"status": "invalid", "errors": ["Finding must include evidence"]}

    return {
        "status": "validated",
        "finding": {
            "finding_id": str(finding.get("finding_id", f"{finding['tool_name']}:{finding['metric_path']}")),
            "title": str(finding.get("title", "Validated observation")),
            "classification": finding["classification"],
            "tool_name": finding["tool_name"],
            "metric_path": finding["metric_path"],
            "value": observed,
            "columns": [str(column) for column in finding.get("columns", [])],
            "evidence": finding["evidence"],
            "interpretation": str(finding.get("interpretation", "")),
            "warnings": [str(warning) for warning in finding.get("warnings", [])],
        },
    }


def validate_investigation(investigation: InvestigationResult) -> dict[str, Any]:
    """Validate successful tool observations and derive trustworthy findings."""

    errors: list[str] = []
    warnings: list[str] = []
    findings: list[dict[str, Any]] = []
    successful: dict[str, dict[str, Any]] = {}

    for step in investigation.steps:
        result = step.result
        if step.tool_name not in _TOOLS:
            errors.append(f"Unknown tool in investigation trace: {step.tool_name}")
            continue
        if result.get("tool_name") not in {None, step.tool_name}:
            errors.append(f"Tool result mismatch for call {step.call_id}")
            continue
        if result.get("status") != "success":
            warnings.append(f"Tool {step.tool_name} did not produce a successful observation")
            continue
        successful[step.tool_name] = result

    for tool_name, result in successful.items():
        findings.extend(_findings_from_tool(tool_name, result))

    if investigation.model_response:
        warnings.append("Model summary is an interpretation and was not used as numerical evidence.")
    if investigation.status == "error":
        status = "failed"
    elif investigation.status == "incomplete":
        status = "incomplete"
        warnings.append("Investigation was incomplete; findings cover executed checks only.")
    elif errors:
        status = "invalid"
    else:
        status = "validated"
    if not findings and status == "validated":
        warnings.append("No issue found in the executed checks; this does not establish that the entire dataset is clean.")

    return {
        "status": status,
        "dataset_id": investigation.dataset_id,
        "goal": investigation.goal,
        "findings": findings,
        "warnings": warnings,
        "errors": errors,
        "trace": _bounded_trace(investigation),
        "usage": dict(investigation.usage),
    }


def _findings_from_tool(tool_name: str, result: dict[str, Any]) -> list[dict[str, Any]]:
    metrics = result.get("metrics", {})
    findings: list[dict[str, Any]] = []

    def add(metric_path: str, value: Any, title: str, classification: str, columns: list[str], evidence: Any = None) -> None:
        if isinstance(value, Number) and value == 0:
            return
        findings.append({
            "finding_id": f"{tool_name}:{metric_path}",
            "title": title,
            "classification": classification,
            "tool_name": tool_name,
            "metric_path": metric_path,
            "value": value,
            "columns": columns,
            "evidence": [{"tool_name": tool_name, "metric_path": metric_path, "observed_value": value, "examples": evidence or []}],
            "confidence": (
                "high" if classification == "measured_fact"
                else "context_required" if classification == "interpretation"
                else "medium"
            ),
            "interpretation": "",
            "warnings": list(result.get("warnings", [])),
        })

    if tool_name == "analyze_missing_values":
        for column, count in metrics.get("missing_counts", {}).items():
            if count:
                add(
                    f"missing_counts.{column}", count, f"Missing values in {column}",
                    "measured_fact", [column],
                    [{"missing_count": count, "missing_percentage": metrics.get("missing_percentages", {}).get(column)}],
                )
    elif tool_name == "detect_duplicates":
        count = metrics.get("duplicate_row_count", 0)
        if count:
            add(
                "duplicate_row_count", count, "Redundant duplicate rows", "measured_fact",
                result.get("parameters", {}).get("columns", []),
                [{"duplicate_percentage": metrics.get("duplicate_percentage"),
                  "duplicate_group_row_count": metrics.get("duplicate_group_row_count"),
                  "examples": result.get("evidence", [])}],
            )
    elif tool_name == "inspect_column":
        if metrics.get("mixed_types_detected"):
            add(
                "mixed_types_detected", True, f"Mixed Python types in {metrics.get('column')}",
                "interpretation", [metrics.get("column")],
                [{"observed_python_types": metrics.get("observed_python_types", {}),
                  "numeric_conversion_failure_count": metrics.get("numeric_conversion_failure_count")}],
            )
    elif tool_name == "detect_outliers":
        count = metrics.get("outlier_candidate_count", 0)
        if count:
            add(
                "outlier_candidate_count", count,
                f"Statistical outlier candidates in {metrics.get('column')}",
                "statistical_candidate", [metrics.get("column")],
                [{"q1": metrics.get("q1"), "q3": metrics.get("q3"),
                  "iqr": metrics.get("iqr"), "lower_bound": metrics.get("lower_bound"),
                  "upper_bound": metrics.get("upper_bound"),
                  "outlier_candidate_percentage": metrics.get("outlier_candidate_percentage"),
                  "examples": result.get("evidence", [])}],
            )
    return findings


def _bounded_trace(investigation: InvestigationResult) -> list[dict[str, Any]]:
    return [
        {"tool_name": step.tool_name, "call_id": step.call_id, "arguments": step.arguments, "status": step.result.get("status")}
        for step in investigation.steps[:8]
    ]


class _Missing:
    pass


_MISSING = _Missing()


def _find_metric(investigation: InvestigationResult, tool_name: str, path: str) -> Any:
    for step in investigation.steps:
        if step.tool_name != tool_name or step.result.get("status") != "success":
            continue
        value: Any = step.result.get("metrics", {})
        for part in path.split("."):
            if not isinstance(value, dict) or part not in value:
                break
            value = value[part]
        else:
            return value
    return _MISSING


def _same_number(left: Number, right: Any) -> bool:
    try:
        return float(left) == float(right)
    except (TypeError, ValueError):
        return False
