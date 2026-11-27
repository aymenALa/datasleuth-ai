"""Built-in synthetic sample CSV datasets for immediate exploration."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from .data_loader import load_csv
from .models import DatasetContext

_SAMPLES_DIR = Path(__file__).resolve().parents[2] / "data" / "samples"


@dataclass(frozen=True)
class SampleDatasetInfo:
    """Metadata for one bundled synthetic sample dataset."""

    key: str
    title: str
    filename: str
    domain: str
    row_count: int
    column_count: int
    scenarios: tuple[str, ...]
    description: str
    suggested_goal: str


SAMPLE_DATASETS: tuple[SampleDatasetInfo, ...] = (
    SampleDatasetInfo(
        key="ecommerce_orders",
        title="E-Commerce Orders",
        filename="ecommerce_orders.csv",
        domain="Retail Operations",
        row_count=24,
        column_count=10,
        scenarios=("Missing values", "Duplicate rows", "Mixed types", "IQR outlier candidates"),
        description="Synthetic order ledger with missing customer/shipping fields, duplicate rows, mixed-type discounts, and extreme order totals.",
        suggested_goal="Investigate missing customer or shipping fields, duplicate order records, mixed discount types, and outlier order totals.",
    ),
    SampleDatasetInfo(
        key="customer_records",
        title="Customer Records",
        filename="customer_records.csv",
        domain="CRM & Accounts",
        row_count=20,
        column_count=9,
        scenarios=("Missing values", "Duplicate rows", "Mixed types", "IQR outlier candidates"),
        description="Synthetic CRM table containing missing tiers/channels, redundant customer rows, text values in numeric age, and high-spend outliers.",
        suggested_goal="Audit customer completeness, duplicate account rows, mixed age formats, and lifetime spend outlier candidates.",
    ),
    SampleDatasetInfo(
        key="sales_transactions",
        title="Sales Transactions",
        filename="sales_transactions.csv",
        domain="Revenue Analytics",
        row_count=18,
        column_count=9,
        scenarios=("Missing values", "Duplicate rows", "Mixed types", "IQR outlier candidates"),
        description="Synthetic sales ledger with missing region/rep codes, duplicate transactions, non-numeric unit prices, and negative/extreme quantities.",
        suggested_goal="Identify missing sales attribution, duplicate transactions, incompatible unit_price entries, and quantity/revenue outliers.",
    ),
    SampleDatasetInfo(
        key="operational_metrics",
        title="Operational Metrics",
        filename="operational_metrics.csv",
        domain="Platform Telemetry",
        row_count=16,
        column_count=8,
        scenarios=("Missing values", "Duplicate rows", "Mixed types", "IQR outlier candidates"),
        description="Synthetic service telemetry logs with missing department/status values, duplicate log entries, mixed status codes, and latency spikes.",
        suggested_goal="Check telemetry completeness, duplicate log events, mixed status_code types, and latency_ms outlier candidates.",
    ),
    SampleDatasetInfo(
        key="enterprise_invoice_ledger",
        title="Enterprise Invoice Ledger",
        filename="enterprise_invoice_ledger.csv",
        domain="B2B Finance (2,000 Rows)",
        row_count=2000,
        column_count=10,
        scenarios=("Missing values", "30 duplicate rows", "Mixed discount_rate", "Invoice amount outliers"),
        description="Reproducibly generated 2,000-row B2B invoice ledger (seed=42) with missing dates/regions, redundant rows, mixed-type discount rates, and extreme invoice amounts.",
        suggested_goal="Perform a comprehensive quality audit across 2,000 invoice records: missingness, duplicate rows, mixed discount rates, and invoice amount outliers.",
    ),
)

_BY_KEY = {item.key: item for item in SAMPLE_DATASETS}


def list_sample_datasets() -> list[SampleDatasetInfo]:
    """Return all available synthetic sample datasets."""

    return list(SAMPLE_DATASETS)


def get_sample_dataset(key: str) -> SampleDatasetInfo:
    """Return metadata for a sample dataset key."""

    if key not in _BY_KEY:
        raise KeyError(f"Unknown sample dataset: {key}")
    return _BY_KEY[key]


def read_sample_csv_bytes(key: str) -> bytes:
    """Read raw UTF-8 CSV bytes for a bundled sample dataset."""

    info = get_sample_dataset(key)
    path = _SAMPLES_DIR / info.filename
    return path.read_bytes()


def load_sample_dataset(key: str) -> DatasetContext:
    """Load and validate a bundled sample CSV through the standard ingestion pipeline."""

    info = get_sample_dataset(key)
    raw = read_sample_csv_bytes(key)
    source = BytesIO(raw)
    source.name = info.filename
    return load_csv(source)
