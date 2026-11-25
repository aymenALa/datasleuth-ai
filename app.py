"""Streamlit interface and workspace shell for DataSleuth AI."""

from __future__ import annotations

import hashlib
import html
from io import BytesIO
from typing import Any

import importlib
import streamlit as st

import datasleuth.ui.theme
import datasleuth.ui.navigation
import datasleuth.ui.views
import datasleuth.ui.views.dataset
import datasleuth.ui.views.overview
import datasleuth.ui.views.investigation

importlib.reload(datasleuth.ui.theme)
importlib.reload(datasleuth.ui.navigation)
importlib.reload(datasleuth.ui.views)
importlib.reload(datasleuth.ui.views.dataset)
importlib.reload(datasleuth.ui.views.overview)
importlib.reload(datasleuth.ui.views.investigation)

from datasleuth.agent import run_investigation
from datasleuth.data_loader import CSVLoadError, load_csv
from datasleuth.models import DatasetContext, InvestigationResult
from datasleuth.reports import build_report
from datasleuth.ui.theme import inject_custom_styles
from datasleuth.ui.navigation import render_sidebar, get_factual_status
from datasleuth.ui.views import (
    render_overview_view,
    render_dataset_view,
    render_investigation_view,
    render_findings_view,
    render_recommendations_view,
    render_trace_view,
    render_reports_view,
)


DEFAULT_GOAL = "Identify the most important data-quality risks and explain the evidence."
_PREVIEW_ROWS = 10


