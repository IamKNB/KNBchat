from myapp.common.api import ErrorEnvelope
from myapp.common.errors import ServiceError, build_error_responses, make_service_route

__all__ = ["FRIENDSHIP_ERROR_RESPONSES", "FriendshipRoute"]

FriendshipRoute = make_service_route(ServiceError, ErrorEnvelope)
FRIENDSHIP_ERROR_RESPONSES = build_error_responses(ErrorEnvelope)
