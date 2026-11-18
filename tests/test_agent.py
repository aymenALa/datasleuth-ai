"""Tests for the bounded Groq investigation agent."""

import json
from types import SimpleNamespace

import httpx
import pandas as pd
import pytest
from groq import APIConnectionError, APITimeoutError, BadRequestError

from datasleuth.agent import (
    InvestigationAgent,
    execute_tool,
    run_investigation,
    tool_definitions,
)
from datasleuth.groq_client import (
    GroqClient,
    GroqConfigurationError,
    GroqInvalidRequestError,
    GroqNetworkError,
    GroqRateLimitError,
    GroqTimeoutError,
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
                response(calls=[call("inspect_column", {"column": "age"}, "call-1")]),
            response("The profile shows four rows and two columns.", usage=None),
        ]
    )
    before = context().dataframe.copy(deep=True)

    result = InvestigationAgent(fake).investigate(context(), "Understand this dataset")

    assert result.status == "complete"
    model_steps = [step for step in result.steps if not step.call_id.startswith("baseline-")]
    assert model_steps[0].tool_name == "inspect_column"
    assert model_steps[0].call_id == "call-1"
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
    assert [step.tool_name for step in result.steps if not step.call_id.startswith("baseline-")] == [
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


def test_duplicate_tool_accepts_omitted_and_explicit_null_columns():
    dataset = context()

    omitted = execute_tool(dataset, "detect_duplicates", {})
    explicit_null = execute_tool(dataset, "detect_duplicates", {"columns": None})
    subset = execute_tool(dataset, "detect_duplicates", {"columns": ["city"]})

    assert omitted["status"] == explicit_null["status"] == subset["status"] == "success"
    assert omitted["metrics"] == explicit_null["metrics"]
    assert subset["parameters"]["columns"] == ["city"]


def test_invalid_json_arguments_are_sent_back_as_tool_errors():
    malformed = SimpleNamespace(
        id="call-1",
        function=SimpleNamespace(name="inspect_column", arguments="{bad-json"),
    )
    fake = FakeClient([response(calls=[malformed]), response("The arguments were invalid.")])

    result = InvestigationAgent(fake).investigate(context(), "Inspect a column")

    assert result.status == "complete"
    model_steps = [step for step in result.steps if not step.call_id.startswith("baseline-")]
    assert model_steps[0].result["status"] == "error"
    assert "JSON object" in model_steps[0].result["error"]


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
    model_steps = [step for step in result.steps if not step.call_id.startswith("baseline-")]
    assert len(model_steps) == 1
    assert model_steps[0].result["status"] == "skipped"


def test_turn_and_tool_limits_return_incomplete_results():
    turn_limited = FakeClient([response(calls=[call("profile_dataset", {}, "call-1")])])
    tool_limited = FakeClient([response(calls=[call("inspect_column", {"column": "age"}, "call-1"), call("detect_outliers", {"column": "age"}, "call-2")])])

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


def test_invalid_request_is_not_retried_and_preserves_safe_diagnostics():
    response = httpx.Response(
        400,
        request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
        headers={"x-ratelimit-remaining-requests": "7"},
    )

    class FailingCompletions:
        def create(self, **kwargs):
            raise BadRequestError("invalid request", response=response, body={"error": "invalid"})

    api = SimpleNamespace(chat=SimpleNamespace(completions=FailingCompletions()))
    client = GroqClient(api_key="test-key", client=api, max_retries=2, sleep=lambda _: pytest.fail("should not retry"))

    with pytest.raises(GroqInvalidRequestError) as raised:
        client.complete([], [])
    assert raised.value.diagnostics["category"] == "invalid_request"
    assert raised.value.diagnostics["http_status"] == 400
    assert "invalid request" not in str(raised.value)
    assert "x-ratelimit-remaining-requests=7" in str(raised.value)


def test_http_400_tool_generation_fields_are_classified_without_raw_arguments():
    response = httpx.Response(
        400,
        request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
    )

    class FailingCompletions:
        def create(self, **kwargs):
            raise BadRequestError(
                "Invalid tool call generated",
                response=response,
                body={
                    "error": {
                        "type": "invalid_request_error",
                        "code": "tool_use_failed",
                        "message": "Invalid tool call generated",
                        "failed_generation": {
                            "reason": "Tool call arguments are not valid JSON",
                            "attempted_arguments": "SECRET_RAW_ARGUMENTS",
                        },
                    }
                },
            )

    api = SimpleNamespace(chat=SimpleNamespace(completions=FailingCompletions()))
    client = GroqClient(api_key="test-key", client=api, max_retries=2)

    with pytest.raises(GroqInvalidRequestError) as raised:
        client.complete([], [])
    diagnostics = raised.value.diagnostics
    assert diagnostics["category"] == "invalid_tool_call"
    assert diagnostics["error_type"] == "invalid_request_error"
    assert diagnostics["error_code"] == "tool_use_failed"
    assert diagnostics["failed_generation_reason"] == "invalid_tool_call"
    assert "SECRET_RAW_ARGUMENTS" not in str(raised.value)


def test_invalid_tool_generation_gets_one_lower_temperature_recovery():
    response = httpx.Response(
        400,
        request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
    )
    success = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(role="assistant", content="done", tool_calls=None))],
        usage=None,
    )

    class Completions:
        def __init__(self):
            self.calls = []

        def create(self, **kwargs):
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                raise BadRequestError(
                    "tool call failed",
                    response=response,
                    body={"error": {"type": "invalid_request_error", "code": "tool_use_failed"}},
                )
            return success

    completions = Completions()
    api = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    client = GroqClient(api_key="test-key", client=api, max_retries=0)

    result, _ = client.complete([], [])

    assert result is success
    assert len(completions.calls) == 2
    assert [call["tool_choice"] for call in completions.calls] == ["auto", "auto"]
    assert completions.calls[0]["temperature"] == 0.5
    assert completions.calls[1]["temperature"] == 0.2


