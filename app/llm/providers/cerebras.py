import json
from collections.abc import AsyncIterator

import httpx

from app.core.exceptions import LLMProviderError
from app.llm.http import raise_for_llm_response, translate_llm_connection_error
from app.llm.providers.base import BaseLLMProvider
from app.llm.schemas import GenerationMetadata, LLMRequest, LLMResponse, LLMStreamChunk


class CerebrasProvider(BaseLLMProvider):
    PROVIDER_NAME = "cerebras"
    CHAT_COMPLETIONS_ENDPOINT = "/chat/completions"

    def __init__(self, client: httpx.AsyncClient, model: str):
        self.client = client
        self.model = model

    async def generate(self, request: LLMRequest) -> LLMResponse:
        payload = self._build_payload(request)

        try:
            response = await self.client.post(
                self.CHAT_COMPLETIONS_ENDPOINT,
                json=payload,
            )
            raise_for_llm_response(response)
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            translate_llm_connection_error(e)

        try:
            data = response.json()

            choice = data["choices"][0]
            usage = data["usage"]

            return LLMResponse(
                content=choice["message"]["content"],
                metadata=GenerationMetadata(
                    provider=self.PROVIDER_NAME,
                    model=data["model"],
                    input_tokens=usage["prompt_tokens"],
                    output_tokens=usage["completion_tokens"],
                    finish_reason=choice["finish_reason"],
                ),
            )
        except (KeyError, IndexError, TypeError, ValueError) as e:
            raise LLMProviderError(
                "Invalid response received from the LLM provider."
            ) from e

    async def generate_stream( self, request: LLMRequest, ) -> AsyncIterator[LLMStreamChunk]:
        payload = self._build_payload(request)

        try:
            async with self.client.stream(
                "POST",
                self.CHAT_COMPLETIONS_ENDPOINT,
                json=payload,
            ) as response:
                raise_for_llm_response(response)

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    if line == "data: [DONE]":
                        break

                    if not line.startswith("data: "):
                        continue

                    data = json.loads(line[6:])

                    choices = data.get("choices")

                    if not choices:
                        continue

                    delta = choices[0].get("delta", {})
                    content = delta.get("content")

                    if content:
                        yield LLMStreamChunk(content=content)

        except (httpx.TimeoutException, httpx.ConnectError) as e:
            translate_llm_connection_error(e)
        except json.JSONDecodeError as e:
            raise LLMProviderError(
                "Invalid streaming response received from the LLM provider."
            ) from e

    def _build_payload(self, request: LLMRequest) -> dict:
        payload = {
            "model": request.model or self.model,
            "messages": [
                {
                    "role": message.role.value,
                    "content": message.content,
                }
                for message in request.messages
            ],
            "temperature": request.temperature,
            "max_completion_tokens": request.max_output_tokens,
            "stream": request.stream,
            "response_format": ( request.response_format.model_dump() if request.response_format else None ),
        }

        return {
            key: value
            for key, value in payload.items()
            if value is not None
        }
        
        
        
        


