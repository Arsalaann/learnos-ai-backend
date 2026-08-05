class LLMError(Exception):
    """Base exception for all LLM errors."""


class LLMAuthenticationError(LLMError):
    """Invalid API credentials."""


class LLMRateLimitError(LLMError):
    """Rate limit exceeded."""

    def __init__(self, message: str, retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class LLMProviderError(LLMError):
    """Unexpected provider error."""


class LLMConnectionError(LLMError):
    """Failed to communicate with the provider."""