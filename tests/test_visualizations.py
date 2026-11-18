"""Tests for deterministic data-quality visualization preparation."""

import json

import pandas as pd
import pytest

from datasleuth.models import DatasetContext
from datasleuth.visualizations import dataset_composition, dataset_composition_figure, issue_breakdown_figure, issue_counts


def make_context(dataframe, name="synthetic.csv"):
    return DatasetContext("visual-dataset", name, dataframe, len(dataframe), len(dataframe.columns), [str(column) for column in dataframe.columns])


def test_clean_dataset_composition_uses_actual_pandas_types_and_no_issue_pie():
    context = make_context(pd.DataFrame({"name": ["Ada", "Grace"], "score": [10, 20]}))

    composition = dataset_composition(context)
    counts = issue_counts(context)

    assert composition.set_index("type_group").loc["Numeric", "column_count"] == 1
    assert composition.set_index("type_group").loc["Text / categorical", "column_count"] == 1
    assert counts == {"Missing cells": 0, "Duplicate rows": 0}
    assert issue_breakdown_figure(counts) is None


def test_composition_recognizes_boolean_datetime_and_other_without_parsing():
    dataframe = pd.DataFrame({
        "amount": [1, 2],
        "active": [True, False],
        "created": pd.to_datetime(["2024-01-01", "2024-01-02"]),
        "label": ["a", "b"],
    })
    dataframe["category"] = pd.Series(["x", "y"], dtype="category")
    context = make_context(dataframe)

    composition = dataset_composition(context).set_index("type_group")

    assert composition.loc["Numeric", "column_count"] == 1
    assert composition.loc["Boolean", "column_count"] == 1
    assert composition.loc["Date/time", "column_count"] == 1
    assert composition.loc["Text / categorical", "column_count"] == 2
    assert composition.loc["Other", "column_count"] == 0


def test_missing_values_only_uses_metric_instead_of_one_slice_pie():
    context = make_context(pd.DataFrame({"name": ["Ada", None], "score": [10, 20]}))

    counts = issue_counts(context)

    assert counts == {"Missing cells": 1, "Duplicate rows": 0}
    assert issue_breakdown_figure(counts) is None


def test_duplicate_rows_only_uses_metric_instead_of_one_slice_pie():
    context = make_context(pd.DataFrame({"name": ["Ada", "Ada"], "score": [10, 10]}))

    counts = issue_counts(context)

    assert counts == {"Missing cells": 0, "Duplicate rows": 1}
    assert issue_breakdown_figure(counts) is None


def test_both_issue_categories_produce_labeled_donut_with_counts():
    context = make_context(pd.DataFrame({"name": ["Ada", "Ada", None], "score": [10, 10, 20]}))

    figure = issue_breakdown_figure(issue_counts(context))

    assert figure is not None
    assert figure.layout.title.text == "Breakdown of Detected Issues"
    assert list(figure.data[0].labels) == ["Missing cells", "Duplicate rows"]
    assert list(figure.data[0].values) == [1, 1]
    assert figure.data[0].hole == pytest.approx(0.5)


def test_header_only_dataset_has_zero_scale_and_no_crash():
    context = make_context(pd.DataFrame(columns=["name", "score"]))

    figure = dataset_composition_figure(context)
    counts = issue_counts(context)

    assert list(figure.data[0].y) == [0, 2, 0, 0, 0]
    assert counts == {"Missing cells": 0, "Duplicate rows": 0}


def test_many_columns_remain_bounded_in_composition_chart():
    dataframe = pd.DataFrame({f"column_{index}": [index] for index in range(40)})
    context = make_context(dataframe)

    figure = dataset_composition_figure(context)

    assert sum(figure.data[0].y) == 40
    assert figure.layout.height == 315


def test_dataset_switching_updates_metrics_without_mutating_inputs():
    first = pd.DataFrame({"value": [1, None]})
    second = pd.DataFrame({"value": [1, 1]})
    first_before = first.copy(deep=True)
    second_before = second.copy(deep=True)

    assert issue_counts(make_context(first, "a.csv"))["Missing cells"] == 1
    assert issue_counts(make_context(second, "b.csv"))["Duplicate rows"] == 1
    pd.testing.assert_frame_equal(first, first_before)
    pd.testing.assert_frame_equal(second, second_before)


def test_chart_data_is_strictly_json_serializable():
    context = make_context(pd.DataFrame({"value": [1, None]}))
    data = dataset_composition(context).to_dict(orient="records")

    json.dumps(data, allow_nan=False)
