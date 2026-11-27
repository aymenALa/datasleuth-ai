"""Investigation Center view: Mode selection, 7-stage lifecycle, execution, and model interpretation."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

from datasleuth.config import MAX_SESSION_LIVE_RUNS
from datasleuth.groq_client import is_live_ai_enabled
from datasleuth.models import DatasetContext, InvestigationResult
from datasleuth.ui.formatters import sanitize_model_markdown

SUGGESTED_OBJECTIVES = [
    "Identify the most important data-quality risks and explain the evidence.",
    "Investigate missing values, affected columns, and potential sample bias.",
    "Examine redundant full-row duplicates and detect statistical outlier candidates.",
    "Review column schema consistency and inspect for mixed or incompatible types.",
]


def _render_lifecycle_bar(
    context: DatasetContext,
    result: InvestigationResult | None,
    report: dict[str, Any] | None,
) -> None:
    """Render the actual 7-stage investigation lifecycle based on real state."""

    has_dataset = context is not None
    has_result = result is not None
    has_steps = bool(result and result.steps)
    has_report = report is not None
    is_failed = bool(result and result.status == "error")

    stages = [
        ("01", "Ingest & Validate", "done" if has_dataset else "pending"),
        ("02", "Dataset Profiling", "done" if has_steps else ("ready" if has_dataset else "pending")),
        ("03", "Tool Selection", "error" if is_failed and not has_steps else ("done" if has_steps else "pending")),
        ("04", "Python Execution", "error" if is_failed and not has_steps else ("done" if has_steps else "pending")),
        ("05", "Evidence Gate", "done" if has_report and not is_failed else ("error" if is_failed else "pending")),
        ("06", "Findings & Advice", "done" if has_report and not is_failed else "pending"),
        ("07", "Report Ready", "done" if has_report else "pending"),
    ]

    cards = []
    for num, label, state in stages:
        if state == "done":
            border, color, tag = "#2DD4BF", "#2DD4BF", "VERIFIED"
        elif state == "ready":
            border, color, tag = "#22D3EE", "#22D3EE", "READY"
        elif state == "error":
            border, color, tag = "#F87171", "#F87171", "HALTED"
        else:
            border, color, tag = "#1E3352", "#64748B", "PENDING"
        cards.append(
            f'<div style="background:#101E31; border:1px solid {border}; border-radius:8px; padding:8px 10px;">'
            f'<div style="display:flex; justify-content:space-between; font-family:monospace; font-size:0.66rem; color:{color}; font-weight:700;">'
            f'<span>{num}</span><span>{tag}</span></div>'
            f'<div style="font-size:0.8rem; font-weight:600; color:#F1F5F9; margin-top:3px;">{html.escape(label)}</div>'
            f'</div>'
        )

    st.markdown(
        '<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(130px, 1fr)); gap:8px; margin-bottom:1.1rem;">'
        + "".join(cards)
        + "</div>",
        unsafe_allow_html=True,
    )


def render_investigation_view(
    context: DatasetContext | None,
    result: InvestigationResult | None,
    report: dict[str, Any] | None,
    on_execute: Any,
) -> None:
    """Render the Investigation Center workspace."""
    st.markdown(
        """
        <div style="border-bottom:1px solid #1E3352; padding-bottom:0.75rem; margin-bottom:1rem;">
            <div class="ds-kicker">Autonomous &amp; Deterministic Intelligence</div>
            <h2 style="margin:0; font-size:1.6rem;">Investigation Center</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if context is None:
        st.markdown(
            """
            <div class="ds-empty-state">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚡</div>
                <div class="ds-empty-state-title">No Dataset Available to Investigate</div>
                <div class="ds-empty-state-desc">
                    Load a sample dataset or upload a UTF-8 CSV in <b>Overview</b> before running an investigation.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    _render_lifecycle_bar(context, result, report)

    st.subheader("Autonomous investigation")
    st.caption(
        "Choose an execution mode and define an analytical goal. Allowlisted read-only tools profile data quality facts."
    )

    groq_ready = is_live_ai_enabled()
    live_runs_used = int(st.session_state.get("live_runs_used", 0))
    live_quota_left = max(0, MAX_SESSION_LIVE_RUNS - live_runs_used)

    mode_options = ["Guided Deterministic Mode (No API Key)"]
    if groq_ready and live_quota_left > 0:
        mode_options.append("Live AI Mode (Groq Autonomous Agent)")

    selected_mode_label = st.radio(
        "Investigation execution mode",
        mode_options,
        index=0,
        horizontal=True,
        key="investigation_mode_selector",
    )
    selected_mode = "live_ai" if selected_mode_label.startswith("Live AI") else "guided"

    if not groq_ready:
        st.info(
            "Live AI Mode is disabled because `GROQ_API_KEY` is not configured in the server environment. "
            "Guided Deterministic Mode is active and runs the real local Python tools with zero API key."
        )
    elif live_quota_left == 0:
        st.warning(
            f"Session Live AI limit ({MAX_SESSION_LIVE_RUNS} runs) reached to protect API quota. "
            "Guided Deterministic Mode remains available."
        )
    elif selected_mode == "live_ai":
        st.caption(f"Live AI session budget remaining: {live_quota_left} of {MAX_SESSION_LIVE_RUNS} runs.")

    # Objective quick suggestions
    st.markdown(
        "<div style='font-size:0.78rem; font-weight:600; color:#94A3B8; margin-bottom:4px; letter-spacing:0.04em;'>SUGGESTED OBJECTIVES:</div>",
        unsafe_allow_html=True,
    )
    suggestion_cols = st.columns(2)
    for i, objective in enumerate(SUGGESTED_OBJECTIVES):
        with suggestion_cols[i % 2]:
            if st.button(f"• {objective}", key=f"sug_{i}", use_container_width=True):
                st.session_state["investigation_goal"] = objective
                st.rerun()

    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

    goal = st.text_area(
        "Investigation goal",
        key="investigation_goal",
        help="Specify quality concerns or audit objectives to guide the investigation.",
    )

    if selected_mode == "live_ai":
        st.markdown(
            """
            <div style="background:#101E31; border:1px solid #1E3352; border-radius:6px; padding:8px 12px; margin-bottom:12px; font-size:0.75rem; color:#94A3B8; line-height:1.4;">
                <b style="color:#E2E8F0;">Privacy &amp; Data Transmission (Live AI):</b> Raw CSV records are analyzed locally using deterministic read-only tools. Dataset metadata (column names, types, counts) and bounded tool evidence are sent to Groq API endpoints. Do not upload confidential PII.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="background:#101E31; border:1px solid #1E3352; border-radius:6px; padding:8px 12px; margin-bottom:12px; font-size:0.75rem; color:#94A3B8; line-height:1.4;">
                <b style="color:#2DD4BF;">Local Execution (Guided Deterministic Mode):</b> Runs a predefined bounded sequence of local Python tools (<code>profile_dataset</code>, <code>analyze_missing_values</code>, <code>detect_duplicates</code>, <code>inspect_column</code>, <code>detect_outliers</code>). Zero external API calls are made.
            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.button("Run investigation", type="primary", width="stretch"):
        if not goal.strip():
            st.warning("Enter an investigation goal before running.")
            return
        spinner_msg = (
            "Running Live AI autonomous investigation via Groq…"
            if selected_mode == "live_ai"
            else "Running Guided Deterministic Python investigation…"
        )
        with st.spinner(spinner_msg):
            on_execute(context, goal.strip(), mode=selected_mode)
        st.rerun()

    # Status feedback
    if result is not None:
        st.markdown("<div style='margin-top:1.25rem;'></div>", unsafe_allow_html=True)
        last_mode = st.session_state.get("investigation_mode", "live_ai")
        mode_badge = (
            "Live AI (Groq Autonomous Agent)"
            if last_mode == "live_ai"
            else "Guided Deterministic Mode (Local Python Only)"
        )
        st.caption(f"Execution mode: **{mode_badge}**")

        if result.status == "complete":
            st.success("Investigation completed successfully.")
        elif result.status == "incomplete":
            st.warning("Investigation incomplete. Findings cover executed checks only.")
        else:
            st.error(result.error or "Investigation failed.")

        # Safe Model Interpretation (only present in Live AI mode when model responded)
        if report and report.get("model_interpretation"):
            st.markdown("<div style='margin-top:1.25rem;'></div>", unsafe_allow_html=True)
            st.subheader("Model interpretation")

            sanitized = sanitize_model_markdown(report["model_interpretation"])
            st.markdown(
                """
                <div class="ds-model-interpretation">
                    <div class="ds-model-disclaimer">
                        <span>🤖</span> AI interpretation — not independently verified evidence
                    </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(sanitized)
            st.markdown("</div>", unsafe_allow_html=True)
            st.caption(
                "Numerical facts and verified findings are established by executed tools; the narrative above is an LLM synthesis."
            )
        elif last_mode == "guided" and result.status == "complete":
            st.info(
                "Guided Deterministic Mode executed local Python tools only — no LLM narrative was generated. "
                "Inspect **Findings**, **Recommendations**, **Execution Trace**, and **Reports** in the sidebar."
            )
