"""Focused local UI and state-transition tests for the Streamlit entry point."""

from io import BytesIO
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import app
from datasleuth.models import InvestigationResult

APP_PATH = Path(__file__).parents[1] / "app.py"


def test_streamlit_startup_renders_standalone_landing_without_uploader():
    at = AppTest.from_file(str(APP_PATH)).run()

    assert len(at.exception) == 0
    assert at.session_state["app_experience"] == "landing"
    assert at.session_state["dataset_context"] is None
    assert len(at.file_uploader) == 0
    assert any("Launch Workspace" in b.label for b in at.button)


def test_launch_workspace_opens_onboarding_with_upload_prompt():
    at = AppTest.from_file(str(APP_PATH)).run()
    launch_btn = [b for b in at.button if "Launch Workspace" in b.label][0]
    launch_btn.click().run()

    assert len(at.exception) == 0
    assert at.session_state["app_experience"] == "onboarding"
    assert at.session_state["dataset_context"] is None
    assert at.file_uploader[0].allowed_type == [".csv"]
    assert any("Upload a UTF-8 CSV" in item.value for item in at.info)


def test_successful_csv_upload_navigates_to_overview_with_metrics_and_charts():
    at = AppTest.from_file(str(APP_PATH)).run()
    [b for b in at.button if "Launch Workspace" in b.label][0].click().run()

    at.file_uploader[0].set_value(("sample.csv", b"name,score\nAda,10\nGrace,20\n", "text/csv"))
    at.run()

    assert len(at.exception) == 0
    assert at.session_state["app_experience"] == "workspace"
    assert at.session_state["active_view"] == "Overview"
    assert at.session_state["dataset_source_type"] == "uploaded"
    assert [metric.label for metric in at.metric] == ["Rows", "Columns", "File"]
    assert at.metric[0].value == "2"
    assert at.metric[1].value == "2"
    assert at.metric[2].value == "sample.csv"
    assert any("Data Quality Visualizations" in item.value for item in at.subheader)
    assert any("No missing cells" in item.value for item in at.info)


def test_invalid_csv_upload_displays_readable_error_on_onboarding():
    at = AppTest.from_file(str(APP_PATH)).run()
    [b for b in at.button if "Launch Workspace" in b.label][0].click().run()

    at.file_uploader[0].set_value(("bad.csv", b"name,name\nAda,1\n", "text/csv"))
    at.run()

    assert at.session_state["app_experience"] == "onboarding"
    assert at.session_state["dataset_context"] is None
    assert any("CSV could not be loaded" in item.value for item in at.error)


def test_oversized_csv_upload_displays_10mb_limit_error():
    at = AppTest.from_file(str(APP_PATH)).run()
    [b for b in at.button if "Launch Workspace" in b.label][0].click().run()

    oversized = b"col\n" + (b"1\n" * (5 * 1024 * 1024 + 500_000))
    at.file_uploader[0].set_value(("huge.csv", oversized, "text/csv"))
    at.run()

    assert at.session_state["app_experience"] == "onboarding"
    assert at.session_state["dataset_context"] is None
    assert any("maximum allowed" in item.value.lower() for item in at.error)


def test_uploading_a_new_dataset_clears_stale_investigation_state(monkeypatch):
    class Uploaded:
        def __init__(self, content):
            self.content = content

        def getvalue(self):
            return self.content

    monkeypatch.setattr(app.st, "session_state", {})
    app._initialize_state()
    app._load_uploaded_dataset(Uploaded(b"a\n1\n"))
    app.st.session_state["investigation_result"] = "old-result"
    app.st.session_state["report"] = "old-report"

    app._load_uploaded_dataset(Uploaded(b"a\n2\n"))

    assert app.st.session_state["dataset_context"].dataframe.iloc[0, 0] == 2
    assert app.st.session_state["investigation_result"] is None
    assert app.st.session_state["report"] is None


def test_upload_processing_does_not_invoke_agent(monkeypatch):
    class Uploaded:
        def getvalue(self):
            return b"a\n1\n"

    def unexpected_call(*args, **kwargs):
        pytest.fail("Agent must not run during upload processing")

    monkeypatch.setattr(app.st, "session_state", {})
    monkeypatch.setattr(app, "run_investigation", unexpected_call)
    app._initialize_state()
    app._load_uploaded_dataset(Uploaded())

    assert app.st.session_state["dataset_context"] is not None


