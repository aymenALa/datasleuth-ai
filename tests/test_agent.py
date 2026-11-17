"""Tests for the bounded Groq investigation agent."""

import json
from types import SimpleNamespace

import pandas as pd
import pytest

from datasleuth.agent import (
    InvestigationAgent,
    execute_tool,
    run_investigation,
    tool_definitions,
)
from datasleuth.groq_client import (
    GroqClient,
    GroqConfigurationError,
    GroqRateLimitError,
)
from datasleuth.models import DatasetContext


def context():
    dataframe = pd.DataFrame({"age": [20, 21, 22, 100], "city": ["Fes", "Fes", "Rabat", "Rabat"]})
    return DatasetContext("dataset-1", "sample.csv", dataframe, 4, 2, ["age", "city"])


def response(content=None, calls=None, usage=None):
    message = SimpleNamespace(role="assistant", content=content, tool_calls=calls or [])
    return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=usage)


def call(name, arguments, call_id):
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(name=name, arguments=json.dumps(arguments)),
    )


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.messages = []

    def complete(self, messages, tools):
        self.messages.append((messages, tools))
        return self.responses.pop(0), {"total_tokens": 3}


def test_registry_exposes_exactly_five_tools():
    names = [item["function"]["name"] for item in tool_definitions()]

    assert names == [
        "profile_dataset",
        "analyze_missing_values",
        "detect_duplicates",
        "inspect_column",
        "detect_outliers",
    ]
    assert all("parameters" in item["function"] for item in tool_definitions())


def test_initial_tool_selection_and_associated_result_call_id():
    fake = FakeClient(
        [
            response(calls=[call("profile_dataset", {}, "call-1")]),
            response("The profile shows four rows and two columns.", usage=None),
        ]
    )
    before = context().dataframe.copy(deep=True)

    result = InvestigationAgent(fake).investigate(context(), "Understand this dataset")

    assert result.status == "complete"
    assert result.steps[0].tool_name == "profile_dataset"
    assert result.steps[0].call_id == "call-1"
    tool_messages = [message for message in fake.messages[1][0] if message.get("role") == "tool"]
    assert tool_messages[-1]["tool_call_id"] == "call-1"
    assert json.loads(tool_messages[-1]["content"])["status"] == "success"
    pd.testing.assert_frame_equal(context().dataframe, before)


def test_multistep_and_multiple_tool_calls_are_executed_in_order():
    fake = FakeClient(
        [
            response(calls=[call("analyze_missing_values", {}, "call-1")]),
            response(calls=[call("inspect_column", {"column": "age"}, "call-2"), call("detect_duplicates", {}, "call-3")]),
            response("No missing values or duplicate rows were found.")
        ]
    )

    result = InvestigationAgent(fake).investigate(context(), "Check completeness and duplicates")

    assert result.status == "complete"
    assert [step.tool_name for step in result.steps] == [
        "analyze_missing_values",
        "inspect_column",
        "detect_duplicates",
    ]
    tool_messages = [message for message in fake.messages[2][0] if message.get("role") == "tool"]
    assert [message["tool_call_id"] for message in tool_messages] == ["call-1", "call-2", "call-3"]


def test_invalid_tool_arguments_and_columns_return_structured_errors():
    dataset = context()

    assert execute_tool(dataset, "not_allowed", {})["status"] == "error"
    assert execute_tool(dataset, "inspect_column", "bad")["status"] == "error"
    assert execute_tool(dataset, "inspect_column", {"column": "missing"})["status"] == "error"
    assert execute_tool(dataset, "detect_outliers", {"column": "age", "method": "zscore"})["status"] == "error"
    assert execute_tool(dataset, "detect_duplicates", {"columns": ["missing"]})["status"] == "error"


def test_invalid_json_arguments_are_sent_back_as_tool_errors():
    malformed = SimpleNamespace(
        id="call-1",
        function=SimpleNamespace(name="inspect_column", arguments="{bad-json"),
    )
    fake = FakeClient([response(calls=[malformed]), response("The arguments were invalid.")])

    result = InvestigationAgent(fake).investigate(context(), "Inspect a column")

    assert result.status == "complete"
    assert result.steps[0].result["status"] == "error"
    assert "JSON object" in result.steps[0].result["error"]


def test_repeated_identical_calls_stop_as_incomplete():
    fake = FakeClient(
        [
            response(calls=[call("profile_dataset", {}, "call-1")]),
            response(calls=[call("profile_dataset", {}, "call-2")]),
        ]
    )

    result = InvestigationAgent(fake).investigate(context(), "Profile repeatedly")

    assert result.status == "incomplete"
    assert "Repeated" in result.error
    assert len(result.steps) == 1


def test_turn_and_tool_limits_return_incomplete_results():
    turn_limited = FakeClient([response(calls=[call("profile_dataset", {}, "call-1")])])
    tool_limited = FakeClient([response(calls=[call("profile_dataset", {}, "call-1"), call("analyze_missing_values", {}, "call-2")])])

    first = InvestigationAgent(turn_limited, max_turns=1).investigate(context(), "Profile")
    second = InvestigationAgent(tool_limited, max_tool_calls=1).investigate(context(), "Profile")

    assert first.status == "incomplete"
    assert second.status == "incomplete"
    assert "limit" in second.error


def test_normal_completion_and_investigation_result_json():
    fake = FakeClient([response("The dataset was investigated.", usage=None)])

    result = InvestigationAgent(fake).investigate(context(), "Summarize")

    assert result.status == "complete"
    assert result.summary == "The dataset was investigated."
    json.dumps(result.to_dict(), allow_nan=False)


def test_missing_api_key_is_a_clear_structured_error(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    result = run_investigation(context(), "Investigate")

    assert result.status == "error"
    assert result.error == "GROQ_API_KEY is not configured"


class RateLimitError(Exception):
    status_code = 429

    def __init__(self):
        self.response = SimpleNamespace(headers={"retry-after": "0"})


def test_rate_limit_retries_are_bounded_and_respect_retry_after():
    class FailingCompletions:
        def __init__(self):
            self.calls = 0

        def create(self, **kwargs):
            self.calls += 1
            raise RateLimitError()

    api = SimpleNamespace(chat=SimpleNamespace(completions=FailingCompletions()))
    sleeps = []
    client = GroqClient(api_key="test-key", client=api, max_retries=2, sleep=sleeps.append)

    with pytest.raises(GroqRateLimitError):
        client.complete([], [])
    assert api.chat.completions.calls == 3
    assert sleeps == [0.0, 0.0]


def test_missing_key_constructor_raises_without_real_api_call(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    with pytest.raises(GroqConfigurationError):
        GroqClient()


def test_tool_failure_does_not_modify_dataframe():
    dataset = context()
    before = dataset.dataframe.copy(deep=True)
    result = execute_tool(dataset, "detect_outliers", {"column": "city"})

    assert result["status"] == "error"
    pd.testing.assert_frame_equal(dataset.dataframe, before)
