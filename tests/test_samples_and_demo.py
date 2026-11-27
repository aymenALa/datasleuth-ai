"""Tests for synthetic sample datasets, guided deterministic mode, and quota guards."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import app
from datasleuth.config import MAX_GLOBAL_LIVE_RUNS, MAX_SESSION_LIVE_RUNS
from datasleuth.demo_runner import run_guided_investigation
from datasleuth.groq_client import is_groq_configured, is_live_ai_enabled
from datasleuth.reports import build_report, report_to_json, report_to_markdown
from datasleuth.sample_datasets import (
    get_sample_dataset,
    list_sample_datasets,
    load_sample_dataset,
    read_sample_csv_bytes,
)

APP_PATH = Path(__file__).parents[1] / "app.py"


def test_all_five_sample_datasets_load_and_match_declared_dimensions():
    samples = list_sample_datasets()
    assert len(samples) == 5
    for info in samples:
        raw = read_sample_csv_bytes(info.key)
        assert len(raw) > 0
        context = load_sample_dataset(info.key)
        assert context.filename == info.filename
        assert context.row_count == info.row_count
        assert context.column_count == info.column_count
        assert len(info.scenarios) >= 3
        assert get_sample_dataset(info.key).title == info.title

    ledger = load_sample_dataset("enterprise_invoice_ledger")
    assert ledger.row_count == 2000
    assert ledger.column_count == 10


def test_guided_deterministic_investigation_produces_verified_report_without_llm():
    for key in ("ecommerce_orders", "enterprise_invoice_ledger"):
        context = load_sample_dataset(key)
        original = context.dataframe.copy(deep=True)

        result = run_guided_investigation(context, "Check data quality")

        assert result.status == "complete"
        assert result.summary is None
        assert result.model_response is None
        assert result.usage == {}
        assert len(result.steps) >= 3
        assert context.dataframe.equals(original)

        report = build_report(context, result)
        assert report["completion_status"] == "validated"
        assert report["outcome"] == "issues_found"
        assert len(report["verified_findings"]) > 0
        assert len(report["cleaning_recommendations"]) > 0
        assert report["model_interpretation"] is None

        assert report_to_json(report)
        md = report_to_markdown(report)
        assert "DataSleuth AI Investigation Report" in md


def test_is_groq_configured_reflects_env(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert is_groq_configured() is False

    monkeypatch.setenv("GROQ_API_KEY", "   ")
    assert is_groq_configured() is False

    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_placeholder")
    assert is_groq_configured() is True
    assert is_live_ai_enabled() is True

    monkeypatch.setenv("DATASLEUTH_PUBLIC_DEMO_MODE", "true")
    assert is_live_ai_enabled() is False


def test_onboarding_sample_selection_guided_investigation_and_dataset_switch(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    def unexpected_agent_call(*args, **kwargs):
        pytest.fail("Live Groq agent must not be called in Guided Deterministic Mode")

    monkeypatch.setattr(app, "run_investigation", unexpected_agent_call)

    at = AppTest.from_file(str(APP_PATH)).run()
    assert at.session_state["app_experience"] == "landing"

    # Launch Workspace -> Onboarding
    [b for b in at.button if "Launch Workspace" in b.label][0].click().run()
    assert at.session_state["app_experience"] == "onboarding"

    # Load first sample dataset (E-Commerce Orders)
    sample_btn = [b for b in at.button if b.key == "onb_sample_ecommerce_orders"][0]
    sample_btn.click().run()
    assert len(at.exception) == 0
    assert at.session_state["app_experience"] == "workspace"
    assert at.session_state["active_view"] == "Overview"
    assert at.session_state["dataset_source_type"] == "sample"
    assert at.session_state["dataset_context"].filename == "ecommerce_orders.csv"

    # Navigate to Investigation and run Guided Deterministic Mode
    [b for b in at.sidebar.button if "Investigation" in b.label][0].click().run()
    assert len(at.exception) == 0

    [b for b in at.button if "Run investigation" in b.label][0].click().run()
    assert len(at.exception) == 0
    assert at.session_state["investigation_result"].status == "complete"
    assert at.session_state["report"]["completion_status"] == "validated"

    # Change Dataset -> load 2,000-row Enterprise Invoice Ledger -> stale results cleared
    [b for b in at.sidebar.button if "Change Dataset" in b.label][0].click().run()
    assert at.session_state["app_experience"] == "onboarding"
    [b for b in at.button if b.key == "onb_sample_enterprise_invoice_ledger"][0].click().run()
    assert at.session_state["app_experience"] == "workspace"
    assert at.session_state["dataset_context"].filename == "enterprise_invoice_ledger.csv"
    assert at.session_state["dataset_context"].row_count == 2000
    assert at.session_state["investigation_result"] is None
    assert at.session_state["report"] is None


def test_session_live_run_cap_blocks_excess_calls(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_placeholder")
    monkeypatch.delenv("DATASLEUTH_PUBLIC_DEMO_MODE", raising=False)
    monkeypatch.setattr(app.st, "session_state", {})
    app._initialize_state()
    app.st.session_state["live_runs_used"] = MAX_SESSION_LIVE_RUNS
    context = load_sample_dataset("customer_records")

    result = app._execute_investigation(context, "Audit", mode="live_ai")
    assert result.status == "error"
    assert "limit" in (result.error or "").lower()


def test_global_live_run_cap_and_public_demo_lock(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_placeholder")
    monkeypatch.setenv("DATASLEUTH_PUBLIC_DEMO_MODE", "true")
    monkeypatch.setattr(app.st, "session_state", {})
    app._initialize_state()
    context = load_sample_dataset("customer_records")

    locked = app._execute_investigation(context, "Audit", mode="live_ai")
    assert locked.status == "error"
    assert "disabled" in (locked.error or "").lower()

    monkeypatch.delenv("DATASLEUTH_PUBLIC_DEMO_MODE", raising=False)
    monkeypatch.setattr(app, "_GLOBAL_LIVE_RUNS", MAX_GLOBAL_LIVE_RUNS)
    capped = app._execute_investigation(context, "Audit", mode="live_ai")
    assert capped.status == "error"
    assert "global" in (capped.error or "").lower()