def test_two_invalid_tool_generation_failures_do_not_exceed_one_recovery():
    response = httpx.Response(
        400,
        request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
    )

    class Completions:
        def __init__(self):
            self.calls = 0

        def create(self, **kwargs):
            self.calls += 1
            raise BadRequestError(
                "tool call failed",
                response=response,
                body={"error": {"type": "invalid_request_error", "code": "tool_use_failed"}},
            )

    completions = Completions()
    api = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    client = GroqClient(api_key="test-key", client=api, max_retries=2)

    with pytest.raises(GroqInvalidRequestError) as raised:
        client.complete([], [])

    assert completions.calls == 2
    assert raised.value.diagnostics["category"] == "invalid_tool_call"
    assert raised.value.diagnostics["tool_call_recovery_attempted"] is True


def test_tool_call_failure_after_partial_investigation_preserves_findings():
    dataset = context()

    class Client:
        def __init__(self):
            self.calls = 0

        def complete(self, messages, tools):
            self.calls += 1
            if self.calls == 1:
                return (
                    SimpleNamespace(
                        choices=[SimpleNamespace(message=SimpleNamespace(
                            role="assistant",
                            content=None,
                            tool_calls=[SimpleNamespace(
                                id="call-1",
                                function=SimpleNamespace(name="profile_dataset", arguments="{}"),
                            )],
                        ))],
                    ),
                    {},
                )
            raise GroqInvalidRequestError(
                "Groq request failed: category=invalid_tool_call; http_status=400",
                {"category": "invalid_tool_call", "http_status": 400},
            )

    result = InvestigationAgent(Client()).investigate(dataset, "profile the dataset")

    assert result.status == "incomplete"
    assert len(result.steps) == 4
    assert result.baseline_tool_calls == 3
    assert sum(step.result.get("status") == "success" for step in result.steps if step.tool_name == "profile_dataset") == 1
    assert result.error is not None


@pytest.mark.parametrize(
    "dataframe,missing_count,duplicate_count",
    [
        (pd.DataFrame({"a": [1, 2], "b": ["x", "y"]}), 0, 0),
        (pd.DataFrame({"a": [1, None], "b": ["x", "y"]}), 1, 0),
        (pd.DataFrame({"a": [1, 1], "b": ["x", "x"]}), 0, 1),
        (pd.DataFrame({"a": [1, 1, None], "b": ["x", "x", "y"]}), 1, 1),
    ],
)
def test_baseline_checks_run_once_and_capture_clean_and_issue_cases(dataframe, missing_count, duplicate_count):
    dataset = DatasetContext("baseline", "synthetic.csv", dataframe, len(dataframe), len(dataframe.columns), list(dataframe.columns))
    before = dataframe.copy(deep=True)
    fake = FakeClient([response("Baseline reviewed.")])

    result = InvestigationAgent(fake).investigate(dataset, "Assess data quality")

    assert result.status == "complete"
    assert result.baseline_tool_calls == 3
    assert [step.call_id for step in result.steps[:3]] == ["baseline-1", "baseline-2", "baseline-3"]
    missing = result.observations[1]["metrics"]
    duplicates = result.observations[2]["metrics"]
    assert sum(missing["missing_counts"].values()) == missing_count
    assert duplicates["duplicate_row_count"] == duplicate_count
    initial_prompt = fake.messages[0][0][1]["content"]
    assert "common_values" not in initial_prompt
    pd.testing.assert_frame_equal(dataframe, before)


def test_redundant_baseline_call_is_skipped_without_duplicate_execution():
    fake = FakeClient([
        response(calls=[call("detect_duplicates", {}, "duplicate-call")]),
        response("Baseline evidence is sufficient."),
    ])

    result = InvestigationAgent(fake).investigate(context(), "Check duplicates")

    skipped = [step for step in result.steps if step.call_id == "duplicate-call"]
    assert len(skipped) == 1
    assert skipped[0].result["status"] == "skipped"
    assert sum(step.result.get("status") == "success" and step.tool_name == "detect_duplicates" for step in result.steps) == 1


def test_http_400_context_size_is_classified_without_retry():
    response = httpx.Response(
        400,
        request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
    )

    class FailingCompletions:
        def create(self, **kwargs):
            raise BadRequestError(
                "Context length exceeded",
                response=response,
                body={"error": {"type": "invalid_request_error", "message": "context length exceeded"}},
            )

    api = SimpleNamespace(chat=SimpleNamespace(completions=FailingCompletions()))
    client = GroqClient(api_key="test-key", client=api, max_retries=2)

    with pytest.raises(GroqInvalidRequestError) as raised:
        client.complete([], [])
    assert raised.value.diagnostics["category"] == "context_size"


def test_connection_and_timeout_failures_are_classified_without_exposing_request_data():
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")

    class FailingCompletions:
        def __init__(self, error):
            self.error = error

        def create(self, **kwargs):
            raise self.error

    for error_type, expected_type, expected_category in [
        (APIConnectionError(message="transport failed", request=request), GroqNetworkError, "connection"),
        (APITimeoutError(request), GroqTimeoutError, "timeout"),
    ]:
        api = SimpleNamespace(chat=SimpleNamespace(completions=FailingCompletions(error_type)))
        client = GroqClient(api_key="test-key", client=api, max_retries=0)
        with pytest.raises(expected_type) as raised:
            client.complete([], [])
        assert raised.value.diagnostics["category"] == expected_category
        assert "api.groq.com" not in str(raised.value)


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
