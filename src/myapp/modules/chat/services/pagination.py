import base64
import binascii
import json
from typing import Any, Callable, Protocol, Self, TypeVar, cast

from myapp.common.errors import raise_service_error

__all__ = [
    "DEFAULT_PAGE_LIMIT",
    "MAX_PAGE_LIMIT",
    "apply_keyset_filter",
    "decode_cursor_payload",
    "encode_cursor_payload",
    "validate_limit",
]

DEFAULT_PAGE_LIMIT = 20
MAX_PAGE_LIMIT = 100

AnchorT = TypeVar("AnchorT")
StatementT = TypeVar("StatementT", bound="SupportsWhere")


class SupportsWhere(Protocol):
    def where(self, *criteria: Any) -> Self: ...


def apply_keyset_filter(
    statement: StatementT,
    anchor: AnchorT | None,
    build_filter: Callable[..., Any],
    **kwargs: Any,
) -> StatementT:
    if anchor is None:
        return statement
    return statement.where(build_filter(anchor=anchor, **kwargs))


def encode_cursor_payload(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")


def decode_cursor_payload(cursor: str | None) -> dict[str, Any] | None:
    if cursor is None:
        return None

    try:
        padded = cursor + ("=" * (-len(cursor) % 4))
        decoded = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
        payload = cast(dict[str, Any], json.loads(decoded))
    except (
            ValueError,
            TypeError,
            json.JSONDecodeError,
            UnicodeDecodeError,
            binascii.Error,
    ):
        raise_service_error(
            status_code=400,
            code="invalid_cursor",
            message="invalid cursor",
            detail=cursor,
        )

    return payload


def validate_limit(limit: int, max_limit: int) -> None:
    if limit < 1 or limit > max_limit:
        raise_service_error(
            status_code=400,
            code="invalid_limit",
            message="invalid pagination parameters",
            detail=f"limit must be between 1 and {max_limit}",
        )
