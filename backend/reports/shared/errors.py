"""Unified API error model.

Every error response the API returns has the shape:
    {"code": "<MACHINE_CODE>", "message": "<safe user message>", "request_id": "..."}
plus an optional "details" object for field-level validation errors.
"""

DEFAULT_CODES = {
    400: "VALIDATION_ERROR",
    401: "NOT_AUTHENTICATED",
    403: "PERMISSION_DENIED",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    415: "UNSUPPORTED_MEDIA_TYPE",
    429: "THROTTLED",
    500: "INTERNAL_ERROR",
}


def build_error(code: str, message: str, request_id: str | None, details=None) -> dict:
    payload = {"code": code, "message": message, "request_id": request_id}
    if details is not None:
        payload["details"] = details
    return payload
