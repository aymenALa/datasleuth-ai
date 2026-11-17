"""CSV ingestion and validation for DataSleuth AI."""

from __future__ import annotations

import csv
import io
import uuid
from os import PathLike
from pathlib import Path
from typing import BinaryIO

import pandas as pd

from .config import MAX_COLUMNS, MAX_CSV_SIZE_BYTES, MAX_ROWS
from .models import DatasetContext


class CSVLoadError(ValueError):
    """Base exception for invalid or unreadable CSV input."""


class CSVFileSizeError(CSVLoadError):
    """Raised when the CSV exceeds the configured byte limit."""


class CSVEncodingError(CSVLoadError):
    """Raised when the CSV is not valid UTF-8 or UTF-8 with BOM."""


class EmptyCSVError(CSVLoadError):
    """Raised when the CSV contains no usable content."""


class CSVValidationError(CSVLoadError):
    """Raised when CSV columns or dimensions violate the data contract."""


class CSVParseError(CSVLoadError):
    """Raised when Pandas cannot parse the CSV structure."""


CSVSource = str | PathLike[str] | BinaryIO


def _read_source(source: CSVSource) -> tuple[bytes, str]:
    """Read a path or binary file-like object without changing its contents."""

    if isinstance(source, (str, PathLike)):
        path = Path(source)
        try:
            return path.read_bytes(), path.name
        except OSError as exc:
            raise CSVLoadError(
                f"Unable to read CSV file ({type(exc).__name__})"
            ) from exc

    if not hasattr(source, "read"):
        raise CSVLoadError("CSV source must be a file path or binary file-like object")

    position = None
    try:
        position = source.tell() if hasattr(source, "tell") else None
        if position is not None and hasattr(source, "seek"):
            source.seek(0)
        content = source.read()
    except (OSError, ValueError) as exc:
        raise CSVLoadError(f"Unable to read CSV file-like object: {exc}") from exc
    finally:
        if position is not None and hasattr(source, "seek"):
            try:
                source.seek(position)
            except (OSError, ValueError):
                pass

    if isinstance(content, str):
        raise CSVLoadError("CSV file-like objects must provide binary data")
    if not isinstance(content, bytes):
        raise CSVLoadError("CSV file-like object returned unsupported data")

    filename = Path(str(getattr(source, "name", "uploaded.csv"))).name
    return content, filename or "uploaded.csv"


def _validate_csv_structure(decoded_content: str) -> list[str]:
    """Validate CSV syntax, headers, and row widths."""

    try:
        reader = csv.reader(io.StringIO(decoded_content), strict=True)
        header = next(reader)
        if not header:
            raise EmptyCSVError("CSV file has no header")
        if any(not name.strip() for name in header):
            raise CSVValidationError(
                "CSV column names must not be empty or whitespace-only"
            )
        if len(set(header)) != len(header):
            raise CSVValidationError("CSV contains duplicate column names")

        for row_number, row in enumerate(reader, start=2):
            if not row:
                continue
            if len(row) != len(header):
                raise CSVValidationError(
                    f"CSV row {row_number} has {len(row)} fields; "
                    f"expected {len(header)}"
                )
    except StopIteration as exc:
        raise EmptyCSVError("CSV file is empty") from exc
    except csv.Error as exc:
        raise CSVParseError(f"Malformed CSV: {exc}") from exc
    return header


def load_csv(source: CSVSource) -> DatasetContext:
    """Load and validate a CSV path or uploaded binary file-like object.

    The source is read in full so oversized input is rejected rather than
    truncated. The returned DataFrame is a new Pandas object; the source bytes
    are never modified.
    """

    content, filename = _read_source(source)
    if len(content) > MAX_CSV_SIZE_BYTES:
        raise CSVFileSizeError(
            f"CSV file is {len(content)} bytes; maximum allowed is "
            f"{MAX_CSV_SIZE_BYTES} bytes"
        )
    if not content.strip():
        raise EmptyCSVError("CSV file is empty")

    try:
        decoded_content = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise CSVEncodingError("CSV must be encoded as UTF-8 or UTF-8 with BOM") from exc

    header = _validate_csv_structure(decoded_content)

    try:
        dataframe = pd.read_csv(
            io.BytesIO(content),
            encoding="utf-8-sig",
            on_bad_lines="error",
        )
    except UnicodeDecodeError as exc:
        raise CSVEncodingError("CSV must be encoded as UTF-8 or UTF-8 with BOM") from exc
    except (pd.errors.ParserError, ValueError) as exc:
        raise CSVParseError(f"Malformed CSV: {exc}") from exc

    row_count, column_count = dataframe.shape
    if row_count > MAX_ROWS:
        raise CSVValidationError(
            f"CSV contains {row_count} rows; maximum allowed is {MAX_ROWS}"
        )
    if column_count > MAX_COLUMNS:
        raise CSVValidationError(
            f"CSV contains {column_count} columns; maximum allowed is {MAX_COLUMNS}"
        )

    # Pandas should preserve the header, but use the independently validated
    # names in the contract to make the input schema explicit.
    column_names = list(header)
    if list(dataframe.columns) != column_names:
        raise CSVValidationError("CSV column names could not be preserved")

    return DatasetContext(
        dataset_id=uuid.uuid4().hex,
        filename=filename,
        dataframe=dataframe,
        row_count=row_count,
        column_count=column_count,
        column_names=column_names,
    )
