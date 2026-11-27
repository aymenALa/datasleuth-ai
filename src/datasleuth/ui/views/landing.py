"""Standalone public landing page for DataSleuth AI."""

from __future__ import annotations

import html
from typing import Callable

import streamlit as st

from datasleuth.ui.brand import GITHUB_REPO_URL, datasleuth_logo_svg


def render_landing_page(
    *,
    on_launch_workspace: Callable[[], None],
    on_resume_workspace: Callable[[], None] | None = None,
    active_dataset_name: str | None = None,
) -> None:
    """Render the standalone full-width public landing page without sidebar or workspace clutter."""

    logo_sm = datasleuth_logo_svg(32)

    # Top responsive navigation bar
    st.markdown(
        f"""
        <div class="ds-landing-nav">
            <div class="ds-landing-nav-brand">
                {logo_sm}
                <div>
                    <span class="ds-brand-title">DataSleuth AI</span>
                    <span class="ds-brand-tag">v0.1 · Evidence Engine</span>
                </div>
            </div>
            <div class="ds-landing-nav-links">
                <a href="#capabilities">Capabilities</a>
                <a href="#architecture">Architecture</a>
                <a href="#lifecycle">Lifecycle</a>
                <a href="#reliability">Reliability</a>
                <a href="{GITHUB_REPO_URL}" target="_blank" rel="noopener noreferrer" class="ds-nav-gh">GitHub ↗</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Cinematic Hero Section
    st.markdown(
        """
        <div class="ds-hero" style="margin-bottom: 1.25rem;">
            <div class="ds-hero-badge">
                <span class="ds-pulse-dot"></span>
                AUTONOMOUS DATA QUALITY INTELLIGENCE · READ-ONLY PYTHON ENGINE
            </div>
            <h1 class="ds-hero-title">
                Investigate your data.<br/>
                <span class="ds-hero-gradient">Trust the evidence.</span>
            </h1>
            <p class="ds-hero-subtitle">
                An autonomous AI agent that investigates data quality, verifies findings through
                deterministic Python tools, and delivers actionable insights — without ever mutating
                your source CSV or fabricating statistics.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Primary CTAs (real Streamlit navigation + GitHub link)
    if active_dataset_name and on_resume_workspace is not None:
        _, cta_col1, cta_col2, cta_col3, _ = st.columns([1.2, 2.2, 2.2, 2.0, 1.2])
        with cta_col1:
            if st.button("Resume Investigation →", key="landing_resume_top", type="primary", use_container_width=True):
                on_resume_workspace()
                st.rerun()
        with cta_col2:
            if st.button("Launch Workspace (New Dataset)", key="landing_launch_top", type="secondary", use_container_width=True):
                on_launch_workspace()
                st.rerun()
        with cta_col3:
            st.link_button("View Source Code ↗", GITHUB_REPO_URL, use_container_width=True)
        st.caption(f"Active session dataset preserved: `{html.escape(active_dataset_name)}`")
    else:
        _, cta_col1, cta_col2, _ = st.columns([2.2, 2.2, 2.0, 2.2])
        with cta_col1:
            if st.button("Launch Workspace →", key="landing_launch_top", type="primary", use_container_width=True):
                on_launch_workspace()
                st.rerun()
        with cta_col2:
            st.link_button("View Source Code ↗", GITHUB_REPO_URL, use_container_width=True)

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # Realistic Product Preview (clearly labeled as illustrative)
    st.markdown(
        """
        <div class="ds-preview-shell">
            <div class="ds-preview-topbar">
                <div class="ds-preview-dots">
                    <span></span><span></span><span></span>
                </div>
                <div class="ds-preview-url">datasleuth-ai · workspace / ecommerce_orders.csv</div>
                <div class="ds-preview-pill">ILLUSTRATIVE PREVIEW</div>
            </div>
            <div class="ds-preview-body">
                <div class="ds-preview-kpis">
                    <div class="ds-preview-kpi">
                        <div class="ds-preview-kpi-label">ROWS PROFILED</div>
                        <div class="ds-preview-kpi-val">24</div>
                        <div class="ds-preview-kpi-sub">10 columns · UTF-8 validated</div>
                    </div>
                    <div class="ds-preview-kpi">
                        <div class="ds-preview-kpi-label">MISSING CELLS</div>
                        <div class="ds-preview-kpi-val" style="color:#22D3EE;">4</div>
                        <div class="ds-preview-kpi-sub">1.67% of 240 total cells</div>
                    </div>
                    <div class="ds-preview-kpi">
                        <div class="ds-preview-kpi-label">DUPLICATE ROWS</div>
                        <div class="ds-preview-kpi-val" style="color:#F59E0B;">1</div>
                        <div class="ds-preview-kpi-sub">4.17% redundant full rows</div>
                    </div>
                    <div class="ds-preview-kpi">
                        <div class="ds-preview-kpi-label">VERIFIED FINDINGS</div>
                        <div class="ds-preview-kpi-val" style="color:#2DD4BF;">5</div>
                        <div class="ds-preview-kpi-sub">100% tool-grounded claims</div>
                    </div>
                </div>
                <div class="ds-preview-split">
                    <div class="ds-preview-panel">
                        <div class="ds-preview-panel-title">OBSERVABLE AGENT EXECUTION TRACE</div>
                        <div class="ds-trace-row"><span class="ds-trace-step">01</span><code>profile_dataset()</code><span class="ds-trace-ok">SUCCESS</span></div>
                        <div class="ds-trace-row"><span class="ds-trace-step">02</span><code>analyze_missing_values()</code><span class="ds-trace-ok">SUCCESS</span></div>
                        <div class="ds-trace-row"><span class="ds-trace-step">03</span><code>detect_duplicates(columns=null)</code><span class="ds-trace-ok">SUCCESS</span></div>
                        <div class="ds-trace-row"><span class="ds-trace-step">04</span><code>inspect_column(column="discount_pct")</code><span class="ds-trace-ok">SUCCESS</span></div>
                        <div class="ds-trace-row"><span class="ds-trace-step">05</span><code>detect_outliers(column="order_total", method="iqr")</code><span class="ds-trace-ok">SUCCESS</span></div>
                    </div>
                    <div class="ds-preview-panel">
                        <div class="ds-preview-panel-title">EVIDENCE-VALIDATED FINDING EXAMPLE</div>
                        <div class="ds-finding-sample">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                                <span style="font-weight:600; color:#F1F5F9; font-size:0.86rem;">Statistical outlier candidates in order_total</span>
                                <span class="ds-badge ds-badge-candidate">STATISTICAL CANDIDATE</span>
                            </div>
                            <div style="font-family:monospace; font-size:0.75rem; color:#22D3EE; margin-bottom:6px;">
                                detect_outliers / outlier_candidate_count = 2
                            </div>
                            <div style="font-size:0.78rem; color:#94A3B8; line-height:1.45;">
                                IQR bounds computed locally by Python (Q1=114.75, Q3=456.00, upper=967.88).
                                Flagged candidates are statistical signals, never auto-deleted.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Technology Stack Bar
    st.markdown(
        """
        <div class="ds-stack-bar">
            <span class="ds-stack-label">BUILT WITH</span>
            <span class="ds-stack-pill">Python 3.10+</span>
            <span class="ds-stack-pill">Pandas &amp; NumPy</span>
            <span class="ds-stack-pill">Groq Tool Calling</span>
            <span class="ds-stack-pill">Plotly</span>
            <span class="ds-stack-pill">Streamlit</span>
            <span class="ds-stack-pill">Pytest</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Bento-Grid Capability Showcase
    st.markdown('<div id="capabilities"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="ds-section-head">
            <div class="ds-kicker">Core Capabilities</div>
            <h2>Why DataSleuth is not a generic AI chatbot</h2>
            <p class="ds-section-sub">
                Standard chatbots guess statistics from raw text. DataSleuth separates LLM planning from deterministic Python execution and validates every numerical claim.
            </p>
        </div>
        <div class="ds-bento-grid">
            <div class="ds-bento-card">
                <div class="ds-bento-tag">01 · DETERMINISTIC INGESTION</div>
                <h3>Validated CSV Contract</h3>
                <p>Enforces UTF-8 / UTF-8-BOM decoding, strict header uniqueness, consistent row widths, and size bounds (10 MB / 50,000 rows / 100 columns) before any analysis runs.</p>
            </div>
            <div class="ds-bento-card">
                <div class="ds-bento-tag">02 · BOUNDED AUTONOMY</div>
                <h3>Allowlisted Tool Calling</h3>
                <p>Groq LLM selects only from 5 read-only tools via strict JSON schemas — never arbitrary Python or shell execution.</p>
            </div>
            <div class="ds-bento-card">
                <div class="ds-bento-tag">03 · EXACT METRICS</div>
                <h3>Missingness &amp; Duplicates</h3>
                <p>Computes exact missing-cell percentages, affected row positions, and full-row or key-based redundant duplicate groups.</p>
            </div>
            <div class="ds-bento-card">
                <div class="ds-bento-tag">04 · CONSERVATIVE SIGNALS</div>
                <h3>IQR Outlier Candidates</h3>
                <p>Computes Q1, Q3, IQR, and 1.5× fence bounds in Python. Flags candidates as statistical signals, never confirmed errors.</p>
            </div>
            <div class="ds-bento-card">
                <div class="ds-bento-tag">05 · EVIDENCE GATE</div>
                <h3>Post-Execution Claim Validation</h3>
                <p>Every verified finding is traced back to an actual tool metric path and observed value. LLM narrative is isolated as unverified model interpretation.</p>
            </div>
            <div class="ds-bento-card">
                <div class="ds-bento-tag">06 · AUDITABLE EXPORTS</div>
                <h3>Strict JSON &amp; Escaped Markdown</h3>
                <p>Generates strict JSON (<code>allow_nan=False</code>) and HTML/Markdown-escaped reports with explicit check coverage and limitations.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Dual-Engine Architecture Visualization
    st.markdown('<div id="architecture"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="ds-section-head">
            <div class="ds-kicker">Dual-Engine Architecture</div>
            <h2>LLM Reasoning Separated from Deterministic Computation</h2>
            <p class="ds-section-sub">
                In Live AI mode, Groq receives schema metadata and bounded tool outputs — never full raw CSV dumps.
            </p>
        </div>
        <div class="ds-arch-grid">
            <div class="ds-arch-box ds-arch-llm">
                <div class="ds-arch-label">ENGINE A · ORCHESTRATION PLANNER</div>
                <h4>Groq LLM (<code>openai/gpt-oss-20b</code>)</h4>
                <ul>
                    <li>Receives goal, column names/dtypes, and baseline metrics</li>
                    <li>Selects follow-up tools (<code>inspect_column</code>, <code>detect_outliers</code>)</li>
                    <li>Bounded to max 8 turns and 8 tool calls</li>
                    <li>Output labeled as <em>unverified interpretation</em></li>
                </ul>
            </div>
            <div class="ds-arch-connector">
                <span>JSON Tool Calls →</span>
                <span style="color:#2DD4BF;">← Bounded Metrics</span>
            </div>
            <div class="ds-arch-box ds-arch-py">
                <div class="ds-arch-label">ENGINE B · DETERMINISTIC COMPUTATION</div>
                <h4>Local Python &amp; Pandas Engine</h4>
                <ul>
                    <li>Executes read-only checks on validated <code>DatasetContext</code></li>
                    <li>Never mutates the source DataFrame or CSV</li>
                    <li>Returns compact, JSON-serializable <code>ToolResult</code></li>
                    <li>Feeds <code>validate_investigation()</code> &amp; Plotly charts</li>
                </ul>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 7-Step Investigation Lifecycle
    st.markdown('<div id="lifecycle"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="ds-section-head">
            <div class="ds-kicker">Execution Pipeline</div>
            <h2>7-Stage Investigation Lifecycle</h2>
        </div>
        <div class="ds-lifecycle-grid">
            <div class="ds-life-step"><span>01</span><b>CSV Ingestion</b><small>UTF-8 &amp; shape validation</small></div>
            <div class="ds-life-step"><span>02</span><b>Dataset Profiling</b><small>Dtypes &amp; baseline counts</small></div>
            <div class="ds-life-step"><span>03</span><b>Tool Selection</b><small>Autonomous AI or Guided</small></div>
            <div class="ds-life-step"><span>04</span><b>Python Execution</b><small>Deterministic tool run</small></div>
            <div class="ds-life-step"><span>05</span><b>Evidence Gate</b><small>Metric-path verification</small></div>
            <div class="ds-life-step"><span>06</span><b>Findings &amp; Advice</b><small>Conservative guidance</small></div>
            <div class="ds-life-step"><span>07</span><b>Report Export</b><small>JSON &amp; escaped Markdown</small></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Reliability & Transparency Section
    st.markdown('<div id="reliability"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="ds-section-head">
            <div class="ds-kicker">Reliability &amp; Security Controls</div>
            <h2>Built for transparency, bounded retries, and safe public demos</h2>
        </div>
        <div class="ds-reliability-grid">
            <div class="ds-rel-card">
                <h4>Two Clear Investigation Modes</h4>
                <p><b>Live AI Investigation</b> uses real Groq tool calling when <code>GROQ_API_KEY</code> is configured server-side. <b>Guided Deterministic Investigation</b> runs a predefined local Python sequence with zero API key and never pretends to be an LLM.</p>
            </div>
            <div class="ds-rel-card">
                <h4>Untrusted Data Isolation</h4>
                <p>CSV cell values are treated strictly as untrusted data, never system instructions. Markdown reports and UI cards escape untrusted strings and strip unsafe HTML tags.</p>
            </div>
            <div class="ds-rel-card">
                <h4>Bounded Retries &amp; Failure Honesty</h4>
                <p>Rate limits, timeouts, and invalid tool-call generations are handled with bounded retries (max 2) and one lower-temperature recovery. Partial evidence is preserved and failures are never hidden.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Final CTA Banner
    st.markdown(
        """
        <div class="ds-card" style="text-align:center; padding:1.75rem 1.25rem; margin-top:1.5rem; border-color:rgba(34,211,238,0.35);">
            <div class="ds-kicker" style="margin-bottom:6px;">Ready to inspect your dataset?</div>
            <h3 style="margin:0 0 8px 0 !important;">Launch the DataSleuth AI Investigation Workspace</h3>
            <p style="color:#94A3B8; font-size:0.88rem; max-width:560px; margin:0 auto 1rem auto;">
                Upload your own UTF-8 CSV or load one of five synthetic datasets — including a 2,000-row enterprise ledger.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _, bot_c1, _ = st.columns([2.5, 2.2, 2.5])
    with bot_c1:
        if st.button("Launch Workspace →", key="landing_launch_bottom", type="primary", use_container_width=True):
            on_launch_workspace()
            st.rerun()

    # Footer
    st.markdown(
        f"""
        <div class="ds-footer">
            <div class="ds-footer-left">
                {datasleuth_logo_svg(24)}
                <span><b>DataSleuth AI</b> · Autonomous CSV Data Quality Investigation</span>
            </div>
            <div class="ds-footer-right">
                <a href="{GITHUB_REPO_URL}" target="_blank" rel="noopener noreferrer">GitHub Repository ↗</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
