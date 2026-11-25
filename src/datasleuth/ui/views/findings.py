"""Findings Explorer view: Searchable, filterable verified findings catalog."""

from __future__ import annotations

import html
from typing import Any
import streamlit as st

from datasleuth.ui.view_models import build_finding_view_models


def render_findings_view(report: dict[str, Any] | None) -> None:
    """Render the Findings Explorer workspace."""
    st.markdown(
        """
        <div style="border-bottom:1px solid #1F293D; padding-bottom:0.75rem; margin-bottom:1rem;">
            <div class="ds-kicker">Analytical Discoveries</div>
            <h2 style="margin:0; font-size:1.6rem;">Findings Explorer</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if report is None:
        st.markdown(
            """
            <div class="ds-empty-state">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">🎯</div>
                <div class="ds-empty-state-title">No Investigation Findings Available</div>
                <div class="ds-empty-state-desc">
                    Execute an investigation in the <b>Investigation Center</b> to generate verified data-quality findings with bounded evidence.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    all_findings = build_finding_view_models(report)

    if not all_findings:
        st.info("No verified issue findings were produced from the executed checks.")
        return

    # Filter toolbar
    st.subheader("Verified findings")
    st.caption(f"Review and filter {len(all_findings)} evidence-backed findings verified against deterministic tool metrics.")

    f_col1, f_col2, f_col3 = st.columns([2, 1, 1])
    with f_col1:
        search_term = st.text_input("Search findings", placeholder="Filter by title or affected column…", key="find_search")
    with f_col2:
        class_options = ["All Classifications"] + sorted(list({f.classification_label for f in all_findings}))
        class_filter = st.selectbox("Classification", class_options, key="find_class_filter")
    with f_col3:
        conf_options = ["All Confidence"] + sorted(list({f.confidence_label for f in all_findings}))
        conf_filter = st.selectbox("Confidence", conf_options, key="find_conf_filter")

    # Column dropdown filter
    all_columns_affected = sorted(list({col for f in all_findings for col in f.columns}))
    if all_columns_affected:
        col_select_options = ["All Columns"] + all_columns_affected
        col_filter = st.selectbox("Filter by affected column", col_select_options, key="find_col_filter")
    else:
        col_filter = "All Columns"

    # Filter logic
    filtered = all_findings
    if search_term.strip():
        term = search_term.strip().lower()
        filtered = [
            f for f in filtered
            if term in f.title.lower() or any(term in col.lower() for col in f.columns)
        ]
    if class_filter != "All Classifications":
        filtered = [f for f in filtered if f.classification_label == class_filter]
    if conf_filter != "All Confidence":
        filtered = [f for f in filtered if f.confidence_label == conf_filter]
    if col_filter != "All Columns":
        filtered = [f for f in filtered if col_filter in f.columns]

    st.caption(f"Displaying {len(filtered)} of {len(all_findings)} verified findings.")

    if not filtered:
        st.markdown(
            """
            <div class="ds-empty-state">
                <div class="ds-empty-state-title">No Matching Findings</div>
                <div class="ds-empty-state-desc">No findings matched your current search and filter criteria. Clear filters to see all findings.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for finding in filtered:
        badge_class = "ds-badge-fact" if finding.classification == "measured_fact" else "ds-badge-candidate"

        with st.container(border=True):
            st.markdown(
                f"""
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:4px;">
                    <div style="font-size:1.02rem; font-weight:700; color:#F8FAFC;">{html.escape(finding.title)}</div>
                    <div>
                        <span class="ds-badge {badge_class}">{html.escape(finding.classification_label)}</span>
                        <span class="ds-badge ds-badge-confidence" style="margin-left:4px;">{html.escape(finding.confidence_label)}</span>
                    </div>
                </div>
                <div style="font-size:0.78rem; color:#94A3B8; margin-bottom:8px;">
                    Source: <code style="color:#38BDF8;">{html.escape(finding.tool_name)} / {html.escape(finding.metric_path)}</code>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col1, col2 = st.columns([3, 1])
            with col1:
                cols_html = "".join([f'<span class="ds-col-tag">{html.escape(c)}</span>' for c in finding.columns]) or '<span class="ds-col-tag">dataset-wide</span>'
                st.markdown(f'<div style="font-size:0.82rem; color:#94A3B8;">Affected columns: {cols_html}</div>', unsafe_allow_html=True)
            with col2:
                st.markdown(
                    f'<div style="font-size:0.82rem; color:#94A3B8;">Observed: <b style="color:#F8FAFC; font-family:monospace; font-size:0.95rem;">{html.escape(str(finding.value))}</b></div>',
                    unsafe_allow_html=True,
                )

            if finding.evidence_summary:
                st.caption(f"Evidence metric: {finding.evidence_summary}")

            if finding.evidence_payload:
                with st.expander("Technical Evidence Payload (JSON)", expanded=False):
                    st.json(finding.evidence_payload)
