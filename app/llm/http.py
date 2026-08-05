import logging

import httpx

from app.core.exceptions import (
    LLMAuthenticationError,
    LLMConnectionError,
    LLMProviderError,
    LLMRateLimitError,
)

logger = logging.getLogger(__name__)


def raise_for_llm_response(response: httpx.Response) -> None:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        status = e.response.status_code

        if status == 401:
            raise LLMAuthenticationError("Invalid LLM API key.") from e

        if status == 429:
            retry_after = response.headers.get("Retry-After")

            retry_after_seconds: int | None = None

            if retry_after is not None:
                try:
                    retry_after_seconds = int(retry_after)
                except ValueError:
                    pass

            logger.error(
                "LLM rate limit exceeded | status=%s | retry_after=%s | body=%s",
                status,
                retry_after_seconds,
                response.text,
            )

            raise LLMRateLimitError(
                "LLM rate limit exceeded.",
                retry_after=retry_after_seconds,
            ) from e

        logger.error(
            "LLM provider error | status=%s body=%s",
            response.status_code,
            response.text,
        )

        raise LLMProviderError(
            f"LLM provider returned HTTP {status}."
        ) from e


def translate_llm_connection_error(error: Exception) -> None:
    if isinstance(error, httpx.TimeoutException):
        raise LLMConnectionError("The LLM request timed out.") from error

    if isinstance(error, httpx.ConnectError):
        raise LLMConnectionError(
            "Failed to connect to the LLM provider."
        ) from error

    raise error