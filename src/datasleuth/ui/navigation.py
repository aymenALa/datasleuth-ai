"""Sidebar workspace shell and navigation component."""

from __future__ import annotations

import html
import streamlit as st

from datasleuth.models import DatasetContext
from datasleuth.ui.brand import datasleuth_logo_svg


NAVIGATION_VIEWS = [
    "Overview",
    "Dataset Explorer",
    "Investigation",
    "Findings",
    "Recommendations",
    "Execution Trace",
    "Reports",
]

NAVIGATION_ICONS = {
    "Overview": ":material/dashboard:",
    "Dataset Explorer": ":material/table_chart:",
    "Investigation": ":material/bolt:",
    "Findings": ":material/crisis_alert:",
    "Recommendations": ":material/verified_user:",
    "Execution Trace": ":material/terminal:",
    "Reports": ":material/description:",
}

_RESULT_VIEWS = {"Findings", "Recommendations", "Execution Trace", "Reports"}


def get_factual_status() -> tuple[str, str]:
    """Derive real status strictly from application state without simulated claims."""
    if st.session_state.get("app_experience") == "landing":
        return "Landing", "#22D3EE"
    if st.session_state.get("upload_error"):
        return "Validation error", "#F87171"
    context = st.session_state.get("dataset_context")
    if context is None:
        return "Awaiting dataset", "#94A3B8"
    if st.session_state.get("investigation_running"):
        return "Investigation running", "#22D3EE"
    result = st.session_state.get("investigation_result")
    if result is None:
        return "Dataset loaded", "#2DD4BF"
    if result.status == "complete":
        return "Investigation completed", "#2DD4BF"
    if result.status == "incomplete":
        return "Investigation incomplete", "#F59E0B"
    return "Investigation failed", "#F87171"


def render_sidebar(context: DatasetContext | None) -> str:
    """Render workspace sidebar shell with real identity, dataset status, and navigation."""
    with st.sidebar:
        st.markdown(
            f"""
            <div class="ds-sidebar-brand">
                {datasleuth_logo_svg(28)}
                DataSleuth AI
            </div>
            <div class="ds-sidebar-sub">
                Data Quality Intelligence
            </div>
            """,
            unsafe_allow_html=True,
        )

        status_text, status_color = get_factual_status()
        st.markdown(
            f"""
            <div style="margin-bottom: 1rem;">
                <span class="ds-status-pill" style="border: 1px solid {status_color}45; background: {status_color}14; color: {status_color}; font-size: 0.74rem;">
                    <span style="display:inline-block; width:6px; height:6px; border-radius:50%; background:{status_color};"></span>
                    {html.escape(status_text)}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.caption("WORKSPACE")

        report = st.session_state.get("report")
        findings_count = len(report.get("verified_findings", [])) if report else 0
        recom_count = len(report.get("cleaning_recommendations", [])) if report else 0
        current_view = st.session_state.get("active_view", "Overview")

        for dest in NAVIGATION_VIEWS:
            is_active = current_view == dest
            badge = ""
            if dest == "Findings":
                badge = f" :gray[({findings_count})]" if report else " :gray[(—)]"
            elif dest == "Recommendations":
                badge = f" :gray[({recom_count})]" if report else " :gray[(—)]"
            elif dest in _RESULT_VIEWS and report is None:
                badge = " :gray[(—)]"

            btn_label = f"{dest}{badge}"
            btn_key = f"nav_btn_{dest.replace(' ', '_')}"
            icon = NAVIGATION_ICONS.get(dest, ":material/arrow_right:")

            clicked = st.button(
                btn_label,
                key=btn_key,
                icon=icon,
                use_container_width=True,
                type="primary" if is_active else "secondary",
            )
            if clicked and not is_active:
                st.session_state["active_view"] = dest
                st.rerun()

        st.divider()

        if context is not None:
            source_type = st.session_state.get("dataset_source_type", "uploaded")
            source_label = "Synthetic Sample" if source_type == "sample" else "Uploaded CSV"
            st.caption("ACTIVE DATASET")
            st.markdown(
                f"""
                <div style="background:#101E31; border:1px solid #1E3352; border-radius:8px; padding:10px 12px; margin-bottom:10px;">
                    <div style="font-size:0.84rem; font-weight:600; color:#F1F5F9; word-break:break-all; margin-bottom:4px;">
                        {html.escape(context.filename)}
                    </div>
                    <div style="font-family:monospace; font-size:0.71rem; color:#22D3EE; margin-bottom:4px;">
                        {html.escape(source_label)}
                    </div>
                    <div style="font-size:0.75rem; color:#94A3B8;">
                        <b style="color:#E2E8F0;">{len(context.dataframe):,}</b> rows · <b style="color:#E2E8F0;">{len(context.dataframe.columns)}</b> cols
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Change Dataset", key="sidebar_change_dataset", type="secondary", use_container_width=True):
                st.session_state["app_experience"] = "onboarding"
                st.session_state["clear_uploader"] = True
                st.rerun()
        else:
            st.caption("DATASET SOURCE")
            st.markdown(
                """
                <div style="background:#101E31; border:1px dashed #1E3352; border-radius:8px; padding:10px 12px; margin-bottom:10px; font-size:0.76rem; color:#94A3B8; line-height:1.4;">
                    No dataset loaded yet. Select a sample or upload a CSV.
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Select Dataset", key="sidebar_select_dataset", type="primary", use_container_width=True):
                st.session_state["app_experience"] = "onboarding"
                st.rerun()

        if st.button("← Back to Home", key="sidebar_back_home", type="secondary", use_container_width=True):
            st.session_state["app_experience"] = "landing"
            st.rerun()

        st.caption("DataSleuth AI v0.1.0 · Read-only Engine · Groq Orchestration")

    return st.session_state.get("active_view", "Overview")
