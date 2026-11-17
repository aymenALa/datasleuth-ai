"""Structured JSON and readable Markdown reports for investigations."""

from __future__ import annotations

import json
import html
from typing import Any

from .models import DatasetContext, InvestigationResult
from .validator import validate_investigation


def cleaning_recommendations(validation: dict[str, Any]) -> list[dict[str, Any]]:
    """Create context-aware, conservative recommendations from validated findings."""

    recommendations = []
    for finding in validation.get("findings", []):
        classification = finding.get("classification")
        columns = finding.get("columns", [])
        evidence = finding.get("evidence", [])
        if finding["metric_path"].startswith("missing_counts"):
            details = evidence[0].get("examples", [{}])[0] if evidence else {}
            percentage = details.get("missing_percentage")
            impact = "Missingness may reduce usable sample size or bias summaries if it is systematic; the effect depends on its mechanism."
            follow_up = "Compare missingness across relevant groups or time periods, if such fields exist, and investigate the source collection process."
            options = "If the mechanism and assumptions are documented, consider an appropriate imputation strategy; otherwise preserve missingness or exclude rows only with an explicit rationale."
            action = "Investigate the cause and define a documented treatment policy before changing data."
            risk = "Do not default to mean/median imputation; it can distort variance, relationships, and subgroup comparisons."
            validation_strategy = "Re-run missingness metrics, reconcile row counts, and compare key distributions before and after any approved treatment."
            if percentage is not None:
                impact = f"{percentage:.2f}% of rows in the affected column are missing; this may reduce usable sample size or bias summaries if missingness is systematic."
        elif finding["metric_path"] == "duplicate_row_count":
            details = evidence[0].get("examples", [{}])[0] if evidence else {}
            impact = f"The measured redundant-row rate is {details.get('duplicate_percentage', 'unknown')}%; duplicates may inflate counts, frequencies, or aggregates."
            follow_up = "Inspect the bounded matching examples and confirm whether repeated rows are duplicate records or legitimate repeated events."
            options = "If a stable business key and duplicate policy are confirmed, consider a documented deduplication step; otherwise retain the records."
            action = "Inspect matching records and define a deduplication key before considering removal."
            risk = "Removing records can discard legitimate repeated events, especially when full-row or key-based equality is not a business rule."
            validation_strategy = "Re-run the same duplicate check, reconcile the expected row reduction, and verify key-level uniqueness after any approved treatment."
        elif finding["metric_path"] == "mixed_types_detected":
            details = evidence[0].get("examples", [{}])[0] if evidence else {}
            failures = details.get("numeric_conversion_failure_count")
            impact = "Mixed observed Python types can make comparisons, grouping, and numeric summaries inconsistent."
            if failures is not None:
                impact += f" A temporary numeric probe failed for {failures} non-null value(s)."
            follow_up = "Inspect incompatible values and determine whether they represent formatting, missingness, or distinct valid categories."
            options = "Convert only after defining an explicit target type and policy for incompatible values; alternatively retain the original column and create a documented derived field."
            action = "Review incompatible entries and define an explicit conversion policy."
            risk = "Conversion may lose information or turn valid values into missing values; no domain rule was applied."
            validation_strategy = "Re-run type inspection, conversion-failure counts, missingness, and representative value checks after any approved conversion."
        elif classification == "statistical_candidate":
            details = evidence[0].get("examples", [{}])[0] if evidence else {}
            impact = f"{details.get('outlier_candidate_percentage', 'Some')}% of eligible numeric observations were flagged; these values may affect means, variance, and model sensitivity."
            follow_up = "Inspect the bounded row/value examples and verify the observations against domain context, source records, and measurement units."
            options = "If domain review supports it, consider a documented robust analysis, cap, transformation, or exclusion policy; never delete solely because of the IQR result."
            action = "Investigate the flagged observations and confirm domain context before modifying them."
            risk = "A statistical outlier is not automatically a data-quality error; the IQR rule has no domain knowledge."
            validation_strategy = "Re-run the IQR check and compare summary statistics, affected-row counts, and model results after any approved treatment."
        else:
            continue
        recommendations.append({
            "issue": finding["title"],
            "columns": columns,
            "supporting_evidence": evidence,
            "evidence_classification": classification,
            "confidence": finding.get("confidence", "context_required"),
            "potential_analytical_impact": impact,
            "suggested_follow_up": follow_up,
            "conditional_treatment_options": options,
            "suggested_action": action,
            "risks_and_assumptions": risk,
            "risks_or_conditions": risk,
            "post_treatment_validation": validation_strategy,
        })
    if not recommendations and validation.get("status") in {"incomplete", "failed"}:
        recommendations.append({
            "issue": "Insufficient investigation evidence",
            "columns": [],
            "supporting_evidence": [],
            "evidence_classification": "insufficient_evidence",
            "confidence": "low",
            "potential_analytical_impact": "No safe treatment recommendation can be supported from the available observations.",
            "suggested_follow_up": "Complete the investigation and execute the relevant deterministic tools before deciding on treatment.",
            "conditional_treatment_options": "None until sufficient evidence is available.",
            "suggested_action": "Do not modify the dataset based on this incomplete or failed investigation.",
            "risks_and_assumptions": "Any treatment would rely on unsupported assumptions.",
            "risks_or_conditions": "Any treatment would rely on unsupported assumptions.",
            "post_treatment_validation": "First obtain a completed investigation with validated tool evidence.",
        })
    return recommendations


