"""DRF exception handler that renders every error via the unified error model."""

from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from .correlation import get_correlation_id
from .errors import DEFAULT_CODES, build_error
from .exceptions import DomainError


def _message_from(data) -> str:
    if isinstance(data, dict):
        if "detail" in data:
            return str(data["detail"])
        for value in data.values():
            if isinstance(value, (list, tuple)) and value:
                return str(value[0])
            if isinstance(value, str):
                return value
    if isinstance(data, (list, tuple)) and data:
        return str(data[0])
    return "حدث خطأ في الطلب."


def custom_exception_handler(exc, context):
    request_id = get_correlation_id()

    if isinstance(exc, DomainError):
        return Response(
            build_error(exc.code, exc.message, request_id, exc.details),
            status=exc.status_code,
        )

    response = drf_exception_handler(exc, context)
    if response is None:
        # Unhandled -> let Django's 500 path handle it (logged, never leaked here).
        return None

    code = DEFAULT_CODES.get(response.status_code, "ERROR")
    details = response.data if isinstance(response.data, (dict, list)) else None
    response.data = build_error(code, _message_from(response.data), request_id, details)
    return response
