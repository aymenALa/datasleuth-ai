"""Focused regression tests for DataSleuth AI modular UI architecture and view models."""

import pandas as pd
import pytest

from datasleuth.models import DatasetContext
from datasleuth.ui.formatters import (
    format_percentage,
    format_count,
    format_classification_label,
    format_confidence_label,
    format_observed_label,
    format_precision_in_text,
    sanitize_model_markdown,
)
from datasleuth.ui.view_models import (
    build_dashboard_metrics,
    build_column_summaries,
    build_finding_view_models,
)


def _make_context(df: pd.DataFrame, filename: str = "test.csv") -> DatasetContext:
    return DatasetContext(
        dataset_id="test-id",
        filename=filename,
        dataframe=df,
        row_count=len(df),
        column_count=len(df.columns),
        column_names=[str(c) for c in df.columns],
    )


def test_format_percentage_handles_none_and_floats():
    assert format_percentage(None) == "N/A"
    assert format_percentage(12.3456) == "12.35%"
    assert format_percentage(0) == "0.00%"
    assert format_percentage(100.0) == "100.00%"


def test_format_count_handles_integers_and_none():
    assert format_count(None) == "N/A"
    assert format_count(1000) == "1,000"
    assert format_count(0) == "0"
    assert format_count(1234567) == "1,234,567"


def test_format_classification_label():
    assert format_classification_label("measured_fact") == "Measured fact"
    assert format_classification_label("statistical_candidate") == "Statistical candidate"
    assert format_classification_label("interpretation") == "Model interpretation"
    assert format_classification_label("custom_type") == "Custom Type"
    assert format_classification_label(None) == "Observation"


def test_format_confidence_label():
    assert format_confidence_label("high") == "High confidence"
    assert format_confidence_label("medium") == "Medium confidence"
    assert format_confidence_label(None) == "Context required"


def test_format_observed_label():
    assert format_observed_label("measured_fact", "missing_counts.score", 3) == "3 missing cells"
    assert format_observed_label("measured_fact", "missing_counts.score", 1) == "1 missing cell"
    assert format_observed_label("measured_fact", "duplicate_row_count", 2) == "2 redundant duplicate rows"
    assert format_observed_label("measured_fact", "duplicate_row_count", 1) == "1 redundant duplicate row"
    assert format_observed_label("statistical_candidate", "outliers", 5) == "5 outlier candidates"


def test_format_precision_in_text_rounds_decimals():
    raw_text = "The measured redundant-row rate is 16.666666666666664%; 25.12345% missing."
    formatted = format_precision_in_text(raw_text)
    assert "16.67%" in formatted
    assert "25.12%" in formatted


def test_sanitize_model_markdown_normalizes_br_and_strips_scripts():
    raw = "Header<br>Cell<br />Value<script>alert(1)</script>"
    clean = sanitize_model_markdown(raw)
    assert "<script>" not in clean
    assert "alert" not in clean
    assert "<br" not in clean
    assert "Header" in clean
    assert "Cell" in clean


def test_dashboard_metrics_computes_exact_rates():
    df = pd.DataFrame({
        "a": [1, None, 3, 4],
        "b": ["x", "y", "x", "x"],
    })
    ctx = _make_context(df)
    metrics = build_dashboard_metrics(ctx, report=None)

    assert metrics.row_count == 4
    assert metrics.column_count == 2
    assert metrics.total_cells == 8
    assert metrics.missing_cells == 1
    assert metrics.missing_cell_rate == pytest.approx(12.5)
    assert metrics.is_investigated is False
    assert metrics.findings_count is None


def test_dashboard_metrics_handles_empty_dataset():
    df = pd.DataFrame()
    ctx = _make_context(df)
    metrics = build_dashboard_metrics(ctx, report=None)

    assert metrics.row_count == 0
    assert metrics.column_count == 0
    assert metrics.total_cells == 0
    assert metrics.missing_cell_rate == 0.0
    assert metrics.duplicate_row_rate == 0.0


def test_column_summaries_completeness():
    df = pd.DataFrame({
        "numeric": [10, 20, None, 40],
        "text": ["a", "b", "c", "d"],
    })
    ctx = _make_context(df)
    summaries = build_column_summaries(ctx)

    assert len(summaries) == 2
    assert summaries[0].name == "numeric"
    assert summaries[0].missing_count == 1
    assert summaries[0].non_missing_count == 3
    assert summaries[0].completeness_percentage == pytest.approx(75.0)

    assert summaries[1].name == "text"
    assert summaries[1].missing_count == 0
    assert summaries[1].completeness_percentage == pytest.approx(100.0)


def test_build_finding_view_models():
    report = {
        "verified_findings": [
            {
                "finding_id": "f_1",
                "title": "Missing values in col",
                "classification": "measured_fact",
                "confidence": "high",
                "tool_name": "analyze_missing_values",
                "metric_path": "missing_counts.col",
                "value": 2,
                "columns": ["col"],
                "evidence": [
                    {
                        "examples": [
                            {"missing_count": 2, "missing_percentage": 20.0}
                        ]
                    }
                ],
            }
        ]
    }
    view_models = build_finding_view_models(report)
    assert len(view_models) == 1
    assert view_models[0].title == "Missing values in col"
    assert view_models[0].classification_label == "Measured fact"
    assert view_models[0].observed_label == "2 missing cells"
    assert "2 missing cells (20.00% of column)" in view_models[0].evidence_summary


def test_report_exports_json_and_markdown_validity():
    import json
    from datasleuth.models import InvestigationResult
    from datasleuth.reports import build_report, report_to_json, report_to_markdown

    df = pd.DataFrame({"name": ["Ada", "Grace"], "score": [10, 20]})
    context = _make_context(df, "sample.csv")
    inv = InvestigationResult("test-id", "Verify quality", "complete", "Interpretation summary")
    report = build_report(context, inv)

    json_str = report_to_json(report)
    parsed = json.loads(json_str)
    assert parsed["dataset"]["filename"] == "sample.csv"
    assert parsed["completion_status"] == "validated"

    md_str = report_to_markdown(report)
    assert "# DataSleuth AI Investigation Report" in md_str
    assert "sample.csv" in md_str
    assert "Verify quality" in md_str
