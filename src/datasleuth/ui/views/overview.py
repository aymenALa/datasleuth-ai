"""Executive Overview view: High-level KPI dashboard, charts, and quality summary."""

from __future__ import annotations

import html
import streamlit as st

from datasleuth.models import DatasetContext
from datasleuth.visualizations import dataset_composition_figure, issue_breakdown_figure, issue_counts
from datasleuth.ui.view_models import build_dashboard_metrics, build_column_summaries
from datasleuth.ui.formatters import format_percentage


def render_overview_view(context: DatasetContext | None) -> None:
    """Render the executive overview dashboard."""
    if context is None:
        return

    report = st.session_state.get("report")
    metrics = build_dashboard_metrics(context, report)

    # Header bar
    st.subheader("Dataset overview")
    st.markdown(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:0.75rem;">
            <div class="ds-kicker">Workspace Analytics</div>
            <div style="font-size:0.84rem; color:#94A3B8;">
                Dataset: <b style="color:#F1F5F9;">{html.escape(context.filename)}</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Primary baseline KPI row (exact labels and values required by regression test suite)
    kpi_cols = st.columns(3)
    kpi_cols[0].metric("Rows", f"{metrics.row_count:,}")
    kpi_cols[1].metric("Columns", f"{metrics.column_count:,}")
    kpi_cols[2].metric("File", context.filename)

    # Derived analytical quality metrics cards
    st.markdown(
        f"""
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:12px; margin-top:12px; margin-bottom:12px;">
            <div class="ds-card" style="margin-bottom:0; padding:12px 14px;">
                <div class="ds-recom-label">Missing Cells</div>
                <div style="font-size:1.4rem; font-weight:700; color:#F1F5F9; font-family:monospace;">{metrics.missing_cells:,}</div>
                <div style="font-size:0.75rem; color:#94A3B8;">{metrics.missing_cell_rate:.2f}% of dataset cells</div>
            </div>
            <div class="ds-card" style="margin-bottom:0; padding:12px 14px;">
                <div class="ds-recom-label">Duplicate Rows</div>
                <div style="font-size:1.4rem; font-weight:700; color:#F1F5F9; font-family:monospace;">{metrics.duplicate_rows:,}</div>
                <div style="font-size:0.75rem; color:#94A3B8;">{metrics.duplicate_row_rate:.2f}% of dataset rows</div>
            </div>
            <div class="ds-card" style="margin-bottom:0; padding:12px 14px;">
                <div class="ds-recom-label">Verified Findings</div>
                <div style="font-size:1.4rem; font-weight:700; color:{'#38BDF8' if metrics.is_investigated else '#64748B'}; font-family:monospace;">
                    {metrics.findings_count if metrics.is_investigated else 'Not investigated'}
                </div>
                <div style="font-size:0.75rem; color:#94A3B8;">{'Deterministic Tool Findings' if metrics.is_investigated else 'Run Investigation to verify'}</div>
            </div>
            <div class="ds-card" style="margin-bottom:0; padding:12px 14px;">
                <div class="ds-recom-label">Outlier Candidates</div>
                <div style="font-size:1.4rem; font-weight:700; color:{'#F59E0B' if metrics.is_investigated else '#64748B'}; font-family:monospace;">
                    {metrics.outlier_candidate_count if metrics.is_investigated else 'Not investigated'}
                </div>
                <div style="font-size:0.75rem; color:#94A3B8;">{'IQR 1.5x candidates' if metrics.is_investigated else 'Statistical candidates'}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='margin-top: 1.25rem;'></div>", unsafe_allow_html=True)

    # Deterministic Data Quality Visualizations
    st.subheader("Data Quality Visualizations")
    chart_columns = st.columns(2)
    with chart_columns[0]:
        st.plotly_chart(dataset_composition_figure(context), width="stretch", theme=None)
    with chart_columns[1]:
        counts = issue_counts(context)
        if sum(counts.values()) == 0:
            st.info("No missing cells or redundant duplicate rows detected.")
        else:
            missing_count = counts.get("Missing cells", 0)
            dup_count = counts.get("Duplicate rows", 0)
            st.markdown(
                f"""
                <div style="background:#111827; border:1px solid #1F293D; border-radius:10px; padding:1.1rem; height:315px; display:flex; flex-direction:column; justify-content:center; gap:14px;">
                    <div style="font-size:0.78rem; font-weight:700; color:#38BDF8; text-transform:uppercase; letter-spacing:0.06em;">Independent Quality Indicators</div>
                    <div style="background:#162033; border:1px solid #202F48; border-radius:8px; padding:12px 14px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-size:0.86rem; color:#94A3B8;">Missing cells (cells)</span>
                            <span style="font-size:1.15rem; font-weight:700; color:{'#F87171' if missing_count > 0 else '#34D399'}; font-family:monospace;">{missing_count:,}</span>
                        </div>
                        <div style="font-size:0.74rem; color:#64748B; margin-top:2px;">Evaluated per cell across {metrics.row_count * metrics.column_count:,} total cells ({metrics.missing_cell_rate:.2f}%)</div>
                    </div>
                    <div style="background:#162033; border:1px solid #202F48; border-radius:8px; padding:12px 14px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-size:0.86rem; color:#94A3B8;">Duplicate rows (rows)</span>
                            <span style="font-size:1.15rem; font-weight:700; color:{'#F59E0B' if dup_count > 0 else '#34D399'}; font-family:monospace;">{dup_count:,}</span>
                        </div>
                        <div style="font-size:0.74rem; color:#64748B; margin-top:2px;">Evaluated per row across {metrics.row_count:,} total rows ({metrics.duplicate_row_rate:.2f}%)</div>
                    </div>
                    <div style="font-size:0.72rem; color:#64748B; line-height:1.35;">
                        Missing cells (cells) and duplicate rows (rows) represent distinct units and are presented independently without combining.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.caption("Charts use deterministic Pandas metrics. Missing cells and duplicate rows are different units and may overlap; outlier candidates are excluded.")

    st.divider()

    # Column Quality Summary
    st.subheader("Column Quality Profile")
    st.caption("Column types below are inferred by Pandas during CSV ingestion.")

    col_summaries = build_column_summaries(context)
    summary_data = [
        {
            "Column": s.name,
            "Inferred Type": s.inferred_type,
            "Valid Values": f"{s.non_missing_count:,}",
            "Missing Cells": f"{s.missing_count:,}",
            "Completeness": format_percentage(s.completeness_percentage),
        }
        for s in col_summaries
    ]
    st.dataframe(summary_data, width="stretch", hide_index=True)

    if not metrics.is_investigated:
        st.info("💡 An autonomous investigation has not yet been executed on this dataset. Go to the **Investigation Center** to run allowlisted tools and generate verified findings.")
