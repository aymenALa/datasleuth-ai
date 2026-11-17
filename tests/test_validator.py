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
