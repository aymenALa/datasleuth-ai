"""Tests for deterministic finding validation."""

import pandas as pd

from datasleuth.models import DatasetContext, InvestigationResult, InvestigationStep
from datasleuth.validator import validate_finding, validate_investigation


def investigation(status="complete", steps=None, summary=None, error=None):
    return InvestigationResult(
        dataset_id="d1", goal="Find issues", status=status, summary=summary,
        steps=steps or [], model_response=summary, error=error, usage={"total_tokens": 4}
    )


def outlier_step():
    return InvestigationStep(
        "detect_outliers", {"column": "value"},
        {"tool_name": "detect_outliers", "status": "success",
         "metrics": {"column": "value", "outlier_candidate_count": 1},
         "evidence": [{"row_position": 2, "value": 100}],
         "warnings": ["Outlier candidates are statistical signals."]},
        "call-1",
    )


def duplicate_step(status="success", count=0):
    return InvestigationStep(
        "detect_duplicates", {},
        {"tool_name": "detect_duplicates", "status": status,
         "metrics": {"duplicate_row_count": count, "duplicate_percentage": 0.0},
         "parameters": {"columns": ["value"]}, "evidence": [], "warnings": []},
        "duplicate-call",
    )


def test_supported_numerical_finding_is_validated_against_tool_metric():
    result = validate_finding(
        {"tool_name": "detect_outliers", "metric_path": "outlier_candidate_count",
         "value": 1, "classification": "statistical_candidate",
         "evidence": [{"row_position": 2, "value": 100}]},
        investigation(steps=[outlier_step()]),
    )

    assert result["status"] == "validated"
    assert result["finding"]["value"] == 1


def test_unsupported_or_mismatched_numerical_claim_is_rejected():
    current = investigation(steps=[outlier_step()])
    missing_metric = validate_finding(
        {"tool_name": "detect_outliers", "metric_path": "made_up", "value": 99,
         "classification": "measured_fact", "evidence": [1]}, current
    )
    mismatch = validate_finding(
        {"tool_name": "detect_outliers", "metric_path": "outlier_candidate_count", "value": 99,
         "classification": "measured_fact", "evidence": [1]}, current
    )

    assert missing_metric["status"] == "invalid"
    assert mismatch["status"] == "invalid"


def test_invalid_tool_reference_and_missing_evidence_are_rejected():
    invalid_trace = investigation(steps=[
        InvestigationStep("not_a_tool", {}, {"tool_name": "not_a_tool", "status": "success"}, "bad")
    ])
    validation = validate_investigation(invalid_trace)
    no_evidence = validate_finding(
        {"tool_name": "detect_outliers", "metric_path": "outlier_candidate_count", "value": 1,
         "classification": "measured_fact"}, investigation(steps=[outlier_step()])
    )

    assert validation["status"] == "invalid"
    assert validation["errors"]
    assert no_evidence["status"] == "invalid"


def test_empty_complete_investigation_is_not_called_clean():
    validation = validate_investigation(investigation())

    assert validation["status"] == "validated"
    assert validation["findings"] == []
    assert any("does not establish" in warning for warning in validation["warnings"])


def test_incomplete_and_failed_investigations_are_distinguished():
    incomplete = validate_investigation(investigation("incomplete", [outlier_step()]))
    failed = validate_investigation(investigation("error", error="Groq unavailable"))

    assert incomplete["status"] == "incomplete"
    assert failed["status"] == "failed"
    assert failed["warnings"] == []


def test_successful_duplicate_check_with_no_duplicates_is_validated_cleanly():
    validation = validate_investigation(investigation(steps=[duplicate_step()]))

    assert validation["status"] == "validated"
    assert validation["findings"] == []
    assert not any("did not produce" in warning for warning in validation["warnings"])


def test_successful_duplicate_check_with_duplicates_produces_a_finding():
    validation = validate_investigation(investigation(steps=[duplicate_step(count=2)]))

    assert validation["status"] == "validated"
    assert validation["findings"][0]["metric_path"] == "duplicate_row_count"
    assert validation["findings"][0]["value"] == 2


def test_failed_duplicate_check_makes_coverage_incomplete_but_preserves_findings():
    validation = validate_investigation(
        investigation(status="complete", steps=[outlier_step(), duplicate_step(status="error")])
    )

    assert validation["status"] == "incomplete"
    assert any(finding["tool_name"] == "detect_outliers" for finding in validation["findings"])
    assert any("detect_duplicates failed" in warning for warning in validation["warnings"])
    assert not any("No issue found" in warning for warning in validation["warnings"])


def test_missing_required_duplicate_observation_makes_coverage_incomplete():
    current = investigation(status="complete", steps=[outlier_step()])
    current.required_tools = ["detect_duplicates"]

    validation = validate_investigation(current)

    assert validation["status"] == "incomplete"
    assert any("Required tool detect_duplicates" in warning for warning in validation["warnings"])
    assert any(finding["tool_name"] == "detect_outliers" for finding in validation["findings"])


def test_baseline_coverage_reports_zero_missing_and_duplicate_checks():
    current = investigation(steps=[
        InvestigationStep(
            "analyze_missing_values", {},
            {"tool_name": "analyze_missing_values", "status": "success", "metrics": {"missing_counts": {"a": 0, "b": 0}}}, "baseline-2"
        ),
        InvestigationStep(
            "detect_duplicates", {"columns": ["a", "b"]},
            {"tool_name": "detect_duplicates", "status": "success", "metrics": {"duplicate_row_count": 0}}, "baseline-3"
        ),
    ])
    current.required_tools = ["analyze_missing_values", "detect_duplicates"]

    validation = validate_investigation(current)

    assert validation["check_coverage"] == [
        {"tool_name": "analyze_missing_values", "status": "succeeded", "missing_value_count": 0},
        {"tool_name": "detect_duplicates", "status": "succeeded", "duplicate_row_count": 0},
    ]
    assert "Missing-value check completed: 0 missing values." in validation["warnings"]
    assert "Exact-duplicate check completed: 0 redundant rows." in validation["warnings"]


def test_failed_baseline_check_is_failed_not_successful_coverage():
    current = investigation(steps=[
        InvestigationStep(
            "detect_duplicates", {"columns": None},
            {"tool_name": "detect_duplicates", "status": "error", "error": "failed"}, "baseline-3"
        ),
    ])
    current.required_tools = ["profile_dataset", "analyze_missing_values", "detect_duplicates"]

    validation = validate_investigation(current)

    assert validation["status"] == "incomplete"
    statuses = {item["tool_name"]: item["status"] for item in validation["check_coverage"]}
    assert statuses == {"profile_dataset": "not_executed", "analyze_missing_values": "not_executed", "detect_duplicates": "failed"}
