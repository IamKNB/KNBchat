from dataclasses import dataclass
from typing import Any, Callable, Coroutine, NoReturn, Type, cast

from fastapi import Request, status
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.routing import APIRoute

from myapp.common.api import ErrorDetail, ErrorEnvelope

__all__ = [
    "ServiceError",
    "raise_service_error",
    "build_error_responses",
    "make_service_route",
]


@dataclass
class ServiceError(ValueError):
    status_code: int
    code: str
    message: str
    detail: ErrorDetail = None

    def __str__(self) -> str:
        if self.detail is not None:
            return f"{self.code}: {self.detail}"
        return self.code


def raise_service_error(
        *,
        status_code: int,
        code: str,
        message: str,
        detail: ErrorDetail = None,
) -> NoReturn:
    raise ServiceError(
        status_code=status_code,
        code=code,
        message=message,
        detail=detail,
    )


HTTP_CODE_MAP = {
    400: "bad_request",
    401: "not_authenticated",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    422: "validation_error",
    500: "internal_error",
}

HTTP_MESSAGE_MAP = {
    400: "bad request",
    401: "not authenticated",
    403: "forbidden",
    404: "not found",
    409: "conflict",
    422: "validation error",
    500: "internal error",
}


def build_error_responses(envelope_model: Type[ErrorEnvelope]) -> dict[int | str, dict[str, Any]]:
    return {
        status.HTTP_400_BAD_REQUEST: {
            "model": envelope_model,
            "description": "Bad request",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": envelope_model,
            "description": "Not authenticated",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": envelope_model,
            "description": "Forbidden",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": envelope_model,
            "description": "Not found",
        },
        status.HTTP_409_CONFLICT: {
            "model": envelope_model,
            "description": "Conflict",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": envelope_model,
            "description": "Validation error",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": envelope_model,
            "description": "Internal error",
        },
    }


def make_service_route(
        service_error_cls: Type[ServiceError],
        envelope_model: Type[ErrorEnvelope],
) -> type[APIRoute]:
    class ServiceRoute(APIRoute):
        def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
            route_handler = super().get_route_handler()

            async def service_route_handler(request: Request) -> Response:
                try:
                    return await route_handler(request)
                except service_error_cls as exc:
                    payload = envelope_model(
                        code=exc.code,
                        message=exc.message,
                        detail=exc.detail,
                    )
                    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())
                except RequestValidationError as exc:
                    payload = envelope_model(
                        code="validation_error",
                        message="validation error",
                        detail=cast(list[dict[str, Any]], exc.errors()),
                    )
                    return JSONResponse(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        content=payload.model_dump(),
                    )
                except FastAPIHTTPException as exc:
                    payload = envelope_model(
                        code=HTTP_CODE_MAP.get(exc.status_code, "http_error"),
                        message=HTTP_MESSAGE_MAP.get(exc.status_code, "http error"),
                        detail=exc.detail,
                    )
                    return JSONResponse(
                        status_code=exc.status_code,
                        content=payload.model_dump(),
                        headers=exc.headers,
                    )

            return service_route_handler

    return ServiceRoute