def _initialize_state() -> None:
    defaults = {
        "dataset_context": None,
        "dataset_signature": None,
        "upload_error": None,
        "investigation_goal": DEFAULT_GOAL,
        "investigation_result": None,
        "report": None,
        "active_view": "Overview",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _signature(uploaded_file: Any) -> str:
    return hashlib.sha256(uploaded_file.getvalue()).hexdigest()


def _load_uploaded_dataset(uploaded_file: Any) -> None:
    signature = _signature(uploaded_file)
    if signature == st.session_state["dataset_signature"]:
        return
    try:
        source = BytesIO(uploaded_file.getvalue())
        source.name = getattr(uploaded_file, "name", "uploaded.csv")
        context = load_csv(source)
    except CSVLoadError as exc:
        st.session_state["dataset_context"] = None
        st.session_state["dataset_signature"] = signature
        st.session_state["upload_error"] = str(exc)
        st.session_state["investigation_result"] = None
        st.session_state["report"] = None
        return
    st.session_state["dataset_context"] = context
    st.session_state["dataset_signature"] = signature
    st.session_state["upload_error"] = None
    st.session_state["investigation_result"] = None
    st.session_state["report"] = None


def _execute_investigation(
    context: DatasetContext,
    goal: str,
    runner: Any | None = None,
) -> InvestigationResult:
    """Run one explicit investigation and persist its report in session state."""

    result = (runner or run_investigation)(context, goal)
    st.session_state["investigation_result"] = result
    st.session_state["report"] = build_report(context, result)
    return result


def _render_top_header(context: DatasetContext | None) -> None:
    """Render the top workspace header with clean inline status badge."""
    status_text, status_color = get_factual_status()
    st.markdown(
        f"""
        <div style="margin-top: 0.25rem; margin-bottom: 0.35rem;">
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:0.25rem;">
                <span class="ds-kicker" style="margin-bottom:0;">Autonomous Data Quality Intelligence</span>
                <span class="ds-status-pill" style="border: 1px solid {status_color}45; background: {status_color}14; color: {status_color}; font-size:0.72rem; padding:3px 9px; line-height:1.2;">
                    <span style="display:inline-block; width:6px; height:6px; border-radius:50%; background:{status_color};"></span>
                    {html.escape(status_text)}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.title("DataSleuth AI")
    st.markdown(
        '<div class="ds-subtitle">Evidence-first autonomous data quality investigation for CSV datasets — no automatic cleaning.</div>',
        unsafe_allow_html=True,
    )


def _render_upload_section(context: DatasetContext | None, active_view: str = "Overview") -> None:
    """Render single authoritative CSV uploader: onboarding guide on Overview, compact controls elsewhere."""
    if context is None:
        if active_view == "Overview":
            st.markdown(
                """
                <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(240px, 1fr)); gap:14px; margin: 0.5rem 0 1.25rem 0;">
                    <div class="ds-card" style="margin-bottom:0; padding:18px;">
                        <div style="font-size:0.75rem; font-weight:700; color:#38BDF8; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:6px;">Step 1</div>
                        <div style="font-weight:600; color:#F1F5F9; font-size:1.02rem; margin-bottom:4px;">Upload a CSV</div>
                        <div style="font-size:0.84rem; color:#94A3B8; line-height:1.4;">Select or drop a UTF-8 CSV dataset with headers. Enforces strict size and shape bounds.</div>
                    </div>
                    <div class="ds-card" style="margin-bottom:0; padding:18px;">
                        <div style="font-size:0.75rem; font-weight:700; color:#818CF8; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:6px;">Step 2</div>
                        <div style="font-weight:600; color:#F1F5F9; font-size:1.02rem; margin-bottom:4px;">Explore Dataset Quality</div>
                        <div style="font-size:0.84rem; color:#94A3B8; line-height:1.4;">Review inferred schemas, missing-cell rates, duplicate groups, and deterministic distributions.</div>
                    </div>
                    <div class="ds-card" style="margin-bottom:0; padding:18px;">
                        <div style="font-size:0.75rem; font-weight:700; color:#34D399; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:6px;">Step 3</div>
                        <div style="font-weight:600; color:#F1F5F9; font-size:1.02rem; margin-bottom:4px;">Run an AI Investigation</div>
                        <div style="font-size:0.84rem; color:#94A3B8; line-height:1.4;">Autonomous read-only agent executes allowlisted inspection tools to verify data quality facts.</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.subheader("Load a dataset")
            uploaded_file = st.file_uploader(
                "Upload a CSV file",
                type=["csv"],
                key="csv_uploader",
                label_visibility="collapsed",
            )
            if uploaded_file is not None:
                _load_uploaded_dataset(uploaded_file)

            if st.session_state["upload_error"]:
                st.error(f"CSV could not be loaded: {st.session_state['upload_error']}")
            else:
                st.info("Upload a UTF-8 CSV to begin. The existing ingestion limits are enforced.")
                st.caption("Supported formats: UTF-8 & UTF-8 with BOM · Row, column, and file size limits validated · Header row required.")
        else:
            col_bar, col_manage = st.columns([3, 1])
            with col_bar:
                st.markdown(
                    """
                    <div style="background:#111827; border:1px dashed #1F293D; border-radius:8px; padding:8px 14px; margin-bottom:12px; display:flex; align-items:center; gap:8px;">
                        <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#94A3B8;"></span>
                        <span style="font-size:0.86rem; color:#94A3B8;">
                            No active dataset loaded. Upload a CSV to activate this workspace.
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col_manage:
                with st.expander("Upload dataset", expanded=False):
                    uploaded_file = st.file_uploader(
                        "Upload a CSV file",
                        type=["csv"],
                        key="csv_uploader",
                        label_visibility="collapsed",
                    )
                    if uploaded_file is not None:
                        _load_uploaded_dataset(uploaded_file)
            if st.session_state.get("upload_error"):
                st.error(f"CSV could not be loaded: {st.session_state['upload_error']}")
    else:
        # Compact dataset-management controls when a dataset is loaded
        col_bar, col_manage = st.columns([3, 1])
        with col_bar:
            st.markdown(
                f"""
                <div style="background:#111827; border:1px solid #1F293D; border-radius:8px; padding:8px 14px; margin-bottom:12px; display:flex; align-items:center; gap:8px;">
                    <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#34D399;"></span>
                    <span style="font-size:0.86rem; color:#E2E8F0;">
                        <b>Active Dataset:</b> <span style="font-family:monospace; color:#38BDF8;">{html.escape(context.filename)}</span>
                        <span style="color:#94A3B8; margin-left:6px;">({len(context.dataframe):,} rows · {len(context.dataframe.columns)} columns)</span>
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_manage:
            with st.expander("Manage dataset", expanded=False):
                st.caption("Replace dataset:")
                replace_file = st.file_uploader(
                    "Upload a CSV file",
                    type=["csv"],
                    key="csv_uploader",
                    label_visibility="collapsed",
                )
                if replace_file is not None:
                    _load_uploaded_dataset(replace_file)
                if st.button("Remove dataset", type="secondary", use_container_width=True, key="btn_remove_dataset"):
                    st.session_state["dataset_context"] = None
                    st.session_state["dataset_signature"] = None
                    st.session_state["upload_error"] = None
                    st.session_state["investigation_result"] = None
                    st.session_state["report"] = None
                    st.rerun()


def main() -> None:
    st.set_page_config(
        page_title="DataSleuth AI",
        page_icon="🔎",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _initialize_state()
    inject_custom_styles()

    current_context: DatasetContext | None = st.session_state.get("dataset_context")
    current_view: str = st.session_state.get("active_view", "Overview")

    # Top header with unclipped status badge
    _render_top_header(current_context)

    # Single authoritative CSV uploader (processes upload and updates session state)
    _render_upload_section(current_context, current_view)

    # Refresh state after potential upload processing in this run
    context: DatasetContext | None = st.session_state["dataset_context"]
    result: InvestigationResult | None = st.session_state["investigation_result"]
    report: dict[str, Any] | None = st.session_state["report"]

    # Render sidebar navigation (always reflects latest state)
    active_view = render_sidebar(context)

    # Route to active view for both loaded and empty states
    if active_view == "Overview":
        render_overview_view(context)
    elif active_view == "Dataset Explorer":
        render_dataset_view(context, _load_uploaded_dataset)
    elif active_view == "Investigation":
        render_investigation_view(context, result, report, _execute_investigation)
    elif active_view == "Findings":
        render_findings_view(report)
    elif active_view == "Recommendations":
        render_recommendations_view(report)
    elif active_view == "Execution Trace":
        render_trace_view(result)
    elif active_view == "Reports":
        render_reports_view(context, report)
    else:
        render_overview_view(context)


if __name__ == "__main__":
    main()
