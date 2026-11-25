"""Recommendation Center view: Structured cleaning recommendations and precision-controlled advice."""

from __future__ import annotations

import html
from typing import Any
import streamlit as st

from datasleuth.ui.formatters import (
    format_classification_label,
    format_precision_in_text,
)


def render_recommendations_view(report: dict[str, Any] | None) -> None:
    """Render the Recommendation Center workspace."""
    st.markdown(
        """
        <div style="border-bottom:1px solid #1F293D; padding-bottom:0.75rem; margin-bottom:1rem;">
            <div class="ds-kicker">Prescriptive Guidance</div>
            <h2 style="margin:0; font-size:1.6rem;">Recommendation Center</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if report is None:
        st.markdown(
            """
            <div class="ds-empty-state">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">💡</div>
                <div class="ds-empty-state-title">No Recommendations Available</div>
                <div class="ds-empty-state-desc">
                    Execute an investigation in the <b>Investigation Center</b> to generate evidence-based cleaning recommendations.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.subheader("Cleaning recommendations")
    st.caption("Advisory only — recommendations are evidence-based suggestions and never modify your source dataset.")

    recommendations = report.get("cleaning_recommendations", [])
    if not recommendations:
        st.info("No recommendations were generated from the executed checks.")
        return

    # Search and filter
    r_col1, r_col2 = st.columns([3, 1])
    with r_col1:
        search_query = st.text_input("Search recommendations", placeholder="Filter recommendations by issue…", key="recom_search")
    with r_col2:
        classifications = ["All Classifications"] + sorted(list({r.get("evidence_classification", "") for r in recommendations if r.get("evidence_classification")}))
        class_filter = st.selectbox("Classification", classifications, key="recom_class_filter")

    filtered = recommendations
    if search_query.strip():
        q = search_query.strip().lower()
        filtered = [r for r in filtered if q in r.get("issue", "").lower()]
    if class_filter != "All Classifications":
        filtered = [r for r in filtered if r.get("evidence_classification") == class_filter]

    st.caption(f"Showing {len(filtered)} of {len(recommendations)} recommendations.")

    if not filtered:
        st.markdown(
            """
            <div class="ds-empty-state">
                <div class="ds-empty-state-title">No Matching Recommendations</div>
                <div class="ds-empty-state-desc">No recommendations matched your filter criteria.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for recommendation in filtered:
        classification = recommendation.get("evidence_classification", "")
        badge_class = "ds-badge-fact" if classification == "measured_fact" else "ds-badge-candidate"
        class_label = format_classification_label(classification)

        impact_text = format_precision_in_text(str(recommendation.get("potential_analytical_impact", "")))
        follow_up_text = format_precision_in_text(str(recommendation.get("suggested_follow_up", "")))
        options_text = format_precision_in_text(str(recommendation.get("conditional_treatment_options", "")))
        risks_text = format_precision_in_text(str(recommendation.get("risks_and_assumptions", "")))
        validation_text = format_precision_in_text(str(recommendation.get("post_treatment_validation", "")))

        with st.container(border=True):
            st.markdown(
                f"""
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
                    <div style="font-size:1.02rem; font-weight:700; color:#F8FAFC;">{html.escape(recommendation.get('issue', ''))}</div>
                    <div>
                        <span class="ds-badge {badge_class}">{html.escape(class_label)}</span>
                        <span class="ds-badge ds-badge-confidence" style="margin-left:4px;">confidence: {html.escape(str(recommendation.get('confidence', '')))}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
                <div class="ds-recom-grid">
                    <div class="ds-recom-item">
                        <div class="ds-recom-label">Potential Analytical Impact</div>
                        <div class="ds-recom-val">{html.escape(impact_text)}</div>
                    </div>
                    <div class="ds-recom-item">
                        <div class="ds-recom-label">Suggested Follow-Up</div>
                        <div class="ds-recom-val">{html.escape(follow_up_text)}</div>
                    </div>
                    <div class="ds-recom-item">
                        <div class="ds-recom-label">Conditional Treatment Options</div>
                        <div class="ds-recom-val">{html.escape(options_text)}</div>
                    </div>
                    <div class="ds-recom-item" style="border-left: 3px solid #F59E0B;">
                        <div class="ds-recom-label" style="color:#F59E0B;">Risks & Assumptions</div>
                        <div class="ds-recom-val">{html.escape(risks_text)}</div>
                    </div>
                </div>
                <div style="margin-top:8px; font-size:0.8rem; color:#94A3B8; background:#0B1120; padding:6px 10px; border-radius:6px; border:1px solid #1F293D;">
                    <b style="color:#38BDF8;">Post-treatment validation:</b> {html.escape(validation_text)}
                </div>
                """,
                unsafe_allow_html=True,
            )
