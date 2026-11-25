"""Report Center view: Report export downloads and consolidated limitations panel."""

from __future__ import annotations

import html
from typing import Any
import streamlit as st

from datasleuth.models import DatasetContext
from datasleuth.reports import report_to_json, report_to_markdown


def render_reports_view(context: DatasetContext | None, report: dict[str, Any] | None) -> None:
    """Render the Report Center workspace."""
    st.markdown(
        """
        <div style="border-bottom:1px solid #1F293D; padding-bottom:0.75rem; margin-bottom:1rem;">
            <div class="ds-kicker">Artifact Export & Governance</div>
            <h2 style="margin:0; font-size:1.6rem;">Report Center</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if report is None:
        st.markdown(
            """
            <div class="ds-empty-state">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">📑</div>
                <div class="ds-empty-state-title">No Investigation Report Generated</div>
                <div class="ds-empty-state-desc">
                    Run an investigation in the <b>Investigation Center</b> to produce verified JSON and Markdown reports.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.subheader("Export report")
    st.caption("Download the complete investigation report for documentation or automated pipeline ingestion.")

    findings_count = len(report.get("verified_findings", []))
    recom_count = len(report.get("cleaning_recommendations", []))
    completion_status = report.get("completion_status", "unknown")

    # Metadata card
    st.markdown(
        f"""
        <div style="background:#111827; border:1px solid #1F293D; border-radius:10px; padding:1rem 1.25rem; margin-bottom:1.25rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <div style="font-size:1.05rem; font-weight:700; color:#F1F5F9;">Investigation Report Summary</div>
                <span class="ds-badge ds-badge-fact">{html.escape(completion_status.upper())}</span>
            </div>
            <div style="display:flex; gap:20px; font-size:0.84rem; color:#94A3B8;">
                <span>Dataset: <b style="color:#F1F5F9;">{html.escape(str(report.get('dataset', {}).get('filename', 'dataset.csv')))}</b></span>
                <span>Verified Findings: <b style="color:#38BDF8;">{findings_count}</b></span>
                <span>Recommendations: <b style="color:#34D399;">{recom_count}</b></span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Download action buttons (exact file names and mimes preserved)
    json_report = report_to_json(report)
    markdown_report = report_to_markdown(report)

    export_columns = st.columns(2)
    export_columns[0].download_button(
        "Download JSON",
        data=json_report,
        file_name="datasleuth-report.json",
        mime="application/json",
        width="stretch",
    )
    export_columns[1].download_button(
        "Download Markdown",
        data=markdown_report,
        file_name="datasleuth-report.md",
        mime="text/markdown",
        width="stretch",
    )

    # Consolidated Warnings & Limitations panel
    all_warnings = (
        report.get("warnings", [])
        + report.get("validation_errors", [])
        + report.get("limitations", [])
    )
    if all_warnings:
        st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
        st.subheader("Warnings and limitations")
        st.caption("Consolidated analytical constraints, tool assumptions, and boundary limitations:")
        for warning in all_warnings:
            st.warning(warning)
