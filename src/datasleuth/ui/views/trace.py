"""Execution Trace view: Complete audit trail of autonomous tool executions."""

from __future__ import annotations

import html
import streamlit as st

from datasleuth.models import InvestigationResult


def render_trace_view(result: InvestigationResult | None) -> None:
    """Render the Execution Trace workspace."""
    st.markdown(
        """
        <div style="border-bottom:1px solid #1F293D; padding-bottom:0.75rem; margin-bottom:1rem;">
            <div class="ds-kicker">Audit Trail & Verification</div>
            <h2 style="margin:0; font-size:1.6rem;">Execution Trace</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if result is None or not result.steps:
        st.markdown(
            """
            <div class="ds-empty-state">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">🔍</div>
                <div class="ds-empty-state-title">No Execution Steps Recorded</div>
                <div class="ds-empty-state-desc">
                    Run an investigation in the <b>Investigation Center</b> to view the ordered tool execution sequence, parameters, and observed metrics.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Compact trace summary metrics
    total_steps = len(result.steps)
    successful_steps = sum(1 for s in result.steps if s.result.get("status") == "success")
    skipped_steps = sum(1 for s in result.steps if s.result.get("status") == "skipped")
    failed_steps = total_steps - successful_steps - skipped_steps

    st.subheader("Investigation trace")
    t_cols = st.columns(4)
    t_cols[0].metric("Total Tool Executions", str(total_steps))
    t_cols[1].metric("Successful Calls", str(successful_steps))
    t_cols[2].metric("Skipped Calls", str(skipped_steps))
    t_cols[3].metric("Failed Calls", str(failed_steps))

    st.caption("Expand steps below to review execution arguments, observed numerical metrics, and bounded JSON evidence.")

    for index, step in enumerate(result.steps, start=1):
        tool_result = step.result
        status = tool_result.get("status", "unknown")
        status_color = "#34D399" if status == "success" else ("#F59E0B" if status == "skipped" else "#F87171")

        with st.expander(f"Step {index} · {step.tool_name} · [{status}]", expanded=(index == total_steps)):
            st.markdown(
                f"""
                <div style="display:flex; gap:16px; font-size:0.82rem; margin-bottom:10px; border-bottom:1px solid #1F293D; padding-bottom:6px;">
                    <span style="color:#94A3B8;">Tool: <b style="color:#F8FAFC;">{html.escape(step.tool_name)}</b></span>
                    <span style="color:#94A3B8;">Call ID: <code style="color:#38BDF8;">{html.escape(step.call_id)}</code></span>
                    <span style="color:{status_color}; font-weight:600;">Status: {html.escape(status.upper())}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            p_col, m_col = st.columns(2)
            with p_col:
                st.caption("Tool Arguments")
                st.json(step.arguments)
            with m_col:
                if status == "success":
                    st.caption("Observed Metrics")
                    st.json(tool_result.get("metrics", {}))
                else:
                    st.error(tool_result.get("error", "Execution failed"))

            if tool_result.get("evidence"):
                with st.expander("Bounded Technical Evidence", expanded=False):
                    st.json(tool_result["evidence"])

            for warning in tool_result.get("warnings", []):
                st.warning(warning)