def build_report(context: DatasetContext, investigation: InvestigationResult) -> dict[str, Any]:
    """Build a bounded report from validated observations only."""

    validation = validate_investigation(investigation)
    if validation["status"] == "failed":
        outcome = "investigation_failed"
    elif validation["status"] == "incomplete":
        outcome = "investigation_incomplete"
    elif validation["findings"]:
        outcome = "issues_found"
    else:
        outcome = "no_issue_found_in_executed_checks"
    return {
        "dataset": {
            "dataset_id": context.dataset_id,
            "filename": context.filename,
            "row_count": int(len(context.dataframe)),
            "column_count": int(len(context.dataframe.columns)),
            "column_names": [str(column) for column in context.dataframe.columns],
        },
        "investigation_goal": investigation.goal,
        "completion_status": validation["status"],
        "outcome": outcome,
        "verified_findings": validation["findings"],
        "cleaning_recommendations": cleaning_recommendations(validation),
        "investigation_trace": validation["trace"],
        "warnings": validation["warnings"],
        "validation_errors": validation["errors"],
        "limitations": [
            "Findings cover executed checks only.",
            "Recommendations are advisory and do not modify the source CSV.",
            "Statistical outlier candidates are not confirmed data-quality errors.",
        ],
        "token_usage": validation["usage"],
        "model_interpretation": investigation.model_response,
        "error": investigation.error,
    }


def report_to_json(report: dict[str, Any]) -> str:
    """Serialize a report strictly, rejecting non-finite numeric values."""

    return json.dumps(report, ensure_ascii=True, allow_nan=False, sort_keys=True)


def report_to_markdown(report: dict[str, Any]) -> str:
    """Render a bounded report with untrusted text escaped for Markdown."""

    lines = [
        "# DataSleuth AI Investigation Report",
        "",
        f"- Dataset: {_escape(report['dataset']['filename'])}",
        f"- Dataset ID: `{_escape(report['dataset']['dataset_id'])}`",
        f"- Status: **{_escape(report['completion_status'])}**",
        f"- Goal: {_escape(report['investigation_goal'])}",
        f"- Outcome: **{_escape(report['outcome'])}**",
        "",
        "## Verified findings",
    ]
    findings = report.get("verified_findings", [])
    if not findings:
        lines.append("No verified issue findings were produced from the executed checks.")
    for finding in findings:
        lines.append(f"- **{_escape(finding['title'])}** ({_escape(finding['classification'])}); evidence: `{_escape(finding['metric_path'])}` = `{_escape(str(finding['value']))}`")
    lines.extend(["", "## Cleaning recommendations"])
    recommendations = report.get("cleaning_recommendations", [])
    if not recommendations:
        lines.append("No recommendations were generated.")
    for recommendation in recommendations:
        lines.append(f"- **Issue:** {_escape(recommendation['issue'])}")
        lines.append(f"  - **Evidence classification:** {_escape(recommendation['evidence_classification'])}; confidence: {_escape(recommendation['confidence'])}")
        lines.append(f"  - **Analytical impact:** {_escape(recommendation['potential_analytical_impact'])}")
        lines.append(f"  - **Follow-up:** {_escape(recommendation['suggested_follow_up'])}")
        lines.append(f"  - **Action:** {_escape(recommendation['suggested_action'])}")
        lines.append(f"  - **Conditional options:** {_escape(recommendation['conditional_treatment_options'])}")
        lines.append(f"  - **Risk/assumptions:** {_escape(recommendation['risks_and_assumptions'])}")
        lines.append(f"  - **Post-treatment validation:** {_escape(recommendation['post_treatment_validation'])}")
    lines.extend(["", "## Warnings and limitations"])
    for warning in report.get("warnings", []) + report.get("validation_errors", []) + report.get("limitations", []):
        lines.append(f"- {_escape(warning)}")
    return "\n".join(lines) + "\n"


def _escape(value: str) -> str:
    escaped = html.escape(value, quote=False)
    return escaped.replace("`", "\\`").replace("[", "\\[").replace("]", "\\]").replace("\r", " ").replace("\n", " ")
