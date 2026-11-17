"""Small, retry-bounded boundary around the Groq Python SDK."""

from __future__ import annotations

import os
import time
from typing import Any, Callable

from groq import Groq

from .config import GROQ_MODEL, MAX_GROQ_RETRIES


class GroqClientError(RuntimeError):
    """Base exception for expected Groq client failures."""


class GroqConfigurationError(GroqClientError):
    """Raised when the API key is not configured."""


class GroqRateLimitError(GroqClientError):
    """Raised when bounded retries still encounter rate limiting."""


class GroqNetworkError(GroqClientError):
    """Raised for retryable network/API transport failures."""


class GroqResponseError(GroqClientError):
    """Raised when the SDK response cannot be used."""


class GroqClient:
    """Injectable Groq client with bounded retries and usage extraction."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = GROQ_MODEL,
        client: Any | None = None,
        max_retries: int = MAX_GROQ_RETRIES,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        key = api_key or os.getenv("GROQ_API_KEY")
        if client is None and not key:
            raise GroqConfigurationError("GROQ_API_KEY is not configured")
        self.model = model
        self.client = client or Groq(api_key=key)
        self.max_retries = max(0, max_retries)
        self._sleep = sleep

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> tuple[Any, dict[str, int]]:
        """Request one chat completion and return response plus usage metrics."""

        attempts = 0
        while True:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                )
                if not response or not _field(response, "choices", None):
                    raise GroqResponseError("Groq returned no choices")
                return response, _usage_metrics(getattr(response, "usage", None))
            except GroqResponseError:
                raise
            except Exception as exc:
                retry_after = _retry_after(exc)
                rate_limited = _status_code(exc) == 429 or retry_after is not None
                retryable = rate_limited or _status_code(exc) in {408, 500, 502, 503, 504}
                if not retryable or attempts >= self.max_retries:
                    if rate_limited:
                        raise GroqRateLimitError("Groq rate limit persisted after bounded retries") from exc
                    raise GroqNetworkError("Groq request failed after bounded retries") from exc
                attempts += 1
                self._sleep(min(retry_after if retry_after is not None else 2**attempts, 30.0))


def _status_code(error: Exception) -> int | None:
    value = getattr(error, "status_code", None)
    return int(value) if isinstance(value, int) else None


def _field(value: Any, name: str, default: Any = None) -> Any:
    return value.get(name, default) if isinstance(value, dict) else getattr(value, name, default)


def _retry_after(error: Exception) -> float | None:
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", {}) or {}
    value = headers.get("retry-after") or headers.get("Retry-After")
    try:
        return max(0.0, float(value)) if value is not None else None
    except (TypeError, ValueError):
        return None


def _usage_metrics(usage: Any) -> dict[str, int]:
    if usage is None:
        return {}
    result = {}
    for name in ("prompt_tokens", "completion_tokens", "total_tokens"):
        value = _field(usage, name)
        if isinstance(value, int):
            result[name] = value
    return result
