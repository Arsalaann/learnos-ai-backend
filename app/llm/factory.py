import httpx

from app.core.config import settings
from app.llm.providers.base import BaseLLMProvider
from app.llm.providers.cerebras import CerebrasProvider


def create_llm_http_client() -> httpx.AsyncClient:
    timeout = httpx.Timeout(
        connect=10.0,
        read=120.0,
        write=30.0,
        pool=10.0,
    )

    if settings.LLM_PROVIDER == "cerebras":
        return httpx.AsyncClient(
            base_url=settings.CEREBRAS_BASE_URL.rstrip("/"),
            headers={
                "Authorization": (
                    f"Bearer {settings.CEREBRAS_API_KEY}"
                ),
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    raise ValueError(
        f"Unsupported LLM provider: {settings.LLM_PROVIDER}"
    )


def create_llm_provider(
    client: httpx.AsyncClient,
) -> BaseLLMProvider:
    if settings.LLM_PROVIDER == "cerebras":
        return CerebrasProvider(
            client=client,
            model=settings.CEREBRAS_MODEL,
        )

    raise ValueError(
        f"Unsupported LLM provider: {settings.LLM_PROVIDER}"
    )