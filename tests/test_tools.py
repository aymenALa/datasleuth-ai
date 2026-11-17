"""Tests for deterministic DataSleuth analysis tools."""

import json

import pandas as pd

from datasleuth.models import DatasetContext
from datasleuth.tools import (
    analyze_missing_values,
    detect_duplicates,
    detect_outliers,
    inspect_column,
    profile_dataset,
)


def make_context(dataframe: pd.DataFrame) -> DatasetContext:
    return DatasetContext(
        dataset_id="test-dataset",
        filename="synthetic.csv",
        dataframe=dataframe,
        row_count=len(dataframe),
        column_count=len(dataframe.columns),
        column_names=list(dataframe.columns),
    )


def assert_unchanged(dataframe, before):
    pd.testing.assert_frame_equal(dataframe, before)


def test_profile_dataset_returns_expected_metrics_and_json():
    dataframe = pd.DataFrame({"age": [20, 30, None], "city": ["Rabat", "Rabat", "Fes"]})
    context = make_context(dataframe)
    before = dataframe.copy(deep=True)

    result = profile_dataset(context)

    assert result.status == "success"
    assert result.metrics["row_count"] == 3
    assert result.metrics["column_count"] == 2
    assert result.metrics["missing_value_count"] == 1
    assert result.metrics["per_column"]["age"]["missing_count"] == 1
    assert result.metrics["numerical_statistics"]["age"]["mean"] == 25.0
    assert result.metrics["categorical_cardinality"]["city"]["unique_count"] == 2
    json.dumps(result.to_dict())
    assert_unchanged(dataframe, before)


def test_profile_dataset_handles_header_only_context():
    dataframe = pd.DataFrame(columns=["name", "score"])

    result = profile_dataset(make_context(dataframe))

    assert result.status == "success"
    assert result.metrics["row_count"] == 0
    assert result.metrics["column_count"] == 2
    assert result.metrics["missing_value_count"] == 0


def test_all_tools_handle_empty_dataset_without_crashing():
    context = make_context(pd.DataFrame(columns=["number", "label"]))

    results = [
        profile_dataset(context),
        analyze_missing_values(context),
        detect_duplicates(context),
        inspect_column(context, "number"),
        detect_outliers(context, "number"),
    ]

    assert all(result.status in {"success", "error"} for result in results)
    for result in results:
        json.dumps(result.to_dict())


def test_analyze_missing_values_reports_counts_percentages_and_empty_columns():
    dataframe = pd.DataFrame({"a": [1, None, 3, None], "b": [None] * 4, "c": [1, 2, 3, 4]})
    before = dataframe.copy(deep=True)

    result = analyze_missing_values(make_context(dataframe))

    metrics = result.metrics
    assert metrics["missing_counts"] == {"a": 2, "b": 4, "c": 0}
    assert metrics["missing_percentages"]["a"] == 50.0
    assert metrics["rows_with_missing_count"] == 4
    assert metrics["rows_with_missing_percentage"] == 100.0
    assert metrics["fully_empty_columns"] == ["b"]
    assert metrics["affected_row_positions"] == [0, 1, 2, 3]
    assert result.warnings
    assert_unchanged(dataframe, before)


def test_analyze_missing_values_handles_clean_data_and_empty_rows():
    dataframe = pd.DataFrame(columns=["a", "b"])

    result = analyze_missing_values(make_context(dataframe))

    assert result.metrics["rows_with_missing_count"] == 0
    assert result.metrics["rows_with_missing_percentage"] == 0.0
    assert result.metrics["fully_empty_columns"] == ["a", "b"]


def test_detect_duplicates_counts_redundant_full_rows_and_bounds_evidence():
    dataframe = pd.DataFrame({"id": [1, 1, 2, 3], "value": ["a", "a", "b", "c"]})
    before = dataframe.copy(deep=True)

    result = detect_duplicates(make_context(dataframe))

    assert result.status == "success"
    assert result.metrics["duplicate_row_count"] == 1
    assert result.metrics["duplicate_group_row_count"] == 2
    assert result.metrics["duplicate_percentage"] == 25.0
    assert result.parameters["columns"] == ["id", "value"]
    assert len(result.evidence) == 2
    assert_unchanged(dataframe, before)


def test_detect_duplicates_supports_key_based_duplicates():
    dataframe = pd.DataFrame({"email": ["a", "a", "b"], "version": [1, 2, 1]})

    result = detect_duplicates(make_context(dataframe), columns=["email"])

    assert result.metrics["duplicate_row_count"] == 1
    assert result.metrics["duplicate_group_row_count"] == 2
    assert result.parameters["columns"] == ["email"]


def test_duplicate_evidence_uses_row_positions_with_non_unique_index():
    dataframe = pd.DataFrame({"id": [1, 1, 2]}, index=[10, 10, 20])

    result = detect_duplicates(make_context(dataframe))

    assert [item["row_position"] for item in result.evidence] == [0, 1]


