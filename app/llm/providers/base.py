from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.llm.schemas import LLMRequest, LLMResponse, LLMStreamChunk


class BaseLLMProvider(ABC):

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a response from an LLM."""
        raise NotImplementedError
    
    @abstractmethod
    async def generate_stream( self, request: LLMRequest, ) -> AsyncIterator[LLMStreamChunk]:
        """Generate a streaming response from an LLM."""
        raise NotImplementedError
    