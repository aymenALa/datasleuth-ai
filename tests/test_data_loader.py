"""Tests for CSV ingestion and dataset validation."""

from io import BytesIO

import pandas as pd
import pytest

from datasleuth import data_loader
from datasleuth.config import MAX_COLUMNS, MAX_CSV_SIZE_BYTES, MAX_ROWS
from datasleuth.data_loader import (
    CSVEncodingError,
    CSVFileSizeError,
    CSVParseError,
    CSVValidationError,
    EmptyCSVError,
    load_csv,
)


def test_loads_valid_csv_and_matches_dataframe_metadata(tmp_path):
    path = tmp_path / "customers.csv"
    path.write_bytes(b"name,age\nAda,36\nGrace,28\n")

    context = load_csv(path)

    assert context.filename == "customers.csv"
    assert context.row_count == len(context.dataframe) == 2
    assert context.column_count == len(context.dataframe.columns) == 2
    assert context.column_names == list(context.dataframe.columns) == ["name", "age"]
    assert context.dataset_id
    assert context.warnings == []


def test_loads_utf8_with_bom():
    context = load_csv(BytesIO("name\n\u00c9lodie\n".encode("utf-8-sig")))

    assert context.column_names == ["name"]
    assert context.dataframe.iloc[0, 0] == "\u00c9lodie"


def test_rejects_empty_file():
    with pytest.raises(EmptyCSVError, match="empty"):
        load_csv(BytesIO(b""))


def test_rejects_whitespace_only_csv():
    with pytest.raises(EmptyCSVError, match="empty"):
        load_csv(BytesIO(b" \t\r\n  \n"))


def test_accepts_header_only_csv():
    context = load_csv(BytesIO(b"name,age\n"))

    assert context.row_count == 0
    assert context.column_count == 2
    assert context.column_names == ["name", "age"]
    assert context.dataframe.empty


def test_rejects_invalid_encoding():
    with pytest.raises(CSVEncodingError, match="UTF-8"):
        load_csv(BytesIO(b"name\n\xff\n"))


def test_rejects_malformed_csv():
    with pytest.raises(CSVParseError, match="Malformed CSV"):
        load_csv(BytesIO(b'name,age\n"Ada,36\n'))


def test_rejects_duplicate_column_names_before_pandas_renames_them():
    with pytest.raises(CSVValidationError, match="duplicate"):
        load_csv(BytesIO(b"name,name\nAda,36\n"))


def test_rejects_empty_or_whitespace_only_column_names():
    with pytest.raises(CSVValidationError, match="empty or whitespace-only"):
        load_csv(BytesIO(b"name, \t\nAda,36\n"))


@pytest.mark.parametrize("csv_bytes", [b"name,age\nAda\n", b"name,age\nAda,36,extra\n"])
def test_rejects_inconsistent_row_widths(csv_bytes):
    with pytest.raises(CSVValidationError, match="expected 2"):
        load_csv(BytesIO(csv_bytes))


def test_rejects_excessive_rows(monkeypatch):
    monkeypatch.setattr(data_loader, "MAX_ROWS", 2)

    with pytest.raises(CSVValidationError, match="rows"):
        load_csv(BytesIO(b"name\nAda\nGrace\nLin\n"))


def test_rejects_excessive_columns(monkeypatch):
    monkeypatch.setattr(data_loader, "MAX_COLUMNS", 2)

    with pytest.raises(CSVValidationError, match="columns"):
        load_csv(BytesIO(b"a,b,c\n1,2,3\n"))


def test_rejects_file_over_size_limit(monkeypatch):
    monkeypatch.setattr(data_loader, "MAX_CSV_SIZE_BYTES", 10)

    with pytest.raises(CSVFileSizeError, match="maximum allowed"):
        load_csv(BytesIO(b"name\n1234567890\n"))


def test_loads_binary_file_like_object_from_start_and_restores_cursor():
    source = BytesIO(b"name,score\nAda,10\n")
    source.seek(3)
    original_bytes = source.getvalue()

    context = load_csv(source)

    assert context.filename == "uploaded.csv"
    assert source.tell() == 3
    assert source.getvalue() == original_bytes
    pd.testing.assert_frame_equal(
        context.dataframe,
        pd.DataFrame({"name": ["Ada"], "score": [10]}),
    )


def test_preserves_nonempty_column_names_and_values_without_cleaning():
    context = load_csv(BytesIO(b" name ,value\n Ada , raw value \n"))

    assert context.column_names == [" name ", "value"]
    assert context.dataframe.iloc[0, 0] == " Ada "
    assert context.dataframe.iloc[0, 1] == " raw value "


def test_limits_have_expected_initial_values():
    assert MAX_CSV_SIZE_BYTES == 10 * 1024 * 1024
    assert MAX_ROWS == 50_000
    assert MAX_COLUMNS == 100
