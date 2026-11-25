"""Presentation-only formatting utilities and text sanitization."""

from __future__ import annotations

import html
import re
from typing import Any


def format_percentage(value: float | int | None, precision: int = 2) -> str:
    """Format a ratio or percentage number cleanly with fixed precision."""
    if value is None:
        return "N/A"
    try:
        num = float(value)
        return f"{num:.{precision}f}%"
    except (ValueError, TypeError):
        return str(value)


def format_count(value: int | float | None) -> str:
    """Format an integer count with comma grouping."""
    if value is None:
        return "N/A"
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return str(value)


def format_classification_label(classification: str | None) -> str:
    """Return an accessible human-readable title for evidence classifications."""
    if not classification:
        return "Observation"
    mapping = {
        "measured_fact": "Measured fact",
        "statistical_candidate": "Statistical candidate",
        "interpretation": "Model interpretation",
    }
    return mapping.get(str(classification).lower(), str(classification).replace("_", " ").title())


def format_confidence_label(confidence: str | None) -> str:
    """Format finding confidence values into clean presentation tags."""
    if not confidence:
        return "Context required"
    normalized = str(confidence).strip().lower()
    mapping = {
        "high": "High confidence",
        "medium": "Medium confidence",
        "low": "Low confidence",
        "context required": "Context required",
    }
    return mapping.get(normalized, str(confidence).title())


def format_observed_label(finding_type: str, metric_path: str, value: Any) -> str:
    """Return a natural units label for observed finding values."""
    if value is None:
        return "N/A"

    if "missing_counts" in metric_path or "missing_value" in metric_path:
        count = format_count(value)
        return f"{count} missing cell{'s' if value != 1 else ''}"

    if "duplicate_row_count" in metric_path:
        count = format_count(value)
        return f"{count} redundant duplicate row{'s' if value != 1 else ''}"

    if "outlier" in metric_path or "outliers" in metric_path:
        count = format_count(value)
        return f"{count} outlier candidate{'s' if value != 1 else ''}"

    if isinstance(value, (int, float)):
        return format_count(value)

    return str(value)


def format_precision_in_text(text: str) -> str:
    """Round unformatted high-precision percentages in descriptive text to 2 decimals."""
    if not text:
        return ""

    def _replace_pct(match: re.Match[str]) -> str:
        try:
            val = float(match.group(1))
            return f"{val:.2f}%"
        except ValueError:
            return match.group(0)

    # Match numbers with 3+ decimal digits followed by %
    return re.sub(r"(\d+\.\d{3,})%", _replace_pct, text)


def sanitize_model_markdown(content: str) -> str:
    """Safely normalize model output for markdown presentation without enabling raw HTML execution."""
    if not content:
        return ""

    # Replace <br>, <br/>, <br /> with clean space or newline
    cleaned = re.sub(r"<br\s*/?>", " ", content, flags=re.IGNORECASE)

    # Strip dangerous HTML tags
    cleaned = re.sub(
        r"<\s*(script|iframe|style|object|embed|applet|form|input|button)[^>]*>.*?<\s*/\s*\1\s*>",
        "",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )
    cleaned = re.sub(
        r"<\s*(script|iframe|style|object|embed|applet|form|input|button)[^>]*>",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Clean high-precision percentages in tables or paragraphs
    cleaned = format_precision_in_text(cleaned)

    return cleaned.strip()
