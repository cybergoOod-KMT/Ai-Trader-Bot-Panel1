from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.request_context import get_request_id, set_error_id, set_request_id

logger = logging.getLogger(__name__)


def sanitize_error_message(detail: object) -> str:
    if isinstance(detail, dict):
        message = str(detail.get("message") or detail.get("detail") or "Request failed.")
    else:
        message = str(detail or "Request failed.")
    lowered = message.lower()
    sensitive_tokens = ("secret", "api_key", "api key", "authorization", "bearer", "signature", "password")
    if any(token in lowered for token in sensitive_tokens):
        return "Sensitive upstream error was suppressed."
    return message


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[JSONResponse]]) -> JSONResponse:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        set_request_id(request_id)
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        error_id = str(uuid.uuid4())
        set_error_id(error_id)
        detail = sanitize_error_message(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": detail, "error_id": error_id, "request_id": getattr(request.state, "request_id", get_request_id())},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        error_id = str(uuid.uuid4())
        set_error_id(error_id)
        logger.exception("Unhandled application error", extra={"error_id": error_id, "request_id": getattr(request.state, "request_id", get_request_id())})
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Unexpected server error.",
                "error_id": error_id,
                "request_id": getattr(request.state, "request_id", get_request_id()),
            },
        )