def test_detect_duplicates_reports_no_duplicates_and_invalid_columns():
    dataframe = pd.DataFrame({"id": [1, 2, 3]})

    clean = detect_duplicates(make_context(dataframe))
    invalid = detect_duplicates(make_context(dataframe), columns=["missing"])

    assert clean.metrics["duplicate_row_count"] == 0
    assert invalid.status == "error"
    assert "missing" in invalid.error


def test_inspect_column_reports_numeric_statistics():
    dataframe = pd.DataFrame({"score": [1, 2, 3, None]})

    result = inspect_column(make_context(dataframe), "score")

    assert result.status == "success"
    assert result.metrics["missing_count"] == 1
    assert result.metrics["non_missing_count"] == 3
    assert result.metrics["unique_value_count"] == 3
    assert result.metrics["numerical_statistics"]["mean"] == 2.0


def test_inspect_column_reports_categorical_and_mixed_types():
    categorical = inspect_column(
        make_context(pd.DataFrame({"city": ["Rabat", "Fes", "Rabat"]})), "city"
    )
    mixed = inspect_column(
        make_context(pd.DataFrame({"value": [1, "two", 3]})), "value"
    )

    assert categorical.metrics["unique_value_count"] == 2
    assert categorical.metrics["mixed_types_detected"] is False
    assert mixed.metrics["mixed_types_detected"] is True
    assert mixed.metrics["numeric_conversion_failure_count"] == 1


def test_inspect_column_rejects_invalid_column():
    result = inspect_column(make_context(pd.DataFrame({"a": [1]})), "missing")

    assert result.status == "error"
    assert result.error == "Column 'missing' does not exist"


def test_detect_outliers_returns_iqr_candidates_and_does_not_mutate():
    dataframe = pd.DataFrame({"value": [1, 2, 2, 3, 100]})
    before = dataframe.copy(deep=True)

    result = detect_outliers(make_context(dataframe), "value")

    assert result.status == "success"
    assert result.metrics["q1"] == 2.0
    assert result.metrics["q3"] == 3.0
    assert result.metrics["iqr"] == 1.0
    assert result.metrics["lower_bound"] == 0.5
    assert result.metrics["upper_bound"] == 4.5
    assert result.metrics["outlier_candidate_count"] == 1
    assert result.metrics["outlier_candidate_percentage"] == 20.0
    assert result.evidence == [{"row_position": 4, "value": 100}]
    assert_unchanged(dataframe, before)


def test_detect_outliers_handles_clean_and_constant_columns():
    clean = detect_outliers(make_context(pd.DataFrame({"value": [1, 2, 3, 4, 5]})), "value")
    constant = detect_outliers(make_context(pd.DataFrame({"value": [7, 7, 7, 7]})), "value")

    assert clean.metrics["outlier_candidate_count"] == 0
    assert constant.status == "success"
    assert constant.metrics["outlier_candidate_count"] == 0
    assert any("zero" in warning for warning in constant.warnings)


def test_detect_outliers_handles_insufficient_data_and_unsupported_method():
    context = make_context(pd.DataFrame({"value": [1, 2, None], "text": ["a", "b", "c"]}))

    insufficient = detect_outliers(context, "value")
    unsupported = detect_outliers(context, "value", method="zscore")
    non_numeric = detect_outliers(context, "text")

    assert insufficient.status == "error"
    assert "4 finite" in insufficient.error
    assert unsupported.status == "error"
    assert "Unsupported" in unsupported.error
    assert non_numeric.status == "error"


def test_all_tools_produce_json_serializable_results_and_preserve_input():
    dataframe = pd.DataFrame(
        {
            "number": [1, 2, 100, float("inf")],
            "group": ["a", "a", "b", pd.NaT],
        }
    )
    before = dataframe.copy(deep=True)
    context = make_context(dataframe)
    results = [
        profile_dataset(context),
        analyze_missing_values(context),
        detect_duplicates(context),
        inspect_column(context, "number"),
        detect_outliers(context, "number"),
    ]

    for result in results:
        json.dumps(result.to_dict())
    assert_unchanged(dataframe, before)


def test_json_serialization_handles_timestamps_missing_and_nonfinite_values():
    dataframe = pd.DataFrame(
        {
            "when": [pd.Timestamp("2025-01-01"), pd.NaT],
            "value": [float("nan"), float("inf")],
        }
    )

    results = [
        profile_dataset(make_context(dataframe)),
        analyze_missing_values(make_context(dataframe)),
        detect_duplicates(make_context(dataframe)),
        inspect_column(make_context(dataframe), "when"),
    ]

    for result in results:
        serialized = json.dumps(result.to_dict(), allow_nan=False)
        assert isinstance(serialized, str)
