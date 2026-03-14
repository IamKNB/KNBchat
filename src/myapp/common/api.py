from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

__all__ = [
    "CursorMeta",
    "ErrorDetail",
    "ErrorEnvelope",
    "Envelope",
    "ListEnvelope",
    "PaginationParams",
]

ErrorDetail = str | dict[str, Any] | list[dict[str, Any]] | None


class CursorMeta(BaseModel):
    has_more: bool
    next_cursor: str | None = None


class ErrorEnvelope(BaseModel):
    code: str
    message: str
    detail: ErrorDetail = None


T = TypeVar("T")


class Envelope(BaseModel, Generic[T]):
    code: str
    message: str
    data: T


class ListEnvelope(BaseModel, Generic[T]):
    code: str
    message: str
    data: list[T]
    meta: CursorMeta


class PaginationParams(BaseModel):
    cursor: str | None = Field(
        default=None,
        description="Opaque keyset cursor from previous response `meta.next_cursor`. Clients should pass through.",
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Page size. Range: 1..100.",
    )