def test_dataset_switching_isolates_results_across_a_a_b_a_and_restart(monkeypatch):
    class Uploaded:
        def __init__(self, name, content):
            self.name = name
            self.content = content

        def getvalue(self):
            return self.content

    monkeypatch.setattr(app.st, "session_state", {})
    app._initialize_state()
    calls = []

    def fake_runner(received_context, goal):
        calls.append((received_context.dataset_id, goal))
        return InvestigationResult(received_context.dataset_id, goal, "complete", goal)

    dataset_a = Uploaded("a.csv", b"value\n1\n")
    dataset_b = Uploaded("b.csv", b"value\n2\n")

    app._load_uploaded_dataset(dataset_a)
    context_a = app.st.session_state["dataset_context"]
    app._execute_investigation(context_a, "A first", runner=fake_runner)
    first_result = app.st.session_state["investigation_result"]
    app._load_uploaded_dataset(dataset_a)
    assert app.st.session_state["investigation_result"] is first_result
    app._execute_investigation(context_a, "A repeated", runner=fake_runner)
    assert app.st.session_state["investigation_result"].goal == "A repeated"

    app._load_uploaded_dataset(dataset_b)
    context_b = app.st.session_state["dataset_context"]
    assert context_b.dataset_id != context_a.dataset_id
    assert app.st.session_state["investigation_result"] is None
    assert app.st.session_state["report"] is None
    app._execute_investigation(context_b, "B first", runner=fake_runner)

    app._load_uploaded_dataset(dataset_a)
    assert app.st.session_state["dataset_context"].dataset_id != context_b.dataset_id
    assert app.st.session_state["investigation_result"] is None
    assert app.st.session_state["report"] is None

    monkeypatch.setattr(app.st, "session_state", {})
    app._initialize_state()
    app._load_uploaded_dataset(dataset_b)
    assert app.st.session_state["investigation_result"] is None
    assert app.st.session_state["report"] is None
    assert len(calls) == 3


def test_mocked_investigation_persists_result_and_report_without_api_call(monkeypatch):
    monkeypatch.setattr(app.st, "session_state", {})
    app._initialize_state()
    context = app.load_csv(BytesIO(b"value\n1\n"))
    calls = []

    def fake_runner(received_context, goal):
        calls.append((received_context.dataset_id, goal))
        return InvestigationResult(received_context.dataset_id, goal, "complete", "Mocked summary")

    result = app._execute_investigation(context, "Inspect the data", runner=fake_runner)

    assert calls == [(context.dataset_id, "Inspect the data")]
    assert app.st.session_state["investigation_result"] is result
    assert app.st.session_state["report"]["completion_status"] == "validated"
    assert app.st.session_state["report"]["model_interpretation"] == "Mocked summary"


def test_workspace_navigation_and_home_resume_flow(monkeypatch):
    def unexpected_agent_call(*args, **kwargs):
        pytest.fail("Agent must not be invoked during navigation")

    monkeypatch.setattr(app, "run_investigation", unexpected_agent_call)

    at = AppTest.from_file(str(APP_PATH)).run()
    [b for b in at.button if "Launch Workspace" in b.label][0].click().run()
    at.file_uploader[0].set_value(("sample.csv", b"name,score\nAda,10\nGrace,20\n", "text/csv"))
    at.run()

    assert at.session_state["app_experience"] == "workspace"
    for dest in ["Dataset Explorer", "Investigation", "Findings", "Recommendations", "Execution Trace", "Reports", "Overview"]:
        btn = [b for b in at.sidebar.button if dest in b.label][0]
        btn.click().run()
        assert len(at.exception) == 0
        assert at.session_state["dataset_context"] is not None

    # Return Home with active dataset -> Resume Investigation available
    back_btn = [b for b in at.sidebar.button if "Back to Home" in b.label][0]
    back_btn.click().run()
    assert at.session_state["app_experience"] == "landing"
    assert at.session_state["dataset_context"] is not None
    resume_btn = [b for b in at.button if "Resume Investigation" in b.label][0]
    resume_btn.click().run()
    assert at.session_state["app_experience"] == "workspace"
    assert at.session_state["dataset_context"].filename == "sample.csv"


def test_streamlit_config_aligns_10mb_upload_limit():
    config_text = (Path(__file__).parents[1] / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    assert "maxUploadSize = 10" in config_text
