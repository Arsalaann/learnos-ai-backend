import httpx
from fastapi import Depends, Request

from app.llm.factory import create_llm_provider
from app.llm.providers.base import BaseLLMProvider
from app.llm.service import LLMService


def get_llm_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client

def get_llm_provider( client: httpx.AsyncClient = Depends(get_llm_http_client), ) -> BaseLLMProvider:
    return create_llm_provider(client)
    

def get_llm_service(provider: BaseLLMProvider = Depends(get_llm_provider)) -> LLMService:
    return LLMService(provider)



        