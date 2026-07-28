"""Domain-level exceptions carrying a machine code + safe message + HTTP status."""


class DomainError(Exception):
    code = "DOMAIN_ERROR"
    status_code = 400
    message = "حدث خطأ غير متوقع."

    def __init__(self, message=None, *, code=None, status_code=None, details=None):
        self.message = message or self.message
        self.code = code or self.code
        self.status_code = status_code or self.status_code
        self.details = details
        super().__init__(self.message)


class InvalidStateTransition(DomainError):
    code = "INVALID_STATE_TRANSITION"
    status_code = 409
    message = "انتقال حالة غير مسموح."


class ReportGenerationError(DomainError):
    code = "REPORT_GENERATION_FAILED"
    status_code = 500
    message = "تعذّر إنشاء التقرير."
