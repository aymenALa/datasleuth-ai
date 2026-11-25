"""Dataset Explorer view: Upload workspace, column searching/filtering, schema, and preview."""

from __future__ import annotations

import html
from typing import Any
import streamlit as st

from datasleuth.models import DatasetContext
from datasleuth.ui.view_models import build_column_summaries
from datasleuth.ui.formatters import format_percentage

_PREVIEW_ROWS = 10


def render_dataset_view(context: DatasetContext | None, on_upload: Any = None) -> None:
    """Render the Dataset Explorer workspace."""
    st.markdown(
        """
        <div style="border-bottom:1px solid #1F293D; padding-bottom:0.75rem; margin-bottom:1rem;">
            <div class="ds-kicker">Data Ingestion & Exploration</div>
            <h2 style="margin:0; font-size:1.6rem;">Dataset Explorer</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if context is None:
        st.markdown(
            """
            <div class="ds-empty-state">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">📁</div>
                <div class="ds-empty-state-title">No Dataset Loaded</div>
                <div class="ds-empty-state-desc">
                    Upload a UTF-8 CSV dataset to explore schema types, missing-value distributions, and preview records.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"""
        <div style="background:#111827; border:1px solid #1F293D; border-radius:8px; padding:10px 14px; margin-bottom:16px; display:flex; justify-content:space-between; align-items:center;">
            <div style="font-size:0.88rem; color:#E2E8F0;">
                <span style="color:#34D399; font-weight:600;">✓ Ingested Dataset:</span> <b>{html.escape(context.filename)}</b>
                <span style="color:#94A3B8; margin-left:8px;">({len(context.dataframe):,} rows · {len(context.dataframe.columns)} columns)</span>
            </div>
            <div style="font-size:0.75rem; color:#94A3B8;">
                Profiled with deterministic read-only Pandas checks
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Explorer Tabs
    tabs = st.tabs([
        "Column Schema & Quality",
        "Dataframe Preview",
        "Ingestion Notes",
    ])

    with tabs[0]:
        st.caption("Search, filter, and inspect inferred column schemas across the active dataset.")
        f_col1, f_col2, f_col3 = st.columns([2, 1, 1])
        with f_col1:
            search_query = st.text_input("Search column name", placeholder="Filter by column name…", key="col_search")
        with f_col2:
            type_filter = st.selectbox(
                "Filter by data type",
                ["All Types", "Numeric", "Text / categorical", "Boolean", "Date/time", "Other"],
                key="col_type_filter",
            )
        with f_col3:
            only_missing = st.checkbox("Only columns with missing values", key="col_only_missing")

        all_summaries = build_column_summaries(context)
        filtered_summaries = all_summaries

        if search_query.strip():
            q = search_query.strip().lower()
            filtered_summaries = [s for s in filtered_summaries if q in s.name.lower()]

        if type_filter != "All Types":
            def _matches_type(s_type: str) -> bool:
                s_lower = s_type.lower()
                if type_filter == "Numeric":
                    return any(t in s_lower for t in ("int", "float", "number"))
                if type_filter == "Text / categorical":
                    return any(t in s_lower for t in ("str", "object", "category", "string"))
                if type_filter == "Boolean":
                    return "bool" in s_lower
                if type_filter == "Date/time":
                    return "datetime" in s_lower or "timestamp" in s_lower
                return True
            filtered_summaries = [s for s in filtered_summaries if _matches_type(s.inferred_type)]

        if only_missing:
            filtered_summaries = [s for s in filtered_summaries if s.missing_count > 0]

        table_data = [
            {
                "Column": s.name,
                "Inferred Dtype": s.inferred_type,
                "Completeness": format_percentage(s.completeness_percentage),
                "Missing Cells": f"{s.missing_count:,}",
                "Valid Observations": f"{s.non_missing_count:,}",
            }
            for s in filtered_summaries
        ]
        st.dataframe(table_data, width="stretch", hide_index=True)
        st.caption(f"Showing {len(filtered_summaries)} of {len(all_summaries)} columns.")

    with tabs[1]:
        p_row1, p_row2 = st.columns([1, 3])
        with p_row1:
            row_limit = st.selectbox("Rows to preview", [10, 25, 50, 100], index=0, key="preview_limit")

        limit = min(row_limit or _PREVIEW_ROWS, len(context.dataframe))
        st.caption(f"Preview — first {limit} rows")
        st.dataframe(context.dataframe.head(limit), width="stretch", hide_index=True)

    with tabs[2]:
        if context.warnings:
            st.caption("Ingestion observations flagged by the data loader:")
            for warning in context.warnings:
                st.warning(warning)
        else:
            st.success("No anomalies or encoding warnings were encountered during CSV validation.")
