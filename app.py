"""Streamlit interface for the DataSleuth AI investigation workflow."""

from __future__ import annotations

import hashlib
from io import BytesIO
from typing import Any

import streamlit as st

from datasleuth.agent import run_investigation
from datasleuth.data_loader import CSVLoadError, load_csv
from datasleuth.models import DatasetContext, InvestigationResult
from datasleuth.reports import build_report, report_to_json, report_to_markdown


DEFAULT_GOAL = "Identify the most important data-quality risks and explain the evidence."
_PREVIEW_ROWS = 10


def _initialize_state() -> None:
    defaults = {
        "dataset_context": None,
        "dataset_signature": None,
        "upload_error": None,
        "investigation_goal": DEFAULT_GOAL,
        "investigation_result": None,
        "report": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _signature(uploaded_file: Any) -> str:
    return hashlib.sha256(uploaded_file.getvalue()).hexdigest()


def _load_uploaded_dataset(uploaded_file: Any) -> None:
    signature = _signature(uploaded_file)
    if signature == st.session_state["dataset_signature"]:
        return
    try:
        source = BytesIO(uploaded_file.getvalue())
        source.name = getattr(uploaded_file, "name", "uploaded.csv")
        context = load_csv(source)
    except CSVLoadError as exc:
        st.session_state["dataset_context"] = None
        st.session_state["dataset_signature"] = signature
        st.session_state["upload_error"] = str(exc)
        st.session_state["investigation_result"] = None
        st.session_state["report"] = None
        return
    st.session_state["dataset_context"] = context
    st.session_state["dataset_signature"] = signature
    st.session_state["upload_error"] = None
    st.session_state["investigation_result"] = None
    st.session_state["report"] = None


def _execute_investigation(
    context: DatasetContext,
    goal: str,
    runner: Any | None = None,
) -> InvestigationResult:
    """Run one explicit investigation and persist its report in session state."""

    result = (runner or run_investigation)(context, goal)
    st.session_state["investigation_result"] = result
    st.session_state["report"] = build_report(context, result)
    return result


def _render_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container { max-width: 1180px; padding-top: 2.2rem; }
        .ds-kicker { color: #53708a; font-size: 0.78rem; font-weight: 700;
                     letter-spacing: .12em; text-transform: uppercase; }
        .ds-subtitle { color: #5f6f7d; font-size: 1.05rem; margin-top: -.6rem; }
        [data-testid="stMetricValue"] { color: #1e4f78; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_header() -> None:
    st.markdown('<div class="ds-kicker">Autonomous data quality investigation</div>', unsafe_allow_html=True)
    st.title("DataSleuth AI")
    st.markdown(
        '<div class="ds-subtitle">Evidence-first investigation for CSV datasets — no automatic cleaning.</div>',
        unsafe_allow_html=True,
    )


def _render_upload() -> None:
    st.subheader("1. Load a dataset")
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"], label_visibility="collapsed")
    if uploaded_file is not None:
        _load_uploaded_dataset(uploaded_file)
    if st.session_state["upload_error"]:
        st.error(f"CSV could not be loaded: {st.session_state['upload_error']}")
    elif st.session_state["dataset_context"] is None:
        st.info("Upload a UTF-8 CSV to begin. The existing ingestion limits are enforced.")


def _render_overview(context: DatasetContext) -> None:
    st.subheader("2. Dataset overview")
    metric_columns = st.columns(3)
    metric_columns[0].metric("Rows", f"{len(context.dataframe):,}")
    metric_columns[1].metric("Columns", f"{len(context.dataframe.columns):,}")
    metric_columns[2].metric("File", context.filename)
    st.caption("Column types below are inferred by Pandas during CSV ingestion.")
    type_table = [{"column": str(column), "inferred_type": str(context.dataframe[column].dtype)} for column in context.dataframe.columns]
    st.dataframe(type_table, width="stretch", hide_index=True)
    st.caption(f"Preview — first {min(_PREVIEW_ROWS, len(context.dataframe))} rows")
    st.dataframe(context.dataframe.head(_PREVIEW_ROWS), width="stretch", hide_index=True)
    for warning in context.warnings:
        st.warning(warning)


def _render_controls(context: DatasetContext) -> None:
    st.subheader("3. Investigation")
    goal = st.text_area(
        "Investigation goal",
        key="investigation_goal",
        help="The goal guides tool selection; the full CSV is never sent to Groq.",
    )
    if st.button("Run investigation", type="primary", width="stretch"):
        if not goal.strip():
            st.warning("Enter an investigation goal before running.")
            return
        with st.spinner("Running bounded investigation…"):
            _execute_investigation(context, goal.strip())


def _status_message(result: InvestigationResult) -> None:
    if result.status == "complete":
        st.success("Investigation completed.")
    elif result.status == "incomplete":
        st.warning("Investigation incomplete. Findings cover executed checks only.")
    else:
        st.error(result.error or "Investigation failed.")


def _render_trace(result: InvestigationResult) -> None:
    st.subheader("Investigation trace")
    if not result.steps:
        st.caption("No tools were executed.")
        return
    for index, step in enumerate(result.steps, start=1):
        tool_result = step.result
        status = tool_result.get("status", "unknown")
        with st.expander(f"Step {index} · {step.tool_name} · {status}", expanded=index == len(result.steps)):
            st.write("Parameters")
            st.json(step.arguments)
            if status == "success":
                st.write("Observed metrics")
                st.json(tool_result.get("metrics", {}))
                if tool_result.get("evidence"):
                    st.write("Bounded evidence")
                    st.json(tool_result["evidence"])
            else:
                st.error(tool_result.get("error", "Tool failed"))
            for warning in tool_result.get("warnings", []):
                st.warning(warning)


def _render_findings(report: dict[str, Any]) -> None:
    st.subheader("Verified findings")
    findings = report.get("verified_findings", [])
    if not findings:
        st.info("No verified issue findings were produced from the executed checks.")
    for finding in findings:
        with st.container(border=True):
            st.markdown(f"**{finding['title']}**")
            st.caption(
                f"{finding['classification']} · confidence: {finding.get('confidence', 'context required')} · "
                f"source: {finding['tool_name']} / {finding['metric_path']}"
            )
            st.write(f"Affected columns: {', '.join(finding.get('columns', [])) or 'dataset-wide'}")
            st.write(f"Observed value: {finding.get('value')}")
            if finding.get("evidence"):
                st.json(finding["evidence"])

    if report.get("model_interpretation"):
        st.subheader("Model interpretation")
        st.info(report["model_interpretation"])
        st.caption("This is an unverified interpretation; numerical facts above come from executed tools.")


def _render_recommendations(report: dict[str, Any]) -> None:
    st.subheader("Cleaning recommendations")
    recommendations = report.get("cleaning_recommendations", [])
    if not recommendations:
        st.info("No recommendations were generated.")
        return
    for recommendation in recommendations:
        with st.container(border=True):
            st.markdown(f"**{recommendation['issue']}**")
            st.caption(
                f"Evidence: {recommendation['evidence_classification']} · "
                f"confidence: {recommendation['confidence']}"
            )
            st.write("Potential analytical impact", recommendation["potential_analytical_impact"])
            st.write("Suggested follow-up", recommendation["suggested_follow_up"])
            st.write("Conditional treatment options", recommendation["conditional_treatment_options"])
            st.write("Risks and assumptions", recommendation["risks_and_assumptions"])
            st.write("Post-treatment validation", recommendation["post_treatment_validation"])


def _render_report_exports(report: dict[str, Any]) -> None:
    st.subheader("Export report")
    json_report = report_to_json(report)
    markdown_report = report_to_markdown(report)
    export_columns = st.columns(2)
    export_columns[0].download_button(
        "Download JSON",
        data=json_report,
        file_name="datasleuth-report.json",
        mime="application/json",
        width="stretch",
    )
    export_columns[1].download_button(
        "Download Markdown",
        data=markdown_report,
        file_name="datasleuth-report.md",
        mime="text/markdown",
        width="stretch",
    )


def main() -> None:
    st.set_page_config(page_title="DataSleuth AI", page_icon="🔎", layout="wide")
    _initialize_state()
    _render_styles()
    _render_header()
    _render_upload()
    context = st.session_state["dataset_context"]
    if context is None:
        return
    _render_overview(context)
    _render_controls(context)
    result = st.session_state["investigation_result"]
    report = st.session_state["report"]
    if result is None or report is None:
        return
    st.divider()
    _status_message(result)
    _render_trace(result)
    _render_findings(report)
    _render_recommendations(report)
    if report.get("warnings") or report.get("validation_errors"):
        st.subheader("Warnings and limitations")
        for message in report.get("warnings", []) + report.get("validation_errors", []) + report.get("limitations", []):
            st.warning(message)
    _render_report_exports(report)


if __name__ == "__main__":
    main()
