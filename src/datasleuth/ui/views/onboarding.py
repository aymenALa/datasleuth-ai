"""Dedicated Dataset Onboarding view: Upload a CSV or load a bundled synthetic sample."""

from __future__ import annotations

import html
from typing import Any, Callable

import streamlit as st

from datasleuth.models import DatasetContext
from datasleuth.sample_datasets import list_sample_datasets, read_sample_csv_bytes
from datasleuth.ui.brand import datasleuth_logo_svg


def render_onboarding_view(
    *,
    on_back_home: Callable[[], None],
    on_load_sample: Callable[[str], None],
    on_upload: Callable[[Any], None],
    active_context: DatasetContext | None = None,
    on_resume_workspace: Callable[[], None] | None = None,
) -> None:
    """Render the dedicated dataset selection and validation experience."""

    # Top onboarding header bar
    nav_c1, nav_c2, nav_c3 = st.columns([3, 1.2, 1.4])
    with nav_c1:
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:10px;">
                {datasleuth_logo_svg(30)}
                <div>
                    <div class="ds-kicker" style="margin:0;">Dataset Onboarding</div>
                    <div style="font-size:1.15rem; font-weight:700; color:#F1F5F9;">Select or Upload a CSV Dataset</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with nav_c2:
        if active_context is not None and on_resume_workspace is not None:
            if st.button("Resume Workspace →", key="onb_resume_ws", type="secondary", use_container_width=True):
                on_resume_workspace()
                st.rerun()
    with nav_c3:
        if st.button("← Back to Home", key="onb_back_home", type="secondary", use_container_width=True):
            on_back_home()
            st.rerun()

    st.markdown(
        """
        <div style="background:#101E31; border:1px solid #1E3352; border-radius:10px; padding:12px 16px; margin:0.75rem 0 1.25rem 0; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
            <div style="font-size:0.86rem; color:#94A3B8;">
                <b style="color:#F1F5F9;">Status:</b> Awaiting dataset selection. Ingestion runs local UTF-8, header, row-width, and size validation without calling any LLM.
            </div>
            <div style="font-family:monospace; font-size:0.75rem; color:#22D3EE;">
                Limits: 10 MB · 50,000 rows · 100 columns
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Option 1: Upload custom CSV
    st.subheader("Option 1 — Upload a custom CSV")
    uploaded_file = st.file_uploader(
        "Upload a CSV file",
        type=["csv"],
        key="csv_uploader",
        label_visibility="collapsed",
    )
    if uploaded_file is not None:
        with st.status("Validating uploaded CSV…", expanded=False):
            on_upload(uploaded_file)
        if st.session_state.get("dataset_context") is not None and not st.session_state.get("upload_error"):
            st.rerun()

    current_error = st.session_state.get("upload_error")
    if current_error:
        st.error(f"CSV could not be loaded: {current_error}")
    else:
        st.info("Upload a UTF-8 CSV to begin. The existing ingestion limits are enforced (max 10 MB, 50,000 rows, 100 columns).")

    st.divider()

    # Option 2: Load a bundled synthetic sample dataset
    st.subheader("Option 2 — Load a synthetic sample dataset")
    st.caption(
        "Each sample is ingested directly through the genuine CSV validation pipeline and loads into the Workspace Overview."
    )

    sample_list = list_sample_datasets()
    sample_cols = st.columns(2)
    for idx, sample in enumerate(sample_list):
        scenarios_html = "".join(
            f'<span class="ds-col-tag" style="font-size:0.72rem;">{html.escape(s)}</span>'
            for s in sample.scenarios
        )
        with sample_cols[idx % 2]:
            with st.container(border=True):
                st.markdown(
                    f"""
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                        <span style="font-weight:700; color:#F1F5F9; font-size:1rem;">{html.escape(sample.title)}</span>
                        <span class="ds-badge ds-badge-fact">{html.escape(sample.domain)}</span>
                    </div>
                    <div style="font-family:monospace; font-size:0.75rem; color:#22D3EE; margin-bottom:6px;">
                        {html.escape(sample.filename)} · {sample.row_count:,} rows · {sample.column_count} cols
                    </div>
                    <div style="font-size:0.82rem; color:#94A3B8; line-height:1.45; margin-bottom:8px;">{html.escape(sample.description)}</div>
                    <div style="margin-bottom:10px;">{scenarios_html}</div>
                    """,
                    unsafe_allow_html=True,
                )
                btn_c1, btn_c2 = st.columns([3, 2])
                with btn_c1:
                    if st.button(
                        "Load Sample Dataset",
                        key=f"onb_sample_{sample.key}",
                        type="primary",
                        use_container_width=True,
                    ):
                        with st.status(f"Validating {sample.filename}…", expanded=False):
                            on_load_sample(sample.key)
                        st.rerun()
                with btn_c2:
                    st.download_button(
                        "Download CSV",
                        data=read_sample_csv_bytes(sample.key),
                        file_name=sample.filename,
                        mime="text/csv",
                        key=f"onb_dl_{sample.key}",
                        use_container_width=True,
                    )
