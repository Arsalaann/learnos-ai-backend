import asyncio
from collections.abc import AsyncIterator

from app.core.exceptions import LLMRateLimitError
from app.llm.providers.base import BaseLLMProvider
from app.llm.schemas import LLMRequest, LLMResponse, LLMStreamChunk


class LLMService:

    MAX_RATE_LIMIT_RETRIES = 2

    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def generate(self, request: LLMRequest) -> LLMResponse:
        for attempt in range(self.MAX_RATE_LIMIT_RETRIES + 1):
            try:
                return await self.provider.generate(request)

            except LLMRateLimitError as error:
                if attempt >= self.MAX_RATE_LIMIT_RETRIES:
                    raise

                retry_after = error.retry_after

                if retry_after is None:
                    raise

                await asyncio.sleep(retry_after)

        raise RuntimeError("LLM generation failed unexpectedly.")

    async def generate_stream(
        self,
        request: LLMRequest,
    ) -> AsyncIterator[LLMStreamChunk]:
        async for chunk in self.provider.generate_stream(request):
            yield chunk