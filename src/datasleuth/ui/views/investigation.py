"""Investigation Center view: Objective suggestions, goal configuration, execution, and safe model interpretation."""

from __future__ import annotations

from typing import Any
import streamlit as st

from datasleuth.models import DatasetContext, InvestigationResult
from datasleuth.ui.formatters import sanitize_model_markdown

SUGGESTED_OBJECTIVES = [
    "Identify the most important data-quality risks and explain the evidence.",
    "Investigate missing values, affected columns, and potential sample bias.",
    "Examine redundant full-row duplicates and detect statistical outlier candidates.",
    "Review column schema consistency and inspect for mixed or incompatible types.",
]


def render_investigation_view(
    context: DatasetContext | None,
    result: InvestigationResult | None,
    report: dict[str, Any] | None,
    on_execute: Any,
) -> None:
    """Render the Investigation Center workspace."""
    st.markdown(
        """
        <div style="border-bottom:1px solid #1F293D; padding-bottom:0.75rem; margin-bottom:1rem;">
            <div class="ds-kicker">Autonomous Intelligence</div>
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
                    Load a dataset in the <b>Dataset Explorer</b> or sidebar before running an autonomous investigation.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.subheader("Autonomous investigation")
    st.caption(
        "Define an analytical goal to guide tool selection. Allowlisted read-only tools profile data quality facts."
    )

    # Objective quick suggestions
    st.markdown("<div style='font-size:0.8rem; font-weight:600; color:#94A3B8; margin-bottom:4px; letter-spacing:0.04em;'>SUGGESTED OBJECTIVES:</div>", unsafe_allow_html=True)
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
        help="Specify quality concerns or audit objectives to guide the autonomous investigation.",
    )

    st.markdown(
        """
        <div style="background:#111827; border:1px solid #1F293D; border-radius:6px; padding:8px 12px; margin-bottom:12px; font-size:0.75rem; color:#94A3B8; line-height:1.4;">
            <b style="color:#E2E8F0;">Privacy & Data Transmission:</b> Raw CSV records are analyzed locally using deterministic read-only tools. To synthesize findings, dataset metadata (column names, types, counts) and bounded tool evidence (such as top frequent values, sample duplicate positions, and IQR outlier candidates) are transmitted to Groq API endpoints. Do not investigate confidential PII in column headers or sample cell contents.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Run investigation", type="primary", width="stretch"):
        if not goal.strip():
            st.warning("Enter an investigation goal before running.")
            return
        with st.spinner("Running bounded autonomous investigation…"):
            on_execute(context, goal.strip())
        st.rerun()

    # Status feedback
    if result is not None:
        st.markdown("<div style='margin-top:1.25rem;'></div>", unsafe_allow_html=True)
        if result.status == "complete":
            st.success("Investigation completed successfully.")
        elif result.status == "incomplete":
            st.warning("Investigation incomplete. Findings cover executed checks only.")
        else:
            st.error(result.error or "Investigation failed.")

        # Safe Model Interpretation
        if report and report.get("model_interpretation"):
            st.markdown("<div style='margin-top:1.25rem;'></div>", unsafe_allow_html=True)
            st.subheader("Model interpretation")

            sanitized = sanitize_model_markdown(report["model_interpretation"])
            st.markdown(
                f"""
                <div class="ds-model-interpretation">
                    <div class="ds-model-disclaimer">
                        <span>🤖</span> AI interpretation — not independently verified evidence
                    </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(sanitized)
            st.markdown("</div>", unsafe_allow_html=True)
            st.caption("Numerical facts and verified findings are established by executed tools; the narrative above is an LLM synthesis.")
