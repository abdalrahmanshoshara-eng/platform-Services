"""Correlation ID: one id per request, propagated to logs and Celery tasks (Phase 4)."""

import contextvars
import uuid

_correlation_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("correlation_id", default=None)

REQUEST_HEADER = "HTTP_X_REQUEST_ID"
RESPONSE_HEADER = "X-Request-ID"


def get_correlation_id() -> str | None:
    return _correlation_id.get()


def set_correlation_id(value: str) -> None:
    _correlation_id.set(value)


class CorrelationIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        cid = request.META.get(REQUEST_HEADER) or uuid.uuid4().hex
        set_correlation_id(cid)
        request.correlation_id = cid
        response = self.get_response(request)
        response[RESPONSE_HEADER] = cid
        return response
