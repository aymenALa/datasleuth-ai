"""Sidebar workspace shell and navigation component."""

from __future__ import annotations

import html
import streamlit as st

from datasleuth.models import DatasetContext


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


def get_factual_status() -> tuple[str, str]:
    """Derive real status strictly from application state without simulated claims."""
    if st.session_state.get("upload_error"):
        return "Upload error", "#F87171"
    context = st.session_state.get("dataset_context")
    if context is None:
        return "Awaiting dataset", "#94A3B8"
    result = st.session_state.get("investigation_result")
    if result is None:
        return "Dataset loaded", "#34D399"
    if result.status == "complete":
        return "Investigation complete", "#34D399"
    if result.status == "incomplete":
        return "Investigation incomplete", "#F59E0B"
    return "Investigation failed", "#F87171"


def render_sidebar(context: DatasetContext | None) -> str:
    """Render workspace sidebar shell with real identity, dataset status, and navigation."""
    with st.sidebar:
        st.markdown(
            """
            <div class="ds-sidebar-brand">
                <span class="ds-sidebar-brand-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="11" cy="11" r="8"></circle>
                        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                        <line x1="11" y1="8" x2="11" y2="14"></line>
                        <line x1="8" y1="11" x2="14" y2="11"></line>
                    </svg>
                </span>
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
            <div style="margin-bottom: 1.15rem;">
                <span class="ds-status-pill" style="border: 1px solid {status_color}45; background: {status_color}14; color: {status_color}; font-size: 0.74rem;">
                    <span style="display:inline-block; width:6px; height:6px; border-radius:50%; background:{status_color};"></span>
                    {html.escape(status_text)}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.caption("WORKSPACE")

        # Build dynamic badge counts from verified data
        report = st.session_state.get("report")
        findings_count = len(report.get("verified_findings", [])) if report else 0
        recom_count = len(report.get("cleaning_recommendations", [])) if report else 0

        current_view = st.session_state.get("active_view", "Overview")

        # Render full-width navigation rows using native Streamlit buttons with stable keys
        for dest in NAVIGATION_VIEWS:
            is_active = (current_view == dest)
            badge = ""
            if dest == "Findings" and findings_count > 0:
                badge = f" :gray[({findings_count})]"
            elif dest == "Recommendations" and recom_count > 0:
                badge = f" :gray[({recom_count})]"

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

        # Active dataset info card in sidebar
        if context is not None:
            st.caption("ACTIVE DATASET")
            st.markdown(
                f"""
                <div style="background:#131C2E; border:1px solid #1E2C42; border-radius:8px; padding:10px 12px; margin-bottom:12px;">
                    <div style="font-size:0.84rem; font-weight:600; color:#F1F5F9; word-break:break-all; margin-bottom:4px; display:flex; align-items:center; gap:6px;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#38BDF8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                            <polyline points="14 2 14 8 20 8"></polyline>
                        </svg>
                        {html.escape(context.filename)}
                    </div>
                    <div style="font-size:0.75rem; color:#94A3B8;">
                        <b style="color:#E2E8F0;">{len(context.dataframe):,}</b> rows · <b style="color:#E2E8F0;">{len(context.dataframe.columns)}</b> cols
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.caption("DATASET SOURCE")
            st.markdown(
                """
                <div style="background:#131C2E; border:1px dashed #1E2C42; border-radius:8px; padding:10px 12px; margin-bottom:12px; font-size:0.76rem; color:#94A3B8; line-height:1.4;">
                    No dataset loaded yet. Upload a CSV to enable intelligence tools.
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.caption("DataSleuth AI v0.1.0 · Read-only Engine · Groq Orchestration")

    return st.session_state.get("active_view", "Overview")
