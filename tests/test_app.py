"""Focused local UI tests for the Streamlit entry point."""

from pathlib import Path
from io import BytesIO

import pytest
from streamlit.testing.v1 import AppTest

import app
from datasleuth.models import InvestigationResult


APP_PATH = Path(__file__).parents[1] / "app.py"


def test_streamlit_startup_has_upload_prompt():
    at = AppTest.from_file(str(APP_PATH)).run()

    assert at.title[0].value == "DataSleuth AI"
    assert at.file_uploader[0].allowed_type == [".csv"]
    assert any("Upload a UTF-8 CSV" in item.value for item in at.info)


def test_successful_csv_upload_renders_bounded_overview():
    at = AppTest.from_file(str(APP_PATH)).run()
    at.file_uploader[0].set_value(("sample.csv", b"name,score\nAda,10\nGrace,20\n", "text/csv"))
    at.run()

    assert [metric.label for metric in at.metric] == ["Rows", "Columns", "File"]
    assert at.metric[0].value == "2"
    assert at.metric[1].value == "2"
    assert at.metric[2].value == "sample.csv"
    assert any("inferred by Pandas" in item.value for item in at.caption)


def test_successful_csv_upload_renders_deterministic_visualizations_without_agent():
    at = AppTest.from_file(str(APP_PATH)).run()
    at.file_uploader[0].set_value(("quality.csv", b"name,score\nAda,10\nGrace,20\n", "text/csv"))
    at.run()

    assert any("Data Quality Visualizations" in item.value for item in at.subheader)
    assert any("No missing cells" in item.value for item in at.info)


def test_invalid_csv_upload_displays_readable_error():
    at = AppTest.from_file(str(APP_PATH)).run()
    at.file_uploader[0].set_value(("bad.csv", b"name,name\nAda,1\n", "text/csv"))
    at.run()

    assert any("CSV could not be loaded" in item.value for item in at.error)


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


def test_dataset_explorer_navigation_after_csv_upload_has_single_authoritative_uploader_and_no_exception(monkeypatch):
    """Reproduce and verify resolution of StreamlitDuplicateElementId on Dataset Explorer navigation."""
    def unexpected_agent_call(*args, **kwargs):
        pytest.fail("Agent must not be invoked during navigation")

    monkeypatch.setattr(app, "run_investigation", unexpected_agent_call)

    # 1. Start application
    at = AppTest.from_file(str(APP_PATH)).run()
    assert len(at.exception) == 0
    assert len(at.file_uploader) == 1

    # 2. Upload a valid CSV
    at.file_uploader[0].set_value(("sample.csv", b"name,score\nAda,10\nGrace,20\n", "text/csv"))
    at.run()
    assert len(at.exception) == 0
    assert at.session_state["dataset_context"] is not None

    # 3. Navigate to Dataset Explorer
    btn_de = [b for b in at.sidebar.button if "Dataset Explorer" in b.label][0]
    btn_de.click().run()

    # 4. Confirm workspace renders without exceptions
    assert len(at.exception) == 0

    # 5. Confirm exactly one authoritative uploader exists
    assert len(at.file_uploader) == 1
    assert at.file_uploader[0].key == "csv_uploader"

    # 6. Confirm dataset remains available
    context = at.session_state["dataset_context"]
    assert context is not None
    assert context.filename == "sample.csv"

    # 7. Navigate to Investigation and all other views
    for dest in ["Investigation", "Findings", "Recommendations", "Execution Trace", "Reports", "Overview"]:
        btn = [b for b in at.sidebar.button if dest in b.label][0]
        btn.click().run()
        assert len(at.exception) == 0
        assert len(at.file_uploader) == 1
        assert at.session_state["dataset_context"] is not None

    # 8. Confirm no agent invocation occurred during navigation
    assert at.session_state["investigation_result"] is None

    # 9. Replace dataset intentionally
    at.file_uploader[0].set_value(("replaced.csv", b"col_a,col_b\n1,2\n3,4\n", "text/csv"))
    at.run()
    assert len(at.exception) == 0
    assert at.session_state["dataset_context"].filename == "replaced.csv"

    # 10. Verify removal/clearing behavior invalidates stale state
    at.file_uploader[0].set_value(None)
    at.session_state["dataset_context"] = None
    at.session_state["dataset_signature"] = None
    at.session_state["investigation_result"] = None
    at.session_state["report"] = None
    at.run()
    assert len(at.exception) == 0
    assert at.session_state["dataset_context"] is None
    assert at.session_state["investigation_result"] is None
    assert at.session_state["report"] is None


