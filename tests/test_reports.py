"""Tests for structured and Markdown investigation reports."""

import json

import pandas as pd

from datasleuth.models import DatasetContext, InvestigationResult, InvestigationStep
from datasleuth.reports import build_report, cleaning_recommendations, report_to_json, report_to_markdown


def context():
    dataframe = pd.DataFrame({"value": [1, 2, 100], "name": ["Ada", "Ada", "Grace"]})
    return DatasetContext("d1", "sample.csv", dataframe, 3, 2, ["value", "name"])


def investigation():
    return InvestigationResult(
        dataset_id="d1", goal="Find unusual values", status="complete",
        summary="The model reviewed the evidence.",
        steps=[InvestigationStep(
            "detect_outliers", {"column": "value"},
            {"tool_name": "detect_outliers", "status": "success",
             "metrics": {"column": "value", "outlier_candidate_count": 1},
             "evidence": [{"row_position": 2, "value": 100}], "warnings": []},
            "call-1"
        )],
        usage={"total_tokens": 8},
    )


def investigation_with_step(tool_name, metrics, parameters=None, evidence=None):
    return InvestigationResult(
        dataset_id="d1", goal="Analyze quality", status="complete", summary=None,
        steps=[InvestigationStep(
            tool_name, parameters or {},
            {"tool_name": tool_name, "status": "success", "metrics": metrics,
             "parameters": parameters or {}, "evidence": evidence or [], "warnings": []},
            "call-1"
        )],
    )


def test_report_contains_metadata_findings_recommendations_trace_and_usage():
    dataset = context()
    before = dataset.dataframe.copy(deep=True)
    report = build_report(dataset, investigation())

    assert report["dataset"]["row_count"] == 3
    assert report["completion_status"] == "validated"
    assert report["outcome"] == "issues_found"
    assert len(report["verified_findings"]) == 1
    assert report["cleaning_recommendations"][0]["suggested_action"]
    assert report["investigation_trace"][0]["call_id"] == "call-1"
    assert report["token_usage"] == {"total_tokens": 8}
    pd.testing.assert_frame_equal(dataset.dataframe, before)


def test_recommendations_are_conservative_and_do_not_modify_dataframe():
    validation = {"findings": [
        {"title": "Missing values in name", "classification": "measured_fact",
         "metric_path": "missing_counts.name", "columns": ["name"],
         "evidence": [{"observed_value": 1}]},
        {"title": "Outlier candidates", "classification": "statistical_candidate",
         "metric_path": "outlier_candidate_count", "columns": ["value"],
         "evidence": [{"observed_value": 1}]},
    ]}
    dataset = context()
    before = dataset.dataframe.copy(deep=True)
    recommendations = cleaning_recommendations(validation)

    assert len(recommendations) == 2
    assert all(item["risks_or_conditions"] for item in recommendations)
    assert "not automatically" in recommendations[1]["risks_or_conditions"]
    pd.testing.assert_frame_equal(dataset.dataframe, before)


def test_missing_recommendation_uses_verified_percentage_and_follow_up():
    report = build_report(
        context(),
        investigation_with_step(
            "analyze_missing_values",
            {"missing_counts": {"name": 2}, "missing_percentages": {"name": 50.0}},
        ),
    )
    recommendation = report["cleaning_recommendations"][0]

    assert "50.00%" in recommendation["potential_analytical_impact"]
    assert recommendation["evidence_classification"] == "measured_fact"
    assert "group" in recommendation["suggested_follow_up"]
    assert "mean/median" in recommendation["risks_and_assumptions"]


def test_full_row_and_key_duplicate_recommendations_preserve_tool_columns():
    full = build_report(
        context(),
        investigation_with_step(
            "detect_duplicates",
            {"duplicate_row_count": 1, "duplicate_percentage": 33.33, "duplicate_group_row_count": 2},
            parameters={"columns": ["value", "name"]},
        ),
    )
    keyed = build_report(
        context(),
        investigation_with_step(
            "detect_duplicates",
            {"duplicate_row_count": 1, "duplicate_percentage": 33.33, "duplicate_group_row_count": 2},
            parameters={"columns": ["name"]},
        ),
    )

    assert full["cleaning_recommendations"][0]["columns"] == ["value", "name"]
    assert keyed["cleaning_recommendations"][0]["columns"] == ["name"]
    assert "33.33" in keyed["cleaning_recommendations"][0]["potential_analytical_impact"]
    assert "deduplication key" in keyed["cleaning_recommendations"][0]["suggested_action"]


def test_mixed_type_recommendation_reports_conversion_evidence():
    report = build_report(
        context(),
        investigation_with_step(
            "inspect_column",
            {"column": "value", "mixed_types_detected": True,
             "observed_python_types": {"int": 2, "str": 1},
             "numeric_conversion_failure_count": 1},
        ),
    )
    recommendation = report["cleaning_recommendations"][0]

    assert "1 non-null" in recommendation["potential_analytical_impact"]
    assert "explicit target type" in recommendation["conditional_treatment_options"]
    assert recommendation["confidence"] == "context_required"


def test_insufficient_evidence_and_clean_datasets_are_distinguished():
    incomplete = build_report(
        context(), InvestigationResult("d1", "Analyze", "incomplete", None)
    )
    clean = build_report(
        context(), InvestigationResult("d1", "Analyze", "complete", "No issues found")
    )

    assert incomplete["outcome"] == "investigation_incomplete"
    assert incomplete["cleaning_recommendations"][0]["evidence_classification"] == "insufficient_evidence"
    assert clean["outcome"] == "no_issue_found_in_executed_checks"
    assert clean["cleaning_recommendations"] == []


def test_json_and_markdown_exports_are_strict_and_escape_untrusted_text():
    malicious_context = DatasetContext(
        "d1", "evil`name[1].csv<script>", pd.DataFrame({"value": [1]}), 1, 1, ["value"]
    )
    report = build_report(malicious_context, investigation())

    serialized = report_to_json(report)
    markdown = report_to_markdown(report)

    assert json.loads(serialized)["dataset"]["filename"] == "evil`name[1].csv<script>"
    assert "evil\\`name\\[1\\].csv&lt;script&gt;" in markdown
    assert "DataFrame" not in serialized


def test_failed_report_is_explicit_and_does_not_claim_cleanliness():
    failed = InvestigationResult("d1", "Investigate", "error", None, error="Unavailable")

    report = build_report(context(), failed)

    assert report["completion_status"] == "failed"
    assert report["outcome"] == "investigation_failed"
    assert report["verified_findings"] == []
    assert report["error"] == "Unavailable"
