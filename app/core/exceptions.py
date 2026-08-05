import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.llm.exceptions import LLMConnectionError, LLMAuthenticationError, LLMRateLimitError, LLMProviderError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI):

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception")

        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
    
    @app.exception_handler(LLMConnectionError)
    async def llm_connection_error_handler(request: Request, exc: LLMConnectionError):
        logger.exception("LLM connection error")

        return JSONResponse(
            status_code=503,
            content={"detail": str(exc)},
        )

    @app.exception_handler(LLMAuthenticationError)
    async def llm_authentication_error_handler(request: Request, exc: LLMAuthenticationError):
        logger.exception("LLM authentication error")

        return JSONResponse(
            status_code=401,
            content={"detail": str(exc)},
        )

    @app.exception_handler(LLMRateLimitError)
    async def llm_rate_limit_error_handler(request: Request, exc: LLMRateLimitError):
        logger.exception("LLM rate limit exceeded")

        return JSONResponse(
            status_code=429,
            content={"detail": str(exc)},
        )

    @app.exception_handler(LLMProviderError)
    async def llm_provider_error_handler(request: Request, exc: LLMProviderError):
        logger.exception("LLM provider error")

        return JSONResponse(
            status_code=502,
            content={"detail": str(exc)},
        )