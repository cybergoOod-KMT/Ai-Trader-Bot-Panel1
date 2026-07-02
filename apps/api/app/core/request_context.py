from __future__ import annotations

from contextvars import ContextVar

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")
error_id_ctx: ContextVar[str] = ContextVar("error_id", default="-")


def get_request_id() -> str:
    return request_id_ctx.get()


def set_request_id(value: str) -> None:
    request_id_ctx.set(value)


def get_error_id() -> str:
    return error_id_ctx.get()


def set_error_id(value: str) -> None:
    error_id_ctx.set(value)
