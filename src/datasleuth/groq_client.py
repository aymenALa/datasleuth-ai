"""Small, retry-bounded boundary around the Groq Python SDK."""

from __future__ import annotations

import os
import time
from typing import Any, Callable

from groq import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    Groq,
    RateLimitError,
)

from .config import (
    GROQ_MODEL,
    GROQ_TEMPERATURE,
    GROQ_TIMEOUT_SECONDS,
    GROQ_TOOL_CALL_RECOVERY_TEMPERATURE,
    MAX_GROQ_RETRIES,
)


def is_groq_configured() -> bool:
    """Return True if a non-empty GROQ_API_KEY is present in the environment."""

    return bool((os.getenv("GROQ_API_KEY") or "").strip())


def is_live_ai_enabled() -> bool:
    """Return True when GROQ_API_KEY is configured and public-demo lock is not active."""

    public_demo = (os.getenv("DATASLEUTH_PUBLIC_DEMO_MODE") or "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    return is_groq_configured() and not public_demo


class GroqClientError(RuntimeError):
    """Base exception for expected Groq client failures."""

    def __init__(self, message: str, diagnostics: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.diagnostics = diagnostics or {}


class GroqConfigurationError(GroqClientError):
    """Raised when the API key is not configured."""


class GroqRateLimitError(GroqClientError):
    """Raised when bounded retries still encounter rate limiting."""


class GroqNetworkError(GroqClientError):
    """Raised for retryable network/API transport failures."""


class GroqResponseError(GroqClientError):
    """Raised when the SDK response cannot be used."""


class GroqAuthenticationError(GroqClientError):
    """Raised for invalid or unauthorized credentials."""


class GroqInvalidRequestError(GroqClientError):
    """Raised when the request format or parameters are rejected."""


class GroqTimeoutError(GroqClientError):
    """Raised when a Groq request times out after bounded retries."""


class GroqServerError(GroqClientError):
    """Raised for server-side failures after bounded retries."""


class GroqClient:
    """Injectable Groq client with bounded retries and usage extraction."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = GROQ_MODEL,
        client: Any | None = None,
        max_retries: int = MAX_GROQ_RETRIES,
        temperature: float | None = GROQ_TEMPERATURE,
        tool_call_recovery_temperature: float | None = GROQ_TOOL_CALL_RECOVERY_TEMPERATURE,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        key = api_key or os.getenv("GROQ_API_KEY")
        if client is None and not key:
            raise GroqConfigurationError("GROQ_API_KEY is not configured")
        self.model = model
        self.client = client or Groq(api_key=key, max_retries=0, timeout=GROQ_TIMEOUT_SECONDS)
        self.max_retries = max(0, max_retries)
        self.temperature = temperature
        self.tool_call_recovery_temperature = tool_call_recovery_temperature
        self._sleep = sleep

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> tuple[Any, dict[str, int]]:
        """Request one chat completion and return response plus usage metrics."""

        attempts = 0
        tool_call_recovery_attempted = False
        temperature = self.temperature
        while True:
            try:
                request = {
                    "model": self.model,
                    "messages": messages,
                    "tools": tools,
                    "tool_choice": "auto",
                }
                if temperature is not None:
                    request["temperature"] = temperature
                response = self.client.chat.completions.create(**request)
                if not response or not _field(response, "choices", None):
                    raise GroqResponseError("Groq returned no choices")
                return response, _usage_metrics(_field(response, "usage", None))
            except GroqResponseError:
                raise
            except Exception as exc:
                diagnosis = _diagnose(exc)
                retry_after = diagnosis.get("retry_after")
                if (
                    diagnosis["category"] == "invalid_tool_call"
                    and not tool_call_recovery_attempted
                    and self.tool_call_recovery_temperature is not None
                ):
                    tool_call_recovery_attempted = True
                    temperature = min(temperature, self.tool_call_recovery_temperature) if temperature is not None else self.tool_call_recovery_temperature
                    continue
                retryable = bool(diagnosis["retryable"])
                if not retryable or attempts >= self.max_retries:
                    raise _classified_error(
                        diagnosis,
                        attempts,
                        self.max_retries,
                        tool_call_recovery_attempted=tool_call_recovery_attempted,
                    ) from exc
                attempts += 1
                self._sleep(min(retry_after if retry_after is not None else 2**attempts, 30.0))


def _status_code(error: Exception) -> int | None:
    value = getattr(error, "status_code", None)
    return int(value) if isinstance(value, int) else None


def _field(value: Any, name: str, default: Any = None) -> Any:
    return value.get(name, default) if isinstance(value, dict) else getattr(value, name, default)


def _response_headers(error: Exception) -> dict[str, str]:
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", {}) or {}
    allowed = {
        "retry-after",
        "x-ratelimit-remaining-requests",
        "x-ratelimit-remaining-tokens",
        "x-ratelimit-reset-requests",
        "x-ratelimit-reset-tokens",
    }
    return {
        str(key).lower(): str(value)
        for key, value in headers.items()
        if str(key).lower() in allowed
    }


def _retry_after(error: Exception, headers: dict[str, str] | None = None) -> float | None:
    headers = headers or _response_headers(error)
    value = headers.get("retry-after")
    try:
        return max(0.0, float(value)) if value is not None else None
    except (TypeError, ValueError):
        return None


def _diagnose(error: Exception) -> dict[str, Any]:
    status = _status_code(error)
    headers = _response_headers(error)
    retry_after = _retry_after(error, headers)
    body_fields = _safe_body_fields(error)
    if isinstance(error, (AuthenticationError,)) or status in {401, 403}:
        category, retryable = "authentication", False
    elif status == 400 or isinstance(error, BadRequestError):
        category, retryable = _classify_bad_request(body_fields), False
    elif status in {404, 409, 422}:
        category, retryable = "invalid_request", False
    elif isinstance(error, RateLimitError) or status == 429:
        category, retryable = "rate_limit", True
    elif isinstance(error, APITimeoutError) or status == 408:
        category, retryable = "timeout", True
    elif isinstance(error, APIConnectionError):
        category, retryable = "connection", True
    elif isinstance(error, APIStatusError) and status in {500, 502, 503, 504}:
        category, retryable = "server", True
    elif status in {500, 502, 503, 504}:
        category, retryable = "server", True
    else:
        category, retryable = "unknown", False
    return {
        "category": category,
        "exception_type": type(error).__name__,
        "http_status": status,
        "retryable": retryable,
        "retry_after": retry_after,
        "headers": headers,
        **body_fields,
    }


def _safe_body_fields(error: Exception) -> dict[str, Any]:
    """Extract only bounded, non-sensitive categories from an SDK error body."""

    body = getattr(error, "body", None)
    error_body = body.get("error", body) if isinstance(body, dict) else {}
    if not isinstance(error_body, dict):
        return {}
    error_type = _safe_label(error_body.get("type"))
    error_code = _safe_label(error_body.get("code"))
    message_category = _message_category(error_body.get("message"))
    failed = error_body.get("failed_generation")
    if not isinstance(failed, dict):
        failed = {}
    failed_reason = _message_category(failed.get("reason"))
    return {
        "error_type": error_type,
        "error_code": error_code,
        "error_message_category": message_category,
        "failed_generation_reason": failed_reason,
    }


def _safe_label(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = "".join(char for char in value if char.isalnum() or char in "._-")
    return cleaned[:80] or None


def _message_category(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.lower()
    if any(term in text for term in ("context length", "context window", "too many tokens", "maximum context")):
        return "context_size"
    if any(term in text for term in ("tool call", "tool_call", "function call", "arguments are not valid json")):
        return "invalid_tool_call"
    if any(term in text for term in ("conversation", "message history", "tool_call_id", "message order")):
        return "invalid_conversation"
    if any(term in text for term in ("schema", "parameter", "request body", "invalid request")):
        return "invalid_request_schema"
    return "other"


def _classify_bad_request(fields: dict[str, Any]) -> str:
    if (
        fields.get("error_code") == "tool_use_failed"
        or fields.get("failed_generation_reason") == "invalid_tool_call"
        or fields.get("error_message_category") == "invalid_tool_call"
    ):
        return "invalid_tool_call"
    if fields.get("error_message_category") == "context_size":
        return "context_size"
    if fields.get("error_message_category") == "invalid_conversation":
        return "invalid_conversation"
    if fields.get("error_message_category") == "invalid_request_schema":
        return "invalid_request_schema"
    return "invalid_request"


def _classified_error(
    diagnosis: dict[str, Any],
    attempts: int,
    max_retries: int,
    *,
    tool_call_recovery_attempted: bool = False,
) -> GroqClientError:
    if tool_call_recovery_attempted:
        diagnosis = {**diagnosis, "tool_call_recovery_attempted": True}
    category = diagnosis["category"]
    status = diagnosis.get("http_status")
    suffix = f"; http_status={status}" if status is not None else ""
    retry_info = f"; retries={attempts}/{max_retries}"
    header_info = "; headers=" + ",".join(
        f"{key}={value}" for key, value in diagnosis.get("headers", {}).items()
    ) if diagnosis.get("headers") else ""
    body_info = "".join(
        f"; {key}={diagnosis[key]}"
        for key in ("error_type", "error_code", "error_message_category", "failed_generation_reason")
        if diagnosis.get(key)
    )
    recovery_info = "; tool_call_recovery=attempted" if tool_call_recovery_attempted else ""
    message = f"Groq request failed: category={category}{suffix}{retry_info}{recovery_info}{header_info}{body_info}"
    exception_types = {
        "authentication": GroqAuthenticationError,
        "invalid_request": GroqInvalidRequestError,
        "invalid_tool_call": GroqInvalidRequestError,
        "invalid_request_schema": GroqInvalidRequestError,
        "invalid_conversation": GroqInvalidRequestError,
        "context_size": GroqInvalidRequestError,
        "rate_limit": GroqRateLimitError,
        "timeout": GroqTimeoutError,
        "connection": GroqNetworkError,
        "server": GroqServerError,
    }
    return exception_types.get(category, GroqClientError)(message, diagnosis)


def _usage_metrics(usage: Any) -> dict[str, int]:
    if usage is None:
        return {}
    result = {}
    for name in ("prompt_tokens", "completion_tokens", "total_tokens"):
        value = _field(usage, name)
        if isinstance(value, int):
            result[name] = value
    return result
