"""Streamlit interface and 3-stage experience shell for DataSleuth AI."""

from __future__ import annotations

import hashlib
import html
import importlib
from io import BytesIO
from pathlib import Path
import sys
import threading
from typing import Any

_SRC_DIR = str(Path(__file__).resolve().parent / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from dotenv import load_dotenv
import streamlit as st

import datasleuth.ui.brand
import datasleuth.ui.navigation
import datasleuth.ui.theme
import datasleuth.ui.views
import datasleuth.ui.views.dataset
import datasleuth.ui.views.investigation
import datasleuth.ui.views.landing
import datasleuth.ui.views.onboarding
import datasleuth.ui.views.overview

importlib.reload(datasleuth.ui.brand)
importlib.reload(datasleuth.ui.theme)
importlib.reload(datasleuth.ui.navigation)
importlib.reload(datasleuth.ui.views)
importlib.reload(datasleuth.ui.views.landing)
importlib.reload(datasleuth.ui.views.onboarding)
importlib.reload(datasleuth.ui.views.dataset)
importlib.reload(datasleuth.ui.views.overview)
importlib.reload(datasleuth.ui.views.investigation)

from datasleuth.agent import run_investigation
from datasleuth.config import MAX_GLOBAL_LIVE_RUNS, MAX_SESSION_LIVE_RUNS
from datasleuth.data_loader import CSVLoadError, load_csv
from datasleuth.demo_runner import run_guided_investigation
from datasleuth.groq_client import is_live_ai_enabled
from datasleuth.models import DatasetContext, InvestigationResult
from datasleuth.reports import build_report
from datasleuth.sample_datasets import get_sample_dataset, load_sample_dataset
from datasleuth.ui.navigation import get_factual_status, render_sidebar
from datasleuth.ui.theme import inject_custom_styles
from datasleuth.ui.views import (
    render_dataset_view,
    render_findings_view,
    render_investigation_view,
    render_landing_page,
    render_onboarding_view,
    render_overview_view,
    render_recommendations_view,
    render_reports_view,
    render_trace_view,
)

load_dotenv(override=False)

DEFAULT_GOAL = "Identify the most important data-quality risks and explain the evidence."
_LIVE_RUN_LOCK = threading.Lock()
_GLOBAL_LIVE_RUNS = 0


def _global_live_runs_remaining() -> int:
    with _LIVE_RUN_LOCK:
        return max(0, MAX_GLOBAL_LIVE_RUNS - _GLOBAL_LIVE_RUNS)


def _initialize_state() -> None:
    defaults = {
        "app_experience": "landing",
        "dataset_context": None,
        "dataset_signature": None,
        "dataset_source_type": None,
        "upload_error": None,
        "investigation_goal": DEFAULT_GOAL,
        "investigation_result": None,
        "investigation_mode": "guided",
        "investigation_running": False,
        "live_runs_used": 0,
        "report": None,
        "active_view": "Overview",
        "clear_uploader": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _signature(uploaded_file: Any) -> str:
    return hashlib.sha256(uploaded_file.getvalue()).hexdigest()


def _load_uploaded_dataset(uploaded_file: Any) -> None:
    signature = _signature(uploaded_file)
    if signature == st.session_state.get("dataset_signature") and st.session_state.get("dataset_context") is not None:
        return
    try:
        source = BytesIO(uploaded_file.getvalue())
        source.name = getattr(uploaded_file, "name", "uploaded.csv")
        context = load_csv(source)
    except CSVLoadError as exc:
        st.session_state["dataset_context"] = None
        st.session_state["dataset_signature"] = signature
        st.session_state["dataset_source_type"] = None
        st.session_state["upload_error"] = str(exc)
        st.session_state["investigation_result"] = None
        st.session_state["report"] = None
        return
    st.session_state["dataset_context"] = context
    st.session_state["dataset_signature"] = signature
    st.session_state["dataset_source_type"] = "uploaded"
    st.session_state["upload_error"] = None
    st.session_state["investigation_goal"] = DEFAULT_GOAL
    st.session_state["investigation_result"] = None
    st.session_state["report"] = None
    st.session_state["app_experience"] = "workspace"
    st.session_state["active_view"] = "Overview"


def _load_sample_dataset(sample_key: str) -> None:
    signature = f"sample:{sample_key}"
    if signature == st.session_state.get("dataset_signature") and st.session_state.get("dataset_context") is not None:
        st.session_state["app_experience"] = "workspace"
        st.session_state["active_view"] = "Overview"
        return
    context = load_sample_dataset(sample_key)
    info = get_sample_dataset(sample_key)
    st.session_state["dataset_context"] = context
    st.session_state["dataset_signature"] = signature
    st.session_state["dataset_source_type"] = "sample"
    st.session_state["upload_error"] = None
    st.session_state["investigation_goal"] = info.suggested_goal
    st.session_state["investigation_result"] = None
    st.session_state["report"] = None
    st.session_state["clear_uploader"] = True
    st.session_state["app_experience"] = "workspace"
    st.session_state["active_view"] = "Overview"


def _execute_investigation(
    context: DatasetContext,
    goal: str,
    runner: Any | None = None,
    mode: str = "live_ai",
) -> InvestigationResult:
    """Run one explicit investigation and persist its report in session state."""

    st.session_state["investigation_running"] = True
    try:
        if runner is not None:
            result = runner(context, goal)
        elif mode == "guided":
            result = run_guided_investigation(context, goal)
        else:
            global _GLOBAL_LIVE_RUNS
            used = int(st.session_state.get("live_runs_used", 0))
            if not is_live_ai_enabled():
                result = InvestigationResult(
                    dataset_id=context.dataset_id,
                    goal=goal,
                    status="error",
                    summary=None,
                    error="Live AI Mode is disabled in this environment; use Guided Deterministic Mode.",
                )
            elif used >= MAX_SESSION_LIVE_RUNS:
                result = InvestigationResult(
                    dataset_id=context.dataset_id,
                    goal=goal,
                    status="error",
                    summary=None,
                    error=f"Session Live AI limit ({MAX_SESSION_LIVE_RUNS}) reached; use Guided Deterministic Mode.",
                )
            else:
                with _LIVE_RUN_LOCK:
                    if _GLOBAL_LIVE_RUNS >= MAX_GLOBAL_LIVE_RUNS:
                        result = InvestigationResult(
                            dataset_id=context.dataset_id,
                            goal=goal,
                            status="error",
                            summary=None,
                            error=f"Global Live AI limit ({MAX_GLOBAL_LIVE_RUNS}) reached; use Guided Deterministic Mode.",
                        )
                    else:
                        _GLOBAL_LIVE_RUNS += 1
                        st.session_state["live_runs_used"] = used + 1
                        result = None
                if result is None:
                    result = run_investigation(context, goal)
    finally:
        st.session_state["investigation_running"] = False

    st.session_state["investigation_mode"] = mode
    st.session_state["investigation_result"] = result
    st.session_state["report"] = build_report(context, result)
    return result


def _render_workspace_header(context: DatasetContext | None) -> None:
    """Render compact workspace header with state badge, dataset info, and quick actions."""
    status_text, status_color = get_factual_status()
    st.markdown(
        f"""
        <div style="margin-top: 0.15rem; margin-bottom: 0.35rem;">
            <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
                <span class="ds-kicker" style="margin-bottom:0;">DataSleuth AI Workspace</span>
                <span class="ds-status-pill" style="border: 1px solid {status_color}45; background: {status_color}14; color: {status_color}; font-size:0.72rem; padding:3px 9px; line-height:1.2;">
                    <span style="display:inline-block; width:6px; height:6px; border-radius:50%; background:{status_color};"></span>
                    {html.escape(status_text)}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if context is not None:
        source_type = st.session_state.get("dataset_source_type", "uploaded")
        source_label = "Synthetic Sample" if source_type == "sample" else "Uploaded CSV"
        bar_col, act_col1, act_col2 = st.columns([3.4, 1.3, 1.3])
        with bar_col:
            st.markdown(
                f"""
                <div style="background:#101E31; border:1px solid #1E3352; border-radius:8px; padding:9px 14px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px;">
                    <span style="font-size:0.86rem; color:#E2E8F0;">
                        <b>Active Dataset:</b> <span style="font-family:monospace; color:#22D3EE;">{html.escape(context.filename)}</span>
                        <span class="ds-badge ds-badge-confidence" style="margin-left:8px;">{html.escape(source_label)}</span>
                    </span>
                    <span style="font-family:monospace; font-size:0.78rem; color:#94A3B8;">
                        {len(context.dataframe):,} rows · {len(context.dataframe.columns)} cols
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with act_col1:
            if st.button("Start Investigation", key="ws_start_inv", type="primary", use_container_width=True):
                st.session_state["active_view"] = "Investigation"
                st.rerun()
        with act_col2:
            if st.button("Change Dataset", key="ws_change_ds", type="secondary", use_container_width=True):
                st.session_state["app_experience"] = "onboarding"
                st.session_state["clear_uploader"] = True
                st.rerun()
    else:
        bar_col, act_col = st.columns([4.2, 1.6])
        with bar_col:
            st.markdown(
                """
                <div style="background:#101E31; border:1px dashed #1E3352; border-radius:8px; padding:9px 14px; font-size:0.86rem; color:#94A3B8;">
                    No active dataset loaded. Select a synthetic sample or upload a CSV to begin.
                </div>
                """,
                unsafe_allow_html=True,
            )
        with act_col:
            if st.button("Select Dataset", key="ws_select_ds", type="primary", use_container_width=True):
                st.session_state["app_experience"] = "onboarding"
                st.rerun()


def main() -> None:
    st.set_page_config(
        page_title="DataSleuth AI",
        page_icon="🔎",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _initialize_state()
    if st.session_state.pop("clear_uploader", False):
        st.session_state.pop("csv_uploader", None)

    experience: str = st.session_state.get("app_experience", "landing")
    context: DatasetContext | None = st.session_state.get("dataset_context")

    inject_custom_styles(hide_sidebar=(experience != "workspace"))

    if experience == "landing":
        def _launch_workspace() -> None:
            st.session_state["app_experience"] = "onboarding"
            st.session_state["clear_uploader"] = True

        def _resume_workspace() -> None:
            st.session_state["app_experience"] = "workspace"

        render_landing_page(
            on_launch_workspace=_launch_workspace,
            on_resume_workspace=_resume_workspace if context is not None else None,
            active_dataset_name=context.filename if context is not None else None,
        )
        return

    if experience == "onboarding":
        def _back_home() -> None:
            st.session_state["app_experience"] = "landing"

        def _resume_from_onboarding() -> None:
            st.session_state["app_experience"] = "workspace"

        render_onboarding_view(
            on_back_home=_back_home,
            on_load_sample=_load_sample_dataset,
            on_upload=_load_uploaded_dataset,
            active_context=context,
            on_resume_workspace=_resume_from_onboarding if context is not None else None,
        )
        return

    # Workspace experience (with sidebar)
    _render_workspace_header(context)
    context = st.session_state["dataset_context"]
    result: InvestigationResult | None = st.session_state["investigation_result"]
    report: dict[str, Any] | None = st.session_state["report"]

    active_view = render_sidebar(context)

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