def test_empty_state_navigation_displays_corresponding_workspace_for_all_destinations():
    """Verify that selecting navigation items without a loaded dataset updates the displayed workspace."""
    at = AppTest.from_file(str(APP_PATH)).run()

    # Initial state is Overview with authoritative uploader
    assert at.session_state["active_view"] == "Overview"
    assert len(at.file_uploader) == 1

    # Navigate to Dataset Explorer with no dataset loaded
    btn_de = [b for b in at.sidebar.button if "Dataset Explorer" in b.label][0]
    btn_de.click().run()
    assert len(at.exception) == 0
    assert at.session_state["active_view"] == "Dataset Explorer"
    assert any("Dataset Explorer" in item.value for item in at.markdown)
    assert any("No Dataset Loaded" in item.value for item in at.markdown)
    assert len(at.file_uploader) == 1

    # Navigate to Investigation with no dataset loaded
    btn_inv = [b for b in at.sidebar.button if "Investigation" in b.label][0]
    btn_inv.click().run()
    assert len(at.exception) == 0
    assert at.session_state["active_view"] == "Investigation"
    assert any("Investigation Center" in item.value for item in at.markdown)
    assert any("No Dataset Available to Investigate" in item.value for item in at.markdown)
    assert len(at.file_uploader) == 1

    # Navigate to Findings with no dataset loaded
    btn_find = [b for b in at.sidebar.button if "Findings" in b.label][0]
    btn_find.click().run()
    assert len(at.exception) == 0
    assert at.session_state["active_view"] == "Findings"
    assert any("Findings Explorer" in item.value for item in at.markdown)
    assert any("No Investigation Findings Available" in item.value for item in at.markdown)

    # Navigate to Recommendations with no dataset loaded
    btn_rec = [b for b in at.sidebar.button if "Recommendations" in b.label][0]
    btn_rec.click().run()
    assert len(at.exception) == 0
    assert at.session_state["active_view"] == "Recommendations"
    assert any("Recommendation Center" in item.value for item in at.markdown)
    assert any("No Recommendations Available" in item.value for item in at.markdown)

    # Navigate to Execution Trace with no dataset loaded
    btn_trace = [b for b in at.sidebar.button if "Execution Trace" in b.label][0]
    btn_trace.click().run()
    assert len(at.exception) == 0
    assert at.session_state["active_view"] == "Execution Trace"
    assert any("Execution Trace" in item.value for item in at.markdown)
    assert any("No Execution Steps Recorded" in item.value for item in at.markdown)

    # Navigate to Reports with no dataset loaded
    btn_rep = [b for b in at.sidebar.button if "Reports" in b.label][0]
    btn_rep.click().run()
    assert len(at.exception) == 0
    assert at.session_state["active_view"] == "Reports"
    assert any("Report Center" in item.value for item in at.markdown)
    assert any("No Investigation Report Generated" in item.value for item in at.markdown)

    # Return to Overview
    btn_ov = [b for b in at.sidebar.button if "Overview" in b.label][0]
    btn_ov.click().run()
    assert len(at.exception) == 0
    assert at.session_state["active_view"] == "Overview"
    assert any("Load a dataset" in item.value for item in at.subheader)
