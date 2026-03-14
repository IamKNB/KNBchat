from myapp.common.api import ErrorEnvelope
from myapp.common.errors import ServiceError, build_error_responses, make_service_route

__all__ = ["CHAT_ERROR_RESPONSES", "ChatRoute"]

ChatRoute = make_service_route(ServiceError, ErrorEnvelope)
CHAT_ERROR_RESPONSES = build_error_responses(ErrorEnvelope)
